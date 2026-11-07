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
