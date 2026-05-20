/**
 * db.ts — "Base de datos" en un archivo JSON local.
 *
 * Versión equivalente a ../api/db.ts pero SIN MongoDB. Toda la persistencia
 * vive en `data.json` (mismo directorio). Ideal para arrancar en cualquier
 * máquina con solo Node — no necesita Docker, no necesita Mongo, no abre
 * puertos extra.
 *
 * Estrategia de concurrencia: cada operación es
 *   1. readFileSync (cargar todo el JSON en memoria)
 *   2. mutar el objeto
 *   3. writeFileSync (volcar todo de nuevo)
 *
 * Como Node es mono-proceso y readFileSync/writeFileSync son síncronos,
 * no hay race conditions DENTRO del proceso. Si corrés N instancias del
 * server contra el mismo archivo, sí podés perder writes — pero para una
 * demo de curso es suficiente.
 *
 * Las firmas son IDÉNTICAS a ../api/db.ts → `api.ts` apenas cambia el import.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { randomUUID } from 'node:crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_FILE = path.join(__dirname, 'data.json');

export const USUARIO_DEMO = 'usuario_demo';

// ---------- Tipos ----------

export interface Producto {
  _id: string;
  nombre: string;
  categoria: string;
  precio: number;
  stock: number;
  descripcion?: string;
}

export interface ItemCarrito {
  producto_id: string;
  cantidad: number;
}

export interface ItemEnriquecido {
  producto_id: string;
  nombre: string;
  categoria: string;
  precio_unitario: number;
  cantidad: number;
  subtotal: number;
}

export interface ResumenCarrito {
  user_id: string;
  items: ItemEnriquecido[];
  total: number;
}

export interface Orden extends ResumenCarrito {
  orden_id: string;
  fecha: string;
  estado: 'confirmada' | 'cancelada';
}

interface State {
  productos: Producto[];
  carritos: Record<string, { items: ItemCarrito[] }>;
  ordenes: Orden[];
}

const STATE_VACIO: State = { productos: [], carritos: {}, ordenes: [] };

// ---------- Acceso al archivo ----------

function loadState(): State {
  if (!existsSync(DATA_FILE)) {
    mkdirSync(path.dirname(DATA_FILE), { recursive: true });
    writeFileSync(DATA_FILE, JSON.stringify(STATE_VACIO, null, 2));
    return structuredClone(STATE_VACIO);
  }
  const raw = readFileSync(DATA_FILE, 'utf-8');
  const parsed = JSON.parse(raw) as Partial<State>;
  return {
    productos: parsed.productos ?? [],
    carritos: parsed.carritos ?? {},
    ordenes: parsed.ordenes ?? [],
  };
}

function saveState(state: State): void {
  writeFileSync(DATA_FILE, JSON.stringify(state, null, 2));
}

// Exponemos `setState` para que seed.ts pueda reemplazar todo el catálogo
export function setProductos(productos: Producto[]): void {
  const state = loadState();
  state.productos = productos;
  saveState(state);
}

export function countProductos(): number {
  return loadState().productos.length;
}

export function dataFilePath(): string {
  return DATA_FILE;
}

// ---------- Helpers ----------

function _productoPorId(state: State, producto_id: string): Producto | undefined {
  return state.productos.find((p) => p._id === producto_id);
}

function _carritoOCrear(state: State, userId: string): { items: ItemCarrito[] } {
  if (!state.carritos[userId]) {
    state.carritos[userId] = { items: [] };
  }
  return state.carritos[userId];
}

function _enriquecer(state: State, userId: string): ResumenCarrito {
  const carrito = state.carritos[userId] ?? { items: [] };
  const items: ItemEnriquecido[] = [];
  let total = 0;

  for (const it of carrito.items) {
    const p = _productoPorId(state, it.producto_id);
    if (!p) continue;
    const subtotal = p.precio * it.cantidad;
    items.push({
      producto_id: p._id,
      nombre: p.nombre,
      categoria: p.categoria,
      precio_unitario: p.precio,
      cantidad: it.cantidad,
      subtotal,
    });
    total += subtotal;
  }

  return { user_id: userId, items, total };
}

// ---------- API pública ----------

export async function carritoResumen(
  userId: string = USUARIO_DEMO,
): Promise<ResumenCarrito> {
  return _enriquecer(loadState(), userId);
}

export async function agregar(
  userId: string,
  producto_id: string,
  cantidad: number = 1,
): Promise<ResumenCarrito> {
  if (cantidad <= 0) throw new Error('cantidad debe ser > 0');
  const state = loadState();
  if (!_productoPorId(state, producto_id)) {
    throw new Error(`producto '${producto_id}' no existe`);
  }
  const carrito = _carritoOCrear(state, userId);
  const existente = carrito.items.find((i) => i.producto_id === producto_id);
  if (existente) existente.cantidad += cantidad;
  else carrito.items.push({ producto_id, cantidad });
  saveState(state);
  return _enriquecer(state, userId);
}

export async function actualizarCantidad(
  userId: string,
  producto_id: string,
  cantidad: number,
): Promise<ResumenCarrito> {
  if (cantidad <= 0) return quitar(userId, producto_id);
  const state = loadState();
  if (!_productoPorId(state, producto_id)) {
    throw new Error(`producto '${producto_id}' no existe`);
  }
  const carrito = _carritoOCrear(state, userId);
  const item = carrito.items.find((i) => i.producto_id === producto_id);
  if (item) item.cantidad = cantidad;
  else carrito.items.push({ producto_id, cantidad });
  saveState(state);
  return _enriquecer(state, userId);
}

export async function quitar(
  userId: string,
  producto_id: string,
): Promise<ResumenCarrito> {
  const state = loadState();
  const carrito = _carritoOCrear(state, userId);
  carrito.items = carrito.items.filter((i) => i.producto_id !== producto_id);
  saveState(state);
  return _enriquecer(state, userId);
}

export async function vaciar(userId: string): Promise<ResumenCarrito> {
  const state = loadState();
  _carritoOCrear(state, userId).items = [];
  saveState(state);
  return _enriquecer(state, userId);
}

export async function finalizar(userId: string): Promise<Orden> {
  const state = loadState();
  const resumen = _enriquecer(state, userId);
  if (!resumen.items.length) throw new Error('el carrito está vacío');

  const orden: Orden = {
    ...resumen,
    orden_id: randomUUID(),
    fecha: new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00'),
    estado: 'confirmada',
  };
  state.ordenes.push(orden);
  if (state.carritos[userId]) state.carritos[userId].items = [];
  saveState(state);
  return orden;
}

export async function buscarProductos(
  query: string = '',
  categoria: string | null = null,
  limite: number = 20,
): Promise<Producto[]> {
  const state = loadState();
  const q = query.toLowerCase();
  let res = state.productos;
  if (q) {
    res = res.filter(
      (p) =>
        p.nombre.toLowerCase().includes(q) ||
        (p.descripcion ?? '').toLowerCase().includes(q),
    );
  }
  if (categoria) res = res.filter((p) => p.categoria === categoria);
  return res.slice(0, limite);
}
