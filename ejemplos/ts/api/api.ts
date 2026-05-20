/**
 * api.ts — REST API para la tienda IPVG (versión TypeScript con Fastify).
 *
 * Equivalente exacto de ../python/mcp/api/api.py: mismos endpoints, mismo
 * cuerpo de request/response, mismo MongoDB. Solo cambia el lenguaje y el
 * framework (FastAPI → Fastify).
 *
 * Endpoints:
 *     GET    /api/productos?q=&categoria=
 *     GET    /api/carrito
 *     POST   /api/carrito/agregar       body: { producto_id, cantidad }
 *     POST   /api/carrito/actualizar    body: { producto_id, cantidad }
 *     POST   /api/carrito/quitar        body: { producto_id }
 *     POST   /api/carrito/vaciar
 *     POST   /api/carrito/finalizar
 *     GET    /                          → index.html
 *
 * Correr:
 *     npm run api:serve
 */

import Fastify from 'fastify';
import fastifyStatic from '@fastify/static';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import * as db from './db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT ?? 8041);
const USUARIO = db.USUARIO_DEMO;

const app = Fastify({ logger: { level: 'warn' } });

// Servir archivos estáticos en /static y la raíz
await app.register(fastifyStatic, {
  root: path.join(__dirname, 'static'),
  prefix: '/static/',
});

app.get('/', (_req, reply) => {
  return reply.sendFile('index.html', path.join(__dirname, 'static'));
});

// ---------- Endpoints ----------

app.get<{ Querystring: { q?: string; categoria?: string } }>(
  '/api/productos',
  async (req) => {
    const { q = '', categoria } = req.query;
    return { items: await db.buscarProductos(q, categoria ?? null) };
  },
);

app.get('/api/carrito', async () => {
  return db.carritoResumen(USUARIO);
});

app.post<{ Body: { producto_id: string; cantidad?: number } }>(
  '/api/carrito/agregar',
  async (req, reply) => {
    const { producto_id, cantidad = 1 } = req.body;
    try {
      return await db.agregar(USUARIO, producto_id, cantidad);
    } catch (e) {
      return reply.code(400).send({ detail: (e as Error).message });
    }
  },
);

app.post<{ Body: { producto_id: string; cantidad: number } }>(
  '/api/carrito/actualizar',
  async (req, reply) => {
    const { producto_id, cantidad } = req.body;
    try {
      return await db.actualizarCantidad(USUARIO, producto_id, cantidad);
    } catch (e) {
      return reply.code(400).send({ detail: (e as Error).message });
    }
  },
);

app.post<{ Body: { producto_id: string } }>(
  '/api/carrito/quitar',
  async (req) => {
    return db.quitar(USUARIO, req.body.producto_id);
  },
);

app.post('/api/carrito/vaciar', async () => {
  return db.vaciar(USUARIO);
});

app.post('/api/carrito/finalizar', async (_req, reply) => {
  try {
    return await db.finalizar(USUARIO);
  } catch (e) {
    return reply.code(400).send({ detail: (e as Error).message });
  }
});

// ---------- Start ----------

try {
  await app.listen({ port: PORT, host: '0.0.0.0' });
  console.log(`🚀 Tienda IPVG (TS) escuchando en http://localhost:${PORT}`);
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
