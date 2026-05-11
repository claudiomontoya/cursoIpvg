"""
apprag_pro/ingestar.py
----------------------
Ingesta profesional del Reglamento Académico 2026 en Qdrant.

Diferencias con apprag/ (versión simple):

  · Chunking ESTRUCTURAL: detecta `TÍTULO X` y `Art. Nº` por regex.
    Cada chunk corresponde a un artículo completo (o se subdivide por oraciones
    si excede el tamaño máximo, pero nunca corta a la mitad de una palabra).

  · Metadata RICA en el payload:
        - titulo_seccion : "TÍTULO V · DE LOS DERECHOS Y DEBERES…"
        - articulo       : "Art. 15º"
        - pagina         : número de página donde inicia el chunk
        - texto          : contenido del chunk
        - fuente         : "reglamento_2026"

  · Limpieza: descarta headers/footers repetidos como "REGLAMENTO ACADÉMICO 2026"
    y los números de página sueltos.

  · Conteo de tokens con `tiktoken` (no con caracteres a ojo).
"""

import os
import re
import uuid
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import pdfplumber
import tiktoken
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

PDF_PATH = ROOT / "reglamento.pdf"
COLLECTION = "reglamento_ipvg_pro"
EMBED_MODEL = "text-embedding-3-small"
DIMENSION = 1536
MAX_TOKENS = 400          # tamaño máximo por chunk (suficiente para un artículo medio)
TOKEN_OVERLAP = 80        # solape solo si hay que partir un artículo largo

openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    timeout=60,   # Qdrant Cloud puede tardar varios segundos en aceptar batches grandes
)
encoder = tiktoken.encoding_for_model(EMBED_MODEL)


# ---------- Regex de estructura ----------
# TÍTULO en una línea, ej: "TÍTULO V DE LOS DERECHOS Y DEBERES DE LOS Y LAS ESTUDIANTES"
RE_TITULO = re.compile(r"^T[IÍ]TULO\s+([IVXLCDM]+)\b\s*(.*)$", re.IGNORECASE)
# Artículo, ej: "Art. 15º" o "Art. 37°" o "Art 15"
RE_ARTICULO = re.compile(r"\bArt\.?\s+(\d+)\s*[º°]?", re.IGNORECASE)
# Header repetido de cada página
RE_HEADER = re.compile(r"^\s*REGLAMENTO\s+ACAD[EÉ]MICO\s+\d{4}\s*$", re.IGNORECASE)


def limpiar_linea(linea: str) -> str:
    """Quita headers repetidos y números de página sueltos."""
    linea = linea.strip()
    if RE_HEADER.match(linea):
        return ""
    if linea.isdigit() and len(linea) <= 3:  # número de página suelto
        return ""
    return linea


def extraer_paginas(pdf_path: Path) -> list[tuple[int, str]]:
    """Extrae texto página a página, limpiando líneas basura."""
    paginas = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            crudo = page.extract_text() or ""
            lineas = [limpiar_linea(l) for l in crudo.split("\n")]
            limpio = "\n".join(l for l in lineas if l)
            if limpio.strip():
                paginas.append((i, limpio))
    return paginas


def contar_tokens(texto: str) -> int:
    return len(encoder.encode(texto))


def partir_por_oraciones(texto: str, max_tokens: int) -> list[str]:
    """Si un artículo es muy largo, lo parte por oraciones manteniendo el límite."""
    oraciones = re.split(r"(?<=[\.\?\!])\s+", texto)
    chunks, buffer = [], ""
    for orac in oraciones:
        candidato = (buffer + " " + orac).strip()
        if contar_tokens(candidato) <= max_tokens:
            buffer = candidato
        else:
            if buffer:
                chunks.append(buffer)
            buffer = orac
    if buffer:
        chunks.append(buffer)
    return chunks


def chunkear_estructural(paginas: list[tuple[int, str]]) -> list[dict]:
    """Recorre el texto manteniendo `titulo_seccion` y `articulo` actuales.
    Cada artículo se vuelca como un chunk; si supera MAX_TOKENS, se subdivide
    por oraciones replicando los metadatos.
    """
    titulo_actual = ""
    articulo_actual = ""
    pagina_inicio = 1
    buffer_lineas: list[str] = []
    chunks: list[dict] = []

    def flush(pagina_fin: int) -> None:
        nonlocal buffer_lineas
        texto = " ".join(buffer_lineas).strip()
        buffer_lineas = []
        if not texto or not articulo_actual:
            return
        # Si supera el límite, parte por oraciones
        sub_textos = (
            [texto]
            if contar_tokens(texto) <= MAX_TOKENS
            else partir_por_oraciones(texto, MAX_TOKENS)
        )
        for sub in sub_textos:
            chunks.append(
                {
                    "texto": sub.strip(),
                    "pagina": pagina_inicio,
                    "titulo_seccion": titulo_actual,
                    "articulo": articulo_actual,
                }
            )

    # Aplano todas las páginas en una lista de (num_pagina, linea) para poder mirar
    # la línea siguiente cuando un TÍTULO viene partido en dos renglones.
    lineas_planas: list[tuple[int, str]] = []
    for num_pagina, texto_pagina in paginas:
        for linea in texto_pagina.split("\n"):
            linea = linea.strip()
            if linea:
                lineas_planas.append((num_pagina, linea))

    i = 0
    while i < len(lineas_planas):
        num_pagina, linea = lineas_planas[i]
        m_titulo = RE_TITULO.match(linea)
        m_articulo = RE_ARTICULO.search(linea)

        if m_titulo:
            # Cambio de TÍTULO → flush lo acumulado
            flush(num_pagina)
            numeral, resto = m_titulo.group(1), m_titulo.group(2).strip()
            # Si la descripción no vino en la misma línea, mirar la siguiente
            if not resto and i + 1 < len(lineas_planas):
                siguiente = lineas_planas[i + 1][1]
                # Heurística: descripción = mayúsculas, sin "Art." y razonablemente larga
                if (
                    siguiente.isupper()
                    and not RE_ARTICULO.search(siguiente)
                    and len(siguiente.split()) >= 2
                ):
                    resto = siguiente
                    i += 1  # consume la línea siguiente
            titulo_actual = f"TÍTULO {numeral}" + (f" · {resto}" if resto else "")
            i += 1
            continue

        if m_articulo and linea.lower().startswith(("art.", "art ")):
            # Comienza un nuevo artículo → flush el anterior
            flush(num_pagina)
            articulo_actual = f"Art. {m_articulo.group(1)}º"
            pagina_inicio = num_pagina
            buffer_lineas.append(linea)
        else:
            buffer_lineas.append(linea)
        i += 1

    flush(paginas[-1][0])
    return chunks


def embed_batch(textos: list[str]) -> list[list[float]]:
    r = openai_client.embeddings.create(model=EMBED_MODEL, input=textos)
    return [d.embedding for d in r.data]


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"No encuentro el PDF en {PDF_PATH}")

    print(f"📄 Leyendo {PDF_PATH.name}…")
    paginas = extraer_paginas(PDF_PATH)
    print(f"   {len(paginas)} páginas con texto")

    print("\n🧩 Chunking estructural (por TÍTULO + Art.º)…")
    chunks = chunkear_estructural(paginas)
    print(f"   {len(chunks)} chunks generados")
    print("   Primeros 3 artículos detectados:")
    for c in chunks[:3]:
        print(f"     · {c['titulo_seccion'] or '(sin título)':52} | {c['articulo']:10} | pág. {c['pagina']}")

    print(f"\n🧮 Generando embeddings (batches de 100)…")
    vectores: list[list[float]] = []
    for i in range(0, len(chunks), 100):
        batch = [c["texto"] for c in chunks[i : i + 100]]
        vectores.extend(embed_batch(batch))
        print(f"   {min(i + 100, len(chunks))}/{len(chunks)}")

    print(f"\n💾 Recreando collection '{COLLECTION}' en Qdrant…")
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
            payload={**chunk, "fuente": "reglamento_2026"},
        )
        for chunk, vec in zip(chunks, vectores)
    ]
    # Subir en lotes de 50 — un upsert de 110 × 1536 floats se pasa del timeout default
    BATCH = 50
    for i in range(0, len(points), BATCH):
        qdrant.upsert(collection_name=COLLECTION, points=points[i : i + BATCH])
        print(f"   subidos {min(i + BATCH, len(points))}/{len(points)}")

    info = qdrant.get_collection(COLLECTION)
    print(f"\n✅ Listo. Points en '{COLLECTION}': {info.points_count}")
    print("   Próximo paso: uvicorn rag.apprag_pro.app:app --reload --port 8000")


if __name__ == "__main__":
    main()
