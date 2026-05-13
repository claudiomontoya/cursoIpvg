"""
db.py — Cliente MongoDB compartido por la API REST y el MCP server.

Conexión: localhost:27017 con admin/admin123. Base de datos `tienda_ipvg`.
Collections:
    productos  — catálogo (poblado por seed.py)
    carritos   — un documento por user_id: { user_id, items: [{producto_id, cantidad}] }
    ordenes    — carritos confirmados con timestamp
"""

import os
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://admin:admin123@localhost:27017/?authSource=admin",
)
DB_NAME = "tienda_ipvg"

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client


def get_db() -> Database:
    return get_client()[DB_NAME]


def productos_col() -> Collection:
    return get_db()["productos"]


def carritos_col() -> Collection:
    return get_db()["carritos"]


def ordenes_col() -> Collection:
    return get_db()["ordenes"]


# ---------- Lógica de carrito (reutilizada por API REST y MCP server) ----------

USUARIO_DEMO = "usuario_demo"


def _carrito_para(user_id: str) -> dict:
    """Devuelve el documento del carrito; si no existe, lo crea."""
    doc = carritos_col().find_one({"user_id": user_id})
    if doc is None:
        doc = {"user_id": user_id, "items": []}
        carritos_col().insert_one(doc)
    doc.pop("_id", None)
    return doc


def _producto_por_id(producto_id: str) -> dict | None:
    return productos_col().find_one({"_id": producto_id}, {"_id": 1, "nombre": 1, "precio": 1, "categoria": 1, "stock": 1})


def carrito_resumen(user_id: str = USUARIO_DEMO) -> dict:
    """Carrito enriquecido con datos de cada producto + total."""
    c = _carrito_para(user_id)
    items_enriquecidos = []
    total = 0
    for it in c["items"]:
        p = _producto_por_id(it["producto_id"])
        if p is None:
            continue
        subtotal = p["precio"] * it["cantidad"]
        items_enriquecidos.append({
            "producto_id": p["_id"],
            "nombre": p["nombre"],
            "categoria": p["categoria"],
            "precio_unitario": p["precio"],
            "cantidad": it["cantidad"],
            "subtotal": subtotal,
        })
        total += subtotal
    return {"user_id": user_id, "items": items_enriquecidos, "total": total}


def agregar(user_id: str, producto_id: str, cantidad: int = 1) -> dict:
    if cantidad <= 0:
        raise ValueError("cantidad debe ser > 0")
    p = _producto_por_id(producto_id)
    if p is None:
        raise ValueError(f"producto '{producto_id}' no existe")
    _carrito_para(user_id)
    # Si ya existe el item en el carrito, sumamos; si no, lo creamos
    actualizado = carritos_col().update_one(
        {"user_id": user_id, "items.producto_id": producto_id},
        {"$inc": {"items.$.cantidad": cantidad}},
    )
    if actualizado.matched_count == 0:
        carritos_col().update_one(
            {"user_id": user_id},
            {"$push": {"items": {"producto_id": producto_id, "cantidad": cantidad}}},
        )
    return carrito_resumen(user_id)


def actualizar_cantidad(user_id: str, producto_id: str, cantidad: int) -> dict:
    if cantidad <= 0:
        return quitar(user_id, producto_id)
    if not _producto_por_id(producto_id):
        raise ValueError(f"producto '{producto_id}' no existe")
    r = carritos_col().update_one(
        {"user_id": user_id, "items.producto_id": producto_id},
        {"$set": {"items.$.cantidad": cantidad}},
    )
    if r.matched_count == 0:
        return agregar(user_id, producto_id, cantidad)
    return carrito_resumen(user_id)


def quitar(user_id: str, producto_id: str) -> dict:
    carritos_col().update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"producto_id": producto_id}}},
    )
    return carrito_resumen(user_id)


def vaciar(user_id: str) -> dict:
    carritos_col().update_one({"user_id": user_id}, {"$set": {"items": []}}, upsert=True)
    return carrito_resumen(user_id)


def finalizar(user_id: str) -> dict:
    """Pasa el carrito actual a la collection `ordenes`, vacía el carrito,
    devuelve el resumen de la orden creada."""
    resumen = carrito_resumen(user_id)
    if not resumen["items"]:
        raise ValueError("el carrito está vacío")
    orden = {
        **resumen,
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "estado": "confirmada",
    }
    inserted = ordenes_col().insert_one(orden)
    vaciar(user_id)
    orden["orden_id"] = str(inserted.inserted_id)
    orden.pop("_id", None)
    return orden


def buscar_productos(query: str = "", categoria: str | None = None, limite: int = 20) -> list[dict]:
    """Búsqueda case-insensitive por nombre + filtro opcional por categoría."""
    filtro: dict = {}
    if query:
        filtro["$or"] = [
            {"nombre": {"$regex": query, "$options": "i"}},
            {"descripcion": {"$regex": query, "$options": "i"}},
        ]
    if categoria:
        filtro["categoria"] = categoria
    cursor = productos_col().find(filtro, {"_id": 1, "nombre": 1, "precio": 1, "categoria": 1, "stock": 1, "descripcion": 1}).limit(limite)
    return list(cursor)
