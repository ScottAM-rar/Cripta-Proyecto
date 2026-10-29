# Tareas: Terreno y cazador

**Entrada**: documentos de diseño en `specs/001-terreno-y-cazador/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerrequisitos**: `plan.md` y `spec.md` (con las 3 clarificaciones de la sesión 2026-10-27).

**Pruebas**: se incluyen en todas las historias porque la constitución (principio IX) exige que cada escenario de aceptación tenga una prueba automatizada o un `partida.log` que cite su requisito. Cada prueba se escribe **antes** del código y debe fallar primero.

**Organización**: tareas agrupadas por historia de usuario para implementarlas y probarlas por separado. Cada tarea indica entre paréntesis los requisitos que atiende.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencia de tareas incompletas).
- **[USn]**: historia de `spec.md` a la que pertenece.
- Las rutas son relativas a la raíz del repositorio. Las pruebas siguen la convención del repositorio (`unittest`, archivos `test_*.py` en la raíz).

## Reglas para todas las tareas (constitución)

- **No usar** `dict` ni `set` como índice, caché o tabla de búsqueda; ni `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` ni bibliotecas de grafos. Se permite `list`, `struct`, `json`, `requests`. No agregar usos nuevos de `deque`.
- Ningún id de sala o entidad, cantidad de páginas, presupuesto ni estadística de una cripta concreta en el código.
- El modelo (`Logica/`, `DTO/`) no importa red, disco ni vista.
- Los commits de especificación van **antes** y **separados** de los de código (principio X).

---

## Fase 1: Preparación y especificación

**Propósito**: cerrar los huecos de especificación detectados al planificar y dejar listo el material de pruebas. Esta fase bloquea todo lo demás.

- [X] T001 Revisar `plan.md` y este `tasks.md` contra la lista de prohibidos del principio I (constitución) y anotar el resultado en `specs/001-terreno-y-cazador/checklists/requirements.md` (sección Notas). (I)
- [X] T002 Resolver con `/speckit-clarify` los dos pendientes de `plan.md` (costos distintos en los dos lados de una conexión; conexiones de un solo sentido) y escribir la respuesta en `specs/001-terreno-y-cazador/spec.md` como requisito y escenario. Confirmar en un commit **solo de especificación**. (FR-102, X)
- [X] T003 Agregar en `specs/001-terreno-y-cazador/spec.md` los escenarios de aceptación que faltan: puerta que se cierra durante el cruce (FR-109); costo y rango inválidos con advertencia (FR-101, FR-108); versiones y caché (FR-118, FR-119); compatibilidad de salidas sin costo (FR-107). Actualizar la matriz de `quickstart.md`. Mismo commit de especificación que T002. (FR-107, FR-108, FR-109, FR-118, FR-119, IX, X)
- [X] T004 [P] Extender la API falsa `tests_labs/api_falsa.py` para que el esqueleto admita `costo` por salida y el catálogo admita fichas con `comportamiento` `cazador` y `rango`, de forma configurable por prueba. (FR-118)
- [X] T005 [P] Crear `tests_labs/cripta_sintetica.py` con un generador de criptas deterministas por semilla (cantidad de salas, costos, puertas, cazadores) para pruebas y para `--bench`. Sin ids ni tamaños fijos. (V, VII)

**Punto de control**: la especificación está confirmada sin marcadores pendientes y existe material de pruebas.

---

## Fase 2: Fundamentos (bloquea todas las historias)

**Propósito**: campos de datos y lectura de esqueleto y catálogo. Sin esto ninguna historia puede probarse.

- [X] T006 [P] Agregar a `SalidaDTO` en `DTO/SalaDTO.py` el campo `costo` ("entero ≥ 1", por defecto 100). No ampliar el uso de `deque`. (FR-101)
- [X] T007 [P] Agregar el campo `rango` ("entero ≥ 0", por defecto 0) a `EnemigoCatalogoDTO` en `DTO/CatalogoDTO.py` y a `EnemigoDTO` en `DTO/ActorDTO.py`. (FR-108)
- [X] T008 [P] Agregar a `ResultadoEventoDTO` en `DTO/ResultadoEventoDTO.py` el campo `costo` ("entero ≥ 1 o ausente"; ausente = no aplica). (FR-103)
- [X] T009 [P] Crear `DTO/AccionEnemigoDTO.py` con `mensaje` (texto) y `costo` (entero ≥ 1; 100 si esperó, atacó o no se movió). (FR-107)
- [X] T010 Leer `costo` de cada salida en `ServicioCripta._armar_salidas` de `adaptadores/servicioCripta.py`: ausente = 100; "cero, negativo, no entero o booleano" = 100 con una advertencia que nombra sala, dirección y valor. Acumular las advertencias en una lista expuesta por el servicio. (FR-101, FR-118)
- [X] T011 Copiar `rango` de la ficha en `resolver_enemigo` de `adaptadores/resolucion.py`: "ausente o inválido (negativo o no entero)" = 0 con advertencia; 0 declarado es válido. (FR-108, FR-118)
- [X] T012 Reconocer `"cazador"` como comportamiento válido en `Logica/ComportamientoFactory.py` (la clase se crea en T032; aquí solo dejar el caso preparado sin romper los demás). (FR-108)

**Punto de control**: los datos de costo y rango entran al modelo; el resto de la Parte I sigue pasando sus pruebas.

---

## Fase 3: Historia 1 — Las salidas tienen costo de tránsito (P1) 🎯 MVP

**Meta**: cruzar una salida tarda según su costo, para el jugador y para errantes y rastreadores; sin costos declarados todo se comporta como antes.

**Prueba independiente**: con una cripta cuyas salidas declaran costos distintos, mover al jugador y a un errante y comprobar los tiempos; con una cripta sin costos, comprobar que nada cambia.

### Pruebas de la Historia 1 (escribir primero; deben fallar)

- [X] T013 [P] [US1] Crear `test_terreno_costos.py` con los escenarios de la Historia 1: salida sin costo = 100 (FR-101); mismo costo en ambos sentidos (FR-102); jugador con salida de costo distinto de 100 (FR-103, FR-104); velocidad alta y costo 1 da intervalo ≥ 1 (FR-104); cambio de velocidad en pleno cruce reescala el tiempo restante (FR-105); errante y rastreador conservan su elección de destino y solo cambia el tiempo (FR-106); atacar y esperar siguen en 100 (FR-107). Cada prueba cita su FR en el nombre o el docstring.
- [X] T014 [P] [US1] Agregar a `test_terreno_costos.py` las pruebas de datos inválidos: costo "cero, negativo, no entero o booleano" produce 100 y una advertencia; esqueleto de la Parte I sin `costo` sigue válido. (FR-101, FR-118)
- [X] T015 [P] [US1] Agregar a `test_terreno_costos.py` la prueba de persistencia: guardar y restaurar una partida conserva el `costo` de cada salida, y un archivo de la versión anterior se rechaza con un mensaje que indica la versión encontrada y la esperada. (FR-119, VI)

### Implementación de la Historia 1

- [X] T016 [US1] Hacer que `ActorLogica._mover` en `Logica/ActorLogica.py` informe en `ResultadoEventoDTO.costo` el costo de la salida cruzada. (FR-103)
- [X] T017 [US1] Cambiar el contrato de `ComportamientoEnemigo.acción` en `Logica/ComportamientoEnemigo.py` para que devuelva `AccionEnemigoDTO` y recibir un parámetro opcional `campo_de_costos` (lo usará solo el cazador). (FR-106, FR-107)
- [X] T018 [P] [US1] Adaptar `Logica/CompErrante.py` al nuevo contrato: misma conducta; el costo es el de la salida cruzada, o 100 si no se movió. (FR-106, FR-107)
- [X] T019 [P] [US1] Adaptar `Logica/CompRastreador.py` al nuevo contrato: misma conducta; el costo es el de la salida cruzada, o 100 si no se movió. (FR-106, FR-107)
- [X] T020 [P] [US1] Adaptar `Logica/CompGuardian.py` al nuevo contrato: nunca se mueve, costo 100. (FR-107)
- [X] T021 [US1] En `Logica/EnemigosLogica.py` programar el siguiente `ACCION_ENEMIGO` con el costo informado por la acción (en vez del 100 fijo); atacar sigue en 100. (FR-103, FR-107)
- [X] T022 [US1] En `Controlador/ControladorJuego.py` construir el evento `MOVER_JUGADOR` con el costo de la salida elegida (en vez del 100 fijo). La fórmula de intervalo en `Logica/RelojVirtual.py` no cambia. (FR-103, FR-104)
- [X] T023 [US1] Persistir el costo: agregar `costo` al final de `SalidaGuardadaDTO` en `DTO/EstadoGuardadoDTO.py`, exportar e importar en `Logica/EstadoGuardadoLogica.py`, y subir `VERSION_ESTADO` de 2 a 3 y `VERSION_FORMATO` de 5 a 6 en `adaptadores/AlmacenPartidaBinario.py`. Sin cambiar el orden de `CLASES_DTO` en `adaptadores/codec_partida.py`. (FR-119, VI)
- [X] T024 [US1] Ejecutar las pruebas existentes de la Parte I (`test_*.py`, `tests_labs/`) y corregir regresiones causadas por el cambio de contrato de comportamientos. (FR-106, FR-107)

**Punto de control**: la Historia 1 pasa por sí sola; sin costos declarados la partida es igual a la de antes.

---

## Fase 4: Historia 2 — El cazador persigue por la ruta más barata (P1)

**Meta**: un cazador calcula el costo mínimo hasta el jugador, se mueve un paso por una ruta de costo mínimo respetando el desempate, ataca en la misma sala y espera si no hay ruta o si el costo supera su rango.

**Prueba independiente**: cripta pequeña con rutas de costos conocidos; verificar paso a paso la decisión del cazador.

### Pruebas de la Historia 2 (escribir primero; deben fallar)

- [X] T025 [P] [US2] Crear `test_cazador.py` con los escenarios de la Historia 2: ataca en la misma sala (FR-110); espera con costo 100 sin ruta abierta (FR-112); espera con costo 100 si el costo mínimo supera el rango (FR-112); prefiere la ruta de menor costo aunque tenga más salas (FR-111, FR-113); desempate por menor id con muchas rutas de igual costo (FR-114); el costo de la acción es el de la salida cruzada (FR-113); no abre puertas cerradas (FR-115). Cada prueba cita su FR.
- [X] T026 [P] [US2] Agregar a `test_cazador.py`: rango 0 declarado solo ataca en su sala; rango ausente o inválido se trata como 0 con advertencia (FR-108); una puerta que se cierra durante el cruce no cancela el cruce en curso y la puerta se evalúa solo al iniciar el movimiento (FR-109); la decisión no cambia según qué salas estén descargadas (FR-117).
- [X] T027 [P] [US2] Crear `test_monticulo_minimo.py` con pruebas del montículo (orden por `(costo, id)`, repetidos, vacío) y de que su implementación no importa módulos prohibidos. (I)

### Implementación de la Historia 2

- [X] T028 [P] [US2] Crear `Logica/MonticuloMinimo.py`: montículo binario sobre `list`, clave `(costo, id de sala)`, con entradas duplicadas y descarte al sacar. No reutilizar el del reloj (ver `research.md` §3). (I)
- [X] T029 [P] [US2] Crear `DTO/MapaDTO.py` con el esqueleto completo: por sala (posición = id), sus salidas `(destino, costo, cerrada_inicial)` en orden N, S, E, O, y la lista de advertencias. Sin diccionarios. (FR-117, FR-118)
- [X] T030 [US2] Declarar `obtener_mapa(cripta_id)` en `Logica/FuenteCripta.py` e implementarlo en `adaptadores/servicioCripta.py` a partir del esqueleto ya descargado (cero solicitudes extra). Debe funcionar igual con `--offline` por `adaptadores/cliente_offline.py`. (FR-117, VI)
- [X] T031 [US2] Crear `Logica/MapaCripta.py`: aristas salientes y entrantes por sala en listas contiguas; el estado de una puerta se lee del `SalidaDTO` de la sala cargada, o de `cerrada_inicial` si la sala no está cargada. Dimensionar con la cantidad de salas del esqueleto. (FR-117, V)
- [X] T032 [US2] Crear `Logica/CampoDeCostos.py` en su versión base **sin reutilización**: costo mínimo desde la sala del jugador por aristas entrantes con `MonticuloMinimo`, acotado por la cota, con reinicio por marca de época, y `costo_hasta_jugador(sala)` que devuelve costo o "fuera de alcance". Esta versión sirve de referencia "desde cero". (FR-111, FR-122)
- [X] T033 [US2] Crear `Logica/CompCazador.py` con `ComportamientoCazador` según `data-model.md`: ataca en la misma sala; si no, obtiene `d`; sin ruta o `d` > rango espera con costo 100; si no, entre las salidas abiertas con `costo(u,v) + costo_hasta_jugador(v) == d` elige el menor id y devuelve el costo de esa salida. Sin azar. (FR-110, FR-111, FR-112, FR-113, FR-114, FR-115, II)
- [X] T034 [US2] Registrar el caso `"cazador"` en `Logica/ComportamientoFactory.py` apuntando a `ComportamientoCazador`. (FR-108)
- [X] T035 [US2] En `Logica/EstadoJuegoLogica.py` construir el `MapaCripta` y el `CampoDeCostos` al iniciar la partida y entregarlos al gestor de eventos. (FR-117)
- [X] T036 [US2] En `Logica/GestorEventos.py`, caso `ACCION_ENEMIGO`, pasar el campo de costos a `decidirAccion` y, desde `Logica/EnemigosLogica.py`, al comportamiento. Los demás comportamientos lo ignoran. La puerta se evalúa al iniciar el movimiento. (FR-109, FR-116)
- [X] T037 [US2] Persistir el rango: agregar `rango` al final de `EnemigoGuardadoDTO` en `DTO/EstadoGuardadoDTO.py` y exportarlo e importarlo en `Logica/EstadoGuardadoLogica.py`; extender la prueba de persistencia de T015 con un cazador. La versión de formato ya subió en T023. (FR-108, FR-119)

**Punto de control**: la Historia 2 pasa por sí sola con el campo base (sin reutilización).

---

## Fase 5: Historia 3 — La decisión es siempre la de calcular desde cero (P1)

**Meta**: reutilizar el campo entre turnos sin cambiar jamás la decisión respecto de calcularlo desde cero (principio III).

**Prueba independiente**: tras cada tipo de evento, comparar la decisión con el campo reutilizado contra la decisión con el campo base de T032.

### Pruebas de la Historia 3 (escribir primero; deben fallar)

- [X] T038 [P] [US3] Crear `test_equivalencia_cazador.py` con los escenarios de la Historia 3: puerta de la ruta que se cierra entre dos turnos; puerta que se abre; el jugador cambia de sala; cazador nuevo con rango mayor que la cota; deshacer con pergamino; restaurar partida. Para cada caso comparar campo reutilizado vs. desde cero. (FR-116, FR-117)
- [X] T039 [P] [US3] Agregar a `test_equivalencia_cazador.py` una prueba por secuencias aleatorias deterministas por semilla (cripta sintética de T005, miles de eventos mezclados) que compare ambas decisiones tras **cada** evento; cualquier diferencia falla la prueba. (FR-116, III)
- [X] T040 [P] [US3] Crear `test_puertas_punto_unico.py` que recorra el código de `Logica/` y `adaptadores/` y falle si encuentra una escritura de `.cerrada` fuera de la función única de cambio de puertas. (FR-116, III)

### Implementación de la Historia 3

- [X] T041 [US3] En `Logica/SalasLogica.py` crear la función única de cambio de estado de una puerta (incrementa el contador de cambios y avisa su destino) y usarla en abrir y cerrar. (FR-116)
- [X] T042 [US3] Hacer que el deshacer de puertas de `Logica/RetrocesoLogica.py` y la restauración de partida en `Logica/EstadoGuardadoLogica.py` pasen por la función única de T041. (FR-116)
- [X] T043 [US3] Agregar reutilización a `Logica/CampoDeCostos.py` según la tabla de `research.md` §4: válido solo si coinciden sala del jugador, cota y contador; cierre o apertura de la puerta x→y invalida solo si y fue alcanzado; nada cambia por moverse, atacar o morir; cota mayor recalcula; cargar partida descarta. Mantener la versión desde cero accesible para las pruebas. (FR-116, III)
- [X] T044 [US3] Avisar al campo de los cambios de sala del jugador (movimiento, deshacer, restauración) desde `Logica/GestorEventos.py` y `Logica/EstadoJuegoLogica.py`. (FR-116)
- [X] T045 [US3] Ejecutar `test_equivalencia_cazador.py` y `test_puertas_punto_unico.py` y corregir cualquier evento que invalide de menos. (FR-116, III)

**Punto de control**: la decisión del cazador coincide en 100 % de los casos con la de calcular desde cero.

---

## Fase 6: Historia 4 — Partidas deterministas y medibles (P2)

**Meta**: misma cripta, semilla y acciones dan la misma partida, y `--bench` demuestra los límites con la alternativa descartada.

**Prueba independiente**: ejecutar dos veces la misma partida y comparar; ejecutar `--bench terreno`.

### Pruebas de la Historia 4 (escribir primero; deben fallar)

- [X] T046 [P] [US4] Crear `test_determinismo_cazador.py`: dos partidas con la misma cripta, semilla y acciones con cazadores dan registros idénticos; una partida con salas descargadas y otra sin descargar dan las mismas decisiones. (FR-117, FR-120, II)
- [X] T047 [P] [US4] Guardar en `specs/001-terreno-y-cazador/replays/` un `partida.log` por escenario reproducible, con el id del requisito en el nombre del archivo o en su cabecera, y una prueba que los reproduzca con el motor de `--replay` sin vista. (FR-120, IX, IV)

### Implementación de la Historia 4

- [X] T048 [US4] Crear `bench/terreno.py` con las cuatro secciones de `contracts/bench-terreno.md`: un cazador frente a muchos (1, 10, 50, 200) contra la búsqueda por cazador; rango pequeño frente a grande con N creciente contra la búsqueda sin cota; puertas estables frente a cambiantes contra invalidar con cualquier cambio; equivalencia. Usar el generador de T005 y la semilla de `bench/datos.py`. (FR-121, FR-122, FR-123, VII)
- [X] T049 [US4] Registrar el bloque `terreno` en `bench/__init__.py` y que el código de salida sea distinto de 0 si el ciclo supera 20 ms. (FR-121, FR-123)
- [X] T050 [P] [US4] Repetir el bloque `ciclo` en `bench/ciclo.py` con decenas de cazadores activos y comprobar el límite de 20 ms. (FR-121, VII)
- [X] T051 [P] [US4] Repetir con la carga nueva los bloques `bench/guardado.py` (campos nuevos) y `bench/retroceso.py` (cambios de puertas por el punto único) y anotar el antes y el después. (VII)
- [X] T052 [US4] Ejecutar `python main.py --bench terreno` y `--bench ciclo,guardado,retroceso`, guardar la salida en `specs/001-terreno-y-cazador/mediciones.md` y comprobar los límites. Si alguna decisión deja de servir, cambiarla y documentarlo. (FR-121, FR-122, VII)

**Punto de control**: determinismo comprobado y límites medidos con la alternativa descartada.

---

## Fase 7: Historia 5 — Los costos y los cazadores se ven en pantalla (P2)

**Meta**: quien juega ve el costo de cada salida y distingue a los cazadores.

**Prueba independiente**: mostrar una sala con salidas de costos distintos y un cazador junto a otro enemigo.

- [X] T053 [P] [US5] Agregar a `test_terreno_costos.py` pruebas del texto de la vista: cada salida muestra su costo (FR-130), el cazador lleva una marca visible distinta de los demás enemigos (FR-131) y las advertencias de datos se imprimen al iniciar. (FR-130, FR-131)
- [X] T054 [US5] Mostrar el costo de cada salida y la marca de cazador en `Controlador/Vista.py` según `contracts/interfaz-vista.md`. La vista no calcula nada. (FR-130, FR-131, IV)
- [X] T055 [US5] Mostrar al iniciar las advertencias acumuladas por el servicio en `Controlador/ControladorJuego.py`. (FR-118)

**Punto de control**: las cinco historias funcionan; la vista solo presenta.

---

## Fase 8: Cierre y transversales

- [X] T056 [P] Completar la matriz de trazabilidad de `specs/001-terreno-y-cazador/quickstart.md` con los nombres reales de pruebas y logs; ningún FR-101 a FR-131 sin prueba. (IX)
- [X] T057 [P] Crear o actualizar `DECISIONES.md` con enlaces a `spec.md` y `plan.md`, indicando si la decisión final coincide con el plan original y, si no, qué medición motivó el cambio. (X)
- [X] T058 [P] Registrar en `PROMPTS_LLM.md` cada comando `/speckit` con texto propio de esta capacidad, con herramienta y modelo. (XI)
- [X] T059 [P] Actualizar `README.md` con el bloque `--bench terreno` y la nota del cambio de versión del formato de partida. (VI)
- [X] T060 Comprobar con búsqueda que el código nuevo no importa `heapq`, `bisect`, `collections`, `networkx` ni usa `dict`/`set` como índice, y que no hay ids ni cantidades de una cripta concreta. (I, V)
- [X] T061 Ejecutar todas las pruebas (`python -m unittest`) y el quickstart completo; registrar cualquier fallo sin ocultarlo. (IX)
- [X] T062 Comparar `spec.md` con el programa entregado y corregir cualquier desajuste primero en la especificación, en commit aparte del código. (X)

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1** primero. T002 y T003 (especificación) bloquean la implementación. T004 y T005 son paralelas entre sí.
- **Fase 2** depende de la Fase 1 y bloquea todas las historias.
- **Fase 3 (US1)** depende de la Fase 2. Es el MVP.
- **Fase 4 (US2)** depende de la Fase 3: usa el nuevo contrato de comportamientos (T017) y el costo informado por el movimiento (T016).
- **Fase 5 (US3)** depende de la Fase 4: reutiliza y compara contra el campo base de T032.
- **Fase 6 (US4)** depende de la Fase 5 (mide la versión final). T046 y T047 pueden empezar tras la Fase 4.
- **Fase 7 (US5)** depende solo de la Fase 2, pero conviene después de la Fase 4 para ver cazadores reales.
- **Fase 8** al final.

### Dentro de cada historia

- Pruebas primero, que deben fallar; luego DTO y datos, lógica, integración.
- Las tareas que tocan el mismo archivo no son paralelas: `Logica/GestorEventos.py` (T036, T044), `adaptadores/servicioCripta.py` (T010, T030), `Logica/EstadoGuardadoLogica.py` (T023, T037, T042), `Logica/CampoDeCostos.py` (T032, T043), `test_terreno_costos.py` (T013 a T015, T053).

### Oportunidades de paralelismo

- Fase 2: T006, T007, T008 y T009 (archivos distintos).
- Historia 1: T013 a T015 juntas; T018, T019 y T020 juntas.
- Historia 2: T025 a T027 juntas; T028 y T029 juntas.
- Historia 3: T038, T039 y T040 juntas.
- Historia 4: T050 y T051 juntas.
- Fase 8: T056 a T059 juntas.

## Estrategia de implementación

1. **MVP**: Fases 1 a 3 (especificación cerrada, fundamentos e Historia 1). Entrega costos de salida funcionando para todos los actores sin tocar a los cazadores.
2. Añadir la Historia 2 (cazador con campo base) y comprobar con `test_cazador.py`.
3. Añadir la Historia 3 (reutilización con equivalencia demostrada). **No** activar la reutilización en el juego hasta que T045 pase.
4. Añadir las Historias 4 y 5; cerrar con la Fase 8.
5. En cada punto de control, confirmar por separado los cambios de especificación (antes) y de código (después).

## Cobertura de requisitos

| Requisito | Tareas |
|---|---|
| FR-101, FR-102 | T002, T006, T010, T013, T014 |
| FR-103, FR-104, FR-105 | T008, T013, T016, T021, T022 |
| FR-106, FR-107 | T009, T013, T017 a T021 |
| FR-108 | T003, T007, T011, T012, T026, T034, T037 |
| FR-109 | T003, T026, T036 |
| FR-110 a FR-115 | T025, T032, T033 |
| FR-116 | T036, T038 a T045 |
| FR-117 | T026, T029 a T031, T035, T046 |
| FR-118, FR-119 | T003, T010, T011, T014, T015, T023, T037, T055 |
| FR-120 | T046, T047 |
| FR-121, FR-122, FR-123 | T032, T048 a T052 |
| FR-130, FR-131 | T053 a T055 |

## Fase final: contrato compartido de rutas

- [ ] T063 Crear pruebas de los métodos `total_salas`, `salidas(sala)` y `entrantes(sala)` de `MapaCripta`, incluidos ids sin sala y conexiones de un solo sentido. (FR-116)
- [ ] T064 Agregar esos métodos a `Logica/MapaCripta.py` sin romper los campos actuales. (FR-116)
- [ ] T065 Crear pruebas de `version_puertas`: sube con cada cambio de puerta y no sube sin cambio. (FR-116)
- [ ] T066 Agregar `version_puertas` a `MapaCripta` y hacer que `CampoDeCostos.puerta_cambio` la suba. (FR-116)
- [ ] T067 Crear pruebas de `BuscadorRutas` con una vista falsa de pocas salas: mismas decisiones que el cazador actual, desempate por menor id, ruta inexistente. (FR-111, FR-114)
- [ ] T068 Crear `Logica/BuscadorRutas.py` con `distancias_hacia(destino, vista, limite)` y `siguiente_paso(origen)`. (FR-111, FR-114)
- [ ] T069 Hacer que el cazador use `BuscadorRutas` sin cambiar su decisión. (FR-111, FR-114, FR-116)
- [ ] T070 Comprobar que las pruebas existentes siguen pasando y que `--bench terreno` da tiempos comparables. (FR-121, FR-122)
