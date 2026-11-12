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
- Estado: las siete historias implementadas. **Pendiente abierto**: confirmar quién repite los bloques `retroceso` y `guardado` de la Parte I como responsable (la 002 solo los corrió de forma informativa; ver `mediciones.md`).

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
| Mediciones de la Parte I repetidas con la carga nueva (`ordenamiento`, `inventario`, `ciclo` informativo) | Sí: ninguna decisión de la Parte I dejó de servir | `mediciones.md`; `retroceso` y `guardado` los repiten sus responsables (por confirmar) |
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
