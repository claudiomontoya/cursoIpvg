"""
07 · RAG end-to-end
-------------------
Pipeline completo en un solo archivo:

    pregunta → embed → Qdrant top-10 → rerank → top-3 → contexto → GPT-4.1 → respuesta

Esto es la receta base de cualquier "chatbot sobre tus documentos".
Lo que cambia en sistemas reales: corpus más grande, mejor chunking, evaluación,
caché de embeddings, citas con offsets, guardrails…
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
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

COLLECTION = "curso_ipvg"
CHAT_MODEL = "gpt-4.1"


def embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model="text-embedding-3-small", input=texto)
    return r.data[0].embedding


def recuperar(pregunta: str, top_n: int = 3) -> list[str]:
    candidatos = qdrant.query_points(
        collection_name=COLLECTION,
        query=embed(pregunta),
        limit=10,
        with_payload=True,
    ).points
    pares = [(pregunta, c.payload["texto"]) for c in candidatos]
    scores = reranker.predict(pares)
    reordenados = sorted(zip(scores, candidatos), key=lambda x: x[0], reverse=True)
    return [c.payload["texto"] for _, c in reordenados[:top_n]]


def responder(pregunta: str) -> str:
    contexto = recuperar(pregunta)
    bloque_contexto = "\n".join(f"- {c}" for c in contexto)

    r = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Respondes preguntas sobre IA generativa usando SOLO el contexto entregado. "
                    "Si la respuesta no está en el contexto, di que no lo sabes."
                ),
            },
            {
                "role": "user",
                "content": f"Contexto:\n{bloque_contexto}\n\nPregunta: {pregunta}",
            },
        ],
        temperature=0.2,
    )
    return r.choices[0].message.content


pregunta = "¿Qué es RAG y para qué sirve un re-ranker?"
print(f"Pregunta: {pregunta}\n")
print(f"Respuesta:\n{responder(pregunta)}")
