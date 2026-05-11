"""
04 · Ingestar documentos
------------------------
Pipeline de ingesta:
    texto → chunks → embeddings → upsert en Qdrant

Cada *point* tiene:
  · id     → identificador único
  · vector → el embedding (1536 floats)
  · payload→ metadatos arbitrarios (texto original, fuente, página…)

El payload es lo que devolvemos al usuario; el vector es solo para buscar.
"""

import os
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

load_dotenv()
openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

COLLECTION = "curso_ipvg"

# "Corpus" mínimo de demo. En la práctica vendría de PDFs, Markdown, una BD…
documentos = [
    "Un token es la unidad mínima que procesa un LLM: puede ser una palabra, parte de una palabra o un signo de puntuación.",
    "El tokenizador convierte texto en IDs numéricos antes de pasarlos al modelo.",
    "Los parámetros de un modelo son los pesos aprendidos durante el entrenamiento. Llama 3 70B tiene 70 mil millones.",
    "La atención (attention) permite que cada token mire a los demás de la secuencia para decidir cuáles son relevantes.",
    "Un transformer está formado por bloques de self-attention y feed-forward apilados; típicamente 32 a 96 capas.",
    "La cuantización pasa los pesos de FP32 a INT8 o INT4 para que el modelo ocupe menos memoria.",
    "Los embeddings son vectores que representan el significado de un texto en un espacio de cientos o miles de dimensiones.",
    "RAG (Retrieval Augmented Generation) combina búsqueda vectorial con un LLM: primero recupera fragmentos relevantes, luego los pasa como contexto al modelo.",
    "Qdrant es una base de datos vectorial open-source escrita en Rust, optimizada para búsqueda por similitud con HNSW.",
    "Un re-ranker es un modelo cross-encoder que reordena los top-k resultados de la búsqueda vectorial para mejorar la precisión.",
]


def embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model="text-embedding-3-small", input=texto)
    return r.data[0].embedding


points = []
for texto in documentos:
    points.append(
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embed(texto),
            payload={"texto": texto, "fuente": "curso_ipvg/teoria"},
        )
    )

qdrant.upsert(collection_name=COLLECTION, points=points)

info = qdrant.get_collection(COLLECTION)
print(f"Ingestados {len(points)} chunks.")
print(f"Total de puntos en '{COLLECTION}': {info.points_count}")
