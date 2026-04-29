"""
Ejemplo 7 · Streaming (respuesta token a token)
================================================
Qué enseña:
  - Cómo recibir la respuesta mientras se genera (SSE bajo el capó)
  - El modelo no es más rápido, pero la LATENCIA PERCIBIDA baja 5-10×
  - Cómo iterar sobre el generador que devuelve la librería

Moraleja:
  Para cualquier UI (chat, app, página web) → usa streaming.
  El usuario empieza a leer desde el primer token, no espera 8 segundos.
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

print("=" * 60)
print(" EJEMPLO 7 · Streaming")
print("=" * 60)
print("\n🤖 Respuesta (mirá cómo aparece letra por letra):\n")

# ---------------------------------------------------------------
# stream=True → devuelve un generador en vez de la respuesta completa
# ---------------------------------------------------------------
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": (
                "Cuéntame una historia corta (4 frases) sobre un estudiante "
                "de IPVG que crea su primer agente de IA."
            ),
        }
    ],
    stream=True,
)

# ---------------------------------------------------------------
# Iteramos sobre los chunks a medida que llegan
# Cada chunk tiene un 'delta' con el texto parcial
# ---------------------------------------------------------------
tokens_recibidos = 0
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        # end="" y flush para imprimir en la misma línea sin buffer
        print(delta, end="", flush=True)
        tokens_recibidos += 1

print(f"\n\n📊 {tokens_recibidos} chunks recibidos.")

# =====================================================================
# MORALEJA
# =====================================================================
print("\n" + "=" * 60)
print("☝️  Los tokens llegan cada ~20-50ms.")
print("   Tiempo total: igual. Tiempo HASTA EL PRIMER TOKEN: mucho menor.")
print()
print("   Claves de implementación:")
print("   - stream=True en la llamada")
print("   - Iterar el generador con 'for chunk in stream'")
print("   - El texto viene en chunk.choices[0].delta.content")
print("   - En web: convertir a Server-Sent Events (SSE) para el browser")
print()
print("   ⚠️  Con streaming pierdes el 'usage' total inmediato.")
print("      Para obtenerlo, agregar stream_options={'include_usage': True}")
print("=" * 60)
