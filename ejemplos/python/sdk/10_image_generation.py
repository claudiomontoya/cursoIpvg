"""
Ejemplo 10 · Generación de imágenes
=====================================
Qué enseña:
  - Usar `client.images.generate` con `gpt-image-1` (o `dall-e-3`)
  - Recibir la imagen como base64, decodificarla y guardarla en disco
  - Registrar el prompt y la ruta resultante en SQLite

Notas:
  - `gpt-image-1` es el modelo más reciente (mejor seguimiento de prompt).
  - Tamaños comunes: '1024x1024', '1024x1792', '1792x1024'.
  - El campo `b64_json` evita una segunda descarga (vs. `url`).
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
# Generación. Pedimos b64_json para no depender de URL temporal.
# ----------------------------------------------------------------------
respuesta = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024",
    n=1,
)

# La respuesta trae .data, lista con n imágenes
img_b64 = respuesta.data[0].b64_json
img_bytes = base64.b64decode(img_b64)

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

# ----------------------------------------------------------------------
# Persistencia: prompt y ruta del archivo
# ----------------------------------------------------------------------
conn.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      prompt),
        (sesion_id, "assistant", f"[imagen generada → {ruta}]"),
    ],
)
conn.commit()
print(f"\n💾 Guardado (sesion_id={sesion_id})")
