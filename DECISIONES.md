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
| Aviso FR-313: si no se obtienen las llaves, `llaves` queda en `None`, `avisoLlaves` guarda el mensaje con la cripta y la partida sigue; el controlador lo muestra como `AVISO:` al iniciar una partida nueva | Sí | `test_llaves_fallos` (partes c, e y g) y comprobación manual con `ControladorJuego` en `--offline` (T022): el aviso aparece y la partida responde a las acciones |
| Restaurar una partida no pide llaves: `llaves` y `avisoLlaves` vuelven a `None` y se piden bajo demanda con `obtenerLlaves()` (FR-325) | Sí | `test_llaves_partida_cargada`: cargar no hace solicitudes; con llaves guardadas, 0; sin ellas, 1 la primera vez y 0 la segunda; restaurar otra cripta no arrastra las llaves anteriores |
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
   operaciones sobre esa cripta fallan con el mensaje genérico.
2. **Un `ValueError` por cripta desconocida no se convierte en `DatoLocalFaltante`**: `ServicioCripta` lanza
   `ValueError(f"La cripta '{cripta_id}' no existe")` y `FuenteSoloLocal._leer` solo convierte
   `ErrorOffline` y `LlavesNoDisponibles`.
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
