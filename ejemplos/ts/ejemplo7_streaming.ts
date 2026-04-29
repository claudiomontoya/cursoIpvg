/**
 * Ejemplo 7 · Streaming (respuesta token a token)
 * ================================================
 * Qué enseña:
 *   - Cómo recibir la respuesta mientras se genera (SSE bajo el capó)
 *   - El modelo no es más rápido, pero la LATENCIA PERCIBIDA baja 5-10×
 *   - Cómo iterar sobre el stream con un async iterator
 *
 * Moraleja:
 *   Para cualquier UI (chat, app, página web) → usa streaming.
 *   El usuario empieza a leer desde el primer token, no espera 8 segundos.
 */

import 'dotenv/config';
import OpenAI from 'openai';

const client = new OpenAI();

console.log('='.repeat(60));
console.log(' EJEMPLO 7 · Streaming');
console.log('='.repeat(60));
console.log('\n🤖 Respuesta (mirá cómo aparece letra por letra):\n');

// ---------------------------------------------------------------
// stream: true → devuelve un async iterator en vez de la respuesta completa
// ---------------------------------------------------------------
const stream = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [
    {
      role: 'user',
      content:
        'Cuéntame una historia corta (4 frases) sobre un estudiante ' +
        'de IPVG que crea su primer agente de IA.',
    },
  ],
  stream: true,
});

// ---------------------------------------------------------------
// Iteramos sobre los chunks a medida que llegan
// Cada chunk tiene un 'delta' con el texto parcial
// ---------------------------------------------------------------
let tokensRecibidos = 0;
for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta?.content;
  if (delta) {
    process.stdout.write(delta); // Imprime inmediatamente sin buffer
    tokensRecibidos++;
  }
}

console.log(`\n\n📊 ${tokensRecibidos} chunks recibidos.`);

// ==========================================================================
// MORALEJA
// ==========================================================================
console.log('\n' + '='.repeat(60));
console.log('☝️  Los tokens llegan cada ~20-50ms.');
console.log('   Tiempo total: igual. Tiempo HASTA EL PRIMER TOKEN: mucho menor.');
console.log('');
console.log('   Claves de implementación:');
console.log('   - stream: true en la llamada');
console.log('   - Iterar con "for await (const chunk of stream)"');
console.log('   - El texto viene en chunk.choices[0].delta.content');
console.log('   - En web: convertir a Server-Sent Events (SSE) para el browser');
console.log('');
console.log("   ⚠️  Con streaming pierdes el 'usage' total inmediato.");
console.log("      Para obtenerlo, agregar stream_options: { include_usage: true }");
console.log('='.repeat(60));
