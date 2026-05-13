"""
05 · Agente CLI sobre el reglamento (OpenAI + MCP stdio)
--------------------------------------------------------
Mismo patrón que `04_agente_openai_stdio.py`, pero apunta a
`03_servidor_reglamento.py` (RAG sobre reglamento.pdf).

Uso:
    python mcp/05_agente_reglamento_stdio.py "¿qué pasa si repruebo dos veces?"

Argumento → pregunta. Sin argumento → preguntas hardcoded de demo.

Esto demuestra que el MISMO patrón de "agente + MCP por stdio" sirve para
cualquier server: solo cambiás la ruta al script y, claro, el system prompt.
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
SERVIDOR = Path(__file__).parent / "03_servidor_reglamento.py"

openai_client = OpenAI()

SYSTEM = (
    "Eres un asistente del Reglamento Académico 2026 del IPVG. "
    "Tenés acceso a la tool `buscar_reglamento(pregunta)` que devuelve fragmentos "
    "relevantes con artículo, título y página. Usala SIEMPRE antes de responder. "
    "Citá el artículo y la página en tu respuesta. Si la info no está, decilo."
)


def mcp_to_openai_schema(t) -> dict:
    return {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema or {"type": "object", "properties": {}},
        },
    }


async def responder(session: ClientSession, tools_openai: list[dict], pregunta: str) -> str:
    """One-shot: pregunta → respuesta. Sin historial."""
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
            return msg.content

        messages.append(msg.model_dump(exclude_unset=True))
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"   🔧 {tc.function.name}({json.dumps(args, ensure_ascii=False)})")
            resultado = await session.call_tool(tc.function.name, args)
            texto = resultado.content[0].text if resultado.content else ""
            preview = (texto[:200] + "…") if len(texto) > 200 else texto
            print(f"      ↳ {preview.replace(chr(10), ' ')}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": texto})

    return "Loop de tools demasiado largo."


async def main() -> None:
    preguntas = (
        [sys.argv[1]]
        if len(sys.argv) > 1
        else [
            "¿Cuáles son las causales de baja académica?",
            "¿Qué pasa si suspendo mis estudios y quiero reincorporarme?",
            "¿Qué requisitos hay para iniciar el proceso de titulación?",
        ]
    )

    server_params = StdioServerParameters(command=sys.executable, args=[str(SERVIDOR)])

    print("🤖 Agente del reglamento (OpenAI + MCP stdio) — conectando…\n")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_mcp = (await session.list_tools()).tools
            tools_openai = [mcp_to_openai_schema(t) for t in tools_mcp]

            for i, pregunta in enumerate(preguntas, 1):
                print(f"────────────────  Pregunta {i}/{len(preguntas)}  ────────────────")
                print(f"👤 {pregunta}\n")
                respuesta = await responder(session, tools_openai, pregunta)
                print(f"\n🤖 {respuesta}\n")


if __name__ == "__main__":
    asyncio.run(main())
