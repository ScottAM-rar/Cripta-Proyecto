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

## 002 · Niebla de guerra y mapa conocido

- Especificación: [`specs/002-niebla-de-guerra/spec.md`](specs/002-niebla-de-guerra/spec.md) (FR-201 a FR-226)
- Plan: [`specs/002-niebla-de-guerra/plan.md`](specs/002-niebla-de-guerra/plan.md), con [`research.md`](specs/002-niebla-de-guerra/research.md)
- Mediciones: [`specs/002-niebla-de-guerra/mediciones.md`](specs/002-niebla-de-guerra/mediciones.md)
- Estado: las siete historias implementadas. **Resuelto**: `retroceso` lo repitió la 006 (hallazgo 4 de su sección) y `guardado` lo cubre la sección 012 (la 002 solo los había corrido de forma informativa; ver `mediciones.md`).

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| Estado por sala en un arreglo indexado por id | Sí | `--bench mapa` A: ≈ 110 µs por 1 000 consultas en 400, 2 000 y 20 000 salas, con k = 1 y k = N/10, y una posición leída por consulta. La lista de conocidas pasa de 0,66 ms a 33,8 ms con k = N/10; con k = 1 es 3× más rápida (límite) |
| Memoria de puertas en una lista plana de 4·N; lectura al entrar y aviso al cambiar | Sí | `--bench mapa` F: aviso 122 µs frente a sondeo 20,5 ms por 1 000 eventos (cambios raros); 2,66 ms frente a 20,1 ms (frecuentes); 0 lecturas del esqueleto por evento con el aviso |
| El aviso del pergamino no observa; la memoria se restaura con `OBSERVAR_PUERTA` | Sí | `test_mapa_conocido` (caminos de cambio de puertas) y `test_niebla_retroceso` (equivalencia con la referencia en recorridos aleatorios) |
| Orden del comando `mapa`: ordenar al consultar con `ordenar_adaptativo` | Sí, **con una corrección a la evidencia preliminar** | `--bench mapa` D: el cruce con el escaneo del arreglo está cerca de k ≈ N/40 y no de N/8 como sugería la medición preliminar; el comando completo con 5 000 exploradas en 20 000 salas cuesta 22,2 ms. Se revisa si el k realista supera N/40 (híbrido) |
| Antorcha con bucle directo sobre las salidas | Sí | `--bench mapa` C: 3,4 µs frente a 9,4 µs de `RecorridoPorNiveles` con límite 1 en 400 salas (la razón baja a 1,4× con 20 000 por una reserva O(N) común a ambos en el bench) |
| Cambios deshacibles `EXPLORAR_SALA`, `AVISTAR_SALA` y `OBSERVAR_PUERTA` con valor anterior | Sí | `--bench mapa` E: 17 µs frente a 953 µs de la instantánea con 20 000 salas; con 400 salas y r ≥ 87 la instantánea gana (límite). `test_niebla_proporcional`: cambios revertidos = registrados |
| Vista para `BuscadorRutas` con consulta directa a los arreglos | Sí | `--bench mapa` G: 1,89 ms frente a 6,84 ms con 20 000 salas; con 2 000 salas las dos se igualan (límite) |
| La vista de consola recibe solo DTO de conocimiento (`mostrar_juego` exige las salidas conocidas) | Sí | `test_niebla_vista`: vista con el grafo completo apagado, sin fugas y búsqueda inversa en el texto |
| Cada salida tiene su propia puerta (un par de salidas por conexión, estados independientes) | **Cambió respecto de la especificación original** | El supuesto de `spec.md` decía que una puerta era una sola; el modelo ya tenía un objeto por salida. Corregido en `spec.md` antes de implementar (principio X) |
| El jugador entra a la sala en el instante de la acción; no hay estado «cruzando» | **Cambió respecto de la especificación original** | `accionJugador`: la acción ocurre ahora y el costo solo programa el siguiente turno. Corregido en `spec.md` |
| `SalaMapaDTO.nombre`: el mapa del esqueleto conserva el nombre de cada sala | **Cambió respecto del plan original** (pendiente P2) | Permite mostrar el nombre de una sala explorada por la antorcha sin descargar su contenido; `MapaCripta` no se modificó |
| `mostrar_juego` ya no muestra el id de las salas no exploradas | **Cambió una prueba de la 001**: `test_terreno_costos` esperaba `Sala 3` | FR-219; la prueba ahora espera «sala sin explorar» y que no aparezca el id |
| Mediciones de la Parte I repetidas con la carga nueva (`ordenamiento`, `inventario`, `ciclo` informativo) | Sí: ninguna decisión de la Parte I dejó de servir | `mediciones.md`; `retroceso` lo repitió la 006 (sección «006 · Comando «ir a»», hallazgo 4: `mapa`, `retroceso`, `ordenamiento` y `ciclo` en CUMPLE) y `guardado` lo cubre la sección «012 · Revisión de la Parte I con la carga nueva» (bloque `guardado` en M0, M1 y M2) |
| Persistencia: `ConocimientoGuardadoDTO` (exploradas en orden de descubrimiento, avistadas ascendentes, puertas observadas) validado con V1 a V5 **antes** de tocar la partida | Sí | `test_niebla_guardado`: ida y vuelta exacta, continuación idéntica, cada validación con la partida actual intacta. ≈ 37 B por sala explorada (`mediciones.md`) |
| Numeración del formato: `VERSION_FORMATO` 7 y `VERSION_ESTADO` 4 (pendiente P3); tras integrar con `main`, que ya usaba 7 y 4 para los puntos de control, **8 y 5** | **Resuelto por el grupo**: el plan solo recomendaba esa numeración | Un archivo sin niebla (formato 7) y un estado de la versión 4 se rechazan con la versión encontrada y la esperada (FR-221); `test_niebla_guardado` y `test_terreno_costos` (FR-119) |


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
| **Alternativa B ratificada**: el punto guarda las longitudes de la bitácora y del log de acciones, no sus copias | Sí | `--bench puntos_control` (partidas de 1 000 acciones, 50 esbirros): los puntos serializados ocupan 1 309 KB con $K=10$ y 12 956 KB con $K=1$; tiempo de una acción con punto de control 2.3 ms de mediana |
| Alternativa A descartada: copia completa de bitácora y log en cada punto | Sí (descarte previsto en `research.md` §3) | Medida con $K=10$: 1 815 KB frente a 1 309 KB de B (1.4 veces); con la mitad de la partida la razón es 1.3, así que crece con la longitud de la partida. Con esta cripta sintética el historial por acción es corto y la diferencia es moderada; B no cuesta más y escala mejor |
| Alternativa C descartada: sin puntos de control (reproducir desde el inicio) | Sí (descarte previsto en `research.md` §7) | Medida: llegar a la acción 999 desde el inicio tarda 2.2 a 2.8 s; desde el punto de control más cercano con $K=10$, 18 ms (más de 100 veces menos). Se comprueba que ambos caminos llegan al mismo estado |
| Fijar $K=10$ como valor por defecto | Sí | Medido el peor caso de reconstrucción (restaurar y reaplicar $K-1$ acciones): $K=1$ 1 ms, $K=10$ 18 ms, $K=50$ 92 ms, $K=100$ 208 ms. $K=10$ es el mayor probado que cabe en los 50 ms de `historia` (§6). El tamaño crece al bajar $K$ (13 MB por 1 000 acciones con $K=1$) |
| Límite de ciclo de eventos con $K=1 \le 20$ ms (FR-426) | Sí | `--bench puntos_control`: 999 acciones con punto de control en cada una; mediana 2.3 ms, máximo 3.1 a 3.5 ms (< 20 ms). **CUMPLE** |
| Contador `acciones_linea_tiempo` independiente de `accionesJugador` | Sí | `self.accionesJugador` permanece intacto para puntaje acumulado (§2.12); `acciones_linea_tiempo` mide la línea de tiempo activa y retrocede con el pergamino (FR-418) |
| Poda por retroceso mediante truncado con `pop()` en lista contigua | Sí | Principio I: sin `dict`, `set`, `heapq`, `bisect` ni `collections`. Complejidad $O(m)$ donde $m \le 5$ |
| `repetirPartida` (`--replay`, `--hasta`) no toma puntos de control | Sí | Invarianza y aislamiento (Principio IV); suites `test_replay_hasta`, `test_determinismo_replay` y `test_rendimiento_replay` se preservan sin sobrecosto |
| Formato de guardado v7 en `AlmacenPartidaBinario.py` (T021 a T024) | Sí | Confirmado e implementado (FR-424, FR-425): `VERSION_FORMATO = 7`, `VERSION_ESTADO = 4`; serialización de `k_checkpoint`, `acciones_linea_tiempo` y bloque de `puntos_control`; rechazo explícito de v6 y Parte I con `ErrorPartida` sin carga silenciosa (Principio VI). Reevaluación de `--bench guardado`: antes (v6/v3) vs después (v7/v4): 10 salas 8,237 B → 12,467 B (guardar 2.36 ms → 2.91 ms, cargar 2.38 ms → 3.63 ms); 100 salas 43,595 B → 47,828 B (guardar 7.36 ms → 7.84 ms); 1 000 salas 408 KB → 412 KB (guardar 56.8 ms → 57.7 ms, acceso directo a sala 318 µs → 324 µs). `--bench puntos_control` reevaluado: peor ciclo con K=1 2.68 ms (< 20 ms), K=10 reconstrucción 12.47 ms (< 50 ms). |

## 009 · Contrato de datos v2 y ubicación de llaves

- Especificación: [`specs/009-contrato-datos-v2/spec.md`](specs/009-contrato-datos-v2/spec.md) (FR-301 a FR-325)
- Plan: [`specs/009-contrato-datos-v2/plan.md`](specs/009-contrato-datos-v2/plan.md), con [`research.md`](specs/009-contrato-datos-v2/research.md)
- Mediciones: [`specs/009-contrato-datos-v2/mediciones.md`](specs/009-contrato-datos-v2/mediciones.md) (`python main.py --bench llaves`)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| Guardado A: las llaves van en la clave `llaves` dentro de `cripta_<id>.bin`; la validación de versión existente las invalida junto con lo demás | Sí (`research.md` §4, decisión A) | `--bench llaves` B: guardar con A y 5 000 salas tarda **27.14 ms**, por debajo del límite de 50 ms de `research.md` §4. La opción B (archivo aparte) fue más rápida: 3.43 ms al guardar y 331.4 µs al leer, frente a 3.73 ms de A. La regla solo cambia de decisión si A supera los 50 ms, y no los supera; el guardado ocurre una vez por cripta y versión (`mediciones.md`, «Revisión de las decisiones») |
| Entradas repetidas: ordenar las posiciones con `ordenar_adaptativo` y comparar vecinas, frente a comparar todas las parejas | Sí (`research.md` §5) | `--bench llaves` C: con k = 1 000, 3.91 ms (validación elegida completa) frente a 78.55 ms (todas las parejas). Las parejas solo ganan con k = 10 (9.6 µs frente a 13.1 µs), y `research.md` §5 ya admite que con k chica cualquiera sirve |
| `solo_guardadas`: sin presupuesto no se consulta; el persistente devuelve lo guardado o lanza `LlavesNoDisponibles`, y el HTTP no hace la solicitud. `limite_solicitudes` hace que un 429 no se reintente si ya no queda presupuesto | Sí. La firma final es `obtener_llaves(cripta_id, solo_guardadas=False, limite_solicitudes=None)`: `limite_solicitudes` se agregó tras `/speckit-analyze` y ya estaba en el contrato y en T009 antes de implementar (el resumen de `plan.md` todavía muestra la firma con solo dos parámetros) | `test_llaves_presupuesto`: sin presupuesto y sin llaves guardadas, 0 consultas y aviso con la cripta; con llaves guardadas, 0 solicitudes; con 1 restante, un 429 no se reintenta (SC-005) |
| Una consulta por cripta y por sesión, contada en el presupuesto (`ServicioCripta.ubicacion_llaves` la memoriza) | Sí | `--bench llaves` D: **1 / 0 / 0** (primera partida, segunda con la misma versión, `--offline`). `test_llaves_presupuesto`: la primera partida pasa de 6 a 7 solicitudes («Solicitudes a la API: 7 de 9») |
| Aviso FR-313: si no se obtienen las llaves, `llaves` queda en `None`, `avisoLlaves` guarda el mensaje con la cripta y la partida sigue; el controlador lo muestra como `AVISO:` al iniciar una partida nueva. Desde T055 el aviso es uniforme: nombra la cripta una sola vez, da el motivo y termina con «La verificación de resolubilidad no está disponible.», incluso sin presupuesto (cuando el `LlavesNoDisponibles` viene del cliente, `ServicioCripta.ubicacion_llaves` lo vuelve a lanzar con esa forma y no repite la cripta si el motivo ya la nombra) | Sí | `test_llaves_fallos` (partes c, e y g, y la clase `AvisoUniforme` de T055) y comprobación manual con `ControladorJuego` en `--offline` (T022): el aviso aparece y la partida responde a las acciones |
| Restaurar una partida no pide llaves: `llaves` y `avisoLlaves` vuelven a `None` y se piden bajo demanda con `obtenerLlaves()` (FR-325) | Sí | `test_llaves_partida_cargada`: cargar no hace solicitudes; con llaves guardadas, 0; sin ellas, 1 la primera vez y 0 la segunda; restaurar otra cripta no arrastra las llaves anteriores |
| La reproducción (`--replay`, `--hasta`) no pide las llaves: `repetirPartida` llama a `iniciarJuego(cripta, semilla, pedir_llaves=False)`, así que no hay consulta ni aviso; si después hacen falta, se piden bajo demanda con `obtenerLlaves()`, como en una partida cargada (FR-325). `--hasta` todavía no existe en `main.py`: es de la capacidad 007 y la regla está en el caso límite de `spec.md` | **Cambió respecto del plan**: `plan.md` §4 decía que `--replay` pedía las llaves al pasar por `iniciarJuego` y que no gastaba nada si estaban guardadas (T058) | Una reproducción no es una partida nueva y las llaves solo sirven para el aviso, así que no gasta presupuesto. `test_llaves_partida_cargada`, clase `Reproduccion` (T058): reproducir en carpeta vacía hace 0 consultas de llaves, `avisoLlaves` queda en `None` y el log no cambia; después, `obtenerLlaves()` pide una vez; una partida nueva sigue pidiendo las llaves al iniciar |
| `FuenteSoloLocal`: envuelve `ServicioCripta` sobre `ClienteOffline`, compara la versión vigente y nunca escribe ni pide nada | **Cambió respecto del plan**: se amplió en T053 con lo que pidió la capacidad 004 (`existe_cripta`, `version_catalogo` con `version_catalogo_vigente`, `objetos_que_suelta` con la última cripta consultada, `obtener_sala_salida`, `obtener_mapa`, `fijar_fichas_en_uso`). Además, `construir_sala` comprueba en el almacén que el contenido de la sala esté antes de delegar, porque el modo sin red no ve las criptas incompletas (ver «Hallazgos y límites») | `test_fuente_solo_local`: 0 solicitudes (espía HTTP sin llamadas) y los archivos de la carpeta iguales byte a byte en todas las pruebas, incluidas las de dato faltante y versión distinta (SC-003) |
| Precarga por saltos frente a precarga por costo (la regla por costo solo existe en el bench, `ServicioPrecargaPorCosto`) | Sí: se mantiene la precarga por saltos y no se modifica `precargar_vecinas` ni `salas_vecinas` (FR-324) | `--bench llaves` A: **inconclusiva**. Las dos reglas dieron los mismos totales de solicitudes en las 9 filas y en la variante `costo_max=300`, y casi no hubo solicitudes disparadas por un enemigo (0.2 de promedio en 2 de 9 filas). Recomendación de `mediciones.md`: mantener la precarga por saltos sin abrir una especificación aparte; es un límite del experimento (el guion no persigue a los cazadores), no una prueba de que el costo nunca sirva |

### Bloque `cache`: antes y después (T050)

Antes: `specs/009-contrato-datos-v2/bench-cache-antes.csv` (T049, código anterior a esta capacidad). Después:
`specs/009-contrato-datos-v2/bench-cache-despues.csv`, generado otra vez para T050 con
`python main.py --bench cache --bench-csv specs/009-contrato-datos-v2/bench-cache-despues.csv` (código de salida 0). Las
9 filas de cuenta (secciones 1 y 6) son idénticas antes, en la medición de T037 (`mediciones.md`) y en esta. Los
tiempos dependen de la máquina y de su carga, así que solo sirven como referencia.

| # | Sección | Medición | Antes (T049) | Después (T050) | Diferencia | Causa |
|---|---|---|---|---|---|---|
| 1 | 1 | sala por sala (sin precarga) | 63 solicitudes | 63 solicitudes | +0 | cuenta: igual; el bloque no pide llaves |
| 2 | 1 | actual + vecinas en cada paso (prof. 2) | 61 solicitudes | 61 solicitudes | +0 | cuenta: igual; el bloque no pide llaves |
| 3 | 1 | perezosa, prof. 2 | 33 solicitudes | 33 solicitudes | +0 | cuenta: igual; el bloque no pide llaves |
| 4 | 1 | perezosa, por defecto (lote de 10) | 9 solicitudes | 9 solicitudes | +0 | cuenta: igual; el bloque no pide llaves |
| 5 | 2 | deque lineal, 25 fichas, acierto | 1.12 µs | 1.12 µs | +0 (+0 %) | tiempo: depende de la máquina |
| 6 | 2 | deque lineal, 25 fichas, fallo | 0.6 µs | 0.77 µs | +0.17 (+28 %) | tiempo: depende de la máquina |
| 7 | 2 | tabla hash propia, 25 fichas, acierto (descartada) | 0.19 µs | 0.36 µs | +0.17 (+89 %) | tiempo: depende de la máquina |
| 8 | 2 | deque lineal, 100 fichas, acierto | 3.42 µs | 3.5 µs | +0.08 (+2 %) | tiempo: depende de la máquina |
| 9 | 2 | deque lineal, 100 fichas, fallo | 1.92 µs | 2.56 µs | +0.64 (+33 %) | tiempo: depende de la máquina |
| 10 | 2 | tabla hash propia, 100 fichas, acierto (descartada) | 0.21 µs | 0.24 µs | +0.03 (+14 %) | tiempo: depende de la máquina |
| 11 | 2 | deque lineal, 1000 fichas, acierto | 30.95 µs | 34.62 µs | +3.67 (+12 %) | tiempo: depende de la máquina |
| 12 | 2 | deque lineal, 1000 fichas, fallo | 18.31 µs | 21.97 µs | +3.66 (+20 %) | tiempo: depende de la máquina |
| 13 | 2 | tabla hash propia, 1000 fichas, acierto (descartada) | 0.31 µs | 0.28 µs | -0.03 (-10 %) | tiempo: depende de la máquina |
| 14 | 2 | deque lineal, 5000 fichas, acierto | 176.7 µs | 181.1 µs | +4.4 (+2 %) | tiempo: depende de la máquina |
| 15 | 2 | deque lineal, 5000 fichas, fallo | 106.76 µs | 109.46 µs | +2.7 (+3 %) | tiempo: depende de la máquina |
| 16 | 2 | tabla hash propia, 5000 fichas, acierto (descartada) | 0.35 µs | 0.51 µs | +0.16 (+46 %) | tiempo: depende de la máquina |
| 17 | 3 | catálogo con 25 fichas | 0.109 ms por lectura | 0.095 ms por lectura | -0.014 (-13 %) | tiempo: depende de la máquina |
| 18 | 3 | catálogo con 200 fichas | 0.202 ms por lectura | 0.213 ms por lectura | +0.011 (+5 %) | tiempo: depende de la máquina |
| 19 | 3 | catálogo con 1000 fichas | 0.511 ms por lectura | 0.495 ms por lectura | -0.016 (-3 %) | tiempo: depende de la máquina |
| 20 | 4 | catálogo con 25 fichas | 3.547 ms | 3.662 ms | +0.115 (+3 %) | tiempo: depende de la máquina |
| 21 | 4 | catálogo con 200 fichas | 11.968 ms | 10.879 ms | -1.09 (-9 %) | tiempo: depende de la máquina |
| 22 | 4 | catálogo con 1000 fichas | 12.707 ms | 12.801 ms | +0.094 (+1 %) | tiempo: depende de la máquina |
| 23 | 5 | salas_vecinas, 1 paso | 38.4 µs | 47.0 µs | +8.6 (+22 %) | tiempo: depende de la máquina |
| 24 | 5 | salas_vecinas, 2 pasos | 98.1 µs | 96.1 µs | -2 (-2 %) | tiempo: depende de la máquina |
| 25 | 5 | precargar_vecinas cuando no hace falta nada | 59.4 µs | 64.0 µs | +4.6 (+8 %) | tiempo: depende de la máquina |
| 26 | 6 | capacidad    5 | 82 aciertos / 938 fallos (8.0 %), 19 solicitudes de red | 82 aciertos / 938 fallos (8.0 %), 19 solicitudes de red | 0 | cuenta: igual; el bloque no pide llaves |
| 27 | 6 | capacidad   10 | 316 aciertos / 704 fallos (31.0 %), 19 solicitudes de red | 316 aciertos / 704 fallos (31.0 %), 19 solicitudes de red | 0 | cuenta: igual; el bloque no pide llaves |
| 28 | 6 | capacidad   25 | 487 aciertos / 533 fallos (47.7 %), 19 solicitudes de red | 487 aciertos / 533 fallos (47.7 %), 19 solicitudes de red | 0 | cuenta: igual; el bloque no pide llaves |
| 29 | 6 | capacidad  100 | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 0 | cuenta: igual; el bloque no pide llaves |
| 30 | 6 | capacidad 1000 | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 0 | cuenta: igual; el bloque no pide llaves |

El +1 por cripta y versión de la consulta de llaves **no aparece** en este bloque: `adaptadores/bench_red_mejorado.py`
usa un `ClienteSintetico` propio, sin `obtener_llaves`, y llama directamente a `ServicioCripta` sin pasar por
`EstadoJuegoLogica.iniciarJuego`, que es lo único que pide las llaves. El +1 se mide en la sección D de
`--bench llaves` (1 / 0 / 0). Ninguna decisión de la Parte I deja de servir: las estrategias de precarga mantienen
63 / 61 / 33 / 9 solicitudes y la caché los mismos aciertos y fallos.

### Hallazgos y límites

1. **Una cripta incompleta en disco no se puede leer con `ClienteOffline`**: `obtener_criptas` solo devuelve las
   criptas completas y, si no hay ninguna, lanza `ErrorOffline("Ninguna cripta está guardada por completo. Juega una vez
   con conexión.")`. Por eso, en `FuenteSoloLocal`, solo `construir_sala` nombra la sala que falta («Falta en disco
   sala n de la cripta X»), porque comprueba `almacen.leer_contenido(cripta_id, numero_sala)` antes de delegar. Las demás
   operaciones sobre esa cripta fallan con un mensaje que no nombra el dato que falta: si no hay ninguna cripta
   completa, `DatoLocalFaltante` con el `ErrorOffline` de arriba como motivo; si hay otras completas, la incompleta no
   está en la lista y, desde T056, sale `DatoLocalFaltante("La cripta X no está en la lista de criptas guardada en
   disco")` (ver el punto 2).
2. **Una cripta desconocida sale como `DatoLocalFaltante` (corregido en T056)**: `ServicioCripta` lanza
   `ValueError(f"La cripta '{cripta_id}' no existe")`, y antes `FuenteSoloLocal._leer` solo convertía `ErrorOffline` y
   `LlavesNoDisponibles`. Desde T056 convierte también ese `ValueError` (solo el de ese mensaje exacto; los demás
   `ValueError` siguen saliendo tal cual) en `DatoLocalFaltante("La cripta X no está en la lista de criptas guardada en
   disco")`. `existe_cripta` sigue devolviendo `False` para una cripta que no está en la lista
   (`test_fuente_solo_local`, prueba de T056).
3. **`FuenteSoloLocal` se amplió en T053** por lo que pidió la capacidad 004: `existe_cripta` (solo existencia, sin
   comparar versión; sin lista en disco lanza `DatoLocalFaltante`), `version_catalogo` con `version_catalogo_vigente`,
   `objetos_que_suelta` con la última cripta consultada, `obtener_sala_salida`, `obtener_mapa` y
   `fijar_fichas_en_uso`. `crear_fuente_solo_local` acepta `version_catalogo_vigente=None`.
4. **`tests_labs/prueba_persistencia_partida.py` ya fallaba antes de esta capacidad**: llama a
   `original.guardarPartida(archivo)` sobre un `EstadoJuegoLogica`, y `EstadoJuegoLogica.guardarPartida` ya no existe:
   se separó en el commit `3fc1017` (2026-10-16, «separación de responsabilidad de guardar partida»), anterior al
   primer commit de la 009 (`57f8137`, 2026-11-06). Hoy `guardarPartida` está en `EstadoJuegoServicio`.
5. **El aviso de llaves salía con doble punto** («…con conexión.. La verificación…») cuando el motivo ya terminaba en
   punto. Se corrigió en `ServicioCripta.ubicacion_llaves` quitando el punto final del motivo
   (`str(error).rstrip('.')`), commit `291afa3`.
6. **Descuadres que ya estaban en `DOCUMENTACION_API.md`**: la tabla de §9 habla de una «cripta de 6 salas», pero el 7
   de la primera partida sale de `test_llaves_presupuesto`, que usa una cripta de 3 salas de la API falsa; y §8.3 dice
   «Primera vez: 6» mientras que `prueba_cliente_persistente` cuenta 7 (dos solicitudes de catálogo, fichas y botín).
7. **Regresión de `--bench guardado` y `--bench ciclo` que encontró T044**: desde T017, `EstadoJuegoLogica.iniciarJuego`
   pide las llaves, y el cliente sintético del bench (`ClienteDeBatalla`, en `bench/juego.py`) no tenía
   `obtener_llaves`. El `AttributeError` no es un `RuntimeError`, así que no se convertía en `LlavesNoDisponibles` y
   cortaba los dos bloques y `python main.py --bench` completo. Se corrigió en T054 agregando a `ClienteDeBatalla` un
   `obtener_llaves(cripta_id, solo_guardadas=False, limite_solicitudes=None)` que devuelve `[]` (cripta sin llaves).
   En el cierre final (T044) los dos bloques terminan y las 9 filas de conteo del bloque `cache` siguen iguales a T049.
8. **Criterio de tiempo intermitente del bloque `ciclo`**: el límite es de 20 ms para el peor de 30 ciclos. Es un
   criterio de la 001, no de las llaves: `bench/ciclo.py` no cambió en la 009 (su último commit es `793b300`, de la 001)
   y la partida del bench usa `ClienteDeBatalla`, sin llaves. En el cierre final (2026-11-08, con otro programa usando
   mucha CPU en la máquina), la fila «300 esbirros activos» no cumplió en ninguna de las tres corridas completas:
   mediana 22.31, 21.19 y 21.17 ms, y peor ciclo 42.61, 37.38 y 39.38 ms. En una corrida aislada de `--bench ciclo`
   dio una mediana de 15.73 ms y un peor ciclo de 29.39 ms. En esas mismas corridas también fallaron por poco
   «100 esbirros activos» (peor ciclo 20.11 y 25.52 ms en las corridas 1 y 3, y 32.32 ms en la aislada) y «50 cazadores
   persiguiendo» (20.95 ms en la corrida 2). Con la máquina libre el criterio se cumple con holgura: en dos corridas completas de `--bench`, «300 esbirros activos»
   dio mediana de 3.85 y 3.82 ms y peor ciclo de 5.76 y 5.71 ms, y el guardado A de Llaves B dio 14.37 y 14.80 ms (límite 50 ms), con código de salida 0 en las dos. Las cifras
   dependen de la carga de la máquina, y la decisión del guardado A se mantiene; ambas mediciones están en
   `specs/009-contrato-datos-v2/checklists/requirements.md`, «Implementación, cierre final (T044)».

## 004 · Línea de tiempo — consulta de estados pasados

- Especificación: [specs/004-linea-de-tiempo/spec.md](specs/004-linea-de-tiempo/spec.md) (FR-427 a FR-443)
- Plan: [specs/004-linea-de-tiempo/plan.md](specs/004-linea-de-tiempo/plan.md), con [research.md](specs/004-linea-de-tiempo/research.md)
- Benchmark: `bench/historia.py` (`python main.py --bench historia`). Cifras de una ejecución en Linux x86_64, Python 3.10, partida de 5 000 acciones con movimiento entre salas y 2 enemigos; en otra máquina cambian los valores absolutos, no las proporciones. Cada consulta se mide 10 veces por K (historia #k e historia <t> en inicio, mitad, cerca del final, justo en un punto de control y K-1 acciones después de uno).

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| **K = 10 por defecto** | Sí | Mediana 4.34 ms y máximo 5.25 ms con K=10 (límite FR-442: 50 ms). K=50: máximo 14.65 ms; K=100: máximo 27.42 ms. Los tres K cumplen en esta cripta sintética; el costo crece casi lineal con K (se reproducen hasta K-1 acciones, dos veces). Memoria: 501 puntos = 2 570.7 KB con K=10; 101 puntos = 518.4 KB con K=50; 51 puntos = 261.9 KB con K=100 (≈5.1 KB por punto). Con la cripta de 007 (50 esbirros por sala) el peor caso de reconstrucción fue K=50: 92 ms y K=100: 208 ms, que no caben en 50 ms; solo K=10 cabe en ambas. Por eso se conserva K=10 (menor latencia, ~2.5 MB por 5 000 acciones) y no depende de lo liviana que sea la cripta. |
| **Búsqueda binaria manual de puntos (sin `bisect`)** | Sí | Principio I. Con 500 puntos: binaria 1.09 µs contra lineal 13.48 µs (12.3×); con 5 000 puntos: 1.52 µs contra 180.90 µs (119.1×). La lista es contigua y ordenada por acciones y por instante; la poda del pergamino conserva ese orden. |
| **Reconstrucción hacia adelante desde el punto más cercano (§5.5)** | Sí | El historial del pergamino conserva solo `MAX_HISTORIAL = 5` acciones, así que reconstruir hacia atrás no es posible sin guardar cambios inversos de toda la partida. No se midió el costo hacia atrás porque el motor no lo permite. Hacia adelante: búsqueda en O(log M) y a lo más K-1 acciones vigentes. |
| **Alternativa descartada: reconstruir desde el inicio sin puntos de control** | Sí | `--bench historia`: 648.12 ms para 5 000 acciones, 149.3× la mediana de historia con K=10 y más de 12 veces el límite de 50 ms. |
| **Dos pasadas sobre el segmento entre dos puntos de control** | Distinto del plan inicial | El log no se trunca al usar un pergamino: conserva las acciones revertidas y el uso del pergamino, que además no restaura el azar. La pasada 1 simula el segmento en una instancia aislada y clasifica cada registro con `GestorEventos.es_uso_de_pergamino` (el catálogo no expone el tipo de un objeto por su id); una pila local deja las acciones vigentes. La pasada 2 vuelve a hidratar y reproduce fielmente hasta la acción o el instante pedido. El costo de ambas pasadas está incluido en las medidas anteriores. |
| **Aislamiento de la consulta** | Sí | Instancia aparte con `_es_aislada`: sin log en disco, sin precarga ni fichas en uso, sin llaves, con su propio azar y con el singleton `RetrocesoLogica` guardado y restituido en `try/finally`. `test_historia_aislamiento.py`, `test_historia_movimiento.py` y `test_historia_persistencia.py`: reloj, acciones, bitácora, log, azar, historial del pergamino, puntos de control, estado exportado y reporte de red/caché idénticos antes y después, también con movimiento, combate, pergamino y caché de 3 fichas. |
| **`historia <t>` en el instante de una decisión tras un pergamino** | Descubierto al implementar | El estado en ese instante incluye lo que ocurrió en la misma decisión (acciones revertidas y el pergamino ya consumido). La reconstrucción solo se detiene cuando el turno del jugador sigue pendiente en la agenda. |
| **Última acción que termina la partida** | Detalle nuevo | La acción se decide en el instante t y termina la partida en ese mismo instante: `historia <t>` muestra el estado final y `historia #N` el estado previo a esa acción. Por eso SC-002 (equivalencia entre `#k` y `<t>`) no aplica a esa última acción. |
| **Consulta en partida terminada** | Sí (clarificación aprobada) | `historia #N+1` entrega el estado final y las consultas funcionan en el bucle posterior a la partida. |


## 003 · Verificación de resolubilidad

- Especificación: [`specs/003-verificacion-resolubilidad/spec.md`](specs/003-verificacion-resolubilidad/spec.md) (FR-330 a FR-346)
- Plan: [`specs/003-verificacion-resolubilidad/plan.md`](specs/003-verificacion-resolubilidad/plan.md), con [`research.md`](specs/003-verificacion-resolubilidad/research.md)
- Mediciones: [`specs/003-verificacion-resolubilidad/mediciones.md`](specs/003-verificacion-resolubilidad/mediciones.md) (`python main.py --bench resolubilidad` y medición manual en las criptas publicadas)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| La llave de cada puerta viaja en la arista del mapa: `AristaMapaDTO.llave` y `AristaCripta.llave` (`str \| None = None`, al final y con valor por defecto); `ServicioCripta.esqueleto()` la copia de la salida de la API | Sí (`research.md` §1, primera tarea). T009: `--offline` (G3) y `FuenteSoloLocal` (G4) la heredaron **sin cambios** en esos adaptadores, porque la llave ya estaba en el esqueleto crudo guardado y bastó con no descartarla en `esqueleto()`; no hizo falta corregir `research.md` §1 | `test_mapa_con_llaves`: 6 de 6 (G1 a G6); G6 confirma que el esqueleto sigue haciendo exactamente las mismas solicitudes que en la línea base. Quien construye una arista con cuatro argumentos sigue funcionando (G5) |
| Un solo recorrido **incremental por oleadas** (`ColaCircular` para las salas, aristas cerradas en espera por número de llave), frente a repetir el recorrido completo desde la sala inicial en cada oleada | Sí (`research.md` §2) | `--bench resolubilidad` A: n = 300, **2,71 ms** frente a 198,41 ms; n = 3 000, **34,29 ms** frente a 220 792,58 ms, con el mismo resultado en los dos tamaños. D: razón t(3 000)/t(300) de **12,7** (límite 20) frente a 1 112,8. C: cadena de 10 000 salas, 58,51 ms; rejilla de 70 × 70, 16,00 ms (límite 200 ms). `Equivalencia.test_fr335_fr346_incremental_igual_a_repetida_en_criptas_al_azar` compara las dos estrategias en criptas al azar por semilla |
| Pendientes de cada oleada en `MonticuloMinimo` con la clave `(sala, número de llave)`; `MonticuloMinimo` se usa sin modificar aunque sus parámetros se llamen `costo` y `sala` | Sí (`research.md` §3; observación 6 del plan) | El desempate de FR-335 sale de la clave, porque los números de llave siguen el orden de los ids: `Determinismo.test_fr335_h3_2_dos_oleadas` (escenario H3-2 literal, orden `A`, `B`, `X`, `C`), `CasosB.test_b_r3_fr335_dos_ejecuciones_mismo_orden` y `Determinismo.test_fr335_orden_de_la_respuesta_no_importa`. Su costo está dentro de los tiempos de la incremental de A y C |
| `IndiceLlaves`: ids distintos ordenados con `ordenar_adaptativo` y `numero(id)` con búsqueda binaria escrita a mano, frente a búsqueda lineal | Sí (`research.md` §4) | `--bench resolubilidad` B (informativa): K = 100, **44,5 µs** frente a 108,0 µs; K = 1 000, **794,4 µs** frente a 11,11 ms; K = 10 000, **10,69 ms** frente a 1 194,44 ms (de 2,4 a unas 112 veces más rápida). `test_indice_llaves`: 8 pruebas, incluida la igualdad con la búsqueda lineal |
| Cuál ubicación se informa de una llave (el suelo antes que un enemigo y, entre enemigos, la menor instancia) se decide **aparte del montículo** (`_mejor_ubicacion`), recorriendo solo las ubicaciones de esa llave en la sala | Sí (`research.md` §3 y `data-model.md`). La implementación lo deja explícito: no depende de cómo desempata el montículo ante claves iguales | `Determinismo.test_fr335_suelo_antes_que_enemigo_y_menor_instancia` y `Determinismo.test_fr335_orden_de_la_respuesta_no_importa` (la respuesta de llaves invertida da el mismo orden) |
| Dónde vive cada parte: `DTO/ResultadoVerificacionDTO.py` (resultado), `Logica/VerificacionResolubilidad.py` (función pura `verificar_resolubilidad` y `verificar(fuente, cripta_id, llaves=None)`), `Logica/ReporteVerificacion.py` (texto), `Logica/IndiceLlaves.py`, `EstadoJuegoServicio.verificar` para el controlador; `FuenteCripta` gana `obtener_sala_inicial` y `obtener_llave_salida` | Sí (plan, «Resumen» punto 4 y «Estructura del proyecto») | `Contrato.test_fr344_firmas_de_la_interfaz` y `Contrato.test_fr344_fuente_entrega_sala_inicial_y_llave_salida`; `MismaOperacion.test_fr344_inicio_y_verificar_dan_el_mismo_resultado` (el inicio de partida y `--verificar` usan la misma operación). La revisión con búsqueda de importaciones y estructuras prohibidas es la de T063 |
| `CriptaNoResoluble` (subclase de `RuntimeError`, con el reporte como mensaje) se lanza dentro de `EstadoJuegoLogica.iniciarJuego`, después de `obtenerLlaves()` y antes de marcar la partida como iniciada, así que el servicio no llega a abrir el log | Sí (observación 3 del plan). T048 comprobó, sin cambios, que `EstadoJuegoServicio.iniciarJuego` la deja pasar antes de `_abrirLog` y que `comprobar_nombre()` no crea archivos | `Inicio.test_fr339_no_resoluble_no_inicia_y_no_crea_log` y `CasosB.test_b_r4_fr339_no_inicia_sin_forzar` (`AlmacenLogTexto.abrir` no se llama); `Inicio.test_fr339_reintento_tras_no_resoluble` |
| Códigos de salida de `--verificar` desde `ResultadoVerificacion.codigo_salida()`: 0 resoluble, 1 no resoluble, 2 error de datos (`resoluble is None` con `motivo_error`); un error de datos nunca da un resultado inventado | Sí (`research.md` §8) | `CodigosDeSalida.test_fr331_resoluble_0_no_resoluble_1_error_2`, `Contrato.test_fr331_codigo_salida` y las pruebas de FR-343 en `ErroresDeDatos` y `CasosLimite`. Conectar el código al proceso es de la capacidad de Fernanda |
| Un error de datos al **iniciar** (por ejemplo, la sala de salida no existe) no bloquea la partida: inicia con `avisoResolubilidad` = motivo + «La verificación de resolubilidad no está disponible.»; `--verificar` sobre la misma cripta termina con código 2 | Sí (observación 4 del plan) | `Inicio.test_fr339_h4_5_datos_invalidos_inicia_con_aviso` y `ErroresDeDatos.test_fr343_h4_5_sala_de_salida_inexistente` |
| T041: nada falló en T040, así que no se tocó la verificación ni ningún adaptador | Sí: sin cambios de código | Las 12 pruebas de T040 pasaron a la primera; cada una se comprobó con una mutación que la hace fallar (evidencia de T040 en `tasks.md`) |
| SC-003 aclarado en la spec: el arranque de la Parte I (lista de criptas y validación de versión) queda fuera de las «0 solicitudes» | **Cambió la especificación** (commit `62813ad`), no el código | Hallazgo de T040 y T041: con las llaves guardadas, una sesión nueva con `ClientePersistente` hace exactamente `("criptas", None)` y `("datos", id)`, que son del arranque de la Parte I y no de la verificación. `Solicitudes.test_fr341_llaves_guardadas_cero_solicitudes` exige esas dos y ninguna de llaves, salas ni contenido |
| La prueba de la 009 `test_llaves_partida_cargada.OtraCripta.test_fr325_e_restaurar_otra_cripta_no_arrastra_las_llaves_anteriores` inicia sus partidas con `forzar=True` | **Cambio en una prueba de otra capacidad** (grupo G, opción A de Scott) | Sus criptas «cripta-A» y «cripta-B» no tienen la llave de salida (`itm_llave_negra`): con FR-339 son no resolubles (`LLAVE_SALIDA_INEXISTENTE`) y no iniciaban. La prueba trata de las llaves al cargar una partida (FR-325), no de resolubilidad; el ayudante `jugar_y_exportar` ganó `forzar=False`. Suite completa: 375 pruebas OK |
| El oráculo de la estrategia repetida (`tests_labs/referencia_resolubilidad.py`, `verificar_repetida`) es más costoso de lo previsto | **Corrección de una previsión** del contrato y de `research.md` §9 («razón cercana a 100»), ya corregida en esos documentos | `--bench resolubilidad` D: razón **1 112,8** con tamaño ×10. Además de recorrer desde cero en cada oleada, el oráculo comprueba con búsquedas lineales (`_contiene`) si una llave ya se obtuvo, y su costo se acerca a O(K² · (S + E)). No cambia la conclusión: la incremental crece de forma lineal (12,7) y la descartada mucho más rápido. El oráculo no se modificó |
| Medición manual de la cripta publicada más grande **sin `FuenteSoloLocal`**: `ServicioCripta` sobre un cliente de disco temporal (una subclase de `ClienteOffline` sin el filtro de cripta completa), además de la función pura sola | **Se apartó del paso 3 de `quickstart.md`** (decisión de Scott, opción B; el paso 3 ya se alineó) | `ClienteOffline` exige la cripta completa, y cripta-06 (300 salas) tenía mapa, datos y llaves, pero no el contenido de las salas, que la verificación no usa y que costaría solicitudes descargar. `ClientePersistente` necesita red en el arranque de la Parte I. Resultado: cripta-06 **resoluble en 2,925 ms** (verificación completa) y 0,391 ms (función pura), 0 solicitudes y `datos_cripta/` sin cambios (sha1). Cumple FR-345 y SC-006 |
| cripta-05 («Cripta sellada») es una cripta **real no resoluble** y no inicia sin `--forzar` | Sí: es lo que pide FR-339; no se corrigió ni se ocultó | Medición manual (T057): la llave de salida `itm_llave_negra` (sala 23) y `itm_llave_hierro` (sala 24) están detrás de las puertas que ellas mismas abren (tres bloqueos de tipo ciclo); 20 salas alcanzables y 4 no alcanzables. El reporte completo está en `mediciones.md`, junto con otras dos observaciones de los datos reales: la versión de cripta-02 cambió (`8091a5cd8b7c` a `52532a77ee04`) y eso vació su contenido guardado; cripta-01 ya no está en la lista guardada de criptas |

### Hallazgos y límites

1. **El `--bench` completo se cortaba en los bloques `guardado` y `ciclo` (T064).** La cripta sintética de esos bloques (`ClienteDeBatalla`, en `bench/juego.py`) declara `itm_llave` como llave de salida en sus datos generales, pero no ubicaba esa llave en ninguna sala. Con FR-339, la partida del bench verificaba la cripta, la encontraba no resoluble y no iniciaba (`CriptaNoResoluble`). Se arregló en los datos del bench, no en el modelo: `obtener_llaves` devuelve `itm_llave` en el suelo de la sala 1, así que la cripta es resoluble y la partida del bench inicia y verifica igual que una real. Lo que miden los bloques no cambia: la ubicación de la llave no entra al estado guardado (1 000 salas: 408 092 B, igual que en la 001) ni cuenta como solicitud. No se vio antes porque T056 solo corrió `--bench resolubilidad`. Es la misma clase de fallo que la regresión de la 009 (T054, punto 7 de su sección): un cambio en el inicio de partida que el cliente sintético del bench no acompañaba.
2. **Datos generales sin `sala_salida` o sin `sala_inicial` (T065).** `ServicioCripta.obtener_sala_inicial` y `obtener_sala_salida` leen esos campos con `[]`, y `verificar` dejaba escapar el `KeyError`. Ahora `verificar` lo traduce a un error de datos (`resoluble=None`, código 2) con el motivo «Datos inválidos en la cripta X: faltan los datos generales «campo».», sin cambiar el adaptador. Sin `sala_salida`, `iniciarJuego` inicia con aviso, como cualquier otro error de datos (FR-339, H4-5). Sin `sala_inicial`, `verificar` también da código 2, pero una partida nueva no puede iniciar: `ServicioCripta.crear_jugador` (Parte I) necesita la sala inicial para ubicar al jugador y falla antes de llegar a la verificación. No se cambió ese adaptador; queda como límite conocido, fuera de la 003. Pruebas: `ErroresDeDatos.test_fr343_t065_datos_generales_sin_sala_inicial_ni_sala_salida` y `ErroresDeDatos.test_fr339_h4_5_t065_sin_sala_salida_la_partida_inicia_con_aviso`.
3. **Con `--offline`, la cripta tiene que estar guardada completa.** Aunque la verificación solo usa el mapa, los datos generales y las llaves, el modo sin red solo ve las criptas guardadas completas, contenido de todas las salas incluido (capacidad 009). Una cripta a la que le falta algo se informa como inexistente y `--verificar` termina con código 2. Lo encontró T065 con cripta-06 y quedó escrito en FR-342 y en el escenario H5-2 (commit `9d610a2`); el programa no cambió. Por esto mismo, la medición de cripta-06 se hizo sin `FuenteSoloLocal` (ver la tabla).

## 006 · Comando «ir a»

- Especificación: [`specs/006-ir-a/spec.md`](specs/006-ir-a/spec.md) (FR-231 a FR-252)
- Plan: [`specs/006-ir-a/plan.md`](specs/006-ir-a/plan.md), con [`research.md`](specs/006-ir-a/research.md)
- Mediciones: `python main.py --bench ir_a` (`bench/ir_a.py`, contrato en [`contracts/bench-ir-a.md`](specs/006-ir-a/contracts/bench-ir-a.md))
- Estado: las seis historias implementadas; `--bench ir_a` en CUMPLE. **Pendientes abiertos**: en 20 000 salas (2 000 exploradas) el paso que captura un punto de control (007) y el recálculo desde cero tras una puerta cerrada superan 5 ms (ver Hallazgos y límites).

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| Ruta con `distancias_hacia` + `siguiente_paso`; el desempate de FR-234 sale de elegir el menor id entre los pasos de una ruta óptima | Sí | `--bench ir_a` A: coincide con la enumeración de rutas en 18 criptas (3x3, 4x4, 5x5). La enumeración gana en 3x3 (163 µs frente a 496 µs) y pierde desde 4x4 (1,25 ms frente a 0,85 ms) y claramente en 5x5 (8,09 ms frente a 1,37 ms); crece de forma exponencial |
| Cada paso es un `MOVER_JUGADOR` entregado a `accionJugador`, más `ingresarEnSala` | Sí, **con una corrección de un supuesto del plan** | `--bench ir_a` B: viajar y caminar a mano dejan el mismo estado. El plan creía que los dormidos se activan solo al pedir la sala; en realidad se activan dentro del movimiento (`cargar_sala`), así que el daño de un enemigo recién despertado cae en el mismo paso. Por eso las causas de parada tienen el orden MUERTE, LLEGADA, DORMIDOS, ENEMIGO ACTIVO, DAÑO |
| Recálculo solo si cambia `version_conocimiento`, **con cota de costo** (la ruta que queda cuesta `restante`) | **Cambió respecto del plan original** (el plan elegía la versión sin cota y dejaba la cota condicionada a la medición) | `--bench ir_a` C y G: sin cota, un recálculo cerca del destino costaba 10 a 15 ms en 20 000 salas; con cota, el máximo del paso sin captura es 1,3 ms. En C la cota fija 2 salas frente a 201 (antorcha, 2 000 salas). H: las tres políticas deciden igual |
| Detención por comprobaciones de la sala actual con un contador de activaciones | Sí | `--bench ir_a` D: se examinan exactamente los enemigos de la sala en los tres tamaños (0, 10 y 100); revisar el contenido de la ruta examinaría 12 000 con 100 enemigos y 120 pasos |
| Pergamino: un nodo del historial por paso y aviso de cancelación | Sí | `--bench ir_a` E: revertir un paso cuesta 57 µs (sin antorcha) y 70 µs (con antorcha) y quita exactamente una acción del historial |
| Registro: marcas `IR_A` y `FIN_IR_A` y pasos como movimientos normales | Sí; **el detalle C2 del análisis no hizo falta** | `--bench ir_a` F: el registro crece en pasos + 2 y repetir con y sin marcas deja la misma partida (10, 100 y 1 000 pasos); repetir 100+100 pasos: 16,8 ms con marcas y 16,7 ms sin ellas |
| Comando `ir a <id>` en el controlador; el rechazo no pasa por `accionJugador` | Sí | `test_viaje_comando`, `test_viaje_rechazo` |
| No se guarda un viaje en curso; formato 8 y estado 5 sin cambios | Sí | `test_viaje_registro` (guardar y cargar con un viaje hecho) |

### Hallazgos y límites

1. **Los dos casos de 20 000 salas que superan 5 ms no son de la ruta.** (a) Un paso en que se captura un punto de control (capacidad 007, cada K = 10 acciones) cuesta 7 a 15 ms porque copia el estado completo, incluido el conocimiento (O(V)); aparece con cualquier acción, no solo con «ir a». (b) Recalcular desde cero el campo de 2 000 salas exploradas tras descubrir una puerta cerrada cuesta unos 12 ms: ahí no hay cota posible (la ruta anterior dejó de valer). Con 200 salas exploradas el mismo recálculo cuesta 0,8 ms. Arreglarlo exige un recálculo incremental o capturar puntos de control con costo proporcional a lo cambiado; ninguna de las dos cosas está en el alcance de esta capacidad.
   **Mapa conocido completo (enunciado §6.1).** Medido con todas las salas exploradas (sección I de `--bench ir_a`): 400 salas, máximo de las medianas por paso 1,4 ms con una puerta cerrada en la ruta (cumple, criterio duro); 2 000 salas, 1,8 ms sin puertas cerradas y 6 a 10 ms con una puerta cerrada; 20 000 salas, 17 a 120 ms. La cripta de referencia aún no está publicada y la mayor publicada tiene 300 salas, así que FR-251/SC-205 exigen 5 ms con el mapa completo hasta 400 salas y con el 10 % explorado hasta 2 000; lo demás se informa. Antes de esta medición el criterio decía «hasta 2 000 salas» sin precisar cuánto estaba explorado.
2. **Medición sin pausas del recolector de basura.** En 20 000 salas una pausa del recolector, de unos 10 ms, cae en un paso cualquiera; los pasos se miden con el recolector apagado (como `timeit`) y el bloque `ciclo` mide el ciclo completo.
3. **Hallazgo en la 002 (no corregido aquí).** `MapaConocido._posicion_adyacente` compara por identidad contra todas las salidas de la sala origen de cada arista entrante, así que cerrar la puerta este de la sala 2 con el jugador en la sala 1 la marca cerrada en el mapa aunque esa puerta no conecta la sala 1 (FR-207 pide observarla solo en las dos salas que conecta). Las pruebas de B-N2 usan una puerta a dos salas del jugador.
4. **Los bloques repetidos con la carga nueva** (`mapa`, `retroceso`, `ordenamiento`, `ciclo`) siguen en CUMPLE; ninguna decisión de la Parte I ni de la 002 dejó de servir. El ciclo con 10 y 50 cazadores quedó en 0,4 ms y 2 ms.
5. **Entorno.** En esta máquina falta el paquete `requests`, por lo que 16 módulos de prueba de la línea base no se pueden importar (`ErrorSinConexion` de `adaptadores/cliente_http.py`); es anterior a esta capacidad y no cambió con ella.

## 011 · Arranque verificado y pantallas de consola claras

- Especificación: [`specs/011-arranque-verificado-pantallas/spec.md`](specs/011-arranque-verificado-pantallas/spec.md) (FR-301 a FR-317)
- Plan: [`specs/011-arranque-verificado-pantallas/plan.md`](specs/011-arranque-verificado-pantallas/plan.md), con [`research.md`](specs/011-arranque-verificado-pantallas/research.md) (decisiones D1 a D8) y [`contracts/`](specs/011-arranque-verificado-pantallas/contracts/)
- Mediciones: `python main.py --bench pantallas` (`bench/pantallas.py`, contrato en [`contracts/bench-pantallas.md`](specs/011-arranque-verificado-pantallas/contracts/bench-pantallas.md)) y `python main.py --bench ciclo` repetido
- Estado: las dos historias implementadas; 711 pruebas en CUMPLE (635 de la línea base + 76 nuevas); `--bench pantallas` en CUMPLE.

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| D1. El servicio entrega las líneas del reporte (`reporteVerificacion`, `lineasDeReporte`); el controlador las pasa a la vista; un rechazo atrapa `CriptaNoResoluble` en el controlador | Sí | `test_arranque_verificado`: el reporte sale antes del primer turno con cripta resoluble, no resoluble, con y sin `--forzar` |
| D2. Pantalla de sala como función pura (`Pantallas.texto_sala`), lista de líneas + `"\n".join` | Sí | `--bench pantallas` A: elegida 8,3 µs / 29,8 µs / 216,4 µs (0 / 10 / 100 enemigos); la **descartada** (`+=`) 12,7 / 41,1 / 280,5 µs, de 1,30 a 1,53 veces más lenta; texto idéntico; sala con 100 enemigos 0,22 ms (máx 0,30 ms), muy por debajo de 20 ms |
| D3. Ayuda y validación de sintaxis desde una sola lista de tuplas `COMANDOS`, con búsqueda lineal | Sí | `--bench pantallas` C: la ayuda cuesta 7,5 µs; el texto fijo (descartado) 0,2 µs, pero se desactualiza; `test_pantallas_texto` comprueba que cada comando reconocido está en la tabla y al revés |
| D4. Códigos de salida en `main.py`, con las constantes con nombre; el valor lo da `ResultadoVerificacion.codigo_salida()` (003) | **Sí, con un matiz**: el plan decía que `main.py` asignaba los códigos; como la 003 ya los decide en el DTO, `main.py` solo los nombra y devuelve `resultado.codigo_salida()` (una sola fuente de verdad; hallazgo D1 del análisis) | `test_arranque_verificado`: 0, 1 y 2 con cripta resoluble, no resoluble, inexistente y datos no disponibles |
| D5. `forzar` viaja por parámetros: `main.py` → `ControladorJuego(..., forzar=)` → `iniciarJuego(..., forzar=)` | Sí | `test_arranque_verificado` (servicio espiado: llega `True` con `--forzar` y `False` sin él) |
| D6. Datos del resumen final: el controlador junta valores que ya existen (`terminado`, `puntaje`, `finPartida`, vida, `mapaConocido`); no se amplió `FinPartidaDTO` | Sí | `test_pantallas_texto` (texto exacto) y `test_pantallas_controlador` (muerte y llegada) |
| D7. Mensajes de rechazo y error con `texto_error(qué_pasó, qué_hacer)` y un catálogo de 39 mensajes en `Pantallas.py`; sin `print` suelto de rechazos en el controlador | Sí | `test_pantallas_texto` (dos partes, español, sin colores) y `test_pantallas_controlador` (el controlador no imprime rechazos con texto suelto) |
| D8. La puerta que el jugador no ha observado se muestra «sin observar» | Sí (se añadió el supuesto a la spec antes del código, principio X) | `test_niebla_vista`, `test_pantallas_texto` |

### Hallazgos y límites

1. **`--bench ciclo` repetido con la carga nueva.** Antes del cambio: 100 esbirros 2,67 ms (máx 7,50), 300 esbirros 8,41 ms (máx 16,14), 50 cazadores 2,23 ms (máx 3,27). Después, tres ejecuciones: 100 esbirros 2,77 a 3,51 ms; 300 esbirros 8,43 a 12,63 ms (máx **14,24, 17,20 y 22,73 ms**); 50 cazadores 3,13 a 5,17 ms de máximo. **Una de las tres ejecuciones mostró 22,73 ms de máximo con 300 esbirros** (NO CUMPLE), con las medianas de todo el bloque unas 1,5 veces más altas, incluidas las cargas de cazadores; las dos ejecuciones siguientes dieron CUMPLE. El ciclo de eventos no se tocó (esta capacidad no modifica `Logica/`, `DTO/` ni `adaptadores/`) y las pantallas se construyen entre dos decisiones del jugador, fuera del ciclo; se atribuye a ruido de la máquina, pero queda registrado sin ocultarlo.
2. **Códigos de salida.** `--verificar`: 0 resoluble, 1 no resoluble, 2 error de uso o lectura. Un rechazo por cripta no resoluble sin `--forzar` sale con 1 (igual que antes); sin criptas disponibles, también 1.
3. **`cerrar` no es un comando.** El texto anterior del prompt lo anunciaba, pero el controlador nunca lo reconoció; la ayuda no lo lista. No se agregó el comando (no estaba en ninguna especificación).
4. **Corrección de textos de `main.py` (FR-308).** Los mensajes de `--replay`, `--cache-size` y `--hasta` se guardaban con la codificación doble («tamaÃ±o», «ReproducciÃ³n»); se corrigieron a UTF-8 correcto.
5. **Laboratorio roto, ajeno a la capacidad (arreglado después, 2026-11-18).** `tests_labs/prueba_reporte_solicitudes.py` fallaba desde antes: sus teclas simuladas no incluían la pregunta de la tabla de puntajes. No se arregló en esta capacidad; después se agregó la respuesta «n» al inicio de las teclas del caso 1 y el laboratorio pasa (17 de 17 comprobaciones, código 0).
6. **Entorno.** Con el Python del sistema falta `requests` (16 módulos no se importan); las pruebas se ejecutan con `.venv/Scripts/python.exe`.
7. **`--bench` completo con `main` ya integrado (2026-11-18).** Corrida de `python main.py --bench` en `Fernanda-persona4`, con `main` integrado (incluye la 012) y los commits `03267c4` y `48f4a0e` ya hechos: **sale con código 0**, sin `Traceback`, y todos los veredictos finales en CUMPLE (§5.2, replay, puntos de control, recorrido por niveles, mapa conocido, ir a, llaves, resolubilidad y pantallas). Hay dos `NO CUMPLE` que no cambiaron el código de salida: los 1000 esbirros del ciclo (prueba de estrés, así rotulada en la propia salida) y `historia K=100` de la 004 (máx 85,32 ms en esta corrida; 27,13 ms de máximo en la corrida anterior del mismo día; el K por defecto, 10, cumple con 9,19 ms). Los `SUPERA 5 ms` de «ir a» son informativos (FR-251). Al redirigir la salida a un archivo en Windows hay que forzar UTF-8 (`$env:PYTHONUTF8 = "1"`), porque la flecha de «binario → DTO» no cabe en cp1252 y el `--bench` se corta con `UnicodeEncodeError`.

## 012 · Revisión de la Parte I con la carga nueva

- Especificación: [`specs/012-revision-parte-i/spec.md`](specs/012-revision-parte-i/spec.md) (FR-370 a FR-388, con las correcciones H1 a H3, L1 y L2)
- Plan: [`specs/012-revision-parte-i/plan.md`](specs/012-revision-parte-i/plan.md), con [`research.md`](specs/012-revision-parte-i/research.md) (decisiones D1 a D5 y hallazgos H1 a H3)
- Mediciones: [`specs/012-revision-parte-i/mediciones.md`](specs/012-revision-parte-i/mediciones.md). Contiene M0 (el antes, código de `0b031ec`), M1 (la carga nueva con el mismo código), M2 (el después, commit `70c9854`), con tres ejecuciones de `python main.py --bench cache` y de `python main.py --bench guardado` en cada paso, la medición manual y el anexo del inventario.
- Estado: D1 y D2 implementadas; todas las filas cumplen su límite; el criterio de cambio de D2 (T034) no aplica.

| Decisión | ¿Coincide con el plan? | Medición o motivo |
|---|---|---|
| D1 · Planeación de la vecindad (`salas_vecinas`): recorrido por niveles sobre la propia lista de salas alcanzadas, leída con un índice y con una marca de fin de nivel, sin cola de biblioteca. **Se mantiene** la estrategia; cambia la estructura | Sí (research D1, opción a) | Fila 23 (1 paso): 18.6 µs en M2 contra 20.2 µs en M0. Fila 24 (2 pasos): 46.6 µs contra 48.6 µs. Límites: 40.40 y 97.20 µs. Las filas 1 a 4 y 26 a 30 son iguales en M1 y M2: la respuesta y la cantidad de lecturas no cambian. **No se reutiliza `ColaCircular`** (research D1, opción b): guardaría una copia de lo que ya está en la lista de salas alcanzadas, y como solo guarda enteros haría falta una segunda cola para el nivel, o codificar sala y nivel en un entero, lo que exige una cota de salas |
| D2 · Caché de fichas (`CacheLRU`): lista propia con la más reciente al final y búsqueda lineal sin índice. **Se mantiene** la política LRU con contador de uso; cambia la estructura | Sí (research D2, opción a). El criterio de cambio (T034) **no aplica** | Sección 2, «lista propia lineal»: la fila más cercana a su límite es la 9 (100 fichas, fallo), con 2.14 µs en M2 contra 2.13 µs en M0 (1.00 ×, límite 4.26 µs). Las filas de acierto bajan entre 27 % y 46 %; por ejemplo, la fila 11 (1 000 fichas) pasa de 33.93 a 18.46 µs. La lista enlazada propia descartada (filas 31 a 34) no mejora: 20.98 µs con 1 000 fichas contra 18.46 µs |
| Capacidad de la caché (25 por defecto). **Se mantiene** | Sí | Sección 6 en M2: con capacidad 25 (fila 28) da 553 aciertos y 630 fallos (46.7 %); con 100 y 1 000 (filas 29 y 30), 1112 aciertos y 71 fallos (94.0 %). Las solicitudes de red son 64 con todas las capacidades (filas 26 a 30): lo que la caché no conserva se lee del disco. Las cuentas son iguales en M1 y M2 |
| Precarga (perezosa por lotes de 10). La regla **no cambia** (FR-324): aquí solo se registran sus filas | Sí | Sección 1 en M2: sala por sala, 64 solicitudes (fila 1); actual + vecinas, 62 (fila 2); perezosa de profundidad 2, 56 (fila 3); perezosa por defecto, 46 (fila 4). Todas son iguales a M1. El aumento desde M0 (63 / 61 / 33 / 9) se debe a la carga (ver «Hallazgos y límites», punto 5) |
| Catálogo en disco (archivo indexado). **Se mantiene** | Sí | Recuperar una ficha liberada (filas 17 a 19): 0.071, 0.178 y 0.437 ms con 25, 200 y 1 000 fichas, frente a unos 400 ms de una solicitud real. Guardar 10 fichas (filas 20 a 22): 2.331, 9.941 y 10.758 ms. Todas las filas quedan por debajo de 2 × M0 |
| Formato binario de partida (formato 8). **Se mantiene**; no se tocó (`AlmacenPartidaBinario`, `codec_partida` y los DTO de guardado quedan fuera de alcance) | Sí | Bloque `guardado` en M2. Con 1 000 salas: guardar tarda 35.98 ms (G21), cargar todo 57.61 ms (G23) y cargar UNA sala 81.7 µs (G25), contra 10.13 ms del JSON, que tiene que leer todo (G26). Leer UNA sala lee 359 a 397 bytes de 400,347 (G42 a G44) y 9 a 10 entradas (≤ ⌊log₂ n⌋ + 1 = 10, G48). Todas las filas de tiempo quedan por debajo de su límite |

### Inventario de usos prohibidos

**Criterio de exclusión**: el inventario cubre el código de producción (`adaptadores/`, `Controlador/`, `DTO/`,
`Logica/`, `model/`, `Servicio/` y `main.py`). Quedan fuera:
- las pruebas (`test_*.py`, `tests_labs/`, `Pruebas.py`);
- el código de medición (`bench/` y `adaptadores/bench_red*.py`, que viven en `adaptadores/` pero solo se ejecutan con `--bench` o a mano);
- los scripts auxiliares (`descargar_cripta.py`).

El criterio es la función del archivo, no la carpeta. La búsqueda y la revisión a mano de las 18 apariciones de `dict`
y de los conjuntos literales están en el anexo de [`mediciones.md`](specs/012-revision-parte-i/mediciones.md) (T037 a T039).

| Ubicación | Estructura | Para qué | ¿Problema evaluado de §5? | Destino | Texto |
|---|---|---|---|---|---|
| `adaptadores/servicioCripta.py` `salas_vecinas` | cola de biblioteca de pares `(sala, nivel)` | recorrido por niveles de la vecindad | sí (planeación de la vecindad) | **corregido** (D1) | recorre la propia lista de salas alcanzadas con un índice y una marca de fin de nivel |
| `adaptadores/cache.py` `CacheLRU` | cola de biblioteca de entradas | caché LRU de fichas | sí (caché de fichas) | **corregido** (D2) | lista propia con la más reciente al final |
| `DTO/SalaDTO.py:33` | `deque(maxlen=4)` | salidas de la sala, en el orden N, S, E, O | no | **justificado** (uso 3) | ver «Justificaciones» |
| `adaptadores/servicioCripta.py:523` `_armar_salidas` | `deque(maxlen=4)` | arma las salidas de la sala desde la respuesta de la API | no | **justificado** (uso 4) | ver «Justificaciones» |
| `Logica/EstadoGuardadoLogica.py:285` | `deque(..., maxlen=4)` | rearma las salidas al cargar una partida | no | **justificado** (uso 5) | ver «Justificaciones» |
| `Logica/GestorEventos.py:2` | `collections.abc.Callable` | anotación de tipo de dos parámetros | no: no es una estructura | **justificado** (uso 6) | ver «Justificaciones» |
| `adaptadores/servicioCripta.py:90, 93, 115` `normalizar_esqueleto` | `dict(sala)`, `{}` y `dict(salida)` | copia del esqueleto con la forma del JSON de la API y el costo resuelto | no: lectura de JSON | **excluido** (uso 7) | es la respuesta JSON o una copia con su misma forma (supuesto de la spec); no se busca por clave como índice |
| `adaptadores/resolucion.py:41, 72` | `dict(ficha)` | copia de la ficha JSON para construir el objeto | no: lectura de JSON | **excluido** (uso 8) | igual que el uso 7; la copia se descarta al construir el objeto |
| `adaptadores/extension.py:20` | conjunto literal de 3 separadores de ruta | comprobar que un nombre de archivo no trae carpetas | no | **justificado** (uso 9) | ver «Justificaciones» |
| `Logica/EstadoJuegoLogica.py:884, 900, 1248` | conjuntos literales de 2 tipos de acción | comprobar pertenencia al reconstruir un evento | no | **justificado** (uso 10) | ver «Justificaciones» |
| las otras 15 apariciones de `: dict` (anotaciones en `AlmacenDisco.py`, `llaves.py`, `resolucion.py` y `servicioCripta.py`) | anotación `dict` | parámetros y atributos que reciben la respuesta JSON | no: lectura de JSON | **excluidas** | revisadas una por una en el anexo de `mediciones.md` (T038); ninguna es índice ni caché |

**Justificaciones** (FR-386):

- **Usos 3 a 5: el contenedor de salidas de la sala.** `SalaDTO.salidas` es un `deque(maxlen=4)` con las salidas que
  existen, en el orden N, S, E, O. `_armar_salidas` lo arma desde el objeto `salidas` de la API, y la carga de partida
  lo rearma desde las salidas guardadas. Guarda como máximo 4 elementos, que se recorren en orden. Nadie busca por
  clave en él ni lo usa como caché, así que no es un índice ni una caché. Corregirlo significaría cambiar el tipo en el
  DTO, en la conversión desde la API y en la carga de partida, más las pruebas de formato. Es un cambio mecánico, pero
  toca el formato de partida y su reconstrucción, que esta capacidad deja fuera de alcance (`DTO/SalaDTO.py`,
  `Logica/EstadoGuardadoLogica.py` y el formato no se tocan).
- **Uso 6: `collections.abc.Callable`.** Solo es una anotación de tipo para dos parámetros de `GestorEventos`. No
  guarda datos ni es una estructura. Corregirlo sería cambiar la anotación, sin efecto en la ejecución.
- **Usos 9 y 10: conjuntos literales constantes** (T039: se justifican tal cual). Son constantes de 2 o 3 elementos
  (4 con `os.altsep`), escritas en la línea donde se usan, y solo sirven para comprobar pertenencia. No guardan datos
  del juego, no crecen y nadie los consulta como índice ni como caché. Pasarlos a tuplas costaría cuatro líneas, pero
  no cambia nada observable ni la complejidad, y obligaría a repetir las pruebas de equivalencia (T030) sin ninguna
  ganancia.

### Antes y después

Tablas copiadas de [`mediciones.md`](specs/012-revision-parte-i/mediciones.md) («Tabla por bloque»). M0: código de
`0b031ec`. M1: la carga nueva con el mismo código. M2: el después, en el commit `70c9854`. Cada fila de tiempo es la
mediana de tres ejecuciones; las filas de cuenta salen iguales en las tres.

Antes = M0 y Carga = M1 (mediana en las filas de tiempo; valor común en las de cuenta). Después = M2, con el mismo criterio. **Límite** (T033, FR-383 y FR-384): 2 × M0; 2 × M1 en las filas nuevas (sin antes en M0) y en las filas de red que la carga ya llevó a más del doble de M0 (fila 4 y filas 26 a 30, corrección L1 de la spec). En las filas de cuenta de red el límite se aplica a las solicitudes. Los tamaños en disco no tienen límite (FR-384 limita guardar, cargar y leer). **Resultado: todas las filas cumplen.** La más cercana a su límite es la fila 3 (perezosa, prof. 2): 56 solicitudes contra 66 (2 × M0), 1.70 × M0, por la carga (+1 llaves y 44 disparadas por cazadores); el código no la mueve (M2 = M1).

#### Bloque `cache`

| # | Sección | Medición | Tipo | Antes (M0) | Carga (M1) | Después (M2) | Diferencia | Límite (2×) | Cumple | Causa |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1. Solicitudes al recorrer un pasillo de 60 salas | sala por sala (sin precarga) | cuenta | 63 solicitudes (~25.2 s de espera) | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | +1 solicitudes vs M0 (+1.6 %); +0 vs M1 | 126 solicitudes (2 × M0) | sí | carga (M0 → M1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 2 | 1. Solicitudes al recorrer un pasillo de 60 salas | actual + vecinas en cada paso (prof. 2) | cuenta | 61 solicitudes (~24.4 s de espera) | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | +1 solicitudes vs M0 (+1.6 %); +0 vs M1 | 122 solicitudes (2 × M0) | sí | carga (M0 → M1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 3 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, prof. 2 | cuenta | 33 solicitudes (~13.2 s de espera) | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | +23 solicitudes vs M0 (+69.7 %); +0 vs M1 | 66 solicitudes (2 × M0) | sí | carga (M0 → M1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 4 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, por defecto (lote de 10) | cuenta | 9 solicitudes (~3.6 s de espera) | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | +37 solicitudes vs M0 (+411.1 %); +0 vs M1 | 92 solicitudes (2 × M1) | sí | carga (M0 → M1), que la llevó a más del doble de M0, por eso el límite es 2 × M1 (FR-383, corrección L1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 5 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 25 fichas, acierto | tiempo | **1.1 µs** | **1.05 µs** | **0.8 µs** | −0.30 µs (-27.3 %) | 2.20 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 6 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 25 fichas, fallo | tiempo | **0.64 µs** | **0.55 µs** | **0.6 µs** | −0.04 µs (-6.3 %) | 1.28 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 7 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 25 fichas, acierto (descartada) | tiempo | **0.2 µs** | **0.2 µs** | **0.2 µs** | ±0.00 µs (+0.0 %) | 0.40 µs (2 × M0) | sí | sin cambio de código; depende de la máquina |
| 8 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 100 fichas, acierto | tiempo | **3.07 µs** | **3.1 µs** | **2.25 µs** | −0.82 µs (-26.7 %) | 6.14 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 9 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 100 fichas, fallo | tiempo | **2.13 µs** | **1.96 µs** | **2.14 µs** | +0.01 µs (+0.5 %) | 4.26 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 10 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 100 fichas, acierto (descartada) | tiempo | **0.23 µs** | **0.21 µs** | **0.22 µs** | −0.01 µs (-4.3 %) | 0.46 µs (2 × M0) | sí | sin cambio de código; depende de la máquina |
| 11 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 1000 fichas, acierto | tiempo | **33.93 µs** | **30.15 µs** | **18.46 µs** | −15.47 µs (-45.6 %) | 67.86 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 12 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 1000 fichas, fallo | tiempo | **19.53 µs** | **18.17 µs** | **19.12 µs** | −0.41 µs (-2.1 %) | 39.06 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 13 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 1000 fichas, acierto (descartada) | tiempo | **0.27 µs** | **0.26 µs** | **0.26 µs** | −0.01 µs (-3.7 %) | 0.54 µs (2 × M0) | sí | sin cambio de código; depende de la máquina |
| 14 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 5000 fichas, acierto | tiempo | **172.4 µs** | **173.42 µs** | **107.81 µs** | −64.59 µs (-37.5 %) | 344.80 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 15 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 5000 fichas, fallo | tiempo | **97.48 µs** | **96.81 µs** | **96.46 µs** | −1.02 µs (-1.0 %) | 194.96 µs (2 × M0) | sí | código: la caché pasó a lista propia (D2, sin índice al recorrer); depende de la máquina |
| 16 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 5000 fichas, acierto (descartada) | tiempo | **0.33 µs** | **0.33 µs** | **0.3 µs** | −0.03 µs (-9.1 %) | 0.66 µs (2 × M0) | sí | sin cambio de código; depende de la máquina |
| 17 | 3. Recuperar una ficha liberada desde disco | catálogo con 25 fichas | tiempo | **0.092 ms por lectura (una solicitud real: ~400 ms)** | **0.071 ms por lectura (una solicitud real: ~400 ms)** | **0.071 ms por lectura (una solicitud real: ~400 ms)** | −21.00 µs (-22.8 %) | 184.00 µs (2 × M0) | sí | carga: la ficha leída es de cazador; sin cambio de código; depende de la máquina |
| 18 | 3. Recuperar una ficha liberada desde disco | catálogo con 200 fichas | tiempo | **0.167 ms por lectura (una solicitud real: ~400 ms)** | **0.149 ms por lectura (una solicitud real: ~400 ms)** | **0.178 ms por lectura (una solicitud real: ~400 ms)** | +11.00 µs (+6.6 %) | 334.00 µs (2 × M0) | sí | carga: la ficha leída es de cazador; sin cambio de código; depende de la máquina |
| 19 | 3. Recuperar una ficha liberada desde disco | catálogo con 1000 fichas | tiempo | **0.42 ms por lectura (una solicitud real: ~400 ms)** | **0.426 ms por lectura (una solicitud real: ~400 ms)** | **0.437 ms por lectura (una solicitud real: ~400 ms)** | +17.00 µs (+4.0 %) | 840.00 µs (2 × M0) | sí | carga: la ficha leída es de cazador; sin cambio de código; depende de la máquina |
| 20 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 25 fichas | tiempo | **2.216 ms** | **2.165 ms** | **2.331 ms** | +115.00 µs (+5.2 %) | 4.43 ms (2 × M0) | sí | sin cambio de código; depende de la máquina |
| 21 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 200 fichas | tiempo | **9.649 ms** | **8.72 ms** | **9.941 ms** | +292.00 µs (+3.0 %) | 19.30 ms (2 × M0) | sí | sin cambio de código; depende de la máquina |
| 22 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 1000 fichas | tiempo | **10.829 ms** | **8.77 ms** | **10.758 ms** | −71.00 µs (-0.7 %) | 21.66 ms (2 × M0) | sí | sin cambio de código; depende de la máquina |
| 23 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 1 paso | tiempo | **20.2 µs** | **19.2 µs** | **18.6 µs** | −1.60 µs (-7.9 %) | 40.40 µs (2 × M0) | sí | código: la vecindad recorre su propia lista (D1); depende de la máquina |
| 24 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 2 pasos | tiempo | **48.6 µs** | **45.0 µs** | **46.6 µs** | −2.00 µs (-4.1 %) | 97.20 µs (2 × M0) | sí | código: la vecindad recorre su propia lista (D1); depende de la máquina |
| 25 | 5. Planear la vecindad en una cripta de 1000 salas | precargar_vecinas cuando no hace falta nada | tiempo | **30.6 µs** | **27.2 µs** | **27.4 µs** | −3.20 µs (-10.5 %) | 61.20 µs (2 × M0) | sí | sin cambio de código (precargar_vecinas no cambia; llama a salas_vecinas); depende de la máquina |
| 26 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad    5 | cuenta | 82 aciertos / 938 fallos (8.0 %) 19 solicitudes de red | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | +45 solicitudes vs M0 (+236.8 %); +0 vs M1 | 128 solicitudes (2 × M1) | sí | carga (M0 → M1), que la llevó a más del doble de M0, por eso el límite es 2 × M1 (FR-383, corrección L1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 27 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   10 | cuenta | 316 aciertos / 704 fallos (31.0 %) 19 solicitudes de red | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | +45 solicitudes vs M0 (+236.8 %); +0 vs M1 | 128 solicitudes (2 × M1) | sí | carga (M0 → M1), que la llevó a más del doble de M0, por eso el límite es 2 × M1 (FR-383, corrección L1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 28 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   25 | cuenta | 487 aciertos / 533 fallos (47.7 %) 19 solicitudes de red | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | +45 solicitudes vs M0 (+236.8 %); +0 vs M1 | 128 solicitudes (2 × M1) | sí | carga (M0 → M1), que la llevó a más del doble de M0, por eso el límite es 2 × M1 (FR-383, corrección L1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 29 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad  100 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | +45 solicitudes vs M0 (+236.8 %); +0 vs M1 | 128 solicitudes (2 × M1) | sí | carga (M0 → M1), que la llevó a más del doble de M0, por eso el límite es 2 × M1 (FR-383, corrección L1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 30 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad 1000 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | +45 solicitudes vs M0 (+236.8 %); +0 vs M1 | 128 solicitudes (2 × M1) | sí | carga (M0 → M1), que la llevó a más del doble de M0, por eso el límite es 2 × M1 (FR-383, corrección L1); código: ninguna diferencia (M2 = M1 en la cuenta, D1 y D2 no cambian cuentas) |
| 31 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 25 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **0.7 µs** | **0.72 µs** | +0.02 µs (+2.9 %) vs M1 | 1.40 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (prototipo de medición); depende de la máquina |
| 32 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 100 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **2.18 µs** | **2.17 µs** | −0.01 µs (-0.5 %) vs M1 | 4.36 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (prototipo de medición); depende de la máquina |
| 33 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 1000 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **20.82 µs** | **20.98 µs** | +0.16 µs (+0.8 %) vs M1 | 41.64 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (prototipo de medición); depende de la máquina |
| 34 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 5000 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **96.78 µs** | **108.04 µs** | +11.26 µs (+11.6 %) vs M1 | 193.56 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (prototipo de medición); depende de la máquina |

#### Bloque `guardado`

| # | Sección | Medición | Tipo | Antes (M0) | Carga (M1) | Después (M2) | Diferencia | Límite (2×) | Cumple | Causa |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | §4.10 | verificación: cargar el binario devuelve exactamente el estado guardado | cuenta | OK | OK | OK | sin cambios | OK | sí | sin cambios |
| G2 | §4.10 | verificación: un archivo de otra versión del formato se rechaza | cuenta | OK | OK | OK | sin cambios | OK | sí | sin cambios |
| G3 | §4.10 | 10 salas  tamaño en disco  [binario] | cuenta | 12,581 bytes | 12,414 bytes | 12,414 bytes | -167 bytes (-1.3 %) | — (sin límite: FR-384 limita guardar, cargar y leer) | — | carga (M0 → M1): cazador con rango, costos de 1 a 9 y conocimiento; sin cambio de código (M2 = M1) |
| G4 | §4.10 | 10 salas  tamaño en disco  [JSON] | cuenta | 28,678 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) | -315 bytes (-1.1 %) | — (sin límite: FR-384 limita guardar, cargar y leer) | — | carga (M0 → M1): cazador con rango, costos de 1 a 9 y conocimiento; sin cambio de código (M2 = M1) |
| G5 | §4.10 | 10 salas  guardar la partida completa  [binario] | tiempo | **1.71 ms** | **1.70 ms** | **1.87 ms** | +160.00 µs (+9.4 %) | 3.42 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G6 | §4.10 | 10 salas  guardar la partida completa  [JSON] | tiempo | **833.0 µs** | **804.6 µs** | **825.5 µs** | −7.50 µs (-0.9 %) | 1.67 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G7 | §4.10 | 10 salas  cargar la partida completa   [binario → DTO] | tiempo | **2.10 ms** | **2.43 ms** | **2.02 ms** | −80.00 µs (-3.8 %) | 4.20 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G8 | §4.10 | 10 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **300.9 µs** | **286.7 µs** | **289.7 µs** | −11.20 µs (-3.7 %) | 601.80 µs (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G9 | §4.10 | 10 salas  cargar UNA sala (la 6)    [binario, acceso directo] | tiempo | **74.0 µs** | **73.6 µs** | **73.5 µs** | −0.50 µs (-0.7 %) | 148.00 µs (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G10 | §4.10 | 10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo] | tiempo | **278.2 µs** | **289.5 µs** | **276.9 µs** | −1.30 µs (-0.5 %) | 556.40 µs (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G11 | §4.10 | 100 salas  tamaño en disco  [binario] | cuenta | 47,943 bytes | 46,646 bytes | 46,646 bytes | -1,297 bytes (-2.7 %) | — (sin límite: FR-384 limita guardar, cargar y leer) | — | carga (M0 → M1): cazador con rango, costos de 1 a 9 y conocimiento; sin cambio de código (M2 = M1) |
| G12 | §4.10 | 100 salas  tamaño en disco  [JSON] | cuenta | 134,896 bytes  (2.81× el binario) | 133,318 bytes  (2.86× el binario) | 133,318 bytes  (2.86× el binario) | -1,578 bytes (-1.2 %) | — (sin límite: FR-384 limita guardar, cargar y leer) | — | carga (M0 → M1): cazador con rango, costos de 1 a 9 y conocimiento; sin cambio de código (M2 = M1) |
| G13 | §4.10 | 100 salas  guardar la partida completa  [binario] | tiempo | **4.97 ms** | **5.00 ms** | **4.56 ms** | −410.00 µs (-8.2 %) | 9.94 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G14 | §4.10 | 100 salas  guardar la partida completa  [JSON] | tiempo | **3.31 ms** | **3.31 ms** | **3.40 ms** | +90.00 µs (+2.7 %) | 6.62 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G15 | §4.10 | 100 salas  cargar la partida completa   [binario → DTO] | tiempo | **6.94 ms** | **7.02 ms** | **6.71 ms** | −230.00 µs (-3.3 %) | 13.88 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G16 | §4.10 | 100 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **1.16 ms** | **1.12 ms** | **1.12 ms** | −40.00 µs (-3.4 %) | 2.32 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G17 | §4.10 | 100 salas  cargar UNA sala (la 51)    [binario, acceso directo] | tiempo | **75.6 µs** | **75.7 µs** | **76.1 µs** | +0.50 µs (+0.7 %) | 151.20 µs (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G18 | §4.10 | 100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo] | tiempo | **1.15 ms** | **1.10 ms** | **1.13 ms** | −20.00 µs (-1.7 %) | 2.30 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G19 | §4.10 | 1000 salas  tamaño en disco  [binario] | cuenta | 412,440 bytes | 400,347 bytes | 400,347 bytes | -12,093 bytes (-2.9 %) | — (sin límite: FR-384 limita guardar, cargar y leer) | — | carga (M0 → M1): cazador con rango, costos de 1 a 9 y conocimiento; sin cambio de código (M2 = M1) |
| G20 | §4.10 | 1000 salas  tamaño en disco  [JSON] | cuenta | 1,213,097 bytes  (2.94× el binario) | 1,199,809 bytes  (3.00× el binario) | 1,199,809 bytes  (3.00× el binario) | -13,288 bytes (-1.1 %) | — (sin límite: FR-384 limita guardar, cargar y leer) | — | carga (M0 → M1): cazador con rango, costos de 1 a 9 y conocimiento; sin cambio de código (M2 = M1) |
| G21 | §4.10 | 1000 salas  guardar la partida completa  [binario] | tiempo | **36.23 ms** | **36.70 ms** | **35.98 ms** | −250.00 µs (-0.7 %) | 72.46 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G22 | §4.10 | 1000 salas  guardar la partida completa  [JSON] | tiempo | **28.83 ms** | **28.94 ms** | **29.75 ms** | +920.00 µs (+3.2 %) | 57.66 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G23 | §4.10 | 1000 salas  cargar la partida completa   [binario → DTO] | tiempo | **60.48 ms** | **59.03 ms** | **57.61 ms** | −2.87 ms (-4.7 %) | 120.96 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G24 | §4.10 | 1000 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **9.80 ms** | **9.56 ms** | **10.70 ms** | +900.00 µs (+9.2 %) | 19.60 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G25 | §4.10 | 1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] | tiempo | **83.6 µs** | **75.3 µs** | **81.7 µs** | −1.90 µs (-2.3 %) | 167.20 µs (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G26 | §4.10 | 1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] | tiempo | **9.46 ms** | **9.69 ms** | **10.13 ms** | +670.00 µs (+7.1 %) | 18.92 ms (2 × M0) | sí | carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G27 | §4.10 | (nota de la salida) El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. | nota | — | — | — | — | — | — | — |
| G28 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | sin antes en M0: fila nueva (FR-378) | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G29 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la del medio, la 6) | cuenta | sin antes en M0: fila nueva (FR-378) | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G30 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la última, la 10) | cuenta | sin antes en M0: fila nueva (FR-378) | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G31 | §4.10 | 10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **79.1 µs** | **77.2 µs** | −1.90 µs (-2.4 %) vs M1 | 158.20 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G32 | §4.10 | 10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **75.0 µs** | **72.3 µs** | −2.70 µs (-3.6 %) vs M1 | 150.00 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G33 | §4.10 | verificación: 10 salas: leer UNA sala lee menos bytes que el archivo | cuenta | sin antes en M0: fila nueva (FR-378) | OK | OK | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G34 | §4.10 | verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4 | cuenta | sin antes en M0: fila nueva (FR-378) | OK | OK | — (igual a M1) | OK | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G35 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | sin antes en M0: fila nueva (FR-378) | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G36 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) | cuenta | sin antes en M0: fila nueva (FR-378) | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G37 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la última, la 100) | cuenta | sin antes en M0: fila nueva (FR-378) | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G38 | §4.10 | 100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **85.5 µs** | **85.5 µs** | ±0.00 µs (+0.0 %) vs M1 | 171.00 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G39 | §4.10 | 100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **75.4 µs** | **76.7 µs** | +1.30 µs (+1.7 %) vs M1 | 150.80 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G40 | §4.10 | verificación: 100 salas: leer UNA sala lee menos bytes que el archivo | cuenta | sin antes en M0: fila nueva (FR-378) | OK | OK | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G41 | §4.10 | verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7 | cuenta | sin antes en M0: fila nueva (FR-378) | OK | OK | — (igual a M1) | OK | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G42 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | sin antes en M0: fila nueva (FR-378) | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G43 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) | cuenta | sin antes en M0: fila nueva (FR-378) | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G44 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la última, la 1000) | cuenta | sin antes en M0: fila nueva (FR-378) | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G45 | §4.10 | 1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **97.9 µs** | **95.4 µs** | −2.50 µs (-2.6 %) vs M1 | 195.80 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G46 | §4.10 | 1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **80.6 µs** | **74.0 µs** | −6.60 µs (-8.2 %) vs M1 | 161.20 µs (2 × M1) | sí | fila nueva (FR-378), su antes es M1; carga: la misma partida con cazador, costos y conocimiento; sin cambio de código; depende de la máquina |
| G47 | §4.10 | verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo | cuenta | sin antes en M0: fila nueva (FR-378) | OK | OK | — (igual a M1) | < tamaño del archivo; entradas ≤ ⌊log₂ n⌋ + 1 | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |
| G48 | §4.10 | verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 | cuenta | sin antes en M0: fila nueva (FR-378) | OK | OK | — (igual a M1) | OK | sí | fila nueva (FR-378), su antes es M1; sin cambio de código (M2 = M1) |

### Medición manual (T036)

Se hizo sin red, con `crear_servicio(offline=True)` sobre una copia de `datos_cripta/` y con `requests.get` y
`requests.post` bloqueados. Solo cripta-04 (50 salas) y cripta-05 (24 salas) tienen esqueleto, datos, contenido de
todas las salas y catálogo. cripta-06 (300 salas, la más grande) no tiene el contenido de todas sus salas. **Se usó
cripta-04** y no se descargó nada. La partida se guardó en formato 8 y se midió con la subclase contadora
`_AlmacenContador` de `bench/guardado.py`:

| Sala | Bytes leídos | Entradas de la tabla | Tiempo (mediana de 9) |
|---|---|---|---|
| la primera (1) | 222 de 25,004 | 5 | 100.6 µs |
| la del medio (26) | 191 de 25,004 | 5 | 61.0 µs |
| la última (50) | 322 de 25,004 | 6 | 71.5 µs |

Tamaño del archivo: 25,004 bytes. ⌊log₂ 50⌋ + 1 = 6. Carga completa: 3.83 ms (mediana de 5). **0 solicitudes.**
`datos_cripta/` quedó sin cambios (mismo md5 antes y después). Cumple FR-382 y SC-006.

### Hallazgos y límites

1. **El orden de las salidas es N, S, E, O (H1).** La spec suponía N, E, S, O, lo que contradecía FR-370 («exactamente
   las mismas salas que la versión vigente»). Se corrigieron FR-371, la convención de las criptas, los escenarios 4, 5,
   6 y 8 de la Historia 1 y el supuesto de la versión vigente. Los valores nuevos se verificaron ejecutando la
   planeación de la vecindad del código de `0b031ec`. D1 conserva ese orden.
2. **Los bytes leídos de una sala crecen de forma logarítmica (H2).** `AlmacenPartidaBinario.leer_sala` lee el pie,
   hace una búsqueda binaria en la tabla de entradas y lee la sala. En M2, la sala más cara lee 262 bytes con 10 salas
   (4 entradas), 334 con 100 (7 entradas) y 397 con 1 000 (10 entradas), siempre con ⌊log₂ n⌋ + 1 entradas como
   máximo y muy por debajo del tamaño del archivo (12,414, 46,646 y 400,347 bytes). La spec exige menos bytes que el
   archivo y un crecimiento no mayor que logarítmico (escenario 1 de la Historia 4, FR-382 y SC-006).
3. **Commit de referencia (H3).** El antes es el código del commit `0b031ec`. Su código de producción es idéntico al de
   `1f009a1`, que nombraba el supuesto original de la spec: entre los dos solo cambiaron documentos de la spec.
4. **Los cazadores del bloque `cache` se mueven de forma aproximada.** El contenido sintético agrega un cazador cada 10
   salas. Después de cada paso del jugador, el código de medición mueve cada cazador una salida hacia el jugador, por
   la menor cantidad de salidas y desempatando en el orden N, S, E, O. Si entra en una sala cuyo contenido no está
   traído, llama a `construir_sala`. Es una aproximación del motor de eventos, porque el bloque llama al servicio
   directamente y no al juego. Busca el peor caso para la red: cazadores activos desde el inicio.
5. **Presupuesto de solicitudes con cazadores (riesgo 1 del enunciado).** Con los cazadores activos desde el inicio
   (peor caso), la carga nueva sube las solicitudes:
   - el pasillo perezoso por defecto (fila 4) pasa de 9 a 46 solicitudes, 39 de ellas disparadas por un cazador;
   - la partida completa (filas 26 a 30) pasa de 19 a 64, 45 de ellas disparadas por un cazador;
   - las demás filas de la sección 1 pasan de 63 a 64 (45 por cazadores), de 61 a 62 (44) y de 33 a 56 (44).

   Con el juego real, la 009 midió 0.2 solicitudes disparadas por un enemigo de promedio, en 2 de 9 filas (`--bench llaves` A). La causa
   es la carga y no el código: D1 y D2 no cambian ninguna cuenta (M1 = M2 en todas las filas de cuenta, T032). Por eso
   FR-383 se corrigió (corrección L1 de la spec): las filas que la carga llevó a más del doble de M0 (fila 4 y filas 26
   a 30) se miden contra 2 × M1, y así el límite sigue midiendo el efecto del código. Con ese límite cumplen (46 contra
   92 y 64 contra 128). La fila más cercana a su límite es la 3 (perezosa de profundidad 2): 56 solicitudes contra 66
   (2 × M0), 1.70 × M0, también por la carga. Si los cazadores del juego real persiguieran desde el inicio como en este
   bloque, el presupuesto de solicitudes sería el primer recurso en agotarse.
6. **El tiempo de leer la primera sala crece con el logaritmo del número de salas (corrección L2).** De 10 a 1 000
   salas, la primera sala pasa de 77.2 µs (68.1 a 78.5 µs en las tres ejecuciones) a 95.4 µs (84.3 a 99.0 µs), cerca
   de 24 % más, y los rangos no se solapan. Eso coincide con las entradas de la tabla que se leen en la búsqueda
   binaria, que pasan de 3 a 9. La del medio (73.5 a 81.7 µs) y la última (72.3 a 74.0 µs) quedan dentro de la
   variación entre ejecuciones. Leer la primera sala es 26 veces más rápido que la carga completa con 10 salas
   (77.2 µs contra 2.02 ms), 78 veces con 100 (85.5 µs contra 6.71 ms) y 604 veces con 1 000 (95.4 µs contra
   57.61 ms). La corrección L2 alinea el escenario 3 de la Historia 4 con FR-382: el crecimiento no puede ser mayor que
   logarítmico. El código no se toca.
