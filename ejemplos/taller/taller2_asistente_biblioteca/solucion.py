"""
╔══════════════════════════════════════════════════════════════════╗
║  TALLER 2 · Asistente de Biblioteca · SOLUCIÓN DOCENTE           ║
╚══════════════════════════════════════════════════════════════════╝

Versión que cumple TODOS los requisitos + los 3 bonus:
  - 4ª tool: devolver_libro
  - Structured outputs opcionales (comentados, ver al final)
  - Tool calls paralelas

No la distribuyas antes de que los alumnos lo intenten.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

from biblioteca_db import LIBROS, RESERVAS

load_dotenv()
client = OpenAI()

MODELO = "gpt-4o-mini"
ESTUDIANTE_DEFAULT = "ana.perez"


# ═══════════════════════════════════════════════════════════════════
# PARTE A · Funciones Python
# ═══════════════════════════════════════════════════════════════════

def buscar_libro(titulo_parcial: str) -> list:
    """Busca libros cuyo título contiene el texto (case-insensitive)."""
    needle = titulo_parcial.lower()
    matches = []
    for libro in LIBROS.values():
        if needle in libro["titulo"].lower():
            matches.append({
                "id": libro["id"],
                "titulo": libro["titulo"],
                "autor": libro["autor"],
                "disponibles": libro["disponibles"],
            })
    return matches


def reservar_libro(libro_id: int, estudiante: str) -> dict:
    """Reserva un libro para un estudiante. Maneja casos de error."""
    if libro_id not in LIBROS:
        return {"error": f"libro con id {libro_id} no encontrado"}

    libro = LIBROS[libro_id]
    if libro["disponibles"] == 0:
        return {
            "error": "sin stock",
            "libro": libro["titulo"],
            "disponibles": 0,
        }

    # OK: decrementar y registrar
    libro["disponibles"] -= 1
    RESERVAS.setdefault(estudiante, []).append(libro_id)

    return {
        "ok": True,
        "libro_id": libro_id,
        "libro": libro["titulo"],
        "restantes": libro["disponibles"],
        "estudiante": estudiante,
    }


def listar_mis_reservas(estudiante: str) -> list:
    """Devuelve los libros reservados por el estudiante."""
    ids = RESERVAS.get(estudiante, [])
    return [
        {"id": LIBROS[i]["id"], "titulo": LIBROS[i]["titulo"], "autor": LIBROS[i]["autor"]}
        for i in ids
    ]


def devolver_libro(libro_id: int, estudiante: str) -> dict:
    """BONUS · 4ª tool: devuelve un libro (incrementa disponibles)."""
    if libro_id not in LIBROS:
        return {"error": f"libro {libro_id} no existe"}

    reservas = RESERVAS.get(estudiante, [])
    if libro_id not in reservas:
        return {"error": f"no tenés reservado el libro {libro_id}"}

    reservas.remove(libro_id)
    LIBROS[libro_id]["disponibles"] += 1

    return {
        "ok": True,
        "libro": LIBROS[libro_id]["titulo"],
        "disponibles": LIBROS[libro_id]["disponibles"],
    }


# ═══════════════════════════════════════════════════════════════════
# PARTE B · Tools (JSON Schema)
# ═══════════════════════════════════════════════════════════════════

tools = [
    {
        "type": "function",
        "function": {
            "name": "buscar_libro",
            "description": "Busca libros en la biblioteca por texto parcial del título (case-insensitive). Devuelve lista de matches con id, título, autor y ejemplares disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo_parcial": {
                        "type": "string",
                        "description": "Texto a buscar en el título del libro (ej: 'python', 'clean', 'design')",
                    },
                },
                "required": ["titulo_parcial"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reservar_libro",
            "description": "Reserva un libro para un estudiante. Falla si el libro no existe o no hay ejemplares disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "libro_id": {
                        "type": "integer",
                        "description": "ID del libro a reservar (obtenido de buscar_libro)",
                    },
                    "estudiante": {
                        "type": "string",
                        "description": "Username del estudiante que reserva",
                    },
                },
                "required": ["libro_id", "estudiante"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_mis_reservas",
            "description": "Lista todos los libros actualmente reservados por el estudiante.",
            "parameters": {
                "type": "object",
                "properties": {
                    "estudiante": {
                        "type": "string",
                        "description": "Username del estudiante",
                    },
                },
                "required": ["estudiante"],
            },
        },
    },
    # BONUS · 4ª tool
    {
        "type": "function",
        "function": {
            "name": "devolver_libro",
            "description": "Devuelve un libro previamente reservado por el estudiante. Incrementa los ejemplares disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "libro_id": {"type": "integer", "description": "ID del libro a devolver"},
                    "estudiante": {"type": "string", "description": "Username del estudiante"},
                },
                "required": ["libro_id", "estudiante"],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════
# PARTE C · Dispatcher y loop del agente
# ═══════════════════════════════════════════════════════════════════

def ejecutar_tool(nombre: str, args: dict) -> dict:
    """Dispatch: nombre de tool → función Python real."""
    dispatch = {
        "buscar_libro":         lambda a: {"resultados": buscar_libro(**a)},
        "reservar_libro":       lambda a: reservar_libro(**a),
        "listar_mis_reservas":  lambda a: {"reservas": listar_mis_reservas(**a)},
        "devolver_libro":       lambda a: devolver_libro(**a),
    }
    fn = dispatch.get(nombre)
    if fn is None:
        return {"error": f"tool desconocida: {nombre}"}
    try:
        return fn(args)
    except Exception as e:
        return {"error": str(e)}


def chat_agente(pregunta_usuario: str, estudiante: str) -> str:
    """Loop completo del agente con tool calling."""
    system_prompt = f"""Eres el asistente de la biblioteca IPVG.
El usuario actual se llama '{estudiante}'. Cuando llames a tools que requieren un estudiante, usá ese username.
Tenés acceso a 4 tools para buscar, reservar, listar y devolver libros.
Sé conciso y amable. Confirma acciones antes de ejecutarlas si hay ambigüedad."""

    historial = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": pregunta_usuario},
    ]

    # Loop: seguimos mientras el modelo siga pidiendo tools
    max_iteraciones = 5   # safety — evitar loops infinitos
    for _ in range(max_iteraciones):
        resp = client.chat.completions.create(
            model=MODELO,
            messages=historial,
            tools=tools,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return msg.content or "(sin respuesta)"

        # Appendear la respuesta del modelo (con los tool_calls) al historial
        historial.append(msg)

        # Ejecutar cada tool pedida (soporta paralelo)
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            resultado = ejecutar_tool(tool_call.function.name, args)

            print(f"   🔧 {tool_call.function.name}({args}) → {resultado}")

            historial.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(resultado, ensure_ascii=False),
            })

    return "⚠️  Se alcanzó el máximo de iteraciones sin respuesta final."


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
        print(f"\n🤖: {respuesta}\n")

    print("\n👋 ¡Hasta la próxima!")


if __name__ == "__main__":
    main()


# =====================================================================
# BONUS · Structured outputs con Pydantic
# =====================================================================
# Si quisieras que la respuesta de reservar_libro venga con un formato
# garantizado, podrías hacer una segunda llamada tipo:
#
#   from pydantic import BaseModel
#   class ConfirmacionReserva(BaseModel):
#       mensaje: str
#       libro_reservado: str
#       ejemplares_restantes: int
#
#   resp = client.beta.chat.completions.parse(
#       model=MODELO,
#       messages=historial,
#       response_format=ConfirmacionReserva,
#   )
#   confirmacion: ConfirmacionReserva = resp.choices[0].message.parsed
# =====================================================================
