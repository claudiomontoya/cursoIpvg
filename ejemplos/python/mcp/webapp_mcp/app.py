"""
webapp_mcp/app.py — Chatbot web que usa MCP como puente a las tools
-------------------------------------------------------------------
La app NO define tools localmente. Las consume de un servidor MCP externo
(mcp_server.py) vía streamable-http. Esto es la gracia de MCP: el chatbot
no sabe NADA de Qdrant, embeddings ni cross-encoder. Solo sabe que existe
un server MCP que le ofrece tools.

Flujo por cada pregunta:
    1. Conectar al MCP server → listar tools
    2. Traducir tools MCP → schema OpenAI
    3. Mandar a OpenAI con esas tools
    4. Si pide tool_calls → invocarlas vía session.call_tool()
    5. Reenviar resultado a OpenAI → respuesta final

Antes de correr esta app:
    Terminal 1:  python mcp/webapp_mcp/mcp_server.py
    Terminal 2:  uvicorn mcp.webapp_mcp.app:app --reload --port 8020
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:9000/mcp")
CHAT_MODEL = "gpt-4.1"

openai_client = OpenAI()

SYSTEM = (
    "Eres un asistente del IPVG. Te conectas a un servidor MCP que te ofrece tools "
    "para responder preguntas sobre el reglamento y para consultar la hora. "
    "Cuando uses `buscar_reglamento`, citá el artículo y la página en la respuesta. "
    "Si la pregunta no necesita ninguna tool, respondé directamente."
)


def _mcp_tool_to_openai(t) -> dict:
    """Traduce el schema MCP de una tool al schema que espera OpenAI."""
    return {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema or {"type": "object", "properties": {}},
        },
    }


async def chat_via_mcp(pregunta: str) -> dict:
    """Loop de tool calling. Abre una sesión MCP por request (para didáctica;
    en producción conviene mantener la sesión viva como singleton)."""
    tools_invocadas: list[dict] = []

    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_mcp = (await session.list_tools()).tools
            tools_openai = [_mcp_tool_to_openai(t) for t in tools_mcp]

            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": pregunta},
            ]

            for _ in range(5):
                r = openai_client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=messages,
                    tools=tools_openai,
                    temperature=0.2,
                )
                msg = r.choices[0].message
                if not msg.tool_calls:
                    return {"respuesta": msg.content, "tools": tools_invocadas}

                messages.append(msg.model_dump(exclude_unset=True))
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments or "{}")
                    # ¡Acá vive la diferencia!  La tool se invoca vía MCP, no localmente:
                    resultado = await session.call_tool(tc.function.name, args)
                    texto = resultado.content[0].text if resultado.content else ""
                    tools_invocadas.append(
                        {"nombre": tc.function.name, "args": args, "resultado_preview": texto[:300]}
                    )
                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": texto}
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


app = FastAPI(title="Chatbot con MCP · IPVG")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest) -> ChatResponse:
    try:
        data = await chat_via_mcp(req.pregunta)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"No pude hablar con el MCP server en {MCP_URL}. "
                f"¿Está corriendo `python mcp/webapp_mcp/mcp_server.py`? · {e}"
            ),
        )
    return ChatResponse(**data)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
