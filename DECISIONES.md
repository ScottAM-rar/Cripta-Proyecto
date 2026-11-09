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
