"""
Ejemplo 2 · Sin memoria (la API es stateless)
==============================================
Qué enseña:
  - Por defecto, CADA llamada a OpenAI es independiente
  - El modelo NO recuerda conversaciones previas
  - Demostración concreta: le decimos el nombre, luego preguntamos

Aha moment:
  Si no guardas el historial y lo reenvías, el modelo parte de cero cada vez.
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

print("=" * 60)
print(" EJEMPLO 2 · Sin memoria — 2 llamadas independientes")
print("=" * 60)

# ---------------------------------------------------------------
# Llamada 1: le decimos nuestro nombre
# ---------------------------------------------------------------
r1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hola, me llamo Claudio y soy de Concepción."}
    ],
)
print("\n[Llamada 1]")
print("👤 Usuario:  Hola, me llamo Claudio y soy de Concepción.")
print(f"🤖 Modelo:   {r1.choices[0].message.content}")

# ---------------------------------------------------------------
# Llamada 2: le preguntamos el nombre (SIN contexto previo)
# Nota: es una llamada NUEVA, no le pasamos el historial.
# ---------------------------------------------------------------
r2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "¿Cómo me llamo y de dónde soy?"}
    ],
)
print("\n[Llamada 2 — nueva, sin historial]")
print("👤 Usuario:  ¿Cómo me llamo y de dónde soy?")
print(f"🤖 Modelo:   {r2.choices[0].message.content}")

# =====================================================================
# MORALEJA
# =====================================================================
print("\n" + "=" * 60)
print("☝️  El modelo NO recuerda el nombre ni la ciudad.")
print("   Cada llamada parte desde cero (stateless).")
print("   Solución: enviar el historial en cada llamada → ejemplo 3.")
print("=" * 60)
