# Plan de implementación: Revisión de la Parte I con la carga nueva

**Rama**: `Scott-Persona3` (carpeta `012-revision-parte-i`) | **Fecha**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación de `specs/012-revision-parte-i/spec.md` (FR-370 a FR-388) | **Investigación**: [research.md](research.md)

## Resumen

Esta capacidad revisa las decisiones de red, caché y guardado de la Parte I con la carga de la Parte II, y quita las dos colas de biblioteca que quedan en código evaluado.

- **Planeación de la vecindad** (`ServicioCripta.salas_vecinas`): deja la cola de biblioteca y recorre por niveles leyendo la propia lista de salas alcanzadas con un índice y una marca de fin de nivel (D1). El resultado, los errores y las búsquedas en el esqueleto son los mismos.
- **Caché de fichas** (`adaptadores/cache.py`): pasa a una lista propia con la más reciente al final (D2), con los mismos aciertos, fallos y orden de expulsión.
- **Mediciones**: se toman en tres pasos. M0 es el antes, con el código de `0b031ec` y **antes de tocar nada**. M1 es la carga nueva sobre el mismo código. M2 es el después. Así cada diferencia queda atribuida a la carga o al código (D3). Cada paso son tres ejecuciones de cada bloque, y cada fila de tiempo registra la mediana de las tres (FR-383, FR-384).
- **Inventario**: se corrigen 2 usos (la vecindad y la caché). Se justifican 6: el contenedor de salidas, su conversión desde la API, su reconstrucción al cargar la partida, `collections.abc.Callable` y dos grupos de conjuntos literales constantes. Se excluyen por ser lectura de JSON los dicts con la forma de la respuesta de la API; quedan 18 apariciones de `dict` por revisar a mano (D5).

**La corrección de la spec ya está hecha** (principio X), en commits propios y anteriores al código:
- `5f38435`: el orden vigente de las salidas es N, S, E, O (research H1), los bytes leídos de una sala crecen con log n (research H2) y la versión vigente es `0b031ec` (research H3);
- `e746807`: lo que encontró el analyze (sin nombres de estructuras, filas nuevas y su antes, mediana de tres ejecuciones, cripta de referencia de 1 000 salas y prefijo FR-3xx).

El plan no cambia ninguna regla: sigue a FR-370 («lo mismo que la versión vigente»).

## Contexto técnico

**Lenguaje y versión**: Python 3.12 (el del proyecto; sin dependencias nuevas).

**Dependencias principales**: biblioteca estándar permitida (`struct`, `json`, `os`, `tempfile`, `time`, `random` con semilla, `inspect` solo en pruebas). Sin `collections`, `heapq`, `bisect` ni `networkx` en lo que se cambia.

**Almacenamiento**: archivos de la caché persistente (`AlmacenDisco`, sin cambios) y partida binaria de formato 8 (`AlmacenPartidaBinario`, sin cambios). Los resultados van en `specs/012-revision-parte-i/` (`mediciones.md` y los CSV de M0, M1 y M2).

**Pruebas**: `unittest`, con archivos `test_*.py` en la raíz, como el resto del proyecto. Dos archivos nuevos (D4).

**Plataforma**: escritorio (Windows y Linux), modo consola y `--bench`, sin red.

**Tipo de proyecto**: juego de consola de un solo proyecto, con capas Controlador → Servicio → Lógica y adaptadores.

**Objetivos de rendimiento**:
- ninguna fila de red del después supera 2 × su antes (FR-383);
- guardar, cargar y leer una sala del binario no superan 2 × su antes (FR-384);
- la vecindad hace el mismo número de búsquedas en el esqueleto que hoy (FR-374).

**Restricciones**:
- no se tocan `SalaDTO`, `EstadoGuardadoLogica`, `AlmacenPartidaBinario`, `EstadoGuardadoDTO` ni `codec_partida`;
- el contenedor de salidas de cada sala no se cambia;
- `Logica` y `DTO` no importan de `adaptadores`;
- la regla de precarga no cambia (FR-324).

**Escala**: criptas sintéticas de 60 salas (pasillo), 100 (rejilla de 10 × 10), 1 000 (vecindad) y partidas de 10, 100 y 1 000 salas. La de 1 000 hace de cripta del tamaño de referencia (research D3).

## Revisión constitucional

*Compuerta: se revisó antes de la fase 0 y otra vez después del diseño (fase 1).*

| Principio | Cómo lo cumple el plan | Estado |
|---|---|---|
| I. Estructuras propias | D1 y D2 quitan las dos colas de biblioteca del código evaluado. No se agrega ningún `dict` ni `set` como índice, ningún `sorted` ni `.sort`, `heapq`, `bisect` ni `networkx`. Las referencias de las pruebas también usan solo listas. Los usos que quedan están en el inventario con su justificación (D5). Ver la [revisión contra la lista de prohibidos](#revisión-contra-la-lista-de-prohibidos-principio-i) | ✅ |
| II. Determinismo | Los cambios conservan el orden (vecindad) y el orden de expulsión (caché). La carga del bench (costos, cazadores, llaves) sale de semillas fijas, y el desempate de los cazadores del bench es N, S, E, O | ✅ |
| III. Equivalencia ante el reuso | No se agrega reuso ni estado entre consultas. D1 descarta las marcas por época justamente para no tener que invalidar nada | ✅ |
| IV. MVC y adaptadores | Los cambios quedan en `adaptadores/`. Nada de `Logica` ni de `DTO` importa de `adaptadores`. `--bench` no instancia la vista | ✅ |
| V. Sin datos de una cripta concreta | Las criptas de medición y de prueba son sintéticas y salen de una semilla. La medición manual con la cripta publicada más grande se hace a mano y no queda en el código | ✅ |
| VI. Presupuesto y versiones | La consulta de llaves se cuenta en el bench (+1). El formato de partida no cambia | ✅ |
| VII. Rendimiento medido | Antes y después con `--bench`. La sección 2 conserva la tabla hash descartada y agrega la lista enlazada descartada. Las criptas son sintéticas por semilla | ✅ |
| VIII. La spec precede al código | El plan no agrega reglas. Los defectos de la spec que encontró (H1 y H2) y los del analyze ya se corrigieron en la spec (`5f38435` y `e746807`) | ✅ |
| IX. Trazabilidad | Cada prueba cita su FR. La tabla requisito → prueba o medición está en [quickstart.md](quickstart.md#trazabilidad) | ✅ |
| X. Cambios de especificación | Las correcciones están en commits de spec separados y anteriores al código (`5f38435` y `e746807`) | ✅ |
| XI. Uso de LLM | El prompt del plan se registra en `PROMPTS_Scott.md` (lo hace el grupo) | ✅ |

**Resultado de la compuerta**: aprobada, sin pendientes.

## Decisiones (detalle en [research.md](research.md))

| Id | Decisión | Elegida | Complejidad | Medición |
|---|---|---|---|---|
| D1 | Vecindad sin cola de biblioteca | Leer `alcanzadas` con un índice y una marca de fin de nivel. Se descartan `ColaCircular` (duplica los datos y no guarda el nivel) y las marcas por id (O(N) por consulta o estado entre consultas) | O(k·N) por las búsquedas en el esqueleto (sin cambios) + O(k²) de pertenencia; memoria O(k) | `--bench cache` sección 5; prueba de equivalencia D4-a |
| D2 | Caché sin cola de biblioteca | Lista propia con la más reciente al final. Se descartan la inserción al frente (corre todo), la lista enlazada (no mejora el orden total sin un índice) y la tabla hash (ya descartada en la Parte I). Si la sección 2 pasa de 2×, se prueba la lista enlazada | O(n) en obtener, insertar y desalojar, igual que hoy | `--bench cache` secciones 2 y 6; prueba de equivalencia D4-b |
| D3 | Mediciones | M0 (antes, el primer paso) → M1 (carga, mismo código) → M2 (después), cada una con tres ejecuciones y la mediana en las filas de tiempo. La carga va en los mismos escenarios. Filas de cuenta y de tiempo según la tabla de D3 | — | `mediciones.md`, CSV |
| D4 | Pruebas | Espías de búsquedas y descargas contra una referencia escrita en la prueba; LRU de referencia con secuencias aleatorias de semilla fija. Ambas pasan primero contra `0b031ec`, salvo las dos comprobaciones del principio I (T009 y T012), que fallan contra `0b031ec` a propósito y pasan después de D1 y D2 | — | `test_vecindad_equivalencia.py`, `test_cache_equivalencia.py`, suite completa |
| D5 | Inventario y documentación | Búsqueda mecánica + revisión manual. 2 se corrigen, 6 se justifican, los dicts con forma de JSON se excluyen y 18 apariciones de `dict` se revisan a mano. Sección 012 en `DECISIONES.md` y notas en las secciones 2, 6 y 8 del documento de la Parte I | — | Repetir la búsqueda (quickstart) |

## Orden de trabajo

1. **M0, antes de tocar cualquier archivo de código**: `--bench cache` y `--bench guardado` con `0b031ec`, tres ejecuciones de cada uno, más la suite completa. Se copian la salida, el comando, la fecha y el commit en `mediciones.md`, y cada fila de tiempo registra la mediana (FR-377, FR-383, FR-384).
2. Corrección de la spec: hecha en `5f38435` y `e746807`, en commits propios anteriores al código.
3. Pruebas D4-a y D4-b. Se comprueba que **pasan con el código de `0b031ec`**, salvo las dos comprobaciones del principio I (T009 y T012), que fallan a propósito y pasan después de D1 y D2.
4. Código de medición: carga nueva en `adaptadores/bench_red_mejorado.py` y `bench/guardado.py`, filas nuevas de guardado, filas de la lista enlazada descartada. Se ejecuta **M1** (tres ejecuciones, mediana en las filas de tiempo) sin haber tocado el código de producción.
5. D1 en `salas_vecinas` y D2 en `cache.py`. Pruebas D4 y la suite completa.
6. **M2**, tres ejecuciones. Se comprueba que las filas de cuenta salen iguales en las tres y, con la mediana de las filas de tiempo, que se cumplen los límites de 2×. Medición manual de la cripta publicada más grande.
7. Inventario final (repetir la búsqueda), sección 012 de `DECISIONES.md` y notas en `DOCUMENTACION_DECISIONES_DISENO.md`, indicando si cada decisión final coincide con este plan (FR-388).

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/012-revision-parte-i/
├── spec.md
├── plan.md                  # este archivo
├── research.md              # fase 0: D1 a D5 y hallazgos H1 a H3
├── data-model.md            # fase 1: entidades de la medición y del inventario
├── quickstart.md            # fase 1: cómo validar y trazabilidad
├── contracts/
│   ├── vecindad-y-cache.md  # comportamiento observable que no cambia
│   └── filas-medicion.md    # catálogo de filas y formato de mediciones.md
├── mediciones.md            # se crea en M0 (paso 1)
├── bench-*-M0|M1|M2-1|2|3.csv  # salidas de --bench-csv (tres ejecuciones por paso)
└── tasks.md                 # lo genera /speckit-tasks
```

### Código (raíz del repositorio)

```text
adaptadores/
├── servicioCripta.py        # D1: solo el cuerpo de salas_vecinas (sigue importando la cola por _armar_salidas, uso justificado)
├── cache.py                 # D2: CacheLRU sobre lista propia; misma interfaz
└── bench_red_mejorado.py    # D3: carga nueva en el cliente sintético, cazadores, +1 llaves, filas descartadas (código de medición)
bench/
└── guardado.py              # D3: carga en estado_con_salas, filas de bytes leídos y de primera/última sala, subclase contadora
test_vecindad_equivalencia.py   # D4-a (nuevo)
test_cache_equivalencia.py      # D4-b (nuevo)
DECISIONES.md                   # D5: sección 012
DOCUMENTACION_DECISIONES_DISENO.md  # D5: notas en §2, §6 y §8
```

**No se tocan**: `DTO/SalaDTO.py`, `DTO/EstadoGuardadoDTO.py`, `Logica/EstadoGuardadoLogica.py`, `adaptadores/AlmacenPartidaBinario.py`, `codec_partida`, `precargar_vecinas` (FR-324), `Logica/ColaCircular.py`, `adaptadores/bench_red.py` (copia histórica que no se ejecuta con `--bench`).

**Decisión de estructura**: un solo proyecto, con las carpetas existentes. No se crean módulos de producción nuevos.

## Revisión contra la lista de prohibidos (principio I)

Se revisó cada elemento del plan contra la lista: `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx`, `dict` y `set` como índice o caché, `sorted()` y `.sort()`.

| Elemento del plan | ¿Usa algo prohibido? | Comentario |
|---|---|---|
| D1 `salas_vecinas` | No | Usa una lista, un índice entero y una marca de fin de nivel. Lee las salidas del esqueleto, un dict con la forma del JSON de la API, igual que hoy: es lectura de JSON, permitida |
| D2 `CacheLRU` | No | Lista de listas `[clave, valor, veces]`. La búsqueda es lineal; no hay dict por clave |
| D3 cliente sintético y cazadores del bench | No | La ruta de los cazadores se calcula por niveles con listas, y el desempate es por orden de letras, no ordenando. Las salidas sintéticas tienen la forma del JSON |
| D3 subclase contadora de bytes | No | Un entero que acumula |
| D4 referencias de las pruebas | No | La cola por índice y la LRU de referencia son listas. Las secuencias salen de `random.Random(semilla)` |
| D5 inventario | — | Es una búsqueda, no código |
| Lo que queda en el repositorio | Sí, justificado | Usos 3 a 6, 9 y 10 del inventario (contenedor de salidas, su conversión y reconstrucción, `collections.abc.Callable` y los conjuntos literales constantes), justificados por escrito según FR-386. Fuera de la caché y la vecindad no se corrige nada, por la clarificación de la spec |

**Conclusión**: nada de lo que el plan agrega o cambia rompe el principio I. El único choque posible es tipográfico: `servicioCripta.py` sigue importando la cola de biblioteca por `_armar_salidas` (uso 4, justificado). Por eso FR-375 se comprueba sobre el código del método `salas_vecinas`, no sobre el archivo.

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar. Las correcciones de la spec (VIII y X) ya están hechas en `5f38435` y `e746807`; no eran excepciones.
