"""
apprag_pro/app.py — Versión profesional del asistente del Reglamento.

Diferencias con apprag/:
  · Collection `reglamento_ipvg_pro` (chunks por artículo, no por chars)
  · La respuesta del LLM cita "Art. 37º · pág. 9", no solo la página
  · Las fuentes traen título de sección + artículo + página
  · System prompt mejorado: pide al modelo citar el número de artículo

Antes de levantar la app: `python rag/apprag_pro/ingestar.py`

Correr:
    uvicorn rag.apprag_pro.app:app --reload --port 8000
    # abrir http://localhost:8000
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

COLLECTION = "reglamento_ipvg_pro"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-nano"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
TOP_K = 12
TOP_N = 4

openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)
reranker = CrossEncoder(RERANK_MODEL)

app = FastAPI(title="RAG Pro · Reglamento Académico IPVG 2026")

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
            "articulo": c.payload.get("articulo", ""),
            "titulo_seccion": c.payload.get("titulo_seccion", ""),
            "score": float(score),
        }
        for score, c in reordenados[:TOP_N]
    ]


def responder(pregunta: str, fuentes: list[dict]) -> str:
    bloques = []
    for f in fuentes:
        encabezado = " · ".join(
            x for x in [f["articulo"], f["titulo_seccion"], f"pág. {f['pagina']}"] if x
        )
        bloques.append(f"[{encabezado}]\n{f['texto']}")
    contexto = "\n\n".join(bloques)

    r = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un asistente del Reglamento Académico 2026 del IPVG. "
                    "Responde SOLO con la información del contexto entregado. "
                    "Cita la fuente al final de cada afirmación usando el formato "
                    "'(Art. NN, pág. P)' cuando exista el artículo, o '(pág. P)' si no. "
                    "Si la pregunta no se puede responder con el contexto, di: "
                    "'No encuentro esa información en el reglamento.'"
                ),
            },
            {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"},
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
    articulo: str
    titulo_seccion: str
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
