"""
02 · Chunking
-------------
Un PDF de 200 páginas no se puede embeber entero: pierde precisión y excede el
límite del modelo de embeddings (~8k tokens). Se parte en *chunks* pequeños
(200–800 tokens, con solape de 10–20%) para que cada vector represente una idea
concreta y la búsqueda devuelva el fragmento exacto, no el documento entero.

Acá usamos una estrategia simple: chunks por número de caracteres con overlap.
En producción se chunkea por párrafos / oraciones / encabezados.
"""

texto = """
La inteligencia artificial generativa es una rama de la IA que crea contenido nuevo:
texto, imágenes, audio y código. A diferencia de la IA discriminativa, que clasifica
o predice, la IA generativa produce.

El componente central son los modelos de lenguaje grande (LLMs), entrenados con
billones de tokens. Un token es una unidad subléxica: puede ser una palabra completa,
parte de una palabra, o incluso un signo de puntuación. El tokenizador convierte texto
en una secuencia de IDs numéricos que el modelo procesa.

Los LLMs predicen el siguiente token más probable dada una secuencia. Aplicando esa
predicción en loop (autoregresivo) generan texto coherente. El mecanismo interno clave
es la atención: cada token mira a los demás para decidir cuáles son relevantes para
predecir lo que viene.

La cuantización reduce el tamaño del modelo: pasar de FP32 a INT8 cuesta menos memoria
y permite correr modelos grandes en hardware modesto, con pérdida mínima de calidad.
""".strip()


def chunk_por_caracteres(texto: str, tam: int = 200, overlap: int = 40) -> list[str]:
    """Parte texto en trozos de `tam` chars con solape de `overlap`."""
    chunks = []
    i = 0
    while i < len(texto):
        chunks.append(texto[i : i + tam])
        i += tam - overlap
    return chunks


chunks = chunk_por_caracteres(texto, tam=200, overlap=40)

print(f"Texto original: {len(texto)} caracteres")
print(f"Total de chunks: {len(chunks)}")
print(f"Tamaño promedio: {sum(len(c) for c in chunks) // len(chunks)} chars\n")

for i, c in enumerate(chunks):
    preview = c.replace("\n", " ")
    print(f"[chunk {i}] {preview[:80]}…")
