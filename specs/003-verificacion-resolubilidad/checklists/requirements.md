# Specification Quality Checklist: Verificación de resolubilidad

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-08
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

- Las 3 `[NEEDS CLARIFICATION]` se resolvieron el 2026-11-08 (Q1: A, Q2: A, Q3: A) y constan en la sección Clarificaciones de la spec: completar = llegar a la sala de salida con la llave de salida obtenible (FR-332); desempate por menor id de sala y luego id de llave (FR-335); aviso de `--forzar` solo al iniciar, como FR-313 (FR-340).
- El nombre `ResultadoVerificacion` aparece una sola vez en Entidades clave como nombre del contrato acordado con quien conecta las opciones (lo pidió la entrada); no se nombran clases, módulos ni estructuras.
- Las opciones `--verificar`, `--forzar`, `--offline` y `--bench` son la interfaz que ve quien juega, no detalles de implementación.
- Los 4 casos B-R del Apéndice B son escenarios de aceptación (H1-2, H2-1, H3-1, H4-1). Todos los FR-330 a FR-346 se citan en al menos un escenario.
- **T001 (2026-11-08, revisión del principio I)**: sin hallazgos. `plan.md`, `research.md`, `data-model.md` y `tasks.md` solo nombran `dict`, `set`, `heapq`, `bisect`, `collections`, `networkx`, `sorted()` y `.sort()` para prohibirlos o descartarlos; las únicas menciones de `dict` son el `dict` de datos generales que ya se lee del JSON en los adaptadores (permitido). `IndiceLlaves` usa `ordenar_adaptativo` y búsqueda binaria propia; el recorrido por oleadas usa `ColaCircular`, `MonticuloMinimo` y listas por id de sala o número de llave; la elección de ubicación compara cadenas a mano; el oráculo (`tests_labs/referencia_resolubilidad.py`) ordena con `ordenar_adaptativo`. Ninguno necesita `dict`, `set`, `collections`, `sorted()` ni `.sort()`.
- **T002 (2026-11-08, línea base antes de cualquier cambio de código)**: `python -m unittest discover -p "test_*.py"`: 295 pruebas, OK (0 fallos, 0 errores). `python -m tests_labs.sin_red`: 95 pruebas con `requests.get` bloqueado, OK (0 fallos, 0 errores). No se ejecutaron `prueba_cliente_http` ni `prueba_servicio`.
- **T002, complemento (2026-11-08, antes de cambiar código)**: con el caso B-R3 de la API falsa v2, `listar_criptas()` + `esqueleto("cripta-01")` hacen exactamente las llamadas `[('criptas', None), ('salas', 'cripta-01')]` (2 solicitudes). Es la línea base que fija la garantía G6 de `test_mapa_con_llaves`.
- **T009 (2026-11-08)**: `test_mapa_con_llaves` pasa completo (6/6). G3 (`--offline`) y G4 (`FuenteSoloLocal`) pasaron sin cambios en esos adaptadores: la llave ya se guardaba en el esqueleto crudo y bastó con no descartarla en `ServicioCripta.esqueleto()`. No hace falta actualizar `research.md` §1. Suite: 301 pruebas OK (295 de la línea base + 6 nuevas); `tests_labs.sin_red`: 95 OK.
