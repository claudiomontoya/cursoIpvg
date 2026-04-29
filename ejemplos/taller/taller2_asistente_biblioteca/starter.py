"""
╔══════════════════════════════════════════════════════════════════╗
║  TALLER 2 · Asistente de Biblioteca con Tools                    ║
║  Starter · Completá los # TODO en orden                          ║
╚══════════════════════════════════════════════════════════════════╝

Integra: tool calling · JSON Schema · dispatch · estado en memoria
Tiempo estimado: 60 - 75 min

Lee el README.md antes de empezar.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

# La base de datos mock está en biblioteca_db.py — NO la modifiques.
from biblioteca_db import LIBROS, RESERVAS

load_dotenv()
client = OpenAI()

MODELO = "gpt-4o-mini"
ESTUDIANTE_DEFAULT = "ana.perez"


# ═══════════════════════════════════════════════════════════════════
# PARTE A · Funciones Python (las que el modelo podrá invocar)
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# TODO 1 · buscar_libro
# ───────────────────────────────────────────────────────────────────
# Debe:
#   - Recorrer LIBROS y filtrar los que contienen `titulo_parcial`
#     en el título (case-insensitive).
#   - Devolver una lista de diccionarios (id, titulo, autor, disponibles).
#   - Si no hay matches, devolver lista vacía.
#
# Ejemplo:
#   buscar_libro("python")
#   → [{"id": 2, "titulo": "Fluent Python", ...},
#      {"id": 8, "titulo": "Effective Python", ...}]
# ═══════════════════════════════════════════════════════════════════
def buscar_libro(titulo_parcial: str) -> list:
    # TU CÓDIGO AQUÍ
    pass


# ───────────────────────────────────────────────────────────────────
# TODO 2 · reservar_libro
# ───────────────────────────────────────────────────────────────────
# Debe manejar 3 casos:
#   1. libro_id no existe en LIBROS → {"error": "libro no encontrado"}
#   2. LIBROS[libro_id]["disponibles"] == 0 → {"error": "sin stock"}
#   3. OK → decrementar disponibles, agregar a RESERVAS[estudiante],
#           devolver {"ok": True, "libro": titulo, "restantes": N}
# ═══════════════════════════════════════════════════════════════════
def reservar_libro(libro_id: int, estudiante: str) -> dict:
    # TU CÓDIGO AQUÍ
    pass


# ───────────────────────────────────────────────────────────────────
# TODO 3 · listar_mis_reservas
# ───────────────────────────────────────────────────────────────────
# Debe devolver la lista de libros reservados por `estudiante`.
# Cada libro debe tener id, titulo, autor.
# Si el estudiante no tiene reservas, devolver lista vacía.
# ═══════════════════════════════════════════════════════════════════
def listar_mis_reservas(estudiante: str) -> list:
    # TU CÓDIGO AQUÍ
    pass


# ═══════════════════════════════════════════════════════════════════
# PARTE B · Definición de tools (JSON Schema)
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# TODO 4 · Completar las 3 definiciones de tools
# ───────────────────────────────────────────────────────────────────
# Formato:
#   {
#       "type": "function",
#       "function": {
#           "name": "nombre_fn",
#           "description": "qué hace (el modelo lee esto)",
#           "parameters": {
#               "type": "object",
#               "properties": { ... },
#               "required": [ ... ]
#           }
#       }
#   }
#
# 💡 La DESCRIPCIÓN es crítica: el modelo decide si llamar la tool
#    según lo que dice acá. Sé clara.
# ═══════════════════════════════════════════════════════════════════
tools = [
    {
        "type": "function",
        "function": {
            "name": "buscar_libro",
            "description": "TU DESCRIPCIÓN",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo_parcial": {
                        "type": "string",
                        "description": "Texto a buscar en el título del libro"
                    }
                },
                "required": ["titulo_parcial"],
            },
        },
    },
    # TODO: agregar reservar_libro
    # TODO: agregar listar_mis_reservas
]


# ═══════════════════════════════════════════════════════════════════
# PARTE C · Dispatcher y loop del agente
# ═══════════════════════════════════════════════════════════════════

def ejecutar_tool(nombre: str, args: dict) -> dict:
    """Dispatcher: según el nombre, llama a la función Python correcta."""
    if nombre == "buscar_libro":
        return {"resultados": buscar_libro(**args)}
    elif nombre == "reservar_libro":
        return reservar_libro(**args)
    elif nombre == "listar_mis_reservas":
        return {"reservas": listar_mis_reservas(**args)}
    return {"error": f"tool desconocida: {nombre}"}


# ───────────────────────────────────────────────────────────────────
# TODO 5 · chat_agente: loop completo
# ───────────────────────────────────────────────────────────────────
# Cómo funciona el loop:
#   1. Construir el historial con el system prompt + el mensaje del usuario.
#   2. Llamar al modelo con `tools=tools`.
#   3. Si la respuesta tiene tool_calls:
#        - Para cada tool_call:
#           * Parsear args con json.loads(tool_call.function.arguments)
#           * Ejecutar con ejecutar_tool(nombre, args)
#           * Appendear la RESPUESTA DEL MODELO al historial (msg)
#           * Appendear un mensaje role="tool" con el resultado
#        - Volver a llamar al modelo con el historial actualizado
#        - Repetir hasta que la respuesta NO tenga tool_calls
#   4. Devolver el contenido de la respuesta final.
#
# 💡 Mirá el ejemplo 4 — el patrón es casi el mismo, pero en un loop.
# ═══════════════════════════════════════════════════════════════════
def chat_agente(pregunta_usuario: str, estudiante: str) -> str:
    # System prompt sugerido (podés mejorarlo):
    system_prompt = f"""Eres el asistente de la biblioteca IPVG.
El usuario actual se llama '{estudiante}'. Usalo cuando llames a tools que piden un estudiante.
Usa las tools disponibles para buscar, reservar y listar. Sé conciso y amable."""

    historial = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": pregunta_usuario},
    ]

    # TODO 5.1: Bucle que llama al modelo y maneja tool_calls
    # while True:
    #     resp = client.chat.completions.create(...)
    #     msg = resp.choices[0].message
    #     if not msg.tool_calls:
    #         return msg.content   # respuesta final
    #     # ... ejecutar tools y appendear al historial
    pass


def main():
    print("📚 Asistente de Biblioteca IPVG")
    print("   (escribí 'salir' para terminar)\n")

    estudiante = input("Tu nombre de usuario: ").strip() or ESTUDIANTE_DEFAULT
    print()

    while True:
        try:
            user_input = input(f"👤 {estudiante}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() == "salir":
            break

        respuesta = chat_agente(user_input, estudiante)
        print(f"🤖: {respuesta}\n")

    print("\n👋 ¡Hasta la próxima!")


if __name__ == "__main__":
    main()
