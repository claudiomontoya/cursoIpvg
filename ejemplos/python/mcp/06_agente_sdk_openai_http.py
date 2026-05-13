"""
06 · Agente con OpenAI Agents SDK + MCP streamable-http
-------------------------------------------------------
Mismo objetivo que 04/05 (agente IA usando tools por MCP), pero con DOS diferencias:

  1. Usa la librería oficial **openai-agents** — abstrae todo el loop de
     tool calling y manejo de sesión MCP. Vos describís el agente y corrés.
  2. Habla con el server MCP por **streamable-http** (no stdio).

Ventaja: 30 líneas en vez de 80, y la misma webapp/server se puede consumir
desde Cursor, Claude Desktop o este script — todos a la vez.

Antes de correr este script, abrí OTRA terminal y arrancá el server HTTP:

    cd ejemplos/python
    python mcp/webapp_mcp/mcp_server.py    # corre en http://localhost:9000/mcp

Después, en esta terminal:

    python mcp/06_agente_sdk_openai_http.py
    python mcp/06_agente_sdk_openai_http.py "¿qué nota necesito para aprobar?"
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")

MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:9000/mcp")

INSTRUCCIONES = (
    "Sos un asistente del IPVG. Tenés tools MCP para responder sobre el "
    "Reglamento Académico 2026 y para consultar la hora. Usá `buscar_reglamento` "
    "siempre que la pregunta sea sobre normativa académica y citá artículo + página. "
    "Si la pregunta no necesita ninguna tool, respondé directamente."
)


async def main() -> None:
    preguntas = (
        [sys.argv[1]]
        if len(sys.argv) > 1
        else [
            "¿Qué hora es?",
            "¿Cuáles son las causales de baja académica?",
            "¿Cómo funciona la suspensión de estudios?",
        ]
    )

    # `MCPServerStreamableHttp` abre y cierra la sesión MCP automáticamente
    async with MCPServerStreamableHttp(
        name="ipvg-tools",
        params={"url": MCP_URL},
    ) as mcp_server:

        # El Agent se construye una vez; el Runner lo reutiliza
        agent = Agent(
            name="AsistenteIPVG",
            model="gpt-4.1",
            instructions=INSTRUCCIONES,
            mcp_servers=[mcp_server],  # ← acá vive la magia: el SDK descubre tools solo
        )

        print(f"🤖 Agente conectado a MCP server en {MCP_URL}\n")

        for i, pregunta in enumerate(preguntas, 1):
            print(f"────────  Pregunta {i}/{len(preguntas)}  ────────")
            print(f"👤 {pregunta}\n")
            resultado = await Runner.run(agent, pregunta)
            print(f"🤖 {resultado.final_output}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   ¿Está corriendo el server? → python mcp/webapp_mcp/mcp_server.py")
        sys.exit(1)
