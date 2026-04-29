/**
 * Ejemplo 1 · Hola mundo con OpenAI
 * ==================================
 * Qué enseña:
 *   - Cómo hacer la primera llamada a OpenAI con el SDK oficial de Node
 *   - Estructura mínima de un mensaje (role + content)
 *   - Cómo leer la respuesta y el uso (tokens = lo que pagas)
 *
 * Requisitos:
 *   npm install
 *   .env con OPENAI_API_KEY
 *
 * Correr:
 *   npm run ejemplo1
 */

import 'dotenv/config';
import OpenAI from 'openai';

// 1. Crear el cliente. Lee OPENAI_API_KEY del entorno automáticamente.
const client = new OpenAI();

// 2. Hacer la llamada: un único mensaje de usuario
const response = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [
    { role: 'user', content: 'Hola, ¿cuál es la capital de Chile? Responde en 1 frase.' },
  ],
});

// 3. Extraer el texto de la respuesta
const texto = response.choices[0].message.content;
console.log('🤖 Respuesta:');
console.log(`   ${texto}\n`);

// 4. Ver el uso de tokens — ESTO es lo que te cobran
const usage = response.usage!;
console.log('📊 Uso (lo que te cobran):');
console.log(`   Tokens input:  ${usage.prompt_tokens}`);
console.log(`   Tokens output: ${usage.completion_tokens}`);
console.log(`   Total:         ${usage.total_tokens}`);

// 5. Costo aproximado (gpt-4o-mini: $0.15 input / $0.60 output por 1M tokens)
const costoInput = (usage.prompt_tokens * 0.15) / 1_000_000;
const costoOutput = (usage.completion_tokens * 0.6) / 1_000_000;
console.log(`   Costo:         $${(costoInput + costoOutput).toFixed(6)} USD`);

// ==========================================================================
// MORALEJA
// ==========================================================================
// Una llamada al modelo es literalmente un POST con JSON.
// Recibes: texto + metadata (usage).
// El "usage" dice cuántos tokens procesaste → cuánto te van a cobrar.
// ==========================================================================
