"""
Ejemplo 9 · Code Interpreter (ejecución de código)
====================================================
Qué enseña:
  - El modelo escribe código Python y lo ejecuta en un sandbox de OpenAI
  - Útil para: cálculos, análisis de datos, generación de gráficos, manipular CSV/Excel
  - Tú solo describes el problema en lenguaje natural

Cuándo usarlo:
  Cuando el problema requiere CÁLCULO REAL (no solo razonamiento).
  Ej: "calcula la media y mediana de estos 1000 números", "resuelve esta integral",
  "lee este CSV y dame los outliers".

Importante:
  El sandbox es efímero (se descarta tras la respuesta). Si necesitás
  persistencia entre llamadas, podés reutilizar el `container_id`.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, crear_sesion

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
sesion_id = crear_sesion(conn, "ejemplo_09_code_interpreter")

pregunta = (
    "Calcula con Python la suma de los primeros 100 números primos "
    "y muestra los 10 primeros de la lista."
)

print("=" * 60)
print(" EJEMPLO 9 · Code Interpreter")
print("=" * 60)
print(f"👤 {pregunta}\n")

# ----------------------------------------------------------------------
# Tool `code_interpreter`. `container.type=auto` deja que OpenAI cree
# un sandbox descartable solo para esta llamada.
# ----------------------------------------------------------------------
respuesta = client.responses.create(
    model="gpt-4o-mini",
    tools=[{
        "type": "code_interpreter",
        "container": {"type": "auto"},
    }],
    input=pregunta,
)

texto = respuesta.output_text
print(f"🤖 {texto}\n")

# ----------------------------------------------------------------------
# Si querés ver el código que ejecutó el modelo, está en items
# de tipo `code_interpreter_call`. Lo extraemos para guardarlo.
# ----------------------------------------------------------------------
codigo_ejecutado = []
for item in respuesta.output:
    if getattr(item, "type", None) == "code_interpreter_call":
        codigo = getattr(item, "code", None)
        if codigo:
            codigo_ejecutado.append(codigo)

if codigo_ejecutado:
    print("📜 Código que ejecutó el modelo:")
    for c in codigo_ejecutado:
        print("-" * 40)
        print(c)
    print("-" * 40)

# ----------------------------------------------------------------------
# Persistencia: pregunta, respuesta y código ejecutado
# ----------------------------------------------------------------------
conn.executemany(
    "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
    [
        (sesion_id, "user",      pregunta),
        (sesion_id, "assistant", texto),
    ],
)
if codigo_ejecutado:
    conn.execute(
        "INSERT INTO tool_calls (sesion_id, herramienta, argumentos, resultado) "
        "VALUES (?, ?, ?, ?)",
        (sesion_id, "code_interpreter", pregunta,
         json.dumps(codigo_ejecutado, ensure_ascii=False)),
    )
conn.commit()
print(f"\n💾 Guardado (sesion_id={sesion_id})")
