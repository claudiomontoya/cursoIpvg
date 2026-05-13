"""
webapp_mcp_sdk/app.py — Chatbot web con OpenAI Agents SDK + MCP HTTP
--------------------------------------------------------------------
Tercera webapp de la serie comparativa:

    webapp_tool/      → OpenAI raw client + tools NATIVAS inline
    webapp_mcp/       → OpenAI raw client + MCP por streamable-http (loop manual)
    webapp_mcp_sdk/   → OpenAI **Agents SDK** + MCP por streamable-http  ← esta

Diferencia clave con webapp_mcp/: usamos `from agents import Agent, Runner` que
abstrae todo el loop de tool calling. El backend pasa de ~120 líneas a ~80, y
el patrón es el mismo que vas a usar para sistemas de N agentes con handoffs.

La conexión MCP se abre en el `lifespan` de FastAPI (una sola sesión viva para
todas las requests) — patrón correcto para producción.

Antes de correr:
    Terminal 1:  python mcp/webapp_mcp/mcp_server.py     # reutiliza el server
    Terminal 2:  cd mcp/webapp_mcp_sdk && uvicorn app:app --port 8030
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:9000/mcp")
CHAT_MODEL = "gpt-4.1"

INSTRUCCIONES = (
    "Sos un asistente del IPVG. Tenés tools MCP para el Reglamento Académico 2026 "
    "y para consultar la hora. Usá `buscar_reglamento` siempre que la pregunta sea "
    "sobre normativa académica y citá artículo + página. Si la pregunta no necesita "
    "ninguna tool, respondé directamente."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Abre la conexión MCP al arrancar el server, la mantiene viva, la cierra al apagar."""
    async with MCPServerStreamableHttp(
        name="ipvg-tools",
        params={"url": MCP_URL},
    ) as mcp_server:
        app.state.agent = Agent(
            name="AsistenteIPVG",
            model=CHAT_MODEL,
            instructions=INSTRUCCIONES,
            mcp_servers=[mcp_server],
        )
        yield


app = FastAPI(title="Chatbot con Agents SDK + MCP · IPVG", lifespan=lifespan)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------- Extracción de tools invocadas desde el RunResult ----------

def extraer_tools(result) -> list[dict]:
    """Recorre los items del Runner y devuelve cada tool_call con su output."""
    invocadas: dict[str, dict] = {}
    for item in result.new_items:
        tipo = item.__class__.__name__
        if tipo == "ToolCallItem":
            raw = getattr(item, "raw_item", None)
            if raw is not None:
                # raw es un objeto del tipo ResponseFunctionToolCall (Responses API)
                args = getattr(raw, "arguments", "{}")
                if isinstance(args, str):
                    import json as _j
                    try:
                        args = _j.loads(args)
                    except Exception:
                        args = {"raw": args}
                invocadas[raw.call_id] = {
                    "nombre": getattr(raw, "name", "?"),
                    "args": args,
                    "resultado_preview": "",
                }
        elif tipo == "ToolCallOutputItem":
            raw = getattr(item, "raw_item", None)
            call_id = raw.get("call_id") if isinstance(raw, dict) else getattr(raw, "call_id", None)
            output = getattr(item, "output", "")
            if call_id in invocadas:
                invocadas[call_id]["resultado_preview"] = str(output)[:300]
    return list(invocadas.values())


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


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest) -> ChatResponse:
    try:
        result = await Runner.run(app.state.agent, req.pregunta)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Error hablando con MCP server o LLM. "
                f"¿Está corriendo `python mcp/webapp_mcp/mcp_server.py`? · {e}"
            ),
        )
    return ChatResponse(
        respuesta=result.final_output or "",
        tools=extraer_tools(result),
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
