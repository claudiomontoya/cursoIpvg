"""
Ejemplo 6 · Memoria persistente en SQLite
==========================================
Qué enseña:
  - El SDK NO recuerda nada entre ejecuciones
  - Si quieres una conversación que sobreviva a reinicios → BD
  - Patrón: cargar historial al iniciar, guardar cada turno

Diferencia con `ejemplo3_con_memoria.py` (carpeta superior):
  Ahí la memoria viví en una lista de Python (se pierde al cerrar).
  Aquí la memoria vive en SQLite → corres el script 3 veces y
  el modelo sigue recordando lo de las ejecuciones previas.
"""

import sys
from dotenv import load_dotenv
from openai import OpenAI

from db import conectar

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()

# Una sesión "fija" identificada por nombre. Si ya existe la reutilizamos;
# si no, la creamos. Así la memoria sobrevive entre ejecuciones.
NOMBRE_SESION = "tutor_ipvg_persistente"

fila = conn.execute(
    "SELECT id FROM sesiones WHERE nombre = ?", (NOMBRE_SESION,)
).fetchone()

if fila:
    sesion_id = fila["id"]
    nueva = False
else:
    cur = conn.execute("INSERT INTO sesiones (nombre) VALUES (?)", (NOMBRE_SESION,))
    conn.commit()
    sesion_id = cur.lastrowid
    nueva = True
    # System prompt inicial solo cuando la sesión es nueva
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (sesion_id, "system", "Eres un tutor amable de IPVG. Responde en 1-2 frases."),
    )
    conn.commit()


def cargar_historial() -> list[dict]:
    """Reconstruye la lista de messages que espera el SDK desde la BD."""
    filas = conn.execute(
        "SELECT rol, contenido FROM mensajes WHERE sesion_id = ? ORDER BY id",
        (sesion_id,),
    ).fetchall()
    return [{"role": f["rol"], "content": f["contenido"]} for f in filas]


def guardar(rol: str, contenido: str):
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (sesion_id, rol, contenido),
    )
    conn.commit()


def preguntar(texto: str):
    guardar("user", texto)
    historial = cargar_historial()       # 👈 incluye TODO lo previo + lo recién guardado

    resp = client.chat.completions.create(
        model="gpt-5.2",
        messages=historial,
    )
    respuesta = resp.choices[0].message.content
    guardar("assistant", respuesta)

    print(f"👤 {texto}")
    print(f"🤖 {respuesta}")
    print(f"   (historial actual: {len(historial)+1} mensajes en BD)\n")


print("=" * 60)
print(" EJEMPLO 6 · Memoria persistente (SQLite)")
print("=" * 60)
print(f"Sesión: {NOMBRE_SESION}  (sesion_id={sesion_id}, "
      f"{'nueva' if nueva else 'recuperada de BD'})\n")

# Permite pasar la pregunta por argumento, o usa una por defecto
if len(sys.argv) > 1:
    preguntar(" ".join(sys.argv[1:]))
else:
    if nueva:
        # Primera vez → contamos algo de nosotros
        preguntar("Hola, me llamo Claudio y enseño en IPVG.")
        preguntar("¿Qué materia debería empezar a enseñar primero sobre IA?")
    else:
        # Veces siguientes → probamos que recuerda
        preguntar("¿Recuerdas mi nombre y dónde enseño?")

print("💡 Volvé a correr el script para ver que la memoria persiste:")
print(f"   python 06_memoria_sqlite.py \"otra pregunta\"")
