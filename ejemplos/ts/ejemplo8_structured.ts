/**
 * Ejemplo 8 · Structured Outputs (JSON con schema)
 * =================================================
 * Qué enseña:
 *   - Forzar al modelo a responder con JSON que sigue un schema exacto
 *   - Eliminar el parsing frágil de "texto libre → JSON"
 *   - Usar Zod para definir el schema + validación automática
 *
 * Moraleja:
 *   Si necesitas datos estructurados → NUNCA le pidas "responde en JSON"
 *   en texto libre. Usá response_format con un schema zod.
 *   El modelo ya no puede salirse del formato.
 */

import 'dotenv/config';
import OpenAI from 'openai';
import { zodResponseFormat } from 'openai/helpers/zod';
import { z } from 'zod';

const client = new OpenAI();

// ---------------------------------------------------------------
// 1. Definir el schema con Zod
//    Estas clases DESCRIBEN la forma exacta del output que queremos.
// ---------------------------------------------------------------
const Habilidad = z.object({
  nombre: z.string(),
  nivel: z
    .enum(['principiante', 'intermedio', 'avanzado'])
    .describe('nivel de dominio'),
});

const Estudiante = z.object({
  nombre: z.string(),
  edad: z.number().int(),
  carrera: z.string(),
  ciudad: z.string(),
  habilidades: z.array(Habilidad),
  busca_trabajo: z.boolean(),
});

type EstudianteT = z.infer<typeof Estudiante>;

// ---------------------------------------------------------------
// 2. Texto libre del que queremos extraer datos
// ---------------------------------------------------------------
const textoFuente = `
Claudio Montoya, 34 años, de Concepción. Estudia Analista Programador en IPVG.
Sabe Python avanzado, JavaScript intermedio y acaba de empezar con Rust (principiante).
También conoce SQL a nivel intermedio. Está buscando prácticas en empresas de software.
`;

console.log('='.repeat(60));
console.log(' EJEMPLO 8 · Structured Outputs');
console.log('='.repeat(60));
console.log('\n📝 Texto fuente:');
console.log(textoFuente.trim());

// ---------------------------------------------------------------
// 3. Llamar con response_format + zodResponseFormat
//    El helper genera el JSON Schema automáticamente desde el zod.
// ---------------------------------------------------------------
const response = await client.beta.chat.completions.parse({
  model: 'gpt-4o-mini',
  messages: [
    {
      role: 'system',
      content: 'Extraes datos estructurados de texto sobre estudiantes.',
    },
    { role: 'user', content: textoFuente },
  ],
  response_format: zodResponseFormat(Estudiante, 'estudiante'),
});

// ---------------------------------------------------------------
// 4. El resultado YA es un objeto validado contra el schema
//    TypeScript sabe el tipo: EstudianteT
// ---------------------------------------------------------------
const estudiante: EstudianteT = response.choices[0].message.parsed!;

console.log('\n📋 Datos extraídos:');
console.log(`   Nombre:        ${estudiante.nombre}`);
console.log(`   Edad:          ${estudiante.edad} años`);
console.log(`   Carrera:       ${estudiante.carrera}`);
console.log(`   Ciudad:        ${estudiante.ciudad}`);
console.log(`   Busca trabajo: ${estudiante.busca_trabajo ? 'sí' : 'no'}`);
console.log(`   Habilidades:`);
for (const h of estudiante.habilidades) {
  console.log(`     - ${h.nombre} (${h.nivel})`);
}

// ---------------------------------------------------------------
// 5. Ahora podés usar el objeto como cualquier objeto tipado
// ---------------------------------------------------------------
console.log(`\n🔧 Operando sobre los datos:`);
const sabePython = estudiante.habilidades.some(
  h => h.nombre.toLowerCase() === 'python'
);
const avanzadas = estudiante.habilidades
  .filter(h => h.nivel === 'avanzado')
  .map(h => h.nombre);
console.log(`   ¿Sabe Python?  ${sabePython ? 'sí' : 'no'}`);
console.log(`   Habilidades avanzadas: ${JSON.stringify(avanzadas)}`);

console.log(`\n📦 Como JSON:`);
console.log(JSON.stringify(estudiante, null, 2));

// ==========================================================================
// MORALEJA
// ==========================================================================
console.log('\n' + '='.repeat(60));
console.log('☝️  El modelo NO puede salirse del schema.');
console.log("   Si el schema dice 'edad: number', no devuelve 'treinta y cuatro'.");
console.log("   Si dice 'habilidades: array', NUNCA devuelve un string.");
console.log('');
console.log('   Adiós a:');
console.log('   ✗ JSON.parse en try/catch');
console.log('   ✗ regex para extraer JSON de texto libre');
console.log("   ✗ prompts rogando '¡RESPONDE EN JSON VÁLIDO!'");
console.log('');
console.log('   Hola a:');
console.log('   ✓ Zod → JSON Schema automático + tipos TS');
console.log('   ✓ response.choices[0].message.parsed → objeto tipado');
console.log('   ✓ Código robusto sin parsing manual');
console.log('='.repeat(60));
