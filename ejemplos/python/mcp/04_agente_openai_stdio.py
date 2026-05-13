"""
04 · Agente CLI con OpenAI + MCP (stdio)
----------------------------------------
Chatbot interactivo en la terminal. NO hay webapp. El agente:

  1. Arranca `01_servidor_basico.py` como subproceso (stdio).
  2. Descubre las tools del server vía MCP.
  3. Las traduce al schema que espera OpenAI.
  4. Para cada pregunta del usuario:
        a. Llama a gpt-4.1 con esas tools.
        b. Si el modelo pide tool_calls → las invoca por MCP.
        c. Reenvía el resultado al modelo → respuesta final.

Es el patrón mínimo "agente IA consumiendo MCP por API". Igual que lo que harías
en producción, pero sin HTTP/UI/frameworks.

Salir: `salir` o Ctrl-D.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")

CHAT_MODEL = "gpt-4.1"
SERVIDOR = Path(__file__).parent / "01_servidor_basico.py"

openai_client = OpenAI()

SYSTEM = (
    "Eres un asistente en una terminal. Te conectas a un servidor MCP que ofrece "
    "tools (suma, hora). Usalas cuando ayuden a responder; si no, contestá directo."
)


def mcp_to_openai_schema(t) -> dict:
    """Traduce el schema de una tool MCP al formato que espera OpenAI."""
    return {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema or {"type": "object", "properties": {}},
        },
    }


async def turno(session: ClientSession, tools_openai: list[dict], historial: list[dict], pregunta: str) -> str:
    """Procesa un turno: agrega la pregunta al historial, loop de tool calls,
    devuelve la respuesta final y deja el historial listo para el próximo turno."""
    historial.append({"role": "user", "content": pregunta})

    for _ in range(5):
        r = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=historial,
            tools=tools_openai,
            temperature=0.2,
        )
        msg = r.choices[0].message

        if not msg.tool_calls:
            historial.append({"role": "assistant", "content": msg.content})
            return msg.content

        historial.append(msg.model_dump(exclude_unset=True))
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"   🔧 {tc.function.name}({json.dumps(args)})")
            resultado = await session.call_tool(tc.function.name, args)
            texto = resultado.content[0].text if resultado.content else ""
            print(f"      ↳ {texto}")
            historial.append({"role": "tool", "tool_call_id": tc.id, "content": texto})

    return "Loop de tools demasiado largo."


async def main() -> None:
    server_params = StdioServerParameters(command=sys.executable, args=[str(SERVIDOR)])

    print("🤖 Agente OpenAI + MCP (stdio) — arrancando…")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_mcp = (await session.list_tools()).tools
            tools_openai = [mcp_to_openai_schema(t) for t in tools_mcp]

            print(f"   conectado a `{session.__class__.__name__}` con {len(tools_mcp)} tools:")
            for t in tools_mcp:
                print(f"     · {t.name} — {t.description}")
            print("   escribí 'salir' para terminar.\n")

            historial: list[dict] = [{"role": "system", "content": SYSTEM}]

            while True:
                try:
                    pregunta = input("👤 ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n👋")
                    return
                if not pregunta or pregunta.lower() in {"salir", "exit", "quit"}:
                    print("👋")
                    return

                respuesta = await turno(session, tools_openai, historial, pregunta)
                print(f"🤖 {respuesta}\n")


if __name__ == "__main__":
    asyncio.run(main())
