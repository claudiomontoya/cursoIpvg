"""
Ejemplo 1 · Llamada básica al SDK de OpenAI
============================================
Qué enseña:
  - Cómo instanciar el cliente `OpenAI()` (lee OPENAI_API_KEY del entorno)
  - Estructura mínima de `chat.completions.create`
  - Cómo persistir la pregunta y la respuesta en SQLite

Idea clave:
  Una llamada al modelo es: lista de mensajes → respuesta.
  El SDK no guarda nada por ti; si quieres historial, lo guardas tú.
"""

from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, crear_sesion

# Carga OPENAI_API_KEY desde ../.env (un directorio arriba)
load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
sesion_id = crear_sesion(conn, "ejemplo_01_basico")

pregunta = "Explica en una frase qué es un token en un LLM."

# ----------------------------------------------------------------------
# Llamada al modelo
# ----------------------------------------------------------------------
respuesta = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Eres un docente claro y breve."},
        {"role": "user",   "content": pregunta},
    ],
)

texto = respuesta.choices[0].message.content

# ----------------------------------------------------------------------
# Persistencia en SQLite
# ----------------------------------------------------------------------
cur = conn.cursor()
cur.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      pregunta),
        (sesion_id, "assistant", texto),
    ],
)
conn.commit()

print("=" * 60)
print(" EJEMPLO 1 · Llamada básica")
print("=" * 60)
print(f"👤 Pregunta : {pregunta}")
print(f"🤖 Respuesta: {texto}")
print(f"\n💾 Guardado en sdk_demo.db (sesion_id={sesion_id})")
