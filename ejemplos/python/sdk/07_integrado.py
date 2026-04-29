"""
Ejemplo 7 · Integrado (memoria + tools + métricas)
====================================================
Qué enseña:
  Junta todo lo anterior en un mini-asistente:
    - Memoria persistente en SQLite (como ej. 6)
    - Una herramienta `consultar_carrera` que el modelo puede llamar
    - Métricas de cada turno guardadas en la tabla `metricas`

Cómo correrlo:
    python 07_integrado.py "¿Qué carreras de informática hay en IPVG?"

Si no pasás argumento, corre una mini-demo con 2 preguntas.
"""

import json
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

from db import conectar, calcular_costo

load_dotenv(dotenv_path="../.env")

client = OpenAI()
conn = conectar()
MODELO = "gpt-4o-mini"

# ======================================================================
# Sesión persistente
# ======================================================================
NOMBRE = "asistente_ipvg_integrado"
fila = conn.execute("SELECT id FROM sesiones WHERE nombre = ?", (NOMBRE,)).fetchone()

if fila:
    sesion_id = fila["id"]
else:
    cur = conn.execute("INSERT INTO sesiones (nombre) VALUES (?)", (NOMBRE,))
    sesion_id = cur.lastrowid
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (sesion_id, "system",
         "Eres un asistente de admisión de IPVG. Si te preguntan por una "
         "carrera específica, usa la herramienta `consultar_carrera`."),
    )
    conn.commit()


# ======================================================================
# Catálogo falso de carreras (en la vida real saldría de una BD/API)
# ======================================================================
CATALOGO = {
    "analista programador": {
        "duracion": "5 semestres",
        "modalidad": "presencial / vespertino",
        "campo":   "desarrollo de software, soporte, datos",
    },
    "ingeniería en informática": {
        "duracion": "8 semestres",
        "modalidad": "presencial",
        "campo":   "arquitectura de software, redes, IA aplicada",
    },
    "técnico en redes": {
        "duracion": "4 semestres",
        "modalidad": "presencial",
        "campo":   "infraestructura, ciberseguridad básica",
    },
}


def consultar_carrera(nombre: str) -> dict:
    clave = nombre.strip().lower()
    return CATALOGO.get(clave, {"error": f"no tengo datos de '{nombre}'"})


TOOLS = [{
    "type": "function",
    "function": {
        "name": "consultar_carrera",
        "description": "Datos oficiales de una carrera de IPVG.",
        "parameters": {
            "type": "object",
            "properties": {"nombre": {"type": "string"}},
            "required": ["nombre"],
        },
    },
}]


# ======================================================================
# Helpers de BD
# ======================================================================
def cargar_historial():
    filas = conn.execute(
        "SELECT rol, contenido FROM mensajes WHERE sesion_id = ? ORDER BY id",
        (sesion_id,),
    ).fetchall()
    return [{"role": f["rol"], "content": f["contenido"]} for f in filas]


def guardar_mensaje(rol: str, contenido: str):
    conn.execute(
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (?, ?, ?)",
        (sesion_id, rol, contenido),
    )
    conn.commit()


def guardar_metrica(usage, latencia_ms):
    costo = calcular_costo(MODELO, usage.prompt_tokens, usage.completion_tokens)
    conn.execute(
        """INSERT INTO metricas
              (ejemplo, modelo, tokens_prompt, tokens_respuesta,
               tokens_total, latencia_ms, costo_usd)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("ejemplo_07_integrado", MODELO,
         usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
         latencia_ms, costo),
    )
    conn.commit()
    return costo


# ======================================================================
# Turno completo: maneja tool calls si aparecen
# ======================================================================
def responder(pregunta: str):
    print(f"\n👤 {pregunta}")
    guardar_mensaje("user", pregunta)

    mensajes = cargar_historial()

    # --- Llamada 1: el modelo puede pedir tools ---
    t0 = time.perf_counter()
    r1 = client.chat.completions.create(
        model=MODELO, messages=mensajes, tools=TOOLS,
    )
    lat1 = int((time.perf_counter() - t0) * 1000)
    guardar_metrica(r1.usage, lat1)

    msg = r1.choices[0].message

    # Si el modelo NO pidió tools, ya está
    if not msg.tool_calls:
        guardar_mensaje("assistant", msg.content)
        print(f"🤖 {msg.content}")
        return

    # Si pidió tools, las ejecutamos y reenviamos
    print(f"🔧 El modelo pidió {len(msg.tool_calls)} tool(s)")
    mensajes.append(msg)
    for tc in msg.tool_calls:
        args = json.loads(tc.function.arguments)
        resultado = consultar_carrera(**args)
        print(f"   → {tc.function.name}({args}) = {resultado}")
        conn.execute(
            "INSERT INTO tool_calls (sesion_id, herramienta, argumentos, resultado) "
            "VALUES (?, ?, ?, ?)",
            (sesion_id, tc.function.name, json.dumps(args), json.dumps(resultado)),
        )
        mensajes.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(resultado),
        })
    conn.commit()

    # --- Llamada 2: respuesta final con los resultados de las tools ---
    t1 = time.perf_counter()
    r2 = client.chat.completions.create(model=MODELO, messages=mensajes)
    lat2 = int((time.perf_counter() - t1) * 1000)
    guardar_metrica(r2.usage, lat2)

    final = r2.choices[0].message.content
    guardar_mensaje("assistant", final)
    print(f"🤖 {final}")


# ======================================================================
# Main
# ======================================================================
print("=" * 60)
print(" EJEMPLO 7 · Integrado (memoria + tools + métricas)")
print("=" * 60)

if len(sys.argv) > 1:
    responder(" ".join(sys.argv[1:]))
else:
    responder("Hola, soy Claudio y me interesa estudiar algo de programación.")
    responder("Cuéntame sobre Analista Programador, por favor.")

# Resumen de costos acumulados de este ejemplo
total = conn.execute(
    "SELECT ROUND(SUM(costo_usd),6) AS c, SUM(tokens_total) AS t "
    "FROM metricas WHERE ejemplo='ejemplo_07_integrado'"
).fetchone()
print(f"\n📊 Acumulado ejemplo 7: tokens={total['t']}  costo=USD {total['c']}")
print("💾 Todo persistido en sdk_demo.db")
