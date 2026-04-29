"""
Ejemplo 5 · Análisis de imagen (multimodal)
============================================
Qué enseña:
  - Los modelos omni aceptan texto + imagen en un mismo mensaje
  - Dos formas de enviar imagen: URL pública o archivo local (base64)
  - El 'content' del mensaje puede ser una LISTA de partes

Casos reales:
  - OCR de recibos, formularios, documentos escaneados
  - Accesibilidad: describir imágenes
  - Control de calidad visual
  - Moderación de contenido

Requisitos:
  pip install openai python-dotenv
  .env con OPENAI_API_KEY
"""

import base64
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


# ---------------------------------------------------------------
# OPCIÓN A · Imagen por URL pública
# ---------------------------------------------------------------
def analizar_por_url(url: str, pregunta: str) -> str:
    """Envía una imagen desde una URL pública."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": pregunta},
                    {"type": "image_url", "image_url": {"url": url}},
                ],
            }
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------
# OPCIÓN B · Imagen local codificada como base64
# ---------------------------------------------------------------
def encode_image_base64(path: str) -> str:
    """Lee un archivo de imagen y lo devuelve como string base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analizar_archivo_local(path: str, pregunta: str) -> str:
    """Envía una imagen local como data URL base64."""
    b64 = encode_image_base64(path)

    # Detectar el media type por la extensión (simplificado)
    ext = Path(path).suffix.lower().lstrip(".")
    media_type = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}.get(ext, "jpeg")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": pregunta},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{media_type};base64,{b64}"},
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------
# Demo
# ---------------------------------------------------------------
print("=" * 60)
print(" EJEMPLO 5 · Análisis de imagen (multimodal)")
print("=" * 60)

# --- Demo principal: imagen LOCAL vía base64 ---
# Esta es la forma más ROBUSTA: no depende de que OpenAI pueda descargar la URL.
# Muchos dominios (Wikipedia, sitios detrás de CDN) bloquean bots.
IMG_LOCAL = "./imagenes/demo.jpg"

print(f"\n[Demo A] Imagen local vía base64 ({IMG_LOCAL})")

if Path(IMG_LOCAL).exists():
    descripcion = analizar_archivo_local(
        IMG_LOCAL,
        "Describe esta imagen en 2 frases. ¿Qué hay en ella? ¿De qué color?"
    )
    print(f"\n🤖 Respuesta:\n   {descripcion}")
else:
    print(f"   ⚠️  Falta {IMG_LOCAL} — descarga cualquier imagen JPG/PNG a esa ruta.")

# --- Demo secundaria: imagen por URL pública ---
# Cuidado: muchos servidores bloquean a OpenAI. Lo ideal es que tu URL sea tu propio CDN.
# Descomentar para probar:
#
# URL_DEMO = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400"
# print(f"\n[Demo B] Imagen por URL pública")
# descripcion_url = analizar_por_url(URL_DEMO, "¿Qué ves?")
# print(f"\n🤖 Respuesta:\n   {descripcion_url}")


# =====================================================================
# MORALEJA
# =====================================================================
print("\n" + "=" * 60)
print("☝️  'content' puede ser una LISTA con texto + imagen.")
print("   La imagen va como URL pública o como data URL base64.")
print()
print("   Límites típicos:")
print("   - Hasta 20 imágenes por mensaje")
print("   - Hasta 20 MB por imagen")
print("   - Formatos: JPEG, PNG, WebP, GIF (no animado)")
print()
print("   💡 Para OCR o imágenes con texto pequeño: usa 'high detail'")
print("      en image_url para que el modelo procese a mayor resolución")
print("      (más caro pero mucho más preciso).")
print("=" * 60)
