# apprag — Webapp RAG sobre el Reglamento Académico 2026

Frontend simple para hacer búsquedas semánticas sobre el reglamento del IPVG.

```
┌──────────────────────────────────────────────────────┐
│  IPVG · REGLAMENTO ACADÉMICO 2026                    │
│                                                       │
│  Asistente del reglamento                            │
│                                                       │
│  ┌────────────────────────────────────┐ ┌────────┐  │
│  │ ¿Cuáles son las causales de baja?  │ │ Buscar │  │
│  └────────────────────────────────────┘ └────────┘  │
│  [chip] [chip] [chip] [chip] [chip]                  │
│                                                       │
│  RESPUESTA                                            │
│  ───────────────────────────────────────────         │
│  Según el reglamento, las causales son... (pág. 8)   │
│                                                       │
│  FUENTES CITADAS                                      │
│  [Pág. 8] score +6.32                                │
│  Texto del chunk recuperado…                         │
│  ...                                                  │
└──────────────────────────────────────────────────────┘
```

## Pre-requisitos

1. `.env` en la raíz del proyecto con `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`.
2. Haber corrido la ingesta una vez:
   ```bash
   python rag/test/ingestar_reglamento.py
   ```
3. Dependencias instaladas:
   ```bash
   cd ejemplos/python
   pip install -r requirements.txt
   ```

## Correr la app

Desde `ejemplos/python/`:

```bash
uvicorn rag.apprag.app:app --reload --port 8000
```

Abrir [http://localhost:8000](http://localhost:8000).

La primera consulta tarda ~3s extra porque el cross-encoder de rerank se carga
en memoria (~80 MB). Las siguientes son < 1s.

## Arquitectura

```
┌─────────────────┐         POST /api/search          ┌──────────────────────┐
│  index.html     │ ───────────────────────────────► │  FastAPI app.py      │
│  (vanilla JS)   │                                   │                       │
│                 │ ◄─────────────────────────────── │  ┌────────────────┐  │
└─────────────────┘    { respuesta, fuentes[] }      │  │ embed (OpenAI) │  │
                                                       │  └───────┬────────┘  │
                                                       │          ▼            │
                                                       │  ┌────────────────┐  │
                                                       │  │ Qdrant top-10  │  │
                                                       │  └───────┬────────┘  │
                                                       │          ▼            │
                                                       │  ┌────────────────┐  │
                                                       │  │ Rerank → top-3 │  │
                                                       │  └───────┬────────┘  │
                                                       │          ▼            │
                                                       │  ┌────────────────┐  │
                                                       │  │ GPT-4.1-nano   │  │
                                                       │  └────────────────┘  │
                                                       └──────────────────────┘
```

## Endpoints

| Método | Ruta            | Descripción                                     |
|--------|-----------------|-------------------------------------------------|
| GET    | `/`             | Devuelve `index.html`                           |
| POST   | `/api/search`   | RAG: recibe `{pregunta}`, devuelve `{respuesta, fuentes}` |
| GET    | `/docs`         | Swagger UI (autogenerado por FastAPI)          |

### Schema de la request

```json
{ "pregunta": "¿Cuáles son las causales de baja académica?" }
```

### Schema de la response

```json
{
  "respuesta": "Las causales son... (pág. 8)",
  "fuentes": [
    { "texto": "...", "pagina": 8, "score": 6.32 },
    { "texto": "...", "pagina": 9, "score": 4.11 },
    { "texto": "...", "pagina": 8, "score": 2.07 }
  ]
}
```

## Probar el endpoint directamente

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cuáles son los derechos del estudiante?"}'
```

## Para producción (cosas que NO hace esta demo)

- Autenticación / rate limiting
- Caché de embeddings de queries repetidas
- Streaming de la respuesta del LLM (mejora UX)
- Logging estructurado y métricas (Recall@K, latencia)
- Frontend con framework (React/Svelte) si la UI crece
- HTTPS + dominio propio
- Health check, readiness probe, observability
