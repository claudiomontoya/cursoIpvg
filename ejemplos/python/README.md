# Ejemplos Python — OpenAI API · IPVG 2026

Ejemplos prácticos para la sesión de IA Generativa. Cada script es autocontenido y enseña **un solo concepto**.

## Setup (una sola vez)

1. Crear un entorno virtual (recomendado):

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Copiar la plantilla de `.env` y poner tu API key:

```bash
cp .env.example .env
# Editar .env y poner OPENAI_API_KEY=sk-proj-...
```

Obtené tu API key en https://platform.openai.com/api-keys

## Orden recomendado

Correr en orden — cada ejemplo construye sobre el anterior.

| # | Archivo | Concepto que enseña |
|---|---------|---------------------|
| 1 | `ejemplo1_hola.py` | Primera llamada, ver respuesta y `usage` |
| 2 | `ejemplo2_sin_memoria.py` | La API es stateless (aha moment) |
| 3 | `ejemplo3_con_memoria.py` | Historial manual, conversación multi-turno |
| 4 | `ejemplo4_tool_calling.py` | El modelo invoca tu función |
| 5 | `ejemplo5_imagen.py` | Multimodal: imagen + texto → texto |
| 6 | `ejemplo6_pdf.py` | Análisis de PDF (2 métodos) |
| 7 | `ejemplo7_streaming.py` | Respuesta token a token |
| 8 | `ejemplo8_structured.py` | Output JSON con schema garantizado |

## Correr

```bash
python ejemplo1_hola.py
python ejemplo2_sin_memoria.py
# ...
```

## Modelo por defecto

Todos los ejemplos usan **`gpt-4o-mini`** — barato, rápido, multimodal. Ideal para aprender.

Para probar modelos más potentes, cambia el `model=` en cada script:
- `gpt-4o-mini` — $0.15 / $0.60 por 1M tokens
- `gpt-4o` — $2.50 / $10.00 por 1M tokens
- `gpt-4.1` — más nuevo y potente
- `o3-mini` — reasoning model (para matemática, código)

## Costo aproximado

Correr los 8 ejemplos gasta aprox **$0.005 USD** (medio centavo). Seguro para clase.

## Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `AuthenticationError` | API key mala o vacía | Revisar `.env` |
| `RateLimitError` | Pasaste tu quota | Esperar o agregar créditos |
| `ModuleNotFoundError: openai` | No instalaste deps | `pip install -r requirements.txt` |
| `FileNotFoundError` en ejemplo 6 | Falta el PDF | Crear `./documentos/documento.pdf` |

## Estructura del proyecto

```
ejemplos/python/
├── README.md              (este archivo)
├── requirements.txt
├── .env.example
├── .env                   (creás tú, no commitear)
├── ejemplo1_hola.py
├── ejemplo2_sin_memoria.py
├── ejemplo3_con_memoria.py
├── ejemplo4_tool_calling.py
├── ejemplo5_imagen.py
├── ejemplo6_pdf.py
├── ejemplo7_streaming.py
├── ejemplo8_structured.py
└── documentos/            (para ejemplo 6)
    └── documento.pdf
```
