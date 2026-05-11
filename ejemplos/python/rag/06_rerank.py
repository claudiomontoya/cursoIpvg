"""
06 · Rerank con cross-encoder
-----------------------------
El embedding de la pregunta y el del documento se calculan por separado
(bi-encoder) → es muy rápido pero pierde precisión: dos textos "parecidos"
en vocabulario pueden no responder a la pregunta.

Un *cross-encoder* recibe (pregunta, candidato) JUNTOS y produce un score de
relevancia. Es ~100× más lento, pero clavado para reordenar los top-k que
salieron de Qdrant.

Estrategia clásica:
    pregunta → top-20 con Qdrant (rápido) → rerank → top-3 (preciso) → LLM

Modelo: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~80 MB, corre en CPU).
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder

load_dotenv()
openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

COLLECTION = "curso_ipvg"
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model="text-embedding-3-small", input=texto)
    return r.data[0].embedding


pregunta = "¿Qué hace exactamente un re-ranker?"

# Paso 1: recall amplio con Qdrant (top-10)
candidatos = qdrant.query_points(
    collection_name=COLLECTION,
    query=embed(pregunta),
    limit=10,
    with_payload=True,
).points

print("Top antes del rerank (orden por similitud vectorial):")
for i, c in enumerate(candidatos[:5], 1):
    print(f"  [{i}] {c.score:.3f}  {c.payload['texto'][:70]}…")

# Paso 2: cross-encoder reordena
pares = [(pregunta, c.payload["texto"]) for c in candidatos]
scores = reranker.predict(pares)
reordenados = sorted(zip(scores, candidatos), key=lambda x: x[0], reverse=True)

print("\nTop después del rerank (orden por relevancia cross-encoder):")
for i, (score, c) in enumerate(reordenados[:5], 1):
    print(f"  [{i}] {score:+.2f}  {c.payload['texto'][:70]}…")
