"""
Ejemplo 4 · Tool calling (function calling)
============================================
Qué enseña:
  - Cómo darle al modelo un "menú" de funciones que puede pedir ejecutar
  - El flujo completo: modelo → tool_call → tu código ejecuta → resultado → modelo
  - El modelo NO ejecuta la función; te pide que TÚ la ejecutes

Moraleja:
  El modelo decide QUÉ llamar y con qué argumentos.
  Tu código ejecuta, le devuelve el resultado, y el modelo redacta la respuesta final.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


# ---------------------------------------------------------------
# 1. Definimos la herramienta con JSON Schema
#    Esto es lo que VE el modelo: nombre, descripción, argumentos.
# ---------------------------------------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_clima",
            "description": "Obtiene el clima actual de una ciudad chilena.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ciudad": {
                        "type": "string",
                        "description": "Nombre de la ciudad (Concepción, Santiago, Chillán, etc.)"
                    }
                },
                "required": ["ciudad"],
            },
        },
    }
]


# ---------------------------------------------------------------
# 2. Nuestra función real (mock)
#    En producción llamaría a una API de clima. Acá devolvemos datos fake.
# ---------------------------------------------------------------
def get_clima(ciudad: str) -> dict:
    """Mock: devuelve datos fake de clima."""
    mock_data = {
        "Concepción": {"temp_c": 14, "condicion": "nublado",    "humedad": 82},
        "Santiago":   {"temp_c": 22, "condicion": "despejado",  "humedad": 45},
        "Chillán":    {"temp_c": 16, "condicion": "llovizna",   "humedad": 91},
        "Los Ángeles":{"temp_c": 18, "condicion": "parcial",    "humedad": 68},
    }
    return mock_data.get(ciudad, {"temp_c": None, "condicion": "desconocido"})


print("=" * 60)
print(" EJEMPLO 4 · Tool calling")
print("=" * 60)

# ---------------------------------------------------------------
# 3. Empezamos la conversación
# ---------------------------------------------------------------
mensajes = [
    {"role": "user", "content": "¿Qué tiempo hace en Concepción? Responde en 1 frase."}
]

# ---------------------------------------------------------------
# 4. PRIMERA llamada — el modelo ve las tools disponibles y decide si usarlas
# ---------------------------------------------------------------
print("\n📞 Llamada 1: usuario pregunta, modelo decide...")
r1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=mensajes,
    tools=tools,
)

msg = r1.choices[0].message
print(msg)
mensajes.append(msg)   # Guardamos la respuesta del modelo en el historial

# ---------------------------------------------------------------
# 5. ¿El modelo pidió ejecutar una tool?
# ---------------------------------------------------------------
if msg.tool_calls:
    for tool_call in msg.tool_calls:
        nombre_fn = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"🔧 El modelo pidió llamar: {nombre_fn}(**{args})")

        # 6. Ejecutamos la función REAL con los argumentos que el modelo eligió
        if nombre_fn == "get_clima":
            resultado = get_clima(**args)
        else:
            resultado = {"error": f"Función desconocida: {nombre_fn}"}

        print(f"   ↳ Resultado: {resultado}")

        # 7. Devolvemos el resultado al modelo como un mensaje "tool"
        mensajes.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(resultado, ensure_ascii=False),
        })

    # ---------------------------------------------------------------
    # 8. SEGUNDA llamada — ahora el modelo tiene el resultado y redacta la respuesta
    # ---------------------------------------------------------------
    print("\n📞 Llamada 2: modelo redacta respuesta final con los datos...")
    r2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        tools=tools,
    )
    print(f"\n🤖 Respuesta final:  {r2.choices[0].message.content}")
else:
    # El modelo no quiso usar ninguna tool — respondió directamente
    print(f"\n🤖 Respuesta directa (sin tool): {msg.content}")

# =====================================================================
# MORALEJA
# =====================================================================
print("\n" + "=" * 60)
print("☝️  El modelo llama tu función indirectamente:")
print("   1. Le damos un menú de tools (JSON Schema).")
print("   2. El modelo devuelve un 'tool_call' con args.")
print("   3. Tu código ejecuta la función REAL.")
print("   4. Le mandas el resultado → el modelo redacta la respuesta.")
print()
print("   Hacen falta 2 llamadas al modelo por cada tool usada.")
print("   El modelo puede pedir VARIAS tools en un turno (paralelo).")
print("=" * 60)
