# MCP · Model Context Protocol

Ejemplos progresivos para entender qué es MCP, cómo se compara con tool calling
nativo, y cómo se integra en una aplicación real.

## Qué es MCP en una línea

> El "USB-C" entre LLMs y herramientas: un protocolo abierto donde un **servidor
> MCP** publica `tools / resources / prompts`, y cualquier **cliente MCP**
> (Claude Desktop, Cursor, este chatbot…) los usa sin reimplementarlos.

## Estructura

```
mcp/
├── 01_servidor_basico.py            ← MCP server · 2 tools (sumar, hora_actual)
├── 02_cliente_basico.py             ← cliente Python que invoca tools (sin LLM)
├── 03_servidor_reglamento.py        ← MCP server · RAG sobre el reglamento
├── 04_agente_openai_stdio.py        ← agente CLI interactivo · OpenAI + MCP server 01
├── 05_agente_reglamento_stdio.py    ← agente one-shot · OpenAI + MCP server 03
├── 06_agente_sdk_openai_http.py     ← agente con OpenAI Agents SDK + streamable-http
│
├── webapp_tool/                     ← chatbot web · tools NATIVAS de OpenAI
│   ├── app.py
│   └── static/index.html
│
├── webapp_mcp/                      ← chatbot web · mismas tools VÍA MCP
│   ├── mcp_server.py                ← server MCP HTTP en :9000 (lo reutiliza webapp_mcp_sdk)
│   ├── app.py                       ← FastAPI en :8020, cliente MCP raw (loop manual)
│   └── static/index.html
│
└── webapp_mcp_sdk/                  ← chatbot web · misma idea pero con Agents SDK
    ├── app.py                       ← FastAPI en :8030, OpenAI Agents SDK
    └── static/index.html
```

### Progresión de complejidad

| Ejemplo | LLM | Transport | UI | Qué demuestra |
|---|---|---|---|---|
| 01 + 02 | – | stdio | – | El protocolo MCP en su forma más pura |
| 03 | – | stdio | – | Cómo exponer un RAG real como server MCP |
| **04** | **OpenAI** | **stdio** | terminal | **Agente IA por API consumiendo tools por MCP** |
| **05** | **OpenAI** | **stdio** | terminal | **Mismo patrón aplicado al reglamento (caso real)** |
| **06** | **OpenAI Agents SDK** | **streamable-http** | terminal | **Misma idea pero con SDK oficial — 30 líneas, sin loop manual** |
| webapp_tool | OpenAI | (sin MCP) | web | Comparación: tools nativas inline |
| webapp_mcp | OpenAI | streamable-http | web | Webapp consumiendo MCP server externo |

## Pre-requisitos

```bash
cd ejemplos/python
source venv/bin/activate
pip install -r requirements.txt
```

`.env` en la raíz del proyecto con `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`.

Para los ejemplos que usan el reglamento, primero hay que haber corrido
`python rag/apprag_pro/ingestar.py` (crea la collection `reglamento_ipvg_pro`).

## Cómo correr cada ejemplo

### 1) Cliente directo invocando un MCP server por stdio

```bash
python mcp/02_cliente_basico.py
```

El cliente arranca el server como subproceso, hace handshake, lista tools, las
invoca. Salida esperada:

```
🔧 Tools que expone el servidor:
   · sumar          → Suma dos números enteros y devuelve el resultado.
   · hora_actual    → Devuelve la hora actual del servidor en formato ISO 8601.

sumar(17, 25)        → 42
hora_actual()        → 2026-05-13T11:22:33
```

### 2) Probar el server del reglamento con MCP Inspector

```bash
npx @modelcontextprotocol/inspector python mcp/03_servidor_reglamento.py
```

Abre una UI web donde podés probar la tool `buscar_reglamento` a mano y ver el
JSON-RPC en bruto.

### 3) Webapp con TOOLS NATIVAS

> ⚠️ Hay un **conflicto de nombres** entre la carpeta local `mcp/` y el package
> instalado `mcp`. Por eso uvicorn hay que correrlo **desde adentro** de la
> carpeta de la webapp (así el import es `app:app`, no `mcp.webapp_tool.app:app`).

```bash
cd ejemplos/python/mcp/webapp_tool
uvicorn app:app --reload --port 8010
# abrir http://localhost:8010
```

Tools definidas inline en el código. Loop de tool calling manual.

### 4) Webapp con MCP (dos terminales)

```bash
# Terminal 1 — server MCP HTTP en :9000
cd ejemplos/python
python mcp/webapp_mcp/mcp_server.py

# Terminal 2 — webapp en :8020
cd ejemplos/python/mcp/webapp_mcp
uvicorn app:app --reload --port 8020
```

### 5) Webapp con OpenAI Agents SDK + MCP (dos terminales)

Misma arquitectura que (4) pero con `openai-agents` en lugar de loop manual.
Reutiliza el MCP server de webapp_mcp/.

```bash
# Terminal 1 — server MCP HTTP en :9000 (mismo que (4))
cd ejemplos/python
python mcp/webapp_mcp/mcp_server.py

# Terminal 2 — webapp Agents SDK en :8030
cd ejemplos/python/mcp/webapp_mcp_sdk
uvicorn app:app --reload --port 8030
```

Abrir [http://localhost:8030](http://localhost:8030). El loop de tool calling
queda dentro del `Runner.run()` del SDK — vos solo definís el `Agent` y le
pasás los `mcp_servers`.

### 6) Agente CLI con Agents SDK + MCP HTTP

```bash
# Terminal 1
python mcp/webapp_mcp/mcp_server.py

# Terminal 2
python mcp/06_agente_sdk_openai_http.py "¿qué requisitos hay para titularse?"
```

Abrir http://localhost:8020. La webapp **NO sabe nada de Qdrant** — solo habla
MCP. Si tirás el server MCP (Ctrl-C en terminal 1), la webapp devuelve 503 con
un mensaje claro.

## Diferencias entre las dos webapps

| Aspecto                           | `webapp_tool/`                 | `webapp_mcp/`                                  |
|-----------------------------------|--------------------------------|------------------------------------------------|
| Dónde viven las tools             | dentro del backend FastAPI     | en un servidor MCP separado                    |
| Cómo se invocan                   | función Python directa         | `session.call_tool()` por HTTP                 |
| Acoplamiento con Qdrant/OpenAI    | la app importa todo            | la app no importa Qdrant ni cross-encoder      |
| Reutilización                     | solo desde esta app            | Claude Desktop, Cursor y otros consumen igual  |
| Latencia por tool call            | ~0 ms (in-process)             | ~20-50 ms (HTTP local)                         |
| Lock-in con proveedor             | sí (OpenAI tool format)        | no — el server es agnóstico                    |
| Complejidad inicial               | menor                          | mayor (dos procesos)                           |

**Cuándo usar cada uno:**
- **Tools nativas**: prototipo rápido, una sola app, no necesitás compartir las
  tools con nada más.
- **MCP**: producción, varias apps consumiendo lo mismo, querés que Claude
  Desktop o Cursor también las pueda usar, querés desacoplar la lógica.

## Conectar tu MCP server a Claude Desktop

Editar `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "reglamento-ipvg": {
      "command": "/Users/.../ejemplos/python/venv/bin/python",
      "args": ["/Users/.../ejemplos/python/mcp/03_servidor_reglamento.py"]
    }
  }
}
```

Reiniciar Claude Desktop. La tool `buscar_reglamento` aparece disponible y
podés preguntarle al chat de Claude cosas como _"¿Qué dice el reglamento sobre
baja académica?"_ y la responde citando los artículos.

## Notas técnicas

- **Transports**:
  - `stdio` — el cliente arranca el server como subproceso. Ideal para Claude
    Desktop y otros clientes locales.
  - `streamable-http` — el server corre como servicio HTTP. Necesario para
    webapps y servers remotos.
- **Primitivas MCP**:
  - `tools` — funciones invocables (lo que usamos en estos ejemplos).
  - `resources` — datos leíbles (archivos, queries SQL, etc).
  - `prompts` — templates de prompts reutilizables.
- **Elicitation** (novedad 2025): el server le pide input adicional al usuario
  durante una invocación.
