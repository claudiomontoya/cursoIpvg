"""
Ejemplo 8 · Web search (browser integrado)
============================================
Qué enseña:
  - Usar la **Responses API** (`client.responses.create`)
  - La tool `web_search` la ejecuta OpenAI por ti (no necesitas Selenium ni APIs externas)
  - El modelo navega, lee páginas y cita fuentes

Diferencia con `chat.completions`:
  La Responses API es la sucesora moderna y soporta tools "built-in"
  (web_search, code_interpreter, file_search, computer_use) sin que
  tengas que implementar las funciones tú.

Modelos compatibles:
  gpt-4o, gpt-4o-mini, gpt-4.1, etc. (los que tengan navegación habilitada)
"""

from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, crear_sesion

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
sesion_id = crear_sesion(conn, "ejemplo_08_web_search")

pregunta = "¿Qué noticias relevantes hay esta semana sobre el Instituto Profesional Virginio Gómez?"

print("=" * 60)
print(" EJEMPLO 8 · Web search")
print("=" * 60)
print(f"👤 {pregunta}\n")

# ----------------------------------------------------------------------
# Llamada a la Responses API con la tool web_search
# ----------------------------------------------------------------------
respuesta = client.responses.create(
    model="gpt-4o-mini",
    tools=[{"type": "web_search"}],   # 👈 navegación lista, sin código extra
    input=pregunta,
)

# La Responses API expone `output_text` como atajo para el texto final
texto = respuesta.output_text
print(f"🤖 {texto}\n")

# ----------------------------------------------------------------------
# Extraer las URLs citadas (cuando el modelo usa web_search)
# El campo `output` es una lista de items: 'message', 'web_search_call', etc.
# Las citas vienen en annotations dentro del message.
# ----------------------------------------------------------------------
fuentes = []
for item in respuesta.output:
    if getattr(item, "type", None) == "message":
        for parte in getattr(item, "content", []):
            for ann in getattr(parte, "annotations", []) or []:
                if getattr(ann, "type", None) == "url_citation":
                    fuentes.append(ann.url)

if fuentes:
    print("🔗 Fuentes citadas:")
    for u in fuentes:
        print(f"   - {u}")

# ----------------------------------------------------------------------
# Persistencia
# ----------------------------------------------------------------------
conn.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      pregunta),
        (sesion_id, "assistant", texto),
    ],
)
# También guardamos las URLs como un "tool_call" para análisis posterior
if fuentes:
    conn.execute(
        "INSERT INTO tool_calls (sesion_id, herramienta, argumentos, resultado) "
        "VALUES (?, ?, ?, ?)",
        (sesion_id, "web_search", pregunta, "\n".join(fuentes)),
    )
conn.commit()
print(f"\n💾 Guardado (sesion_id={sesion_id})")
