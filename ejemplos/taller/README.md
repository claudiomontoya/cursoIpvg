# Taller · Clase 1 · IA Generativa · IPVG 2026

Dos ejercicios prácticos para consolidar lo visto en la primera clase.

## 📦 Contenido

| # | Taller | Duración | Conceptos |
|---|--------|----------|-----------|
| 1 | [Tutor Virtual](./taller1_tutor_virtual/) | 45–60 min | Mensajes · memoria · system prompt · bucle de chat |
| 2 | [Asistente de Biblioteca](./taller2_asistente_biblioteca/) | 60–75 min | Tool calling · JSON Schema · dispatch de funciones · estado |

## ⚙️ Setup común

Los dos talleres usan las mismas dependencias que los ejemplos 1-8 del curso.

**Opción A — reutilizar el venv de los ejemplos:**

```bash
# Desde la raíz de ejemplos/python/ activas su venv:
cd ../python
source venv/bin/activate
cd ../taller
```

**Opción B — crear un venv propio:**

```bash
cd taller
python3 -m venv venv
source venv/bin/activate
pip install openai python-dotenv pydantic
```

**API key:** cada taller tiene su propio `.env.example`. Copiá la `OPENAI_API_KEY` del archivo `.env` raíz del proyecto.

## 🎯 Cómo trabajar

Cada taller tiene:

- **`README.md`** — enunciado, requisitos, criterios de éxito
- **`starter.py`** — esqueleto con `# TODO` que tenés que completar
- **`solucion.py`** — referencia del docente (no la abras antes de intentar)

Flujo recomendado:

```
1. Leer el README del taller completo (5 min)
2. Abrir starter.py y leer los TODOs en orden
3. Implementar paso a paso, ejecutando después de cada TODO
4. Validar contra los "Criterios de éxito" del README
5. Si te queda tiempo, intenta los retos BONUS
```

## 🧪 Ejecución

```bash
cd taller1_tutor_virtual
python starter.py          # ← tu versión
# o
python solucion.py         # ← referencia docente
```

## 📊 Criterios de evaluación

- **✓ Requisitos mínimos** (70%): la checklist principal del README
- **✓ Código limpio** (20%): variables bien nombradas, funciones reutilizables
- **✓ Bonus** (10%): al menos un reto extra

No se evalúa performance de tokens ni arquitectura — el foco es entender los conceptos.

## 💡 Tips

- Si te atascás, **volvé a los ejemplos 1-8** del curso antes de pedir ayuda
- Usá `print()` para inspeccionar `response.choices[0].message` durante debugging
- **Ningún** taller requiere internet aparte de la API de OpenAI
- Costo estimado por taller: menos de $0.01 USD

---

**Próximas clases:** agregaremos talleres de RAG (clase 2), agentes multi-paso (clase 3), structured outputs aplicado (clase 4) y evaluación / monitoring (clase 5).
