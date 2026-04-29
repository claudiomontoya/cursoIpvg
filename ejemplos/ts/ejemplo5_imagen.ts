/**
 * Ejemplo 5 · Análisis de imagen (multimodal)
 * ============================================
 * Qué enseña:
 *   - Los modelos omni aceptan texto + imagen en un mismo mensaje
 *   - Dos formas de enviar imagen: URL pública o archivo local (base64)
 *   - El 'content' del mensaje puede ser un array de partes
 *
 * Nota: usamos base64 como método principal porque muchos dominios
 * (Wikipedia, sitios con bot protection) bloquean la descarga por OpenAI.
 */

import 'dotenv/config';
import OpenAI from 'openai';
import { readFileSync, existsSync } from 'node:fs';
import { extname } from 'node:path';

const client = new OpenAI();

// ---------------------------------------------------------------
// OPCIÓN A · Imagen por URL pública
// ---------------------------------------------------------------
async function analizarPorUrl(url: string, pregunta: string): Promise<string> {
  const response = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: pregunta },
          { type: 'image_url', image_url: { url } },
        ],
      },
    ],
  });
  return response.choices[0].message.content ?? '';
}

// ---------------------------------------------------------------
// OPCIÓN B · Imagen local codificada como base64 (más robusta)
// ---------------------------------------------------------------
function encodeImageBase64(path: string): string {
  return readFileSync(path).toString('base64');
}

async function analizarArchivoLocal(path: string, pregunta: string): Promise<string> {
  const b64 = encodeImageBase64(path);

  // Detectar el media type por la extensión
  const ext = extname(path).slice(1).toLowerCase();
  const mediaTypeMap: Record<string, string> = {
    jpg: 'jpeg',
    jpeg: 'jpeg',
    png: 'png',
    webp: 'webp',
    gif: 'gif',
  };
  const mediaType = mediaTypeMap[ext] ?? 'jpeg';

  const response = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: pregunta },
          {
            type: 'image_url',
            image_url: { url: `data:image/${mediaType};base64,${b64}` },
          },
        ],
      },
    ],
  });
  return response.choices[0].message.content ?? '';
}

// ---------------------------------------------------------------
// Demo
// ---------------------------------------------------------------
console.log('='.repeat(60));
console.log(' EJEMPLO 5 · Análisis de imagen (multimodal)');
console.log('='.repeat(60));

const IMG_LOCAL = './imagenes/demo.jpg';

console.log(`\n[Demo A] Imagen local vía base64 (${IMG_LOCAL})`);

if (existsSync(IMG_LOCAL)) {
  const descripcion = await analizarArchivoLocal(
    IMG_LOCAL,
    'Describe esta imagen en 2 frases. ¿Qué hay en ella? ¿De qué color?'
  );
  console.log(`\n🤖 Respuesta:\n   ${descripcion}`);
} else {
  console.log(`   ⚠️  Falta ${IMG_LOCAL} — descarga cualquier imagen JPG/PNG a esa ruta.`);
}

// Demo secundaria (descomentar si querés probar con URL):
//
// const URL_DEMO = 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400';
// const descUrl = await analizarPorUrl(URL_DEMO, '¿Qué ves?');
// console.log(`\n🤖 (URL): ${descUrl}`);

// ==========================================================================
// MORALEJA
// ==========================================================================
console.log('\n' + '='.repeat(60));
console.log("☝️  'content' puede ser un ARRAY con texto + imagen.");
console.log('   La imagen va como URL pública o como data URL base64.');
console.log('');
console.log('   Límites típicos:');
console.log('   - Hasta 20 imágenes por mensaje');
console.log('   - Hasta 20 MB por imagen');
console.log('   - Formatos: JPEG, PNG, WebP, GIF (no animado)');
console.log('');
console.log("   💡 Para OCR o imágenes con texto pequeño: detail: 'high'");
console.log('      en image_url (más caro pero mucho más preciso).');
console.log('='.repeat(60));
