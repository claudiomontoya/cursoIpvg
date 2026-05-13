"""
01 · Servidor MCP básico
------------------------
Un servidor MCP mínimo con FastMCP. Expone DOS herramientas (tools) a cualquier
cliente MCP (Claude Desktop, Cursor, Zed, Claude Code, este curso…).

Conceptos clave:
  · MCP server  : un proceso que expone TOOLS / RESOURCES / PROMPTS
  · @mcp.tool() : decorador que registra una función como tool invocable
  · stdio       : el server lee/escribe JSON-RPC por stdin/stdout
                 (el cliente lo arranca como subproceso)

Para probarlo solo (sin cliente):
    python rag/../mcp/01_servidor_basico.py
    # queda esperando en stdin — no rompe, solo no responde

Para invocar las tools desde un cliente, ver 02_cliente_basico.py
"""

from datetime import datetime
from mcp.server.fastmcp import FastMCP

# El nombre del server aparece cuando un cliente se conecta
mcp = FastMCP("curso-ipvg-basico")


@mcp.tool()
def sumar(a: int, b: int) -> int:
    """Suma dos números enteros y devuelve el resultado."""
    return a + b


@mcp.tool()
def hora_actual() -> str:
    """Devuelve la hora actual del servidor en formato ISO 8601."""
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    # transport="stdio" es el default — JSON-RPC por stdin/stdout
    mcp.run()
