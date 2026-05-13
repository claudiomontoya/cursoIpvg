"""
webapp_tool/app.py — Chatbot web con TOOLS NATIVAS de OpenAI (sin MCP)
----------------------------------------------------------------------
La app define las tools inline y maneja el loop de tool calling a mano:
    user → OpenAI → ¿tool_calls? → ejecutar localmente → OpenAI → respuesta

Mismas dos tools que la webapp_mcp/:
    · hora_actual()
    · buscar_reglamento(pregunta)

Correr:
    uvicorn mcp.webapp_tool.app:app --reload --port 8010
"""

import json
import os
from datetime import datetime
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
CHAT_MODEL = "gpt-4.1"

openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    timeout=60,
)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


# ---------- Definición de tools (formato OpenAI) ----------

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "hora_actual",
            "description": "Devuelve la hora actual del servidor en formato ISO 8601.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_reglamento",
            "description": (
                "Busca en el Reglamento Académico 2026 del IPVG y devuelve los 3 fragmentos "
                "más relevantes (con artículo, título de sección y página)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pregunta": {
                        "type": "string",
                        "description": "Pregunta en lenguaje natural sobre el reglamento.",
                    }
                },
                "required": ["pregunta"],
            },
        },
    },
]


# ---------- Implementación de las tools ----------

def _embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model="text-embedding-3-small", input=texto)
    return r.data[0].embedding


def tool_hora_actual() -> str:
    return datetime.now().isoformat(timespec="seconds")


def tool_buscar_reglamento(pregunta: str) -> str:
    candidatos = qdrant.query_points(
        collection_name=COLLECTION,
        query=_embed(pregunta),
        limit=10,
        with_payload=True,
    ).points
    pares = [(pregunta, c.payload["texto"]) for c in candidatos]
    scores = reranker.predict(pares)
    top = sorted(zip(scores, candidatos), key=lambda x: x[0], reverse=True)[:3]

    bloques = []
    for score, c in top:
        enc = " · ".join(
            x for x in [c.payload.get("articulo"), c.payload.get("titulo_seccion"), f"pág. {c.payload['pagina']}"] if x
        )
        bloques.append(f"[{enc}]\n{c.payload['texto']}")
    return "\n\n".join(bloques)


DISPATCH = {
    "hora_actual": lambda args: tool_hora_actual(),
    "buscar_reglamento": lambda args: tool_buscar_reglamento(args["pregunta"]),
}


# ---------- Chat loop con tool calling ----------

SYSTEM = (
    "Eres un asistente del IPVG. Tenés DOS herramientas: `hora_actual` y "
    "`buscar_reglamento`. Usá `buscar_reglamento` cuando el estudiante pregunte "
    "algo sobre el reglamento académico. Citá el artículo y la página en la respuesta. "
    "Si la pregunta no necesita ninguna tool, respondé directamente."
)


def chat(pregunta: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": pregunta},
    ]
    tools_invocadas: list[dict] = []

    # Loop hasta que el modelo NO pida más tools
    for _ in range(5):
        r = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            temperature=0.2,
        )
        msg = r.choices[0].message
        if not msg.tool_calls:
            return {"respuesta": msg.content, "tools": tools_invocadas}

        # Anotar el mensaje del assistant con sus tool_calls
        messages.append(msg.model_dump(exclude_unset=True))

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            resultado = DISPATCH[tc.function.name](args)
            tools_invocadas.append(
                {"nombre": tc.function.name, "args": args, "resultado_preview": resultado[:300]}
            )
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": resultado}
            )

    return {"respuesta": "Demasiadas vueltas en el loop de tools.", "tools": tools_invocadas}


# ---------- API ----------

class ChatRequest(BaseModel):
    pregunta: str


class ToolInvocada(BaseModel):
    nombre: str
    args: dict
    resultado_preview: str


class ChatResponse(BaseModel):
    respuesta: str
    tools: list[ToolInvocada]


app = FastAPI(title="Chatbot con TOOLS nativas · IPVG")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.post("/api/chat", response_model=ChatResponse)
def api_chat(req: ChatRequest) -> ChatResponse:
    data = chat(req.pregunta)
    return ChatResponse(**data)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
