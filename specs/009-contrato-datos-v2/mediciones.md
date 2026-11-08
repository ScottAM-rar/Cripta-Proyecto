# Mediciones: contrato de datos v2 y ubicación de llaves (capacidad 009)

- **Fecha**: 2026-11-07 (la salida dice 2026-11-07 19:00)
- **Python**: 3.12.10 · **Sistema**: Windows AMD64 · **Semilla**: 2026
- **Comando**: `python main.py --bench llaves` · **Código de salida**: 0

Los tiempos dependen de la máquina y de su carga en el momento de medir: se informa la **mediana** de 7 repeticiones
(con mínimo y máximo), tal como sale del comando. Las cuentas de solicitudes y las verificaciones no dependen del reloj:
en dos ejecuciones seguidas del bloque dieron lo mismo.

La precarga del juego (`precargar_vecinas` y `salas_vecinas` de `adaptadores/servicioCripta.py`) **no se modificó**. La
precarga por costo existe solo dentro del bench (`ServicioPrecargaPorCosto` en `bench/llaves.py`).

## Salida completa

```text
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-07 19:00 · semilla 2026
... midiendo llaves

Llaves (A): presupuesto con cazadores, precarga por saltos frente a por costo (FR-322, FR-323)
  verificación: precarga por costo: lote ≤ 10 + indispensables, las incluye, dentro de la cripta y 0 si ya están OK
  rejilla con costo_max=9, cazadores de rango 600 a 4+ salidas del jugador, guion de 60 movimientos por salidas abiertas; solo informa 
  verificación: lado 10, 1 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 10   1 cazadores  saltos [elegida]                            15.6 / 0.2  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 10   1 cazadores  costo [descartada]                          15.6 / 0.2  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 10, 4 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 10   4 cazadores  saltos [elegida]                            16.2 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 10   4 cazadores  costo [descartada]                          16.2 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 10, 16 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 10  16 cazadores  saltos [elegida]                            20.0 / 0.2  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 10  16 cazadores  costo [descartada]                          20.0 / 0.2  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 20, 1 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 20   1 cazadores  saltos [elegida]                            16.6 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 20   1 cazadores  costo [descartada]                          16.6 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 20, 4 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 20   4 cazadores  saltos [elegida]                            19.0 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 20   4 cazadores  costo [descartada]                          19.0 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 20, 16 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 20  16 cazadores  saltos [elegida]                            19.6 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 20  16 cazadores  costo [descartada]                          19.6 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 40, 1 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 40   1 cazadores  saltos [elegida]                            16.4 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 40   1 cazadores  costo [descartada]                          16.4 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 40, 4 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 40   4 cazadores  saltos [elegida]                            18.4 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 40   4 cazadores  costo [descartada]                          18.4 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  verificación: lado 40, 16 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  lado 40  16 cazadores  saltos [elegida]                            18.8 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  lado 40  16 cazadores  costo [descartada]                          18.8 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  comparación poco concluyente: solo 2 de 9 filas tienen solicitudes disparadas por un enemigo y 0 distinguen las reglas (los cazadores se activan solo cuando el jugador entra en su sala, y con costo_max=9 y rango 600 un cazador activo ve casi toda la rejilla) 
  verificación: variante costo_max=300 (como bench/terreno.py): lado 20, 4 cazadores: las dos reglas terminan en la misma sala con los mismos movimientos OK
  variante costo_max=300 (como bench/terreno.py): lado 20   4 cazadores  saltos [elegida] 19.0 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)
  variante costo_max=300 (como bench/terreno.py): lado 20   4 cazadores  costo [descartada] 19.0 / 0.0  solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)

Llaves (B): guardar y leer, clave en cripta_<id>.bin frente a archivo aparte (research.md §4)
  20 llaves; el archivo de la cripta ya tiene esqueleto y contenido de todas las salas 
  verificación: 50 salas: A y B guardan y leen la misma lista        OK
     50 salas  guardar  [A: clave en cripta_<id>.bin, elegida]       10.04 ms  (9.15 ms – 12.43 ms)  mediana (mín – máx)
     50 salas  guardar  [B: llaves_<id>.bin, descartada]             2.79 ms  (2.70 ms – 3.27 ms)  mediana (mín – máx)
     50 salas  leer     [A: clave en cripta_<id>.bin, elegida]       214.3 µs  (179.7 µs – 389.5 µs)  mediana (mín – máx)
     50 salas  leer     [B: llaves_<id>.bin, descartada]             363.4 µs  (297.2 µs – 492.1 µs)  mediana (mín – máx)
  verificación: 500 salas: A y B guardan y leen la misma lista       OK
    500 salas  guardar  [A: clave en cripta_<id>.bin, elegida]       9.75 ms  (9.08 ms – 10.80 ms)  mediana (mín – máx)
    500 salas  guardar  [B: llaves_<id>.bin, descartada]             2.97 ms  (2.72 ms – 3.32 ms)  mediana (mín – máx)
    500 salas  leer     [A: clave en cripta_<id>.bin, elegida]       459.9 µs  (446.3 µs – 517.0 µs)  mediana (mín – máx)
    500 salas  leer     [B: llaves_<id>.bin, descartada]             321.1 µs  (298.8 µs – 439.1 µs)  mediana (mín – máx)
  verificación: 5000 salas: A y B guardan y leen la misma lista      OK
   5000 salas  guardar  [A: clave en cripta_<id>.bin, elegida]       27.14 ms  (22.10 ms – 42.58 ms)  mediana (mín – máx)
   5000 salas  guardar  [B: llaves_<id>.bin, descartada]             3.43 ms  (2.92 ms – 4.16 ms)  mediana (mín – máx)
   5000 salas  leer     [A: clave en cripta_<id>.bin, elegida]       3.73 ms  (3.31 ms – 4.76 ms)  mediana (mín – máx)
   5000 salas  leer     [B: llaves_<id>.bin, descartada]             331.4 µs  (295.1 µs – 552.4 µs)  mediana (mín – máx)
  guardar con A y 5000 salas ≤ 50 ms (research.md §4)                CUMPLE  27.14 ms

Llaves (C): entradas repetidas, ordenar frente a todas las parejas (research.md §5)
  verificación: k = 10: las dos detectan la repetida y no inventan otra OK
  k =   10  validar_llaves real  [ordenar y comparar vecinas, elegida] 13.1 µs  (12.7 µs – 14.4 µs)  mediana (mín – máx)
  k =   10  solo repetidas       [todas las parejas, descartada]     9.6 µs  (9.6 µs – 10.0 µs)  mediana (mín – máx)
  verificación: k = 100: las dos detectan la repetida y no inventan otra OK
  k =  100  validar_llaves real  [ordenar y comparar vecinas, elegida] 289.6 µs  (285.2 µs – 373.5 µs)  mediana (mín – máx)
  k =  100  solo repetidas       [todas las parejas, descartada]     778.0 µs  (746.3 µs – 983.6 µs)  mediana (mín – máx)
  verificación: k = 1000: las dos detectan la repetida y no inventan otra OK
  k = 1000  validar_llaves real  [ordenar y comparar vecinas, elegida] 3.91 ms  (3.83 ms – 4.16 ms)  mediana (mín – máx)
  k = 1000  solo repetidas       [todas las parejas, descartada]     78.55 ms  (76.05 ms – 80.02 ms)  mediana (mín – máx)
  la elegida incluye además las demás reglas de FR-311; los tiempos solo informan 

Llaves (D): una solicitud por cripta: primera partida, segunda y --offline (SC-001, SC-002)
  primera partida (carpeta vacía)                                    1  consultas («llaves», …)
  segunda partida, misma versión                                     0  consultas («llaves», …)
  --offline                                                          0  solicitudes de red
  verificación: las tres partidas reciben la misma lista de llaves   OK
  1 / 0 / 0                                                          CUMPLE  1 / 0 / 0

Llaves (SC-001, SC-002): CUMPLE.
```

## Elegida frente a descartada

| Sección | Elegida | Descartada | Qué se midió | Conclusión |
|---|---|---|---|---|
| A. Presupuesto con cazadores | Precarga por saltos (`ServicioCripta.precargar_vecinas`) | Precarga por costo de ruta (`ServicioPrecargaPorCosto`) | Solicitudes totales y disparadas por un enemigo en una partida real de 60 movimientos, lados 10, 20 y 40, con 1, 4 y 16 cazadores de rango 600, promedio de 5 semillas, más la variante `costo_max=300` (lado 20, 4 cazadores) | Totales idénticos en las 9 filas y en la variante (por ejemplo, lado 20 con 4 cazadores: 19.0 / 0.0 en las dos reglas). Solicitudes disparadas por un enemigo: 0.2 en 2 filas y 0.0 en las demás. No distingue las reglas |
| B. Guardar llaves | Clave `llaves` en `cripta_<id>.bin` (opción A) | `llaves_<id>.bin` con su propia versión (opción B) | Guardar y leer 20 llaves en un archivo con 50, 500 y 5 000 salas con contenido | A con 5 000 salas: guardar 27.14 ms, leer 3.73 ms. B con 5 000 salas: guardar 3.43 ms, leer 331.4 µs. B es más rápida al guardar y al leer; A queda por debajo del límite de 50 ms |
| C. Entradas repetidas | Ordenar las posiciones (`ordenar_adaptativo`) y comparar vecinas | Comparar todas las parejas | `validar_llaves` real frente a solo la detección de repetidas por parejas, k = 10, 100 y 1 000, con verificación previa de que las dos detectan lo mismo | k = 10: 13.1 µs frente a 9.6 µs (gana la descartada). k = 100: 289.6 µs frente a 778.0 µs. k = 1 000: 3.91 ms frente a 78.55 ms. Las parejas solo ganan con k pequeña |
| D. Una solicitud por cripta | — | — | Consultas `("llaves", …)` en la primera partida, en la segunda con la misma versión y en `--offline` | **1 / 0 / 0**: CUMPLE (SC-001, SC-002) |

## Recomendación sobre la precarga

**Mantener la precarga por saltos y no abrir una especificación aparte.**

En la sección A, las dos reglas dieron los mismos totales de solicitudes en todas las filas, también en la variante
`costo_max=300`. Casi no hubo solicitudes disparadas por un enemigo (0.2 de promedio en 2 de 9 filas, 0.0 en el resto),
porque los cazadores solo se activan cuando el jugador entra en su sala. Además, los lotes que arman las dos reglas
difieren en a lo sumo 2 salas: con alcance de 3 saltos desde la esquina hay exactamente 10 candidatas, el tamaño del
lote, y con alcance de 2 saltos hay 12. Este último dato no sale de la tabla del bench sino de la revisión de los lotes
hecha al implementar la sección A (grupo I2). Por tanto **no hay evidencia de que el orden por costo ahorre
solicitudes**.

Es un **límite del experimento**, no una prueba de que el costo nunca sirva: el guion es una caminata por salidas
abiertas que no persigue a los cazadores, así que casi nunca hay un cazador activo cruzando salas sin cargar. Si una
capacidad futura necesita medir ese caso, tendrá que diseñar un guion que lo provoque.

## Revisión de las decisiones (T037)

Criterios de `research.md` §4 (guardado) y §5 (repetidas), comparados con los números medidos arriba:

- **B, guardado (§4)**: la regla es pasar a la opción B solo si guardar con la opción A y 5 000 salas supera los
  50 ms. Medido: **27.14 ms** (mediana; mínimo 22.10 ms, máximo 42.58 ms), por debajo del límite. Sin esconderlo: la
  opción B es más rápida al guardar (3.43 ms) y al leer (331.4 µs frente a 3.73 ms con 5 000 salas), porque su archivo
  es pequeño y A reescribe el archivo completo de la cripta. Pero la regla de research.md solo cambia de decisión si A
  supera los 50 ms, y no los supera. El guardado ocurre una vez por cripta y versión.
- **C, repetidas (§5)**: «todas las parejas» se descartaría si con k = 1 000 es más lenta. Medido con k = 1 000:
  **78.55 ms** con todas las parejas frente a **3.91 ms** con la validación elegida completa. Las parejas no ganan con
  claridad para k ≤ 1 000: solo son más rápidas con k = 10 (9.6 µs frente a 13.1 µs), y research.md ya admite que con
  k chica cualquiera sirve.

**Las decisiones se mantienen**: opción A para el guardado y ordenar con comparación de vecinas para las repetidas.

## Bloque cache: antes y después (T050)

- **Antes**: `bench-cache-antes.csv`, medido en T049 con el código anterior a esta capacidad.
- **Después**: `bench-cache-despues.csv`, con
  `python main.py --bench cache --bench-csv specs/009-contrato-datos-v2/bench-cache-despues.csv` (código de salida 0).

Las dos tienen 30 filas, en el mismo orden y con las mismas mediciones. Las filas de solicitudes, aciertos y fallos son
cuentas y se comparan exactamente; las de tiempo dependen de la máquina y de su carga, y se muestran solo como
referencia.

| # | Sección | Medición | Antes | Después | Diferencia | Causa |
|---|---|---|---|---|---|---|
| 1 | 1 | sala por sala (sin precarga) | 63 solicitudes | 63 solicitudes | +0 | cuenta exacta: igual |
| 2 | 1 | actual + vecinas en cada paso (prof. 2) | 61 solicitudes | 61 solicitudes | +0 | cuenta exacta: igual |
| 3 | 1 | perezosa, prof. 2 | 33 solicitudes | 33 solicitudes | +0 | cuenta exacta: igual |
| 4 | 1 | perezosa, por defecto (lote de 10) | 9 solicitudes | 9 solicitudes | +0 | cuenta exacta: igual |
| 5 | 2 | deque lineal, 25 fichas, acierto | 1.12 µs | 1.33 µs | +0.21 (+19 %) | tiempo: depende de la máquina |
| 6 | 2 | deque lineal, 25 fichas, fallo | 0.6 µs | 0.69 µs | +0.09 (+15 %) | tiempo: depende de la máquina |
| 7 | 2 | tabla hash propia, 25 fichas, acierto (descartada) | 0.19 µs | 0.23 µs | +0.04 (+21 %) | tiempo: depende de la máquina |
| 8 | 2 | deque lineal, 100 fichas, acierto | 3.42 µs | 3.54 µs | +0.12 (+4 %) | tiempo: depende de la máquina |
| 9 | 2 | deque lineal, 100 fichas, fallo | 1.92 µs | 2.2 µs | +0.28 (+15 %) | tiempo: depende de la máquina |
| 10 | 2 | tabla hash propia, 100 fichas, acierto (descartada) | 0.21 µs | 0.23 µs | +0.02 (+10 %) | tiempo: depende de la máquina |
| 11 | 2 | deque lineal, 1000 fichas, acierto | 30.95 µs | 37.1 µs | +6.15 (+20 %) | tiempo: depende de la máquina |
| 12 | 2 | deque lineal, 1000 fichas, fallo | 18.31 µs | 22.34 µs | +4.03 (+22 %) | tiempo: depende de la máquina |
| 13 | 2 | tabla hash propia, 1000 fichas, acierto (descartada) | 0.31 µs | 0.28 µs | -0.03 (-10 %) | tiempo: depende de la máquina |
| 14 | 2 | deque lineal, 5000 fichas, acierto | 176.7 µs | 178.53 µs | +1.83 (+1 %) | tiempo: depende de la máquina |
| 15 | 2 | deque lineal, 5000 fichas, fallo | 106.76 µs | 107.56 µs | +0.8 (+1 %) | tiempo: depende de la máquina |
| 16 | 2 | tabla hash propia, 5000 fichas, acierto (descartada) | 0.35 µs | 0.33 µs | -0.02 (-6 %) | tiempo: depende de la máquina |
| 17 | 3 | catálogo con 25 fichas | 0.109 ms por lectura | 0.075 ms por lectura | -0.034 (-31 %) | tiempo: depende de la máquina |
| 18 | 3 | catálogo con 200 fichas | 0.202 ms por lectura | 0.172 ms por lectura | -0.03 (-15 %) | tiempo: depende de la máquina |
| 19 | 3 | catálogo con 1000 fichas | 0.511 ms por lectura | 0.451 ms por lectura | -0.06 (-12 %) | tiempo: depende de la máquina |
| 20 | 4 | catálogo con 25 fichas | 3.547 ms | 2.413 ms | -1.13 (-32 %) | tiempo: depende de la máquina |
| 21 | 4 | catálogo con 200 fichas | 11.968 ms | 9.722 ms | -2.25 (-19 %) | tiempo: depende de la máquina |
| 22 | 4 | catálogo con 1000 fichas | 12.707 ms | 9.475 ms | -3.23 (-25 %) | tiempo: depende de la máquina |
| 23 | 5 | salas_vecinas, 1 paso | 38.4 µs | 37.3 µs | -1.1 (-3 %) | tiempo: depende de la máquina |
| 24 | 5 | salas_vecinas, 2 pasos | 98.1 µs | 89.0 µs | -9.1 (-9 %) | tiempo: depende de la máquina |
| 25 | 5 | precargar_vecinas cuando no hace falta nada | 59.4 µs | 57.8 µs | -1.6 (-3 %) | tiempo: depende de la máquina |
| 26 | 6 | capacidad    5 | 82 aciertos / 938 fallos (8.0 %), 19 solicitudes de red | 82 aciertos / 938 fallos (8.0 %), 19 solicitudes de red | 0 | cuenta exacta: igual |
| 27 | 6 | capacidad   10 | 316 aciertos / 704 fallos (31.0 %), 19 solicitudes de red | 316 aciertos / 704 fallos (31.0 %), 19 solicitudes de red | 0 | cuenta exacta: igual |
| 28 | 6 | capacidad   25 | 487 aciertos / 533 fallos (47.7 %), 19 solicitudes de red | 487 aciertos / 533 fallos (47.7 %), 19 solicitudes de red | 0 | cuenta exacta: igual |
| 29 | 6 | capacidad  100 | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 0 | cuenta exacta: igual |
| 30 | 6 | capacidad 1000 | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %), 19 solicitudes de red | 0 | cuenta exacta: igual |

**Cuentas**: las 9 filas de cuentas (secciones 1 y 6) son **idénticas** antes y después. La consulta de llaves no sumó
ninguna solicitud en este bloque. T050 esperaba «+1 solicitud por cripta y versión», pero eso no aplica aquí: el bloque
`cache` (`adaptadores/bench_red_mejorado.py`) usa un `ClienteSintetico` propio, sin `obtener_llaves`, y llama
directamente a `ServicioCripta` (`listar_criptas`, `crear_jugador`, `precargar`, `precargar_vecinas`,
`construir_sala`), sin pasar por `EstadoJuegoLogica.iniciarJuego`, que es lo único que pide las llaves. Por eso
`ubicacion_llaves` nunca se llama y las cuentas no cambian. El +1 por cripta y versión sí se mide en la sección D de
`--bench llaves` (1 / 0 / 0).

**Tiempos**: las diferencias van de −32 % a +22 % según la fila, en las dos direcciones, en un código que esta capacidad
no tocó (caché, catálogo, `salas_vecinas`, `precargar_vecinas`). Se atribuyen a la carga de la máquina en cada medición.

Ninguna decisión de la Parte I deja de servir con estos números: las estrategias de precarga mantienen exactamente las
mismas solicitudes (63 / 61 / 33 / 9) y la caché los mismos aciertos y fallos.
