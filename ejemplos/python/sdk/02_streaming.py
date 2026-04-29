"""
Ejemplo 2 · Streaming de tokens
================================
Qué enseña:
  - `stream=True` devuelve un iterador de "chunks" (trozos)
  - Cada chunk trae un `delta.content` con un fragmento del texto
  - Útil para UIs estilo ChatGPT (sensación de respuesta en vivo)

Idea clave:
  Sin streaming esperas TODA la respuesta antes de ver algo.
  Con streaming ves los tokens según se generan → mejor UX.
"""

import sys
from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, crear_sesion

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
sesion_id = crear_sesion(conn, "ejemplo_02_streaming")

pregunta = "Cuéntame en 3 frases la historia del transformer."

print("=" * 60)
print(" EJEMPLO 2 · Streaming")
print("=" * 60)
print(f"👤 {pregunta}")
print("🤖 ", end="", flush=True)

# stream=True → iteramos chunks
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": pregunta}],
    stream=True,
)

# Acumulamos el texto completo para poder guardarlo en BD al final
texto_completo = []

for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:                      # algunos chunks vienen vacíos (rol, finish_reason)
        sys.stdout.write(delta)    # escribimos sin newline ni buffer
        sys.stdout.flush()
        texto_completo.append(delta)

print()  # newline final

# ----------------------------------------------------------------------
# Persistencia: cuando termina el stream, guardamos la respuesta entera
# ----------------------------------------------------------------------
respuesta_final = "".join(texto_completo)
conn.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      pregunta),
        (sesion_id, "assistant", respuesta_final),
    ],
)
conn.commit()

print(f"\n💾 Respuesta completa guardada (sesion_id={sesion_id})")
