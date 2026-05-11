"""
05 · Búsqueda por similitud
---------------------------
La pregunta del usuario se embebe (mismo modelo que la ingesta) y Qdrant devuelve
los k vectores más cercanos en la collection. El `score` es la similitud coseno:
1.0 perfecto, 0.0 sin relación.

HNSW (Hierarchical Navigable Small World) hace esta búsqueda en milisegundos sobre
millones de vectores — sin recorrer todo el índice.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

load_dotenv()
openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

COLLECTION = "curso_ipvg"


def embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model="text-embedding-3-small", input=texto)
    return r.data[0].embedding


pregunta = "¿Cómo se reduce el tamaño en memoria de un modelo grande?"
vector_pregunta = embed(pregunta)

resultados = qdrant.query_points(
    collection_name=COLLECTION,
    query=vector_pregunta,
    limit=3,
    with_payload=True,
).points

print(f"Pregunta: {pregunta}\n")
print("Top 3 resultados por similitud:")
for i, r in enumerate(resultados, 1):
    print(f"\n[{i}] score={r.score:.3f}")
    print(f"    {r.payload['texto']}")
