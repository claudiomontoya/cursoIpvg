"""
Ejemplo 8 · Structured Outputs (JSON con schema)
=================================================
Qué enseña:
  - Forzar al modelo a responder con JSON que sigue un schema exacto
  - Eliminar el parsing frágil de "texto libre → JSON"
  - Usar Pydantic para definir el schema + validación automática

Moraleja:
  Si necesitas datos estructurados → NUNCA le pidas "responde en JSON"
  en texto libre. Usá response_format con un schema.
  El modelo ya no puede salirse del formato.

Casos de uso:
  - Extracción de entidades (nombres, fechas, cantidades)
  - Clasificación multi-etiqueta
  - Conversión de texto libre a registros de base de datos
  - Agentes que necesitan output garantizado para el siguiente paso
"""

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()
client = OpenAI()


# ---------------------------------------------------------------
# 1. Definir el schema como clases Pydantic
#    Estas clases DESCRIBEN la forma exacta del output que queremos.
# ---------------------------------------------------------------
class Habilidad(BaseModel):
    nombre: str
    nivel: str = Field(description="principiante, intermedio o avanzado")


class Estudiante(BaseModel):
    nombre: str
    edad: int
    carrera: str
    ciudad: str
    habilidades: list[Habilidad]
    busca_trabajo: bool


# ---------------------------------------------------------------
# 2. Texto libre del que queremos extraer datos
# ---------------------------------------------------------------
texto_fuente = """
Claudio Montoya, 34 años, de Concepción. Estudia Analista Programador en IPVG.
Sabe Python avanzado, JavaScript intermedio y acaba de empezar con Rust (principiante).
También conoce SQL a nivel intermedio. Está buscando prácticas en empresas de software.
"""

print("=" * 60)
print(" EJEMPLO 8 · Structured Outputs")
print("=" * 60)
print("\n📝 Texto fuente:")
print(texto_fuente.strip())

# ---------------------------------------------------------------
# 3. Llamar con response_format=Estudiante
#    La librería de OpenAI reconoce la clase Pydantic y genera el JSON Schema.
# ---------------------------------------------------------------
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Extraes datos estructurados de texto sobre estudiantes.",
        },
        {"role": "user", "content": texto_fuente},
    ],
    response_format=Estudiante,
)

# ---------------------------------------------------------------
# 4. El resultado YA es un objeto Pydantic validado
#    No hace falta json.loads, no hace falta validar tipos, está listo.
# ---------------------------------------------------------------
estudiante: Estudiante = response.choices[0].message.parsed

print("\n📋 Datos extraídos:")
print(f"   Nombre:        {estudiante.nombre}")
print(f"   Edad:          {estudiante.edad} años")
print(f"   Carrera:       {estudiante.carrera}")
print(f"   Ciudad:        {estudiante.ciudad}")
print(f"   Busca trabajo: {'sí' if estudiante.busca_trabajo else 'no'}")
print(f"   Habilidades:")
for h in estudiante.habilidades:
    print(f"     - {h.nombre} ({h.nivel})")

# ---------------------------------------------------------------
# 5. Ahora podés usar el objeto como cualquier objeto Python
# ---------------------------------------------------------------
print(f"\n🔧 Operando sobre los datos:")
print(f"   ¿Sabe Python?  {'sí' if any(h.nombre.lower()=='python' for h in estudiante.habilidades) else 'no'}")
print(f"   Habilidades avanzadas: {[h.nombre for h in estudiante.habilidades if h.nivel=='avanzado']}")

# También podés convertir a dict/JSON si lo necesitás
import json
print(f"\n📦 Como JSON:")
print(json.dumps(estudiante.model_dump(), indent=2, ensure_ascii=False))


# =====================================================================
# MORALEJA
# =====================================================================
print("\n" + "=" * 60)
print("☝️  El modelo NO puede salirse del schema.")
print("   Si el schema dice 'edad: int', no te va a devolver 'treinta y cuatro'.")
print("   Si dice 'habilidades: list[Habilidad]', NUNCA te devuelve un string.")
print()
print("   Adiós a:")
print("   ✗ json.loads en try/except")
print("   ✗ regex para extraer JSON de texto libre")
print("   ✗ prompts rogando '¡RESPONDE EN JSON VÁLIDO!'")
print()
print("   Hola a:")
print("   ✓ Pydantic → JSON Schema automático")
print("   ✓ response.choices[0].message.parsed → objeto tipado")
print("   ✓ Código robusto sin parsing manual")
print("=" * 60)
