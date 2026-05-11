# RAG con Qdrant — Curso IPVG

7 ejemplos progresivos que arman un sistema completo de Retrieval-Augmented Generation.
Cada archivo enseña **un solo concepto** en ~50 líneas comentadas en español.

## Setup

```bash
cd ejemplos/python
pip install -r requirements.txt
cp .env.example .env       # editar con tus keys reales
```

Las variables necesarias en `.env`:

| Variable            | Para qué                                    |
|---------------------|---------------------------------------------|
| `OPENAI_API_KEY`    | Generar embeddings (text-embedding-3-small) |
| `ANTHROPIC_API_KEY` | LLM final en `07_rag_completo.py`           |
| `QDRANT_URL`        | URL del cluster Qdrant Cloud                |
| `QDRANT_API_KEY`    | API key del cluster                         |

## Orden recomendado

| # | Archivo                  | Concepto                                                    |
|---|--------------------------|-------------------------------------------------------------|
| 0 | `00_conexion.py`         | Conectar a Qdrant Cloud y listar collections                |
| 1 | `01_embedding.py`        | Qué es un embedding · dimensión · similitud coseno          |
| 2 | `02_chunking.py`         | Partir un documento en chunks con overlap                   |
| 3 | `03_crear_coleccion.py`  | Crear una collection (dim + distancia)                      |
| 4 | `04_ingestar.py`         | chunk → embed → upsert (con payload)                        |
| 5 | `05_buscar.py`           | Búsqueda vectorial top-k                                    |
| 6 | `06_rerank.py`           | Cross-encoder reordena top-k → top-n                        |
| 7 | `07_rag_completo.py`     | Pipeline end-to-end con Claude                              |

Ejecutar en orden:

```bash
python rag/00_conexion.py
python rag/01_embedding.py
python rag/02_chunking.py
python rag/03_crear_coleccion.py
python rag/04_ingestar.py
python rag/05_buscar.py
python rag/06_rerank.py
python rag/07_rag_completo.py
```

## Costos aproximados (ejecutar los 8)

- Embeddings (OpenAI): < $0.0001 USD
- LLM final (Claude Haiku 4.5): ~$0.001 USD
- Qdrant Cloud: free tier alcanza con sobra
- Cross-encoder rerank: gratis (corre local en CPU)

**Total: bajo $0.005 USD.**

## Notas técnicas

- **Embeddings**: `text-embedding-3-small` (1536 dim). Alternativa local: `sentence-transformers` con `all-MiniLM-L6-v2` (384 dim, gratis).
- **Distancia**: `COSINE` para texto normalizado. `DOT` si los vectores ya están normalizados (más rápido). `EUCLID` para datos espaciales.
- **Chunking**: el ejemplo usa partición por caracteres. En producción: por párrafos / encabezados / oraciones, con tokenizador para respetar el límite del modelo de embeddings (~8k tokens).
- **Rerank**: `cross-encoder/ms-marco-MiniLM-L-6-v2` se descarga la primera vez (~80 MB) y corre en CPU. Para producción: Cohere Rerank, Voyage Rerank, o un cross-encoder fine-tuned.
- **HNSW**: el índice de Qdrant. Búsqueda aproximada en O(log n) — milisegundos sobre millones de vectores.
