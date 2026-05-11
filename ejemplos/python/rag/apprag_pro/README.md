# apprag_pro — Versión profesional

Misma idea que `apprag/` pero con calidad de producción en el RAG:
**chunking estructural por artículo**, metadata rica, citas precisas.

## Qué cambia vs. `apprag/`

| Aspecto              | apprag (didáctico)              | apprag_pro                                       |
|----------------------|---------------------------------|--------------------------------------------------|
| Chunking             | 500 chars + overlap fijo        | Por TÍTULO + Art. Nº (regex sobre la estructura) |
| Conteo de tamaño     | caracteres                      | tokens reales (`tiktoken`)                       |
| Payload              | `{texto, pagina}`               | `{texto, pagina, articulo, titulo_seccion}`      |
| Limpieza             | nada                            | quita headers/footers repetidos                  |
| Cita en respuesta    | "(pág. 5)"                      | "(Art. 15º, pág. 5)"                             |
| Cita en UI           | badge "Pág. N"                  | badges "Art. 15º · TÍTULO V · pág. 5"            |
| Collection Qdrant    | `reglamento_ipvg`               | `reglamento_ipvg_pro` (coexisten)                |
| Top-K / Top-N        | 10 / 3                          | 12 / 4                                           |

Visualmente: cada fuente muestra el **número de artículo** como badge amarillo,
el **título de la sección** al lado, y al final **página + score**.

## Cómo funciona el chunking estructural

```
PDF
 │
 ▼  pdfplumber (página por página)
texto crudo + limpieza
 │
 ▼  recorrido línea por línea
   ┌─ ¿match TÍTULO X …? → cambia `titulo_seccion`
   ├─ ¿match Art. Nº? → flush chunk anterior, abre uno nuevo
   └─ otra línea → append al buffer
 │
 ▼  si el artículo > 400 tokens
partir por oraciones (regex sobre . ? !) manteniendo el límite
 │
 ▼  cada chunk = { texto, pagina, articulo, titulo_seccion }
embedding (text-embedding-3-small)
 │
 ▼
upsert a Qdrant
```

**Por qué este chunking es mejor:**
- Cada chunk es una **unidad semántica completa** (un artículo entero)
- Las citas son **referenciables**: "Art. 37º" es lo que un abogado citaría
- El LLM responde mejor porque cada bloque tiene contexto autónomo
- Búsquedas tipo "art 15" funcionan literalmente — el modelo de embedding
  ve el texto "Art. 15º" dentro del chunk

## Pre-requisitos

`.env` en la raíz del proyecto con `OPENAI_API_KEY`, `QDRANT_URL`,
`QDRANT_API_KEY`. Dependencias:

```bash
cd ejemplos/python
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

### 1) Ingesta (una sola vez)

```bash
python rag/apprag_pro/ingestar.py
```

Salida esperada:
```
📄 Leyendo reglamento.pdf…
   18 páginas con texto
🧩 Chunking estructural (por TÍTULO + Art.º)…
   ~85 chunks generados
   Primeros 3 artículos detectados:
     · TÍTULO I · DISPOSICIONES GENERALES   | Art. 1º     | pág. 2
     · TÍTULO II · DE LA FUNCIÓN DOCENTE    | Art. 6º     | pág. 2
     · TÍTULO III · DE LA ADMISIÓN Y MATRÍ… | Art. 10º    | pág. 3
🧮 Generando embeddings…
💾 Recreando collection 'reglamento_ipvg_pro' en Qdrant…
✅ Listo.
```

### 2) Webapp

```bash
uvicorn rag.apprag_pro.app:app --reload --port 8000
# abrir http://localhost:8000
```

## Endpoints

| Método | Ruta            | Descripción                                                  |
|--------|-----------------|--------------------------------------------------------------|
| GET    | `/`             | Devuelve `index.html`                                        |
| POST   | `/api/search`   | RAG: `{pregunta}` → `{respuesta, fuentes: [{texto, pagina, articulo, titulo_seccion, score}]}` |
| GET    | `/docs`         | Swagger UI                                                   |

### Ejemplo response

```json
{
  "respuesta": "Las causales son: reprobar dos veces una asignatura (Art. 37º, pág. 9)...",
  "fuentes": [
    {
      "texto": "Art. 37º Aquellos y aquellas estudiantes que se encuentren cursando carreras impartidas en modalidad presencial respecto a sus Programas Especiales, quedarán en situación de 'Baja Académica' o 'Pérdida de Carrera' cuando: ...",
      "pagina": 9,
      "articulo": "Art. 37º",
      "titulo_seccion": "TÍTULO X · DE LA BAJA ACADÉMICA Y DE LA CONTINUACIÓN DE ESTUDIOS",
      "score": 6.32
    }
  ]
}
```

## Decisiones técnicas

- **Sin streaming todavía**: para no agregar complejidad. Si lo queremos, hay
  que cambiar la response del endpoint a `StreamingResponse` y consumir con
  SSE en el frontend.
- **Reglex de TÍTULO/Art.**: simple y suficiente para este PDF. Si otro PDF
  tiene otra convención (por ejemplo "Artículo 15" en vez de "Art. 15º"),
  basta actualizar `RE_ARTICULO` en `ingestar.py`.
- **No usar LangChain**: el `RecursiveCharacterTextSplitter` no entiende
  estructura legal. Para reglamentos, chunking estructural a mano gana.
- **Embedding model**: igual que `apprag/` (`text-embedding-3-small`) para
  comparar de manera justa. Si querés más recall: cambiar a `-large`
  (3072 dim, 6× costo).
