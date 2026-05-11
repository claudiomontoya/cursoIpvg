"""
apprag/app.py — Webapp RAG sobre el Reglamento Académico 2026
-------------------------------------------------------------
FastAPI con una sola ruta: POST /api/search → respuesta + fuentes citadas.
Sirve además el index.html estático en /.

Antes de correr esta app hay que haber ejecutado:
    python rag/test/ingestar_reglamento.py

Correr la app:
    uvicorn rag.apprag.app:app --reload --port 8000
    # luego abrir http://localhost:8000
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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
# Se carga al arrancar el server (no en cada request)
reranker = CrossEncoder(RERANK_MODEL)

app = FastAPI(title="RAG · Reglamento Académico IPVG 2026")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------- Pipeline ----------

def embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model=EMBED_MODEL, input=texto)
    return r.data[0].embedding


def recuperar(pregunta: str) -> list[dict]:
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
                    "Responde SOLO con la información del contexto entregado. "
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


# ---------- API ----------

class SearchRequest(BaseModel):
    pregunta: str


class Fuente(BaseModel):
    texto: str
    pagina: int
    score: float


class SearchResponse(BaseModel):
    respuesta: str
    fuentes: list[Fuente]


@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    fuentes = recuperar(req.pregunta)
    respuesta = responder(req.pregunta, fuentes)
    return SearchResponse(respuesta=respuesta, fuentes=fuentes)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
