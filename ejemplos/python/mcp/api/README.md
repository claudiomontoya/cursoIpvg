# Tienda IPVG · API REST + Webapp clásica

Sistema completo de catálogo + carrito de compras. **API REST tradicional con
botones** — sin chat ni MCP. Es la versión "tradicional" para comparar después
con [`../api_mcp/`](../api_mcp/) que reexpone la misma lógica por MCP + chat.

## Stack

- **MongoDB 4** en `localhost:27017` con `admin/admin123`
- **FastAPI** sirviendo API + HTML estático
- **HTML/CSS/JS vanilla** (sin frameworks ni build)
- 20 productos demo en 4 categorías (libros · útiles · cafetería · merch)

## Setup

### 1) Levantar MongoDB 4

```bash
cd mcp/api
docker-compose up -d
# verificar: docker ps | grep ipvg-mongo
```

### 2) Sembrar productos

```bash
cd ejemplos/python
source venv/bin/activate
python mcp/api/seed.py
```

Salida esperada: `✅ 20 productos en la collection productos.`

### 3) Correr la app

Desde `mcp/api/`:

```bash
cd ejemplos/python/mcp/api
/Users/.../venv/bin/uvicorn api:app --reload --port 8040
```

Abrir [http://localhost:8040](http://localhost:8040).

## Endpoints REST

| Método | Ruta                          | Body                                      |
|--------|-------------------------------|-------------------------------------------|
| GET    | `/api/productos?q=&categoria=`| -                                         |
| GET    | `/api/carrito`                | -                                         |
| POST   | `/api/carrito/agregar`        | `{producto_id, cantidad}`                 |
| POST   | `/api/carrito/actualizar`     | `{producto_id, cantidad}`                 |
| POST   | `/api/carrito/quitar`         | `{producto_id}`                           |
| POST   | `/api/carrito/vaciar`         | -                                         |
| POST   | `/api/carrito/finalizar`      | -                                         |

Swagger UI en [http://localhost:8040/docs](http://localhost:8040/docs).

## Modelo de datos en MongoDB

```text
db: tienda_ipvg
  ├── productos       _id, nombre, categoria, precio, stock, descripcion
  ├── carritos        user_id, items[{producto_id, cantidad}]
  └── ordenes         items[], total, fecha, estado, orden_id
```

> Para esta demo hay un único `user_id = "usuario_demo"`. En un sistema real
> esto vendría del token de sesión.
