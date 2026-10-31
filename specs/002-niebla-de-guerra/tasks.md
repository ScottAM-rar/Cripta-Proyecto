# Tareas: Niebla de guerra y mapa conocido

**Entrada**: documentos de diseño en `specs/002-niebla-de-guerra/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerrequisitos**: `plan.md` y `spec.md` (con las 2 clarificaciones de la sesión 2026-10-31 y los supuestos corregidos: cada salida tiene su propia puerta, y el jugador está en la sala destino desde el instante de la acción, sin estado «cruzando»; SC-006 se mide por conteo). La numeración del formato binario (P3 del plan) debe cerrarse con Scott antes de las tareas T033 a T036.

**Pruebas**: se incluyen en todas las historias porque la constitución (principio IX) exige que cada escenario de aceptación tenga una prueba automatizada o un `partida.log` que cite su requisito. Cada prueba se escribe **antes** del código y debe fallar primero.

**Organización**: tareas agrupadas por historia de usuario para implementarlas y probarlas por separado. Cada tarea indica entre paréntesis los requisitos que atiende. La historia 3 (antorcha, P2) se implementa antes que la 4 (pergamino) porque el caso del Apéndice B «pergamino que revierte una entrada con antorcha» necesita ambas.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencia de tareas incompletas).
- **[USn]**: historia de `spec.md` a la que pertenece.
- Las rutas son relativas a la raíz del repositorio. Las pruebas siguen la convención del repositorio (`unittest`, archivos `test_*.py` en la raíz, ayudas en `tests_labs/`).

## Reglas para todas las tareas (constitución)

- **No usar** `dict` ni `set` como índice, caché o tabla de búsqueda; ni `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` ni bibliotecas de grafos; **ni `sorted()` ni `list.sort()`** (el orden sale de `ordenar_adaptativo`). Se permite `list`, `struct`, `json`, `requests`. No agregar usos nuevos de `deque` (solo se recorre el de `SalaDTO.salidas`, en lectura).
- **No modificar** `Logica/MapaCripta.py`, `Logica/RecorridoPorNiveles.py`, `Logica/BuscadorRutas.py` ni `Logica/PuertasLogica.py`. El único punto de cambio de puertas sigue siendo `PuertasLogica.fijar_cerrada`; ningún código nuevo escribe `.cerrada`.
- Ningún id de sala o entidad, cantidad, presupuesto ni nombre de una cripta concreta en el código. Todo se dimensiona con el mayor id del esqueleto más uno (los ids van desde 1; listas de tamaño N+1).
- El modelo (`Logica/`, `DTO/`) no importa red, disco ni vista.
- El conocimiento solo lee el esqueleto (`MapaCripta`) y `esta_abierta`; **nunca** llama a `ingresarEnSala` ni a `construir_sala` para explorar.
- Los commits de especificación van **antes** y **separados** de los de código (principio X). No escribir en `PROMPTS_LLM.md` (el registro lo lleva el grupo en `PROMPTS_LLM_Fer.md`).

---

## Fase 1: Preparación

**Propósito**: revisar contra la constitución y dejar listo el material de pruebas. Bloquea todo lo demás.

- [ ] T001 Revisar `plan.md` y este `tasks.md` contra la lista de prohibidos del principio I y anotar el resultado en `specs/002-niebla-de-guerra/checklists/requirements.md` (sección Notas). (I)
- [ ] T002 [P] Agregar a `tests_labs/cripta_sintetica.py` una función `mapa_dto_desde_esqueleto(esqueleto)` que devuelva el `MapaDTO` (con nombres) armado por el mismo camino que usa el juego (`ServicioCripta.obtener_mapa` sobre la API falsa), junto a la existente `mapa_desde_esqueleto`. Sin ids ni tamaños fijos. (V, FR-206)
- [ ] T003 [P] Crear `tests_labs/referencia_conocimiento.py` con la **referencia ingenua**: a partir del esqueleto, una lista de entradas del jugador (sala, antorcha encendida o no, estados reales de las puertas en ese instante) y los cambios de puerta vistos, reconstruye **desde cero** el estado de cada sala (0 desconocida, 1 avistada, 2 explorada), la puerta recordada de cada salida (0 sin observar, 1 abierta, 2 cerrada) y las exploradas en orden de descubrimiento, con bucles simples. Sin `dict`/`set`. Recibe un parámetro `con_puertas` (por defecto verdadero): con falso solo reconstruye y compara estados de sala y exploradas, que es lo único que existe en la historia 1. Es la comparación de la equivalencia (principio III) y de SC-003. (III, FR-203, FR-207, FR-214)
- [ ] T004 Agregar a `tests_labs/referencia_conocimiento.py` la función `comprobar_invariantes(conocimiento, mapa, salas, jugador)` que recibe también `con_puertas` (por defecto verdadero) y verifica I1 a I6 de `data-model.md`; con `con_puertas` falso comprueba solo I2, I3, I4 e I5, y con verdadero además I1 e I6: puerta recordada igual a la real en las salidas adyacentes a la sala del jugador (I1); `estado[s] == 2` si y solo si `s` está en `exploradas`, sin repetidas (I2); `estado[s] == 1` si y solo si no está explorada y es destino de una salida de una explorada (I3); la sala del jugador está explorada (I4); `puertas[sala*4+d] != 0` solo si esa salida existe (I5); una puerta nunca observada vale 0 (I6). Depende de T003 (mismo archivo). (FR-201, FR-203, FR-207)

**Punto de control**: material de pruebas listo; el análisis contra el principio I está registrado.

---

## Fase 2: Fundamentos (bloquea todas las historias)

**Propósito**: el nombre de cada sala llega al conocimiento, existen los DTO y la estructura del conocimiento, y el modelo la construye. Sin esto ninguna historia puede probarse.

- [ ] T005 [P] Escribir en `test_mapa_conocido.py` (archivo nuevo) la clase `TestNombresDelEsqueleto`: `obtener_mapa` conserva el nombre de cada sala del esqueleto; `MapaCripta` construido con ese mapa responde igual que antes (mismas aristas, costos y `existe`). Debe fallar primero. (FR-206, plan P2)
- [ ] T006 [P] Agregar el campo `nombre` ("texto"; por defecto vacío) a `SalaMapaDTO` en `DTO/MapaDTO.py`, al final de la clase para no romper llamadas existentes. (plan P2)
- [ ] T007 Rellenar `SalaMapaDTO.nombre` desde el esqueleto en `ServicioCripta.obtener_mapa` de `adaptadores/servicioCripta.py`. `MapaCripta` no se toca. Depende de T006. (FR-206, plan P2)
- [ ] T008 [P] Crear `DTO/ConocimientoDTO.py` con los DTO de lectura de la vista, exactamente como en `data-model.md`: `MapaConocidoDTO` (`sala_actual`, `salas`), `SalaConocidaDTO` (`id`, `nombre`, `salidas`) y `SalidaConocidaDTO` (`direccion`, `costo`, `puerta` con valores `"abierta"`, `"cerrada"` o `"sin observar"`, `destino_explorado`, `destino_id` y `destino_nombre` vacíos si `destino_explorado` es falso). Sin referencias a `MapaCripta` ni a `SalaDTO`. (FR-216, FR-219)
- [ ] T009 Crear `Logica/MapaConocido.py` con la estructura según `data-model.md`: constructor que recibe `MapaCripta`, los nombres, la lista de salas del modelo, el jugador y una función `registrar(lista_de_cambios)`; `estado` ("lista de enteros de tamaño N; 0 desconocida, 1 avistada, 2 explorada"), `puertas` ("lista de enteros de tamaño 4·N; posición sala*4 + d, con d 0 norte, 1 sur, 2 este, 3 oeste; 0 sin observar, 1 abierta, 2 cerrada"), `exploradas` (ids en orden de descubrimiento), `version_conocimiento`, `salas_reveladas` y `salidas_examinadas`; consultas `estado_de(sala)`, `puerta_recordada(sala, d)`, `exploradas_en_orden()` e índice de dirección. Todo dimensionado con `mapa.tamano`. Sin `dict`/`set`. (FR-201, FR-206, FR-223)
- [ ] T010 Construir el conocimiento en `Logica/EstadoJuegoLogica.py` con **un único auxiliar** `_crearMapaYConocimiento(cripta, salas, jugador)`, que obtiene el `MapaDTO` **una sola vez** y devuelve el campo de costos y el `MapaConocido` compartiendo el mismo `MapaCripta` (nombres tomados del `MapaDTO`). `iniciarJuego` lo usa ahora y la restauración (T035) lo usará después; `_crearCampoDeCostos` se conserva como envoltorio que devuelve solo el campo, para no romper llamadas existentes (`EstadoGuardadoLogica.restaurar` la usa hoy). Exponer `mapaConocido` en el modelo; si la fuente no entrega el mapa, queda en `None`. Todavía no explora nada. Depende de T007 y T009. (FR-201, FR-222)
- [ ] T011 En `Logica/GestorEventos.py` agregar el atributo `mapa_conocido` (asignado por quien arma la partida, como `campo_de_costos`) y pasárselo a `PergaminoLogica` (atributo `mapa_conocido`). Ambos atributos pueden quedar en `None` (valor por defecto). Sin cambiar todavía ningún comportamiento. Depende de T009. (FR-214)

**Punto de control**: `test_mapa_conocido.TestNombresDelEsqueleto` pasa; el modelo construye un conocimiento vacío; la Parte I y las capacidades 001 y 005 siguen pasando sus pruebas.

---

## Fase 3: Historia 1 — Explorar y avistar salas (P1) 🎯 MVP

**Meta**: el jugador empieza conociendo la sala inicial y, al entrar a una sala, la explora y avista las salas detrás de sus salidas, abiertas o cerradas.

**Prueba independiente**: en una cripta pequeña conocida, mover al jugador por varias salas y comprobar tras cada entrada el estado de cada sala.

- [ ] T012 [US1] Escribir en `test_mapa_conocido.py` la clase `TestExplorarYAvistar` con los escenarios 1 a 7 de la historia 1: instante 0 (sala inicial explorada, destinos avistados, el resto desconocido); entrar a una sala avistada (pasa a explorada); entrar a una sala nueva con tres salidas, una con puerta cerrada (las tres avistadas); una avistada solo se sabe que existe (el conocimiento no entrega su nombre ni sus salidas); sala ya explorada que no pasa a avistada; reentrar sin perder estados; conexión de un solo sentido que no avista (`esqueleto_de_conexiones` con `un_sentido=True`). Al final de cada prueba llamar a `comprobar_invariantes(..., con_puertas=False)` y comparar con la referencia sin puertas. Agregar la clase `TestSinConocimiento`: con `mapa_conocido` en `None` (fuente sin mapa, o `GestorEventos` armado sin él, como en las pruebas de la Parte I y 001) mover al jugador, abrir y cerrar puertas y usar el pergamino funciona sin errores y sin cambios respecto de antes. Debe fallar primero. (FR-201 a FR-205, FR-213)
- [ ] T013 [US1] Implementar en `Logica/MapaConocido.py` `iniciar(sala)` (conocimiento del instante 0: explora la sala, avista sus destinos; **no registra** cambios) y `entrar(sala, antorcha=False)` sin antorcha: explora la sala si no lo estaba y avista cada destino desconocido que **exista** en el esqueleto, recorriendo `mapa.salidas(sala)` en el orden N, S, E, O; registra todo en **un solo nodo** con `registrar` (orden: `EXPLORAR_SALA`, luego sus `AVISTAR_SALA`; cada cambio es un `CambioDTO` con `tipo_accion`, `objeto_afectado` = el conocimiento, `indice` = id de la sala, `valor_anterior` y `valor_nuevo`) y **solo si hubo cambio real**; actualiza `salas_reveladas`, `salidas_examinadas` y `version_conocimiento`. Lanza `ValueError` si la sala no existe en el esqueleto. Depende de T009. (FR-202, FR-203, FR-204, FR-205, FR-224)
- [ ] T014 [US1] Llamar a `iniciar` con la sala inicial del jugador al final de `EstadoJuegoLogica.iniciarJuego` en `Logica/EstadoJuegoLogica.py`, antes de que exista ninguna acción (sin historial, por tanto no deshacible). Depende de T010 y T013. (FR-202, FR-215)
- [ ] T015 [US1] En `Logica/GestorEventos.py`, caso `MOVER_JUGADOR`, llamar a `mapa_conocido.entrar(jugador.id_sala_actual, ...)` cuando el movimiento tuvo éxito, justo después de `cargar_sala` (el jugador ya está en la sala destino en el instante de la acción: no hay estado «cruzando»). **Si `mapa_conocido` es `None`, no hace nada.** Todavía sin antorcha (se agrega en T023). Depende de T013 y T011. (FR-204)

**Punto de control**: la historia 1 se prueba sola: `python -m unittest test_mapa_conocido` en OK.

---

## Fase 4: Historia 2 — El mapa recuerda las puertas como las vio por última vez (P1)

**Meta**: cada salida recuerda el estado de su puerta de la última observación; se observa estando en la sala de origen o en la de destino de esa salida, al entrar y cuando la puerta cambia mientras el jugador sigue allí. El cambio se avisa por el aviso que ya recibe `fijar_cerrada`; no se crea un segundo camino de cambio de puertas.

**Prueba independiente**: abrir una puerta con cierre automático, alejarse hasta que se cierre, comprobar que lo recordado sigue abierto y luego volver a una de sus salas.

- [ ] T016 [US2] Escribir en `test_mapa_conocido.py` la clase `TestMemoriaDePuertas` con los escenarios 1 a 4 de la historia 2: puerta con cierre automático que el mapa recuerda abierta y está cerrada (**Apéndice B**) y que al volver a una de sus dos salas pasa a cerrada; lo recordado desde una sala lejana sigue abierto; cambio de puerta con el jugador en su sala (la abre él, o se cierra sola) refleja el nuevo estado en el mismo instante; salida hacia una avistada recordada como parte de la sala actual. Agregar: puerta nunca observada vale «sin observar» (FR-209); con dos salidas inversas en estados distintos, cada una se recuerda por separado. Al final de cada prueba llamar a `comprobar_invariantes(..., con_puertas=True)` y comparar con la referencia completa. Debe fallar primero. (FR-206, FR-207, FR-208, FR-209)
- [ ] T017 [US2] Escribir en `test_mapa_conocido.py` la clase `TestCaminosDeCambioDePuertas`: todo cambio de puerta **hacia adelante** (abrir, cerrar, cierre automático) llega a `MapaConocido.puerta_cambio` y el cambio que hace el pergamino al deshacer **no** llega; un cambio de una puerta lejos del jugador no registra nada; `Logica/MapaConocido.py` no escribe `.cerrada`. (FR-207, FR-208, III)
- [ ] T018 [US2] Ampliar `MapaConocido.entrar` en `Logica/MapaConocido.py`: tras explorar y avistar, observar las puertas de **cada arista saliente y de cada arista entrante** de la sala usando `MapaCripta.esta_abierta(arista, salas)` (el estado de la sala cargada o, si no está cargada, el inicial); anotar solo las diferencias con lo recordado, como `OBSERVAR_PUERTA` (`indice` = `sala*4 + d` de la salida observada; `valor_anterior` 0, 1 o 2; `valor_nuevo` 1 o 2) dentro del **mismo nodo** de la entrada. `iniciar` también observa (sin registrar). Depende de T013. (FR-202, FR-207)
- [ ] T019 [US2] Implementar `MapaConocido.puerta_cambio(salida)` en `Logica/MapaConocido.py`: buscar **por identidad** el objeto `salida` entre las salidas de la sala del jugador y entre las salidas de las salas de origen de sus aristas entrantes (solo las cargadas); si lo encuentra, anotar el nuevo estado como un `OBSERVAR_PUERTA` en un nodo propio solo si difiere de lo recordado; si no lo encuentra, no hace nada. Sin cambiar la firma de `fijar_cerrada`. Depende de T018. (FR-207, FR-208)
- [ ] T020 [US2] En `Logica/GestorEventos.py` separar los avisos de puerta: `_puerta_cambio(salida)` queda como está (solo invalida el campo de costos) y se le sigue entregando a `PergaminoLogica`; agregar `_puerta_cambio_adelante(salida)` que hace lo anterior **y** llama a `mapa_conocido.puerta_cambio(salida)`, y se le entrega a `SalaLogica` (abrir, cerrar y cierre automático). **Si `mapa_conocido` es `None`, solo hace lo de `_puerta_cambio`.** Depende de T019. (FR-207, FR-214)

**Punto de control**: las historias 1 y 2 pasan sus pruebas y `test_puertas_punto_unico.py` sigue en OK.

---

## Fase 5: Historia 3 — La antorcha ilumina las salas vecinas (P2)

**Meta**: con la antorcha encendida en el instante de entrar, todas las vecinas por cualquier salida quedan exploradas (nombre y salidas), sin revelar contenido y sin activar enemigos ni trampas ni descargar nada.

**Prueba independiente**: entrar con la antorcha encendida a una sala cuyas vecinas tienen enemigos y trampas, y comprobar conocimiento, solicitudes, enemigos activos y agenda.

- [ ] T021 [US3] Escribir en `test_mapa_conocido.py` la clase `TestAntorcha` con los escenarios 1 a 7 de la historia 3: vecinas con enemigos y trampas quedan exploradas **sin activarse** (**Apéndice B**: ningún enemigo con `activo` verdadero, ningún evento nuevo en la agenda, ninguna trampa disparada, 0 solicitudes nuevas a la fuente, `ultimo_paso` de las vecinas intacto); las salidas de las vecinas quedan avistadas; vecina detrás de puerta cerrada también explorada; con la antorcha apagada solo avista; encender la antorcha dentro de una sala no explora hasta la siguiente entrada (FR-212); apagarla no quita lo explorado; las puertas de una vecina explorada que no comparte el jugador figuran «sin observar» (FR-209). Debe fallar primero. (FR-203, FR-209 a FR-212)
- [ ] T022 [US3] Ampliar `MapaConocido.entrar(sala, antorcha)` en `Logica/MapaConocido.py`: si `antorcha` es verdadero, para cada salida de `sala` (orden N, S, E, O) cuyo destino exista y no esté explorado, explorarlo (`EXPLORAR_SALA`) y avistar los destinos desconocidos de **sus** salidas (`AVISTAR_SALA`), con un **bucle directo** sobre `mapa.salidas(...)`, sin `RecorridoPorNiveles`. **No** observa puertas de las vecinas, no llama a `ingresarEnSala` ni a `construir_sala`, no toca `ultimo_paso`. Todo en el mismo nodo de la entrada. Depende de T018. (FR-210, FR-211, FR-224)
- [ ] T023 [US3] En `Logica/GestorEventos.py`, caso `MOVER_JUGADOR`, pasar a `entrar` el valor de `jugador.antorcha_encendida` leído **en el instante de la entrada**; encender o apagar la antorcha no llama a `entrar`. Mantiene la guarda de `None` de T015. Depende de T022. (FR-210, FR-212)

**Punto de control**: las historias 1 a 3 pasan sus pruebas.

---

## Fase 6: Historia 4 — El pergamino de retroceso también deshace lo descubierto (P1)

**Meta**: al usar el pergamino el conocimiento vuelve exactamente a como estaba antes de la acción deshecha; el conocimiento del instante 0 no se puede deshacer. Contrato: `contracts/cambios-deshacibles.md`.

**Prueba independiente**: tomar el conocimiento antes de una acción, ejecutarla, usar el pergamino y comparar con la referencia.

- [ ] T024 [US4] Crear `test_niebla_retroceso.py` con los escenarios 1 a 5 de la historia 4: entrada con antorcha encendida y pergamino (**Apéndice B**: la sala y las vecinas exploradas por la antorcha vuelven a avistada o desconocida); entrada sin antorcha; acción en que el jugador observó una puerta cambiada; pergamino sin historial (la sala inicial sigue explorada y sus vecinas avistadas); cinco acciones y cinco pergaminos devuelven el conocimiento previo a la primera. Agregar: acción rechazada sin cambios de conocimiento, historial recortado (lo descubierto en acciones descartadas se conserva), `version_conocimiento` sube también al deshacer, y recorridos aleatorios con semilla fija que comparan el conocimiento incremental con `referencia_conocimiento` tras cada acción y cada deshacer y llaman a `comprobar_invariantes`. Debe fallar primero. (FR-214, FR-215, SC-003)
- [ ] T025 [US4] Implementar `MapaConocido.deshacer(cambio)` en `Logica/MapaConocido.py` según el contrato: `EXPLORAR_SALA` restaura `estado[sala] = valor_anterior` y quita la sala del **final** de `exploradas` (`ValueError` si no es la última); `AVISTAR_SALA` restaura `estado[sala]`; `OBSERVAR_PUERTA` restaura `puertas[indice]`; los tres suben `version_conocimiento` y **no registran** ningún cambio nuevo. Depende de T013, T018 y T022. (FR-214, FR-225)
- [ ] T026 [US4] En `Logica/PergaminoLogica.py`, `_revertir_cambio`: agregar una sola rama `EXPLORAR_SALA | AVISTAR_SALA | OBSERVAR_PUERTA` que delegue en `cambio.objeto_afectado.deshacer(cambio)`. No tocar `RetrocesoLogica`. Confirmar que el `avisar_puerta` del pergamino es el que solo invalida el campo de costos (T020). Depende de T025. (FR-214)

**Punto de control**: las historias 1 a 4 pasan sus pruebas; en cualquier recorrido aleatorio, deshacer devuelve el conocimiento exacto previo.

---

## Fase 7: Historia 5 — Ver el mapa conocido (P1)

**Meta**: el comando `mapa` muestra las salas exploradas con sus salidas y las avistadas como «sala sin explorar», solo desde el conocimiento del jugador; y la pantalla de la sala actual deja de revelar el id o nombre de las salas no exploradas. Contrato: `contracts/interfaz-vista.md`.

**Prueba independiente**: tras explorar parte de una cripta, mostrar el mapa; luego alterar las partes desconocidas y comprobar que el mapa no cambia.

- [ ] T027 [US5] Crear `test_niebla_vista.py` con los escenarios 1 a 6 de la historia 5 y las pruebas de `contracts/interfaz-vista.md` §4: (1) **vista con el grafo completo apagado**: construir a mano un `MapaConocidoDTO` y la sala actual e imprimir con `mostrar_mapa_conocido` y `mostrar_juego` sin `MapaCripta` ni lista de salas, con objetos que lanzan error si se tocan; (2) dos partidas idénticas salvo nombre, salidas y contenido de salas desconocidas o avistadas imprimen el mismo mapa (SC-002); (3) el texto impreso no contiene id ni nombre de salas avistadas o desconocidas; dos salidas hacia la misma avistada se ven idénticas; (4) orden ascendente de id y salidas en el orden declarado; (5) `mapa` no avanza el reloj, no cuenta como acción, no entra al historial del pergamino ni al log; (6) «sin observar» se imprime tal cual (FR-209). Debe fallar primero. (FR-209, FR-216 a FR-219)
- [ ] T028 [US5] Implementar en `Logica/MapaConocido.py` `instantanea()`, que devuelve un `MapaConocidoDTO`: las exploradas **en orden ascendente de id usando `ordenar_adaptativo` sobre una copia** de `exploradas` (nunca `sorted()` ni `list.sort()`), cada una con sus salidas en el orden en que la sala las declara, el costo de la arista, la puerta recordada como texto, y el destino con `destino_id` y `destino_nombre` **solo si está explorado**. Una avistada solo aparece como `destino_explorado = False`. Depende de T008 y T009. (FR-216, FR-217, FR-219)
- [ ] T029 [US5] Exponer la consulta: en `Logica/EstadoJuegoLogica.py` los métodos `mapaConocido()` y `vistaSalaActual()` (la sala del jugador con sus salidas en el mismo formato; `ValueError` si el juego no ha sido iniciado) y en `Servicio/EstadoJuegoServicio.py` los métodos con el mismo nombre que los reenvían. Entregan DTO, nunca el mapa completo ni salas del modelo. Ninguno avanza el reloj ni abre acción. Depende de T028. (FR-216, FR-218, FR-219)
- [ ] T030 [P] [US5] En `Controlador/Vista.py` agregar `mostrar_mapa_conocido(mapa_dto)` con el formato de `contracts/interfaz-vista.md` §3 (sala actual con `*`, «sala sin explorar» para avistadas, «sin observar» para puertas sin observar, ninguna sala desconocida) y cambiar la sección SALIDAS de `mostrar_juego` para recibir las salidas conocidas de la sala actual como parámetro **obligatorio, sin valor por defecto** (así no existe un camino que imprima `Sala {id}` de una no explorada); destino con nombre solo si está explorado. Actualizar la llamada con 4 argumentos de `test_terreno_costos.py` (línea ≈ 163) para que construya y pase el DTO de la sala actual. Depende de T008. (FR-209, FR-216, FR-219)
- [ ] T031 [US5] En `Controlador/ControladorJuego.py` agregar el comando `mapa`: se resuelve en el controlador, imprime con la vista y vuelve a pedir la orden **sin** llamar a `accionJugador`, sin tocar el reloj, el historial ni el log; pasar a `mostrar_juego` el resultado de `vistaSalaActual()`; incluir `mapa` en el texto de ayuda de comandos. Depende de T029 y T030. (FR-216, FR-218, FR-219)

**Punto de control**: las historias 1 a 5 pasan sus pruebas; el recorrido manual 1 a 3 de `quickstart.md` funciona.

---

## Fase 8: Historia 6 — Guardar y cargar una partida con niebla (P2)

**Meta**: el conocimiento se guarda con la partida y se restaura exactamente; un archivo sin niebla se rechaza con versión encontrada y esperada. Contrato: `contracts/estado-guardado-niebla.md`.

**Prueba independiente**: explorar, guardar, cargar y comparar conocimiento y salida del mapa antes y después.

**Bloqueo**: T033 a T036 dependen de cerrar P3 (numeración del formato) con Scott. Se asume `VERSION_ESTADO = 4` y `VERSION_FORMATO = 7` salvo que el grupo decida otra cosa; en ese caso ajustar T033 y T036 y anotarlo en el contrato.

- [ ] T032 [US6] Crear `test_niebla_guardado.py` con los escenarios 1 a 3 de la historia 6 y las comprobaciones V1 a V5: ida y vuelta con salas exploradas, avistadas y una puerta recordada distinta de la real; continuación con las mismas acciones idéntica a una partida que no se guardó (SC-004); cada comprobación V1 a V5 con un estado manipulado (id fuera de rango, repetidos, avistadas incoherentes con las exploradas, sala del jugador no explorada, puerta de una salida que no existe) que se rechaza **sin tocar la partida actual**; estado con `conocimiento` ausente (`None`) rechazado por `restaurar`; archivo de la versión anterior rechazado con un mensaje que contiene la versión encontrada y la esperada. Debe fallar primero. (FR-220, FR-221, FR-222)
- [ ] T033 [US6] Agregar a `DTO/EstadoGuardadoDTO.py` `PuertaRecordadaDTO` (`sala`, `direccion` "entero de 0 a 3", `cerrada` booleano) y `ConocimientoGuardadoDTO` (`exploradas` en orden de descubrimiento, `avistadas` en orden ascendente, `puertas` ascendente por sala y dirección, solo las observadas), el campo `conocimiento` **al final** de `EstadoGuardadoDTO` con `None` por defecto (quien lo construye hoy, `AlmacenPartidaBinario` al decodificar y `EstadoGuardadoLogica`, no se rompe; `exportar` siempre lo rellena), y subir `VERSION_ESTADO` a 4 con el comentario de la versión (numeración sujeta a P3). Depende de T032. (FR-220, FR-221)
- [ ] T034 [US6] Implementar en `Logica/MapaConocido.py` `exportar()` (devuelve `ConocimientoGuardadoDTO`; no guarda `version_conocimiento` ni contadores) y `restaurar(dto)` con la validación V1 a V5 (y rechazo de `dto` en `None`) de `contracts/estado-guardado-niebla.md` §3 (`ValueError` con mensaje «conocimiento inválido: …»); deja `version_conocimiento` en 0. La validación ocurre **antes** de modificar nada. Depende de T033. (FR-220)
- [ ] T035 [US6] En `Logica/EstadoGuardadoLogica.py`: `exportar` rellena `conocimiento`; `restaurar` valida el conocimiento junto con el resto **antes** del reemplazo final, construye el `MapaConocido` de la partida restaurada con el auxiliar `_crearMapaYConocimiento` de T010 (compartiendo el `MapaCripta` del campo de costos; sustituye a la llamada actual a `_crearCampoDeCostos`), y lo entrega al `GestorEventos` y al pergamino. El historial del pergamino sigue empezando vacío. Depende de T034 y T010. (FR-220, FR-222)
- [ ] T036 [US6] **Scott**: registrar `ConocimientoGuardadoDTO` y `PuertaRecordadaDTO` en `adaptadores/codec_partida.py` y subir `VERSION_FORMATO` a 7 en `adaptadores/AlmacenPartidaBinario.py` (comentario: «7: conocimiento del jugador (niebla de guerra); 6: anterior»). Entrega firme: 9 de noviembre. Bloqueada por P3. Al terminar, `test_niebla_guardado` debe pasar completa. (FR-220, FR-221, VI)

**Punto de control**: las historias 1 a 6 pasan sus pruebas; guardar y cargar conserva el mapa.

---

## Fase 9: Historia 7 — Niebla determinista, neutral para los enemigos y rápida (P3)

**Meta**: misma cripta, semilla y acciones dan el mismo mapa conocido; la niebla no cambia a los enemigos; consultar, explorar y deshacer cuestan lo esperado, medido con `--bench` incluida la alternativa descartada de cada decisión.

**Prueba independiente**: ejecutar dos veces la misma partida y comparar; ejecutar `--bench mapa` y leer sus secciones.

- [ ] T037 [US7] Crear `test_niebla_determinismo.py` con los escenarios 1 y 2 de la historia 7: la misma partida jugada dos veces produce el mismo conocimiento (estado, puertas y orden de exploradas) en cada instante, con el contenido de las salas descargado y sin descargar; las decisiones, movimientos y activaciones de un enemigo que está en una sala desconocida son idénticas con el conocimiento desactivado (`mapa_conocido` en `None`, ver T012) y activado (FR-213). Debe fallar primero o, si ya cumple, quedar como regresión. (FR-213, FR-222)
- [ ] T038 [US7] Crear `test_niebla_proporcional.py` con los escenarios 3 a 5 de la historia 7 **por conteo, no por tiempo**: en criptas sintéticas de tres tamaños (el mayor 50 veces el menor), con un mapa conocido pequeño y uno grande, `salas_reveladas` y `salidas_examinadas` de una entrada son iguales (sin y con antorcha); cada consulta de estado de sala o de puerta recordada lee exactamente una posición de `estado` o de `puertas` (se comprueba con listas instrumentadas: una subclase de `list` que cuenta las lecturas), con el mapa conocido pequeño y grande y en los tres tamaños (SC-006); deshacer una acción de r cambios revierte exactamente r cambios en los tres tamaños. (FR-223, FR-224, FR-225)
- [ ] T039 [US7] Crear `bench/mapa.py` con las secciones A a H de `contracts/bench-mapa.md` sobre criptas sintéticas deterministas por semilla (`bench/datos.py`, `tests_labs/cripta_sintetica.py`) en tres tamaños (400, 2 000 y 20 000 salas): A consulta (arreglo frente a lista de salas conocidas; criterio duro: una posición leída por consulta); B exploración sin y con antorcha con **criterio duro por conteo** y tiempo solo informativo; C bucle directo frente a `RecorridoPorNiveles` con límite 1 (verificando el mismo conjunto explorado); D orden de las exploradas con k = 50, 500 y 5 000 (ordenar al consultar frente a escanear el arreglo y a mantener la lista ordenada con búsqueda binaria propia, verificando los tres resultados iguales); E reversión de r = 1, 10 y 100 cambios frente a instantánea de arreglos; F observación por aviso frente a sondeo tras cada evento; G búsqueda `BuscadorRutas` sobre la vista frente al mapa materializado; H equivalencia con la referencia. Las alternativas descartadas existen **solo** aquí. Sin `dict`/`set`/`sorted()`. Usa `bench/medicion.py`. (FR-226, VII)
- [ ] T040 [US7] Registrar el bloque `mapa` en `bench/__init__.py` (`BLOQUES`, importación y código de salida distinto de 0 si falla un criterio duro: conteos de B y E, 0 observaciones por evento sin cambio en F, equivalencia en H). Depende de T039. (FR-226)
- [ ] T041 [US7] Repetir con la carga nueva los bloques `ordenamiento` y `inventario` (la vista de la Parte I; sección «Revisión de decisiones de la primera parte» del enunciado) con `python main.py --bench ordenamiento,inventario`, comparar con las cifras de `DOCUMENTACION_DECISIONES_DISENO.md` y anotar el antes y el después en `specs/002-niebla-de-guerra/mediciones.md`. Si una decisión de la Parte I deja de servir, cambiarla y documentarla. Los bloques `retroceso`, `guardado` y `ciclo` los repiten sus responsables; aquí solo se corre `python main.py --bench ciclo` como comprobación informativa de que sigue bajo 20 ms. **Dependencia (constitución VII)**: en `specs/002-niebla-de-guerra/mediciones.md` anotar quién repite `retroceso`, `guardado` y `ciclo` y dónde queda su resultado. Depende de T040. (VII)

**Punto de control**: las siete historias pasan sus pruebas; `python main.py --bench mapa` termina con código 0.

---

## Fase 10: Contrato para «ir a» — vista del conocimiento para `BuscadorRutas`

**Propósito**: entregar la vista que usará la especificación 006. Solo se define y prueba el contrato; el viaje queda fuera. Contrato: `contracts/vista-buscador.md`.

- [ ] T042 [P] Crear `test_vista_conocimiento_buscador.py`: una `BuscadorRutas` real sobre la vista no atraviesa salas no exploradas ni puertas recordadas cerradas o sin observar; el costo hallado coincide con el de un mapa materializado de referencia; `salidas` y `entrantes` devuelven lista vacía para una sala no explorada; el destino debe estar explorado; `version_conocimiento` sube al explorar, al observar y al deshacer y **no** al consultar. Debe fallar primero. (FR-219; contrato 006)
- [ ] T043 Implementar `VistaMapaConocido(mapa_conocido)` en `Logica/MapaConocido.py` con `tamano`, `salidas(sala)`, `entrantes(sala)` y `transitable(arista)` ("verdadero solo si el origen y el destino están explorados y la puerta recordada de esa salida es abierta"), consultando los arreglos sin copiar nada, y exponiendo `version_conocimiento`. No modificar `BuscadorRutas` ni `MapaCripta`. Depende de T042 y T009. (contrato 006)

---

## Fase 11: Cierre y transversales

- [ ] T044 [P] Agregar a `test_mapa_conocido.py` la clase `TestSinProhibidos` que recorre `Logica/MapaConocido.py`, `DTO/ConocimientoDTO.py` y `bench/mapa.py` y falla si encuentra `dict(`, `set(`, `{}` usados como índice, `sorted(`, `.sort(`, `heapq`, `bisect`, `collections`, `networkx`, o la importación de red, disco o vista en el modelo. (I, IV)
- [ ] T045 Crear `tests_labs/escenarios_niebla.py` (`python -m tests_labs.escenarios_niebla`) que reproduzca y grabe en `specs/002-niebla-de-guerra/replays/` un `partida.log` por escenario con el requisito en el nombre, como `FR-208-puerta-recordada-abierta.log`, `FR-210-antorcha-explora-vecinas.log` y `FR-214-pergamino-con-antorcha.log` (los tres del **Apéndice B**), más entrar a una sala nueva (FR-204), avistar por una salida (FR-203), guardar y cargar con niebla (FR-220) y mostrar el mapa (FR-216); comprobar que `--replay` reproduce el mismo conocimiento. Depende de las fases 3 a 9. (IX, FR-222)
- [ ] T046 Escribir `specs/002-niebla-de-guerra/mediciones.md` con los resultados de `python main.py --bench mapa` por sección (elegida y descartada), los criterios duros cumplidos, los límites encontrados y qué resultado cambiaría cada decisión, y la comparación con las evidencias preliminares de `research.md`. Depende de T040. (VII, FR-226)
- [ ] T047 Agregar a `DECISIONES.md` la sección «002 · Niebla de guerra» con enlaces a `spec.md`, `plan.md`, `research.md` y `mediciones.md`, y una tabla de las ocho decisiones indicando si coinciden con el plan original y la medición que las respalda (incluir P1, P2 y P3). Depende de T046. (constitución, flujo obligatorio)
- [ ] T048 Ejecutar `python -m unittest discover` (todas las pruebas, incluidas las de la Parte I, 001 y 005, y `test_puertas_punto_unico`) y el recorrido manual de `quickstart.md` §4; corregir lo que falle. (IX)
- [ ] T049 Revisar la matriz de trazabilidad de `quickstart.md` §5 y la cobertura de este archivo: cada FR-201 a FR-226 con escenario y prueba, sin huecos; registrar el resultado en `specs/002-niebla-de-guerra/checklists/requirements.md` (Notas). Comprobar además que `mediciones.md` deja constancia de la repetición de `retroceso`, `guardado` y `ciclo` por sus responsables; si falta, anotarlo en `DECISIONES.md` como pendiente abierto. Depende de T045 y T048. (IX, VII)

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Fase 1** (Preparación) → bloquea todo.
- **Fase 2** (Fundamentos) → bloquea las fases 3 a 10.
- **Fase 3** (US1) → base de las demás: `entrar` y la construcción del conocimiento.
- **Fase 4** (US2) depende de la 3 (`entrar` se amplía con la observación de puertas).
- **Fase 5** (US3) depende de la 3 y de T018 (mismo `entrar`).
- **Fase 6** (US4) depende de las fases 3, 4 y 5 (revierte los tres tipos de cambio y el caso con antorcha).
- **Fase 7** (US5) depende de la 3 (necesita explorar); puede avanzar en paralelo con las fases 4 a 6 en sus tareas T030 y T028.
- **Fase 8** (US6) depende de la 3 y de que el conocimiento esté completo (fases 3 a 5); T036 es de Scott y depende de P3.
- **Fase 9** (US7) depende de las fases 3 a 6.
- **Fase 10** (vista para «ir a») depende de T009 y T025.
- **Fase 11** (Cierre) depende de todas.

### Dentro de cada historia

- Las pruebas se escriben primero y deben fallar.
- Orden: DTO → estructura/lógica → modelo (`EstadoJuegoLogica`, `GestorEventos`, `PergaminoLogica`) → servicio → controlador/vista.
- Tareas sobre el mismo archivo (`Logica/MapaConocido.py`, `test_mapa_conocido.py`, `Logica/GestorEventos.py`) **no** se marcan [P].

### Oportunidades de paralelismo

- Fase 1: T002 y T003 en paralelo (T004 espera a T003).
- Fase 2: T005, T006 y T008 en paralelo.
- Fase 7: T030 (vista) en paralelo con T028 y T029 (lógica y servicio).
- Fase 10: T042 en paralelo con cualquier tarea de las fases 7 a 9.
- Fase 11: T044 en paralelo con T045.
- Personas distintas: Scott con T036 desde que P3 esté cerrado; quien lleve la vista con T030; quien lleve el conocimiento con T009 a T026.

### Ejemplo de paralelismo (Fase 2)

```text
Tarea: "T005 Prueba de nombres del esqueleto en test_mapa_conocido.py"
Tarea: "T006 SalaMapaDTO.nombre en DTO/MapaDTO.py"
Tarea: "T008 DTO/ConocimientoDTO.py"
```

---

## Estrategia de implementación

### Primero el MVP (historia 1)

1. Fases 1 y 2.
2. Fase 3 (US1): el jugador explora y avista. Detenerse y validar con `python -m unittest test_mapa_conocido`.
3. Añadir las fases 4 (puertas) y 7 (mapa visible) para que el conocimiento ya se pueda consultar; después 5 (antorcha) y 6 (pergamino).

### Entrega incremental

1. Fases 1 a 3: sabe qué ha explorado.
2. Fase 4: recuerda puertas.
3. Fase 7 (puede adelantarse a la 5 y 6): comando `mapa` y pantalla sin fugas.
4. Fases 5 y 6: antorcha y pergamino (Apéndice B completo).
5. Fase 8: guardado (cuando P3 esté cerrado y Scott entregue).
6. Fases 9 a 11: determinismo, mediciones, vista para «ir a» y cierre.

### Fechas del grupo

- 6 de noviembre: el contrato `contracts/cambios-deshacibles.md` y las tareas T025 y T026 deben estar listos para JP y Scott.
- 9 de noviembre: T033 a T036 (guardado) con Scott.

---

## Cobertura de requisitos

| Requisito | Tareas |
|---|---|
| FR-201 | T004, T009, T012 |
| FR-202 | T012, T013, T014, T018 |
| FR-203 | T012, T013, T021, T022 |
| FR-204 | T012, T013, T015 |
| FR-205 | T012, T013 |
| FR-206 | T005, T007, T009, T016 |
| FR-207 | T016, T017, T018, T019, T020 |
| FR-208 | T016, T017, T019 |
| FR-209 | T016, T021, T027, T030 |
| FR-210 | T021, T022, T023 |
| FR-211 | T021, T022 |
| FR-212 | T021, T023 |
| FR-213 | T037 |
| FR-214 | T003, T011, T020, T024, T025, T026 |
| FR-215 | T014, T024 |
| FR-216 | T027, T028, T029, T030, T031 |
| FR-217 | T027, T028 |
| FR-218 | T027, T029, T031 |
| FR-219 | T027, T028, T029, T030, T031, T042 |
| FR-220 | T032, T033, T034, T035, T036 |
| FR-221 | T032, T033, T036 |
| FR-222 | T010, T032, T035, T037, T045 |
| FR-223 | T009, T038, T039 |
| FR-224 | T013, T022, T038, T039 |
| FR-225 | T025, T038, T039 |
| FR-226 | T039, T040, T046 |

Casos del Apéndice B: puerta recordada abierta que está cerrada (T016, T045), antorcha sin activar enemigos ni trampas (T021, T045), pergamino que revierte una entrada con antorcha (T024, T045).
