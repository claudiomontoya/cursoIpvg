"""
Ejemplo 9 · Chat por terminal SIN el SDK de OpenAI
====================================================
Qué enseña:
  - Qué hace el SDK por debajo: una llamada HTTPS POST a /v1/chat/completions
    con un JSON y un header Authorization: Bearer <API_KEY>
  - Cómo parsear "Server-Sent Events" (SSE) a mano para soportar streaming
  - Persistencia de la conversación en SQLite (sin ORM, sqlite3 stdlib)

Diferencia con `ejemplo7_streaming.py`:
  Aquel usa `from openai import OpenAI`. Acá NO importamos `openai`.
  Solo `urllib`, `json`, `sqlite3` (todo stdlib) + `python-dotenv` para la API key.

Cómo correrlo:
    python ejemplo9_chat_sin_sdk.py

Comandos en el chat:
    /salir       termina
    /historial   muestra los turnos guardados
    /nueva       abre una sesión nueva
"""

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["OPENAI_API_KEY"]      # falla rápido si no está
URL     = "https://api.openai.com/v1/chat/completions"
MODELO  = "gpt-4o-mini"

DB_PATH = Path(__file__).parent / "chat_sin_sdk.db"

SYSTEM_PROMPT = (
    "Eres un asistente didáctico de IPVG. Respondes claro y conciso, en español."
)


# ======================================================================
# SQLite — schema inline para mantener este ejemplo self-contained
# ======================================================================
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL UNIQUE,
            creada_en TEXT DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS mensajes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id  INTEGER NOT NULL,
            rol        TEXT NOT NULL,
            contenido  TEXT NOT NULL,
            creado_en  TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    return conn


def obtener_o_crear_sesion(conn: sqlite3.Connection, nombre: str):
    fila = conn.execute("SELECT id FROM sesiones WHERE nombre = ?", (nombre,)).fetchone()
    if fila:
        return fila["id"], False
    cur = conn.execute("INSERT INTO sesiones (nombre) VALUES (?)", (nombre,))
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (cur.lastrowid, "system", SYSTEM_PROMPT),
    )
    conn.commit()
    return cur.lastrowid, True


def cargar_historial(conn, sid: int) -> list[dict]:
    filas = conn.execute(
        "SELECT rol, contenido FROM mensajes WHERE sesion_id = ? ORDER BY id",
        (sid,),
    ).fetchall()
    return [{"role": f["rol"], "content": f["contenido"]} for f in filas]


def guardar(conn, sid: int, rol: str, contenido: str):
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (sid, rol, contenido),
    )
    conn.commit()


# ======================================================================
# HTTP + SSE manual — corazón didáctico del ejemplo
# ======================================================================
def llamar_streaming(messages: list[dict]):
    """
    Envía el chat a /v1/chat/completions con stream=True y va devolviendo
    (delta_text, usage_o_None) chunk a chunk.

    Formato SSE:
      Cada línea relevante empieza con 'data: '
      El payload es JSON, salvo el final '[DONE]'.
    """
    payload = {
        "model": MODELO,
        "messages": messages,
        "stream": True,
        # include_usage: el último chunk trae prompt/completion tokens
        "stream_options": {"include_usage": True},
    }
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type":  "application/json",
            "Accept":        "text/event-stream",
        },
    )

    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        # Devolvemos el cuerpo del error para que el usuario vea qué pasó
        detalle = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {detalle}") from None

    # Iteramos línea a línea (cada chunk SSE puede traer varias)
    for raw in resp:
        linea = raw.decode("utf-8").strip()
        if not linea or not linea.startswith("data:"):
            continue
        data = linea[len("data:"):].strip()
        if data == "[DONE]":
            break
        chunk = json.loads(data)

        # En streaming, choices[0].delta.content trae el fragmento.
        # El último chunk con usage suele venir con choices vacío.
        delta = ""
        if chunk.get("choices"):
            delta = chunk["choices"][0].get("delta", {}).get("content", "") or ""

        usage = chunk.get("usage")   # solo presente al final
        yield delta, usage


# ======================================================================
# Turno: persiste, llama, imprime con streaming, persiste respuesta
# ======================================================================
def turno(conn, sid: int, texto_usuario: str):
    guardar(conn, sid, "user", texto_usuario)
    historial = cargar_historial(conn, sid)

    print("🤖 ", end="", flush=True)

    partes = []
    usage_final = None
    t0 = time.perf_counter()

    for delta, usage in llamar_streaming(historial):
        if delta:
            sys.stdout.write(delta)
            sys.stdout.flush()
            partes.append(delta)
        if usage:
            usage_final = usage

    latencia_ms = int((time.perf_counter() - t0) * 1000)
    print()  # newline

    respuesta = "".join(partes)
    guardar(conn, sid, "assistant", respuesta)

    if usage_final:
        print(f"   · tokens={usage_final['total_tokens']}  "
              f"(prompt={usage_final['prompt_tokens']}, "
              f"resp={usage_final['completion_tokens']})  "
              f"latencia={latencia_ms}ms\n")


# ======================================================================
# Comandos auxiliares
# ======================================================================
def cmd_historial(conn, sid: int):
    filas = conn.execute(
        "SELECT rol, contenido, creado_en FROM mensajes "
        "WHERE sesion_id = ? AND rol != 'system' ORDER BY id",
        (sid,),
    ).fetchall()
    if not filas:
        print("(sin turnos aún)\n")
        return
    print(f"\n--- Historial ({len(filas)} mensajes) ---")
    for f in filas:
        marca = "👤" if f["rol"] == "user" else "🤖"
        print(f"[{f['creado_en']}] {marca} {f['contenido']}")
    print("--- fin ---\n")


# ======================================================================
# REPL
# ======================================================================
def main():
    conn = init_db()
    nombre = "chat_sin_sdk"
    sid, nueva = obtener_o_crear_sesion(conn, nombre)

    print("=" * 60)
    print(" EJEMPLO 9 · Chat por terminal SIN SDK (HTTP + SSE)")
    print("=" * 60)
    print(f"Sesión: {nombre}  (sid={sid}, "
          f"{'nueva' if nueva else 'continuando'})")
    print(f"BD:     {DB_PATH.name}")
    print("Comandos: /salir  /nueva  /historial")
    print("-" * 60)

    while True:
        try:
            entrada = input("👤 Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Hasta luego.")
            break

        if not entrada:
            continue

        if entrada in ("/salir", "/exit", "/quit"):
            print("👋 Hasta luego.")
            break
        if entrada == "/nueva":
            nuevo = f"chat_sin_sdk_{int(time.time())}"
            sid, _ = obtener_o_crear_sesion(conn, nuevo)
            print(f"🆕 Nueva sesión: {nuevo} (sid={sid})")
            continue
        if entrada == "/historial":
            cmd_historial(conn, sid)
            continue

        try:
            turno(conn, sid, entrada)
        except Exception as e:
            print(f"⚠️  Error: {e}\n")

    conn.close()


if __name__ == "__main__":
    main()
