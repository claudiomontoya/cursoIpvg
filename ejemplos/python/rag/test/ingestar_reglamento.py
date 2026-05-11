"""
test/ingestar_reglamento.py
---------------------------
Ingesta el PDF real `reglamento.pdf` (Reglamento Académico 2026 IPVG) en una
nueva collection de Qdrant: `reglamento_ipvg`.

Pipeline:
    PDF → texto por página → chunks (~500 chars, overlap 100) → embed → upsert

El payload guarda { texto, pagina } para poder citar la fuente en las respuestas.
Correr UNA VEZ antes de buscar o levantar la webapp.
"""

import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import pdfplumber
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Carga .env desde el root del proyecto (sube 3 niveles: test/ → rag/ → python/ → ejemplos/ → root)
ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

PDF_PATH = ROOT / "reglamento.pdf"
COLLECTION = "reglamento_ipvg"
EMBED_MODEL = "text-embedding-3-small"
DIMENSION = 1536
CHUNK_SIZE = 500
OVERLAP = 100

openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)


def extraer_paginas(pdf_path: Path) -> list[tuple[int, str]]:
    """Devuelve [(num_pagina, texto), ...] saltando páginas vacías.

    Usa pdfplumber porque decodifica bien las ligaduras tipográficas (fi, ff, ffi)
    que pypdf deja como '/f_i' o caracteres rotos.
    """
    paginas = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            texto = (page.extract_text() or "").strip()
            if texto:
                paginas.append((i, texto))
    return paginas


def chunkear(texto: str, tam: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Chunking por caracteres con overlap. Recorta espacios extra."""
    texto = " ".join(texto.split())
    chunks, i = [], 0
    while i < len(texto):
        trozo = texto[i : i + tam].strip()
        if trozo:
            chunks.append(trozo)
        i += tam - overlap
    return chunks


def embed(textos: list[str]) -> list[list[float]]:
    """Batch de embeddings — 1 sola llamada para todos."""
    r = openai_client.embeddings.create(model=EMBED_MODEL, input=textos)
    return [d.embedding for d in r.data]


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"No encuentro el PDF en {PDF_PATH}")

    print(f"📄 Leyendo {PDF_PATH.name}…")
    paginas = extraer_paginas(PDF_PATH)
    print(f"   {len(paginas)} páginas con texto")

    # Chunkear cada página manteniendo trazabilidad
    items: list[tuple[str, int]] = []  # (chunk_texto, num_pagina)
    for num_pagina, texto in paginas:
        for chunk in chunkear(texto):
            items.append((chunk, num_pagina))
    print(f"   {len(items)} chunks generados")

    print(f"\n🧮 Generando embeddings (batches de 100)…")
    vectores: list[list[float]] = []
    for i in range(0, len(items), 100):
        batch = [t for t, _ in items[i : i + 100]]
        vectores.extend(embed(batch))
        print(f"   {min(i + 100, len(items))}/{len(items)}")

    print(f"\n💾 Creando collection '{COLLECTION}' en Qdrant…")
    if qdrant.collection_exists(COLLECTION):
        qdrant.delete_collection(COLLECTION)
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=DIMENSION, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={"texto": texto, "pagina": pagina, "fuente": "reglamento_2026"},
        )
        for (texto, pagina), vec in zip(items, vectores)
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points)

    info = qdrant.get_collection(COLLECTION)
    print(f"\n✅ Listo. Points en '{COLLECTION}': {info.points_count}")
    print(f"   Próximo paso: python test/buscar_reglamento.py")


if __name__ == "__main__":
    main()
