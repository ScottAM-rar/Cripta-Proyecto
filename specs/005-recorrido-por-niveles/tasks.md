# Tareas: Recorrido por niveles de la cripta

**Entrada**: documentos de diseño en `specs/005-recorrido-por-niveles/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerrequisitos**: `plan.md` y `spec.md` (con las 2 clarificaciones de la sesión 2026-10-27, el requisito FR-513 y SC-004 por conteo). Esta capacidad se apoya en código de la capacidad 001 que ya está en el repositorio: `Logica/MapaCripta.py`, `Logica/MonticuloMinimo.py` y `tests_labs/cripta_sintetica.py`.

**Pruebas**: se incluyen en todas las historias porque la constitución (principio IX) exige que cada escenario de aceptación tenga una prueba automatizada. Cada prueba se escribe **antes** del código y debe fallar primero.

**Organización**: tareas agrupadas por historia de usuario. Cada tarea indica entre paréntesis los requisitos que atiende.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencia de tareas incompletas).
- **[USn]**: historia de `spec.md` a la que pertenece.
- Las rutas son relativas a la raíz del repositorio. Las pruebas usan `unittest` (archivos `test_*.py` en la raíz).

## Reglas para todas las tareas (constitución)

- **No usar** `dict` ni `set` como índice, caché o tabla de búsqueda; ni `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` ni bibliotecas de grafos. Se permite `list`, `struct`, `json`, `requests`. Tampoco `list.sort()` ni `sorted()` para ordenar lo que se evalúa: se usa `ordenar_adaptativo`.
- Ningún id de sala o entidad, cantidad de páginas, presupuesto ni estadística de una cripta concreta en el código de producción.
- El modelo (`Logica/`, `DTO/`) no importa red, disco ni vista.
- No se modifican `adaptadores/servicioCripta.py` (`salas_vecinas`, `precargar_vecinas`) ni la verificación de resolubilidad: en esta capacidad el recorrido solo se construye y se mide.
- Los commits de especificación y plan van **antes** y **separados** de los de código (principio X).

---

## Fase 1: Preparación

**Propósito**: material de pruebas y revisión de la constitución. Bloquea todo lo demás.

- [X] T001 Revisar `plan.md` y este `tasks.md` contra la lista de prohibidos del principio I (constitución) y anotar el resultado en `specs/005-recorrido-por-niveles/checklists/requirements.md` (sección Notas). Comprobar en particular que ninguna alternativa del bench (`pop(0)`, índice de cabeza, dos listas, montículo) necesita `deque` ni `collections`. (I)
- [X] T002 [P] Ampliar `tests_labs/cripta_sintetica.py` con tres piezas deterministas por semilla: (a) `esqueleto_arbol(ramificacion, niveles)` (ids desde 1 en orden de niveles; la raíz con `ramificacion` hijos; cada sala con a lo sumo 4 salidas, así que la ramificación máxima es 3; con 3 y 9 niveles son 29 524 salas); (b) `esqueleto_dirigido_aleatorio(total, semilla, fraccion_un_sentido, fraccion_inexistentes)` (conexiones aleatorias que incluyen ciclos, caminos paralelos, dos salidas distintas hacia la misma sala, una salida de una sala a sí misma, conexiones de un solo sentido y, según `fraccion_inexistentes`, salidas hacia ids que no existen en el esqueleto; a lo sumo 4 salidas por sala; ids desde 1); (c) `mapa_desde_esqueleto(esqueleto)`, que arma un `MapaCripta` a partir de un esqueleto crudo por el mismo camino que usa el juego (`ServicioCripta.obtener_mapa` sobre `HttpConfigurable`, como hace `bench/terreno.py`) y que usarán T008, T009, T014, T015 y T018. (FR-503, FR-506, FR-511, FR-513)
- [X] T003 [P] Crear `tests_labs/referencia_recorrido.py` con un recorrido de **referencia ingenua** para comparar: sobre el esqueleto crudo (lista de salas con `salidas`), usa solo listas, `pop(0)`, búsqueda con `in` y un ordenamiento simple escrito dentro del propio archivo; no importa `Logica.RecorridoPorNiveles` ni `Logica.ordenamiento`. Devuelve `(salas, niveles)`, acepta límite y un criterio de transitabilidad que es una función del **par `(origen, destino)`** (ids de sala), no de la arista ni de la letra de dirección; ignora las salidas hacia ids que no existen en el esqueleto. Solo se usa en pruebas. (FR-501 a FR-508, FR-513)

**Punto de control**: material de pruebas listo y revisión de la constitución anotada.

---

## Fase 2: Fundamentos (bloquea todas las historias)

**Propósito**: la cola, el resultado y la lista de existencia del mapa. Sin esto el recorrido no se puede escribir.

- [X] T004 [P] Crear `test_cola_circular.py` con pruebas de `Logica/ColaCircular.py`: orden FIFO; mezclar `agregar` y `sacar` hasta dar varias vueltas al almacén; crecimiento al llenarse conserva el orden (con "capacidad inicial 16", agregar 100 elementos seguidos y comprobar que salen en el mismo orden); `vacia()`, `vaciar()` y longitud; `sacar()` en una cola vacía lanza `IndexError`; el archivo del módulo no importa `heapq`, `bisect`, `collections` ni `networkx`. (I, FR-510)
- [X] T005 [P] Crear `DTO/RecorridoDTO.py` con `salas` (lista de enteros: ids de sala en el orden de visita, el primero es el origen, "sin repetidos") y `niveles` (lista de enteros del mismo largo; `niveles[i]` es el nivel de `salas[i]`; "no decrece; dentro de un mismo nivel `salas` crece estrictamente"). Sin lógica. (FR-501, FR-502, FR-503)
- [X] T006 [P] Agregar a `MapaCripta` en `Logica/MapaCripta.py` el campo `existe` ("lista de booleanos, tamaño `tamano`"; `existe[i]` es verdadero si el esqueleto tiene una sala con id `i`), armado junto con las aristas. No cambiar nada de lo que ya hace; las pruebas de la capacidad 001 deben seguir pasando. (FR-512)
- [X] T007 Crear `Logica/ColaCircular.py` según `data-model.md`: cola de enteros sobre una `list` de capacidad fija, "capacidad inicial pequeña (16); no depende de ninguna cripta", índice de cabeza y tamaño, y al llenarse la capacidad se duplica copiando los elementos en orden desde la cabeza. Operaciones: `agregar(valor)`, `sacar()` ("falla con `IndexError` si está vacía"), `vacia()`, `vaciar()`, longitud. Sin `deque` ni `collections`. Debe hacer pasar `test_cola_circular.py`. (I, FR-510)

**Punto de control**: `python -m unittest test_cola_circular` pasa y la suite de la capacidad 001 sigue pasando.

---

## Fase 3: Historia 1 — Recorrer la cripta en orden de cercanía (P1) 🎯 MVP

**Meta**: dado un origen, se obtiene la secuencia de salas alcanzables por nivel, con menor id dentro de cada nivel, sin repetidos y sin salas inalcanzables, respetando las salidas de un solo sentido y el criterio de transitabilidad.

**Prueba independiente**: criptas pequeñas armadas a mano (línea, ciclo, caminos paralelos, un solo sentido) comparadas con la secuencia escrita a mano; criptas aleatorias comparadas con la referencia ingenua.

### Pruebas de la Historia 1 (escribir primero; deben fallar)

- [X] T008 [US1] Crear `test_recorrido_por_niveles.py` con los escenarios de la Historia 1, armando los mapas con `mapa_desde_esqueleto` (T002) y con **los resultados esperados escritos a mano** como listas literales en la prueba (ni calculados con la referencia ni con el propio recorrido): línea de 5 salas en orden de cercanía (FR-501); dos vecinas al mismo nivel con las salidas declaradas en orden contrario al de sus ids, y el ejemplo de `research.md` §4 (origen 1 con salidas a 5 y 3; la 3 lleva a la 9 y la 5 a la 4; resultado esperado `1, 3, 5, 4, 9` con niveles `0, 1, 1, 2, 2`) (FR-502); ciclo sin repetidos, dos caminos hacia la misma sala en el nivel más cercano, dos salidas hacia la misma sala, salida de una sala a sí misma y origen dentro de un ciclo (FR-503); origen sin salidas (FR-508); salas sin camino desde el origen (FR-505); salida de un solo sentido (FR-506); criterio de transitabilidad, definido sobre el par `(origen, destino)` y adaptado a la arista con `lambda arista: criterio(arista.origen, arista.destino)`, que excluye una salida y sus salas exclusivas, y sin criterio valen todas (FR-507); origen inexistente lanza `ValueError` (FR-512); una salida hacia una sala que no existe se ignora, esa sala no aparece y el resto del recorrido no cambia (FR-513); `MapaCripta.existe` correcto para ids con y sin sala. Cada prueba cita su FR en el nombre. (FR-501 a FR-508, FR-512, FR-513)
- [X] T009 [US1] Agregar a `test_recorrido_por_niveles.py` la prueba de equivalencia: sobre 200 criptas de `esqueleto_dirigido_aleatorio` (semillas fijas, tamaños de 1 a 300 salas, con salidas hacia ids inexistentes; cada una con un origen y un criterio de transitabilidad derivados de la semilla, definido como función del par `(origen, destino)` y usado tal cual en la referencia y, adaptado con `lambda arista: criterio(arista.origen, arista.destino)`, en el recorrido), el recorrido coincide en `salas` y `niveles` con `tests_labs/referencia_recorrido.py`; además se comprueban las invariantes de `RecorridoDTO` (ids crecientes dentro de cada nivel, sin repetidos, `salas[0]` es el origen con nivel 0). (FR-501, FR-502, FR-503, FR-505, FR-506, FR-507, FR-513)

### Implementación de la Historia 1

- [X] T010 [US1] Crear `Logica/RecorridoPorNiveles.py` con la clase `RecorridoPorNiveles(mapa)` y `recorrer(origen, limite=None, transitable=None) -> RecorridoDTO` según `data-model.md` y `contracts/interfaz-recorrido.md`: dos listas `_marca` y `_nivel` de tamaño `mapa.tamano`, época que sube en cada llamada, `ColaCircular` con el nivel en curso, y una lista auxiliar para el nivel siguiente que se ordena con `ordenar_adaptativo` antes de encolarse. Validar `origen`: "ha de existir en el esqueleto"; si no, `ValueError` (FR-512). Ignorar las salidas hacia ids fuera de `mapa.tamano` o sin sala (`existe` falso): esa sala no aparece en el recorrido y el recorrido no se rechaza por ello (FR-513). `transitable`: "función que recibe una arista y devuelve verdadero o falso", o ausente (todas son transitables), evaluada una vez por arista examinada. Si `recorrer` falla a mitad, vaciar la cola antes de propagar el error. Mientras no exista T012, si `limite` no es `None` lanzar `NotImplementedError`. (FR-501, FR-502, FR-503, FR-505, FR-506, FR-507, FR-508, FR-512, FR-513)
- [X] T011 [US1] Ejecutar `python -m unittest test_recorrido_por_niveles test_cola_circular` y `python -m unittest discover -p "test_*.py"`; corregir fallos del recorrido sin tocar las pruebas de la capacidad 001. (FR-501 a FR-508, FR-512, FR-513)

**Punto de control**: la Historia 1 pasa por sí sola; el recorrido coincide con la referencia en 200 criptas aleatorias.

---

## Fase 4: Historia 2 — Limitar hasta dónde se recorre (P1)

**Meta**: un límite de niveles corta el recorrido sin examinar más allá.

**Prueba independiente**: recorrer una línea larga con límites distintos y comprobar dónde se corta.

### Pruebas de la Historia 2 (escribir primero; deben fallar)

- [X] T012 [US2] Agregar a `test_recorrido_por_niveles.py`: límite de 2 niveles no incluye las salas a 3 saltos o más; límite 0 deja solo el origen; límite mayor que la distancia a la sala más lejana da lo mismo que sin límite (FR-504); límite inválido ("entero mayor o igual que 0, o ausente"): `-1`, `1.5`, `True` y `"2"` lanzan `ValueError` que nombra el valor recibido; la equivalencia con la referencia incluye ahora un límite aleatorio (de 0 a 8 o ausente). (FR-504)

### Implementación de la Historia 2

- [X] T013 [US2] En `Logica/RecorridoPorNiveles.py` implementar `limite`: validar ("entero mayor o igual que 0, o ausente"; un booleano, un negativo o un no entero se rechazan con `ValueError`), quitar el `NotImplementedError` de T010 y **no examinar las salidas** de las salas cuyo nivel es igual al límite, para que el costo sea proporcional a lo visitado. (FR-504, FR-510)

**Punto de control**: las Historias 1 y 2 pasan; el límite 0 solo toca el origen.

---

## Fase 5: Historia 3 — Resultados repetibles y de costo proporcional (P2)

**Meta**: dos ejecuciones iguales dan la misma secuencia, el trabajo depende de lo visitado y no de N, y `--bench` lo mide con la alternativa descartada.

**Prueba independiente**: repetir el mismo recorrido y comparar; contar el trabajo en criptas de distinto tamaño; ejecutar `--bench recorrido`.

### Pruebas de la Historia 3 (escribir primero; deben fallar)

- [X] T014 [P] [US3] Crear `test_recorrido_determinismo.py`: el mismo recorrido repetido 100 veces sobre la misma cripta da 100 veces la misma secuencia, también reutilizando el mismo `RecorridoPorNiveles` (las marcas de época no filtran nada entre llamadas) y alternando con recorridos de otros orígenes; el resultado no cambia si el mapa se construye con las salas del esqueleto en otro orden de llegada. (FR-509)
- [X] T015 [P] [US3] Crear `test_recorrido_proporcional.py`: con contadores `salas_visitadas` y `salidas_examinadas` del último recorrido, un recorrido de 2 niveles desde el centro de una rejilla visita y examina **exactamente lo mismo** en una cripta de 400, de 4 900 y de 40 000 salas, y esos contadores son proporcionales a lo visitado (a lo sumo 4 salidas examinadas por sala visitada). Es una prueba de conteo, no de tiempo, para que sea estable, y es el **criterio verificable de SC-004**; arma las tres criptas con `mapa_desde_esqueleto` (T002). (FR-510)

### Implementación de la Historia 3

- [X] T016 [US3] Agregar a `RecorridoPorNiveles` los contadores `salas_visitadas` y `salidas_examinadas` (del último recorrido), sin cambiar el resultado. Debe hacer pasar T014 y T015. (FR-509, FR-510)
- [X] T017 [US3] Crear `bench/recorrido.py` con las **alternativas descartadas** del bloque, que existen solo aquí y reciben el mismo mapa, origen y límite que el recorrido real: cola con `list` y `pop(0)`; cola con `list` e índice de cabeza que solo avanza; dos listas por nivel intercambiadas (sin cola); y recorrido con `MonticuloMinimo` de clave `(nivel, id)`. Todas devuelven `(salas, niveles)`. Ninguna usa `deque` ni `collections`. (FR-511, VII)
- [X] T018 [US3] En `bench/recorrido.py` implementar las secciones de `contracts/bench-recorrido.md`, armando los mapas con `mapa_desde_esqueleto` (T002): A (límites 2 y 5 y sin límite en rejillas de 400, 4 900 y 40 000 salas, origen central; informa las salas visitadas y las salidas examinadas de cada caso; el **criterio duro es de conteo** (SC-004): con límite 2 las tres criptas visitan las mismas salas y examinan las mismas salidas; la **razón de tiempos** 40 000 / 400 se informa como medición, sin umbral); B (cola circular frente a `pop(0)`, índice de cabeza y dos listas, con verificación previa de que todas dan el mismo recorrido); C (B repetida en rejilla y en `esqueleto_arbol(3, 9)`); D (`ordenar_adaptativo` por nivel frente al montículo `(nivel, id)`); E (recorrido nuevo frente a `ServicioCripta.salas_vecinas` sobre la misma cripta, **solo informativa**: no se compara la secuencia, porque `salas_vecinas` ordena por letra de dirección y no incluye el origen; se informa el tiempo de cada una y cuántas salas alcanza; no interviene en el código de salida; sin modificar esa función); F (recorrido frente a `tests_labs/referencia_recorrido.py` en criptas aleatorias, 0 diferencias). Usar `bench/medicion.py`, la semilla de `bench/datos.py` y criptas sintéticas deterministas. (FR-510, FR-511, VII)
- [X] T019 [US3] Registrar el bloque `recorrido` en `bench/__init__.py` (incluido en `--bench` sin argumentos) y hacer que el código de salida sea distinto de 0 si falla la verificación previa de B, si F tiene diferencias o si falla el **criterio de conteo de SC-004** en A (las tres criptas no visitan las mismas salas o no examinan las mismas salidas). La razón de tiempos de A y toda la sección E solo informan: nunca cambian el código de salida. (FR-510, FR-511)
- [X] T020 [US3] Ejecutar `python main.py --bench recorrido`, guardar la salida completa en `specs/005-recorrido-por-niveles/mediciones.md` junto con una tabla de decisiones («elegida frente a descartada, qué se midió, conclusión»), comprobar el criterio de conteo de SC-004 y registrar la razón de tiempos como medición informativa. (FR-510, VII)
- [X] T021 [US3] **Revisar las decisiones con lo medido.** Si B, C o D muestran que una alternativa (dos listas por nivel, índice de cabeza o montículo) gana con claridad a la elegida, cambiar `Logica/RecorridoPorNiveles.py` y documentar el antes y el después en `mediciones.md` y en `DECISIONES.md`. Si el conteo de SC-004 falla, es un defecto del recorrido: corregir el código; si solo la razón de tiempos sale alta, no es un fallo (es informativa): documentarla en `mediciones.md`. Si nada cambia, anotarlo: «las decisiones se mantienen». (VII, X)

**Punto de control**: determinismo y proporcionalidad comprobados; las decisiones respaldadas o corregidas con mediciones.

---

## Fase 6: Cierre y transversales

- [X] T022 [P] Completar la matriz de trazabilidad de `specs/005-recorrido-por-niveles/quickstart.md` con los nombres reales de pruebas; comprobar con un recorrido automático de las pruebas que ningún FR-501 a FR-512 queda sin cubrir. (IX)
- [X] T023 [P] Agregar la sección 005 a `DECISIONES.md` con enlaces a `spec.md` y `plan.md`, indicando si cada decisión final coincide con el plan original y, si no, qué medición motivó el cambio. (X)
- [X] T024 [P] Registrar en `PROMPTS_LLM.md` cada comando `/speckit` con texto propio de esta capacidad (`specify`, `clarify`, `plan`, `tasks`, `implement`), con herramienta y modelo. (XI)
- [X] T025 [P] Actualizar `README.md` con `python main.py --bench recorrido` y una línea sobre la capacidad 005. (VII)
- [X] T026 Comprobar con búsqueda que el código nuevo (`Logica/ColaCircular.py`, `Logica/RecorridoPorNiveles.py`, `DTO/RecorridoDTO.py`) no importa `heapq`, `bisect`, `collections` ni `networkx`, no usa `dict`/`set` como índice ni `sorted()`/`list.sort()`, y no contiene ids ni tamaños de una cripta concreta. Las alternativas descartadas existen solo en `bench/recorrido.py`. (I, V)
- [X] T027 Ejecutar todas las pruebas (`python -m unittest discover -p "test_*.py"`) y `python main.py --bench`; comparar los laboratorios de `tests_labs/` con la línea base; registrar cualquier fallo sin ocultarlo. (IX)
- [X] T028 Comparar `spec.md` con el programa entregado y corregir cualquier desajuste primero en la especificación, en commit aparte del código. (X)

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1** primero. T002 y T003 son paralelas entre sí.
- **Fase 2** depende de la Fase 1 y bloquea las historias. T004, T005 y T006 son paralelas; T007 depende de T004 (la prueba va antes).
- **Fase 3 (US1)** depende de la Fase 2. Es el MVP.
- **Fase 4 (US2)** depende de la Fase 3: amplía `RecorridoPorNiveles.py` y `test_recorrido_por_niveles.py`.
- **Fase 5 (US3)** depende de la Fase 4 (mide el recorrido completo). Solo las **pruebas** T014 y T015 pueden adelantarse (escribirse y verlas fallar) tras T011; T016 a T021 esperan a que termine la Fase 4.
- **Fase 6** al final.

### Dentro de cada historia

- Pruebas primero, que deben fallar; luego código.
- Las tareas que tocan el mismo archivo no son paralelas: `test_recorrido_por_niveles.py` (T008, T009, T012), `Logica/RecorridoPorNiveles.py` (T010, T013, T016, T021), `bench/recorrido.py` (T017, T018), `tests_labs/cripta_sintetica.py` (T002).

### Oportunidades de paralelismo

- Fase 1: T002 y T003.
- Fase 2: T004, T005 y T006.
- Historia 3: T014 y T015.
- Fase 6: T022, T023, T024 y T025.

## Estrategia de implementación

1. **MVP**: Fases 1 a 3. Entrega un recorrido por niveles correcto, comparado con una referencia ingenua, sin límite de niveles.
2. Añadir la Historia 2 (límite) y comprobarla con las mismas pruebas.
3. Añadir la Historia 3: determinismo, proporcionalidad y el bloque `recorrido` del bench. **Las decisiones de estructuras (cola circular, orden por nivel) se confirman o se cambian con T021**, no antes.
4. Cerrar con la Fase 6.
5. En cada punto de control, confirmar por separado los cambios de especificación y plan (antes) y de código (después).

## Cobertura de requisitos

| Requisito | Tareas |
|---|---|
| FR-501 | T003, T005, T008, T009, T010 |
| FR-502 | T005, T008, T009, T010 |
| FR-503 | T002, T005, T008, T009, T010 |
| FR-504 | T012, T013 |
| FR-505 | T003, T008, T009, T010 |
| FR-506 | T002, T008, T009, T010 |
| FR-507 | T008, T009, T010 |
| FR-508 | T003, T008, T010 |
| FR-509 | T014, T016 |
| FR-510 | T007, T013, T015, T016, T018, T019, T020 |
| FR-511 | T002, T017, T018, T019 |
| FR-512 | T006, T008, T010 |
| FR-513 | T002, T003, T008, T009, T010 |
