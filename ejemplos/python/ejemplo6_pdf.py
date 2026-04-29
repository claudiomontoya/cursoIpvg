"""
Ejemplo 6 · Análisis de PDF
============================
Qué enseña:
  Dos formas de darle un PDF al modelo:

  (A) Files API · el modelo lee el PDF NATIVAMENTE (texto + imágenes + tablas)
      → mejor para documentos ricos, escaneados, con layout importante

  (B) Extracción local con pypdf · solo el texto, enviado inline
      → más barato, más simple, más rápido
      → pierde imágenes y layout

Cuándo usar cuál:
  - Documento con solo texto (contrato, nota, artículo) → (B)
  - Documento con tablas, gráficos, imágenes, escaneado → (A)

Requisitos:
  pip install openai python-dotenv pypdf
  Un PDF cualquiera en ./documentos/documento.pdf
"""

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

PDF_PATH = "./documentos/documento.pdf"


# ---------------------------------------------------------------
# OPCIÓN A · Files API (PDF nativo)
# ---------------------------------------------------------------
def analizar_con_files_api(pdf_path: str, pregunta: str) -> str:
    """
    Sube el PDF a OpenAI y lo referencia en el mensaje.
    El modelo ve el PDF completo: texto, imágenes, tablas, layout.
    """
    # 1. Subir el archivo a la Files API
    with open(pdf_path, "rb") as f:
        archivo = client.files.create(file=f, purpose="user_data")

    print(f"   📤 PDF subido a OpenAI. file_id: {archivo.id}")

    # 2. Referenciarlo en un mensaje multimodal
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": pregunta},
                    {"type": "file", "file": {"file_id": archivo.id}},
                ],
            }
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------
# OPCIÓN B · Extracción local con pypdf (solo texto)
# ---------------------------------------------------------------
def analizar_extrayendo_texto(pdf_path: str, pregunta: str) -> str:
    """
    Extrae el texto del PDF localmente y lo envía inline.
    Más simple y barato. Pierde imágenes, gráficos y layout.
    """
    from pypdf import PdfReader

    # 1. Extraer texto de todas las páginas
    reader = PdfReader(pdf_path)
    paginas = []
    for i, pagina in enumerate(reader.pages, 1):
        texto = pagina.extract_text() or ""
        paginas.append(f"=== Página {i} ===\n{texto}")

    texto_completo = "\n\n".join(paginas)

    # 2. Truncar si es muy largo (proteger el context window)
    if len(texto_completo) > 50_000:
        texto_completo = texto_completo[:50_000] + "\n\n[... documento truncado ...]"

    print(f"   📄 Texto extraído: {len(texto_completo)} caracteres, "
          f"{len(reader.pages)} páginas")

    # 3. Llamada al modelo con el texto dentro de tags <doc>
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Respondes usando SOLO el contenido del documento. "
                    "Si la información no aparece, dilo explícitamente."
                ),
            },
            {
                "role": "user",
                "content": f"Documento:\n<doc>\n{texto_completo}\n</doc>\n\n{pregunta}",
            },
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------
# Demo
# ---------------------------------------------------------------
print("=" * 60)
print(" EJEMPLO 6 · Análisis de PDF")
print("=" * 60)

if not Path(PDF_PATH).exists():
    print(f"\n⚠️  No hay PDF en {PDF_PATH}")
    print("   Crea la carpeta ./documentos/ y pon cualquier PDF con ese nombre.")
    print("   Ej: cualquier artículo, contrato, informe, etc.")
else:
    # --- Opción B (más simple) ---
    print("\n[Opción B] Extracción local + inline")
    respuesta_b = analizar_extrayendo_texto(
        PDF_PATH,
        "Resume este documento en 3 viñetas concisas. ¿De qué trata?"
    )
    print(f"\n🤖 Respuesta:\n{respuesta_b}")

    # --- Opción A (descomentá para probar) ---
    # print("\n[Opción A] Files API (PDF nativo)")
    # respuesta_a = analizar_con_files_api(
    #     PDF_PATH,
    #     "Extrae las tablas y explícalas. Si no hay tablas, dilo."
    # )
    # print(f"\n🤖 Respuesta:\n{respuesta_a}")


# =====================================================================
# MORALEJA
# =====================================================================
print("\n" + "=" * 60)
print("☝️  Dos caminos para un PDF:")
print()
print("   Files API · nativo:")
print("     ✓ Ve imágenes, tablas, gráficos, layout")
print("     ✗ Más caro, requiere subida previa")
print("     → Recibos escaneados, papers con figuras, formularios")
print()
print("   Extracción local (pypdf) + inline:")
print("     ✓ Más barato, más rápido")
print("     ✗ Solo texto, pierde todo lo visual")
print("     → Contratos, artículos, libros, notas")
print()
print("   💡 Si el PDF es muy largo: dividir por capítulos/secciones,")
print("      indexar en vector DB, y hacer RAG (ejemplo de Vector DBs).")
print("=" * 60)
