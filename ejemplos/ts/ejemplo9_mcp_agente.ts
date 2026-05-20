/**
 * Ejemplo 9 · Agente con OpenAI Agents SDK + MCP (streamable-http)
 * ================================================================
 * Equivalente TypeScript del archivo Python `mcp/06_agente_sdk_openai_http.py`.
 *
 * Qué enseña:
 *   - Cómo usar el Agents SDK oficial de OpenAI en Node/TS
 *   - Cómo conectarse a un servidor MCP por streamable-http (single endpoint)
 *   - Que el SDK descubre las tools del server automáticamente — no hay que
 *     traducir schemas ni manejar el loop de tool calling a mano
 *
 * Antes de correr, levantá el server MCP (es el mismo de los ejemplos Python):
 *
 *     # otra terminal
 *     cd ../python
 *     source venv/bin/activate
 *     python mcp/webapp_mcp/mcp_server.py   # corre en http://localhost:9000/mcp
 *
 * Correr este archivo:
 *
 *     npm run ejemplo9
 *     npm run ejemplo9 -- "¿qué pasa si suspendo mis estudios?"
 */

import 'dotenv/config';
import { Agent, run } from '@openai/agents';
import { MCPServerStreamableHttp } from '@openai/agents';

const MCP_URL = process.env.MCP_URL ?? 'http://127.0.0.1:9000/mcp';

const INSTRUCCIONES = [
  'Sos un asistente del IPVG.',
  'Tenés tools MCP para responder sobre el Reglamento Académico 2026',
  'y para consultar la hora. Usá `buscar_reglamento` siempre que la pregunta',
  'sea sobre normativa académica y citá artículo + página.',
  'Si la pregunta no necesita ninguna tool, respondé directamente.',
].join(' ');

async function main(): Promise<void> {
  // 1. Pregunta(s): argumento CLI, o batch demo
  const arg = process.argv[2];
  const preguntas = arg
    ? [arg]
    : [
        '¿Qué hora es?',
        '¿Cuáles son las causales de baja académica?',
        '¿Cómo funciona la suspensión de estudios?',
      ];

  // 2. Abrir conexión al MCP server por streamable-http
  const mcpServer = new MCPServerStreamableHttp({
    url: MCP_URL,
    name: 'ipvg-tools',
  });
  await mcpServer.connect();

  try {
    // 3. Construir el agente UNA vez. El SDK leerá `list_tools` del server
    //    y traducirá los schemas MCP al formato que espera el modelo.
    const agent = new Agent({
      name: 'AsistenteIPVG',
      model: 'gpt-4.1',
      instructions: INSTRUCCIONES,
      mcpServers: [mcpServer],
    });

    console.log(`🤖 Agente conectado a MCP server en ${MCP_URL}\n`);

    // 4. Loop sobre las preguntas
    for (let i = 0; i < preguntas.length; i++) {
      const pregunta = preguntas[i];
      console.log(`────────  Pregunta ${i + 1}/${preguntas.length}  ────────`);
      console.log(`👤 ${pregunta}\n`);

      const resultado = await run(agent, pregunta);
      console.log(`🤖 ${resultado.finalOutput}\n`);
    }
  } finally {
    // 5. Cerrar la sesión MCP siempre, aunque haya error
    await mcpServer.close();
  }
}

main().catch((err) => {
  console.error('\n❌ Error:', err.message ?? err);
  console.error('   ¿Está corriendo el server?');
  console.error('   → cd ../python && python mcp/webapp_mcp/mcp_server.py');
  process.exit(1);
});

// ==========================================================================
// MORALEJA
// ==========================================================================
// Mismo resultado que el archivo Python: 50 líneas, sin loop manual,
// sin traducción de schemas, sin gestionar tool calls.
// Lo único que cambia entre Python y TS es la sintaxis: `import`, `await`,
// `class new ...` en vez de `with ... as ...`.
// El concepto y el server MCP son IDÉNTICOS — esa es la gracia del protocolo.
// ==========================================================================
