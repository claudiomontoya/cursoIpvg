"""
01 · ¿Qué es un embedding?
--------------------------
Un *embedding* es un vector (lista de números) que representa el significado de
un texto. Textos parecidos quedan cerca en el espacio vectorial; textos sin
relación quedan lejos.

Modelo: `text-embedding-3-small` (OpenAI) → 1536 dimensiones, ~$0.02 / 1M tokens.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

def embed(texto: str) -> list[float]:
    r = client.embeddings.create(model="text-embedding-3-small", input=texto)
    return r.data[0].embedding

textos = [
    "El gato duerme en el sofá",
    "Mi felino descansa en el sillón",
    "La capital de Francia es París",
]

vectores = [embed(t) for t in textos]

print(f"Dimensión del vector: {len(vectores[0])}")
print(f"Primeros 5 valores del primer texto: {vectores[0][:5]}\n")

def coseno(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb)

print("Similitud coseno (1.0 = idéntico, 0.0 = sin relación):")
print(f"  gato-sofá  vs  felino-sillón : {coseno(vectores[0], vectores[1]):.3f}")
print(f"  gato-sofá  vs  París         : {coseno(vectores[0], vectores[2]):.3f}")
