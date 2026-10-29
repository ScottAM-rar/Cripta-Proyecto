# Mediciones: Terreno y cazador

Generadas con `python main.py --bench guardado,retroceso,ciclo,terreno` el 2026-10-27 (Python 3.14.7, macOS arm64, semilla 2026). Criptas sintéticas deterministas por semilla; sin red ni vista. Las cifras cambian algo de una máquina a otra; lo que importa son las proporciones y los límites.

## Resumen frente a los límites (principio VII)

| Requisito | Límite | Resultado | Veredicto |
|---|---|---|---|
| FR-121: ciclo con decenas de cazadores (bloque `ciclo`, 50 cazadores persiguiendo y el jugador caminando) | < 20 ms | máx. 0,53 ms | Cumple |
| FR-121: ciclo de decisiones de 50 cazadores (bloque `terreno` A, jugador moviéndose cada ciclo) | < 20 ms | máx. 0,09 ms | Cumple |
| FR-122: cazador de rango pequeño en cripta que crece de 400 a 40 000 salas | no proporcional a N | 17 µs, 52 µs y 28 µs (24, 63 y 35 salas exploradas) | Cumple |
| FR-123: puertas estables / cambiantes, un cazador / muchos, rango pequeño / grande | medible con `--bench` | secciones A, B y C | Cumple |
| Equivalencia con calcular desde cero (principio III) | 100 % | 12 000 decisiones, 0 diferencias | Cumple |

## Decisiones y la alternativa descartada

| Decisión | Alternativa descartada | Qué se midió | Conclusión |
|---|---|---|---|
| Campo de costos compartido y reutilizado | Calcular desde cero por cazador | 50 cazadores, jugador quieto: 17 µs frente a 3,03 ms. Jugador moviéndose cada ciclo: 77 µs frente a 2,95 ms. 200 cazadores: 65 µs frente a 13,1 ms | Se mantiene. Con un solo cazador y el jugador moviéndose, ambas valen lo mismo (≈ 50 µs): la ganancia crece con la cantidad de cazadores |
| Búsqueda acotada por el rango | Búsqueda sin cota | A 40 000 salas: 28 µs frente a 57 ms (35 frente a 39 968 salas exploradas) | Se mantiene. Sin cota el costo crece con la cripta |
| Invalidar por evento | Invalidar con cualquier cambio de puerta | Puertas que cambian lejos de la zona: 0 búsquedas frente a 18 por cada 40 ciclos (0,79 ms frente a 1,99 ms). Dentro de la zona: 10 frente a 18 búsquedas | Se mantiene. Con puertas estables no hay diferencia |
| Montículo propio nuevo | Reutilizar el del reloj | No se midió: se descartó por acoplamiento al evento (`research.md` §3) | Sin cambio |

**Plan original frente a lo construido**: coincide con `plan.md`. No hubo que cambiar ninguna decisión por una medición.

**Limitación honesta**: las secciones A y C ponen a los cazadores en un cuadrado de 9 x 9 salas alrededor del jugador para que la decisión haga trabajo real. Con cazadores repartidos por toda la cripta casi todos quedan fuera de rango y cuestan menos. Y en el bloque `ciclo` los cazadores alcanzan al jugador en pocos ciclos y pasan a atacar, así que el ciclo mezcla persecución y ataque.

## Mediciones de la Parte I repetidas con la carga nueva

Se repitió cada bloque antes y después de esta capacidad (el «antes» se midió con el código de la Parte I sin tocar). La relación entre las alternativas no cambia, así que **ninguna decisión de la Parte I deja de servir**.

| Medición | Antes | Después | Cambio |
|---|---|---|---|
| Guardado binario, 1 000 salas: tamaño | 395 092 B | 408 092 B | +3,3 % (un entero más por salida) |
| Guardado binario, 1 000 salas: guardar | 18,50 ms | 19,56 ms | +5,7 % |
| Guardado binario, 1 000 salas: cargar todo | 28,73 ms | 30,68 ms | +6,8 % |
| Guardado binario, 1 000 salas: cargar una sala | 37,8 µs | 41,4 µs | +9 % (ruido de medida) |
| JSON, 1 000 salas: conseguir una sala (leer todo) | 4,85 ms | 5,31 ms | +9 % |
| Binario frente a JSON, tamaño | 2,91× menor | 2,95× menor | sin cambio |
| Binario frente a JSON, una sala suelta | ≈ 128× más rápido | ≈ 128× más rápido | sin cambio |
| Retroceso: instantáneas, mundo de 3 000 entidades | 10,30 ms | 10,34 ms | sin cambio |
| Retroceso: diferencias, 200 acciones de 1 cambio | 193 µs | 204 µs | ruido |
| Ciclo de eventos, 300 esbirros | 1,87 ms | 1,87 ms | sin cambio |

## Salida completa del bloque `terreno`

```text
Terreno y cazador (A): un cazador frente a muchos, ciclo de decisiones — límite 20 ms (FR-121)
  verificación: 1 cazadores (1 dentro de su rango): ambas decisiones coinciden OK
     1 cazadores, jugador quieto              campo compartido (elegida) 0.5 µs  (0.4 µs – 0.9 µs)  mediana (mín – máx)
     1 cazadores, jugador quieto              desde cero por cazador (descartada) 53.1 µs  (51.5 µs – 53.8 µs)  mediana (mín – máx)
      ¿el peor de 25 ciclos con 1 cazadores (jugador quieto) < 20 ms? CUMPLE  (máx 0.9 µs)
     1 cazadores, jugador se mueve cada ciclo campo compartido (elegida) 51.9 µs  (42.1 µs – 58.9 µs)  mediana (mín – máx)
     1 cazadores, jugador se mueve cada ciclo desde cero por cazador (descartada) 53.5 µs  (42.3 µs – 61.1 µs)  mediana (mín – máx)
      ¿el peor de 25 ciclos con 1 cazadores (jugador se mueve cada ciclo) < 20 ms? CUMPLE  (máx 58.9 µs)
  verificación: 10 cazadores (8 dentro de su rango): ambas decisiones coinciden OK
    10 cazadores, jugador quieto              campo compartido (elegida) 3.6 µs  (3.5 µs – 3.9 µs)  mediana (mín – máx)
    10 cazadores, jugador quieto              desde cero por cazador (descartada) 547.6 µs  (532.7 µs – 607.6 µs)  mediana (mín – máx)
      ¿el peor de 25 ciclos con 10 cazadores (jugador quieto) < 20 ms? CUMPLE  (máx 3.9 µs)
    10 cazadores, jugador se mueve cada ciclo campo compartido (elegida) 56.5 µs  (45.9 µs – 72.9 µs)  mediana (mín – máx)
    10 cazadores, jugador se mueve cada ciclo desde cero por cazador (descartada) 536.8 µs  (429.7 µs – 590.7 µs)  mediana (mín – máx)
      ¿el peor de 25 ciclos con 10 cazadores (jugador se mueve cada ciclo) < 20 ms? CUMPLE  (máx 72.9 µs)
  verificación: 50 cazadores (38 dentro de su rango): ambas decisiones coinciden OK
    50 cazadores, jugador quieto              campo compartido (elegida) 16.8 µs  (16.3 µs – 17.7 µs)  mediana (mín – máx)
    50 cazadores, jugador quieto              desde cero por cazador (descartada) 3.03 ms  (2.97 ms – 3.10 ms)  mediana (mín – máx)
      ¿el peor de 25 ciclos con 50 cazadores (jugador quieto) < 20 ms? CUMPLE  (máx 17.7 µs)
    50 cazadores, jugador se mueve cada ciclo campo compartido (elegida) 77.0 µs  (62.7 µs – 85.2 µs)  mediana (mín – máx)
    50 cazadores, jugador se mueve cada ciclo desde cero por cazador (descartada) 2.95 ms  (2.33 ms – 3.28 ms)  mediana (mín – máx)
      ¿el peor de 25 ciclos con 50 cazadores (jugador se mueve cada ciclo) < 20 ms? CUMPLE  (máx 85.2 µs)
  verificación: 200 cazadores (151 dentro de su rango): ambas decisiones coinciden OK
   200 cazadores, jugador quieto              campo compartido (elegida) 64.5 µs  (63.1 µs – 91.9 µs)  mediana (mín – máx)
   200 cazadores, jugador quieto              desde cero por cazador (descartada) 13.07 ms  (12.93 ms – 13.33 ms)  mediana (mín – máx)
   200 cazadores, jugador se mueve cada ciclo campo compartido (elegida) 135.4 µs  (104.2 µs – 172.7 µs)  mediana (mín – máx)
   200 cazadores, jugador se mueve cada ciclo desde cero por cazador (descartada) 12.79 ms  (10.27 ms – 20.67 ms)  mediana (mín – máx)
  Un ciclo = cada cazador decide una vez. El campo compartido explora la zona una vez (y solo si algo cambió); la alternativa la repite por cazador. 
  Los cazadores están dentro de un cuadrado de 9 x 9 salas alrededor del jugador: parte está dentro de su rango y parte no. 

Terreno y cazador (B): rango pequeño frente a grande al crecer la cripta (FR-122)
     400 salas  rango pequeño 600 — acotada (elegida)                16.7 µs  (16.5 µs – 17.5 µs)  mediana (mín – máx)
     400 salas  sin cota (descartada)                                388.0 µs  (379.9 µs – 389.7 µs)  mediana (mín – máx)
     400 salas  salas exploradas: acotada / sin cota                 24 / 400
    4900 salas  rango pequeño 600 — acotada (elegida)                52.4 µs  (51.8 µs – 53.5 µs)  mediana (mín – máx)
    4900 salas  sin cota (descartada)                                5.72 ms  (5.68 ms – 5.75 ms)  mediana (mín – máx)
    4900 salas  salas exploradas: acotada / sin cota                 63 / 4,898
   40000 salas  rango pequeño 600 — acotada (elegida)                27.5 µs  (27.3 µs – 28.0 µs)  mediana (mín – máx)
   40000 salas  sin cota (descartada)                                56.54 ms  (56.01 ms – 57.43 ms)  mediana (mín – máx)
   40000 salas  salas exploradas: acotada / sin cota                 35 / 39,968
  Con rango pequeño el trabajo depende de la zona dentro del rango, no de cuántas salas tiene la cripta. 

Terreno y cazador (C): puertas estables frente a cambiantes (FR-123)
  puertas estables (sin cambios)     invalidar por evento (elegida)  661.4 µs  (645.4 µs – 714.1 µs)  mediana (mín – máx)
      búsquedas por cada 40 ciclos                                   0
  puertas estables (sin cambios)     invalidar con cualquier cambio (descartada) 647.3 µs  (633.0 µs – 710.1 µs)  mediana (mín – máx)
      búsquedas por cada 40 ciclos                                   0
  puertas cambian lejos de la zona   invalidar por evento (elegida)  788.8 µs  (755.0 µs – 832.2 µs)  mediana (mín – máx)
      búsquedas por cada 40 ciclos                                   0
  puertas cambian lejos de la zona   invalidar con cualquier cambio (descartada) 1.99 ms  (1.57 ms – 2.25 ms)  mediana (mín – máx)
      búsquedas por cada 40 ciclos                                   18
  puertas cambian dentro de la zona  invalidar por evento (elegida)  1.11 ms  (444.8 µs – 1.49 ms)  mediana (mín – máx)
      búsquedas por cada 40 ciclos                                   10
  puertas cambian dentro de la zona  invalidar con cualquier cambio (descartada) 1.44 ms  (760.2 µs – 2.00 ms)  mediana (mín – máx)
      búsquedas por cada 40 ciclos                                   18
  40 ciclos seguidos con 50 cazadores de rango pequeño en 2 500 salas; una puerta cambia por ciclo. Cambiar una puerta fuera de la zona calculada no obliga a recalcular. 

Terreno y cazador (D): la decisión reutilizada es la de calcular desde cero (principio III)
  verificación: 12,000 decisiones reutilizadas vs desde cero, 0 diferencias OK
  decisiones idénticas                                               100 %  debe ser 100 %
```

## Salida del bloque `ciclo` (con cazadores)

```text
Ciclo de eventos entre dos decisiones (§5.2): límite 20 ms
     10 esbirros activos (   10 eventos pendientes)  1 ciclo completo 61.8 µs  (59.8 µs – 102.9 µs)  mediana (mín – máx)
      ¿el peor de 30 ciclos < 20 ms?                                 CUMPLE  (máx 102.9 µs)
    100 esbirros activos (  100 eventos pendientes)  1 ciclo completo 590.0 µs  (569.5 µs – 2.00 ms)  mediana (mín – máx)
      ¿el peor de 30 ciclos < 20 ms?                                 CUMPLE  (máx 2.00 ms)
    300 esbirros activos (  300 eventos pendientes)  1 ciclo completo 1.90 ms  (1.78 ms – 4.02 ms)  mediana (mín – máx)
      ¿el peor de 30 ciclos < 20 ms?                                 CUMPLE  (máx 4.02 ms)
   1000 esbirros activos ( 1000 eventos pendientes)  1 ciclo completo 6.71 ms  (6.26 ms – 8.35 ms)  mediana (mín – máx)
      ¿el peor de 30 ciclos < 20 ms?                                 CUMPLE  (máx 8.35 ms)  prueba de estrés, no decide el veredicto
     10 cazadores persiguiendo (el jugador camina)  1 ciclo completo 93.7 µs  (90.0 µs – 141.1 µs)  mediana (mín – máx)
      ¿el peor de 30 ciclos < 20 ms?                                 CUMPLE  (máx 141.1 µs; 10 de 10 comparten sala con el jugador al final)
     50 cazadores persiguiendo (el jugador camina)  1 ciclo completo 449.0 µs  (435.4 µs – 533.5 µs)  mediana (mín – máx)
      ¿el peor de 30 ciclos < 20 ms?                                 CUMPLE  (máx 533.5 µs; 50 de 50 comparten sala con el jugador al final)
  reproducir un log de 300 acciones (incluye armar el juego)         22.66 ms  (22.39 ms – 22.67 ms)  mediana (mín – máx)
  Un ciclo = la acción ESPERAR del jugador + todos los eventos que ocurren hasta su siguiente decisión.
```

## Búsqueda con vista del mapa frente al campo sin vista (T071, 2026-10-29)

`BuscadorRutas` busca sobre una vista (`entrantes`, `salidas` y `transitable`) para que otras capacidades puedan usarlo con el mapa conocido por el jugador. La alternativa descartada es mantener la búsqueda dentro del campo de costos, directa sobre las listas del mapa (el código anterior a T068, reescrito como `CampoSinVista` en `bench/terreno.py`). Sección E de `python main.py --bench terreno`; mismas cargas que A y B, y las dos variantes dan las mismas decisiones (verificación OK).

| Carga | Sin vista (descartada) | Con vista (elegida) | Diferencia |
|---|---|---|---|
| 50 cazadores, jugador quieto | 33,0 µs | 40,2 µs | +22 % |
| 50 cazadores, jugador se mueve cada ciclo | 92,9 µs | 105,8 µs | +14 % |
| 200 cazadores, jugador quieto | 134,4 µs | 163,8 µs | +22 % |
| 200 cazadores, jugador se mueve cada ciclo | 193,1 µs | 225,7 µs | +17 % |
| Búsqueda fría de rango pequeño, 400 salas | 16,9 µs | 19,9 µs | +18 % |
| Búsqueda fría de rango pequeño, 4 900 salas | 53,5 µs | 60,8 µs | +14 % |
| Búsqueda fría de rango pequeño, 40 000 salas | 28,2 µs | 32,9 µs | +17 % |

**Conclusión**: la vista cuesta entre un 14 % y un 22 % más (una llamada por arista), pero el peor ciclo medido sigue siendo de unos 0,25 ms frente al límite de 20 ms (FR-121), y la búsqueda de rango pequeño sigue sin crecer con la cripta (FR-122). Se mantiene la vista: es lo que permite reutilizar la búsqueda con el mapa conocido (otras capacidades). Si una capacidad futura necesitara la búsqueda más rápida, el camino es especializar la vista real, no quitarla.

**Antes y después de T068**: las cifras de la primera tabla de este archivo (por ejemplo 17 µs con 50 cazadores y el jugador quieto) se midieron otro día y con el código anterior; no son comparables con esta tabla porque la máquina y la carga cambian. Para comparar se usan solo las dos columnas de arriba, medidas en la misma ejecución.

```text
Terreno y cazador (E): búsqueda con vista del mapa frente al campo sin vista (T071)
  verificación: 50 cazadores: ambas decisiones coinciden             OK
    50 cazadores, jugador quieto              con vista (elegida)    40.2 µs  (38.9 µs – 72.8 µs)
    50 cazadores, jugador quieto              sin vista (descartada) 33.0 µs  (32.5 µs – 33.8 µs)
    50 cazadores, jugador se mueve cada ciclo con vista (elegida)    105.8 µs  (83.9 µs – 116.4 µs)
    50 cazadores, jugador se mueve cada ciclo sin vista (descartada) 92.9 µs  (73.7 µs – 105.5 µs)
  verificación: 200 cazadores: ambas decisiones coinciden            OK
   200 cazadores, jugador quieto              con vista (elegida)    163.8 µs  (162.6 µs – 180.4 µs)
   200 cazadores, jugador quieto              sin vista (descartada) 134.4 µs  (131.2 µs – 157.5 µs)
   200 cazadores, jugador se mueve cada ciclo con vista (elegida)    225.7 µs  (167.9 µs – 246.4 µs)
   200 cazadores, jugador se mueve cada ciclo sin vista (descartada) 193.1 µs  (145.2 µs – 219.9 µs)
     400 salas, búsqueda fría de rango pequeño con vista (elegida)   19.9 µs  (19.7 µs – 21.3 µs)
     400 salas, búsqueda fría de rango pequeño sin vista (descartada) 16.9 µs  (16.6 µs – 17.7 µs)
    4900 salas, búsqueda fría de rango pequeño con vista (elegida)   60.8 µs  (58.7 µs – 61.6 µs)
    4900 salas, búsqueda fría de rango pequeño sin vista (descartada) 53.5 µs  (53.0 µs – 64.9 µs)
   40000 salas, búsqueda fría de rango pequeño con vista (elegida)   32.9 µs  (32.2 µs – 37.5 µs)
   40000 salas, búsqueda fría de rango pequeño sin vista (descartada) 28.2 µs  (27.7 µs – 29.3 µs)
```
