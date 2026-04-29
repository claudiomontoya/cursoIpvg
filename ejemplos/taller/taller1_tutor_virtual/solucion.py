"""
╔══════════════════════════════════════════════════════════════════╗
║  TALLER 1 · Tutor Virtual · SOLUCIÓN DE REFERENCIA (docente)     ║
╚══════════════════════════════════════════════════════════════════╝

Versión que cumple TODOS los requisitos mínimos + los 3 bonus:
  - Contador de tokens de la sesión
  - Ventana deslizante (últimos 10 turnos)
  - Comando /resumen

No la distribuyas antes de que los alumnos lo intenten.
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

MODELO = "gpt-4o-mini"
VENTANA_MAX_TURNOS = 10  # cantidad de turnos (user + assistant) a conservar

# ──────────────────────────────────────────────────────────────────
# System prompt: rol + alcance + tono + redirección
# ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un tutor virtual de la carrera Analista Programador del Instituto Profesional Virginio Gómez (IPVG).

TU ROL:
- Ayudas a estudiantes con dudas sobre la carrera: programación, análisis de sistemas, bases de datos, desarrollo web, matemática aplicada, metodologías ágiles.

TONO:
- Amable, cercano, conciso (1-3 frases por respuesta).
- Si el estudiante te da su nombre, recordálo y usálo en los siguientes turnos.

ALCANCE:
- Solo respondés sobre temas de la carrera o vida académica en IPVG.
- Si preguntan sobre temas fuera de tu alcance (deportes, política, farándula, cocina, etc.), redirigí amablemente: "Solo puedo ayudarte con temas de la carrera Analista Programador. ¿Tenés alguna duda sobre el contenido de los módulos?"
"""


# Historial inicial
historial = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

# Contador de tokens (bonus)
_tokens_totales = {"total": 0, "input": 0, "output": 0}


def _aplicar_ventana_deslizante():
    """
    Bonus: mantiene solo el system prompt + los últimos N turnos.
    Un "turno" = 1 mensaje user + 1 mensaje assistant.
    """
    global historial
    if len(historial) <= 1:
        return
    # Separamos el system del resto
    system = historial[0]
    resto = historial[1:]
    # Un turno son 2 mensajes (user + assistant). Si hay más de 2N mensajes, recortamos.
    if len(resto) > VENTANA_MAX_TURNOS * 2:
        resto = resto[-VENTANA_MAX_TURNOS * 2:]
    historial = [system] + resto


def chat(mensaje_usuario: str) -> str:
    """Realiza un turno de chat y actualiza el historial."""
    historial.append({"role": "user", "content": mensaje_usuario})

    resp = client.chat.completions.create(
        model=MODELO,
        messages=historial,
    )

    respuesta = resp.choices[0].message.content
    historial.append({"role": "assistant", "content": respuesta})

    # Contabilidad de tokens (bonus)
    _tokens_totales["total"] += resp.usage.total_tokens
    _tokens_totales["input"] += resp.usage.prompt_tokens
    _tokens_totales["output"] += resp.usage.completion_tokens

    # Recortar el historial (bonus)
    _aplicar_ventana_deslizante()

    return respuesta


def generar_resumen() -> str:
    """Bonus: pide al modelo un resumen de la conversación hasta ahora."""
    mensajes_para_resumen = historial + [
        {"role": "user", "content": "Hazme un resumen de nuestra conversación en 2-3 bullets."}
    ]
    resp = client.chat.completions.create(model=MODELO, messages=mensajes_para_resumen)
    return resp.choices[0].message.content


def main():
    print("🎓 Tutor Virtual · Analista Programador IPVG")
    print("   Comandos: 'salir' para terminar · '/resumen' para ver resumen\n")

    while True:
        try:
            user_input = input("👤 Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input.lower() == "salir":
            break

        if user_input == "/resumen":
            print(f"\n📋 Resumen:\n{generar_resumen()}\n")
            continue

        respuesta = chat(user_input)
        print(f"🤖 Tutor: {respuesta}\n")

    # ── Mensaje de despedida con stats ──
    print("\n" + "=" * 60)
    print("👋 ¡Nos vemos en la próxima clase!")
    print(f"📊 Tokens usados en la sesión:")
    print(f"   Input:  {_tokens_totales['input']}")
    print(f"   Output: {_tokens_totales['output']}")
    print(f"   Total:  {_tokens_totales['total']}")
    costo = (_tokens_totales['input'] * 0.15 + _tokens_totales['output'] * 0.60) / 1_000_000
    print(f"   Costo:  ${costo:.6f} USD")
    print("=" * 60)


if __name__ == "__main__":
    main()
