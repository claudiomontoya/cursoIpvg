"""
Ejemplo 11 · Chat por terminal con persistencia
=================================================
Qué enseña:
  - Loop interactivo (REPL) clásico: leer input → llamar al modelo → imprimir
  - La conversación se guarda turno a turno en SQLite, así que si cerrás
    la terminal y volvés a abrir, el chat continúa donde lo dejaste
  - Streaming para que veas los tokens en vivo
  - Métricas (tokens, latencia, costo) registradas por cada turno

Comandos durante el chat:
  /salir       → termina la sesión
  /nueva       → empieza una conversación nueva (cambia de sesión)
  /historial   → muestra todos los turnos de la sesión actual
  /metricas    → muestra tokens y costo acumulado de la sesión

Cierre limpio:
  Ctrl+C también cierra la conexión sin corromper la BD.
"""

import sys
import time
from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, calcular_costo

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
MODELO = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "Eres un asistente didáctico de IPVG. Respondes claro y conciso, "
    "en español, adaptando tu tono al nivel de la pregunta."
)


# ======================================================================
# Sesión: por defecto reutilizamos "chat_terminal" para que persista
# entre ejecuciones. /nueva crea una nueva con timestamp.
# ======================================================================
def obtener_o_crear_sesion(nombre: str) -> tuple[int, bool]:
    fila = conn.execute(
        "SELECT id FROM sesiones WHERE nombre = ?", (nombre,)
    ).fetchone()
    if fila:
        return fila["id"], False
    cur = conn.execute("INSERT INTO sesiones (nombre) VALUES (?)", (nombre,))
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (cur.lastrowid, "system", SYSTEM_PROMPT),
    )
    conn.commit()
    return cur.lastrowid, True


def cargar_historial(sesion_id: int) -> list[dict]:
    filas = conn.execute(
        "SELECT rol, contenido FROM mensajes WHERE sesion_id = ? ORDER BY id",
        (sesion_id,),
    ).fetchall()
    return [{"role": f["rol"], "content": f["contenido"]} for f in filas]


def guardar(sesion_id: int, rol: str, contenido: str):
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (sesion_id, rol, contenido),
    )
    conn.commit()


def guardar_metrica(sesion_id: int, prompt_tk: int, resp_tk: int, lat_ms: int):
    """Asociamos las métricas a la sesión vía el campo `ejemplo`."""
    costo = calcular_costo(MODELO, prompt_tk, resp_tk)
    conn.execute(
        """INSERT INTO metricas
              (ejemplo, modelo, tokens_prompt, tokens_respuesta,
               tokens_total, latencia_ms, costo_usd)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (f"chat_terminal_sid={sesion_id}", MODELO,
         prompt_tk, resp_tk, prompt_tk + resp_tk, lat_ms, costo),
    )
    conn.commit()
    return costo


# ======================================================================
# Comandos /
# ======================================================================
def cmd_historial(sesion_id: int):
    filas = conn.execute(
        "SELECT rol, contenido, creado_en FROM mensajes "
        "WHERE sesion_id = ? AND rol != 'system' ORDER BY id",
        (sesion_id,),
    ).fetchall()
    if not filas:
        print("(sin turnos aún)")
        return
    print(f"\n--- Historial ({len(filas)} mensajes) ---")
    for f in filas:
        marca = "👤" if f["rol"] == "user" else "🤖"
        print(f"[{f['creado_en']}] {marca} {f['contenido']}")
    print("--- fin historial ---\n")


def cmd_metricas(sesion_id: int):
    fila = conn.execute(
        """SELECT COUNT(*) AS n,
                  SUM(tokens_total) AS tokens,
                  ROUND(SUM(costo_usd), 6) AS costo,
                  ROUND(AVG(latencia_ms)) AS lat_prom
             FROM metricas
            WHERE ejemplo = ?""",
        (f"chat_terminal_sid={sesion_id}",),
    ).fetchone()
    print(f"\n📊 Sesión {sesion_id}: "
          f"turnos={fila['n']}  tokens={fila['tokens'] or 0}  "
          f"latencia≈{fila['lat_prom'] or 0}ms  "
          f"costo=USD {fila['costo'] or 0}\n")


# ======================================================================
# Turno con streaming
# ======================================================================
def turno(sesion_id: int, texto_usuario: str):
    guardar(sesion_id, "user", texto_usuario)
    historial = cargar_historial(sesion_id)

    print("🤖 ", end="", flush=True)

    t0 = time.perf_counter()
    # `stream_options.include_usage=True` → el último chunk trae el usage,
    # útil porque con streaming normalmente lo perderías.
    stream = client.chat.completions.create(
        model=MODELO,
        messages=historial,
        stream=True,
        stream_options={"include_usage": True},
    )

    partes = []
    usage = None
    for chunk in stream:
        # Algunos chunks (el último) vienen sin choices pero con usage
        if chunk.choices:
            delta = chunk.choices[0].delta.content
            if delta:
                sys.stdout.write(delta)
                sys.stdout.flush()
                partes.append(delta)
        if chunk.usage:
            usage = chunk.usage

    latencia_ms = int((time.perf_counter() - t0) * 1000)
    print()  # newline final

    respuesta = "".join(partes)
    guardar(sesion_id, "assistant", respuesta)

    if usage:
        costo = guardar_metrica(
            sesion_id, usage.prompt_tokens, usage.completion_tokens, latencia_ms
        )
        print(f"   · tokens={usage.total_tokens}  "
              f"latencia={latencia_ms}ms  "
              f"costo=USD {costo:.6f}\n")


# ======================================================================
# REPL
# ======================================================================
def main():
    nombre = "chat_terminal"
    sesion_id, nueva = obtener_o_crear_sesion(nombre)

    print("=" * 60)
    print(" EJEMPLO 11 · Chat por terminal (persistente)")
    print("=" * 60)
    print(f"Sesión: {nombre}  (sid={sesion_id}, "
          f"{'nueva' if nueva else 'continuando'})")
    print("Comandos: /salir  /nueva  /historial  /metricas")
    print("-" * 60)

    if not nueva:
        # Mostramos los últimos 4 turnos para retomar el hilo
        recientes = conn.execute(
            "SELECT rol, contenido FROM mensajes "
            "WHERE sesion_id = ? AND rol != 'system' "
            "ORDER BY id DESC LIMIT 4",
            (sesion_id,),
        ).fetchall()
        if recientes:
            print("Últimos mensajes (más reciente arriba):")
            for f in recientes:
                marca = "👤" if f["rol"] == "user" else "🤖"
                preview = f["contenido"][:80] + ("…" if len(f["contenido"]) > 80 else "")
                print(f"  {marca} {preview}")
            print("-" * 60)

    while True:
        try:
            entrada = input("👤 Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl+C o Ctrl+D → salida limpia
            print("\n👋 Hasta luego.")
            break

        if not entrada:
            continue

        # Comandos especiales
        if entrada in ("/salir", "/exit", "/quit"):
            print("👋 Hasta luego.")
            break
        if entrada == "/nueva":
            nuevo_nombre = f"chat_terminal_{int(time.time())}"
            sesion_id, _ = obtener_o_crear_sesion(nuevo_nombre)
            print(f"🆕 Nueva sesión iniciada: {nuevo_nombre} (sid={sesion_id})")
            continue
        if entrada == "/historial":
            cmd_historial(sesion_id)
            continue
        if entrada == "/metricas":
            cmd_metricas(sesion_id)
            continue

        # Turno normal
        try:
            turno(sesion_id, entrada)
        except Exception as e:
            # No queremos que un error de red mate todo el chat
            print(f"⚠️  Error en la llamada: {e}\n")

    conn.close()


if __name__ == "__main__":
    main()
