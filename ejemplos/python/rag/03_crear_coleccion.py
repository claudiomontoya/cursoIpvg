"""
03 · Crear una collection
-------------------------
Antes de subir vectores hay que decirle a Qdrant:
  · cómo se llamará la collection
  · qué dimensión tienen los vectores (1536 para text-embedding-3-small)
  · qué distancia usar para comparar (COSINE es la estándar para texto)

`recreate_collection` borra y vuelve a crear — útil en demos, peligroso en prod.
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()
client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

NOMBRE = "curso_ipvg"
DIMENSION = 1536  # text-embedding-3-small

client.recreate_collection(
    collection_name=NOMBRE,
    vectors_config=VectorParams(size=DIMENSION, distance=Distance.COSINE),
)

info = client.get_collection(NOMBRE)
print(f"Collection '{NOMBRE}' creada.")
print(f"  · dimensión : {info.config.params.vectors.size}")
print(f"  · distancia : {info.config.params.vectors.distance}")
print(f"  · puntos    : {info.points_count}")
