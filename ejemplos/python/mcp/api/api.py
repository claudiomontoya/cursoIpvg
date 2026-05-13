"""
api.py — REST API tradicional para la tienda IPVG.

Endpoints:
    GET    /api/productos?q=&categoria=     — catálogo (búsqueda opcional)
    GET    /api/carrito                     — carrito actual (usuario demo único)
    POST   /api/carrito/agregar             — body: {producto_id, cantidad}
    POST   /api/carrito/actualizar          — body: {producto_id, cantidad}
    POST   /api/carrito/quitar              — body: {producto_id}
    POST   /api/carrito/vaciar              — borra todos los items
    POST   /api/carrito/finalizar           — checkout, devuelve la orden
    GET    /                                — sirve index.html

Correr (desde mcp/api/):
    uvicorn api:app --reload --port 8040
"""

import sys
from pathlib import Path

# Permite importar db.py desde el mismo directorio sin instalar como package
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import db

USUARIO = db.USUARIO_DEMO

app = FastAPI(title="Tienda IPVG · API REST")
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


# ---------- Schemas ----------

class AgregarRequest(BaseModel):
    producto_id: str
    cantidad: int = 1


class ActualizarRequest(BaseModel):
    producto_id: str
    cantidad: int


class QuitarRequest(BaseModel):
    producto_id: str


# ---------- Endpoints ----------

@app.get("/api/productos")
def listar_productos(q: str = "", categoria: str | None = None):
    return {"items": db.buscar_productos(q, categoria)}


@app.get("/api/carrito")
def ver_carrito():
    return db.carrito_resumen(USUARIO)


@app.post("/api/carrito/agregar")
def agregar(req: AgregarRequest):
    try:
        return db.agregar(USUARIO, req.producto_id, req.cantidad)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/carrito/actualizar")
def actualizar(req: ActualizarRequest):
    try:
        return db.actualizar_cantidad(USUARIO, req.producto_id, req.cantidad)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/carrito/quitar")
def quitar(req: QuitarRequest):
    return db.quitar(USUARIO, req.producto_id)


@app.post("/api/carrito/vaciar")
def vaciar():
    return db.vaciar(USUARIO)


@app.post("/api/carrito/finalizar")
def finalizar():
    try:
        return db.finalizar(USUARIO)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
