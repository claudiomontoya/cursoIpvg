/**
 * Ejemplo 3 · Memoria con historial manual
 * =========================================
 * Qué enseña:
 *   - Mantener una lista de mensajes como "historial"
 *   - Appendear user y assistant en cada turno
 *   - El modelo ahora recuerda turnos previos
 *   - BONUS: observar cómo crece el costo con cada turno
 *
 * Moraleja:
 *   La "memoria" es un array de objetos. Simple, explícita, bajo tu control.
 *   La responsabilidad de truncar/resumir historiales largos es TUYA.
 */

import 'dotenv/config';
import OpenAI from 'openai';
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions';

const client = new OpenAI();

// 1. Historial: empezamos con un system prompt (personalidad del asistente)
const historial: ChatCompletionMessageParam[] = [
  {
    role: 'system',
    content: 'Eres un tutor amable y conciso de IPVG. Responde en 1-2 frases.',
  },
];

/**
 * Flujo por turno:
 *   1. Appendeamos el mensaje del usuario al historial
 *   2. Llamamos al modelo con TODO el historial
 *   3. Appendeamos la respuesta del asistente al historial
 *   4. Mostramos el turno y el uso de tokens acumulado
 */
async function preguntar(textoUsuario: string): Promise<void> {
  // 1. Append usuario
  historial.push({ role: 'user', content: textoUsuario });

  // 2. Llamada con todo el historial
  const resp = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: historial,
  });

  // 3. Extraer respuesta y appendear al historial
  const respuesta = resp.choices[0].message.content ?? '';
  historial.push({ role: 'assistant', content: respuesta });

  // 4. Mostrar turno + uso
  const turno = historial.filter(m => m.role === 'user').length;
  console.log(`\n[Turno ${turno}]  tokens usados: ${resp.usage?.total_tokens}`);
  console.log(`👤 Tú:     ${textoUsuario}`);
  console.log(`🤖 Tutor:  ${respuesta}`);
}

console.log('='.repeat(60));
console.log(' EJEMPLO 3 · Con memoria — conversación multi-turno');
console.log('='.repeat(60));

// ---------------------------------------------------------------
// Una conversación real de 4 turnos
// ---------------------------------------------------------------
await preguntar('Hola, me llamo Claudio y estudio Analista Programador en IPVG.');
await preguntar('¿Qué carreras hay relacionadas con datos?');
await preguntar('¿Cuál me recomiendas para alguien que ya sabe programar?');
await preguntar('¿Cómo me llamo y qué estoy estudiando?'); // ← prueba de memoria

// ==========================================================================
// MORALEJA
// ==========================================================================
console.log('\n' + '='.repeat(60));
console.log('☝️  En el último turno el modelo recordó nombre y carrera.');
console.log("   La memoria vive en el array 'historial' (Node, en tu proceso).");
console.log(`   Historial actual: ${historial.length} mensajes.`);
console.log('');
console.log('   ⚠️  Cada turno reenvía el historial ENTERO → los tokens crecen.');
console.log('   Con el tiempo conviene:');
console.log('     - Truncar los turnos más antiguos');
console.log('     - Resumir el historial cuando supere N tokens');
console.log("     - Guardar memoria 'permanente' en una base de datos");
console.log('='.repeat(60));
