# Tareas: Comando «ir a»

**Entrada**: documentos de diseño en `specs/006-ir-a/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerrequisitos**: `plan.md` y `spec.md` (con las 3 clarificaciones de la sesión 2026-11-11: paradas por peligro, desempate por posición y registro del viaje). La capacidad 002 integrada (formato 8, estado 5).

**Pruebas**: se incluyen en todas las historias porque la constitución (principio IX) exige que cada escenario de aceptación tenga una prueba automatizada o un `partida.log` que cite su requisito. Cada prueba se escribe **antes** del código y debe fallar primero por la razón correcta.

**Organización**: tareas agrupadas por historia de usuario. Cada tarea indica entre paréntesis los requisitos que atiende. Las historias 1 a 4 son P1 y las 5 y 6 son P2. La historia 1 es el MVP: un viaje completo hasta una sala explorada.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencia de tareas incompletas).
- **[USn]**: historia de `spec.md` a la que pertenece.
- Las rutas son relativas a la raíz del repositorio. Las pruebas siguen la convención del repositorio (`unittest`, archivos `test_*.py` en la raíz, ayudas en `tests_labs/`).

## Reglas para todas las tareas (constitución)

- **No usar** `dict` ni `set` como índice, caché o tabla de búsqueda; ni `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` ni bibliotecas de grafos; **ni `sorted()` ni `list.sort()`** (el orden sale de `ordenar_adaptativo`/`insertion_sort` de `Logica/ordenamiento.py`).
- **No modificar** `Logica/BuscadorRutas.py`, `Logica/MapaConocido.py` (ni `VistaMapaConocido`), `Logica/MapaCripta.py`, `Logica/RetrocesoLogica.py` ni `Logica/PuertasLogica.py`, salvo que una medición de `--bench ir_a` lo exija; en ese caso se documenta el antes y el después en `DECISIONES.md` antes de tocarlos. El único punto de cambio de puertas sigue siendo `PuertasLogica.fijar_cerrada`.
- Ningún id de sala o entidad, cantidad, presupuesto ni nombre de una cripta concreta en el código. Los ids de las pruebas salen de criptas sintéticas.
- El modelo (`Logica/`, `DTO/`) no importa red, disco ni vista.
- **Un paso de «ir a» es un movimiento normal**: se entrega a `accionJugador` como `MOVER_JUGADOR`. `ViajeLogica` no mueve al jugador, no avanza el reloj, no activa trampas ni explora salas por su cuenta.
- La ruta solo usa el conocimiento (`VistaMapaConocido`); nunca el estado real de las puertas ni el contenido de salas no visitadas. No llama a `construir_sala` ni descarga contenido para decidir (FR-248).
- Los commits de especificación van **antes** y **separados** de los de código (principio X). El registro de prompts lo lleva el grupo en `PROMPTS_LLM_Fer.md`; no escribir en `PROMPTS_LLM.md`.

---

## Fase 1: Preparación

**Propósito**: revisar contra la constitución, corregir la especificación antes del código y dejar listo el material de pruebas. Bloquea todo lo demás.

- [X] T001 Revisar `plan.md` y este `tasks.md` contra la lista de prohibidos del principio I y anotar el resultado en `specs/006-ir-a/checklists/requirements.md` (sección Notas). (I)
- [X] T002 Corregir en `specs/006-ir-a/spec.md` la última oración de FR-252 por «La reproducción DEBE reproducir el mismo viaje paso a paso y comprobar que su resultado coincide con el registrado.», según `research.md` D6. Confirmación **separada** y anterior a cualquier confirmación de código. (FR-252, X)
- [X] T003 [P] Crear `tests_labs/escenarios_ir_a.py` con las criptas de prueba del viaje, reutilizando `esqueleto_rejilla` y `mapa_dto_desde_esqueleto` de `tests_labs/cripta_sintetica.py` y los casos B-N1, B-N2, B-N3 y B-N6 de `CASOS_APENDICE_B` en `tests_labs/api_falsa.py` (sin modificarlos): (a) dos rutas de distinto costo hacia una misma sala, (b) un diamante con rutas de igual costo, (c) una cadena larga con una puerta de cierre automático con y sin ruta alterna, (d) una sala intermedia y un destino con enemigos dormidos, (e) un enemigo ya activo y una trampa que daña. Cada constructor recibe la semilla. Sin red ni ids de la cripta real. (FR-231 a FR-249)
- [X] T004 [P] Crear `tests_labs/referencia_viaje.py` con las **referencias ingenuas**: (1) `caminar_a_mano(servicio, salas)` que ejecuta la ruta como movimientos individuales por `accionJugador`; (2) `ruta_minima_lexicografica(esqueleto, origen, destino, abiertas)` que enumera todas las rutas de menor costo y devuelve la de menor lista de ids (solo para criptas pequeñas); (3) `resumen_estado(servicio)` con sala, reloj, vida, conocimiento y salas cargadas, para comparar estados. Sin `dict`/`set`/`sorted()`. (FR-234, FR-236, III)

**Punto de control**: material de pruebas listo; `spec.md` corregido; el análisis contra el principio I está registrado.

---

## Fase 2: Fundamentos (bloquea todas las historias)

**Propósito**: el resultado del viaje, los contadores de la lógica y el esqueleto del orquestador existen y están conectados al servicio. Sin esto ninguna historia puede probarse.

- [X] T005 [P] Crear `DTO/ResultadoViajeDTO.py` con `ResultadoViajeDTO` según `data-model.md` (`estado`, `motivo`, `mensaje`, `sala_final`, `pasos`, `tiempo`, `recorrido`) y las constantes de estado (`EN_CURSO`, `LLEGADO`, `DETENIDO`, `RECHAZADO`) y de motivo (`DESTINO_INEXISTENTE`, `NO_EXPLORADO`, `SIN_RUTA_INICIAL`, `YA_ESTAS_ALLI`, `SIN_RUTA`, `ENEMIGOS_DORMIDOS`, `ENEMIGO_ACTIVO`, `DANO`, `MUERTE`, `PERGAMINO`, `MOVIMIENTO_RECHAZADO`, `CANCELADO_POR_JUGADOR`) con el texto de cada uno tal como figura en `data-model.md`. Datos simples, sin comportamiento. `recorrido` es una lista. (data-model)
- [X] T006 Agregar a `Logica/EstadoJuegoLogica.py` los atributos de ejecución `viaje_activo = None` y `activaciones_enemigos = 0`; subir `activaciones_enemigos` en 1 por cada enemigo que despierta `_activarEnemigos`; dejar `viaje_activo = None` en `iniciarJuego`, `restaurar_estado` y `restaurarDesdePuntoControl`. Ninguno se exporta al estado guardado ni se deshace. Depende de T005. (D4, D8, FR-243)
- [X] T007 Crear `Logica/ViajeLogica.py` con la clase `ViajeLogica` y los campos de `data-model.md` (`destino`, `estado`, `motivo`, `pasos`, `tiempo`, `version_vista`, `buscador`, `vista`, `recorrido`). El constructor recibe la lógica del juego, crea un `BuscadorRutas` y usa la `VistaMapaConocido` de su `mapaConocido`. Declara `iniciar(destino)`, `avanzar()`, `ejecutar()` y `cancelar(motivo)` con sus firmas de `contracts/viaje-logica.md` (cuerpos en las historias). Sin importar red, disco ni vista. Depende de T005. (D2, contracts/viaje-logica.md)
- [X] T008 Agregar a `Logica/EstadoJuegoLogica.py` los métodos `iniciarViaje(destino)`, `avanzarViaje()`, `ejecutarViaje()` y `cancelarViaje()`, que crean o usan `ViajeLogica` y guardan `viaje_activo`; si la cripta no entrega esqueleto (`mapaConocido is None`) lanzan `ValueError` como `instantaneaMapaConocido`. Agregar en `Servicio/EstadoJuegoServicio.py` `irA(destino)`, `iniciarViaje(destino)`, `avanzarViaje()` y `cancelarViaje()` que solo delegan. Depende de T006 y T007. (FR-231, contracts/viaje-logica.md §5)

**Punto de control**: el modelo y el servicio exponen el viaje (aún sin comportamiento); la Parte I y las capacidades 001 a 009 siguen pasando sus pruebas (`python -m unittest discover -p "test_*.py"`).

---

## Fase 3: Historia 1 — Viajar a una sala explorada por la ruta más barata (P1) 🎯 MVP

**Meta**: «ir a <id>» lleva al jugador hasta una sala explorada por la ruta de menor costo que conoce, un paso por vez, con el mismo efecto que caminarla a mano.

**Prueba independiente**: en una cripta pequeña con dos caminos de distinto costo, ejecutar «ir a» y comprobar la secuencia de salas, el tiempo consumido y que el estado final es el de caminar la misma ruta a mano.

### Pruebas de la Historia 1 (escribirlas primero; deben fallar)

- [X] T009 [P] [US1] Escribir en `test_viaje_ruta.py` (archivo nuevo) la clase `TestRutaMasBarata`: con dos rutas de distinto costo recorre la menor y el reloj avanza la suma de los costos (escenario 1; FR-231 a FR-233); con un diamante de igual costo elige la ruta de menor id en la primera posición en que difieren y coincide con `ruta_minima_lexicografica` (escenario 2; FR-234); «ir a» la sala actual devuelve `YA_ESTAS_ALLI` sin mover ni consumir tiempo (escenario 3; FR-231); una puerta recordada cerrada y una «sin observar» no se usan como paso (escenario 4; FR-235); un destino explorado solo por la antorcha es válido (caso límite; FR-231); una sala solo avistada en la ruta no se usa como paso (SC-206; C10). Usa `tests_labs/escenarios_ir_a.py`. (FR-231 a FR-236)
- [X] T010 [P] [US1] Escribir en `test_viaje_equivalencia.py` (archivo nuevo) la clase `TestViajeEsCaminar`: tras un viaje completo, sala, reloj, vida, conocimiento y salas cargadas son idénticos a los de caminar la misma ruta a mano con `caminar_a_mano`; el viaje deja un nodo del historial del pergamino por paso (escenario 5; FR-233, FR-236, FR-244). (FR-233, FR-236)
- [X] T011 [P] [US1] Escribir en `test_viaje_comando.py` (archivo nuevo) la clase `TestComandoIrA`: con entradas simuladas, `ir a <id>` de una sala explorada llama al servicio, imprime «Llegaste a la sala N tras P pasos (tiempo T).» y el siguiente turno muestra la sala nueva; las mayúsculas y los espacios sobrantes no importan. Sin pruebas del rechazo (van en la Historia 2). (FR-231, contracts/comando-ir-a.md)

### Implementación de la Historia 1

- [X] T012 [US1] En `Logica/ViajeLogica.py` implementar `iniciar(destino)` para el camino feliz: calcula el campo con `buscador.distancias_hacia(destino, vista, LIMITE_SIN_COTA)` (constante grande propia, sin literales de cripta), guarda `version_vista`, pone `estado = EN_CURSO` y `recorrido = []`. Sin comprobaciones de rechazo todavía (Historia 2). Depende de T007. (FR-232, FR-235, D1)
- [X] T013 [US1] En `Logica/ViajeLogica.py` implementar `avanzar()` y `ejecutar()` para el camino feliz: `arista = buscador.siguiente_paso(sala_actual)`; arma el mismo `EventoDTO(costo de la salida, 0, jugador, "MOVER_JUGADOR", [sala_actual, dirección])` que el controlador y lo entrega a `accionJugador`; llama a `ingresarEnSala(sala nueva)`; anota la sala en `recorrido` y sube `pasos`; `tiempo` es la diferencia del reloj. Si la sala nueva es el destino, `estado = LLEGADO`. Devuelve `ResultadoViajeDTO`. No mueve, no avanza el reloj ni explora por su cuenta. Depende de T012. (FR-233, FR-234, FR-236, D2)
- [X] T014 [US1] En `Controlador/ControladorJuego.py` reconocer `ir a <id>` **antes** de `_mapear_entrada_a_evento` (como `mapa` e `historia`): interpreta el id entero, llama a `servicio.irA(destino)` y pasa el resultado a la vista; un id no entero imprime «El destino debe ser el número de una sala.» sin llamar al servicio; agregar `ir a <sala>` al texto de ayuda. En `Controlador/Vista.py` agregar `mostrar_viaje(resultado)` con las salidas de `contracts/comando-ir-a.md` §3. La vista solo imprime. Depende de T013. (FR-231, contracts/comando-ir-a.md)

**Punto de control**: T009, T010 y T011 pasan; el viaje completo funciona de punta a punta en consola. MVP.

---

## Fase 4: Historia 2 — Rechazo sin costo (P1)

**Meta**: si el destino no se puede alcanzar con lo que el jugador sabe, el comando se rechaza de inmediato con un motivo claro y la partida queda exactamente igual (B-N1).

**Prueba independiente**: pedir «ir a» una sala avistada, una desconocida, una inexistente y una explorada sin ruta conocida, y comprobar que reloj, conocimiento, log y pergamino no cambian.

### Pruebas de la Historia 2 (escribirlas primero; deben fallar)

- [X] T015 [P] [US2] Escribir en `test_viaje_rechazo.py` (archivo nuevo) la clase `TestRechazoSinCosto`: **B-N1** (sala avistada y desconocida → `NO_EXPLORADO`; escenario 1), explorada sin ruta conocida (→ `SIN_RUTA_INICIAL`; escenario 2) e id inexistente (→ `DESTINO_INEXISTENTE`; escenario 3). En los tres: el reloj, el conocimiento, `acciones_linea_tiempo`, el log y `partida.log` quedan idénticos y no se escribe la marca `IR_A`; un pergamino posterior deshace la acción anterior al rechazo y no el rechazo (escenario 4). Construye el caso con el constructor B-N1 de `tests_labs/api_falsa.py`. (FR-237, FR-238)
- [X] T016 [P] [US2] Agregar a `test_viaje_comando.py` la clase `TestComandoRechazado`: `ir a <sala no explorada>` imprime el motivo y el reloj queda igual; `ir a x` no llama al servicio. (FR-237, FR-238, B-N1)

### Implementación de la Historia 2

- [X] T017 [US2] En `Logica/ViajeLogica.py` completar `iniciar(destino)` con las comprobaciones de `contracts/viaje-logica.md` §2, en ese orden y **antes de tocar nada**: juego iniciado y no terminado; `destino` entero dentro de la cripta (`DESTINO_INEXISTENTE`); estado del destino *explorada* (`NO_EXPLORADO`); destino distinto de la sala actual (`YA_ESTAS_ALLI`); `costo(sala_actual)` distinto de `None` con el campo calculado (`SIN_RUTA_INICIAL`). Un rechazo devuelve `RECHAZADO` con su mensaje, deja `viaje_activo = None` y no escribe ni avanza nada. Depende de T012. (FR-237, FR-238)
- [X] T018 [US2] En `Controlador/Vista.py` y `Controlador/ControladorJuego.py` mostrar los mensajes de rechazo en una sola línea y no repetir el bloque de la sala; el turno siguiente sigue igual. Depende de T017 y T014. (FR-237, contracts/comando-ir-a.md §3)

**Punto de control**: T015 y T016 pasan; B-N1 verificado.

---

## Fase 5: Historia 3 — Una puerta recordada abierta resulta cerrada (P1)

**Meta**: el viaje descubre al llegar a una sala que una puerta recordada abierta está cerrada, actualiza el mapa, recalcula la ruta y, si no queda ninguna, se detiene sin consumir tiempo adicional (B-N2).

**Prueba independiente**: abrir una puerta con cierre automático, alejarse hasta que se cierre y pedir un viaje cuya ruta más barata la usa; comprobar la actualización del mapa y la nueva ruta o la detención.

### Pruebas de la Historia 3 (escribirlas primero; deben fallar)

- [X] T019 [P] [US3] Escribir en `test_viaje_puerta_cerrada.py` (archivo nuevo) la clase `TestPuertaRecordadaAbierta`: con ruta alterna, el viaje llega a la sala de la puerta, el mapa recuerda la puerta cerrada, la ruta se recalcula desde esa sala y llega por la alterna (escenario 1); **B-N2** sin alterna, el viaje se detiene en esa sala con `SIN_RUTA`, el mapa queda actualizado y el reloj no avanza por el paso no dado (escenario 2); un nuevo «ir a» al mismo destino se rechaza con `SIN_RUTA_INICIAL` (escenario 3); una puerta recordada abierta que sigue abierta no provoca recálculo ni detención (escenario 4). Construye el caso con el constructor B-N2 de `tests_labs/api_falsa.py`. (FR-239 a FR-241, FR-237)
- [X] T020 [P] [US3] Agregar a `test_viaje_equivalencia.py` la clase `TestReusoDelCampo`: en viajes con puertas que cambian, cierre automático y entrada a salas ya exploradas, la decisión de cada paso con el campo reutilizado (recálculo solo si `version_conocimiento` cambió) es idéntica a recalcular desde cero antes de cada paso; y sin cambios de conocimiento no hay ningún recálculo (contador de `salas_fijadas` del buscador). (III, D3)

### Implementación de la Historia 3

- [X] T021 [US3] En `Logica/ViajeLogica.py` completar `avanzar()` con el paso 2 y 3 de `contracts/viaje-logica.md` §3: antes de cada paso compara `version_conocimiento` con `version_vista` y, si difiere, recalcula el campo y actualiza `version_vista`; si `costo(sala_actual)` es `None`, pasa a `DETENIDO(SIN_RUTA)` **sin llamar a `accionJugador`** (sin tiempo, sin acción, sin registro de paso). Si el gestor rechaza el movimiento, `DETENIDO(MOVIMIENTO_RECHAZADO)` sin tiempo. Depende de T013. (FR-239 a FR-241, D3)

**Punto de control**: T019 y T020 pasan; B-N2 verificado.

---

## Fase 6: Historia 4 — Peligro y pergamino detienen el viaje (P1)

**Meta**: el viaje se detiene al despertar enemigos dormidos, ante un enemigo activo, al recibir daño o al morir; y un pergamino revierte solo el último paso y cancela el viaje (B-N3 y B-N6).

**Prueba independiente**: preparar una ruta que atraviesa una sala con enemigos dormidos y comprobar activación y detención; en otro viaje, usar el pergamino a mitad y comprobar el estado.

### Pruebas de la Historia 4 (escribirlas primero; deben fallar)

- [X] T022 [P] [US4] Escribir en `test_viaje_enemigos.py` (archivo nuevo) la clase `TestDetencionPorPeligro`: **B-N3** al entrar a una sala intermedia con enemigos dormidos, estos se activan exactamente como en una entrada a mano (mismas activaciones, mismos números de secuencia, misma agenda; comparado con `caminar_a_mano`) y el viaje se detiene allí (escenario 1); si esa sala es el destino, se activan y el viaje termina en `LLEGADO` (escenario 2); una sala sin enemigos dormidos no detiene (escenario 5); un enemigo ya activo en la sala → `ENEMIGO_ACTIVO`; daño de una trampa → `DANO`; muerte → `MUERTE` y fin de partida. Usa el constructor B-N3 de `tests_labs/api_falsa.py` y `escenarios_ir_a.py`. (FR-242, FR-243, FR-249)
- [X] T023 [P] [US4] Escribir en `test_viaje_pergamino.py` (archivo nuevo) la clase `TestPergaminoEnViaje`: **B-N6** con la API paso a paso (`iniciarViaje`/`avanzarViaje`), tras varios pasos usar el pergamino revierte únicamente el último paso (sala, reloj, conocimiento y activaciones de ese paso) y el viaje queda `DETENIDO(PERGAMINO)` sin continuar (escenarios 3; FR-244, FR-245); un segundo pergamino revierte el paso anterior, uno por uso, dentro del máximo de 5 acciones (escenario 4); tras un viaje terminado, un pergamino revierte el último paso sin cancelar nada; con el viaje aceptado y 0 pasos dados, el pergamino cancela el viaje (`DETENIDO(PERGAMINO)`), deja `IR_A` y el registro del pergamino antes de `FIN_IR_A` y deshace la acción anterior al comando (caso límite; C5). Usa el constructor B-N6 de `tests_labs/api_falsa.py`. (FR-244, FR-245)

### Implementación de la Historia 4

- [X] T024 [US4] En `Logica/ViajeLogica.py` completar `avanzar()` con la evaluación de detención tras cada paso, en el orden de `research.md` D4: guarda la vida y `activaciones_enemigos` **antes** del paso; después de `accionJugador` e `ingresarEnSala` evalúa MUERTE (`fin`), LLEGADA (sala = destino, aunque se hayan activado enemigos), DANO (vida menor que antes), ENEMIGOS_DORMIDOS (el contador subió) y ENEMIGO_ACTIVO (algún enemigo vivo y activo en la sala actual, recorriendo solo los enemigos de esa sala). Cada detención pone su motivo y su mensaje. Depende de T021. (FR-242, FR-243, FR-249, D4)
- [X] T025 [US4] En `Logica/EstadoJuegoLogica.py`, dentro de `accionJugador`, justo después de `_registrarAccionEnLog` del uso de pergamino y antes del `return` de esa rama (la de `GestorEventos.es_uso_de_pergamino`), y solo si el pergamino tuvo éxito (no en el camino en que no hay nada que deshacer; C3), llamar a `self.viaje_activo.cancelar("PERGAMINO")` si hay un viaje `EN_CURSO` y dejar `viaje_activo = None`. `ViajeLogica.cancelar(motivo)` pasa a `DETENIDO(motivo)`, no hace nada si el viaje ya terminó y no recalcula. Depende de T024. (FR-244, FR-245, D5)

**Punto de control**: T022 y T023 pasan; B-N3 y B-N6 verificados.

---

## Fase 7: Historia 5 — Antorcha encendida durante el viaje (P2)

**Meta**: con la antorcha encendida, cada entrada del viaje explora las vecinas igual que una entrada a mano, y las salas nuevas sirven para recalcular la ruta.

**Prueba independiente**: encender la antorcha, viajar por varias salas y comparar el mapa conocido final con el de caminar a mano la misma ruta.

- [X] T026 [P] [US5] Escribir en `test_viaje_antorcha.py` (archivo nuevo) la clase `TestViajeConAntorcha`: con la antorcha encendida, el mapa conocido tras el viaje es idéntico al de caminar a mano la misma ruta; las vecinas se exploran sin activar enemigos ni trampas (escenario 1; FR-246, FR-211); tras una puerta cerrada, el recálculo puede usar salas recién exploradas por la antorcha (escenario 2); si la antorcha se apaga a mitad de un viaje (API paso a paso), las entradas posteriores exploran según su estado en el instante de cada entrada (escenario 3). (FR-246)
- [X] T027 [US5] Si T026 revela una diferencia con caminar a mano, corregirla en `Logica/ViajeLogica.py` (la antorcha actúa dentro de `MapaConocido.entrar` llamado por el gestor; el viaje no debe duplicarlo). Si T026 pasa sin cambios, dejar constancia en `specs/006-ir-a/checklists/requirements.md` (Notas) de que la historia 5 se cumple por construcción del paso. Depende de T026. (FR-246)

**Punto de control**: T026 pasa.

---

## Fase 8: Historia 6 — Viaje reproducible y registrado (P2)

**Meta**: la misma cripta, semilla y acciones producen el mismo viaje, con o sin contenido descargado; el log lleva la orden, los pasos y el resultado, y la reproducción es fiel.

**Prueba independiente**: ejecutar dos veces la misma partida con «ir a» y comparar `partida.log`; repetir con y sin contenido descargado; repetir el log y verificar el estado.

### Pruebas de la Historia 6 (escribirlas primero; deben fallar)

- [X] T028 [P] [US6] Escribir en `test_viaje_determinismo.py` (archivo nuevo) la clase `TestDeterminismoDelViaje`: dos ejecuciones idénticas dan el mismo recorrido, tiempo, mapa conocido y `partida.log` (escenario 1; FR-247); guardar y cargar a mitad de la partida y repetir el mismo «ir a» da el mismo resultado (escenario 2); el cálculo de la ruta da lo mismo con el contenido de las salas del trayecto descargado y sin descargar, y no pide descargas nuevas (escenario 3; FR-248). (FR-247, FR-248, II)
- [X] T029 [P] [US6] Escribir en `test_viaje_registro.py` (archivo nuevo) la clase `TestRegistroDelViaje`: el log de un viaje lleva exactamente `IR_A` (destino), los `MOVER_JUGADOR` de los pasos y `FIN_IR_A` (estado, motivo, sala final), en ese orden y con costo 0 en las marcas; un rechazo no escribe nada; un viaje cancelado por pergamino deja el registro del pergamino antes de `FIN_IR_A`; repetir el log da el mismo estado; un `FIN_IR_A` con sala final distinta falla con «La reproducción no es fiel»; `historia #k` y `replay hasta` a mitad de un viaje dan el estado de caminar a mano esos pasos; guardar y cargar con un viaje ya hecho no cambia el formato (formato 8, estado 5). Incluye un viaje que termina en una sala con enemigos dormidos (B-N3): repetir el log da el mismo estado, con los enemigos ya activados, que el viaje en vivo (C2). (FR-252, D6, D8)
- [X] T030 [P] [US6] Escribir en `test_viaje_sin_red.py` (archivo nuevo) la clase `TestViajeSinRed`: con el cliente falso contador de solicitudes, un viaje completo no hace ninguna solicitud adicional a las de caminar a mano la misma ruta (el presupuesto no cambia). (FR-248, VI)

### Implementación de la Historia 6

- [X] T031 [US6] En `Logica/LogEventos.py` agregar `TIPOS_MARCA_VIAJE = ("IR_A", "FIN_IR_A")` y `registrar_marca(tipo, datos_extra)` que agrega un registro JSON con `tiempo_ejecucion` 0, actor `{"tipo": "jugador"}` y los datos, con el mismo estilo que `registrar_cursor`; sin tocar los demás métodos. Depende de T029. (FR-252, contracts/registro-viaje.md §1)
- [X] T032 [US6] En `Logica/EstadoJuegoLogica.py` agregar el auxiliar `_registrarMarcaViaje(tipo, datos)` que llama a `logEventos.registrar_marca` y envía la línea al `registrador_log` por la misma ruta que `_registrarAccionEnLog`; y en `Logica/ViajeLogica.py` escribir `IR_A` al aceptar la orden (después de las comprobaciones de rechazo) y `FIN_IR_A` (estado, motivo o «ninguno», sala final) al llegar, detenerse o cancelarse. Depende de T031 y T017. (FR-252, D6)
- [X] T033 [US6] En `Logica/EstadoJuegoLogica.py` hacer que los cuatro puntos que hoy comparan con `TIPOS_CURSOR_INVENTARIO` (`_planificarSegmento`, `_ejecutarPasada2` y los dos bucles de `_repetirPartidaInterno`) reconozcan también `TIPOS_MARCA_VIAJE` y la salten sin ejecutar ni contar (un `continue`); importar la constante desde `Logica/LogEventos.py`. Depende de T031. (FR-252, contracts/registro-viaje.md §2)
- [X] T034 [US6] En `Logica/EstadoJuegoLogica.py` hacer que la repetición completa y la repetición hasta un instante o acción, al llegar a `FIN_IR_A`, comprueben que `jugador.id_sala_actual` es la sala final anotada y, si no, lancen `ValueError("La reproducción no es fiel: ...")`; la repetición hasta un instante no comprueba si se corta antes de esa marca. Antes de comprobar, la repetición llama a `ingresarEnSala` con la sala actual al procesar `FIN_IR_A`: en vivo el viaje lo hace tras cada paso, incluido el último, y en la repetición solo se llama antes del siguiente movimiento, así que sin esta llamada los enemigos dormidos de la sala final no se activarían (hallazgo C2 de `analyze`). **Implementado así**: no hizo falta esa llamada, porque los enemigos dormidos se activan dentro del movimiento (`cargar_sala`) y no al pedir la sala (research D4). Depende de T033. (FR-252, D6)

**Punto de control**: T028, T029 y T030 pasan; el `partida.log` de un viaje se repite fielmente.

---

## Fase 9: Rendimiento y mediciones (`--bench ir_a`)

**Propósito**: respaldar con datos FR-250 y FR-251 y la alternativa descartada de cada decisión (constitución VII). Bloque nuevo, criptas sintéticas deterministas por semilla, sin red ni vista. Contrato: `contracts/bench-ir-a.md`.

- [X] T035 [P] Crear `bench/ir_a.py` con el esqueleto del bloque (constantes `SECCION_A` a `SECCION_H`, tamaños 400, 2 000 y 20 000 salas, mediana de 7 repeticiones con `bench/medicion.py`, función `ejecutar(filas)` que devuelve `True` si cumple) y el armado de las criptas con `esqueleto_rejilla` y `bench/juego.py`. Sin `dict`/`set`/`sorted()`. (FR-251, VII)
- [X] T036 Agregar a `bench/ir_a.py` la sección A (ruta): campo + recorrido de un viaje frente a la alternativa **enumerar rutas óptimas y comparar lista a lista** (solo existe aquí); verificación previa de que ambas dan la misma lista; informar el número de rutas enumeradas y la razón de tiempos. Depende de T035 y T013. (D1)
- [X] T037 Agregar a `bench/ir_a.py` la sección B (paso por el flujo normal): un paso completo frente a un camino propio que solo mueve y avanza el reloj (solo existe aquí); **criterio duro**: caminar a mano y viajar dejan el mismo estado. Depende de T036. (D2)
- [X] T038 Agregar a `bench/ir_a.py` la sección C (recálculo): recálculos y salas fijadas por viaje con las tres políticas (cada paso, solo si cambia la versión, y con `limite` igual al costo restante de la ruta vigente cuando sigue válida). **Criterio duro**: la política B recalcula 0 veces sin cambios de conocimiento y las decisiones de B y C coinciden con las de recalcular cada paso. **Implementado así**: la política adoptada es B con cota de costo (T042); decide igual que recalcular en cada paso (sección H). Depende de T037 y T021. (D3)
- [X] T039 Agregar a `bench/ir_a.py` las secciones D (detención con 0, 10 y 100 enemigos frente a revisar el contenido de las salas de la ruta; **duro**: crece con los enemigos de la sala, no con V), E (revertir un paso con y sin antorcha; **duro**: cambios revertidos = cambios del paso) y F (escribir las marcas y repetir viajes de 10, 100 y 1 000 pasos frente a repetir sin marcas; **duro**: diferencia constante de 2 registros). Depende de T038, T025 y T034. (D4, D5, D6)
- [X] T040 Agregar a `bench/ir_a.py` la sección G (**paso, peor caso**): antorcha encendida, destino lejano, 10 % explorado y un paso que descubre una puerta cerrada y recalcula sin límite; **criterio duro**: mediana y máximo ≤ 5 ms por paso en los tres tamaños. **Implementado así**: criterio duro en 400 y 2 000 salas; en 20 000 se informa (FR-251). Y la sección H (equivalencia: política B frente a recalcular desde cero en cada paso, con y sin antorcha, puertas que cambian y pergamino; 100 % idénticas). Depende de T039. (FR-250, III)
- [X] T041 Registrar el bloque en `bench/__init__.py` (`("ir_a", ir_a.ejecutar)` en `BLOQUES`), su criterio de salida (código 1 si G supera 5 ms o falla cualquier verificación) y la línea de cierre «Ir a (paso ≤ 5 ms y equivalencias): CUMPLE / NO CUMPLE». Depende de T040. (FR-251)
- [X] T042 Ejecutar `python main.py --bench ir_a`. Si G supera 5 ms con la política B, adoptar la política C en `Logica/ViajeLogica.py` (recálculo con `limite` = costo restante de la ruta vigente solo si ninguna salida pendiente dejó de ser transitable; sin límite cuando una puerta se cerró) usando el parámetro `limite` que ya existe, sin modificar `BuscadorRutas`, y volver a medir. Anotar en `DECISIONES.md` las cifras (antes y después) y la política elegida. Si aún supera 5 ms, informarlo como defecto y no continuar. Depende de T041. (FR-250, VII)
- [X] T050 Agregar a `bench/ir_a.py` la sección I (**paso con el mapa conocido completo**, enunciado §6.1): todas las salas exploradas, antorcha encendida, con y sin una puerta cerrada en la ruta, en 400, 2 000 y 20 000 salas; **criterio duro** en 400 salas (el máximo de las medianas por paso ≤ 5 ms); en 2 000 y 20 000 se informa sin ocultarlo. Depende de T040. (FR-250, FR-251)
- [X] T043 Ejecutar de forma informativa `python main.py --bench mapa`, `--bench retroceso`, `--bench ciclo` y `--bench ordenamiento` con la carga nueva (el contrato de `--bench ir_a` solo lista mapa, retroceso y ciclo; ordenamiento se mide aquí por la constitución VII; C8) y anotar en `DECISIONES.md` si alguna decisión de la Parte I o de la 002 deja de servir (el ciclo debe seguir bajo 20 ms). Depende de T042. (VII)

**Punto de control**: `--bench ir_a` en CUMPLE; las cifras y la política elegida están en `DECISIONES.md`.

---

## Fase 10: Cierre y transversales

**Propósito**: verificar la constitución, la trazabilidad y que nada de lo anterior se rompió.

- [X] T044 [P] Buscar en `Logica/ViajeLogica.py`, `DTO/ResultadoViajeDTO.py`, `bench/ir_a.py` y los cambios de `Logica/EstadoJuegoLogica.py` y `Logica/LogEventos.py` los usos prohibidos (`dict`/`set` como índice, `heapq`, `bisect`, `collections`, `networkx`, `sorted(`, `.sort(`) e imports de red, disco o vista en el modelo; y los literales de la cripta de desarrollo. Anotar el resultado en `specs/006-ir-a/checklists/requirements.md` (Notas). (I, IV, V)
- [X] T045 [P] Documentar el comando `ir a <id>` en `README.md` y las decisiones D1 a D8 (alternativas y cifras de `--bench ir_a`) en `DOCUMENTACION_DECISIONES_DISENO.md`; actualizar `tests_labs/api_falsa.py` solo si el contrato de la 009 pide documentar que los pasos `("ir_a", sala)` y `("pergamino",)` ya se ejecutan (sin cambiar su firma ni sus casos). (VIII)
- [X] T046 Construir la tabla requisito → escenario → prueba en `specs/006-ir-a/checklists/requirements.md`: cada FR-231 a FR-252 y cada caso B-N1, B-N2, B-N3 y B-N6 con su prueba, sin huecos; si algún requisito queda sin prueba, agregarla. (IX)
- [X] T047 Ejecutar `python -m unittest discover -p "test_*.py"` y comprobar que todo pasa (pruebas anteriores más las nuevas `test_viaje_*.py`), y los laboratorios `python -m tests_labs.<nombre>` de la línea base (`prueba_cliente_persistente`, `prueba_cliente_offline`, `prueba_fabrica`, `prueba_precarga_presupuesto`, `prueba_almacen_disco`, `prueba_cliente_http_errores`), que deben seguir iguales. No ejecutar `prueba_cliente_http`, `prueba_servicio` ni `python -m tests_labs.escenarios_terreno`. (VI)
- [X] T048 Recorrer `specs/006-ir-a/quickstart.md` de punta a punta (pruebas, casos del Apéndice B, determinismo, `--bench ir_a` y la prueba manual en consola) y anotar en `checklists/requirements.md` lo observado. Depende de T047. (SC-201 a SC-206)
- [X] T049 Registrar en `PROMPTS_LLM_Fer.md` (no en `PROMPTS_LLM.md`) los comandos `/speckit-specify`, `/speckit-clarify`, `/speckit-plan` y `/speckit-tasks` de esta capacidad con su texto, la herramienta y el modelo. (XI)

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Fase 1** (Preparación): sin dependencias; bloquea todo.
- **Fase 2** (Fundamentos): depende de la Fase 1; **bloquea todas las historias**.
- **Fases 3 a 8** (Historias 1 a 6): dependen de la Fase 2. Orden de prioridad: 1 → 2 → 3 → 4 (P1) y luego 5 → 6 (P2).
- **Fase 9** (Rendimiento): depende de que existan las historias que mide (T013, T021, T025, T034).
- **Fase 10** (Cierre): depende de todo lo anterior.

### Dependencias entre historias

- **US1** (MVP): solo la Fase 2.
- **US2**: sobre `iniciar` de US1 (T012); no depende de US3 a US6.
- **US3**: sobre `avanzar` de US1 (T013).
- **US4**: sobre `avanzar` de US3 (T021), porque ambas editan el mismo método; las pruebas T022 y T023 pueden escribirse antes.
- **US5**: sin código propio esperado; depende de US1 y US3 para su prueba de recálculo.
- **US6**: sobre US1 y US2 (marca `IR_A` después del rechazo) y US4 (cancelación por pergamino).

### Dentro de cada historia

- Las pruebas se escriben primero y deben fallar; después la implementación; las tareas sin [P] sobre el mismo archivo van en el orden indicado.

### Oportunidades de paralelismo

- **Fase 1**: T003 y T004 [P].
- **Fase 2**: T005 [P]; T006 y T007 dependen de T005 y pueden hacerse a la vez (archivos distintos).
- **US1**: T009, T010 y T011 [P] (tres archivos de prueba).
- **US2**: T015 y T016 [P].
- **US3**: T019 y T020 [P].
- **US4**: T022 y T023 [P].
- **US6**: T028, T029 y T030 [P].
- **Fase 9**: T035 [P] con cualquier historia; T036 a T040 son secuenciales (mismo archivo).
- **Fase 10**: T044 y T045 [P].
- Con varias personas: tras la Fase 2, una persona hace US1 → US2 → US3 → US4 (el hilo de `ViajeLogica.py`) y otra hace US6 (T031, T033 y las pruebas T028 a T030) y `bench/ir_a.py` hasta T035.

### Ejemplo de paralelismo (US1)

```text
Tarea: "T009 test_viaje_ruta.py — clase TestRutaMasBarata"
Tarea: "T010 test_viaje_equivalencia.py — clase TestViajeEsCaminar"
Tarea: "T011 test_viaje_comando.py — clase TestComandoIrA"
```

---

## Estrategia de implementación

### MVP primero (solo Historia 1)

1. Fase 1 y Fase 2.
2. Fase 3: un viaje completo por la ruta más barata, desde el comando.
3. **Detenerse y validar**: T009 a T011 pasan y la consola viaja de verdad.

### Entrega incremental

1. Fundamentos → US1 (MVP) → US2 (rechazo seguro, B-N1) → US3 (mapa desactualizado, B-N2) → US4 (peligro y pergamino, B-N3 y B-N6): las cuatro P1 completan el comportamiento del Apéndice B.
2. US5 (antorcha) y US6 (reproducibilidad y registro) cierran las P2.
3. Fase 9 mide y, si hace falta, adopta la política C del recálculo; Fase 10 cierra con la trazabilidad.

### Notas

- Cada tarea indica los requisitos que atiende; los ids FR-2xx aparecen en el nombre de la prueba o en su docstring para la trazabilidad (principio IX).
- Si una prueba o una medición contradice `spec.md` o `plan.md`, se corrige primero la especificación o el plan, en confirmación separada, y después el código (principio X).
- Ninguna tarea cambia el formato binario de partida (formato 8, estado 5): el viaje no se guarda en curso.
