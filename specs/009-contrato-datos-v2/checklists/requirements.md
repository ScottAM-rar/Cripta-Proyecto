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

### Implementación, cierre final (T044) (2026-11-08, rama Scott-Persona3, `7c885a9`)

Python 3.12.10, Windows AMD64. Los mismos laboratorios del cierre anterior, uno por uno con `python -m tests_labs.<nombre>`;
sin red: no se ejecutaron `prueba_cliente_http` ni `prueba_servicio`. Durante las mediciones había otro programa con
mucho uso de CPU abierto en la máquina (un juego, `VALORANT-Win64-Shipping`), así que los tiempos de esta sesión son más
altos que los del cierre anterior.

`python main.py --bench` se ejecutó primero tres veces con la salida redirigida a un archivo: las tres terminaron con
código 1 por `UnicodeEncodeError: 'charmap' codec can't encode character '→'`. Al redirigir, Python escribe en
cp1252 y no puede codificar la flecha de la fila «cargar la partida completa [binario → DTO]» (`bench/guardado.py`,
línea 93; el archivo no cambió en la 009, su último commit es `793b300`, de la 001). Es un efecto de la forma de capturar
la salida y no un fallo del bench, así que las tres corridas que valen son las que siguen, con `PYTHONIOENCODING=utf-8`
(no cambia el código).

| Comando | Resultado | Línea base (T002 / T049) | Diferencia |
|---|---|---|---|
| `python -m unittest discover -p "test_*.py"` | 295 pruebas, OK | 197 pruebas, OK | +98 pruebas nuevas de la 009 (288 en el cierre anterior; +7 de T054 a T058); ninguna falla |
| `python -m tests_labs.prueba_almacen_disco` | 40 de 40 | sin línea base en T002 (37 de 37 antes de T007) | igual al cierre anterior |
| `python -m tests_labs.prueba_archivo_indexado` | 23 de 23 | sin línea base en T002 | igual al cierre anterior |
| `python -m tests_labs.prueba_botin_enemigos` | 31 de 31 comprobaciones correctas | sin línea base en T002 | igual al cierre anterior |
| `python -m tests_labs.prueba_cache` | código de salida 0; imprime una lista y no tiene comprobaciones | sin línea base en T002 | igual al cierre anterior |
| `python -m tests_labs.prueba_cache_uso` | 13 de 13 | sin línea base en T002 | igual al cierre anterior |
| `python -m tests_labs.prueba_cliente_http_errores` | 13 de 13 | sin línea base en T002 | igual al cierre anterior |
| `python -m tests_labs.prueba_cliente_offline` | 13 de 13 | 13 de 13 | igual |
| `python -m tests_labs.prueba_cliente_persistente` | 23 de 23 | 23 de 23 | igual |
| `python -m tests_labs.prueba_fabrica` | 21 de 21 | 13 de 13 | +8 casos de T025 y T053 (igual al cierre anterior) |
| `python -m tests_labs.prueba_persistencia_partida` | **FALLA** (código 1): `AttributeError: 'EstadoJuegoLogica' object has no attribute 'guardarPartida'` en la línea 134 | sin línea base en T002 | **Anterior a la 009** (`3fc1017`, 2026-10-16); igual al cierre anterior |
| `python -m tests_labs.prueba_precarga_presupuesto` | 24 de 24 | 24 de 24 | igual |
| `python -m tests_labs.prueba_reporte_solicitudes` | **FALLA** (código 1): `IndexError: pop from empty list` en la línea 37, durante `ControladorJuego.iniciar` (línea 53) | sin línea base en T002 | **Anterior a la 009**: la pregunta de la tabla de puntajes (`c315271`, 2026-10-16) no está en las respuestas del laboratorio; igual al cierre anterior |
| `python -m tests_labs.prueba_vecinas_reporte` | 30 de 30 | sin línea base en T002 | igual al cierre anterior |
| `python -m tests_labs.sin_red` | 95 pruebas, 0 fallos, 0 errores | — (nuevo, T051) | +7 respecto de las 88 del cierre anterior |
| `python main.py --bench`, corrida 1 | **código 1**. Todos los bloques terminan (ya no hay `AttributeError` en `guardado` ni en `ciclo`). Bloque `ciclo`: «100 esbirros activos» NO CUMPLE (máx 20.11 ms); «300 esbirros activos» NO CUMPLE (mediana 22.31 ms, máx 42.61 ms). Bloque `llaves`, sección B: «guardar con A y 5000 salas ≤ 50 ms» NO CUMPLE (57.25 ms) | sin línea base completa (T049 midió solo `cache`) | ver abajo |
| `python main.py --bench`, corrida 2 | **código 1**. Bloque `ciclo`: «300 esbirros activos» NO CUMPLE (mediana 21.19 ms, máx 37.38 ms); «50 cazadores persiguiendo» NO CUMPLE (máx 20.95 ms). Bloque `llaves`, B: NO CUMPLE (58.30 ms) | — | ver abajo |
| `python main.py --bench`, corrida 3 | **código 1**. Bloque `ciclo`: «100 esbirros activos» NO CUMPLE (máx 25.52 ms); «300 esbirros activos» NO CUMPLE (mediana 21.17 ms, máx 39.38 ms). Bloque `llaves`, B: NO CUMPLE (50.12 ms) | — | ver abajo |
| En las tres corridas | `recorrido`: CUMPLE; `llaves` D: 1 / 0 / 0, CUMPLE; verificaciones de B y C: OK; filas de `terreno` (cazadores con jugador quieto y en movimiento): CUMPLE. La fila de 1 000 esbirros no cumple en ninguna corrida, pero es una prueba de estrés y no decide el veredicto | — | — |
| Diagnóstico: `python main.py --bench llaves` solo | código 1: guardar con A y 5000 salas 62.19 ms, NO CUMPLE | — | — |
| Diagnóstico: `python main.py --bench ciclo` solo | código 1: «100 esbirros activos» máx 32.32 ms; «300 esbirros activos» mediana 15.73 ms, máx 29.39 ms | — | — |

**Bloque `cache`, 9 filas de conteo** (iguales en las tres corridas):

| Fila | T049 (antes) | Cierre final, corridas 1, 2 y 3 | Diferencia |
|---|---|---|---|
| sala por sala (sin precarga) | 63 solicitudes | 63 | igual |
| actual + vecinas (prof. 2) | 61 | 61 | igual |
| perezosa, prof. 2 | 33 | 33 | igual |
| perezosa, por defecto (lote de 10) | 9 | 9 | igual |
| caché, capacidad 5 | 82 / 938, 19 solicitudes | 82 / 938, 19 | igual |
| caché, capacidad 10 | 316 / 704, 19 | 316 / 704, 19 | igual |
| caché, capacidad 25 | 487 / 533, 19 | 487 / 533, 19 | igual |
| caché, capacidad 100 | 950 / 70, 19 | 950 / 70, 19 | igual |
| caché, capacidad 1000 | 950 / 70, 19 | 950 / 70, 19 | igual |

**Fallos anotados**:

- `prueba_persistencia_partida` y `prueba_reporte_solicitudes`: ya fallaban antes de la 009 (ver el cierre anterior).
- Criterio de tiempo del bloque `ciclo` (límite de 20 ms para el peor de 30 ciclos): `bench/ciclo.py` no cambió en la 009
  (su último commit es `793b300`, de la 001). En esta sesión, con la máquina cargada, la fila «300 esbirros activos» no
  cumplió en ninguna corrida y su mediana también pasó de 20 ms (21.17 a 22.31 ms en las corridas completas, 15.73 ms en
  la corrida aislada). Además fallaron por poco otras dos filas que el prompt del cierre no nombraba: «100 esbirros
  activos» (corridas 1 y 3) y «50 cazadores persiguiendo» (corrida 2).
- **Criterio de tiempo del bloque `llaves`, sección B** (guardar con la opción A y 5 000 salas ≤ 50 ms, `research.md`
  §4): **no cumplió en ninguna de las cuatro mediciones** (57.25, 58.30, 50.12 y 62.19 ms). Es un criterio de la 009 y
  no estaba entre los fallos admitidos. En el cierre anterior el bloque `llaves` terminó con código 0 y `DECISIONES.md`
  registra 27.14 ms. Lo probable es la carga de la máquina, pero no se comprobó con la máquina libre.

**T044 queda sin marcar**: además de los fallos admitidos, falla el criterio de 50 ms del bloque `llaves`.

### Implementación, cierre final (T044): repetición con la máquina libre (2026-11-08, rama Scott-Persona3, `a122f53`)

Las mediciones anteriores se tomaron con otro programa usando mucha CPU. Se repitieron en PowerShell con ese programa cerrado y `$env:PYTHONIOENCODING = "utf-8"`. De las cuatro ejecuciones pedidas (`--bench llaves` y tres `--bench` completos), la terminal conservó la salida de dos `python main.py --bench` completos; las otras dos no quedaron guardadas, así que no se anotan.

| Corrida | Código de salida | «NO CUMPLE» | Llaves B: guardar con A y 5000 salas (≤ 50 ms) | Ciclo: 300 esbirros activos (peor de 30 ciclos < 20 ms) | Ciclo: 100 esbirros | Ciclo: 50 cazadores |
|---|---|---|---|---|---|---|
| `--bench` completo, corrida 1 | 0 | ninguno | CUMPLE, 14.37 ms | CUMPLE, mediana 3.85 ms, máx 5.76 ms | CUMPLE, máx 3.37 ms | CUMPLE, máx 1.19 ms |
| `--bench` completo, corrida 2 | 0 | ninguno | CUMPLE, 14.80 ms | CUMPLE, mediana 3.82 ms, máx 5.71 ms | CUMPLE, máx 3.08 ms | CUMPLE, máx 1.54 ms |

En ambas corridas: Llaves D da 1 / 0 / 0 (CUMPLE), «Llaves (SC-001, SC-002): CUMPLE.» y «Recorrido por niveles (SC-004, equivalencia y verificaciones previas): CUMPLE.». La fila de 1 000 esbirros (prueba de estrés, no decide el veredicto) dio máx 15.52 y 18.12 ms.

**Conclusión:** con la máquina libre, el criterio de 50 ms de Llaves B y los de tiempo del bloque `ciclo` se cumplen con holgura (14.37 y 14.80 ms; peor ciclo de 5.76 y 5.71 ms). Los incumplimientos de la sección anterior (50.12 a 62.19 ms y 21 a 22 ms de mediana en 300 esbirros) se debieron a la carga de la máquina, no a la capacidad. Lo único que falla es lo anterior a la 009: `prueba_persistencia_partida` (`guardarPartida`) y `prueba_reporte_solicitudes` (pregunta de puntajes). T044 queda marcada.
