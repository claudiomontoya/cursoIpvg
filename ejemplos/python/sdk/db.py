"""
Helper compartido · SQLite
===========================
Centraliza la creación de la base de datos para que todos los ejemplos
escriban en el mismo archivo `sdk_demo.db`.

Tablas:
  - mensajes          → cada interacción usuario↔modelo
  - metricas          → tokens, latencia y costo por llamada
  - sesiones          → identifica conversaciones con memoria
  - tool_calls        → trazas de function calling
"""

import sqlite3
from pathlib import Path

# Misma carpeta que los ejemplos → fácil de inspeccionar con un visor SQLite
DB_PATH = Path(__file__).parent / "sdk_demo.db"


def conectar() -> sqlite3.Connection:
    """
    Abre la conexión, asegura que las tablas existan y la devuelve.
    Usa row_factory para que los SELECT devuelvan dicts en vez de tuplas.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL,
            creada_en    TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS mensajes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id    INTEGER,
            rol          TEXT NOT NULL,        -- system | user | assistant | tool
            contenido    TEXT NOT NULL,
            creado_en    TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (sesion_id) REFERENCES sesiones(id)
        );

        CREATE TABLE IF NOT EXISTS metricas (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            ejemplo           TEXT NOT NULL,
            modelo            TEXT NOT NULL,
            tokens_prompt     INTEGER,
            tokens_respuesta  INTEGER,
            tokens_total      INTEGER,
            latencia_ms       INTEGER,
            costo_usd         REAL,
            creado_en         TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS tool_calls (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id    INTEGER,
            herramienta  TEXT NOT NULL,
            argumentos   TEXT,
            resultado    TEXT,
            creado_en    TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    return conn


def crear_sesion(conn: sqlite3.Connection, nombre: str) -> int:
    """Inserta una nueva sesión y devuelve su id (para usar como FK)."""
    cur = conn.cursor()
    cur.execute("INSERT INTO sesiones (nombre) VALUES (?)", (nombre,))
    conn.commit()
    return cur.lastrowid


# Precios aproximados por 1M de tokens (USD) — actualizar si cambian
PRECIOS = {
    "gpt-5.2":     {"in": 1.75, "out": 14.00},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4o":      {"in": 2.50, "out": 10.00},
}


def calcular_costo(modelo: str, tokens_in: int, tokens_out: int) -> float:
    """
    Devuelve el costo en USD de una llamada.
    Si el modelo no está en la tabla, retorna 0 (no rompemos el ejemplo).
    """
    p = PRECIOS.get(modelo)
    if not p:
        return 0.0
    return (tokens_in / 1_000_000) * p["in"] + (tokens_out / 1_000_000) * p["out"]
