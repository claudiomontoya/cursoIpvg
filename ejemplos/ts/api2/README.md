# Tienda IPVG · versión JSON (sin base de datos)

Mismo dominio, mismos endpoints, **mismo HTML** que [`../api/`](../api/) —
pero la persistencia vive en un archivo **`data.json`** local. Cero
infraestructura: solo Node.

## Por qué existe esta versión

- Para correr en una máquina sin Docker ni Mongo (laptop de un alumno, CI mínimo, ejemplo en clase rápido).
- Para mostrar que **la "base de datos" es solo una decisión de implementación**: si cambiás `db.ts`, el resto (`api.ts`, frontend, contratos) no se entera.
- Para ver el JSON crudo y entender qué se está guardando. Cuando hagas una compra, abrí `data.json` y mirá cómo creció la lista de órdenes.

## Pre-requisitos

```bash
cd ejemplos/ts
npm install --legacy-peer-deps    # ya está si hiciste el api/ Mongo
```

## Uso

### 1) Sembrar (crea `data.json` con 20 productos)

```bash
npm run api2:seed
```

Salida: `✅ 20 productos escritos en .../api2/data.json`

### 2) Servir

```bash
npm run api2:serve
# → http://localhost:8042
```

### 3) Inspeccionar la "base"

```bash
cat api2/data.json | jq
```

Vas a ver algo como:

```json
{
  "productos": [ { "_id": "lib-001", ... }, ... ],
  "carritos": { "usuario_demo": { "items": [ { "producto_id": "caf-001", "cantidad": 2 } ] } },
  "ordenes": []
}
```

## Trade-offs vs `../api/` (Mongo)

| Aspecto              | `api/` (Mongo)                     | **`api2/` (JSON)**                           |
|----------------------|------------------------------------|----------------------------------------------|
| Setup                | requiere docker + mongo            | **nada, solo `node`**                        |
| Concurrencia         | seguro multi-proceso               | ⚠️ un solo proceso (race entre N apps)       |
| Queries complejas    | `$regex`, índices, agregaciones    | `Array.filter` — todo en RAM                 |
| Escalabilidad        | millones de productos              | hasta ~10k cómodos                           |
| Debugging            | mongo shell / Compass              | **`cat data.json`** o abrir en VSCode         |
| Backups              | dump / replica set                 | copiar el archivo                            |
| Pérdida de datos     | replicación                        | borraste el archivo, perdiste todo           |

## Tres versiones lado a lado (totalmente independientes)

| Versión         | Lenguaje | Framework | Persistencia          | Puerto |
|-----------------|----------|-----------|------------------------|--------|
| `python/mcp/api/`| Python  | FastAPI   | MongoDB (`tienda_ipvg`) | 8040   |
| `ts/api/`        | TS      | Fastify   | MongoDB (`tienda_ipvg`) | 8041   |
| **`ts/api2/`**   | **TS**  | **Fastify** | **`data.json`**       | **8042** |

Los dos primeros comparten DB → se ven los mismos datos. Esta tercera tiene su propio archivo. Útil para enseñar que el contrato HTTP no depende del backend de datos.

## Estructura

```text
ts/api2/
├── db.ts                # readFileSync + writeFileSync sobre data.json
├── seed.ts              # CLI que inicializa data.json
├── api.ts               # Fastify (mismas rutas que ../api/api.ts)
├── data.json            # 👈 tu "base de datos" — versionable, legible, portable
└── static/index.html    # mismo HTML que ../api/, badge cambiado
```

## Notas técnicas

- **Atomicidad**: `readFileSync` + mutación + `writeFileSync` corre síncrono dentro de un mismo proceso de Node — no hay race entre handlers. Si corrés DOS procesos del server contra el mismo archivo, sí podés perder writes.
- **Performance**: cada operación lee y escribe el archivo completo. Con 20 productos es invisible (~1 ms). Con 10k productos puede empezar a doler — ahí ya conviene migrar a SQLite o Mongo.
- **Migración a real DB**: como `db.ts` expone funciones (no Mongo queries), reemplazás solo ese archivo. `api.ts` ni se entera. Es la misma idea que la slide 29 · Vector DBs: "la API se elige según el caso, los contratos se mantienen".
