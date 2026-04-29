/**
 * Ejemplo 6 · Análisis de PDF
 * ============================
 * Qué enseña:
 *   Dos formas de darle un PDF al modelo:
 *
 *   (A) Files API · el modelo lee el PDF NATIVAMENTE (texto + imágenes + tablas)
 *       → mejor para documentos ricos, escaneados, con layout importante
 *
 *   (B) Extracción local con pdf-parse · solo el texto, enviado inline
 *       → más barato, más simple, más rápido
 *       → pierde imágenes y layout
 */

import 'dotenv/config';
import OpenAI from 'openai';
import { readFileSync, existsSync, createReadStream } from 'node:fs';
import pdfParse from 'pdf-parse';

const client = new OpenAI();

const PDF_PATH = './documentos/documento.pdf';

// ---------------------------------------------------------------
// OPCIÓN A · Files API (PDF nativo)
// ---------------------------------------------------------------
async function analizarConFilesApi(pdfPath: string, pregunta: string): Promise<string> {
  // 1. Subir el archivo a la Files API
  const archivo = await client.files.create({
    file: createReadStream(pdfPath),
    purpose: 'user_data',
  });

  console.log(`   📤 PDF subido a OpenAI. file_id: ${archivo.id}`);

  // 2. Referenciarlo en un mensaje multimodal
  const response = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: pregunta },
          { type: 'file', file: { file_id: archivo.id } },
        ],
      },
    ],
  });
  return response.choices[0].message.content ?? '';
}

// ---------------------------------------------------------------
// OPCIÓN B · Extracción local con pdf-parse (solo texto)
// ---------------------------------------------------------------
async function analizarExtrayendoTexto(pdfPath: string, pregunta: string): Promise<string> {
  // 1. Extraer texto de todas las páginas
  const buffer = readFileSync(pdfPath);
  const pdf = await pdfParse(buffer);

  // 2. Truncar si es muy largo (proteger el context window)
  let texto = pdf.text;
  if (texto.length > 50_000) {
    texto = texto.slice(0, 50_000) + '\n\n[... documento truncado ...]';
  }

  console.log(`   📄 Texto extraído: ${texto.length} caracteres, ${pdf.numpages} páginas`);

  // 3. Llamada al modelo con el texto dentro de tags <doc>
  const response = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'system',
        content:
          'Respondes usando SOLO el contenido del documento. ' +
          'Si la información no aparece, dilo explícitamente.',
      },
      {
        role: 'user',
        content: `Documento:\n<doc>\n${texto}\n</doc>\n\n${pregunta}`,
      },
    ],
  });
  return response.choices[0].message.content ?? '';
}

// ---------------------------------------------------------------
// Demo
// ---------------------------------------------------------------
console.log('='.repeat(60));
console.log(' EJEMPLO 6 · Análisis de PDF');
console.log('='.repeat(60));

if (!existsSync(PDF_PATH)) {
  console.log(`\n⚠️  No hay PDF en ${PDF_PATH}`);
  console.log('   Crea la carpeta ./documentos/ y pon cualquier PDF con ese nombre.');
} else {
  // --- Opción B (más simple) ---
  console.log('\n[Opción B] Extracción local + inline');
  const respuestaB = await analizarExtrayendoTexto(
    PDF_PATH,
    'Resume este documento en 3 viñetas concisas. ¿De qué trata?'
  );
  console.log(`\n🤖 Respuesta:\n${respuestaB}`);

  // --- Opción A (descomentá para probar) ---
  // console.log('\n[Opción A] Files API (PDF nativo)');
  // const respuestaA = await analizarConFilesApi(
  //   PDF_PATH,
  //   'Extrae las tablas y explícalas. Si no hay tablas, dilo.'
  // );
  // console.log(`\n🤖 Respuesta:\n${respuestaA}`);
}

// ==========================================================================
// MORALEJA
// ==========================================================================
console.log('\n' + '='.repeat(60));
console.log('☝️  Dos caminos para un PDF:');
console.log('');
console.log('   Files API · nativo:');
console.log('     ✓ Ve imágenes, tablas, gráficos, layout');
console.log('     ✗ Más caro, requiere subida previa');
console.log('     → Recibos escaneados, papers con figuras, formularios');
console.log('');
console.log('   Extracción local (pdf-parse) + inline:');
console.log('     ✓ Más barato, más rápido');
console.log('     ✗ Solo texto, pierde todo lo visual');
console.log('     → Contratos, artículos, libros, notas');
console.log('');
console.log('   💡 Si el PDF es muy largo: dividir por capítulos/secciones,');
console.log('      indexar en vector DB, y hacer RAG.');
console.log('='.repeat(60));
