# Tienda IPVG · Chat + MCP + Agents SDK

Misma tienda que [`../api/`](../api/) — **mismo MongoDB, mismos productos, mismo
carrito** — pero la interacción es por **chat natural** en lugar de botones.

El backend usa **OpenAI Agents SDK** consumiendo un **MCP server** que expone
las operaciones de carrito como tools. Si vacías por chat, se vacía también
en la otra webapp (comparten DB).

## Cómo funciona

```text
┌──────────────────────┐                    ┌────────────────────────┐
│  /static/index.html  │                    │  ../api/api.py (REST)  │
│  (chat + cart panel) │                    │  + ../api/static       │
└──────────┬───────────┘                    └───────────┬────────────┘
           │                                            │
           ▼                                            ▼
┌──────────────────────┐                    ┌────────────────────────┐
│   app.py · FastAPI   │                    │   api.py · FastAPI     │
│   + Agents SDK       │                    │   (CRUD directo)       │
└──────────┬───────────┘                    └───────────┬────────────┘
           │                                            │
           ▼                                            │
┌──────────────────────┐                                │
│ mcp_server.py        │  ←──── MCP via streamable-http │
│ (tools: agregar,     │       en http://127.0.0.1:9001/mcp
│  quitar, finalizar…) │                                │
└──────────┬───────────┘                                │
           │                                            │
           └─────────────┬──────────────────────────────┘
                         ▼
                ┌─────────────────┐
                │   MongoDB 4     │  ← admin/admin123 en :27017
                │  (compartido)   │
                └─────────────────┘
```

## Setup

Requiere haber hecho los pasos 1 y 2 de [`../api/README.md`](../api/README.md)
(MongoDB corriendo + `seed.py` ejecutado).

## Cómo correr (3 procesos)

```bash
# Terminal 1 — MongoDB ya está corriendo (docker)

# Terminal 2 — MCP server en :9001
cd ejemplos/python
source venv/bin/activate
python mcp/api_mcp/mcp_server.py

# Terminal 3 — chatbot web en :8050
cd ejemplos/python/mcp/api_mcp
/Users/.../venv/bin/uvicorn app:app --reload --port 8050
```

Abrir [http://localhost:8050](http://localhost:8050).

## Tools que expone el MCP server

| Tool                    | Descripción                                    |
|-------------------------|------------------------------------------------|
| `buscar_productos`      | catálogo con filtro por nombre y categoría     |
| `ver_carrito`           | estado actual del carrito + total              |
| `agregar_al_carrito`    | suma cantidad si ya estaba                     |
| `actualizar_cantidad`   | setea cantidad exacta (0 → elimina)            |
| `quitar_del_carrito`    | elimina por completo                           |
| `vaciar_carrito`        | borra todos los items                          |
| `finalizar_compra`      | crea orden + vacía carrito                     |

## Ejemplos de chat que funcionan

| Pedido                                          | Tools que se invocan                      |
|-------------------------------------------------|-------------------------------------------|
| "Mostrame qué libros tienen"                    | `buscar_productos`                        |
| "Agregame un café y dos brownies"               | `buscar_productos` × 2 + `agregar_*` × 2  |
| "Cambiá el café a 3 unidades"                   | `ver_carrito` + `actualizar_cantidad`     |
| "Sacame el brownie"                             | `ver_carrito` + `quitar_del_carrito`      |
| "¿Qué tengo en el carrito?"                     | `ver_carrito`                             |
| "Vaciá todo"                                    | `vaciar_carrito`                          |
| "Finalizá la compra"                            | `ver_carrito` + `finalizar_compra`        |

## Por qué el carrito se ve siempre fresco

El endpoint `/api/chat` después de correr el agente hace un query DIRECTO a
MongoDB para obtener el carrito y lo devuelve en la response. Así el panel
lateral siempre refleja el estado real, sin depender de que el LLM lo
incluya en el texto.
