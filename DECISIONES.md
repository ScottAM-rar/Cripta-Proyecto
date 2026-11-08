# Documento de Decisiones (Parte II)

Por capacidad: enlace a su especificación y a su plan, si la decisión final coincide con el plan original y, si no, qué medición motivó el cambio (constitución, flujo obligatorio). Las decisiones de la Parte I siguen en `DOCUMENTACION_DECISIONES_DISENO.md`.

## 001 · Terreno y cazador

- Especificación: [`specs/001-terreno-y-cazador/spec.md`](specs/001-terreno-y-cazador/spec.md) (FR-101 a FR-131)
- Plan: [`specs/001-terreno-y-cazador/plan.md`](specs/001-terreno-y-cazador/plan.md), con [`research.md`](specs/001-terreno-y-cazador/research.md)
- Mediciones: [`specs/001-terreno-y-cazador/mediciones.md`](specs/001-terreno-y-cazador/mediciones.md)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| Mapa del esqueleto en listas contiguas, aristas salientes y entrantes; estado de puertas leído de la sala cargada o, si no está cargada, el inicial | Sí | `test_cazador` (FR-117) y `test_determinismo_cazador`: misma decisión con y sin salas descargadas |
| Búsqueda de menor costo desde la sala del jugador, acotada por el rango, con montículo propio y reinicio por marca de época | Sí | `--bench terreno` B: 28 µs frente a 57 ms sin cota a 40 000 salas |
| Campo compartido por todos los cazadores del instante | Sí | `--bench terreno` A: con 50 cazadores, 17 µs (jugador quieto) y 77 µs (jugador moviéndose) frente a ≈ 3 ms calculando por cazador |
| Invalidación por evento, con un punto único de cambio de puertas (`PuertasLogica.fijar_cerrada`) | Sí | `--bench terreno` C: 0 búsquedas frente a 18 por 40 ciclos con puertas lejanas; `test_equivalencia_cazador` y `test_puertas_punto_unico` |
| El contrato de los comportamientos devuelve `AccionEnemigoDTO` (mensaje y costo) | Sí | El siguiente evento del actor se programa con el costo de la salida cruzada (FR-103) |
| Costo inválido → 100 con advertencia; rango ausente o inválido → 0 con advertencia | Sí (decidido en `/speckit-clarify`) | Clarificaciones 2 y 3 de `spec.md` |
| Costos distintos en los dos lados → gana la sala de menor id; conexiones de un solo sentido válidas | **Cambió respecto del plan original**: el plan dejaba ambos puntos como «regla provisional» | Se resolvieron en la especificación antes de implementar (FR-102 ampliado, FR-124 nuevo) |
| Ids de sala densos desde 1 (no desde 0) | **Corrección al plan**: `research.md` decía 0..N−1 | El código de la Parte I usa listas de tamaño N+1 indexadas por id; las estructuras se dimensionan con el mayor id más uno |
| Formato de partida: `VERSION_ESTADO` 3 y `VERSION_FORMATO` 6; los archivos anteriores se rechazan | Sí | `test_terreno_costos` (FR-119) |
| Mediciones de la Parte I repetidas con la carga nueva | Sí: ninguna decisión de la Parte I dejó de servir | `mediciones.md`: binario sigue ≈ 2,9× menor que JSON y ≈ 128× más rápido para una sala; +3 % de tamaño por el costo de cada salida |
| Búsqueda de rutas generalizada (`BuscadorRutas`) sobre una vista del mapa, para que otras capacidades la reutilicen con el mapa conocido | **Cambió respecto del plan original**: el plan tenía la búsqueda dentro del campo de costos | Ampliación del plan (2026-10-29): 197 pruebas en OK, decisiones idénticas a calcular desde cero (12 000 comparaciones, 0 diferencias) y ciclo dentro de 20 ms. Alternativa descartada (campo sin vista, T071): la vista cuesta entre 14 % y 22 % más (50 cazadores con el jugador quieto: 33,0 µs frente a 40,2 µs; 200 cazadores con el jugador moviéndose: 193 µs frente a 226 µs) y el peor ciclo sigue en ≈ 0,25 ms frente al límite de 20 ms. Se mantiene la vista porque permite buscar sobre el mapa conocido. `mediciones.md`, sección «Búsqueda con vista» |
| `MapaCripta` con `total_salas`, `salidas(sala)`, `entrantes(sala)` y `version_puertas`; la versión la sube solo `fijar_cerrada` | **Cambió respecto del plan original**: se agregó como contrato compartido | `test_mapa_cripta.py` y `test_puertas_punto_unico.py`. Al restaurar una partida se crea un `MapaCripta` nuevo, así que `version_puertas` empieza de cero con el estado restaurado y no hace falta subirla |

## 005 · Recorrido por niveles

- Especificación: [`specs/005-recorrido-por-niveles/spec.md`](specs/005-recorrido-por-niveles/spec.md) (FR-501 a FR-513)
- Plan: [`specs/005-recorrido-por-niveles/plan.md`](specs/005-recorrido-por-niveles/plan.md), con [`research.md`](specs/005-recorrido-por-niveles/research.md)
- Mediciones: [`specs/005-recorrido-por-niveles/mediciones.md`](specs/005-recorrido-por-niveles/mediciones.md)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| Visitados con marca de época, dos listas indexadas por id de sala | Sí | SC-004 por conteo: un recorrido de 2 niveles visita 13 salas y examina 20 salidas en 400, 4 900 y 40 000 salas (`test_recorrido_proporcional` y `--bench recorrido`, sección A) |
| Cola circular propia sobre una lista | Sí (instrucción del grupo), **con una observación abierta** | Frente a `pop(0)` gana en frontera ancha (árbol: 25,1 ms frente a 41,1 ms). Pero las **dos listas por nivel** (sin cola) son 8 % a 14 % más rápidas en las tres criptas medidas, como anticipaba `research.md` §3. No se cambió: la diferencia es pequeña y la cola fue pedida. **Decisión pendiente del grupo** |
| Ordenar cada nivel con `ordenar_adaptativo` (no `sorted()`) | Sí | El orden de descubrimiento sigue al de los padres, no al de los ids (ejemplo `1, 3, 5, 4, 9`). Frente al montículo `(nivel, id)`: el montículo es 19 % (rejilla) y 46 % (árbol) más lento |
| `MapaCripta.existe` para rechazar un origen inexistente y ignorar salidas hacia salas inexistentes | Sí | `test_recorrido_por_niveles` (FR-512, FR-513) |
| El criterio de transitabilidad lo pasa quien pide el recorrido; sin criterio valen todas | Sí | Clarificación 2026-10-27; `TestOrdenYAlcance` |
| SC-004 se verifica por conteo y la razón de tiempos solo informa | **Cambió respecto de la especificación original**, que usaba una razón de tiempos (≤ 2×) | `/speckit-analyze` (A1): el tiempo de operaciones de decenas de µs es frágil. Medido: la razón fue 0,99× |
| FR-513: una salida hacia una sala que no existe se ignora | **Agregado a la especificación tras `/speckit-analyze` (S1)**; el plan ya lo suponía | `TestOrigenYSalasInexistentes` y la equivalencia con la referencia |
| `ServicioCripta.salas_vecinas` no se modifica | Sí | Medido como referencia: con límite 5 en 40 000 salas tarda 11,75 ms frente a 0,02 ms del recorrido nuevo, porque busca cada sala con un recorrido lineal. Reemplazarlo le toca a la capacidad que adopte el recorrido |


## 008 · Reproducción acotada hasta un instante dado (replay-hasta)

- Especificación: [`specs/008-replay-hasta/spec.md`](specs/008-replay-hasta/spec.md) (FR-401 a FR-413)
- Plan: [`specs/008-replay-hasta/plan.md`](specs/008-replay-hasta/plan.md), con [`research.md`](specs/008-replay-hasta/research.md)
- Mediciones: [`specs/008-replay-hasta/mediciones.md`](specs/008-replay-hasta/mediciones.md)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| **Opción b ratificada**: tope de tiempo en `_avanzarHastaProximoTurno`; ciclo de eventos se interrumpe antes de desapilar cualquier evento con `tiempo_ejecucion > tope` | Sí | `--bench replay` Sección A: razón de eventos = **0.500** en las tres escalas (250, 1 000 y 4 000 acciones), ≤ 0.55 (SC-003). **CUMPLE** |
| Opción a descartada (corte solo entre acciones del jugador): `_avanzarHastaProximoTurno` sin tope procesa todos los eventos de enemigos hasta el próximo turno del jugador | Sí (descarte previsto en `research.md`) | `--bench replay` Sección B (t = 50 001 en 1 000 acciones): la opción a termina con el reloj en 50 100 > t y procesa 1503 eventos frente a 1500 de la opción b, que termina en 50 000; falla FR-402 |
| Opción c descartada (reproducción total y recorte de salida): el log se lee completo antes de responder | Sí (descarte previsto en `research.md`) | `--bench replay` Sección B: Opción c procesa **el 100 %** de eventos independientemente de t (3 000 frente a 1 500 en 1 000 acciones); falla FR-412 |
| Decisión del jugador en `t` no se ejecuta; `repetirPartida` comprueba `reloj.tiempo_actual < hasta` antes de cada registro del log | Sí | FR-403, FR-406; `TestTruncamientoTemporal.test_FR403_decision_jugador_en_tope_no_se_ejecuta` |
| `_completarInstante(hasta)` ejecuta los eventos de otros actores con tiempo == `hasta` y número de secuencia posterior al `TURNO_JUGADOR` | Sí | FR-403; `TestTruncamientoTemporal.test_FR403_completar_instante_ejecuta_eventos_de_otros_actores_en_tope` |
| Con `t=0` no se ejecuta ninguna acción sin regla especial; la misma comprobación `reloj.tiempo_actual < hasta` lo resuelve | Sí | FR-406; `TestCasosLimite.test_FR406_hasta_cero_no_ejecuta_ninguna_accion` |
| `ResultadoReplayHastaDTO` como DTO puro; la lógica no escribe en `stdout` | Sí | Principio IV; `TestAislamientoReplay`: sin vista, sin log nuevo, sin puntajes |
| `--hasta` sin `--replay` termina con código 2 antes de crear `EstadoJuegoServicio` | Sí | FR-408, SC-004; `TestArgumentosCLI.test_SC004_latencia_rechazo_menor_a_100ms`: latencia < 0.1 s |
| Propiedad de prefijo verificada: estado en `t` con reproducción acotada == estado en `t` de la partida completa | Sí | FR-411; `TestDeterminismoReplay.test_FR411_propiedad_de_prefijo` |


## 007 – Puntos de control de la partida

- Especificación: [`specs/007-puntos-de-control/spec.md`](specs/007-puntos-de-control/spec.md) (FR-414 a FR-426)
- Plan: [`specs/007-puntos-de-control/plan.md`](specs/007-puntos-de-control/plan.md), con [`research.md`](specs/007-puntos-de-control/research.md)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| **Alternativa B ratificada**: instantánea de estado con marca de longitud en bitácora y log de acciones | Sí | `--bench puntos_control`: memoria a 5 000 acciones lineal $O(N)$ (~600 KB con $K=10$; ~6 MB con $K=1$). Tiempo neto de captura mediana 268.8 µs (0.27 ms) |
| Alternativa A descartada: copia completa exhaustiva de bitácora y log en cada punto | Sí (descarte previsto en `research.md` §3) | Memoria a 5 000 acciones cuadrática $O(N^2)$: requeriría $\approx 12.5$ millones de entradas de log (>300 MB con $K=1$) degradando el ciclo |
| Alternativa C descartada: sin puntos de control (reproducir siempre desde cero) | Sí (descarte previsto en `research.md` §7) | Distancia de recuperación hasta una acción $k$ arbitraria es $O(k)$ (hasta 5 000 pasos de repetición) |
| Fijar $K=10$ como valor por defecto | Sí | Medido: distancia máxima 9 pasos (<10), memoria < 1 MB a 5 000 acciones, ciclo con punto 1.57 ms |
| Límite de ciclo de eventos con $K=1 \le 20$ ms (FR-426) | Sí | `--bench puntos_control`: ciclo con captura $K=1$ en cripta sintética representativa (50 esbirros) dio mediana **1.57 ms** (máximo **1.75 ms** < 20 ms). **CUMPLE** |
| Contador `acciones_linea_tiempo` independiente de `accionesJugador` | Sí | `self.accionesJugador` permanece intacto para puntaje acumulado (§2.12); `acciones_linea_tiempo` mide la línea de tiempo activa y retrocede con el pergamino (FR-418) |
| Poda por retroceso mediante truncado con `pop()` en lista contigua | Sí | Principio I: sin `dict`, `set`, `heapq`, `bisect` ni `collections`. Complejidad $O(m)$ donde $m \le 5$ |
| `repetirPartida` (`--replay`, `--hasta`) no toma puntos de control | Sí | Invarianza y aislamiento (Principio IV); suites `test_replay_hasta`, `test_determinismo_replay` y `test_rendimiento_replay` se preservan sin sobrecosto |
| Formato de guardado v7 en `AlmacenPartidaBinario.py` (T021 a T024) | Pendiente de confirmación | Pruebas de contrato v7 preparadas en `test_persistencia_v7.py` (T020). T021 a T024 no se implementan por falta de confirmación de Scott, de acuerdo con la regla de coordinación |
