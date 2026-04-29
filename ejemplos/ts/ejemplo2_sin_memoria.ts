/**
 * Ejemplo 2 · Sin memoria (la API es stateless)
 * ==============================================
 * Qué enseña:
 *   - Por defecto, CADA llamada a OpenAI es independiente
 *   - El modelo NO recuerda conversaciones previas
 *   - Demostración concreta: le decimos el nombre, luego preguntamos
 *
 * Aha moment:
 *   Si no guardas el historial y lo reenvías, el modelo parte de cero cada vez.
 */

import 'dotenv/config';
import OpenAI from 'openai';

const client = new OpenAI();

console.log('='.repeat(60));
console.log(' EJEMPLO 2 · Sin memoria — 2 llamadas independientes');
console.log('='.repeat(60));

// ---------------------------------------------------------------
// Llamada 1: le decimos nuestro nombre
// ---------------------------------------------------------------
const r1 = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [
    { role: 'user', content: 'Hola, me llamo Claudio y soy de Concepción.' },
  ],
});
console.log('\n[Llamada 1]');
console.log('👤 Usuario:  Hola, me llamo Claudio y soy de Concepción.');
console.log(`🤖 Modelo:   ${r1.choices[0].message.content}`);

// ---------------------------------------------------------------
// Llamada 2: le preguntamos el nombre (SIN contexto previo)
// Nota: es una llamada NUEVA, no le pasamos el historial.
// ---------------------------------------------------------------
const r2 = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [
    { role: 'user', content: '¿Cómo me llamo y de dónde soy?' },
  ],
});
console.log('\n[Llamada 2 — nueva, sin historial]');
console.log('👤 Usuario:  ¿Cómo me llamo y de dónde soy?');
console.log(`🤖 Modelo:   ${r2.choices[0].message.content}`);

// ==========================================================================
// MORALEJA
// ==========================================================================
console.log('\n' + '='.repeat(60));
console.log('☝️  El modelo NO recuerda el nombre ni la ciudad.');
console.log('   Cada llamada parte desde cero (stateless).');
console.log('   Solución: enviar el historial en cada llamada → ejemplo 3.');
console.log('='.repeat(60));
