# Specification Quality Checklist: Contrato de datos v2 y ubicación de llaves

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-06
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Pendiente 1 marcador (FR-313, citado también en Historia 3 escenario 3): ¿se juega sin verificación ante fallo de llaves? — resuelto en la clarificación y la corrección post-analyze; ahora FR-301 a FR-325
- La ruta del servicio (`GET /criptas/<id>/llaves`) y `--offline` se nombran en la entrada del usuario; en la spec se habla de «consulta de llaves» y del modo `--offline` como opción de juego ya existente, no como detalle de implementación.
- Cobertura: FR-301 a FR-324 citados por al menos un escenario. — resuelto en la clarificación y la corrección post-analyze; ahora FR-301 a FR-325

### Implementación, grupo A (2026-11-07, código sin cambios, rama Scott-Persona3, `d0968c1`)

**T049 — línea base de `--bench cache`** (`python main.py --bench cache --bench-csv specs/009-contrato-datos-v2/bench-cache-antes.csv`, Python 3.12.10, Windows AMD64, semilla 2026; salida 0; CSV con 30 filas en `bench-cache-antes.csv`):

- Solicitudes al recorrer un pasillo de 60 salas: sala por sala 63; actual + vecinas (prof. 2) 61; perezosa prof. 2 33; perezosa por defecto (lote de 10) 9.
- Caché en una partida completa (150 pasos, rejilla 10x10), aciertos / fallos y solicitudes de red:
  - capacidad 5: 82 / 938 (8.0 %), 19 solicitudes
  - capacidad 10: 316 / 704 (31.0 %), 19 solicitudes
  - capacidad 25: 487 / 533 (47.7 %), 19 solicitudes
  - capacidad 100: 950 / 70 (93.1 %), 19 solicitudes
  - capacidad 1000: 950 / 70 (93.1 %), 19 solicitudes
- Los tiempos (búsqueda en caché, lectura y escritura en disco, vecindad) quedan en el CSV; dependen de la máquina y no se usan como línea base estricta.
- La consola de Windows (cp1252) muestra mal los acentos y los símbolos § y µ; el CSV está bien en UTF-8.

**T002 — línea base de pruebas y laboratorios**:

- `python -m unittest discover -p "test_*.py"`: **197 pruebas, OK** (0 fallos, 0 errores), en 16 archivos `test_*.py`.
- Laboratorios ejecutados **como dice T002** (`python tests_labs/<lab>.py`): **los 4 fallan** con `ModuleNotFoundError: No module named 'adaptadores'`. Al ejecutarse como script, `sys.path` empieza en `tests_labs/` y no en la raíz.
- Los mismos laboratorios ejecutados como indican su docstring y `DOCUMENTACION_API.md` (`python -m tests_labs.<lab>`):
  - `prueba_cliente_persistente`: 23 de 23 OK
  - `prueba_cliente_offline`: 13 de 13 OK
  - `prueba_fabrica`: 13 de 13 OK
  - `prueba_precarga_presupuesto`: 24 de 24 OK
- Línea base de llamadas sin llaves (para T013 a), tomada de `prueba_cliente_persistente`:
  - Primera ejecución en carpeta vacía: 7 solicitudes, `criptas`, `datos`, `salas`, `contenido`, `version_catalogo` y `catalogo` ×2 (fichas y botín).
  - Segunda ejecución con nada cambiado: 3 solicitudes, `criptas`, `datos` y `version_catalogo`.
  - `prueba_fabrica`: 7 solicitudes en la primera ejecución.

**T001 — revisión contra el principio I** (`plan.md`, `research.md`, `tasks.md`):

- No proponen `dict`, `set`, `heapq`, `bisect` ni `collections` como índice. Esos nombres solo aparecen:
  - como prohibición (plan, Constitución; tasks, reglas y T043);
  - como alternativa descartada (research: `set` de tuplas);
  - en el riesgo R3, el `deque` existente;
  - como tipo de la respuesta JSON cruda (`list[dict]`, `respuesta: dict`, `contenido_en_disco -> dict | None`), que se lee y no se usa como índice.
- Detección de repetidos: `ordenar_adaptativo` (`Logica/ordenamiento.py`) no importa nada de `collections` y acepta `key`. Basta con ordenar por la terna y comparar posiciones vecinas, sin `dict` ni `set`.
- `existe`: es una lista de booleanos indexada por número de sala, hecha con una `list` común.
- Precarga por costo del bench: `Logica/CampoDeCostos.py` importa solo `BuscadorRutas` y `MapaCripta`; `BuscadorRutas` importa solo `MonticuloMinimo`; `MonticuloMinimo` no importa nada. Ninguno usa `dict`, `set`, `heapq`, `bisect` ni `collections`.
- Ya existe y no es de esta capacidad: `adaptadores/servicioCripta.py` importa `collections.deque` (línea 2; usos en `salas_vecinas` l. 330 y `_armar_salidas` l. 450–455). Coincide con R3; no se agregan usos.
- Discrepancia de documentación, sin corregir: la firma de `obtener_llaves` en `research.md` §2 (tabla, línea 44) y en `data-model.md` (sección ClienteInterfaz) no incluye `limite_solicitudes`, que sí aparece en `contracts/interfaz-clientes.md` y en T009.

### Implementación, cierre (T044) (2026-11-07, rama Scott-Persona3, `d2bf716`)

Python 3.12.10, Windows AMD64. Sin red: no se ejecutaron `prueba_cliente_http` ni `prueba_servicio`, que usan el servidor
real. Antes de correr los laboratorios se comprobó que los que escriben `logs/` o `Partidas Guardadas/` lo hacen en una
carpeta temporal (`os.chdir`). No se ejecutaron los archivos que no son laboratorios (`api_falsa`, `cripta_sintetica`,
`escenarios_terreno`, `laboratorio`, `laboratorio_archivo`, `partida_prueba`, `referencia_recorrido`).

| Comando | Resultado | Línea base (T002 / T049) | Diferencia |
|---|---|---|---|
| `python -m unittest discover -p "test_*.py"` | 288 pruebas, OK | 197 pruebas, OK | +91 pruebas nuevas de la 009; ninguna falla |
| `python -m tests_labs.prueba_almacen_disco` | 40 de 40 | sin línea base en T002 (37 de 37 antes de T007) | +3 casos de T007 |
| `python -m tests_labs.prueba_archivo_indexado` | 23 de 23 | sin línea base en T002 | — |
| `python -m tests_labs.prueba_botin_enemigos` | 31 de 31 comprobaciones correctas | sin línea base en T002 | — |
| `python -m tests_labs.prueba_cache` | código de salida 0; imprime una lista y no tiene comprobaciones | sin línea base en T002 | — |
| `python -m tests_labs.prueba_cache_uso` | 13 de 13 | sin línea base en T002 | — |
| `python -m tests_labs.prueba_cliente_http_errores` | 13 de 13 | sin línea base en T002 (13 de 13 al empezar el grupo C2) | igual |
| `python -m tests_labs.prueba_cliente_offline` | 13 de 13 | 13 de 13 | igual |
| `python -m tests_labs.prueba_cliente_persistente` | 23 de 23 | 23 de 23 | igual |
| `python -m tests_labs.prueba_fabrica` | 21 de 21 | 13 de 13 | +8 casos de T025 y T053 |
| `python -m tests_labs.prueba_persistencia_partida` | **FALLA** (código 1): `AttributeError: 'EstadoJuegoLogica' object has no attribute 'guardarPartida'` en la línea 134 (`original.guardarPartida(archivo)`) | sin línea base en T002 | **Anterior a la 009**: `EstadoJuegoLogica.guardarPartida` se separó en `3fc1017` (2026-10-16); falla igual antes y después de T047 |
| `python -m tests_labs.prueba_precarga_presupuesto` | 24 de 24 | 24 de 24 | igual |
| `python -m tests_labs.prueba_reporte_solicitudes` | **FALLA** (código 1): `IndexError: pop from empty list` en la línea 37, durante `ControladorJuego.iniciar` (línea 53, «Ingresa el número de la cripta») | sin línea base en T002 | **Anterior a la 009**: el laboratorio responde `["n", "1", "7", …]`, pero el controlador pregunta primero por la tabla de puntajes y después si se carga una partida. La pregunta de puntajes entró en `c315271` (2026-10-16) y el laboratorio no cambió desde entonces; en la base de la 009 la lista de respuestas y las preguntas eran las mismas |
| `python -m tests_labs.prueba_vecinas_reporte` | 30 de 30 | sin línea base en T002 | — |
| `python -m tests_labs.sin_red` | 88 pruebas, 0 fallos, 0 errores | — (nuevo, T051) | — |
| `python main.py --bench` (todos los bloques) | **código 1**: se corta en el bloque `guardado` con `AttributeError: 'ClienteDeBatalla' object has no attribute 'obtener_llaves'` | sin línea base completa (T049 midió solo `cache`) | **Regresión de la 009** (ver abajo) |
| `python main.py --bench <bloque>`, uno por uno | código 0: `agenda`, `cache`, `salas`, `inventario`, `retroceso`, `ordenamiento`, `bitacora`, `terreno` («§5.2: … CUMPLE»), `recorrido` («CUMPLE») y `llaves` («Llaves (SC-001, SC-002): CUMPLE.»). Código 1: `guardado` y `ciclo`, con el mismo `AttributeError` | — | `guardado` y `ciclo`: regresión de la 009 |
| Cuentas del bloque `cache` | 63 / 61 / 33 / 9 solicitudes; caché 82/938, 316/704, 487/533, 950/70 y 950/70 aciertos/fallos, con 19 solicitudes de red | las mismas (T049) | iguales; los tiempos dependen de la máquina y no se comparan |

**Regresión de la 009 en `--bench guardado` y `--bench ciclo`**: `bench/juego.py` arma la partida del bench con
`ClienteDeBatalla`, un cliente sintético sin `obtener_llaves`. Desde T017 (commit `a0a7c43`), `EstadoJuegoLogica.iniciarJuego`
llama a `obtenerLlaves()`. La consulta llega a `ClientePersistente.obtener_llaves`, que llama a
`self.cliente.obtener_llaves`, y el `AttributeError` resultante no es un `RuntimeError`, así que no se convierte en
`LlavesNoDisponibles` y corta el bloque. `bench/juego.py`, `bench/guardado.py` y `bench/ciclo.py` no cambiaron en la 009,
y en la base de la 009 `iniciarJuego` no pedía llaves: antes funcionaban. **T044 queda sin marcar** hasta corregirlo.
