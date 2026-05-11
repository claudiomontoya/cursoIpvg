# test/ — RAG sobre el Reglamento Académico 2026

Dos scripts que aplican el pipeline RAG completo a un documento real:
`reglamento.pdf` (Reglamento Académico 2026 del Instituto Profesional Virginio
Gómez, Universidad de Concepción).

## Pre-requisitos

`.env` en la raíz del proyecto (`/Users/claudiomontoya/Desktop/cursoIpvg/.env`)
con:

```
OPENAI_API_KEY=sk-...
QDRANT_URL=https://....cloud.qdrant.io:6333
QDRANT_API_KEY=...
```

Dependencias (instalar una sola vez):

```bash
cd ejemplos/python
pip install -r requirements.txt
```

## Uso

### 1) Ingesta (correr UNA vez)

```bash
python rag/test/ingestar_reglamento.py
```

Lee `reglamento.pdf` página por página, chunkea, genera embeddings y crea
la collection `reglamento_ipvg` en Qdrant Cloud. Toma ~30 segundos.

Salida esperada:
```
📄 Leyendo reglamento.pdf…
   17 páginas con texto
   ~80 chunks generados
🧮 Generando embeddings (batches de 100)…
💾 Creando collection 'reglamento_ipvg' en Qdrant…
✅ Listo. Points en 'reglamento_ipvg': 80
```

### 2) Buscar (CLI interactiva)

```bash
python rag/test/buscar_reglamento.py
```

Ejemplo de preguntas que funcionan bien:

- ¿Cuáles son las causales de baja académica?
- ¿Qué pasa si suspendo mis estudios?
- ¿Cuáles son los derechos del estudiante?
- ¿Cómo es el proceso de titulación?
- ¿Qué nota mínima necesito para aprobar una asignatura?

El sistema responde citando las páginas del PDF de donde extrajo la
información.

## Cómo funciona (resumen)

```
PDF → pypdf → texto por página
            → chunking (~500 chars, overlap 100)
            → embedding (text-embedding-3-small, 1536 dim)
            → Qdrant upsert con payload {texto, pagina}

pregunta → embedding → Qdrant top-10 (HNSW)
                    → cross-encoder rerank → top-3
                    → GPT-4.1-nano con system prompt
                    → respuesta con citas (pág. X)
```

## Parámetros que podés ajustar

En `ingestar_reglamento.py`:
- `CHUNK_SIZE = 500` — más chico = más preciso pero más caro
- `OVERLAP = 100` — 20% del chunk

En `buscar_reglamento.py`:
- `TOP_K = 10` — cuántos candidatos saca Qdrant
- `TOP_N = 3` — cuántos llegan al LLM tras el rerank
- `CHAT_MODEL` — cambiar a `gpt-4o-mini` para más calidad y ~5× costo

## Costos por pregunta

- Embedding: 1 query × ~$0.00001
- LLM: ~1500 tokens input + 200 output × ~$0.00015
- Qdrant Cloud: gratis (free tier)
- Rerank: gratis (corre local)

**~$0.0002 por pregunta.**
