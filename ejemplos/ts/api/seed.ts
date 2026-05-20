/**
 * seed.ts — Pobla la collection `productos` con 20 productos demo.
 *
 * Mismos 20 productos que el Python (../python/mcp/api/seed.py) y la MISMA
 * collection — el ejemplo TS y el Python son intercambiables.
 *
 * Idempotente: si la collection ya existe, la limpia y rellena de nuevo.
 *
 * Correr:
 *     npm run api:seed
 */

import { productos, getClient } from './db.js';

const PRODUCTOS = [
  // ----- Libros (5) -----
  { _id: 'lib-001', nombre: 'Python para Analista Programador',     categoria: 'libros', precio: 18500, stock: 25, descripcion: 'Manual oficial de la carrera. Cubre sintaxis, OOP, archivos, APIs.' },
  { _id: 'lib-002', nombre: 'Introducción a la IA Generativa',      categoria: 'libros', precio: 22000, stock: 18, descripcion: 'LLMs, embeddings, RAG y agentes explicados desde cero.' },
  { _id: 'lib-003', nombre: 'Bases de Datos · Teoría y Práctica',   categoria: 'libros', precio: 19500, stock: 30, descripcion: 'Modelado relacional, SQL avanzado, NoSQL, MongoDB.' },
  { _id: 'lib-004', nombre: 'Redes y Ciberseguridad Básica',        categoria: 'libros', precio: 21000, stock: 12, descripcion: 'TCP/IP, firewalls, criptografía, OWASP Top 10.' },
  { _id: 'lib-005', nombre: 'Soft Skills para Programadores',       categoria: 'libros', precio: 14500, stock: 40, descripcion: 'Comunicación, trabajo en equipo, presentaciones técnicas.' },

  // ----- Útiles (5) -----
  { _id: 'uti-001', nombre: 'Cuaderno IPVG · 100 hojas',            categoria: 'utiles', precio: 3500,  stock: 120, descripcion: 'Cuaderno tapa dura con logo institucional.' },
  { _id: 'uti-002', nombre: 'Set de lápices grafito + goma',        categoria: 'utiles', precio: 2200,  stock: 200, descripcion: '6 lápices HB + goma de borrar profesional.' },
  { _id: 'uti-003', nombre: 'Resaltadores pack x4',                 categoria: 'utiles', precio: 4500,  stock: 80,  descripcion: 'Amarillo, verde, rosa, azul. Punta biselada.' },
  { _id: 'uti-004', nombre: 'Calculadora científica',               categoria: 'utiles', precio: 12500, stock: 35,  descripcion: '240 funciones, modo estadística. Imprescindible cálculo I/II.' },
  { _id: 'uti-005', nombre: 'Mochila para laptop 15.6"',            categoria: 'utiles', precio: 28900, stock: 22,  descripcion: 'Compartimento acolchado + puerto USB externo.' },

  // ----- Café y snacks (5) -----
  { _id: 'caf-001', nombre: 'Café americano',                       categoria: 'cafeteria', precio: 1500, stock: 999, descripcion: 'Café de grano recién molido. 240 ml.' },
  { _id: 'caf-002', nombre: 'Cappuccino',                           categoria: 'cafeteria', precio: 2200, stock: 999, descripcion: 'Espresso doble + leche vaporizada + canela.' },
  { _id: 'caf-003', nombre: 'Té de hierbas',                        categoria: 'cafeteria', precio: 1300, stock: 999, descripcion: 'Selección de manzanilla, menta o frutos rojos.' },
  { _id: 'caf-004', nombre: 'Sandwich de jamón y queso',            categoria: 'cafeteria', precio: 3500, stock: 50,  descripcion: 'Pan ciabatta tostado, jamón de pavo, queso mantecoso.' },
  { _id: 'caf-005', nombre: 'Brownie casero',                       categoria: 'cafeteria', precio: 2200, stock: 60,  descripcion: 'Receta de la abuela. Con chips de chocolate amargo.' },

  // ----- Merch institucional (5) -----
  { _id: 'mer-001', nombre: 'Taza IPVG · cerámica blanca',          categoria: 'merch', precio: 6500,  stock: 80, descripcion: '330 ml. Logo institucional impreso por sublimación.' },
  { _id: 'mer-002', nombre: 'Polera IPVG · algodón',                categoria: 'merch', precio: 12500, stock: 60, descripcion: 'Tallas S/M/L/XL. Color azul institucional.' },
  { _id: 'mer-003', nombre: 'Gorro IPVG',                           categoria: 'merch', precio: 7500,  stock: 70, descripcion: 'Regulable. Bordado al frente.' },
  { _id: 'mer-004', nombre: 'Sticker pack IPVG · 10 piezas',        categoria: 'merch', precio: 2500,  stock: 200, descripcion: 'Para laptop, botella, mochila. Vinilo resistente.' },
  { _id: 'mer-005', nombre: 'Botella térmica IPVG · 500ml',         categoria: 'merch', precio: 14900, stock: 45, descripcion: 'Acero inoxidable. Mantiene calor/frío 12h.' },
];

async function main(): Promise<void> {
  try {
    const client = await getClient();
    await client.db('admin').command({ ping: 1 });
  } catch (e) {
    console.error('❌ No puedo conectarme a MongoDB.');
    console.error('   Levantá la base:  cd ../python/mcp/api && docker-compose up -d');
    console.error('   Error original:', (e as Error).message);
    process.exit(1);
  }

  const col = await productos();
  await col.deleteMany({});
  await col.insertMany(PRODUCTOS as any);
  const count = await col.countDocuments();
  console.log(`✅ ${count} productos en la collection \`productos\`.`);
  console.log('   Categorías:', [...new Set(PRODUCTOS.map((p) => p.categoria))].sort());

  await (await getClient()).close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
