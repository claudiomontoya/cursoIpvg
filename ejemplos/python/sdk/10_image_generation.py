"""
Ejemplo 10 · Generación de imágenes
=====================================
Qué enseña:
  - Usar Responses API con `gpt-5.2` y la tool hosted `image_generation`
  - Extraer la imagen base64 desde un item `image_generation_call`
  - Decodificarla y guardarla en disco
  - Registrar el prompt y la ruta resultante en SQLite

Notas:
  - `gpt-5.2` es el modelo principal: interpreta el pedido y llama la tool.
  - La generación final la realiza internamente un modelo GPT Image.
  - El resultado de `image_generation_call.result` viene en base64.
"""

import base64
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, crear_sesion

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
sesion_id = crear_sesion(conn, "ejemplo_10_image_generation")

prompt = (
    "Una ilustración educativa estilo flat: un cerebro de circuitos "
    "azul profundo con detalles dorados, sobre fondo blanco, "
    "aspecto institucional y limpio."
)

print("=" * 60)
print(" EJEMPLO 10 · Image generation")
print("=" * 60)
print(f"📝 Prompt: {prompt}\n")

# ----------------------------------------------------------------------
# Generación con Responses API + hosted tool.
# `tool_choice` fuerza que este ejemplo produzca una imagen.
# ----------------------------------------------------------------------
respuesta = client.responses.create(
    model="gpt-5.2",
    input=prompt,
    tools=[{"type": "image_generation"}],
    tool_choice={"type": "image_generation"},
)

image_calls = [
    item
    for item in respuesta.output
    if getattr(item, "type", None) == "image_generation_call"
]

if not image_calls:
    raise RuntimeError("La respuesta no incluyó un item image_generation_call.")

img_b64 = image_calls[0].result
img_bytes = base64.b64decode(img_b64)
prompt_revisado = getattr(image_calls[0], "revised_prompt", None)

# ----------------------------------------------------------------------
# Guardamos en disco con timestamp para no pisar versiones previas
# ----------------------------------------------------------------------
salida_dir = Path(__file__).parent / "imagenes_generadas"
salida_dir.mkdir(exist_ok=True)
nombre = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
ruta = salida_dir / nombre
ruta.write_bytes(img_bytes)

print(f"🖼️  Imagen guardada en: {ruta}")
print(f"   Tamaño: {len(img_bytes)//1024} KB")
if prompt_revisado:
    print(f"   Prompt revisado: {prompt_revisado}")

# ----------------------------------------------------------------------
# Persistencia: prompt y ruta del archivo
# ----------------------------------------------------------------------
conn.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      prompt),
        (sesion_id, "assistant", f"[imagen generada con gpt-5.2 → {ruta}]"),
    ],
)
conn.commit()
print(f"\n💾 Guardado (sesion_id={sesion_id})")
