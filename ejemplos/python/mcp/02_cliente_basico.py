"""
02 · Cliente MCP básico
-----------------------
Lanza `01_servidor_basico.py` como subproceso, se conecta vía stdio,
descubre las tools disponibles, y las invoca.

Flujo:
    1. arrancar el servidor con subprocess (stdio)
    2. iniciar sesión MCP
    3. session.list_tools()  → catálogo de funciones
    4. session.call_tool()   → invocar una tool con argumentos
    5. parsear el resultado
"""

import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVIDOR = Path(__file__).parent / "01_servidor_basico.py"


async def main() -> None:
    # Comando que arranca el server (el cliente lo controla como subproceso)
    server_params = StdioServerParameters(
        command=sys.executable,         # python del venv actual
        args=[str(SERVIDOR)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1) handshake — descubre versión del protocolo, capabilities…
            await session.initialize()

            # 2) listar tools disponibles
            tools = await session.list_tools()
            print("🔧 Tools que expone el servidor:")
            for t in tools.tools:
                print(f"   · {t.name:14} → {t.description}")
            print()

            # 3) invocar `sumar`
            r1 = await session.call_tool("sumar", {"a": 17, "b": 25})
            print(f"sumar(17, 25)        → {r1.content[0].text}")

            # 4) invocar `hora_actual`
            r2 = await session.call_tool("hora_actual", {})
            print(f"hora_actual()        → {r2.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
