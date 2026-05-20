# Tienda IPVG · versión TypeScript (Node + Fastify + MongoDB)

Equivalente exacto de [`../python/mcp/api/`](../../python/mcp/api/) pero
escrito en **TypeScript** sobre Node. Mismo dominio, mismos endpoints, mismo
HTML, **mismo MongoDB**.

## Stack

| Pieza        | Python (FastAPI)         | TS (esta carpeta)              |
|--------------|--------------------------|--------------------------------|
| Framework    | FastAPI                  | **Fastify**                    |
| Driver Mongo | pymongo                  | **mongodb (driver oficial)**   |
| Runtime      | python 3.11              | **Node 18+ con tsx**           |
| Schema       | Pydantic                 | tipos TS                       |
| Puerto       | 8040                     | **8041** (para coexistir)      |
| DB           | `tienda_ipvg`            | `tienda_ipvg` (la MISMA)       |

Como comparten la base, podés:

1. Levantar la versión Python y agregar 2 cafés.
2. Levantar la versión TS y verlos en su carrito.
3. Vaciar desde TS — la Python también se vacía al refrescar.

Es la misma demostración que se da en la slide 39 (MCP vs Tool): **el dominio
se escribe una vez en la base, la "puerta" la elegís según el cliente**.

## Setup

Pre-requisito: **MongoDB 4 corriendo en localhost:27017** con `admin/admin123`
(usa el mismo contenedor que el Python — o levantalo con `docker-compose up -d`
en `../python/mcp/api/`).

```bash
cd ejemplos/ts
npm install --legacy-peer-deps
```

## Correr

### 1) Sembrar productos (una sola vez)

```bash
npm run api:seed
```

Salida esperada: `✅ 20 productos en la collection productos.`

> Si ya corriste el seed en Python, los productos ya están. Podés saltarte
> este paso o correrlo para "resetear" el catálogo.

### 2) Servir la app

```bash
npm run api:serve
# → http://localhost:8041
```

## Endpoints

Idénticos al Python:

| Método | Ruta                          | Body                                      |
|--------|-------------------------------|-------------------------------------------|
| GET    | `/api/productos?q=&categoria=`| -                                         |
| GET    | `/api/carrito`                | -                                         |
| POST   | `/api/carrito/agregar`        | `{producto_id, cantidad}`                 |
| POST   | `/api/carrito/actualizar`     | `{producto_id, cantidad}`                 |
| POST   | `/api/carrito/quitar`         | `{producto_id}`                           |
| POST   | `/api/carrito/vaciar`         | -                                         |
| POST   | `/api/carrito/finalizar`      | -                                         |

Probarlos con `curl`:

```bash
curl http://localhost:8041/api/productos?categoria=libros | jq
curl -X POST http://localhost:8041/api/carrito/agregar \
  -H "Content-Type: application/json" \
  -d '{"producto_id":"caf-001","cantidad":2}' | jq
```

## Estructura

```text
ts/api/
├── db.ts                # cliente Mongo + lógica de carrito (mirror de db.py)
├── seed.ts              # CLI para sembrar productos
├── api.ts               # Fastify server + rutas
└── static/index.html    # mismo HTML que el Python — sin build
```

## Comparación Python ↔ TS

| Operación              | Python (`db.py`)                | TS (`db.ts`)                                 |
|------------------------|---------------------------------|----------------------------------------------|
| Insertar item / sumar  | `update_one(... $inc ...)`      | `await col.updateOne(... $inc ...)`          |
| Schema en endpoint     | `pydantic.BaseModel`            | `Body` genérico de Fastify (`Body: {...}`)  |
| Conexión               | `MongoClient(uri)`              | `await new MongoClient(uri).connect()`       |
| Dispatcher             | decoradores `@app.post`         | métodos `app.post<{Body}>('/path', ...)`     |

Las dos APIs producen exactamente el mismo JSON. La UI no nota la diferencia.
