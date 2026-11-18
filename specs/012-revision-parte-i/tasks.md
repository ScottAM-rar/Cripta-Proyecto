# Tareas: Revisión de la Parte I con la carga nueva

**Entrada**: [plan.md](plan.md), [spec.md](spec.md) (FR-370 a FR-388), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Requisitos previos**: la corrección de la spec (H1, H2 y H3, principio X) tiene que estar en un commit propio, anterior a cualquier tarea de código.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin depender de tareas incompletas).
- **[US1]…[US5]**: historia de la spec. US1: la vecindad se planea igual que hoy; US2: la vecindad cumple el principio I; US3: mediciones de red, caché y guardado con la carga nueva; US4: leer una sala sin leer todo el archivo; US5: inventario de usos prohibidos.
- Cada tarea cita los FR que atiende. No hay tareas sin requisito.

**Organización**: las fases siguen el **orden de trabajo del plan**, que es obligatorio porque el antes (M0) y M1 tienen que medirse con el código sin tocar. Dentro de cada fase las tareas van agrupadas por historia, con las pruebas antes que el código. Las pruebas de equivalencia tienen que pasar contra el código de `0b031ec` antes de cambiarlo. Las únicas excepciones son las dos comprobaciones del principio I (T009 y T012): fallan contra `0b031ec` a propósito, porque demuestran el cambio.

## Reglas para todas las tareas (constitución)

- **Principio I**: nada de `collections`, `heapq`, `bisect` ni `networkx`; ningún `dict` ni `set` como índice o caché; nada de `sorted()` ni `.sort()`. Vale también en las referencias de las pruebas y en el código de medición nuevo.
- **No se tocan** `DTO/SalaDTO.py`, `DTO/EstadoGuardadoDTO.py`, `Logica/EstadoGuardadoLogica.py`, `adaptadores/AlmacenPartidaBinario.py`, `codec_partida` ni `precargar_vecinas` (FR-324). Usar sus clases desde el código de medición, sin modificarlas, sí está permitido.
- `Logica` y `DTO` no importan de `adaptadores`. `--bench` no instancia la vista ni usa la red.
- Sin commits dentro de las tareas. Los hace el grupo, con la spec antes que el código (principio X).

## Revisión contra la lista de prohibidos (principio I)

**Hecha el 2026-11-18**, antes de implementar. Lista: `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx`, `dict` y `set` como índice o caché, `sorted()` y `.sort()`. Se revisan las tareas que escriben código nuevo.

| Tarea | ¿Usa algo prohibido? | Comentario |
|---|---|---|
| T005 | No | El cliente sintético y el espía cuentan con enteros. Los esqueletos de `esqueleto_de_conexiones` tienen la forma del JSON de la API (lectura de JSON, permitida). La referencia recorre por niveles con una lista de pares y un índice de lectura; la pertenencia se comprueba recorriendo la lista |
| T006 | No | **Muestreo de salas**: las 50 salas de la cripta de 1 000 salen de `random.Random(semilla).sample(...)`, que devuelve una lista; se recorren en el orden devuelto, sin ordenarlas |
| T007 | No | Listas literales y comparaciones |
| T008 | No | Solo `assertRaises` y contadores enteros |
| T009 | No | Los nombres prohibidos aparecen solo como texto que se busca en el código fuente, guardado en una tupla constante; no se usan |
| T010 | No | La LRU de referencia es una lista de listas `[clave, valor, veces]` con búsqueda lineal, sin `dict` por clave. Las secuencias salen de `random.Random(semilla)` |
| T011 | No | Casos dirigidos sobre la misma referencia |
| T012 | No | Reutiliza `importaciones_prohibidas` de `test_monticulo_minimo.py`, que recorre el árbol sintáctico y compara contra la tupla `MODULOS_PROHIBIDOS` |
| T015 | No | Las salidas sintéticas tienen la forma del JSON de la API. El costo simétrico se lee de la salida opuesta ya armada, sin tabla aparte. `obtener_llaves` devuelve una lista con la forma de la API |
| T016 | No | Las posiciones de los cazadores se guardan en una lista; la pertenencia se comprueba recorriéndola |
| T017 | No | **Recorrido de los cazadores del bench**: por niveles, con una lista de pares (sala, primera salida) leída con un índice. La pertenencia se comprueba recorriendo la lista. El desempate sale de expandir las salidas en el orden N, S, E, O, sin ordenar |
| T018 | No | Llamadas al servicio y contadores enteros |
| T019 | No | **Lista enlazada de prototipo**: nodos propios con anterior y siguiente, y búsqueda lineal desde la cabeza. No hay índice por clave (eso sería la alternativa (d) de D2, ya descartada) |
| T020 | No | Clases DTO sin modificar. `exploradas` y `avistadas` se arman con `range` y salen ya en orden ascendente, sin ordenar |
| T021 | No | **Envoltorio que cuenta bytes**: guarda el archivo y un entero que suma lo que devuelve cada `read`; el contador de entradas es otro entero |
| T024 | No | Lista `alcanzadas`, un índice de lectura y una marca de fin de nivel. La pertenencia se comprueba recorriendo la lista. `.get("salidas") or {}` es lectura de JSON |
| T027 | No | Lista propia de listas, con `del` y `append`; se quita la importación de `collections` |
| T039 | Quita o justifica | Pasar los conjuntos literales a tuplas quita dos usos de la lista. Si se dejan, quedan en el inventario con su justificación (FR-386) |
| T047 | No | Usa la infraestructura de T005. La cripta de 1 000 salas se arma con `esqueleto_de_conexiones` a partir de una lista de conexiones |

---

## Fase 1: Preparación — el antes (M0, sin tocar código)

**Objetivo**: dejar registrado el antes oficial con el código de `0b031ec` antes de cualquier cambio.

- [X] T001 Comprobar que el código de producción, de medición y de pruebas es el de `0b031ec`: `git diff --stat 0b031ec -- adaptadores Logica DTO Controlador Servicio model main.py bench tests_labs` no muestra nada. Crear `specs/012-revision-parte-i/mediciones.md` con las secciones de [contracts/filas-medicion.md](contracts/filas-medicion.md): M0, M1 y M2 (cada una con sus tres ejecuciones), medición manual, pruebas y tabla por bloque. (FR-377)
- [X] T002 Ejecutar tres veces cada bloque: `python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M0-1.csv` y `python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M0-1.csv`, y lo mismo con `-2` y `-3`. Copiar en la sección M0 de `specs/012-revision-parte-i/mediciones.md`, para cada ejecución, la salida de consola, los comandos, la fecha y hora, el commit (`git rev-parse --short HEAD`) y el código de salida (debe ser 0). Cada fila de tiempo registra la mediana de las tres; las filas de cuenta deben salir iguales en las tres. (FR-377, FR-381, FR-383, FR-384)
- [X] T003 Ejecutar `python -m unittest discover -p "test_*.py"` y `python -m tests_labs.sin_red` con el mismo código y anotar en la sección «Pruebas» de `specs/012-revision-parte-i/mediciones.md` los totales (ejecutadas, fallos, errores y omitidas) de cada uno. Ese es el resultado que M2 tiene que repetir. (FR-387)
- [X] T004 Numerar las filas de M0 en las tablas de `specs/012-revision-parte-i/mediciones.md` según el catálogo de [contracts/filas-medicion.md](contracts/filas-medicion.md). Si la salida real difiere del catálogo, gana M0 y se ajusta el catálogo en `mediciones.md`. Marcar cada fila como «cuenta» o «tiempo» según la tabla de tipos de research D3. (FR-377, FR-379)

**Punto de control**: el antes está guardado. Ninguna tarea de código puede empezar antes de esto.

---

## Fase 2: Pruebas de equivalencia contra `0b031ec` (D4)

**Objetivo**: tener las referencias escritas en las pruebas y demostrar que reproducen el comportamiento vigente antes de tocarlo.

### Historia 1 — La vecindad se planea igual que hoy

- [ ] T005 [P] [US1] Crear `test_vecindad_equivalencia.py` en la raíz, solo con la infraestructura:
  - un cliente sintético (como `ClienteSintetico` de `adaptadores/bench_red_mejorado.py`) que cuenta las llamadas a `obtener_salas`;
  - una subclase espía de `ServicioCripta` que redefine `_buscar_esqueleto` para contar las llamadas y delegar en la original;
  - constructores de criptas con `tests_labs.cripta_sintetica.esqueleto_de_conexiones`: lineal, rejilla 3 × 3, árbol y con ciclos, con las convenciones de la spec, más una cripta con una puerta cerrada, una con una salida de un solo sentido, una sala sin salidas, una salida a la propia sala, dos salidas a la misma sala y una de 1 000 salas (`esqueleto_dirigido_aleatorio` con semilla fija);
  - la **función de referencia escrita en la prueba**: recorrido por niveles con una lista de pares y un índice de lectura, salidas en el orden N, S, E, O, sin estructuras de biblioteca. Devuelve la lista de salas y el número de búsquedas (1 + salas expandidas).

  (FR-370, FR-371, FR-374)
- [ ] T006 [US1] En `test_vecindad_equivalencia.py`, para cada cripta de T005, todas sus salas y las profundidades 0, 1, 2 y 5 (en la de 1 000 salas, 50 salas tomadas con la semilla), comprobar:
  - la lista de `salas_vecinas` es igual a la de la referencia;
  - las búsquedas contadas por el espía son iguales a las de la referencia;
  - después de la primera consulta por cripta, el cliente no recibe más llamadas a `obtener_salas`;
  - con profundidad 0, la respuesta es `[]` y hay 1 búsqueda.

  Cada caso cita sus FR en el docstring. (FR-370, FR-371, FR-372, FR-374)
- [ ] T007 [US1] En `test_vecindad_equivalencia.py`, comprobar los valores literales de la Historia 1 corregida:
  - lineal, sala 3: [4,2], [4,2,5,1] y [4,2,5,1,6]; lineal, sala 1, prof. 5: [2,3,4,5,6];
  - rejilla, sala 5: [2,8,6,4] y [2,8,6,4,3,1,9,7]; rejilla, sala 1, prof. 2: [4,2,7,5,3];
  - árbol, sala 1: [2,3] y [2,3,4,5,6]; árbol, sala 4, prof. 5: [2,1,5,3,6];
  - ciclos, sala 1: [3,2] y [3,2,4];
  - búsquedas en la rejilla desde la sala 5: 1, 2 y 6 con profundidad 0, 1 y 2.

  (FR-371, FR-374)
- [ ] T008 [US1] En `test_vecindad_equivalencia.py`, comprobar los errores:
  - profundidad −1 → `ValueError("La profundidad no puede ser negativa")` con 0 búsquedas, también con una sala inexistente (se comprueba primero la profundidad);
  - sala inexistente con profundidad 0, 1, 2 y 5 → `ValueError` que nombra la sala;
  - cripta inexistente → `ValueError` de la carga del esqueleto.

  (FR-373)

### Historia 2 — La vecindad cumple el principio I

- [ ] T009 [US2] En `test_vecindad_equivalencia.py`, una prueba que lee el código de `ServicioCripta.salas_vecinas` con `inspect.getsource` y comprueba que no aparece ninguno de `deque`, `collections`, `heapq`, `bisect`, `set(`, `dict(`, `sorted(` ni `.sort(`. Es la excepción: **falla contra `0b031ec`** y tiene que pasar después de T024. Se documenta en su docstring. (FR-375)

### Historia 5 — Caché de fichas equivalente

- [ ] T010 [P] [US5] Crear `test_cache_equivalencia.py` en la raíz:
  - una **LRU de referencia escrita en la prueba**, con listas y la semántica de [contracts/vecindad-y-cache.md](contracts/vecindad-y-cache.md) (en uso, rechazo si todo está en uso, expulsión de la menos reciente libre, `claves()` de más a menos reciente);
  - 20 semillas × 2 000 operaciones aleatorias (`obtener`, `insertar`, `marcar_en_uso`, `marcar_libre`, `establecer_en_uso`, `en_uso`) con capacidades 1, 2, 5 y 25, sobre un universo de claves mayor que la capacidad;
  - después de cada operación se comparan el valor devuelto, `claves()`, `len`, `aciertos` y `fallos`, y en cada inserción con la caché llena, qué clave salió.

  (FR-386, FR-387)
- [ ] T011 [US5] En `test_cache_equivalencia.py`, casos dirigidos:
  - `CacheLRU(0)` → `ValueError("La capacidad de la caché debe ser al menos 1")`;
  - todo en uso → `insertar` devuelve `False` y `len ≤ capacidad`;
  - reinsertar una clave existente reemplaza el valor, la pone primera en `claves()` y no expulsa nada;
  - se expulsa la menos reciente libre aunque haya más antiguas en uso;
  - `marcar_libre` no baja de 0;
  - `establecer_en_uso` cuenta las repeticiones.

  (FR-386, FR-387)
- [ ] T012 [US5] En `test_cache_equivalencia.py`, una prueba que usa `importaciones_prohibidas` de `test_monticulo_minimo.py` sobre `adaptadores/cache.py` y exige que no haya ninguna. Es la excepción: **falla contra `0b031ec`** y tiene que pasar después de T027. Se documenta en su docstring. (FR-386)

### Ejecución contra `0b031ec`

- [ ] T013 [US1] Ejecutar `python -m unittest test_vecindad_equivalencia -v` con el código sin tocar. Todo pasa salvo T009. Anotar el resultado en la sección «Pruebas» de `specs/012-revision-parte-i/mediciones.md`. Si falla otra cosa, se corrige la referencia de la prueba, nunca el código. (FR-370, FR-371, FR-372, FR-373, FR-374)
- [ ] T014 [US5] Ejecutar `python -m unittest test_cache_equivalencia -v` con el código sin tocar. Todo pasa salvo T012. Anotar el resultado en `specs/012-revision-parte-i/mediciones.md`. (FR-386, FR-387)

**Punto de control**: las referencias reproducen lo vigente.

---

## Fase 3: Código de medición con la carga nueva y M1 (sin tocar producción)

**Objetivo**: poner la carga nueva en las mismas filas (FR-378), agregar las filas nuevas de guardado y medir M1 con el código vigente.

### Historia 3 — Carga nueva en el bloque `cache`

- [ ] T015 [US3] En `adaptadores/bench_red_mejorado.py`, `ClienteSintetico`:
  - cada salida de `obtener_salas` lleva `"costo"` entre 1 y 9, sacado de `random.Random(SEMILLA)` (importar `SEMILLA` de `bench.datos`) y simétrico en las dos direcciones de cada conexión;
  - agregar `obtener_llaves(cripta_id, solo_guardadas=False, limite_solicitudes=None)`, que suma 1 a `llamadas` y devuelve una llave con la misma forma que `tests_labs/api_falsa.py` (parámetro `llaves`).

  (FR-378)
- [ ] T016 [US3] En `adaptadores/bench_red_mejorado.py`, `ClienteConCatalogo`:
  - agregar un cazador cada 10 salas (posiciones sacadas de `random.Random(SEMILLA)`), con un tipo propio en `obtener_contenido`;
  - `obtener_catalogo` devuelve para ese tipo una ficha con `"comportamiento": "cazador"` y `"rango"` (la de `tests_labs.cripta_sintetica.ficha_cazador`, `rango=600`);
  - en la sección 3, una de las fichas del catálogo pasa a ser de cazador.

  (FR-378)
- [ ] T017 [US3] En `adaptadores/bench_red_mejorado.py`, una función de medición `_mover_cazadores(servicio, cid, cazadores, sala_jugador)`:
  - cada cazador avanza una salida hacia la sala del jugador, por la menor cantidad de salidas, calculada con un recorrido por niveles sobre listas y con desempate en el orden N, S, E, O;
  - si entra en una sala cuyo contenido no está traído, llama a `servicio.construir_sala(cid, sala)` y suma las solicitudes que provocó;
  - los cazadores están activos desde el inicio (peor caso, research D3);
  - devuelve las solicitudes disparadas.

  Sin `dict` ni `set` como índice. (FR-378)
- [ ] T018 [US3] En `adaptadores/bench_red_mejorado.py`, `solicitudes_por_estrategia` (sección 1) y `cache_en_partida` (sección 6):
  - llamar a `servicio.ubicacion_llaves(cid)` una vez después de `crear_jugador`;
  - llamar a `_mover_cazadores` después de cada paso del jugador;
  - en la columna de unidad, agregar «de ellas, X disparadas por un cazador».

  El recorrido (pasillo de 60 y serpiente de 150 pasos) no cambia. (FR-378, FR-379)
- [ ] T019 [US3] En `adaptadores/bench_red_mejorado.py`, `busqueda_en_cache` (sección 2): un prototipo de **lista doblemente enlazada propia** (alternativa descartada de D2, que vive solo en el código de medición) y una fila «lista enlazada propia, N fichas, acierto (descartada)» por tamaño, después de las filas existentes de ese tamaño. No se cambia el nombre de ninguna fila existente. (FR-378: fila de alternativa descartada; principio VII, research D2)

### Historia 4 — Carga y filas nuevas en el bloque `guardado`

- [ ] T020 [P] [US4] En `bench/guardado.py`, `estado_con_salas`:
  - el segundo enemigo de cada sala pasa a ser cazador (`comportamiento="cazador"`, `rango=600`);
  - cada `SalidaGuardadaDTO` recibe `costo` entre 1 y 9 del mismo `rng`;
  - se asigna un `ConocimientoGuardadoDTO` con `exploradas` = salas impares en orden ascendente (la mitad) y `avistadas` = las pares.

  Las clases DTO se usan sin modificarlas. (FR-378, FR-381)
- [ ] T021 [US4] En `bench/guardado.py`:
  - una subclase de medición de `AlmacenPartidaBinario` que redefine `_abrir` (devuelve un envoltorio que suma los bytes de cada `read`) y `_entrada` (cuenta las llamadas);
  - por tamaño, filas nuevas: «bytes leídos al cargar UNA sala» de la primera, la del medio y la última (unidad: «bytes de N del archivo»), y «cargar UNA sala (la primera / la última) [binario, acceso directo]» con `medir`;
  - con `verificar`: los bytes leídos son menos que el tamaño del archivo, y las entradas leídas son a lo sumo ⌊log₂ n⌋ + 1.

  (FR-381, FR-382)

### M1

- [ ] T022 [US3] Comprobar que `git diff --stat 0b031ec -- adaptadores/servicioCripta.py adaptadores/cache.py` no muestra nada. Ejecutar tres veces cada bloque, con `--bench-csv specs/012-revision-parte-i/bench-cache-M1-1.csv` y `bench-guardado-M1-1.csv` (y lo mismo con `-2` y `-3`). Copiar, para cada ejecución, la salida, los comandos, la fecha, el commit y el código de salida (0) en la sección M1 de `specs/012-revision-parte-i/mediciones.md`; cada fila de tiempo registra la mediana de las tres. Completar la columna «Carga (M1)» y anotar «carga: …» en la causa de cada fila que difiera de M0 (por ejemplo, «+1 consulta de llaves», «X disparadas por un cazador»). (FR-377, FR-378, FR-379, FR-383, FR-384)
- [ ] T023 [US4] En `specs/012-revision-parte-i/mediciones.md`, marcar las filas nuevas de T019 y T021 con «sin antes en M0: fila nueva (FR-378)». Su antes es su medición con el código vigente y la carga nueva, es decir, M1 (la mediana en las filas de tiempo), y con ese antes se calcula el límite de 2×. (FR-377, FR-382, FR-384)

**Punto de control**: el efecto de la carga está aislado del efecto del código.

---

## Fase 4: D1 — vecindad sin cola de biblioteca

### Historias 1 y 2

- [ ] T047 [US2] En `test_vecindad_equivalencia.py`, antes de cambiar el código, una prueba de proporcionalidad cuyo docstring cita FR-376 y la Historia 2, escenario 2:
  - con profundidad 5, las búsquedas en el esqueleto que cuenta el espía son 1 más las salas expandidas (las de nivel menor que 5). En la rejilla 3 × 3 desde la sala 5 son 10;
  - una cripta de 1 000 salas contiene la misma rejilla en las salas 1 a 9, con las mismas salidas. Las salas 10 a 1 000 forman una fila y solo se conectan con la rejilla por una salida de un solo sentido de la sala 10 a la sala 1, así que desde la rejilla no se llega a ellas. La vecindad de la sala 5 con profundidad 5 y el número de búsquedas son los mismos que en la rejilla sola.

  Se ejecuta contra el código sin tocar y tiene que pasar. (FR-376)
- [ ] T024 [US1] [US2] En `adaptadores/servicioCripta.py`, reescribir **solo el cuerpo** de `salas_vecinas` según [data-model.md](data-model.md) («Consulta de vecindad»):
  - `if profundidad < 0: raise ValueError("La profundidad no puede ser negativa")` primero, y después `self._buscar_esqueleto(cripta_id, numero_sala)`;
  - `alcanzadas = [numero_sala]`, `lectura = 0`, `nivel = 0`, `fin_nivel = 1`;
  - mientras `lectura < len(alcanzadas)` y `nivel < profundidad`: expandir `alcanzadas[lectura]` (una llamada a `_buscar_esqueleto`, salidas en `_LETRAS_EN_ORDEN`, agregar los destinos que no están en `alcanzadas`) y avanzar `lectura`; cuando `lectura == fin_nivel`, `nivel += 1` y `fin_nivel = len(alcanzadas)`;
  - devolver `alcanzadas[1:]`.

  No quitar `from collections import deque` (lo usa `_armar_salidas`, uso justificado) y no tocar `precargar_vecinas`. (FR-370, FR-371, FR-372, FR-373, FR-374, FR-375, FR-376)
- [ ] T025 [US1] Ejecutar `python -m unittest test_vecindad_equivalencia -v`: todo pasa, **incluidas T009 y T047**. (FR-370, FR-371, FR-372, FR-373, FR-374, FR-375, FR-376)
- [ ] T026 [US2] Ejecutar `python main.py --bench cache` una vez y comprobar en la sección 5 que `salas_vecinas` a 1 y 2 pasos no supera 2 × su valor de M1. Es un control preliminar contra M1; el límite final de FR-383 se comprueba en T033 contra M0, con la mediana de las tres ejecuciones de M2. (FR-376, FR-383)

---

## Fase 5: D2 — caché sin cola de biblioteca

### Historia 5

- [ ] T027 [US5] En `adaptadores/cache.py`, reescribir `CacheLRU` sobre una lista propia ordenada de **menos a más reciente** (la más reciente al final), según [data-model.md](data-model.md) («Entrada de la caché»):
  - quitar `from collections import deque`;
  - un acierto o una reinserción sacan la entrada de su posición y la agregan al final;
  - `_desalojar` recorre desde el inicio y quita la primera con `veces_en_uso == 0`;
  - `claves()` recorre desde el final;
  - la búsqueda va del final al inicio;
  - se conservan la interfaz, los mensajes de error y los docstrings; el de la clase se actualiza.

  (FR-386, FR-387)
- [ ] T028 [US5] Ejecutar `python -m unittest test_cache_equivalencia -v`: todo pasa, **incluida T012**. (FR-386, FR-387)
- [ ] T029 [US5] En `adaptadores/bench_red_mejorado.py`, cambiar el nombre de las filas de la sección 2 de «deque lineal» a «lista propia lineal», sin cambiar su posición ni su escenario, y actualizar el docstring del módulo. (FR-379)
- [ ] T030 [US5] Con D1 y D2 hechos (T025 y T028), ejecutar `python -m unittest discover -p "test_*.py"` y `python -m tests_labs.sin_red`. `discover` da los totales de T003 más las pruebas de `test_vecindad_equivalencia.py` y `test_cache_equivalencia.py`, con 0 fallos y 0 errores; `sin_red` da los mismos totales que en T003. Ninguna prueba que pasaba en T003 falla ahora. (FR-387)

---

## Fase 6: el después (M2, tres ejecuciones) y los límites

### Historia 3

- [ ] T031 [US3] Ejecutar tres veces cada bloque, con `--bench-csv specs/012-revision-parte-i/bench-cache-M2-1.csv` y `bench-guardado-M2-1.csv` (y lo mismo con `-2` y `-3`). Copiar, para cada ejecución, la salida, los comandos, la fecha, el commit (más «árbol con cambios») y el código de salida (0) en la sección M2 de `specs/012-revision-parte-i/mediciones.md`; cada fila de tiempo registra la mediana de las tres. (FR-377, FR-378, FR-383, FR-384)
- [ ] T032 [US3] Comprobar en `mediciones.md`:
  - las filas de cuenta son idénticas en las tres ejecuciones de M2;
  - las secciones 1 y 6 del bloque `cache` son iguales en M1 y M2.

  Si algo difiere, se investiga antes de seguir. (FR-379, FR-387)
- [ ] T033 [US3] Completar en `specs/012-revision-parte-i/mediciones.md`, para cada fila: «Después (M2)» (la mediana en las filas de tiempo), la diferencia absoluta y en %, el límite (2 × M0, o 2 × M1 en las filas nuevas), «Cumple» y la causa («código: …», «depende de la máquina» o «sin cambios»). (FR-379, FR-383, FR-384)
- [ ] T034 [US5] **Solo si** en T033 una fila «lista propia lineal» de la sección 2 sigue pasando 2 × su antes: aplicar el criterio de cambio de D2 (pasar `adaptadores/cache.py` a la lista enlazada propia del prototipo de T019), repetir T028, T030 y T031 a T033, y anotarlo como cambio respecto del plan. Si no hace falta, marcar la tarea con «no aplica» y la fila que lo demuestra. (FR-383, FR-386, FR-387)

### Historia 4

- [ ] T035 [US4] En `specs/012-revision-parte-i/mediciones.md`, registrar para 10, 100 y 1 000 salas los bytes leídos (primera, del medio y última), el tamaño del archivo y las entradas leídas frente a ⌊log₂ n⌋ + 1, y confirmar que las verificaciones de T021 dieron «ok» y que la lectura de una sala tarda menos que la carga completa. Comparar además entre 10, 100 y 1 000 salas el tiempo de leer la primera, la del medio y la última sala, y confirmar que no crece con el número de salas más allá de la variación entre las tres ejecuciones (Historia 4, escenario 3). (FR-382, FR-384)
- [ ] T036 [US4] Medición manual:
  1. Revisar qué criptas de `datos_cripta/` tienen esqueleto, contenido y catálogo, y elegir la más grande.
  2. Sin red (`--offline`, o armando el estado con `FuenteSoloLocal`), generar y guardar una partida de formato 8 en una carpeta temporal.
  3. Medirla con la subclase contadora de T021 (tamaño, bytes, entradas y tiempo de la primera, la del medio y la última sala, y la carga completa) y comprobar 0 solicitudes.
  4. Anotar el resultado en la sección «Medición manual» de `specs/012-revision-parte-i/mediciones.md`.

  Si ninguna cripta está completa, anotarlo así y no descargar nada. (FR-382)

---

## Fase 7: inventario y documentación

### Historia 5 — Inventario

- [ ] T037 [US5] Repetir la búsqueda de la sección «Inventario» de [quickstart.md](quickstart.md) sobre `adaptadores Controlador DTO Logica model Servicio main.py`, excluyendo `bench_red.py` y `bench_red_mejorado.py`, y pegar la salida en un anexo de `specs/012-revision-parte-i/mediciones.md`. `adaptadores/cache.py` ya no aparece. `adaptadores/servicioCripta.py` aparece solo por `_armar_salidas`. (FR-385, FR-375)
- [ ] T038 [US5] Revisar a mano cada aparición de `dict(`, `= {}` o `: dict` (18 en `0b031ec`) y de los conjuntos literales. Clasificar cada una como «índice, caché o tabla de búsqueda» o como «lectura de JSON» (respuesta de la API o copia con su misma forma), con una línea de motivo, en el anexo de `mediciones.md`. Toda aparición que sea índice o caché pasa a la tabla del inventario con el criterio de FR-386. Las apariciones que la búsqueda de conjuntos literales encuentra en marcadores de f-string (`{x}` dentro de una cadena con prefijo `f`) se descartan con el criterio «marcador de f-string no cuenta», que se escribe en el anexo junto con cuántas líneas descartó. (FR-385, FR-386)
- [ ] T039 [US5] Para los usos 9 y 10 de research D5 (`adaptadores/extension.py:20` y `Logica/EstadoJuegoLogica.py:884, 900, 1248`), decidir si se justifican tal cual o se pasan a tuplas. Si se pasan a tuplas, cambiar solo esas líneas y repetir T030. Anotar la decisión. (FR-386, FR-387)

### Historias 3, 4 y 5 — Documento de Decisiones

- [ ] T040 [US5] En `DECISIONES.md`, crear la sección «## 012 · Revisión de la Parte I con la carga nueva» con enlaces a `specs/012-revision-parte-i/spec.md`, `plan.md` y `mediciones.md`, y la subsección «Inventario de usos prohibidos». Esta lleva:
  - el criterio de exclusión (pruebas, código de medición y scripts auxiliares, por la función del archivo);
  - una tabla «Ubicación | Estructura | Para qué | ¿Problema evaluado de §5? | Destino | Texto», con los usos de research D5 y los de T038;
  - las justificaciones de los usos 3 a 6, 9 y 10 (qué hacen, por qué no son índice ni caché y qué costaría corregirlos).

  (FR-385, FR-386, FR-388)
- [ ] T041 [US3] En `DECISIONES.md` §012, una tabla «Decisión | ¿Coincide con el plan? | Medición o motivo» con:
  - D1 (vecindad), con el motivo por el que no se reutiliza `ColaCircular` (research D1): guardaría una copia de lo que ya está en la lista de salas alcanzadas y, como solo guarda enteros, haría falta una segunda cola o codificar sala y nivel en un entero con una cota de salas;
  - D2 (caché, con el resultado de T034);
  - la capacidad de la caché (sección 6, aciertos y fallos por capacidad);
  - la precarga (solo sus filas; la regla no cambia por FR-324);
  - el catálogo en disco (filas 17 a 22);
  - el formato binario de partida.

  Cada fila cita al menos una fila del después y dice si la decisión se mantiene o cambia. (FR-375, FR-380, FR-388)
- [ ] T042 [US3] [US4] En `DECISIONES.md` §012, las tablas de antes y después de los dos bloques (copiadas de `mediciones.md`), el resultado de la medición manual (T036) y una subsección «Hallazgos y límites» con:
  - el orden N, S, E, O y la corrección de la spec (H1);
  - el crecimiento logarítmico de los bytes leídos (H2);
  - el commit de referencia (H3);
  - la aproximación del movimiento de los cazadores en el bloque `cache`.

  (FR-377, FR-382, FR-388)
- [ ] T043 [P] [US3] En `DOCUMENTACION_DECISIONES_DISENO.md`, agregar una nota de una o dos líneas con el veredicto y un enlace a `DECISIONES.md` §012 en:
  - «## 2. Caché de fichas y almacenamiento en disco» (caché, catálogo y precarga);
  - «## 6. Guardado binario de la partida»;
  - «## 8. El mundo: salas, vecindad, mensajes recientes y puntajes» (vecindad).

  Sin borrar la evidencia original. Si alguna decisión cambia, actualizar también su fila en «## 10. Resumen de las decisiones». (FR-388)

---

## Fase 8: cierre

- [ ] T044 [P] En `tests_labs/sin_red.py`, agregar `"test_vecindad_equivalencia"` y `"test_cache_equivalencia"` a `PRUEBAS` y actualizar el docstring para que nombre la capacidad 012. (FR-387)
- [ ] T045 Cierre:
  - ejecutar `python -m unittest discover -p "test_*.py"`, `python -m tests_labs.sin_red`, `python main.py --bench cache` y `python main.py --bench guardado`, todos con código de salida 0;
  - anotar los totales y los códigos en la sección «Pruebas» de `specs/012-revision-parte-i/mediciones.md`;
  - confirmar que ninguna tarea tocó `DTO/SalaDTO.py`, `DTO/EstadoGuardadoDTO.py`, `Logica/EstadoGuardadoLogica.py`, `adaptadores/AlmacenPartidaBinario.py` ni `codec_partida` (`git diff --stat 0b031ec --` sobre esos archivos no muestra nada).

  Depende de T044. (FR-377, FR-383, FR-384, FR-387)
- [ ] T046 En `specs/012-revision-parte-i/spec.md`, cambiar `**Estado**: Borrador` por `**Estado**: Implementada (T001 a T047)`. Depende de T045. (FR-370 a FR-388, cierre)

---

## Dependencias y orden de ejecución

```text
T001 → T002 → T003 → T004                       (M0: antes de cualquier cambio)
  └─► T005 ─► T006, T007, T008, T009 ─► T013     (vecindad contra 0b031ec)
  └─► T010 ─► T011, T012 ─────────────► T014     (caché contra 0b031ec)
T013, T014 ─► T015 ─► T016 ─► T017 ─► T018 ─► T019 ┐
              T020 ─► T021 ─────────────────────────┴► T022 ─► T023   (M1)
T023 ─► T047 ─► T024 ─► T025 ─► T026            (D1; T047 se ejecuta antes de cambiar el código)
T023 ─► T027 ─► T028 ─► T029 ─► T030             (D2; puede ir en paralelo con D1, otro archivo)
T025 ─► T030                                     (T030 espera también a D1)
T026, T030 ─► T031 ─► T032 ─► T033 ─► T034 (condicional) ─► T035 ─► T036
T036 ─► T037 ─► T038 ─► T039 ─► T040 ─► T041 ─► T042 ─► T043
T043, T044 ─► T045 ─► T046
```

- **Por historia**: US1 (T005–T008, T013, T024, T025) y US2 (T009, T047, T024, T026) dependen de M0 y de M1. US5 (T010–T012, T014, T027–T030, T034, T037–T040) depende de M0 y de M1 para D2. US3 y US4 (T015–T023, T031–T036, T041–T043) dependen de que D1 y D2 estén hechos para M2.
- **Bloqueo duro**: ninguna tarea de las fases 4 y 5 puede empezar antes de T022 (M1), porque M1 tiene que medir el código de producción sin tocar.

## Oportunidades de paralelismo

- **Fase 2**: T005 (`test_vecindad_equivalencia.py`) y T010 (`test_cache_equivalencia.py`) son archivos distintos.
- **Fase 3**: T020 y T021 (`bench/guardado.py`) en paralelo con T015 a T019 (`adaptadores/bench_red_mejorado.py`).
- **Fases 4 y 5**: D1 (T047 y T024 a T026, `test_vecindad_equivalencia.py` y `servicioCripta.py`) y D2 (T027 y T028, `cache.py`) tocan archivos distintos. T029 espera a T027, y T030 a ambas.
- **Fase 7 y 8**: T043 (`DOCUMENTACION_DECISIONES_DISENO.md`) y T044 (`tests_labs/sin_red.py`).

```text
# Ejemplo, fase 2:
T005 [US1] test_vecindad_equivalencia.py   |   T010 [US5] test_cache_equivalencia.py
# Ejemplo, fase 3:
T015..T019 [US3] adaptadores/bench_red_mejorado.py   |   T020..T021 [US4] bench/guardado.py
```

## Estrategia de implementación

- **MVP**: fases 1 a 4. Con el antes medido, las pruebas de equivalencia y D1 se cierra el incumplimiento conocido de §6.2 en la planeación de la vecindad (US1 y US2) con su prueba de equivalencia.
- **Incremento 2**: fase 5 (D2, US5 código).
- **Incremento 3**: fase 6 (M2 y límites, US3 y US4).
- **Incremento 4**: fases 7 y 8 (inventario y documentación, cierre).
- Cada incremento deja la suite completa en verde, salvo T009 y T012, que fallan a propósito hasta que se hacen D1 y D2.

## Criterios de prueba independientes por historia

| Historia | Cómo se prueba sola |
|---|---|
| US1 | `python -m unittest test_vecindad_equivalencia`: equivalencia con la referencia en salas, orden, errores, búsquedas y descargas |
| US2 | T009 pasa (código fuente del método sin nada de la lista) + T047 (búsquedas proporcionales a las salas alcanzadas) + sección 5 del bloque `cache` |
| US3 | `mediciones.md` con M0, M1 y M2 (tres ejecuciones cada una, mediana en las filas de tiempo), cada fila con causa y límite; `DECISIONES.md` §012 con un veredicto por decisión |
| US4 | Filas de bytes y entradas leídas del bloque `guardado` y medición manual |
| US5 | `python -m unittest test_cache_equivalencia` + búsqueda del inventario sin apariciones fuera de la tabla |

## Trazabilidad requisito → tareas

| Requisito | Tareas |
|---|---|
| FR-370 | T005, T006, T013, T024, T025 |
| FR-371 | T005, T006, T007, T013, T024, T025 |
| FR-372 | T006, T013, T024, T025 |
| FR-373 | T008, T013, T024, T025 |
| FR-374 | T005, T006, T007, T013, T024, T025 |
| FR-375 | T009, T024, T025, T037, T041 |
| FR-376 | T024, T025, T026, T047 |
| FR-377 | T001, T002, T004, T022, T023, T031, T042, T045 |
| FR-378 | T015, T016, T017, T018, T019, T020, T022, T031 |
| FR-379 | T004, T018, T022, T029, T032, T033 |
| FR-380 | T041 |
| FR-381 | T002, T020, T021 |
| FR-382 | T021, T023, T035, T036, T042 |
| FR-383 | T002, T022, T026, T031, T033, T034, T045 |
| FR-384 | T002, T022, T023, T031, T033, T035, T045 |
| FR-385 | T037, T038, T040 |
| FR-386 | T010, T011, T012, T014, T027, T028, T034, T038, T039, T040 |
| FR-387 | T003, T010, T011, T014, T027, T028, T030, T032, T034, T039, T044, T045 |
| FR-388 | T040, T041, T042, T043 |

Los 19 requisitos (FR-370 a FR-388) tienen al menos una tarea, y todas las tareas citan al menos un requisito. T046 los cierra todos.
