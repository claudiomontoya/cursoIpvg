/**
 * Ejemplo 4 · Tool calling (function calling)
 * ============================================
 * Qué enseña:
 *   - Cómo darle al modelo un "menú" de funciones que puede pedir ejecutar
 *   - El flujo completo: modelo → tool_call → tu código ejecuta → resultado → modelo
 *   - El modelo NO ejecuta la función; te pide que TÚ la ejecutes
 *
 * Moraleja:
 *   El modelo decide QUÉ llamar y con qué argumentos.
 *   Tu código ejecuta, le devuelve el resultado, y el modelo redacta la respuesta final.
 */

import 'dotenv/config';
import OpenAI from 'openai';
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions';

const client = new OpenAI();

// ---------------------------------------------------------------
// 1. Definimos la herramienta con JSON Schema
//    Esto es lo que VE el modelo: nombre, descripción, argumentos.
// ---------------------------------------------------------------
const tools = [
  {
    type: 'function' as const,
    function: {
      name: 'get_clima',
      description: 'Obtiene el clima actual de una ciudad chilena.',
      parameters: {
        type: 'object',
        properties: {
          ciudad: {
            type: 'string',
            description: 'Nombre de la ciudad (Concepción, Santiago, Chillán, etc.)',
          },
        },
        required: ['ciudad'],
      },
    },
  },
];

// ---------------------------------------------------------------
// 2. Nuestra función real (mock)
//    En producción llamaría a una API de clima. Acá devolvemos datos fake.
// ---------------------------------------------------------------
type DatosClima = { temp_c: number | null; condicion: string; humedad: number | null };

function getClima(ciudad: string): DatosClima {
  const mockData: Record<string, DatosClima> = {
    'Concepción':  { temp_c: 14, condicion: 'nublado',   humedad: 82 },
    'Santiago':    { temp_c: 22, condicion: 'despejado', humedad: 45 },
    'Chillán':     { temp_c: 16, condicion: 'llovizna',  humedad: 91 },
    'Los Ángeles': { temp_c: 18, condicion: 'parcial',   humedad: 68 },
  };
  return mockData[ciudad] ?? { temp_c: null, condicion: 'desconocido', humedad: null };
}

console.log('='.repeat(60));
console.log(' EJEMPLO 4 · Tool calling');
console.log('='.repeat(60));

// ---------------------------------------------------------------
// 3. Empezamos la conversación
// ---------------------------------------------------------------
const mensajes: ChatCompletionMessageParam[] = [
  { role: 'user', content: '¿Qué tiempo hace en Concepción? Responde en 1 frase.' },
];

// ---------------------------------------------------------------
// 4. PRIMERA llamada — el modelo ve las tools disponibles y decide si usarlas
// ---------------------------------------------------------------
console.log('\n📞 Llamada 1: usuario pregunta, modelo decide...');
const r1 = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: mensajes,
  tools,
});

const msg = r1.choices[0].message;
mensajes.push(msg); // Guardamos la respuesta del modelo en el historial

// ---------------------------------------------------------------
// 5. ¿El modelo pidió ejecutar una tool?
// ---------------------------------------------------------------
if (msg.tool_calls && msg.tool_calls.length > 0) {
  for (const toolCall of msg.tool_calls) {
    const nombreFn = toolCall.function.name;
    const args = JSON.parse(toolCall.function.arguments) as { ciudad: string };

    console.log(`🔧 El modelo pidió llamar: ${nombreFn}(${JSON.stringify(args)})`);

    // 6. Ejecutamos la función REAL con los argumentos que el modelo eligió
    let resultado: unknown;
    if (nombreFn === 'get_clima') {
      resultado = getClima(args.ciudad);
    } else {
      resultado = { error: `Función desconocida: ${nombreFn}` };
    }

    console.log(`   ↳ Resultado: ${JSON.stringify(resultado)}`);

    // 7. Devolvemos el resultado al modelo como un mensaje "tool"
    mensajes.push({
      role: 'tool',
      tool_call_id: toolCall.id,
      content: JSON.stringify(resultado),
    });
  }

  // ---------------------------------------------------------------
  // 8. SEGUNDA llamada — ahora el modelo tiene el resultado y redacta la respuesta
  // ---------------------------------------------------------------
  console.log('\n📞 Llamada 2: modelo redacta respuesta final con los datos...');
  const r2 = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: mensajes,
    tools,
  });
  console.log(`\n🤖 Respuesta final:  ${r2.choices[0].message.content}`);
} else {
  // El modelo no quiso usar ninguna tool — respondió directamente
  console.log(`\n🤖 Respuesta directa (sin tool): ${msg.content}`);
}

// ==========================================================================
// MORALEJA
// ==========================================================================
console.log('\n' + '='.repeat(60));
console.log('☝️  El modelo llama tu función indirectamente:');
console.log('   1. Le damos un menú de tools (JSON Schema).');
console.log("   2. El modelo devuelve un 'tool_call' con args.");
console.log('   3. Tu código ejecuta la función REAL.');
console.log('   4. Le mandas el resultado → el modelo redacta la respuesta.');
console.log('');
console.log('   Hacen falta 2 llamadas al modelo por cada tool usada.');
console.log('   El modelo puede pedir VARIAS tools en un turno (paralelo).');
console.log('='.repeat(60));
