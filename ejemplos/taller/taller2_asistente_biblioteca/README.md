# Taller 2 · Asistente de Biblioteca con Tools

> Tiempo estimado: **60 – 75 min**
> Requisitos previos: haber visto los ejemplos **4 y 8**

## 🎯 Objetivo

Construir un **asistente conversacional** que puede buscar libros y gestionar reservas de la biblioteca IPVG. El asistente **no** hace la lógica de búsqueda o reserva directamente — le da un menú de `tools` al modelo, y el modelo decide cuáles llamar según lo que el usuario pregunte.

Este ejercicio integra:
- Tool calling (function calling)
- Definición de tools con JSON Schema
- Dispatcher de funciones en tu código
- Manejo de estado (reservas en memoria)
- Loop completo: pregunta → tool_calls → ejecución → respuesta

## 📚 El dominio

Tenés una base de datos mock (`biblioteca_db.py`) con:
- **10 libros** con ID, título, autor, cantidad de ejemplares disponibles
- Un diccionario de **reservas por estudiante** (empieza vacío)

El asistente debe poder:
- Buscar libros por texto parcial del título
- Reservar un libro (decrementa disponibles)
- Listar las reservas de un estudiante

## ✅ Criterios de éxito (requisitos mínimos)

- [ ] Implementar **3 funciones Python** que operan sobre `LIBROS` y `RESERVAS`:
  - [ ] `buscar_libro(titulo_parcial)` — match case-insensitive por título
  - [ ] `reservar_libro(libro_id, estudiante)` — manejar casos: no existe, sin stock, OK
  - [ ] `listar_mis_reservas(estudiante)` — devolver lista de libros reservados
- [ ] Definir las **3 tools** en formato JSON Schema (nombre, descripción, parámetros)
- [ ] Implementar **`ejecutar_tool(nombre, args)`** — el dispatcher que conecta el nombre de la tool con la función Python
- [ ] Implementar **`chat_agente()`** con el loop completo:
  - [ ] Llama al modelo con las tools
  - [ ] Mientras el modelo pida tool_calls, ejecutarlas y volver a llamar
  - [ ] Cuando el modelo responde sin tool_calls, devolver el contenido
- [ ] Probar las 3 acciones:
  - [ ] Buscar: "¿Tienen algún libro sobre Python?"
  - [ ] Reservar: "Reservame Clean Code"
  - [ ] Listar: "¿Qué libros tengo reservados?"

## 🎁 Bonus (si te sobra tiempo)

- [ ] **4ª tool:** `devolver_libro(libro_id, estudiante)` — incrementa disponibles, saca de `RESERVAS`
- [ ] **Structured outputs:** definir un modelo Pydantic `ConfirmacionReserva` y usar `response_format` para la respuesta final
- [ ] **Respuestas paralelas:** si el modelo pide varias tool_calls a la vez (por ejemplo buscar 2 libros), ejecutarlas todas antes de volver a llamar

## 📝 Pasos sugeridos

Abre `starter.py` y completa los `# TODO` en orden:

1. **TODO 1-3** — Implementar las 3 funciones Python (`buscar_libro`, `reservar_libro`, `listar_mis_reservas`)
2. **TODO 4** — Completar la definición de `tools` (3 schemas)
3. **TODO 5** — Implementar `chat_agente()` con el loop de tool calling

## 🧪 Cómo probar tu solución

Secuencia de prueba típica:

```
👤 ana.perez: Hola, ¿qué libros tienen sobre programación en Python?
🤖: (debería llamar a buscar_libro y responder con los matches)

👤 ana.perez: Reservame "Effective Python"
🤖: (debería llamar a reservar_libro y confirmar)

👤 ana.perez: ¿Y el Design Patterns?
🤖: (debería intentar reservar y fallar porque no hay stock → responder que no hay)

👤 ana.perez: ¿Qué libros tengo reservados?
🤖: (debería llamar a listar_mis_reservas y responder con el Effective Python)

👤 ana.perez: salir
```

## 🚀 Correr

```bash
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY

python starter.py
```

## 🆘 Si te atascas

1. Releé el **ejemplo 4** (`ejemplo4_tool_calling.py`) — ahí está el patrón del loop
2. Releé el **ejemplo 8** (`ejemplo8_structured.py`) — para el bonus de Pydantic
3. Si el modelo no llama a tu tool: revisá que la `description` sea clara
4. Si falla al ejecutar: `print()` los args que te pasa el modelo, quizás se equivoca

## 💡 Concepto clave

El modelo NO ejecuta nada. Solo responde con:
```json
{"name": "buscar_libro", "arguments": "{\"titulo_parcial\": \"Python\"}"}
```
**Tu código** es el que ejecuta la función Python real. El modelo después **recibe el resultado** como un mensaje nuevo (role="tool") y genera la respuesta final en lenguaje natural.

Dibujo del flujo:

```
     [Usuario: "¿Tienen Clean Code?"]
              ↓
     [Modelo decide: quiero llamar buscar_libro(Clean Code)]
              ↓
     [Tu código ejecuta buscar_libro y obtiene resultados]
              ↓
     [Le das el resultado al modelo como role="tool"]
              ↓
     [Modelo redacta: "Sí, tenemos 'Clean Code' con 2 ejemplares disponibles"]
              ↓
     [Mostrás al usuario]
```
