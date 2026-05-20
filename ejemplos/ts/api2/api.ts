/**
 * api.ts — REST API igual a ../api/api.ts pero respaldada por data.json.
 *
 * Idéntico contrato HTTP que las otras dos versiones (Python + TS+Mongo):
 * mismas rutas, mismos bodies, mismas responses. Solo cambia de dónde sale
 * la data — acá vive en disco como JSON, no en MongoDB.
 *
 * Correr:
 *     npm run api2:serve
 */

import Fastify from 'fastify';
import fastifyStatic from '@fastify/static';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import * as db from './db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT ?? 8042);
const USUARIO = db.USUARIO_DEMO;

const app = Fastify({ logger: { level: 'warn' } });

await app.register(fastifyStatic, {
  root: path.join(__dirname, 'static'),
  prefix: '/static/',
});

app.get('/', (_req, reply) => {
  return reply.sendFile('index.html', path.join(__dirname, 'static'));
});

// ---------- Endpoints (mismo contrato que ../api/api.ts) ----------

app.get<{ Querystring: { q?: string; categoria?: string } }>(
  '/api/productos',
  async (req) => {
    const { q = '', categoria } = req.query;
    return { items: await db.buscarProductos(q, categoria ?? null) };
  },
);

app.get('/api/carrito', async () => db.carritoResumen(USUARIO));

app.post<{ Body: { producto_id: string; cantidad?: number } }>(
  '/api/carrito/agregar',
  async (req, reply) => {
    try {
      return await db.agregar(USUARIO, req.body.producto_id, req.body.cantidad ?? 1);
    } catch (e) {
      return reply.code(400).send({ detail: (e as Error).message });
    }
  },
);

app.post<{ Body: { producto_id: string; cantidad: number } }>(
  '/api/carrito/actualizar',
  async (req, reply) => {
    try {
      return await db.actualizarCantidad(USUARIO, req.body.producto_id, req.body.cantidad);
    } catch (e) {
      return reply.code(400).send({ detail: (e as Error).message });
    }
  },
);

app.post<{ Body: { producto_id: string } }>(
  '/api/carrito/quitar',
  async (req) => db.quitar(USUARIO, req.body.producto_id),
);

app.post('/api/carrito/vaciar', async () => db.vaciar(USUARIO));

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
  console.log(`🚀 Tienda IPVG (TS · JSON) escuchando en http://localhost:${PORT}`);
  console.log(`   Persistencia en: ${db.dataFilePath()}`);
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
