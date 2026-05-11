"""
00 · Conexión a Qdrant Cloud
----------------------------
Primer contacto con la base vectorial. Solo verificamos que la API key funciona
y que podemos hablar con el cluster: pedimos la lista de collections.

Una *collection* en Qdrant es como una tabla: agrupa vectores del mismo tamaño
(misma dimensión) y la misma métrica de distancia (coseno, dot, euclidiana...).
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

collections = client.get_collections()
print("Collections en el cluster:")
for c in collections.collections:
    print(f"  · {c.name}")

if not collections.collections:
    print("  (ninguna todavía — las creamos en el ejemplo 03)")
