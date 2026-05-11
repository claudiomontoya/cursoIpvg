# Ejemplos del SDK de OpenAI · IPVG

Material docente progresivo. Cada script es independiente y persiste lo
relevante en **`sdk_demo.db`** (SQLite, en esta misma carpeta).

## Orden sugerido

| # | Archivo | Concepto |
|---|---|---|
| 1 | `01_basico.py` | Llamada mínima a `chat.completions` |
| 2 | `02_streaming.py` | Respuestas token a token (`stream=True`) |
| 3 | `03_vision.py` | Imágenes (URL o base64 local) |
| 4 | `04_tools.py` | Function calling: el modelo invoca tus funciones |
| 5 | `05_metricas.py` | Tokens, latencia y costo USD por llamada |
| 6 | `06_memoria_sqlite.py` | Conversación persistente entre ejecuciones |
| 7 | `07_integrado.py` | Memoria + tools + métricas, todo junto |
| 8 | `08_web_search.py` | Browser integrado (Responses API + `web_search`) |
| 9 | `09_code_interpreter.py` | Ejecución de código en sandbox de OpenAI |
| 10 | `10_image_generation.py` | Generar imágenes con `gpt-5.2` + `image_generation` |
| 11 | `11_chat_terminal.py` | REPL interactivo con persistencia y streaming |

## Setup

Reusa el venv y `.env` de la carpeta padre (`ejemplos/python/`):

```bash
cd /Users/claudiomontoya/Desktop/cursoIpvg/ejemplos/python
source venv/bin/activate          # activa el entorno virtual
cd sdk
python 01_basico.py               # corre el primero
```

Si el venv no existe:

```bash
cd ejemplos/python
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # y edita con tu OPENAI_API_KEY
```

## Inspeccionar la base de datos

```bash
sqlite3 sdk_demo.db
sqlite> .tables
sqlite> SELECT * FROM metricas;
sqlite> SELECT rol, contenido FROM mensajes WHERE sesion_id = 1;
```

O con un visor gráfico (DB Browser for SQLite, TablePlus, DBeaver).

## Esquema de la BD

- **`sesiones`** — agrupa los mensajes de una conversación
- **`mensajes`** — cada turno (`system` / `user` / `assistant` / `tool`)
- **`metricas`** — tokens, latencia y costo USD por llamada
- **`tool_calls`** — trazas de function calling (qué tool, args, resultado)

Todo el código de tablas vive en `db.py`, compartido por los ejemplos SDK.
