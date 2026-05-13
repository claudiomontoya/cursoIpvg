"""
webapp_mcp/mcp_server.py — Servidor MCP con dos tools
-----------------------------------------------------
Mismas dos tools que webapp_tool/, pero acá viven dentro de un MCP server.
Cualquier cliente MCP (esta webapp, Claude Desktop, Cursor…) puede usarlas
sin saber nada de Qdrant.

Transport: streamable-http en http://localhost:9000/mcp

Correr (terminal aparte):
    python mcp/webapp_mcp/mcp_server.py
"""

import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

COLLECTION = "reglamento_ipvg_pro"
openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    timeout=60,
)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

mcp = FastMCP("ipvg-tools", host="127.0.0.1", port=9000)


@mcp.tool()
def hora_actual() -> str:
    """Devuelve la hora actual del servidor en formato ISO 8601."""
    return datetime.now().isoformat(timespec="seconds")


@mcp.tool()
def buscar_reglamento(pregunta: str) -> str:
    """Busca en el Reglamento Académico 2026 del IPVG y devuelve los 3 fragmentos
    más relevantes (artículo + título de sección + página).
    """
    r = openai_client.embeddings.create(model="text-embedding-3-small", input=pregunta)
    vec = r.data[0].embedding

    candidatos = qdrant.query_points(
        collection_name=COLLECTION,
        query=vec,
        limit=10,
        with_payload=True,
    ).points
    pares = [(pregunta, c.payload["texto"]) for c in candidatos]
    scores = reranker.predict(pares)
    top = sorted(zip(scores, candidatos), key=lambda x: x[0], reverse=True)[:3]

    bloques = []
    for _, c in top:
        enc = " · ".join(
            x for x in [c.payload.get("articulo"), c.payload.get("titulo_seccion"), f"pág. {c.payload['pagina']}"] if x
        )
        bloques.append(f"[{enc}]\n{c.payload['texto']}")
    return "\n\n".join(bloques)


if __name__ == "__main__":
    # streamable-http: HTTP transport, soporta SSE para respuestas largas y reconexión
    mcp.run(transport="streamable-http")
