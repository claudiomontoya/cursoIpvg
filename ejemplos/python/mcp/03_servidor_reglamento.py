"""
03 · Servidor MCP del Reglamento
--------------------------------
Server MCP que expone el RAG sobre el reglamento como UNA tool:
    buscar_reglamento(pregunta: str) -> str

Reutiliza la collection `reglamento_ipvg_pro` (creada en rag/apprag_pro/ingestar.py).
Cualquier cliente MCP (Claude Desktop, Cursor, este curso…) puede pedirle al server
que busque en el reglamento sin saber nada de Qdrant ni cross-encoders.

Para usarlo desde Claude Desktop, agregar a `claude_desktop_config.json`:

    {
      "mcpServers": {
        "reglamento": {
          "command": "python",
          "args": ["/ruta/absoluta/a/ejemplos/python/mcp/03_servidor_reglamento.py"]
        }
      }
    }
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")

COLLECTION = "reglamento_ipvg_pro"
openai_client = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    timeout=60,
)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

mcp = FastMCP("reglamento-ipvg")


def _embed(texto: str) -> list[float]:
    r = openai_client.embeddings.create(model="text-embedding-3-small", input=texto)
    return r.data[0].embedding


@mcp.tool()
def buscar_reglamento(pregunta: str) -> str:
    """Busca en el Reglamento Académico 2026 del IPVG y devuelve los 3 fragmentos
    más relevantes (con su artículo, título y página). Útil para responder dudas
    sobre matrícula, evaluación, baja académica, titulación, derechos del
    estudiante, etc.
    """
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
        encabezado = " · ".join(
            x for x in [c.payload.get("articulo"), c.payload.get("titulo_seccion"), f"pág. {c.payload['pagina']}"] if x
        )
        bloques.append(f"[{encabezado}]\n{c.payload['texto']}")
    return "\n\n".join(bloques)


if __name__ == "__main__":
    mcp.run()  # stdio
