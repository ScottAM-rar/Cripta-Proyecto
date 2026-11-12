# Investigación: Comando «ir a»

**Carpeta**: `006-ir-a` | **Fecha**: 2026-11-11

Cada decisión lista al menos dos alternativas con su complejidad, los módulos que toca y la medición de `--bench ir_a` que la respalda (las secciones se definen en [contracts/bench-ir-a.md](contracts/bench-ir-a.md)). Notación: `V` = salas exploradas, `E` = salidas entre ellas, `g` = salidas de una sala (≤ 4), `L` = pasos de la ruta, `e` = enemigos de una sala.

## Hechos del código que condicionan el diseño

1. **`BuscadorRutas` ya hace lo necesario** (`Logica/BuscadorRutas.py`): `distancias_hacia(destino, vista, limite)` es un Dijkstra desde el destino por aristas entrantes y `siguiente_paso(origen)` elige, entre las salidas con `costo(u,v) + costo(v) = costo(u)`, la de menor id de destino. Reinicia por época (O(1)), así que el trabajo es proporcional a la región alcanzada.
2. **`VistaMapaConocido` cumple su contrato** (`Logica/MapaConocido.py`): `salidas`/`entrantes` vacías para salas no exploradas, `transitable` solo con origen y destino explorados y puerta recordada «abierta», y `version_conocimiento` que sube con todo cambio (también al deshacer).
3. **Un movimiento normal es `accionJugador(EventoDTO "MOVER_JUGADOR")`** (`Logica/EstadoJuegoLogica.py`): el gestor mueve, carga la sala, llama a `MapaConocido.entrar(sala, antorcha)` (observa puertas y explora con antorcha, FR-204/FR-210), activa trampas, programa el turno y avanza el reloj hasta la próxima decisión, y registra la acción en el log.
4. **La activación de enemigos dormidos NO ocurre dentro de `accionJugador`**: ocurre en `ingresarEnSala(sala)` cuando la sala es la del jugador, y el controlador la dispara al empezar cada turno con `servicio.obtenerSala(...)`. Por eso el viaje debe hacer esa misma llamada tras cada paso (D2, D4).
5. **El log es una lista de registros JSON** y varias rutas lo recorren registro por registro: repetición, repetición hasta un instante, y las pasadas 1 y 2 de los segmentos de puntos de control (`_repetirPartidaInterno`, `_planificarSegmento`, `_ejecutarPasada2`). Hoy solo conocen los registros de cursor de inventario (`TIPOS_CURSOR_INVENTARIO`) como excepción.
6. **El pergamino se resuelve dentro de `accionJugador`** (`GestorEventos.es_uso_de_pergamino`); es el único punto desde el cual se puede avisar a un viaje en curso.

---

## D1. Cálculo de la ruta y desempate de FR-234

**Decisión**: calcular el campo de costos hacia el destino con `BuscadorRutas.distancias_hacia(destino, VistaMapaConocido, limite)` y avanzar preguntando `siguiente_paso(sala_actual)`. No se materializa la ruta.

**Por qué el desempate coincide con FR-234.** FR-234 pide: entre rutas de igual costo total, gana la que tiene el menor id en la primera posición en que difieren sus listas de ids. Sea `u` la sala actual y `d` el costo mínimo. Todas las rutas óptimas empiezan en `u`; la primera posición donde pueden diferir es la sala siguiente. Una sala siguiente `v` admite una ruta óptima si y solo si `costo(u,v) + d(v) = d(u)`, que es justo el filtro de `siguiente_paso`; y desde cualquier `v` así existe una continuación óptima. La ruta mínima lexicográfica elige entonces el menor `v` de ese conjunto y repite el razonamiento desde `v`. Es decir, elegir en cada sala el menor id entre las que siguen una ruta óptima construye exactamente la ruta mínima lexicográfica. (Caso límite: dos salidas de una misma sala al mismo destino con el mismo costo dan la misma lista de ids; `siguiente_paso` conserva la primera en el orden en que la sala declara sus salidas, FR-217, así que sigue siendo determinista.)

| Alternativa | Complejidad | Módulos | Veredicto |
|---|---|---|---|
| **A. `distancias_hacia` + `siguiente_paso`** (elegida) | Cálculo O((V+E) log V) acotado a la región alcanzada; cada paso O(g) | Ninguno nuevo; usa `BuscadorRutas` y `VistaMapaConocido` tal cual | Elegida: reutiliza lo ya probado, sin estructura nueva, y es exacta |
| B. Enumerar rutas óptimas completas y comparar lista a lista | O(número de rutas empatadas × L): crece de forma exponencial con diamantes encadenados | Módulo nuevo de enumeración | Descartada: costo impredecible; el resultado es el mismo que A |
| C. Dijkstra desde el origen con predecesor de menor id | O((V+E) log V) | Habría que modificar `BuscadorRutas` | Descartada: su desempate elige la **última** sala (el criterio del cazador, 001) y no la primera; no cumple FR-234 |

**Medición** (`--bench ir_a`, sección A): en rejillas pequeñas con muchos empates, A y B producen la misma lista de salas (verificación previa, criterio duro); se informan el número de rutas que B enumera y el tiempo de ambas. Se anota que C da un resultado distinto en las criptas con empates.

## D2. Cada paso como movimiento normal frente a un camino propio

**Decisión**: el paso construye el mismo `EventoDTO("MOVER_JUGADOR", [sala_actual, dirección])` que el controlador (costo = costo de la salida) y lo entrega a `accionJugador`; después llama a `ingresarEnSala(sala nueva)`, que es lo que el controlador hace al empezar su turno, y que activa a los enemigos dormidos (§2.4). Con eso, el reloj virtual, el intervalo por velocidad, la agenda, las trampas, la antorcha, la observación de puertas (002), el pergamino, el log y los puntos de control son los de siempre.

| Alternativa | Complejidad | Módulos | Veredicto |
|---|---|---|---|
| **A. Paso = `accionJugador` + `ingresarEnSala`** (elegida) | La del movimiento normal; el viaje agrega O(g + e) por paso | `ViajeLogica` (nuevo) | Elegida: cero reglas duplicadas; FR-233 y FR-236 se cumplen por construcción |
| B. Camino propio: mover al jugador, avanzar el reloj, programar el turno, llamar a `entrar` y activar trampas dentro del viaje | O(g) de reglas más lo que duplique | Duplica `GestorEventos` y parte de `EstadoJuegoLogica` | Descartada: cualquier divergencia (velocidad, efectos, trampas) rompe FR-236 y la equivalencia con caminar a mano; cada regla nueva habría que mantenerla en dos sitios |

**Medición** (sección B): el paso de A completo frente a un esqueleto de B que solo mueve y avanza el reloj (la alternativa **solo existe en `bench/ir_a.py`**, igual que en la 002). Se informa la diferencia; el criterio duro es la equivalencia: caminar la misma ruta a mano y viajar dejan el mismo estado (sala, reloj, conocimiento, vida, salas cargadas).

## D3. Recálculo de la ruta y puerta recordada abierta que resulta cerrada

**Decisión**: calcular el campo al iniciar y **recalcularlo solo si `version_conocimiento` cambió** desde el último cálculo. Antes de cada paso se compara un entero.

**Equivalencia con recalcular en cada paso (constitución III).** El campo de costos depende únicamente de (a) el destino, fijo en el viaje, y (b) el grafo que ve la vista: salas exploradas, sus salidas con costo y puertas recordadas abiertas. Todo cambio de (b) sube `version_conocimiento` (contrato de la 002: explorar, avistar, observar y deshacer). Si la versión no cambió, (b) es idéntico y el campo recalculado sería igual; `siguiente_paso` depende solo del campo y de la sala actual, así que la decisión es idéntica. Por evento:

| Evento durante el viaje | ¿Sube la versión? | Acción del viaje |
|---|---|---|
| Entrar a una sala explorada sin cambios de puerta ni antorcha | No | Reutiliza el campo |
| Entrar con antorcha encendida (exploran vecinas, FR-210) | Sí | Recalcula: las vecinas nuevas pueden abrir una ruta más barata |
| Observar una puerta que difiere de la recordada (la ruta pendiente usaba una puerta recordada abierta que está cerrada, FR-239) | Sí | Recalcula; si `costo(sala_actual)` es `None`, se detiene sin dar el paso (FR-241) |
| Una puerta de la sala del jugador cambia mientras él está allí (cierre automático, FR-207) | Sí | Recalcula |
| Una puerta lejana cambia | No | No se entera (FR-208): así es el mapa recordado |
| Usar el pergamino | Sí | El viaje se cancela (D5), no recalcula |

**Sin tiempo adicional (FR-241).** La puerta cerrada se descubre **al entrar a la sala que la contiene** (observación de la 002), es decir, durante un paso que sí se dio y cuyo tiempo ya se consumió. El paso siguiente no se da, y el viaje no llama a `accionJugador`: no hay tiempo, acción ni registro adicionales. Si por una carrera de eventos el movimiento llegara a ser rechazado por el gestor (invariante rota), el viaje también se detiene sin tiempo (el rechazo no consume, Apéndice B).

| Alternativa | Complejidad por paso | Veredicto |
|---|---|---|
| A. Recalcular en cada paso | O((V+E) log V) de la región alcanzada | Descartada: es el patrón más caro y no cambia ninguna decisión (se mide para demostrarlo) |
| **B. Recalcular solo si la versión cambió** (elegida) | O(g) si no cambió; recálculo completo si cambió | Elegida en principio |
| C. B + `limite` = costo restante de la ruta vigente cuando la ruta aún es válida | Recálculo acotado a la bola de radio igual al costo restante | **Condicional**: se adopta solo si la medición del peor caso (antorcha, V grande) de B supera 5 ms. No modifica `BuscadorRutas` (usa su parámetro `limite`); la ruta vigente es válida si ninguna salida pendiente dejó de ser transitable, y solo entonces el límite es seguro (con puerta cerrada se recalcula sin límite) |

**Medición** (sección C): número de recálculos y de salas fijadas (`salas_fijadas` del buscador) por viaje con A, B y C; tiempo del paso en el peor caso. Criterio duro por conteo: B recalcula 0 veces en un viaje sin cambios de conocimiento; **y** la decisión de B coincide con la de A en cada paso (sección H).

## D4. Condiciones de detención (FR-243, FR-249) y motivo

**Decisión**: tras cada paso (después de `accionJugador` e `ingresarEnSala`) el viaje evalúa, en este orden, y se detiene en la primera que se cumpla:

| Orden | Condición | Motivo | Cómo se detecta |
|---|---|---|---|
| 1 | La partida terminó (el jugador murió, FR-249c) | `MUERTE` | `fin` de la lógica |
| 2 | La sala actual es el destino | `LLEGADA` (no es detención: el viaje termina bien) | comparación de ids; aunque haya enemigos dormidos, se activaron y el viaje terminó (Historia 4, escenario 2) |
| 3 | La vida del jugador bajó respecto de antes del paso (FR-249b) | `DANO` | vida antes y después del paso |
| 4 | Se activaron enemigos dormidos en este paso (FR-242, FR-243) | `ENEMIGOS_DORMIDOS` | contador `activaciones_enemigos` de la lógica antes y después de `ingresarEnSala` |
| 5 | Hay un enemigo vivo y activo en la sala (FR-249a) | `ENEMIGO_ACTIVO` | recorrido de los enemigos de la sala actual |
| 6 | No hay ruta conocida desde la sala actual (D3) | `SIN_RUTA` | `costo(sala_actual)` es `None` tras recalcular |

Cada motivo tiene un texto fijo para el jugador. Un viaje que se rechaza antes de empezar usa los motivos `DESTINO_INEXISTENTE`, `NO_EXPLORADO` y `SIN_RUTA_INICIAL` (FR-237). Un pergamino usa `PERGAMINO`.

| Alternativa | Complejidad | Veredicto |
|---|---|---|
| **A. Contador de activaciones + comprobaciones de la sala actual** (elegida) | O(e) por paso | Elegida: distingue «dormidos que se activaron» de «ya activo» sin leer el contenido de salas no visitadas |
| B. Mirar el contenido de las salas de la ruta antes de entrar | O(L × e) y puede forzar descargas | Descartada: viola FR-248 (no depende del contenido descargado) y la descarga rompe el presupuesto de red |
| C. Dejar que el jugador compruebe cada paso (sin detener) | — | Descartada: no cumple FR-243/FR-249 |

El contador `activaciones_enemigos` es un entero de ejecución que `_activarEnemigos` incrementa; no se guarda ni se deshace, porque solo se compara dentro de un paso. **Medición** (sección D): coste de las comprobaciones por paso con 0, 10 y 100 enemigos en la sala (criterio duro: proporcional a `e`, no a V ni al tamaño de la cripta).

## D5. Pergamino durante el viaje (FR-244, FR-245)

**Decisión**: cada paso es una acción normal (nodo propio en el historial del pergamino, 5 como máximo). Cuando `accionJugador` procesa un uso de pergamino y hay un viaje en curso, llama a `viaje.cancelar(PERGAMINO)`; el pergamino ya revirtió **solo la última acción**, que es el último paso (junto con lo ocurrido hasta la siguiente decisión, incluidas las activaciones de enemigos y el conocimiento, 002 FR-214). El viaje queda cancelado y no continúa ni se reanuda solo.

| Alternativa | Complejidad | Módulos | Veredicto |
|---|---|---|---|
| **A. Un nodo por paso + aviso de cancelación** (elegida) | Revertir cuesta los cambios de un paso (ya medido en la 002, sección E) | `ViajeLogica`, `EstadoJuegoLogica` (una llamada) | Elegida: el pergamino no necesita saber que existe el viaje |
| B. Todo el viaje como una sola acción deshacible | Revertir cuesta los cambios del viaje completo | `RetrocesoLogica` (agrupar nodos) | Descartada: contradice «revierte solo el último paso», y el máximo de 5 acciones no calzaría |
| C. El viaje comprueba el pergamino antes de cada paso (sondeo del contador de acciones) | O(1) por paso | `ViajeLogica` | Descartada: funciona, pero un pergamino al final del viaje no lo vería y habría estados en que el viaje cree seguir vivo |

**Cómo se llega a esa situación.** Un viaje ejecutado por la orden `ir a` en consola termina antes de devolver el control (decisión 8), así que el pergamino interviene en la API paso a paso (`iniciarViaje`/`avanzarViaje`), que usan las pruebas, la API falsa de la 009 (guion `("ir_a", sala)` seguido de `("pergamino",)`) y `--bench`. Si en consola se usa el pergamino **después** de un viaje, revierte el último paso del viaje (FR-244, «durante o tras un viaje») y no hay nada que cancelar.

**Medición** (sección E): costo de revertir un paso con y sin antorcha (cambios revertidos = cambios del paso; criterio duro por conteo, reutiliza la medida de la 002).

## D6. Registro en `partida.log` (FR-252) y reproducción

**Decisión**: el log gana dos **marcas informativas**. Una orden aceptada escribe: (1) la marca `IR_A` con el destino, (2) un registro normal `MOVER_JUGADOR` por cada paso dado (los que el flujo normal ya escribe) y (3) la marca `FIN_IR_A` con el resultado, el motivo y la sala final. Un comando rechazado no escribe nada (FR-238). Las marcas llevan costo 0, no son eventos del reloj ni acciones, y las rutas que recorren el log las saltan igual que ya saltan o ejecutan los de cursor. Formato en [contracts/registro-viaje.md](contracts/registro-viaje.md).

La reproducción **rehace el viaje porque repite sus pasos** (movimientos normales, deterministas) y **verifica las marcas**: tras `FIN_IR_A` comprueba que el jugador está en la sala final anotada; si no, falla con «La reproducción no es fiel».

| Alternativa | Complejidad | Módulos | Veredicto |
|---|---|---|---|
| **A. Marcas + pasos como acciones normales** (elegida) | Log: +2 registros por viaje; repetición: O(pasos) | `LogEventos`; cuatro puntos de `EstadoJuegoLogica` que recorren el log | Elegida: pasos, `acciones_linea_tiempo`, puntos de control, `historia #k` y `replay hasta` funcionan igual que con movimientos a mano, incluso a mitad de un viaje |
| B. Una sola entrada «ir a» y la repetición vuelve a ejecutar el viaje; los pasos se omiten | Log: 1 registro; repetición: recalcula rutas | `EstadoJuegoLogica` (repetición y segmentos) | Descartada: el viaje cambia las cuentas de acciones y puntos de control (que se indexan por registro y por acción), y `historia #k` o `replay hasta` a mitad de un viaje no podrían detenerse en el paso k |
| C. Solo los pasos, sin marcas | Log: sin cambios | — | Descartada: incumple FR-252 (orden, destino y resultado deben quedar registrados) |

**Impacto en el formato guardado**: ninguno. Las marcas son cadenas JSON en la misma lista del log; no hay campos ni versión nueva (decisión 8). Se comprueba con una prueba de guardar y cargar con un viaje ya hecho.

**Ajuste de redacción propuesto para `spec.md` (constitución X: especificación primero)**: la última oración de FR-252 dice «La reproducción DEBE rehacer el viaje a partir de la orden». Con A la reproducción rehace el viaje **a partir de sus pasos registrados** y comprueba que la orden y el resultado coincidan. Se propone redactar: «La reproducción DEBE reproducir el mismo viaje paso a paso y comprobar que su resultado coincide con el registrado.» No cambia ningún comportamiento observable.

**Medición** (sección F): costo de escribir las dos marcas y de repetir un viaje de L = 10, 100 y 1 000 pasos frente a repetir esos pasos sin marcas (criterio duro: la diferencia es constante, no crece con L).

## D7. Comando, controlador y vista

**Decisión**: el comando es `ir a <id>` con el id numérico de la sala (FR-231). El controlador lo reconoce antes de `_mapear_entrada_a_evento` (como `mapa` y `historia`), llama a `servicio.irA(destino)` y pasa el resultado a `Vista.mostrar_viaje`. El rechazo (B-N1) lo decide `ViajeLogica` **antes de tocar nada**: destino inexistente, no explorado (avistado o desconocido) o sin ruta conocida; ni el reloj, ni el log, ni el conocimiento, ni el pergamino se enteran (FR-238).

| Alternativa | Complejidad | Veredicto |
|---|---|---|
| **A. Comando propio `ir a <id>` en el controlador, resultado en un DTO** (elegida) | O(1) para interpretar | Elegida: igual que `mapa` e `historia`; la vista solo imprime |
| B. Convertir «ir a» en un `EventoDTO` más del reloj | — | Descartada: no es un evento del reloj; sería una acción con costo desconocido hasta calcular la ruta, y el rechazo no debe pasar por `accionJugador` |
| C. Pedir el destino por nombre de sala | O(V) por búsqueda | Descartada: nombres repetidos serían ambiguos y las avistadas no tienen nombre; el id es único y ya se muestra en el mapa |

**Medición** (sección G cubre el costo total): interpretar el comando y rechazar B-N1 cuesta O(1) y no cambia el reloj (verificación).

## D8. Qué se guarda

**Decisión**: nada. Un viaje es una orden que termina antes de devolver el control; la API paso a paso es transitoria. `guardarPartida` guarda exactamente lo de siempre (formato 8, estado 5); `restaurar_estado`, `restaurarDesdePuntoControl` e `iniciarJuego` dejan `viaje_activo = None`, de modo que un viaje no sobrevive a una carga.

| Alternativa | Complejidad | Veredicto |
|---|---|---|
| **A. No guardar viaje; descartar el viaje en curso al cargar** (elegida) | O(1) | Elegida: sin formato nuevo, sin estados a medias |
| B. Guardar destino y ruta del viaje en curso | +campo en el estado guardado, subir formato y estado | Descartada: nada la pide y obligaría a subir versión; Principio VI |

**Medición**: ninguna propia; se comprueba que un guardado antes y después de un viaje completo difiere solo en lo que los movimientos ya cambian (prueba de guardado).

---

## Rendimiento: el peor caso del paso (FR-250)

El paso cuesta: construir el evento + `accionJugador` (movimiento normal, ya medido en el ciclo de la Parte I) + `ingresarEnSala` + comprobaciones O(e) + (a veces) recálculo del campo. El recálculo domina cuando ocurre. **Peor caso a medir**: antorcha encendida (la versión sube en cada entrada), cripta de 20 000 salas, 10 % explorada (2 000), destino lejano, y una puerta recordada abierta cerrada que fuerza un recálculo sin límite. Si ese peor caso supera 5 ms con B, se adopta C (D3), que acota el recálculo al radio del costo restante; si aun así supera, se informa como defecto antes de implementar (nada se oculta tras un promedio: se reporta mediana y máximo).

## Qué no se hace (frente a la tentación)

- **No se modifica `BuscadorRutas`** ni `VistaMapaConocido`: el contrato de la 002 alcanza y D3-C usa un parámetro que ya existe. Si una medición lo exigiera, se documenta el antes y el después en `DECISIONES.md`.
- **No se guarda la ruta** como lista: se pregunta el siguiente paso al campo. Menos estado, nada que invalidar a mano.
- **No se leen salas no descargadas** para decidir; solo el conocimiento (FR-248).
