"""
app.py — Chatbot web que gestiona el carrito por chat usando MCP + Agents SDK.

Pipeline por cada turno:
    user → OpenAI Agents SDK → MCP (tienda-ipvg en :9001) → MongoDB → cart update

El endpoint /api/chat devuelve { respuesta, tools, carrito }. El frontend usa
`carrito` para refrescar el panel de la derecha tras cada turno (el LLM no
maneja la UI, solo la lógica).

Antes de correr:
    Terminal 1:  python mcp/api_mcp/mcp_server.py
    Terminal 2:  cd mcp/api_mcp && uvicorn app:app --port 8050
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

# Necesitamos importar db.py de ../api/ para consultar el carrito directo (sin pasar por MCP)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
import db

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:9001/mcp")
CHAT_MODEL = "gpt-4.1"

INSTRUCCIONES = """
Sos el asistente de compras de la Tienda IPVG. Atendés a UN solo usuario
(usuario_demo) en una conversación natural en español chileno.

Tenés tools MCP para:
  - buscar_productos(query, categoria)
  - ver_carrito()
  - agregar_al_carrito(producto_id, cantidad)
  - actualizar_cantidad(producto_id, cantidad)
  - quitar_del_carrito(producto_id)
  - vaciar_carrito()
  - finalizar_compra()

Reglas:
  · Para AGREGAR algo: SIEMPRE `buscar_productos` primero para obtener el
    `producto_id` correcto. Nunca inventes IDs.
  · Si el usuario menciona algo ambiguo ("agregame un café"), buscá y, si hay
    varias opciones, listalas y preguntá cuál.
  · Antes de `finalizar_compra` confirmá el contenido y el total con el usuario.
  · Si el carrito está vacío y el usuario pide finalizar, decilo.
  · Cuando respondas en texto, mencioná los nombres reales de los productos y
    sus precios. No expongas los IDs internos al usuario.
""".strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with MCPServerStreamableHttp(
        name="tienda-ipvg",
        params={"url": MCP_URL},
    ) as mcp_server:
        app.state.agent = Agent(
            name="AsistenteTienda",
            model=CHAT_MODEL,
            instructions=INSTRUCCIONES,
            mcp_servers=[mcp_server],
        )
        # Historial de conversación por proceso (demo single-user)
        app.state.historial: list = []
        yield


app = FastAPI(title="Tienda IPVG · Chat + MCP", lifespan=lifespan)
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


# ---------- Extracción de tools invocadas desde el RunResult ----------

def extraer_tools(result) -> list[dict]:
    invocadas: dict[str, dict] = {}
    for item in result.new_items:
        tipo = item.__class__.__name__
        if tipo == "ToolCallItem":
            raw = getattr(item, "raw_item", None)
            if raw is not None:
                args = getattr(raw, "arguments", "{}")
                if isinstance(args, str):
                    import json as _j
                    try: args = _j.loads(args)
                    except Exception: args = {"raw": args}
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
                invocadas[call_id]["resultado_preview"] = str(output)[:240]
    return list(invocadas.values())


# ---------- API ----------

class ChatRequest(BaseModel):
    pregunta: str


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    try:
        # Usar el historial para que el agente recuerde turnos previos
        app.state.historial.append({"role": "user", "content": req.pregunta})
        result = await Runner.run(app.state.agent, app.state.historial)
        # Persistir el siguiente turno usando los items que produjo el run
        app.state.historial = result.to_input_list()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Error con MCP/OpenAI. "
                f"¿Está corriendo `python mcp/api_mcp/mcp_server.py` y MongoDB? · {e}"
            ),
        )

    # Consulta el carrito DIRECTO a Mongo para el panel lateral
    carrito = db.carrito_resumen(db.USUARIO_DEMO)

    return {
        "respuesta": result.final_output or "",
        "tools": extraer_tools(result),
        "carrito": carrito,
    }


@app.post("/api/reset")
def reset():
    """Borra el historial de la conversación (no toca el carrito)."""
    app.state.historial = []
    return {"ok": True}


@app.get("/api/carrito")
def carrito_actual():
    return db.carrito_resumen(db.USUARIO_DEMO)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
