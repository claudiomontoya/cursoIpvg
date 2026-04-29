# Taller 1 · Tutor Virtual de Analista Programador

> Tiempo estimado: **45 – 60 min**
> Requisitos previos: haber visto los ejemplos **1, 2, 3 y 6**

## 🎯 Objetivo

Construir un **chatbot tutor** para estudiantes de Analista Programador del IPVG. El estudiante puede preguntarle dudas sobre la carrera y recibe respuestas del modelo.

Este ejercicio integra **todo lo que viste en los ejemplos 1-3 y 6**:
- Mensajes con roles (`system`, `user`, `assistant`)
- Memoria manual con una lista de historial
- System prompt bien construido (rol, alcance, tono)
- Bucle de conversación

## ✅ Criterios de éxito (requisitos mínimos)

Tu programa debe cumplir TODOS estos puntos:

- [ ] Tiene un **system prompt** que establece:
  - [ ] El rol del asistente (tutor de Analista Programador)
  - [ ] El alcance (solo temas de la carrera)
  - [ ] El tono (amable, conciso)
- [ ] Usa un **historial** que crece con cada turno (user + assistant)
- [ ] Corre un **bucle** que pide input del usuario hasta que escribe `salir`
- [ ] Si el usuario **dice su nombre** ("me llamo X"), el tutor lo recuerda y lo usa en los siguientes turnos
- [ ] Si el usuario pregunta **temas fuera de la carrera** (fútbol, política, cocina), el tutor redirige amablemente
- [ ] Al salir, muestra un mensaje de despedida

## 🎁 Bonus (si te sobra tiempo)

- [ ] Mostrar al final el **total de tokens** consumidos en la sesión
- [ ] Implementar una **ventana deslizante**: mantener solo los últimos 10 turnos del historial (preservando siempre el system prompt)
- [ ] Agregar un comando `/resumen` que le pida al modelo que resuma la conversación hasta ahora

## 📝 Pasos sugeridos

Abre `starter.py` y completa los `# TODO` en orden:

1. **TODO 1** — Escribir el `SYSTEM_PROMPT`
2. **TODO 2** — Inicializar `historial` con ese system prompt
3. **TODO 3** — Implementar la función `chat(mensaje_usuario)`
4. **TODO 4** — Escribir el bucle principal en `main()`
5. **TODO 5** — Manejar la salida (`salir`)
6. **TODO 6** — Conectar input → `chat()` → print

## 🧪 Cómo probar tu solución

Ejecuta `python starter.py` y prueba esta secuencia:

```
👤 Tú: Hola, me llamo Daniel
🤖: (debería saludarte por nombre)

👤 Tú: ¿Qué se aprende en la carrera?
🤖: (debería mencionar programación / análisis / BD...)

👤 Tú: ¿Quién ganó el mundial 2022?
🤖: (debería redirigir amablemente al ámbito de la carrera)

👤 Tú: ¿Cómo me llamo?
🤖: (debería responder "Daniel")

👤 Tú: salir
🤖: despedida + (bonus) contador de tokens
```

## 🚀 Correr

```bash
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY

python starter.py
```

## 🆘 Si te atascas

1. Releé el **ejemplo 3** (`ejemplo3_con_memoria.py`) — ahí está el patrón de historial
2. Releé el **ejemplo 6** (`ejemplo6_pdf.py`) — para system prompts con alcance
3. Si nada funciona, abrí `solucion.py` para ver una implementación posible
