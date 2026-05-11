"""
test/buscar_reglamento.py
-------------------------
CLI interactiva sobre la collection `reglamento_ipvg`.

Pipeline en cada pregunta:
    pregunta → embed → Qdrant top-10 → rerank cross-encoder → top-3 → GPT → respuesta

La respuesta cita las páginas del PDF de donde sale el contexto.
Requiere haber corrido `ingestar_reglamento.py` antes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

COLLECTION = "reglamento_ipvg"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-nano"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
TOP_K = 10
TOP_N = 3

openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)
reranker = CrossEncoder(RERANK_MODEL)


def embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model=EMBED_MODEL, input=texto)
    return r.data[0].embedding


def recuperar(pregunta: str) -> list[dict]:
    """Devuelve top-N chunks reordenados: [{texto, pagina, score}, ...]."""
    candidatos = qdrant.query_points(
        collection_name=COLLECTION,
        query=embed(pregunta),
        limit=TOP_K,
        with_payload=True,
    ).points

    pares = [(pregunta, c.payload["texto"]) for c in candidatos]
    scores = reranker.predict(pares)
    reordenados = sorted(zip(scores, candidatos), key=lambda x: x[0], reverse=True)

    return [
        {
            "texto": c.payload["texto"],
            "pagina": c.payload["pagina"],
            "score": float(score),
        }
        for score, c in reordenados[:TOP_N]
    ]


def responder(pregunta: str, fuentes: list[dict]) -> str:
    contexto = "\n\n".join(
        f"[Página {f['pagina']}]\n{f['texto']}" for f in fuentes
    )
    r = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un asistente del Reglamento Académico 2026 del IPVG. "
                    "Responde SOLO con la información del contexto. "
                    "Cita las páginas entre paréntesis al final de cada afirmación, ej: (pág. 5). "
                    "Si la respuesta no está en el contexto, di: "
                    "'No encuentro esa información en el reglamento.'"
                ),
            },
            {
                "role": "user",
                "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}",
            },
        ],
        temperature=0.2,
    )
    return r.choices[0].message.content


def main() -> None:
    print("📚 Asistente del Reglamento Académico 2026 · IPVG")
    print("   Escribe tu pregunta o 'salir' para terminar.\n")

    while True:
        pregunta = input("❓ ").strip()
        if not pregunta or pregunta.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego 👋")
            break

        fuentes = recuperar(pregunta)
        respuesta = responder(pregunta, fuentes)

        print(f"\n🤖 {respuesta}\n")
        print("📎 Fuentes consultadas:")
        for i, f in enumerate(fuentes, 1):
            preview = f["texto"][:120].replace("\n", " ")
            print(f"   [{i}] pág. {f['pagina']} (score={f['score']:+.2f}) — {preview}…")
        print()


if __name__ == "__main__":
    main()
