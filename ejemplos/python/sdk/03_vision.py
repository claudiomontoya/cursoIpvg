"""
Ejemplo 3 · Vision (modelo multimodal)
=======================================
Qué enseña:
  - Enviar una IMAGEN al modelo junto con texto
  - Dos modos: por URL pública o por base64 (imagen local)
  - El `content` del mensaje pasa de string a lista de "partes"

Idea clave:
  Un modelo multimodal acepta partes de tipo `text` o `image_url`.
  El resto del SDK no cambia: misma `chat.completions.create`.
"""

import base64
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, crear_sesion

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
sesion_id = crear_sesion(conn, "ejemplo_03_vision")


def imagen_local_a_data_url(ruta: Path) -> str:
    """
    Convierte una imagen local a un data URL (base64) que el SDK acepta.
    Formato: data:image/<ext>;base64,<...>
    """
    extension = ruta.suffix.lstrip(".").lower()       # 'png', 'jpg', ...
    if extension == "jpg":
        extension = "jpeg"
    contenido = base64.b64encode(ruta.read_bytes()).decode("utf-8")
    return f"data:image/{extension};base64,{contenido}"


# ----------------------------------------------------------------------
# Elegimos la fuente de la imagen
#   - Si existe ../imagenes/ejemplo.* la usamos (modo offline, didáctico).
#   - Si no, caemos a una URL pública.
# ----------------------------------------------------------------------
carpeta_imgs = Path(__file__).parent.parent / "imagenes"
locales = list(carpeta_imgs.glob("*.png")) + list(carpeta_imgs.glob("*.jpg"))

if locales:
    ruta = locales[0]
    image_url = imagen_local_a_data_url(ruta)
    fuente = f"local: {ruta.name}"
else:
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    fuente = "URL pública (Wikipedia)"

pregunta = "Describe esta imagen en 2 frases. ¿Qué objetos ves?"

print("=" * 60)
print(" EJEMPLO 3 · Vision")
print("=" * 60)
print(f"🖼️  Fuente: {fuente}")
print(f"👤 {pregunta}")

respuesta = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            # 👇 content como LISTA de partes: cada parte es texto o imagen
            "content": [
                {"type": "text",      "text": pregunta},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ],
)

texto = respuesta.choices[0].message.content
print(f"🤖 {texto}")

# ----------------------------------------------------------------------
# Persistencia: guardamos la pregunta y la descripción generada.
# Nota: no guardamos los bytes de la imagen para no inflar la BD;
# guardamos la fuente (URL o nombre de archivo) como contexto.
# ----------------------------------------------------------------------
conn.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      f"[imagen={fuente}] {pregunta}"),
        (sesion_id, "assistant", texto),
    ],
)
conn.commit()
print(f"\n💾 Guardado (sesion_id={sesion_id})")
