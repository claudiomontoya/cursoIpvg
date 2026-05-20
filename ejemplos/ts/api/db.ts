/**
 * db.ts — Cliente MongoDB compartido y lógica de carrito.
 * Equivalente TypeScript de ../python/mcp/api/db.py.
 *
 * Conexión: localhost:27017 con admin/admin123. Base de datos `tienda_ipvg`
 * (la MISMA que usa el ejemplo Python — corren contra los mismos datos).
 *
 * Collections:
 *   productos  — catálogo (poblado por seed.ts)
 *   carritos   — un documento por user_id: { user_id, items: [{producto_id, cantidad}] }
 *   ordenes    — carritos confirmados con timestamp
 */

import { MongoClient, type Db, type Collection } from 'mongodb';

const MONGO_URI =
  process.env.MONGO_URI ??
  'mongodb://admin:admin123@localhost:27017/?authSource=admin';

const DB_NAME = 'tienda_ipvg';

export const USUARIO_DEMO = 'usuario_demo';

let _client: MongoClient | null = null;

export async function getClient(): Promise<MongoClient> {
  if (_client) return _client;
  _client = new MongoClient(MONGO_URI, { serverSelectionTimeoutMS: 3000 });
  await _client.connect();
  return _client;
}

export async function getDb(): Promise<Db> {
  return (await getClient()).db(DB_NAME);
}

export async function productos(): Promise<Collection> {
  return (await getDb()).collection('productos');
}

export async function carritos(): Promise<Collection> {
  return (await getDb()).collection('carritos');
}

export async function ordenes(): Promise<Collection> {
  return (await getDb()).collection('ordenes');
}

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

// ---------- Lógica de carrito ----------

async function _carritoPara(userId: string): Promise<{ items: ItemCarrito[] }> {
  const col = await carritos();
  let doc = await col.findOne({ user_id: userId });
  if (!doc) {
    await col.insertOne({ user_id: userId, items: [] });
    doc = { user_id: userId, items: [] };
  }
  return doc as { items: ItemCarrito[] };
}

async function _productoPorId(producto_id: string): Promise<Producto | null> {
  const col = await productos();
  return (await col.findOne({ _id: producto_id })) as Producto | null;
}

export async function carritoResumen(
  userId: string = USUARIO_DEMO,
): Promise<ResumenCarrito> {
  const c = await _carritoPara(userId);
  const itemsEnriquecidos: ItemEnriquecido[] = [];
  let total = 0;

  for (const it of c.items) {
    const p = await _productoPorId(it.producto_id);
    if (!p) continue;
    const subtotal = p.precio * it.cantidad;
    itemsEnriquecidos.push({
      producto_id: p._id,
      nombre: p.nombre,
      categoria: p.categoria,
      precio_unitario: p.precio,
      cantidad: it.cantidad,
      subtotal,
    });
    total += subtotal;
  }

  return { user_id: userId, items: itemsEnriquecidos, total };
}

export async function agregar(
  userId: string,
  producto_id: string,
  cantidad: number = 1,
): Promise<ResumenCarrito> {
  if (cantidad <= 0) throw new Error('cantidad debe ser > 0');
  const p = await _productoPorId(producto_id);
  if (!p) throw new Error(`producto '${producto_id}' no existe`);

  await _carritoPara(userId);
  const col = await carritos();

  // Si ya existe el item en el carrito, sumamos; si no, lo creamos
  const r = await col.updateOne(
    { user_id: userId, 'items.producto_id': producto_id },
    { $inc: { 'items.$.cantidad': cantidad } },
  );
  if (r.matchedCount === 0) {
    await col.updateOne(
      { user_id: userId },
      { $push: { items: { producto_id, cantidad } } as any },
    );
  }

  return carritoResumen(userId);
}

export async function actualizarCantidad(
  userId: string,
  producto_id: string,
  cantidad: number,
): Promise<ResumenCarrito> {
  if (cantidad <= 0) return quitar(userId, producto_id);
  if (!(await _productoPorId(producto_id))) {
    throw new Error(`producto '${producto_id}' no existe`);
  }
  const col = await carritos();
  const r = await col.updateOne(
    { user_id: userId, 'items.producto_id': producto_id },
    { $set: { 'items.$.cantidad': cantidad } },
  );
  if (r.matchedCount === 0) return agregar(userId, producto_id, cantidad);
  return carritoResumen(userId);
}

export async function quitar(
  userId: string,
  producto_id: string,
): Promise<ResumenCarrito> {
  const col = await carritos();
  await col.updateOne(
    { user_id: userId },
    { $pull: { items: { producto_id } } as any },
  );
  return carritoResumen(userId);
}

export async function vaciar(userId: string): Promise<ResumenCarrito> {
  const col = await carritos();
  await col.updateOne(
    { user_id: userId },
    { $set: { items: [] } },
    { upsert: true },
  );
  return carritoResumen(userId);
}

export async function finalizar(
  userId: string,
): Promise<ResumenCarrito & { orden_id: string; fecha: string; estado: string }> {
  const resumen = await carritoResumen(userId);
  if (!resumen.items.length) throw new Error('el carrito está vacío');

  const orden = {
    ...resumen,
    fecha: new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00'),
    estado: 'confirmada',
  };

  const col = await ordenes();
  const inserted = await col.insertOne(orden);
  await vaciar(userId);

  return { ...orden, orden_id: inserted.insertedId.toString() };
}

export async function buscarProductos(
  query: string = '',
  categoria: string | null = null,
  limite: number = 20,
): Promise<Producto[]> {
  const filtro: Record<string, unknown> = {};
  if (query) {
    filtro.$or = [
      { nombre: { $regex: query, $options: 'i' } },
      { descripcion: { $regex: query, $options: 'i' } },
    ];
  }
  if (categoria) filtro.categoria = categoria;

  const col = await productos();
  const docs = await col
    .find(filtro, {
      projection: { _id: 1, nombre: 1, precio: 1, categoria: 1, stock: 1, descripcion: 1 },
    })
    .limit(limite)
    .toArray();
  return docs as unknown as Producto[];
}
