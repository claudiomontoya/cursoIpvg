"""
Ejemplo 4 · Tools (function calling)
=====================================
Qué enseña:
  - Declarar herramientas con un esquema JSON
  - El modelo decide CUÁL llamar y con QUÉ argumentos
  - Tú ejecutas la función real en Python y devuelves el resultado
  - El modelo redacta la respuesta final usando ese resultado

Flujo (importante entenderlo):
  1) Mandas el prompt + las definiciones de tools
  2) El modelo responde con `tool_calls` (no responde al usuario aún)
  3) Ejecutas las funciones en Python
  4) Mandas los resultados de vuelta como mensajes role="tool"
  5) El modelo ahora sí redacta la respuesta final
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, crear_sesion

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
sesion_id = crear_sesion(conn, "ejemplo_04_tools")


# ======================================================================
# 1. Funciones reales (las ejecuta tu código, no el modelo)
# ======================================================================
def obtener_clima(ciudad: str) -> dict:
    """Mock — en la vida real consultarías una API meteorológica."""
    datos_falsos = {
        "Concepción": {"temp": 14, "estado": "lluvioso"},
        "Santiago":   {"temp": 22, "estado": "soleado"},
        "Punta Arenas": {"temp": 6, "estado": "ventoso"},
    }
    return datos_falsos.get(ciudad, {"temp": 18, "estado": "desconocido"})


def calcular(expresion: str) -> dict:
    """Evalúa una expresión aritmética simple. Solo dígitos y operadores."""
    permitidos = set("0123456789+-*/(). ")
    if not set(expresion) <= permitidos:
        return {"error": "expresión no permitida"}
    return {"resultado": eval(expresion)}   # ok porque ya validamos


# Mapa nombre → función (para despachar lo que pida el modelo)
DISPATCH = {
    "obtener_clima": obtener_clima,
    "calcular": calcular,
}


# ======================================================================
# 2. Definición de tools (esto es lo que el modelo "ve")
# ======================================================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "obtener_clima",
            "description": "Devuelve el clima actual de una ciudad chilena.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ciudad": {"type": "string", "description": "Nombre de la ciudad"}
                },
                "required": ["ciudad"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular",
            "description": "Evalúa una expresión aritmética simple.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expresion": {"type": "string", "description": "Ej: '2+2*3'"}
                },
                "required": ["expresion"],
            },
        },
    },
]


# ======================================================================
# 3. Conversación
# ======================================================================
mensajes = [
    {"role": "system", "content": "Eres un asistente que usa herramientas cuando aplican."},
    {"role": "user",   "content": "¿Qué tiempo hace en Concepción y cuánto es 15*7?"},
]

print("=" * 60)
print(" EJEMPLO 4 · Tools (function calling)")
print("=" * 60)
print(f"👤 {mensajes[-1]['content']}")

# --- Primera llamada: el modelo decide qué tools llamar ---
primera = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=mensajes,
    tools=tools,
)

mensaje_modelo = primera.choices[0].message
mensajes.append(mensaje_modelo)        # 👈 agregamos su mensaje (con tool_calls) al historial

# --- Ejecutamos cada tool_call y guardamos su resultado ---
if mensaje_modelo.tool_calls:
    for tc in mensaje_modelo.tool_calls:
        nombre = tc.function.name
        args = json.loads(tc.function.arguments)
        resultado = DISPATCH[nombre](**args)

        print(f"🔧 Tool llamada: {nombre}({args}) → {resultado}")

        # Guardamos la traza en SQLite
        conn.execute(
            "INSERT INTO tool_calls (sesion_id, herramienta, argumentos, resultado) "
            "VALUES (?, ?, ?, ?)",
            (sesion_id, nombre, json.dumps(args), json.dumps(resultado)),
        )

        # Devolvemos el resultado al modelo como mensaje role="tool"
        mensajes.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(resultado),
        })

# --- Segunda llamada: el modelo redacta la respuesta final con los resultados ---
final = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=mensajes,
)

respuesta = final.choices[0].message.content
print(f"🤖 {respuesta}")

# Persistimos pregunta y respuesta final
conn.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      "¿Qué tiempo hace en Concepción y cuánto es 15*7?"),
        (sesion_id, "assistant", respuesta),
    ],
)
conn.commit()
print(f"\n💾 Tool calls y respuesta guardadas (sesion_id={sesion_id})")
