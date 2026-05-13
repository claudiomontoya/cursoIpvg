"""
mcp_server.py — Server MCP que expone la tienda IPVG como tools.

Es el MISMO dominio que `../api/api.py`, pero accedido por MCP. Reutiliza
`../api/db.py` para no duplicar la lógica ni los datos: ambos lados hablan
con la MISMA base MongoDB. Si vacías el carrito por chat, se vacía también
en la webapp REST.

Transport: streamable-http en http://localhost:9001/mcp

Correr:
    python mcp/api_mcp/mcp_server.py
"""

import sys
from pathlib import Path

# Importamos db.py de la carpeta hermana ../api/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

import db
from mcp.server.fastmcp import FastMCP

USUARIO = db.USUARIO_DEMO

mcp = FastMCP("tienda-ipvg", host="127.0.0.1", port=9001)


@mcp.tool()
def buscar_productos(query: str = "", categoria: str = "") -> list[dict]:
    """Busca productos en el catálogo. `query` busca en nombre y descripción
    (case-insensitive). `categoria` opcional: 'libros', 'utiles', 'cafeteria',
    'merch'. Devuelve hasta 20 productos con _id, nombre, precio, stock, etc.
    """
    return db.buscar_productos(query, categoria or None)


@mcp.tool()
def ver_carrito() -> dict:
    """Devuelve el carrito actual con sus items enriquecidos (nombre, precio,
    subtotal) y el total. Usar antes de modificar para mostrar el estado actual.
    """
    return db.carrito_resumen(USUARIO)


@mcp.tool()
def agregar_al_carrito(producto_id: str, cantidad: int = 1) -> dict:
    """Agrega `cantidad` unidades del producto al carrito. Si ya estaba, suma.
    `producto_id` es el _id del catálogo (por ejemplo 'lib-001'). Devuelve el
    carrito actualizado.
    """
    return db.agregar(USUARIO, producto_id, cantidad)


@mcp.tool()
def actualizar_cantidad(producto_id: str, cantidad: int) -> dict:
    """Setea la cantidad exacta de un producto en el carrito. Si la cantidad
    es 0 o negativa, elimina el item. Devuelve el carrito actualizado.
    """
    return db.actualizar_cantidad(USUARIO, producto_id, cantidad)


@mcp.tool()
def quitar_del_carrito(producto_id: str) -> dict:
    """Elimina por completo un producto del carrito (sin importar cantidad).
    Devuelve el carrito actualizado.
    """
    return db.quitar(USUARIO, producto_id)


@mcp.tool()
def vaciar_carrito() -> dict:
    """Vacía el carrito completo. Devuelve el carrito (vacío)."""
    return db.vaciar(USUARIO)


@mcp.tool()
def finalizar_compra() -> dict:
    """Confirma la orden con los items actuales del carrito, guarda la orden
    en la base, y deja el carrito vacío. Devuelve el resumen de la orden
    creada con su `orden_id` y `fecha`. Falla si el carrito está vacío.
    """
    return db.finalizar(USUARIO)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
