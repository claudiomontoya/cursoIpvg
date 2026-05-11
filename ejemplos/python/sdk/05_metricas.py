"""
Ejemplo 5 · Métricas (tokens, latencia, costo)
===============================================
Qué enseña:
  - Leer `response.usage` para conocer tokens de prompt y respuesta
  - Medir latencia con time.perf_counter
  - Calcular costo aproximado a partir de los precios por 1M tokens
  - Persistir todo en la tabla `metricas` para análisis posterior

Para qué sirve:
  Saber qué te está costando cada llamada y dónde optimizar
  (prompts más cortos, modelos más baratos, caché, etc.).
"""

import time
from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, calcular_costo

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()


def llamar_y_medir(modelo: str, pregunta: str):
    """
    Hace una llamada y registra: tokens, latencia y costo en SQLite.
    Devuelve el texto de respuesta para poder mostrarlo.
    """
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": pregunta}],
    )
    latencia_ms = int((time.perf_counter() - t0) * 1000)

    u = resp.usage          # objeto con prompt_tokens, completion_tokens, total_tokens
    costo = calcular_costo(modelo, u.prompt_tokens, u.completion_tokens)

    conn.execute(
        """INSERT INTO metricas
            (ejemplo, modelo, tokens_prompt, tokens_respuesta,
             tokens_total, latencia_ms, costo_usd)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("ejemplo_05_metricas", modelo,
         u.prompt_tokens, u.completion_tokens, u.total_tokens,
         latencia_ms, costo),
    )
    conn.commit()

    print(f"  modelo  : {modelo}")
    print(f"  tokens  : prompt={u.prompt_tokens}  resp={u.completion_tokens}  total={u.total_tokens}")
    print(f"  latencia: {latencia_ms} ms")
    print(f"  costo   : USD {costo:.6f}")
    print()
    return resp.choices[0].message.content


print("=" * 60)
print(" EJEMPLO 5 · Métricas")
print("=" * 60)

pregunta = "Resume en 1 frase qué es la cuantización de modelos."

# Medimos el modelo principal del curso.
for modelo in ["gpt-5.2"]:
    print(f"▶ Probando {modelo}")
    texto = llamar_y_medir(modelo, pregunta)
    print(f"  💬 {texto}\n")

# ----------------------------------------------------------------------
# Resumen agregado leyendo la tabla `metricas`
# ----------------------------------------------------------------------
print("-" * 60)
print(" Resumen acumulado (tabla `metricas`)")
print("-" * 60)
filas = conn.execute("""
    SELECT modelo,
           COUNT(*) AS llamadas,
           SUM(tokens_total) AS tokens,
           ROUND(AVG(latencia_ms)) AS latencia_prom_ms,
           ROUND(SUM(costo_usd), 6) AS costo_total
      FROM metricas
     GROUP BY modelo
""").fetchall()

for f in filas:
    print(f"  {f['modelo']:14s}  "
          f"llamadas={f['llamadas']:<3}  "
          f"tokens={f['tokens']:<6}  "
          f"latencia≈{f['latencia_prom_ms']}ms  "
          f"costo=USD {f['costo_total']}")

print("\n💾 Métricas guardadas en sdk_demo.db → tabla `metricas`")
