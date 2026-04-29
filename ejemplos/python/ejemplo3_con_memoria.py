"""
Ejemplo 3 · Memoria con historial manual
=========================================
Qué enseña:
  - Mantener una lista de mensajes como "historial"
  - Appendear user y assistant en cada turno
  - El modelo ahora recuerda turnos previos
  - BONUS: observar cómo crece el costo con cada turno

Moraleja:
  La "memoria" es una lista de diccionarios. Simple, explícita, bajo tu control.
  La responsabilidad de truncar/resumir historiales largos es TUYA.
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# 1. Historial: empezamos con un system prompt (personalidad del asistente)
historial = [
    {
        "role": "system",
        "content": "Eres un tutor amable y conciso de IPVG. Responde en 1-2 frases."
    }
]


def preguntar(texto_usuario: str):
    """
    Flujo por turno:
      1. Appendeamos el mensaje del usuario al historial
      2. Llamamos al modelo con TODO el historial
      3. Appendeamos la respuesta del asistente al historial
      4. Mostramos el turno y el uso de tokens acumulado
    """
    # 1. Append usuario
    historial.append({"role": "user", "content": texto_usuario})

    # 2. Llamada con todo el historial
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historial,
    )

    # 3. Extraer respuesta y appendear al historial
    respuesta = resp.choices[0].message.content
    historial.append({"role": "assistant", "content": respuesta})

    # 4. Mostrar turno + uso
    turno = sum(1 for m in historial if m["role"] == "user")
    print(f"\n[Turno {turno}]  tokens usados: {resp.usage.total_tokens}")
    print(f"👤 Tú:     {texto_usuario}")
    print(f"🤖 Tutor:  {respuesta}")


print("=" * 60)
print(" EJEMPLO 3 · Con memoria — conversación multi-turno")
print("=" * 60)

# ---------------------------------------------------------------
# Una conversación real de 4 turnos
# ---------------------------------------------------------------
preguntar("Hola, me llamo Claudio y estudio Analista Programador en IPVG.")
preguntar("¿Qué carreras hay relacionadas con datos?")
preguntar("¿Cuál me recomiendas para alguien que ya sabe programar?")
preguntar("¿Cómo me llamo y qué estoy estudiando?")   # ← prueba de memoria

# =====================================================================
# MORALEJA
# =====================================================================
print("\n" + "=" * 60)
print("☝️  En el último turno el modelo recordó nombre y carrera.")
print("   La memoria vive en la lista 'historial' (Python, en tu proceso).")
print(f"   Historial actual: {len(historial)} mensajes.")
print()
print("   ⚠️  Cada turno reenvía el historial ENTERO → los tokens crecen.")
print("   Con el tiempo conviene:")
print("     - Truncar los turnos más antiguos")
print("     - Resumir el historial cuando supere N tokens")
print("     - Guardar memoria 'permanente' en una base de datos")
print("=" * 60)
