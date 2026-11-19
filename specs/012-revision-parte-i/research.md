# Investigación (fase 0): Revisión de la Parte I con la carga nueva

**Capacidad**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Fecha**: 2026-11-17

Cada decisión indica qué se decidió, por qué, qué alternativas se consideraron, la complejidad esperada y cómo se mide. Las cifras de «antes» que se citan son de la 009 (`DECISIONES.md`, bloque `cache`, T050). Sirven solo como orientación: el antes oficial de esta capacidad es la medición M0 (D3).

---

## Hallazgos previos que condicionan el plan

**H1 · El orden vigente de las salidas es N, S, E, O, no N, E, S, O.** `adaptadores/servicioCripta.py:31` define `_LETRAS_EN_ORDEN = ("N", "S", "E", "O")`, y `tests_labs/prueba_vecinas_reporte.py:68` lo confirma («orden N, S, E, O»). FR-371 y los escenarios 4 a 8 de la Historia 1 de la spec suponen N, E, S, O, lo que contradice FR-370 («exactamente las mismas salas que la versión vigente»). El plan conserva el orden vigente, porque es lo que pide FR-370 y lo que mantiene comparables las mediciones. Hay que corregir la spec antes de `/speckit-tasks` (principio X). Los valores correctos, calculados con la regla vigente, son:

| Escenario | Spec actual | Con el orden vigente (N, S, E, O) |
|---|---|---|
| Lineal, sala 3 (prof. 1 / 2 / 5) | [4,2] / [4,2,5,1] / [4,2,5,1,6] | **sin cambios** (solo hay E y O) |
| Lineal, sala 1, prof. 5 | [2,3,4,5,6] | sin cambios |
| Rejilla, sala 5, prof. 1 | [2,6,8,4] | **[2,8,6,4]** |
| Rejilla, sala 5, prof. 2 y 5 | [2,6,8,4,3,1,9,7] | **[2,8,6,4,3,1,9,7]** |
| Rejilla, sala 1, prof. 2 | [2,4,3,5,7] | **[4,2,7,5,3]** |
| Árbol, sala 1, prof. 1 | [3,2] | **[2,3]** |
| Árbol, sala 1, prof. 2 y 5 | [3,2,6,4,5] | **[2,3,4,5,6]** |
| Árbol, sala 4, prof. 5 | [2,1,5,3,6] | sin cambios |
| Ciclos, sala 1, prof. 1 | [2,3] | **[3,2]** |
| Ciclos, sala 1, prof. 2 y 5 | [2,3,4] | **[3,2,4]** |

Las cuentas de búsquedas del escenario 12 (1, 2 y 6 en la rejilla desde la sala 5) no dependen del orden y siguen valiendo.

**H2 · La lectura de una sala hace búsqueda binaria en la tabla de entradas.** `AlmacenPartidaBinario.leer_sala` lee el pie, ⌈log₂ n⌉ entradas como máximo y la sala. Los bytes leídos crecen con log n, no son constantes. El escenario 1 de la Historia 4 («no dependen de cuántas salas tiene la partida») debería decir «crecen como mucho con el logaritmo del número de salas y son mucho menos que el archivo». El plan mide los bytes reales y no toca esa clase (restricción del pedido).

**H3 · Commit de referencia.** El pedido fija el «antes» en `0b031ec`, y el supuesto de la spec nombra `1f009a1`. Entre los dos solo cambiaron `spec.md` y la lista de control (`git diff --stat 1f009a1 0b031ec`), así que el código de producción es el mismo. El plan usa `0b031ec`, y conviene actualizar el supuesto de la spec junto con la corrección de H1.

---

## D1 · Planeación de la vecindad sin cola de biblioteca (FR-370 a FR-376)

**Hoy**: recorrido por niveles con una cola de biblioteca de pares `(sala, nivel)` y una lista `alcanzadas` en la que se comprueba linealmente si una sala ya está (`destino not in alcanzadas`).

**Alternativas**:

| | Idea | Estructura extra | Costo por consulta (k = salas alcanzadas, N = salas de la cripta) |
|---|---|---|---|
| (a) | Usar la propia lista `alcanzadas` como cola: un índice de lectura avanza sobre ella y una marca de fin de nivel (`fin_nivel = len(alcanzadas)` al cerrar cada nivel) da el nivel sin guardarlo | ninguna | k búsquedas en el esqueleto (O(N) cada una, igual que hoy), 4k comprobaciones de pertenencia O(k), avance O(1) |
| (b) | `ColaCircular` de `Logica` (solo enteros), con el nivel deducido contando: al empezar cada nivel se anota cuántos elementos tiene la cola y se sacan exactamente esos | 1 cola propia, más la lista `alcanzadas` que la respuesta necesita igual | igual que (a), más copiar cada sala dos veces (lista y cola) y crecer la cola por duplicación |
| (c) | Marcas de pertenencia por id (una lista de tamaño N, o marcas con época por cripta, como `BuscadorRutas`) | lista de N o estado por cripta | pertenencia O(1), pero crear la lista cuesta O(N) por consulta (rompe FR-376) y la época exige estado persistente e invalidación por cripta |

**Elección: (a).** En un recorrido por niveles la cola contiene, en todo momento, exactamente un tramo final de la lista de salas alcanzadas, en el mismo orden. Esa lista ya existe y ya define el orden de la respuesta, así que leerla con un índice es la cola sin duplicar datos. El nivel se deduce con la marca de fin de nivel: al cruzarla, el nivel sube en 1.

**Por qué no (b)** (FR-375 pide reutilizar una estructura propia si es adecuada o decir por qué no): `ColaCircular` es adecuada y sería una alternativa válida: el nivel se puede deducir contando los elementos de la cola al empezar cada nivel, sin segunda cola ni codificación (corrección 2026-11-18: la versión anterior de este párrafo decía que haría falta una segunda cola o una codificación `sala × base + nivel`, y eso no es cierto). Pero aquí sobra: la lista `alcanzadas` hace falta de todos modos, porque define el orden de la respuesta y sirve para saber si una sala ya se alcanzó, así que la cola guardaría una copia de las mismas salas y agregaría una estructura sin quitar ningún recorrido. Leer `alcanzadas` con un índice da lo mismo sin duplicar datos. Si se prefiriera reutilizar la `ColaCircular` por coherencia con el reparto, el cambio sería local a `salas_vecinas` y las mismas pruebas de equivalencia lo comprueban. **Por qué no (c)**: cambia el costo de la consulta de O(k²) a O(N) en la parte que FR-376 obliga a que no dependa de N, o agrega estado entre consultas que habría que invalidar (principio III).

**Equivalencia con lo vigente (FR-370 a FR-374)**:
- **Orden.** Se procesan las salas en el orden en que se descubrieron, y en cada una las salidas en `_LETRAS_EN_ORDEN`, la misma secuencia que la cola de biblioteca. La respuesta es `alcanzadas[1:]`.
- **Errores y orden de comprobación.** Primero `profundidad < 0` (sin leer el esqueleto) y después la validación con `_buscar_esqueleto` de la sala de partida, igual que hoy.
- **Búsquedas en el esqueleto.** Hoy se llama a `_buscar_esqueleto` una vez para validar y otra por cada sala sacada de la cola con `nivel < profundidad`. En (a), el bucle termina cuando el nivel llega a la profundidad, así que expande exactamente las salas de nivel menor que la profundidad: el mismo conjunto, en el mismo orden. Con profundidad 0 no se expande ninguna (1 búsqueda en total).
- **Descargas.** No cambia `_cargar_esqueleto` (descarga una vez por cripta).

**Complejidad**: tiempo O(k · N) por las búsquedas lineales en el esqueleto, que no cambian (FR-376 las deja fuera), más O(k²) de pertenencia, como hoy. Memoria O(k), con menos objetos que hoy porque no hay tuplas `(sala, nivel)`.

**Medición**: bloque `cache`, sección 5 (`salas_vecinas`, 1 y 2 pasos en 1 000 salas), con antes y después. Equivalencia con la prueba D4-a. No se agrega una fila con (b): la decisión no depende de su tiempo, porque (b) hace el mismo trabajo más una copia.

---

## D2 · Caché de fichas sin cola de biblioteca (FR-386, FR-387)

**Hoy** (`adaptadores/cache.py`): cola de biblioteca de entradas `[clave, valor, veces_en_uso]` con la más reciente al frente.
- La búsqueda es lineal desde el frente.
- Un acierto o una reinserción quitan la entrada de en medio (`remove`) y la ponen al frente (`appendleft`).
- Desalojar recorre desde el fondo (`reversed`) y quita la primera entrada que no está en uso.
- `claves()` devuelve de la más reciente a la menos reciente.

`ColaCircular` no sirve: guarda enteros, y no saca de en medio ni inserta al frente.

**Comportamiento observable que hay que conservar**: lo que devuelven `obtener` e `insertar` (incluido el `False` cuando todo está en uso), los contadores `aciertos` y `fallos`, el orden de `claves()`, qué clave se expulsa y cuándo, `en_uso`, `establecer_en_uso`, `marcar_en_uso`, `marcar_libre`, `len` y `capacidad`.

**Alternativas** (n = entradas, a lo sumo la capacidad):

| | Idea | Acierto | Inserción nueva | Expulsión | Notas |
|---|---|---|---|---|---|
| (a) | Lista propia con la **más reciente al final**: buscar desde el final hacia el inicio, `del` en la posición y `append` | O(n) búsqueda + O(n) corrimiento (un corrimiento en bloque, en C) | O(1) amortizado | recorrer desde el inicio hasta la primera libre, O(n) | `claves()` recorre al revés. Es la más simple, y el movimiento a la cabeza es O(1) amortizado |
| (b) | Lista propia con la **más reciente al inicio** (`insert(0, …)`) | O(n) + O(n) | O(n) corrimiento | recorrer desde el final, O(n) | el mismo orden de memoria que hoy, pero insertar al frente siempre corre todo |
| (c) | Lista doblemente enlazada propia (nodos con anterior y siguiente) | O(n) búsqueda + O(1) reenlace | O(1) | desde la cola hasta la primera libre, O(n) | sin un índice por clave (prohibido usar dict, y la tabla hash propia ya se descartó en la Parte I) la búsqueda sigue siendo lineal, así que el O(1) del reenlace no cambia el orden total. Es más código y hay un objeto por entrada |
| (d) | Tabla hash propia más lista enlazada (LRU clásico O(1)) | O(1) esperado | O(1) | O(1) amortizado | ya se midió como alternativa descartada (sección 2, «tabla hash propia») con el criterio de la Parte I: la caché tiene 25 fichas y la búsqueda lineal cuesta ~1 µs frente a ~400 ms de una solicitud |

**Elección: (a).** Tiene el mismo orden de complejidad que hoy, en todas las operaciones: la búsqueda O(n) domina, y `remove` en la cola de biblioteca ya era O(n). Insertar es O(1) amortizado, igual que `appendleft`, y no necesita estructura nueva ni código de enlaces. El orden lógico (de más a menos reciente) es el mismo; solo se guarda invertido en memoria, y `claves()` y `_desalojar` lo leen en el sentido que corresponde.

**Criterio de cambio, fijado antes de medir**: si en la medición M2 alguna fila de tiempo de la sección 2 de (a) supera el doble de su antes (FR-383), se prueba (c) con las mismas pruebas de equivalencia. Si (c) cumple, se adopta y se documenta como cambio respecto del plan (FR-388). (b) solo sirve como referencia.

**Alternativa descartada medida (principio VII)**: la sección 2 conserva la fila «tabla hash propia (descartada)» y agrega una fila «lista enlazada propia (descartada)» por tamaño (25, 100, 1 000 y 5 000), con un prototipo que vive solo en el código de medición. Son filas sin antes comparable (FR-377).

**Complejidad**: `obtener` O(n), `insertar` O(n) (búsqueda más expulsión), `claves` O(n), `establecer_en_uso` O(n·m), igual que hoy. Memoria O(n).

**Medición**: bloque `cache`.
- Sección 2: las filas «deque lineal» pasan a llamarse «lista propia lineal», con la misma posición y el mismo escenario. El cambio de nombre se anota en la columna de causa.
- Sección 6: aciertos, fallos y solicitudes por capacidad son filas de cuenta y deben salir idénticas (FR-387). La carga nueva puede moverlas entre M0 y M1, pero no entre M1 y M2 (ver D3).

---

## D3 · Mediciones: antes, carga nueva y después (FR-377 a FR-384)

**Tres pasos**, para poder atribuir cada diferencia (FR-378 pide decir si viene del código o de la carga). Cada paso son tres ejecuciones de cada bloque, y el valor de cada fila de tiempo es la mediana de las tres (FR-383, FR-384):

| Id | Código de producción | Código de medición | Para qué |
|---|---|---|---|
| **M0** | `0b031ec`, sin tocar | `0b031ec`, sin tocar | **Primer paso del plan, antes de cualquier cambio.** Es el «antes» oficial de cada fila (FR-377) |
| **M1** | `0b031ec`, sin tocar | con la carga nueva y las filas nuevas de guardado | separa el efecto de la carga del efecto del código. Da el antes de las filas que no existen en M0 |
| **M2** | revisado (D1 y D2) | el mismo que M1 | el «después» oficial (FR-378). Sus tres ejecuciones comprueban además que las filas de cuenta salen idénticas (FR-379) |

**Atribución de la causa** en cada fila: M0 → M1 es la carga; M1 → M2 es el código. Las filas de tiempo llevan además «depende de la máquina». La tabla de `mediciones.md` y de `DECISIONES.md` muestra M0 (antes) y M2 (después). M1 aparece como columna auxiliar.

**Comandos** (los mismos en M0, M1 y M2, tres veces cada uno; solo cambia el nombre del CSV):

```
python main.py --bench cache    --bench-csv specs/012-revision-parte-i/bench-cache-M0-1.csv
python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M0-1.csv
# se repiten con -2 y -3
```

La salida de la consola se copia en `mediciones.md` con el comando, la fecha y el commit (`git rev-parse --short HEAD`, más «árbol con cambios» si los hay).

**Cómo entra la carga nueva en las mismas filas (FR-378)**: el escenario de cada fila no cambia (mismo pasillo de 60 salas, misma serpiente de 150 pasos, mismos tamaños). Solo se le agrega la carga.

- **Bloque `cache`, secciones 1 y 6** (las que juegan un recorrido):
  - **Costos de salida**: el cliente sintético declara un `costo` en cada salida, entre 1 y 9, sacado de un generador con semilla fija (`bench.datos.SEMILLA`).
  - **Consulta de llaves**: el cliente sintético responde a `obtener_llaves` con una llave, y cada recorrido llama a `servicio.ubicacion_llaves(cid)` una vez al empezar, como hace `iniciarJuego`. Se espera +1 solicitud por fila de la sección 1 y por capacidad de la sección 6.
  - **Cazadores que se mueven**: el contenido sintético agrega un cazador (ficha con comportamiento cazador y `rango`) cada 10 salas, en salas fijadas por la semilla. Después de cada paso del jugador, el código de medición mueve cada cazador una salida hacia el jugador, por la menor cantidad de salidas y con desempate en el orden N, S, E, O. Si entra en una sala cuyo contenido no está traído, llama a `construir_sala`, la misma carga que provoca un enemigo en el juego a través de `ingresarEnSala`. Las solicitudes que provoca se cuentan aparte, en la columna de unidad («de ellas, X disparadas por un cazador»).
  - **Límite declarado**: este movimiento es una aproximación del motor de eventos, porque el bloque llama al servicio directamente y no al juego. El efecto con el juego real ya se midió en `--bench llaves` A (009): 0.2 solicitudes disparadas de promedio. Aquí se busca el peor caso para la red: cazadores activos desde el inicio.
- **Bloque `cache`, secciones 2 a 5**: miden una operación aislada (buscar en la caché, leer una ficha, guardar un lote, planear la vecindad) que la carga no cambia. Las fichas de la sección 3 y el esqueleto de la sección 5 llevan costos y una ficha de cazador para que el contenido sea el de la Parte II. La causa esperada de la diferencia es «código» o «depende de la máquina».
- **Bloque `guardado`**: la partida sintética de `estado_con_salas` ya es de formato 8 en M0, porque la escribe el código vigente. La carga agrega:
  - uno de los dos enemigos de cada sala pasa a ser cazador con `rango`;
  - las salidas llevan `costo` sacado de la semilla;
  - el conocimiento del jugador cubre la mitad de las salas (exploradas o avistadas).

**Filas nuevas del bloque `guardado`** (exigidas por FR-381 y FR-382; no son filas de carga, así que no contradicen FR-378): por tamaño, «bytes leídos al cargar UNA sala» (primera, del medio y última) y «tiempo de cargar UNA sala» para la primera y la última (la del medio ya existe).
- Los bytes se cuentan con una subclase de medición de `AlmacenPartidaBinario` que redefine `_abrir` para devolver un archivo que suma los bytes de cada `read`. La clase de producción no se toca.
- Estas filas no existen en M0. Su antes es M1, marcado «sin antes en M0: fila nueva (FR-381, FR-382)».

**Cripta del tamaño de la referencia (§6.1)**: la cripta de referencia todavía no se publicó, y la mayor publicada tiene 300 salas (dato de la 006). Se toma la fila de **1 000 salas** como la del tamaño de referencia, más de 3 veces la mayor publicada, igual que la 006 usó 400 y 2 000. La semilla es `bench.datos.azar(n)`, la que ya usa el bloque.

**Medición manual (FR-382, segunda viñeta)**: se busca en `datos_cripta/` la cripta publicada más grande que tenga esqueleto, contenido y catálogo (la 003 encontró que cripta-06, con 300 salas, no tiene contenido).
- Con esa cripta se juega en `--offline` hasta guardar, o se arma el estado desde su esqueleto con `FuenteSoloLocal`, sin solicitudes.
- Se mide con la misma subclase contadora y se anota en `mediciones.md` y en la sección 012 de `DECISIONES.md`.
- Si ninguna está completa, se registra así y no se descarga nada.

**Tipos de fila**:

| Tipo | Filas | Regla |
|---|---|---|
| **Cuenta** (deben ser idénticas entre dos ejecuciones con la misma semilla) | `cache` 1 (solicitudes), `cache` 6 (aciertos, fallos y solicitudes), `guardado` tamaño en bytes (binario y JSON), `guardado` bytes leídos, filas de verificación | iguales en las tres ejecuciones de cada paso. Cambiar el código no las mueve: M1 = M2 (FR-387) |
| **Tiempo** (dependen de la máquina) | `cache` 2, 3, 4 y 5; `guardado` guardar, cargar y leer una sala (binario y JSON) | el valor de cada fila es la mediana de tres ejecuciones (FR-383, FR-384). Después ≤ 2 × antes en red (FR-383) y en guardado (FR-384); si la mediana pasa el límite, cuenta como regresión |

**Límites**: FR-383 se compara contra M0 (antes oficial). Para las filas nuevas, y para las filas de red que la carga nueva ya llevó a más del doble de M0 (con la causa escrita), contra M1. FR-384 vale para guardar, cargar y leer una sala del binario, en los tres tamaños.

---

## D4 · Pruebas (FR-370 a FR-374, FR-387)

**a) `test_vecindad_equivalencia.py`** (en la raíz, como las demás pruebas):
- **Criptas**: las cuatro de la spec (lineal, rejilla, árbol y con ciclos, armadas con `tests_labs.cripta_sintetica.esqueleto_de_conexiones`), una con una puerta cerrada, una con una salida de un solo sentido y una sintética de 1 000 salas (`esqueleto_dirigido_aleatorio` con semilla fija).
- **Versión de referencia escrita en la prueba**: recorrido por niveles con dos listas (cola por índice y lista de pares), sin estructuras de biblioteca, usando el mismo orden de letras que el servicio.
- **Espías**:
  - una subclase de `ServicioCripta` que redefine `_buscar_esqueleto` para contar llamadas y delegar;
  - un cliente sintético que cuenta las llamadas a `obtener_salas`.
- **Comprobaciones**, para todas las salas y las profundidades 0, 1, 2 y 5:
  - salas y orden iguales a los de la referencia (FR-370, FR-371);
  - vacío con profundidad 0 (FR-372);
  - el mismo número de búsquedas que la referencia, que cuenta 1 más 1 por sala expandida (FR-374);
  - 0 descargas después de la primera (FR-374);
  - con profundidad negativa, `ValueError` sin búsquedas; con sala inexistente, `ValueError` (FR-373).
- Valores literales de los escenarios de la spec (FR-371), una vez corregidos según H1.
- Proporcionalidad (FR-376, Historia 2, escenario 2): con profundidad 5, las búsquedas son 1 más las salas expandidas, y no cambian al rodear la misma vecindad con una cripta de 1 000 salas.
- Búsqueda de importaciones prohibidas en el código de `salas_vecinas` (FR-375): se lee el código fuente del método con `inspect.getsource` y se buscan los nombres prohibidos.
- **Antes de cambiar el código, la prueba se ejecuta contra `0b031ec` y debe pasar**, salvo la búsqueda de nombres prohibidos (T009), que falla a propósito hasta D1. Así se demuestra que la referencia reproduce lo vigente.

**b) `test_cache_equivalencia.py`**:
- **Referencia escrita en la prueba**: una LRU de listas, con la misma semántica (en uso, rechazo si todo está en uso, orden).
- **Secuencias aleatorias con semilla fija**: 20 semillas × 2 000 operaciones (`obtener`, `insertar`, `marcar_en_uso`, `marcar_libre`, `establecer_en_uso`, `en_uso`) sobre capacidades 1, 2, 5 y 25.
- **Después de cada operación** se comparan los valores devueltos, `claves()`, `len`, `aciertos` y `fallos`. Cuando se expulsa, también qué clave se fue (FR-386, FR-387).
- **Casos dirigidos**: todo en uso (devuelve `False` y no supera la capacidad), reinserción de una clave existente y expulsión de la menos reciente que esté libre.
- También pasa contra `0b031ec` antes del cambio, salvo la búsqueda de importaciones prohibidas en `cache.py` (T012), que falla a propósito hasta D2.

**c) Pruebas existentes**: se ejecuta la suite completa (`python -m unittest discover -p "test_*.py"`) en M0 y en M2. En M2 debe dar los totales de M0 más las pruebas de los dos archivos nuevos, con 0 fallos y 0 errores (FR-387).

Cada clase o caso de prueba cita su FR-3xx en la descripción.

---

## D5 · Inventario y documentación (FR-385, FR-386, FR-388)

**Alcance del código de producción**: `adaptadores/`, `Controlador/`, `DTO/`, `Logica/`, `model/`, `Servicio/` y `main.py`.

**Criterio de exclusión** (se escribe tal cual en `DECISIONES.md`):
- las pruebas (`test_*.py`, `tests_labs/`, `Pruebas.py`);
- el código de medición (`bench/` y `adaptadores/bench_red*.py`, que viven en `adaptadores/` pero solo se ejecutan con `--bench` o a mano);
- los scripts auxiliares (`descargar_cripta.py`).

El criterio es la función del archivo, no la carpeta.

**Método**:
1. **Búsqueda mecánica** con los patrones de [quickstart.md](quickstart.md#inventario): importaciones de `heapq`, `bisect`, `collections` y `networkx`; `sorted(` y `.sort(`; `set(`, `frozenset` y literales de conjunto; `dict(`, `{}` y asignaciones por clave.
2. **Revisión manual** de cada aparición. Un dict cuenta como uso prohibido si se usa como índice, caché o tabla de búsqueda. No cuenta si solo es la respuesta JSON o una copia con la misma forma (supuesto de la spec).
3. **Tabla**: ubicación (archivo:línea), estructura, para qué sirve, si resuelve un problema evaluado de §5, y destino (corregido o justificado) con su texto.

**Inventario preliminar** (búsqueda del 2026-11-17 sobre `0b031ec`):

| # | Ubicación | Uso | ¿Problema evaluado de §5? | Destino |
|---|---|---|---|---|
| 1 | `adaptadores/servicioCripta.py` `salas_vecinas` | cola de biblioteca del recorrido por niveles | sí (planeación de la vecindad) | **corregir** (D1) |
| 2 | `adaptadores/cache.py` | cola de biblioteca de la LRU | sí (caché de fichas) | **corregir** (D2) |
| 3 | `DTO/SalaDTO.py:33` | contenedor de salidas de la sala, `maxlen=4` | no | **justificar** (no se toca, por la restricción del pedido) |
| 4 | `adaptadores/servicioCripta.py` `_armar_salidas` | arma ese contenedor desde la respuesta de la API | no | **justificar** |
| 5 | `Logica/EstadoGuardadoLogica.py:285` | reconstruye ese contenedor al cargar una partida | no | **justificar** (no se toca) |
| 6 | `Logica/GestorEventos.py:2` | `collections.abc.Callable`, solo como anotación de tipo | no: no es una estructura | **justificar** (es una anotación; no guarda datos) |
| 7 | `adaptadores/servicioCripta.py` `normalizar_esqueleto` | `dict(sala)` y `salidas_nuevas = {}` por letra: copia con la forma del JSON de la API | no: lectura de JSON | revisado y **excluido** por el supuesto del JSON. Se anota en la tabla con ese motivo |
| 8 | `adaptadores/resolucion.py:41,72` | `dict(ficha)`: copia de la ficha JSON para construir el objeto | no: lectura de JSON | revisado y **excluido** (igual que el 7) |
| 9 | `adaptadores/extension.py:20` | conjunto literal de 3 separadores de ruta, para comprobar pertenencia | no | **justificar**: es una constante de 3 elementos, no un índice de datos del juego. Pasarla a una tupla costaría una línea; se decide en la tarea del inventario |
| 10 | `Logica/EstadoJuegoLogica.py:884, 900, 1248` | conjuntos literales de 2 tipos de acción, para comprobar pertenencia | no | **justificar** con el mismo motivo que el 9 (o pasar a tupla, sin cambio observable) |
| — | 18 apariciones de `dict(`, `= {}` o `: dict` | por revisar a mano en el inventario final | — | cada una se clasifica como uso de índice o caché (y entonces va a la tabla con su destino) o como lectura de JSON (excluida, con el motivo) |

Después de D1, `servicioCripta.py` sigue importando la cola de biblioteca por el uso 4, que se justifica. La comprobación de FR-375 es por método, no por archivo.

**Texto de las justificaciones 3 a 5** (FR-386): guardan como máximo 4 salidas, que se recorren en orden. Nadie busca por clave en ellas ni las usa como caché, así que no son un índice. Corregirlas significaría cambiar el tipo en el DTO, en la conversión desde la API y en la carga de partida, más las pruebas de formato: es un cambio mecánico, pero toca el formato y su reconstrucción, que esta capacidad deja fuera de alcance.

**Documentación**:
- **`DECISIONES.md`**, sección «012 · Revisión de la Parte I con la carga nueva», con el formato de las demás:
  - enlaces a la spec, al plan y a `mediciones.md`;
  - una tabla «Decisión | ¿Coincide con el plan? | Medición o motivo» con D1, D2, la precarga (solo filas, FR-324), el catálogo en disco y el formato binario;
  - las tablas de antes y después de los dos bloques;
  - el inventario;
  - «Hallazgos y límites», con H1, H2 y la aproximación de los cazadores.
- **`DOCUMENTACION_DECISIONES_DISENO.md`**: una nota de una o dos líneas con el veredicto (se mantiene o cambia) y un enlace a la sección 012, en tres secciones:
  - «2. Caché de fichas y almacenamiento en disco» (caché, catálogo en disco y precarga);
  - «6. Guardado binario de la partida»;
  - «8. El mundo: salas, vecindad, mensajes recientes y puntajes» (planeación de la vecindad).

  La evidencia original no se borra. Si una nota dice «cambia», también se actualiza la fila correspondiente de «10. Resumen de las decisiones».
