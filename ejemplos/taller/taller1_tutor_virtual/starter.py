"""
╔══════════════════════════════════════════════════════════════════╗
║  TALLER 1 · Tutor Virtual de Analista Programador                ║
║  Starter · Completá los # TODO en orden                          ║
╚══════════════════════════════════════════════════════════════════╝

Integra: mensajes con roles · memoria manual · system prompt · loop
Tiempo estimado: 45 - 60 min

Lee el README.md antes de empezar.
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


# ═══════════════════════════════════════════════════════════════════
# TODO 1 · Escribir el SYSTEM PROMPT
# ───────────────────────────────────────────────────────────────────
# El system prompt define la personalidad, el alcance y el tono.
# Debe cumplir:
#   - Rol: tutor virtual de la carrera Analista Programador en IPVG
#   - Alcance: solo responde sobre temas de la carrera (programación,
#     análisis, bases de datos, desarrollo web, matemática aplicada...)
#   - Tono: amable, conciso (1-3 frases por respuesta)
#   - Redirige: si le preguntan cosas fuera del alcance, explica
#     que solo puede ayudar con temas de la carrera.
# ═══════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
TU CÓDIGO AQUÍ
"""


# ═══════════════════════════════════════════════════════════════════
# TODO 2 · Inicializar el historial con el system prompt
# ───────────────────────────────────────────────────────────────────
# El historial es una lista de diccionarios con role + content.
# Debe empezar con un mensaje de role="system" conteniendo SYSTEM_PROMPT.
# ═══════════════════════════════════════════════════════════════════
historial = [
    # TU CÓDIGO AQUÍ
]


# ═══════════════════════════════════════════════════════════════════
# TODO 3 · Implementar la función chat()
# ───────────────────────────────────────────────────────────────────
# Debe hacer:
#   1. Appendear el mensaje del usuario al historial (role="user")
#   2. Llamar a client.chat.completions.create con model="gpt-4o-mini"
#      y messages=historial
#   3. Extraer la respuesta del modelo
#   4. Appendear la respuesta al historial (role="assistant")
#   5. Retornar el texto de la respuesta
#
# 💡 Tip: mirá el ejemplo3_con_memoria.py para el patrón.
# ═══════════════════════════════════════════════════════════════════
def chat(mensaje_usuario: str) -> str:
    # 3.1: appendear mensaje del usuario
    # TU CÓDIGO AQUÍ

    # 3.2: llamar al modelo
    # TU CÓDIGO AQUÍ

    # 3.3: extraer la respuesta
    respuesta = ""  # ← reemplazar

    # 3.4: appendear la respuesta al historial
    # TU CÓDIGO AQUÍ

    # 3.5: retornar
    return respuesta


# ═══════════════════════════════════════════════════════════════════
# TODO 4 · Implementar el bucle principal en main()
# ───────────────────────────────────────────────────────────────────
# El bucle debe:
#   - Mostrar un mensaje de bienvenida una vez
#   - Pedir input() al usuario con un prompt amigable
#   - Si el usuario escribe "salir" → salir del bucle
#   - Si no → llamar a chat() y mostrar la respuesta
# ═══════════════════════════════════════════════════════════════════
def main():
    print("🎓 Tutor Virtual · Analista Programador IPVG")
    print("   (escribí 'salir' para terminar)\n")

    while True:
        # TODO 4.1: leer input del usuario
        user_input = ""  # ← reemplazar

        # TODO 5: detectar "salir" y cortar el bucle
        # TU CÓDIGO AQUÍ

        # TODO 6: llamar a chat() y mostrar la respuesta
        # TU CÓDIGO AQUÍ

    # ── BONUS ──
    # Mostrá el total de tokens consumidos en la sesión.
    # Tip: tenés que guardarlo dentro de chat() (por ejemplo, en una lista global).
    print("\n👋 ¡Nos vemos en la próxima clase!")


if __name__ == "__main__":
    main()
