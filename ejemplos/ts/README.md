# Ejemplos TypeScript — OpenAI API · IPVG 2026

Los mismos 8 ejemplos que la versión Python, pero en TypeScript con el SDK oficial de OpenAI para Node.

## Setup (una sola vez)

1. Instalar dependencias:

```bash
npm install
```

2. Copiar la plantilla de `.env` y poner tu API key:

```bash
cp .env.example .env
# Editar .env y poner OPENAI_API_KEY=sk-proj-...
```

## Correr

```bash
npm run ejemplo1
npm run ejemplo2
# ...
npm run ejemplo8
```

## Orden recomendado

| # | Script | Concepto |
|---|--------|----------|
| 1 | `ejemplo1_hola.ts` | Primera llamada, `usage` |
| 2 | `ejemplo2_sin_memoria.ts` | API stateless |
| 3 | `ejemplo3_con_memoria.ts` | Historial manual |
| 4 | `ejemplo4_tool_calling.ts` | Function calling |
| 5 | `ejemplo5_imagen.ts` | Multimodal (imagen local base64) |
| 6 | `ejemplo6_pdf.ts` | PDF con pdf-parse |
| 7 | `ejemplo7_streaming.ts` | Async iterator sobre stream |
| 8 | `ejemplo8_structured.ts` | Zod + `zodResponseFormat` |

## Diferencias clave con Python

- **Ejecución:** `tsx` ejecuta TypeScript directo sin compilación previa
- **ESM:** los scripts usan `import` (no `require`) porque `package.json` tiene `"type": "module"`
- **Top-level await:** funciona directamente (Node 18+)
- **Structured outputs:** usamos `zod` + `zodResponseFormat` en lugar de Pydantic
- **PDF:** usamos `pdf-parse` en lugar de `pypdf`

## Stack

- **Node.js** 18+ (para top-level await y fetch nativo)
- **tsx** — ejecuta TS directo
- **openai** — SDK oficial (v4.x)
- **dotenv** — lee `.env`
- **zod** — schema validation (para structured outputs)
- **pdf-parse** — extracción de texto de PDFs

## Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `Cannot find module 'openai'` | No hiciste `npm install` | `npm install` |
| `API key not found` | Falta `.env` | Copiar `.env.example` y editar |
| `ERR_MODULE_NOT_FOUND` al importar `.ts` | Sin `tsx` | Usar `npm run ejemploN` (no `node`) |
| Error con `pdf-parse` | Falta PDF en `./documentos/` | Crear el archivo |

## Estructura

```
ejemplos/ts/
├── package.json
├── tsconfig.json
├── .env.example
├── .env                    (creás tú, no commitear)
├── README.md
├── ejemplo1_hola.ts
├── ejemplo2_sin_memoria.ts
├── ejemplo3_con_memoria.ts
├── ejemplo4_tool_calling.ts
├── ejemplo5_imagen.ts
├── ejemplo6_pdf.ts
├── ejemplo7_streaming.ts
├── ejemplo8_structured.ts
├── imagenes/
│   └── demo.jpg
└── documentos/
    └── documento.pdf
```
