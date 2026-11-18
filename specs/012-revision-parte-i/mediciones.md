# Mediciones: Revisión de la Parte I con la carga nueva (012)

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Tareas**: [tasks.md](tasks.md) · **Formato**: [contracts/filas-medicion.md](contracts/filas-medicion.md)

Cada paso (M0, M1 y M2) son tres ejecuciones de cada bloque. En las filas de **tiempo** el valor del paso es la **mediana de las tres** (FR-383, FR-384); las filas de **cuenta** tienen que salir iguales en las tres (FR-379). Los tiempos dependen de la máquina: Windows AMD64, Python 3.12.10.

## Catálogo de filas (ajuste con M0, T004)

- **Bloque `cache`**: M0 da 30 filas y coincide con el catálogo (filas 1 a 30, en el orden de salida). Las filas 31 a 34 son la lista enlazada propia (descartada) de T019: aparecen desde M1, al final del bloque, con el rótulo de la sección 2.
- **Bloque `guardado`**: el catálogo no las numeraba. Gana M0: 27 líneas, numeradas **G1 a G27** en el orden de salida. G1 y G2 son las verificaciones; G3 a G26, ocho filas por tamaño (10, 100 y 1 000 salas); **G27 no es una medición** sino la nota de texto con que termina el bloque, y no se compara. Las filas nuevas de T021 aparecen desde M1 como **G28 a G48**, siete por tamaño: bytes leídos de la primera, la del medio y la última sala (cuenta), tiempo de la primera y la última (tiempo) y dos verificaciones (cuenta).
- **Tipos** (research D3): cuenta = `cache` 1 a 4 y 26 a 30, `guardado` G1 a G4, G11, G12, G19 y G20, y las nuevas de bytes leídos y verificaciones (G28 a G30, G33 a G37, G40 a G44, G47 y G48); tiempo = `cache` 5 a 25 y 31 a 34, y el resto de `guardado` (G31, G32, G38, G39, G45 y G46 entre las nuevas).

## M0 · el antes (código de `0b031ec`)

- **Commit**: `fca5b45` (`git rev-parse --short HEAD`), con árbol con cambios. El código es el de `0b031ec`:
  - `git diff --stat 0b031ec -- adaptadores Logica DTO Controlador Servicio model main.py bench tests_labs` no muestra nada (T001);
  - `git diff --stat 0b031ec -- '*.py'` tampoco (incluye los `test_*.py` y `Pruebas.py` de la raíz).
  - Los cambios del árbol no son código que ejecuten los bloques: `specs/003-verificacion-resolubilidad/mediciones.md` y `quickstart.md` (modificados), y `bench_final.txt` y `descargar_cripta.py` (sin versionar; nadie importa `descargar_cripta`).
- **Ejecución**: en primer plano, una tras otra, sin otros procesos del proyecto. La salida de consola se redirigió a un archivo para copiarla aquí.
- **Incidencia con `guardado`**: el primer intento de las tres ejecuciones terminó con código 1 y sin CSV, por `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'` al imprimir «→». Al redirigir la salida, Python usa cp1252 en Windows. No es un fallo del bloque. Se reintentó una vez con `PYTHONIOENCODING=utf-8`, que solo cambia la codificación de la salida, y las tres ejecuciones terminaron con código 0. Las de `cache` no imprimen «→» y terminaron con código 0 sin esa variable; su salida, capturada en cp1252, se copia aquí convertida a UTF-8.

### M0-1 · `cache`

- Fecha y hora: 2026-11-18 06:29:27 -0600
- Comando: `python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M0-1.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:29 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       63  solicitudes (~25.2 s de espera)
  actual + vecinas en cada paso (prof. 2)                            61  solicitudes (~24.4 s de espera)
  perezosa, prof. 2                                                  33  solicitudes (~13.2 s de espera)
  perezosa, por defecto (lote de 10)                                 9  solicitudes (~3.6 s de espera)

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  deque lineal, 25 fichas, acierto                                   1.1  µs
  deque lineal, 25 fichas, fallo                                     0.64  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.2  µs
  deque lineal, 100 fichas, acierto                                  3.07  µs
  deque lineal, 100 fichas, fallo                                    2.13  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.23  µs
  deque lineal, 1000 fichas, acierto                                 31.65  µs
  deque lineal, 1000 fichas, fallo                                   19.53  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.23  µs
  deque lineal, 5000 fichas, acierto                                 169.92  µs
  deque lineal, 5000 fichas, fallo                                   97.55  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.33  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.111  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.167  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.42  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             2.363  ms
  catálogo con 200 fichas                                            9.482  ms
  catálogo con 1000 fichas                                           10.829  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              22.6  µs
  salas_vecinas, 2 pasos                                             48.6  µs
  precargar_vecinas cuando no hace falta nada                        30.9  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     82 aciertos / 938 fallos (8.0 %)  19 solicitudes de red
  capacidad   10                                                     316 aciertos / 704 fallos (31.0 %)  19 solicitudes de red
  capacidad   25                                                     487 aciertos / 533 fallos (47.7 %)  19 solicitudes de red
  capacidad  100                                                     950 aciertos / 70 fallos (93.1 %)  19 solicitudes de red
  capacidad 1000                                                     950 aciertos / 70 fallos (93.1 %)  19 solicitudes de red

Resultados guardados en specs/012-revision-parte-i/bench-cache-M0-1.csv
```

### M0-2 · `cache`

- Fecha y hora: 2026-11-18 06:29:39 -0600
- Comando: `python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M0-2.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:29 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       63  solicitudes (~25.2 s de espera)
  actual + vecinas en cada paso (prof. 2)                            61  solicitudes (~24.4 s de espera)
  perezosa, prof. 2                                                  33  solicitudes (~13.2 s de espera)
  perezosa, por defecto (lote de 10)                                 9  solicitudes (~3.6 s de espera)

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  deque lineal, 25 fichas, acierto                                   0.99  µs
  deque lineal, 25 fichas, fallo                                     0.54  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.2  µs
  deque lineal, 100 fichas, acierto                                  3.05  µs
  deque lineal, 100 fichas, fallo                                    1.85  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.2  µs
  deque lineal, 1000 fichas, acierto                                 33.93  µs
  deque lineal, 1000 fichas, fallo                                   18.64  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.44  µs
  deque lineal, 5000 fichas, acierto                                 179.5  µs
  deque lineal, 5000 fichas, fallo                                   97.19  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.36  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.09  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.154  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.441  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             2.216  ms
  catálogo con 200 fichas                                            11.131  ms
  catálogo con 1000 fichas                                           10.84  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              18.4  µs
  salas_vecinas, 2 pasos                                             48.6  µs
  precargar_vecinas cuando no hace falta nada                        27.7  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     82 aciertos / 938 fallos (8.0 %)  19 solicitudes de red
  capacidad   10                                                     316 aciertos / 704 fallos (31.0 %)  19 solicitudes de red
  capacidad   25                                                     487 aciertos / 533 fallos (47.7 %)  19 solicitudes de red
  capacidad  100                                                     950 aciertos / 70 fallos (93.1 %)  19 solicitudes de red
  capacidad 1000                                                     950 aciertos / 70 fallos (93.1 %)  19 solicitudes de red

Resultados guardados en specs/012-revision-parte-i/bench-cache-M0-2.csv
```

### M0-3 · `cache`

- Fecha y hora: 2026-11-18 06:29:43 -0600
- Comando: `python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M0-3.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:29 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       63  solicitudes (~25.2 s de espera)
  actual + vecinas en cada paso (prof. 2)                            61  solicitudes (~24.4 s de espera)
  perezosa, prof. 2                                                  33  solicitudes (~13.2 s de espera)
  perezosa, por defecto (lote de 10)                                 9  solicitudes (~3.6 s de espera)

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  deque lineal, 25 fichas, acierto                                   1.92  µs
  deque lineal, 25 fichas, fallo                                     1.22  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.45  µs
  deque lineal, 100 fichas, acierto                                  7.29  µs
  deque lineal, 100 fichas, fallo                                    4.2  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.48  µs
  deque lineal, 1000 fichas, acierto                                 37.62  µs
  deque lineal, 1000 fichas, fallo                                   21.42  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.27  µs
  deque lineal, 5000 fichas, acierto                                 172.4  µs
  deque lineal, 5000 fichas, fallo                                   97.48  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.29  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.092  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.168  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.419  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             1.995  ms
  catálogo con 200 fichas                                            9.649  ms
  catálogo con 1000 fichas                                           10.116  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              20.2  µs
  salas_vecinas, 2 pasos                                             50.3  µs
  precargar_vecinas cuando no hace falta nada                        30.6  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     82 aciertos / 938 fallos (8.0 %)  19 solicitudes de red
  capacidad   10                                                     316 aciertos / 704 fallos (31.0 %)  19 solicitudes de red
  capacidad   25                                                     487 aciertos / 533 fallos (47.7 %)  19 solicitudes de red
  capacidad  100                                                     950 aciertos / 70 fallos (93.1 %)  19 solicitudes de red
  capacidad 1000                                                     950 aciertos / 70 fallos (93.1 %)  19 solicitudes de red

Resultados guardados en specs/012-revision-parte-i/bench-cache-M0-3.csv
```

### M0-1 · `guardado`

- Fecha y hora: 2026-11-18 06:30:08 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M0-1.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:30 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,581  bytes
     10 salas  tamaño en disco  [JSON]                               28,678  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.71 ms  (1.66 ms – 1.75 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   924.8 µs  (794.8 µs – 1.02 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          2.10 ms  (2.09 ms – 2.17 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 300.9 µs  (279.9 µs – 369.2 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   74.0 µs  (72.0 µs – 92.4 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   282.2 µs  (272.3 µs – 299.9 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            47,943  bytes
    100 salas  tamaño en disco  [JSON]                               134,896  bytes  (2.81× el binario)
    100 salas  guardar la partida completa  [binario]                5.27 ms  (4.78 ms – 6.82 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   3.40 ms  (3.36 ms – 3.43 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          7.23 ms  (6.97 ms – 8.92 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.14 ms  (1.12 ms – 1.28 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  75.6 µs  (73.0 µs – 95.5 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.11 ms  (1.09 ms – 1.20 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            412,440  bytes
   1000 salas  tamaño en disco  [JSON]                               1,213,097  bytes  (2.94× el binario)
   1000 salas  guardar la partida completa  [binario]                34.94 ms  (34.26 ms – 37.82 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   28.83 ms  (25.95 ms – 30.58 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          54.74 ms  (52.90 ms – 60.81 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 9.80 ms  (8.71 ms – 23.43 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 240.4 µs  (213.5 µs – 296.8 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 9.46 ms  (8.98 ms – 12.37 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M0-1.csv
```

### M0-2 · `guardado`

- Fecha y hora: 2026-11-18 06:30:09 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M0-2.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:30 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,581  bytes
     10 salas  tamaño en disco  [JSON]                               28,678  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.67 ms  (1.63 ms – 1.68 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   789.9 µs  (763.9 µs – 849.2 µs)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          2.17 ms  (2.13 ms – 2.30 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 497.7 µs  (308.3 µs – 749.0 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   76.1 µs  (72.5 µs – 95.6 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   278.2 µs  (266.5 µs – 299.1 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            47,943  bytes
    100 salas  tamaño en disco  [JSON]                               134,896  bytes  (2.81× el binario)
    100 salas  guardar la partida completa  [binario]                4.82 ms  (4.78 ms – 5.15 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   3.31 ms  (3.21 ms – 3.49 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          6.89 ms  (6.82 ms – 7.18 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.21 ms  (1.20 ms – 1.45 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  75.4 µs  (73.7 µs – 93.1 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.22 ms  (1.20 ms – 1.35 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            412,440  bytes
   1000 salas  tamaño en disco  [JSON]                               1,213,097  bytes  (2.94× el binario)
   1000 salas  guardar la partida completa  [binario]                36.23 ms  (33.47 ms – 36.92 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   27.59 ms  (25.53 ms – 29.97 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          60.94 ms  (57.18 ms – 67.66 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 10.19 ms  (9.61 ms – 10.57 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 83.6 µs  (79.5 µs – 224.4 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 9.96 ms  (9.76 ms – 12.29 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M0-2.csv
```

### M0-3 · `guardado`

- Fecha y hora: 2026-11-18 06:30:11 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M0-3.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:30 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,581  bytes
     10 salas  tamaño en disco  [JSON]                               28,678  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.71 ms  (1.65 ms – 1.83 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   833.0 µs  (781.3 µs – 1.05 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          1.89 ms  (1.86 ms – 2.18 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 279.6 µs  (257.0 µs – 345.9 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   66.4 µs  (63.5 µs – 78.2 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   257.5 µs  (249.5 µs – 264.9 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            47,943  bytes
    100 salas  tamaño en disco  [JSON]                               134,896  bytes  (2.81× el binario)
    100 salas  guardar la partida completa  [binario]                4.97 ms  (4.89 ms – 6.78 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   3.10 ms  (2.91 ms – 5.45 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          6.94 ms  (6.22 ms – 6.98 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.16 ms  (1.14 ms – 1.37 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  75.6 µs  (73.8 µs – 98.1 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.15 ms  (1.07 ms – 1.95 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            412,440  bytes
   1000 salas  tamaño en disco  [JSON]                               1,213,097  bytes  (2.94× el binario)
   1000 salas  guardar la partida completa  [binario]                36.84 ms  (36.44 ms – 39.63 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   29.57 ms  (29.01 ms – 30.82 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          60.48 ms  (57.95 ms – 64.42 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 9.26 ms  (9.10 ms – 9.47 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 83.4 µs  (79.9 µs – 115.4 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 8.84 ms  (8.46 ms – 10.99 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M0-3.csv
```

## M1 · la carga nueva con el código vigente

- **Commit**: `5ed7d50` (`git rev-parse --short HEAD`), con árbol con cambios: solo el código de medición
  (`adaptadores/bench_red_mejorado.py` y `bench/guardado.py`, T015 a T021). El código de producción es el de `0b031ec`:
  `git diff --stat 0b031ec -- adaptadores/servicioCripta.py adaptadores/cache.py` no muestra nada, y tampoco
  `git diff --stat 0b031ec -- adaptadores Logica DTO Controlador Servicio model main.py` fuera de `bench_red_mejorado.py`.
- **Ejecución**: en primer plano, una tras otra, con `PYTHONIOENCODING=utf-8` desde el principio. Las seis
  ejecuciones terminaron con código 0 al primer intento.
- **Carga** (research D3, FR-378): costos de salida de 1 a 9 (secciones 1, 5 y 6), la consulta de llaves contada en
  el presupuesto (+1, secciones 1 y 6), un cazador cada 10 salas activo desde el inicio que avanza una salida hacia
  el jugador en cada paso (secciones 1 y 6), la ficha leída de la sección 3 es de cazador, y la partida de
  `guardado` lleva un cazador con rango por sala, costo en cada salida y el conocimiento de la mitad de las salas.
- **Filas nuevas**: `cache` 31 a 34 (lista enlazada propia, descartada) y `guardado` G28 a G48 (bytes leídos y
  entradas de la tabla al cargar UNA sala, tiempo de la primera y la última, y sus verificaciones). Van al final de
  cada bloque, así que ninguna fila existente cambia de número, nombre ni escenario.

### M1-1 · `cache`

- Fecha y hora: 2026-11-18 06:51:07 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M1-1.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:51 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       64  solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador
  actual + vecinas en cada paso (prof. 2)                            62  solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, prof. 2                                                  56  solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, por defecto (lote de 10)                                 46  solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  deque lineal, 25 fichas, acierto                                   0.99  µs
  deque lineal, 25 fichas, fallo                                     0.51  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.2  µs
  deque lineal, 100 fichas, acierto                                  3.11  µs
  deque lineal, 100 fichas, fallo                                    1.87  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.23  µs
  deque lineal, 1000 fichas, acierto                                 28.47  µs
  deque lineal, 1000 fichas, fallo                                   19.79  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.25  µs
  deque lineal, 5000 fichas, acierto                                 164.24  µs
  deque lineal, 5000 fichas, fallo                                   89.79  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.32  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.075  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.154  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.454  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             2.441  ms
  catálogo con 200 fichas                                            8.709  ms
  catálogo con 1000 fichas                                           8.499  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              19.2  µs
  salas_vecinas, 2 pasos                                             44.4  µs
  precargar_vecinas cuando no hace falta nada                        27.2  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     83 aciertos / 1100 fallos (7.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   10                                                     327 aciertos / 856 fallos (27.6 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   25                                                     553 aciertos / 630 fallos (46.7 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad  100                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad 1000                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista enlazada propia, 25 fichas, acierto (descartada)             0.73  µs
  lista enlazada propia, 100 fichas, acierto (descartada)            2.22  µs
  lista enlazada propia, 1000 fichas, acierto (descartada)           20.82  µs
  lista enlazada propia, 5000 fichas, acierto (descartada)           96.78  µs

Resultados guardados en specs/012-revision-parte-i/bench-cache-M1-1.csv
```

### M1-2 · `cache`

- Fecha y hora: 2026-11-18 06:51:15 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M1-2.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:51 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       64  solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador
  actual + vecinas en cada paso (prof. 2)                            62  solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, prof. 2                                                  56  solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, por defecto (lote de 10)                                 46  solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  deque lineal, 25 fichas, acierto                                   1.05  µs
  deque lineal, 25 fichas, fallo                                     0.55  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.2  µs
  deque lineal, 100 fichas, acierto                                  3.09  µs
  deque lineal, 100 fichas, fallo                                    1.96  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.19  µs
  deque lineal, 1000 fichas, acierto                                 30.34  µs
  deque lineal, 1000 fichas, fallo                                   17.76  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.28  µs
  deque lineal, 5000 fichas, acierto                                 173.42  µs
  deque lineal, 5000 fichas, fallo                                   96.81  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.36  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.071  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.137  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.384  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             2.165  ms
  catálogo con 200 fichas                                            9.504  ms
  catálogo con 1000 fichas                                           8.77  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              20.4  µs
  salas_vecinas, 2 pasos                                             49.2  µs
  precargar_vecinas cuando no hace falta nada                        27.1  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     83 aciertos / 1100 fallos (7.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   10                                                     327 aciertos / 856 fallos (27.6 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   25                                                     553 aciertos / 630 fallos (46.7 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad  100                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad 1000                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista enlazada propia, 25 fichas, acierto (descartada)             0.69  µs
  lista enlazada propia, 100 fichas, acierto (descartada)            2.18  µs
  lista enlazada propia, 1000 fichas, acierto (descartada)           19.12  µs
  lista enlazada propia, 5000 fichas, acierto (descartada)           96.21  µs

Resultados guardados en specs/012-revision-parte-i/bench-cache-M1-2.csv
```

### M1-3 · `cache`

- Fecha y hora: 2026-11-18 06:51:22 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M1-3.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:51 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       64  solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador
  actual + vecinas en cada paso (prof. 2)                            62  solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, prof. 2                                                  56  solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, por defecto (lote de 10)                                 46  solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  deque lineal, 25 fichas, acierto                                   1.12  µs
  deque lineal, 25 fichas, fallo                                     0.65  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.23  µs
  deque lineal, 100 fichas, acierto                                  3.1  µs
  deque lineal, 100 fichas, fallo                                    2.01  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.21  µs
  deque lineal, 1000 fichas, acierto                                 30.15  µs
  deque lineal, 1000 fichas, fallo                                   18.17  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.26  µs
  deque lineal, 5000 fichas, acierto                                 174.69  µs
  deque lineal, 5000 fichas, fallo                                   103.96  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.33  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.07  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.149  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.426  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             2.132  ms
  catálogo con 200 fichas                                            8.72  ms
  catálogo con 1000 fichas                                           9.789  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              18.6  µs
  salas_vecinas, 2 pasos                                             45.0  µs
  precargar_vecinas cuando no hace falta nada                        27.5  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     83 aciertos / 1100 fallos (7.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   10                                                     327 aciertos / 856 fallos (27.6 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   25                                                     553 aciertos / 630 fallos (46.7 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad  100                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad 1000                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista enlazada propia, 25 fichas, acierto (descartada)             0.7  µs
  lista enlazada propia, 100 fichas, acierto (descartada)            2.13  µs
  lista enlazada propia, 1000 fichas, acierto (descartada)           21.07  µs
  lista enlazada propia, 5000 fichas, acierto (descartada)           100.53  µs

Resultados guardados en specs/012-revision-parte-i/bench-cache-M1-3.csv
```

### M1-1 · `guardado`

- Fecha y hora: 2026-11-18 06:51:34 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M1-1.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:51 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,414  bytes
     10 salas  tamaño en disco  [JSON]                               28,363  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                2.00 ms  (1.72 ms – 2.94 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   876.3 µs  (784.1 µs – 1.01 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          2.14 ms  (2.08 ms – 2.23 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 279.7 µs  (274.9 µs – 348.1 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   73.6 µs  (72.0 µs – 92.9 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   289.5 µs  (268.6 µs – 327.1 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            46,646  bytes
    100 salas  tamaño en disco  [JSON]                               133,318  bytes  (2.86× el binario)
    100 salas  guardar la partida completa  [binario]                5.00 ms  (4.82 ms – 6.67 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   3.31 ms  (3.13 ms – 3.38 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          7.02 ms  (6.94 ms – 7.18 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.14 ms  (1.10 ms – 1.16 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  77.1 µs  (73.2 µs – 111.0 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.10 ms  (1.07 ms – 1.20 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            400,347  bytes
   1000 salas  tamaño en disco  [JSON]                               1,199,809  bytes  (3.00× el binario)
   1000 salas  guardar la partida completa  [binario]                36.45 ms  (32.35 ms – 37.37 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   28.10 ms  (27.26 ms – 30.49 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          59.03 ms  (58.12 ms – 60.93 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 8.77 ms  (8.68 ms – 10.13 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 71.1 µs  (67.5 µs – 139.0 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 9.52 ms  (9.03 ms – 11.75 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 
     10 salas  bytes leídos al cargar UNA sala (la primera, la 1)    239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la del medio, la 6)  239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la última, la 10)    262  bytes de 12,414 del archivo; 4 entradas de la tabla
     10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 77.8 µs  (76.0 µs – 79.7 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] 75.0 µs  (71.6 µs – 84.7 µs)  mediana (mín – máx)
  verificación: 10 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4     OK
    100 salas  bytes leídos al cargar UNA sala (la primera, la 1)    299  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) 304  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la última, la 100)   334  bytes de 46,646 del archivo; 7 entradas de la tabla
    100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 85.8 µs  (84.0 µs – 111.3 µs)  mediana (mín – máx)
    100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] 75.4 µs  (73.8 µs – 95.5 µs)  mediana (mín – máx)
  verificación: 100 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7    OK
   1000 salas  bytes leídos al cargar UNA sala (la primera, la 1)    359  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) 374  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la última, la 1000)  397  bytes de 400,347 del archivo; 10 entradas de la tabla
   1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 103.2 µs  (82.7 µs – 309.8 µs)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] 74.3 µs  (72.7 µs – 81.0 µs)  mediana (mín – máx)
  verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 OK

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M1-1.csv
```

### M1-2 · `guardado`

- Fecha y hora: 2026-11-18 06:51:35 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M1-2.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:51 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,414  bytes
     10 salas  tamaño en disco  [JSON]                               28,363  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.61 ms  (1.58 ms – 1.63 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   804.6 µs  (775.5 µs – 875.2 µs)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          2.43 ms  (2.04 ms – 2.76 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 286.7 µs  (276.9 µs – 444.4 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   70.6 µs  (65.8 µs – 108.9 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   279.8 µs  (271.5 µs – 314.9 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            46,646  bytes
    100 salas  tamaño en disco  [JSON]                               133,318  bytes  (2.86× el binario)
    100 salas  guardar la partida completa  [binario]                4.78 ms  (4.75 ms – 4.90 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   3.05 ms  (2.95 ms – 3.31 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          7.02 ms  (6.86 ms – 8.68 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.10 ms  (1.00 ms – 1.18 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  65.5 µs  (63.8 µs – 85.0 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.04 ms  (985.7 µs – 1.10 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            400,347  bytes
   1000 salas  tamaño en disco  [JSON]                               1,199,809  bytes  (3.00× el binario)
   1000 salas  guardar la partida completa  [binario]                38.03 ms  (36.65 ms – 40.36 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   28.94 ms  (28.57 ms – 31.91 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          64.02 ms  (57.26 ms – 77.51 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 9.56 ms  (8.57 ms – 10.15 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 75.3 µs  (70.1 µs – 102.5 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 10.07 ms  (9.78 ms – 11.40 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 
     10 salas  bytes leídos al cargar UNA sala (la primera, la 1)    239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la del medio, la 6)  239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la última, la 10)    262  bytes de 12,414 del archivo; 4 entradas de la tabla
     10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 95.5 µs  (81.0 µs – 186.1 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] 83.4 µs  (76.1 µs – 309.4 µs)  mediana (mín – máx)
  verificación: 10 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4     OK
    100 salas  bytes leídos al cargar UNA sala (la primera, la 1)    299  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) 304  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la última, la 100)   334  bytes de 46,646 del archivo; 7 entradas de la tabla
    100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 74.7 µs  (73.0 µs – 83.8 µs)  mediana (mín – máx)
    100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] 64.9 µs  (64.5 µs – 76.0 µs)  mediana (mín – máx)
  verificación: 100 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7    OK
   1000 salas  bytes leídos al cargar UNA sala (la primera, la 1)    359  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) 374  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la última, la 1000)  397  bytes de 400,347 del archivo; 10 entradas de la tabla
   1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 97.9 µs  (95.4 µs – 150.0 µs)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] 83.0 µs  (81.5 µs – 135.7 µs)  mediana (mín – máx)
  verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 OK

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M1-2.csv
```

### M1-3 · `guardado`

- Fecha y hora: 2026-11-18 06:51:37 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M1-3.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 06:51 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,414  bytes
     10 salas  tamaño en disco  [JSON]                               28,363  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.70 ms  (1.67 ms – 1.76 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   773.6 µs  (762.9 µs – 822.5 µs)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          2.54 ms  (2.12 ms – 2.99 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 328.6 µs  (303.6 µs – 426.4 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   74.8 µs  (72.9 µs – 111.4 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   355.8 µs  (296.6 µs – 400.7 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            46,646  bytes
    100 salas  tamaño en disco  [JSON]                               133,318  bytes  (2.86× el binario)
    100 salas  guardar la partida completa  [binario]                5.11 ms  (4.44 ms – 6.33 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   4.20 ms  (3.46 ms – 4.92 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          6.65 ms  (6.03 ms – 7.02 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.12 ms  (1.08 ms – 1.17 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  75.7 µs  (73.9 µs – 94.5 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.10 ms  (1.09 ms – 1.12 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            400,347  bytes
   1000 salas  tamaño en disco  [JSON]                               1,199,809  bytes  (3.00× el binario)
   1000 salas  guardar la partida completa  [binario]                36.70 ms  (34.64 ms – 38.20 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   29.04 ms  (27.37 ms – 31.24 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          58.25 ms  (52.08 ms – 62.37 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 9.68 ms  (9.56 ms – 10.44 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 82.7 µs  (78.0 µs – 114.7 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 9.69 ms  (9.42 ms – 11.70 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 
     10 salas  bytes leídos al cargar UNA sala (la primera, la 1)    239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la del medio, la 6)  239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la última, la 10)    262  bytes de 12,414 del archivo; 4 entradas de la tabla
     10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 79.1 µs  (76.6 µs – 88.3 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] 74.4 µs  (72.4 µs – 84.6 µs)  mediana (mín – máx)
  verificación: 10 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4     OK
    100 salas  bytes leídos al cargar UNA sala (la primera, la 1)    299  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) 304  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la última, la 100)   334  bytes de 46,646 del archivo; 7 entradas de la tabla
    100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 85.5 µs  (84.1 µs – 106.7 µs)  mediana (mín – máx)
    100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] 75.8 µs  (74.8 µs – 173.0 µs)  mediana (mín – máx)
  verificación: 100 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7    OK
   1000 salas  bytes leídos al cargar UNA sala (la primera, la 1)    359  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) 374  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la última, la 1000)  397  bytes de 400,347 del archivo; 10 entradas de la tabla
   1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 97.9 µs  (94.4 µs – 108.7 µs)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] 80.6 µs  (79.7 µs – 96.8 µs)  mediana (mín – máx)
  verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 OK

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M1-3.csv
```

## M2 · el después

- **Commit**: `70c9854` (`git rev-parse --short HEAD`). Árbol sin cambios en `adaptadores/` ni en `bench/`; solo
  archivos ajenos a la capacidad (`bench_final.txt`, `descargar_cripta.py` y los fines de línea de `specs/003`).
  Código revisado: D1 (`salas_vecinas` sobre su propia lista) y D2 (`CacheLRU` sobre una lista propia), con el
  código de medición de M1.
- **Ejecución**: en primer plano, una tras otra, con `PYTHONIOENCODING=utf-8`. Las seis ejecuciones terminaron con
  código 0 al primer intento.

### M2-1 · `cache`

- Fecha y hora: 2026-11-18 07:13:53 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M2-1.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 07:13 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       64  solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador
  actual + vecinas en cada paso (prof. 2)                            62  solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, prof. 2                                                  56  solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, por defecto (lote de 10)                                 46  solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista propia lineal, 25 fichas, acierto                            0.7  µs
  lista propia lineal, 25 fichas, fallo                              0.6  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.2  µs
  lista propia lineal, 100 fichas, acierto                           1.98  µs
  lista propia lineal, 100 fichas, fallo                             1.91  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.22  µs
  lista propia lineal, 1000 fichas, acierto                          18.46  µs
  lista propia lineal, 1000 fichas, fallo                            18.29  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.24  µs
  lista propia lineal, 5000 fichas, acierto                          104.45  µs
  lista propia lineal, 5000 fichas, fallo                            95.16  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.31  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.071  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.178  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.456  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             3.319  ms
  catálogo con 200 fichas                                            9.793  ms
  catálogo con 1000 fichas                                           11.038  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              17.6  µs
  salas_vecinas, 2 pasos                                             44.2  µs
  precargar_vecinas cuando no hace falta nada                        27.4  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     83 aciertos / 1100 fallos (7.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   10                                                     327 aciertos / 856 fallos (27.6 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   25                                                     553 aciertos / 630 fallos (46.7 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad  100                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad 1000                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista enlazada propia, 25 fichas, acierto (descartada)             0.72  µs
  lista enlazada propia, 100 fichas, acierto (descartada)            2.17  µs
  lista enlazada propia, 1000 fichas, acierto (descartada)           18.94  µs
  lista enlazada propia, 5000 fichas, acierto (descartada)           108.04  µs

Resultados guardados en specs/012-revision-parte-i/bench-cache-M2-1.csv
```

### M2-2 · `cache`

- Fecha y hora: 2026-11-18 07:14:01 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M2-2.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 07:14 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       64  solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador
  actual + vecinas en cada paso (prof. 2)                            62  solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, prof. 2                                                  56  solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, por defecto (lote de 10)                                 46  solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista propia lineal, 25 fichas, acierto                            0.85  µs
  lista propia lineal, 25 fichas, fallo                              0.66  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.24  µs
  lista propia lineal, 100 fichas, acierto                           2.25  µs
  lista propia lineal, 100 fichas, fallo                             2.18  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.23  µs
  lista propia lineal, 1000 fichas, acierto                          20.26  µs
  lista propia lineal, 1000 fichas, fallo                            20.16  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.28  µs
  lista propia lineal, 5000 fichas, acierto                          116.68  µs
  lista propia lineal, 5000 fichas, fallo                            101.23  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.3  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.071  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.277  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.437  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             2.087  ms
  catálogo con 200 fichas                                            9.975  ms
  catálogo con 1000 fichas                                           10.758  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              20.0  µs
  salas_vecinas, 2 pasos                                             54.5  µs
  precargar_vecinas cuando no hace falta nada                        31.8  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     83 aciertos / 1100 fallos (7.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   10                                                     327 aciertos / 856 fallos (27.6 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   25                                                     553 aciertos / 630 fallos (46.7 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad  100                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad 1000                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista enlazada propia, 25 fichas, acierto (descartada)             0.71  µs
  lista enlazada propia, 100 fichas, acierto (descartada)            2.08  µs
  lista enlazada propia, 1000 fichas, acierto (descartada)           20.98  µs
  lista enlazada propia, 5000 fichas, acierto (descartada)           103.79  µs

Resultados guardados en specs/012-revision-parte-i/bench-cache-M2-2.csv
```

### M2-3 · `cache`

- Fecha y hora: 2026-11-18 07:14:08 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench cache --bench-csv specs/012-revision-parte-i/bench-cache-M2-3.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 07:14 · semilla 2026
... midiendo cache

Red, caché y disco (§4.2–§4.4, §5.1): 1. Solicitudes al recorrer un pasillo de 60 salas
  sala por sala (sin precarga)                                       64  solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador
  actual + vecinas en cada paso (prof. 2)                            62  solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, prof. 2                                                  56  solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador
  perezosa, por defecto (lote de 10)                                 46  solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista propia lineal, 25 fichas, acierto                            0.8  µs
  lista propia lineal, 25 fichas, fallo                              0.57  µs
  tabla hash propia, 25 fichas, acierto (descartada)                 0.19  µs
  lista propia lineal, 100 fichas, acierto                           2.71  µs
  lista propia lineal, 100 fichas, fallo                             2.14  µs
  tabla hash propia, 100 fichas, acierto (descartada)                0.2  µs
  lista propia lineal, 1000 fichas, acierto                          18.14  µs
  lista propia lineal, 1000 fichas, fallo                            19.12  µs
  tabla hash propia, 1000 fichas, acierto (descartada)               0.26  µs
  lista propia lineal, 5000 fichas, acierto                          107.81  µs
  lista propia lineal, 5000 fichas, fallo                            96.46  µs
  tabla hash propia, 5000 fichas, acierto (descartada)               0.29  µs

Red, caché y disco (§4.2–§4.4, §5.1): 3. Recuperar una ficha liberada desde disco
  catálogo con 25 fichas                                             0.073  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 200 fichas                                            0.167  ms por lectura (una solicitud real: ~400 ms)
  catálogo con 1000 fichas                                           0.436  ms por lectura (una solicitud real: ~400 ms)

Red, caché y disco (§4.2–§4.4, §5.1): 4. Guardar 10 fichas nuevas (reescribe el archivo completo)
  catálogo con 25 fichas                                             2.331  ms
  catálogo con 200 fichas                                            9.941  ms
  catálogo con 1000 fichas                                           10.459  ms

Red, caché y disco (§4.2–§4.4, §5.1): 5. Planear la vecindad en una cripta de 1000 salas
  salas_vecinas, 1 paso                                              18.6  µs
  salas_vecinas, 2 pasos                                             46.6  µs
  precargar_vecinas cuando no hace falta nada                        27.0  µs

Red, caché y disco (§4.2–§4.4, §5.1): 6. Caché en una partida completa (150 pasos por una rejilla de 10x10)
  capacidad    5                                                     83 aciertos / 1100 fallos (7.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   10                                                     327 aciertos / 856 fallos (27.6 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad   25                                                     553 aciertos / 630 fallos (46.7 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad  100                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador
  capacidad 1000                                                     1112 aciertos / 71 fallos (94.0 %)  64 solicitudes de red; de ellas, 45 disparadas por un cazador

Red, caché y disco (§4.2–§4.4, §5.1): 2. Búsqueda en la caché (µs por operación)
  lista enlazada propia, 25 fichas, acierto (descartada)             0.83  µs
  lista enlazada propia, 100 fichas, acierto (descartada)            3.83  µs
  lista enlazada propia, 1000 fichas, acierto (descartada)           23.61  µs
  lista enlazada propia, 5000 fichas, acierto (descartada)           109.43  µs

Resultados guardados en specs/012-revision-parte-i/bench-cache-M2-3.csv
```

### M2-1 · `guardado`

- Fecha y hora: 2026-11-18 07:14:16 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M2-1.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 07:14 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,414  bytes
     10 salas  tamaño en disco  [JSON]                               28,363  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.87 ms  (1.76 ms – 2.81 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   825.5 µs  (796.6 µs – 1.01 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          2.27 ms  (2.22 ms – 2.47 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 316.1 µs  (299.9 µs – 412.6 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   73.5 µs  (71.3 µs – 90.9 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   279.5 µs  (270.6 µs – 300.3 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            46,646  bytes
    100 salas  tamaño en disco  [JSON]                               133,318  bytes  (2.86× el binario)
    100 salas  guardar la partida completa  [binario]                4.87 ms  (4.52 ms – 4.89 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   3.40 ms  (3.31 ms – 3.63 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          7.51 ms  (7.04 ms – 11.25 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.22 ms  (1.11 ms – 1.27 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  78.7 µs  (73.3 µs – 98.9 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.13 ms  (1.11 ms – 1.19 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            400,347  bytes
   1000 salas  tamaño en disco  [JSON]                               1,199,809  bytes  (3.00× el binario)
   1000 salas  guardar la partida completa  [binario]                37.19 ms  (36.07 ms – 40.16 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   40.78 ms  (28.56 ms – 51.64 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          59.97 ms  (58.60 ms – 65.44 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 10.70 ms  (10.04 ms – 11.83 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 88.8 µs  (81.9 µs – 114.0 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 10.13 ms  (9.63 ms – 13.68 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 
     10 salas  bytes leídos al cargar UNA sala (la primera, la 1)    239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la del medio, la 6)  239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la última, la 10)    262  bytes de 12,414 del archivo; 4 entradas de la tabla
     10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 77.2 µs  (76.1 µs – 90.9 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] 72.3 µs  (71.1 µs – 124.3 µs)  mediana (mín – máx)
  verificación: 10 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4     OK
    100 salas  bytes leídos al cargar UNA sala (la primera, la 1)    299  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) 304  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la última, la 100)   334  bytes de 46,646 del archivo; 7 entradas de la tabla
    100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 85.5 µs  (84.0 µs – 90.2 µs)  mediana (mín – máx)
    100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] 77.0 µs  (74.4 µs – 79.0 µs)  mediana (mín – máx)
  verificación: 100 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7    OK
   1000 salas  bytes leídos al cargar UNA sala (la primera, la 1)    359  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) 374  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la última, la 1000)  397  bytes de 400,347 del archivo; 10 entradas de la tabla
   1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 99.0 µs  (93.9 µs – 108.7 µs)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] 81.7 µs  (79.8 µs – 94.6 µs)  mediana (mín – máx)
  verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 OK

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M2-1.csv
```

### M2-2 · `guardado`

- Fecha y hora: 2026-11-18 07:14:18 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M2-2.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 07:14 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,414  bytes
     10 salas  tamaño en disco  [JSON]                               28,363  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.96 ms  (1.80 ms – 3.14 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   880.9 µs  (822.9 µs – 1.10 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          1.90 ms  (1.87 ms – 1.97 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 289.7 µs  (272.4 µs – 388.3 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   74.6 µs  (66.5 µs – 112.1 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   276.9 µs  (271.7 µs – 301.6 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            46,646  bytes
    100 salas  tamaño en disco  [JSON]                               133,318  bytes  (2.86× el binario)
    100 salas  guardar la partida completa  [binario]                4.56 ms  (4.46 ms – 5.01 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   2.96 ms  (2.88 ms – 3.17 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          6.71 ms  (6.44 ms – 7.64 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.12 ms  (1.09 ms – 1.18 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  76.1 µs  (69.0 µs – 101.7 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.21 ms  (1.14 ms – 1.49 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            400,347  bytes
   1000 salas  tamaño en disco  [JSON]                               1,199,809  bytes  (3.00× el binario)
   1000 salas  guardar la partida completa  [binario]                35.98 ms  (33.96 ms – 40.71 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   27.61 ms  (27.09 ms – 29.72 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          55.73 ms  (55.05 ms – 58.07 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 11.31 ms  (9.11 ms – 11.55 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 73.3 µs  (68.5 µs – 111.3 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 10.37 ms  (9.93 ms – 11.95 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 
     10 salas  bytes leídos al cargar UNA sala (la primera, la 1)    239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la del medio, la 6)  239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la última, la 10)    262  bytes de 12,414 del archivo; 4 entradas de la tabla
     10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 78.5 µs  (76.0 µs – 80.2 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] 73.4 µs  (72.7 µs – 77.1 µs)  mediana (mín – máx)
  verificación: 10 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4     OK
    100 salas  bytes leídos al cargar UNA sala (la primera, la 1)    299  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) 304  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la última, la 100)   334  bytes de 46,646 del archivo; 7 entradas de la tabla
    100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 86.0 µs  (85.2 µs – 134.1 µs)  mediana (mín – máx)
    100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] 76.7 µs  (75.1 µs – 79.1 µs)  mediana (mín – máx)
  verificación: 100 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7    OK
   1000 salas  bytes leídos al cargar UNA sala (la primera, la 1)    359  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) 374  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la última, la 1000)  397  bytes de 400,347 del archivo; 10 entradas de la tabla
   1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 84.3 µs  (81.8 µs – 103.3 µs)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] 74.0 µs  (69.5 µs – 310.2 µs)  mediana (mín – máx)
  verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 OK

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M2-2.csv
```

### M2-3 · `guardado`

- Fecha y hora: 2026-11-18 07:14:19 -0600
- Comando: `PYTHONIOENCODING=utf-8 python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M2-3.csv`
- Código de salida: 0

```
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-18 07:14 · semilla 2026
... midiendo guardado

Guardado de la partida (§4.10): binario propio  vs  JSON
  verificación: cargar el binario devuelve exactamente el estado guardado OK
  verificación: un archivo de otra versión del formato se rechaza    OK
     10 salas  tamaño en disco  [binario]                            12,414  bytes
     10 salas  tamaño en disco  [JSON]                               28,363  bytes  (2.28× el binario)
     10 salas  guardar la partida completa  [binario]                1.70 ms  (1.65 ms – 1.73 ms)  mediana (mín – máx)
     10 salas  guardar la partida completa  [JSON]                   799.1 µs  (768.0 µs – 848.5 µs)  mediana (mín – máx)
     10 salas  cargar la partida completa   [binario → DTO]          2.02 ms  (1.81 ms – 2.22 ms)  mediana (mín – máx)
     10 salas  cargar la partida completa   [JSON, solo analiza el texto] 277.9 µs  (259.3 µs – 362.1 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la 6)    [binario, acceso directo]   65.3 µs  (63.2 µs – 81.4 µs)  mediana (mín – máx)
     10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo]   265.3 µs  (253.0 µs – 281.4 µs)  mediana (mín – máx)
    100 salas  tamaño en disco  [binario]                            46,646  bytes
    100 salas  tamaño en disco  [JSON]                               133,318  bytes  (2.86× el binario)
    100 salas  guardar la partida completa  [binario]                4.56 ms  (4.41 ms – 6.83 ms)  mediana (mín – máx)
    100 salas  guardar la partida completa  [JSON]                   3.56 ms  (3.30 ms – 3.67 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [binario → DTO]          6.24 ms  (6.05 ms – 6.80 ms)  mediana (mín – máx)
    100 salas  cargar la partida completa   [JSON, solo analiza el texto] 1.11 ms  (1.08 ms – 1.22 ms)  mediana (mín – máx)
    100 salas  cargar UNA sala (la 51)    [binario, acceso directo]  66.0 µs  (64.2 µs – 86.3 µs)  mediana (mín – máx)
    100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo]  1.09 ms  (1.02 ms – 1.16 ms)  mediana (mín – máx)
   1000 salas  tamaño en disco  [binario]                            400,347  bytes
   1000 salas  tamaño en disco  [JSON]                               1,199,809  bytes  (3.00× el binario)
   1000 salas  guardar la partida completa  [binario]                34.93 ms  (33.37 ms – 38.13 ms)  mediana (mín – máx)
   1000 salas  guardar la partida completa  [JSON]                   29.75 ms  (27.51 ms – 31.30 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [binario → DTO]          57.61 ms  (53.82 ms – 58.52 ms)  mediana (mín – máx)
   1000 salas  cargar la partida completa   [JSON, solo analiza el texto] 9.44 ms  (9.18 ms – 9.72 ms)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] 81.7 µs  (78.5 µs – 109.2 µs)  mediana (mín – máx)
   1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] 10.02 ms  (8.46 ms – 11.96 ms)  mediana (mín – máx)
  El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. 
     10 salas  bytes leídos al cargar UNA sala (la primera, la 1)    239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la del medio, la 6)  239  bytes de 12,414 del archivo; 3 entradas de la tabla
     10 salas  bytes leídos al cargar UNA sala (la última, la 10)    262  bytes de 12,414 del archivo; 4 entradas de la tabla
     10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 68.1 µs  (66.4 µs – 127.8 µs)  mediana (mín – máx)
     10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] 63.5 µs  (62.2 µs – 146.1 µs)  mediana (mín – máx)
  verificación: 10 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4     OK
    100 salas  bytes leídos al cargar UNA sala (la primera, la 1)    299  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) 304  bytes de 46,646 del archivo; 6 entradas de la tabla
    100 salas  bytes leídos al cargar UNA sala (la última, la 100)   334  bytes de 46,646 del archivo; 7 entradas de la tabla
    100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 74.9 µs  (72.3 µs – 89.8 µs)  mediana (mín – máx)
    100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] 65.3 µs  (64.2 µs – 79.7 µs)  mediana (mín – máx)
  verificación: 100 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7    OK
   1000 salas  bytes leídos al cargar UNA sala (la primera, la 1)    359  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) 374  bytes de 400,347 del archivo; 9 entradas de la tabla
   1000 salas  bytes leídos al cargar UNA sala (la última, la 1000)  397  bytes de 400,347 del archivo; 10 entradas de la tabla
   1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] 95.4 µs  (86.6 µs – 101.7 µs)  mediana (mín – máx)
   1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] 71.7 µs  (69.6 µs – 80.7 µs)  mediana (mín – máx)
  verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo OK
  verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 OK

Resultados guardados en specs/012-revision-parte-i/bench-guardado-M2-3.csv
```

## Comprobación de las filas de cuenta

- **M0**: las 10 filas de cuenta de `cache` y las 8 de `guardado` son idénticas en las tres ejecuciones.
- **M1**: las 10 filas de cuenta de `cache` y las 26 de `guardado` (8 existentes y 18 nuevas: bytes leídos y verificaciones) son idénticas en las tres ejecuciones.
- **M2** (T032): las 10 filas de cuenta de `cache` y las 26 de `guardado` son idénticas en las tres ejecuciones.
- **M1 = M2** (T032, FR-387): todas las filas de cuenta de los dos bloques son iguales en M1 y M2, incluidas las secciones 1 y 6 de `cache` (solicitudes, aciertos, fallos y disparadas por cazadores). D1 y D2 no cambian ninguna cuenta. Lo único que cambia entre M1 y M2 es el nombre de las filas 5, 6, 8, 9, 11, 12, 14 y 15 (T029).

## Medición manual

T036 (FR-382, segunda viñeta). Script temporal fuera del repositorio (ya borrado): copia `datos_cripta/` a una carpeta
temporal, arma el servicio con `crear_servicio(offline=True)` sobre la copia y bloquea `requests.get` y
`requests.post`. Arma la partida con el modelo real (`EstadoJuegoLogica`), entra en la sala inicial y carga las demás
salas con `_cargarSala` (como cuando un enemigo entra en una sala: sin precarga), la exporta y la guarda en formato 8
con `AlmacenPartidaBinario`. Mide con la subclase contadora `_AlmacenContador` de `bench/guardado.py` (T021).
`datos_cripta/` quedó sin cambios (mismo md5 antes y después).

```
## Criptas en datos_cripta/
- cripta-02: 20 salas; datos: sí; contenido de todas las salas: no; fichas de catálogo que faltan: 0 -> incompleta
- cripta-03: 40 salas; datos: sí; contenido de todas las salas: no; fichas de catálogo que faltan: 0 -> incompleta
- cripta-04: 50 salas; datos: sí; contenido de todas las salas: sí; fichas de catálogo que faltan: 0 -> COMPLETA
- cripta-05: 24 salas; datos: sí; contenido de todas las salas: sí; fichas de catálogo que faltan: 0 -> COMPLETA
- cripta-06: 300 salas; datos: sí; contenido de todas las salas: no; fichas de catálogo que faltan: 0 -> incompleta

## Cripta elegida: cripta-04 (50 salas)
- salas en la partida exportada: 50; solicitudes del servicio: 0
- tamaño del archivo (formato 8): 25,004 bytes
- ⌊log₂ n⌋ + 1 = 6 (n = 50)

| Sala | Bytes leídos | Entradas de la tabla | Tiempo (mediana de 9) |
|---|---|---|---|
| la primera (1) | 222 de 25,004 | 5 | 100.6 µs |
| la del medio (26) | 191 de 25,004 | 5 | 61.0 µs |
| la última (50) | 322 de 25,004 | 6 | 71.5 µs |

- carga completa: 3.83 ms (mediana de 5)
- solicitudes al final: 0
- fecha y hora: 2026-11-18 07:15:46
```

- **Criptas**: `criptas.bin` lista cripta-02 a cripta-06; cripta-01 tiene archivo pero no está en la lista. Solo
  cripta-04 (50 salas) y cripta-05 (24) tienen esqueleto, datos, contenido de todas las salas y catálogo. cripta-06
  (300 salas, la más grande) no tiene contenido de todas sus salas, como ya había visto la 003. **Se usó cripta-04.**
  No se descargó nada.
- **Resultado**: la partida de 50 salas pesa 25 004 bytes; leer UNA sala lee de 191 a 322 bytes y de 5 a 6 entradas
  de la tabla (⌊log₂ 50⌋ + 1 = 6), y tarda de 61 a 101 µs frente a 3.83 ms de la carga completa. **0 solicitudes.**
  Cumple FR-382 y SC-006.

## Pruebas

### M0 (código de `0b031ec`, T003)

| Comando | Fecha y hora | Ejecutadas | Fallos | Errores | Omitidas | Código de salida |
|---|---|---|---|---|---|---|
| `python -m unittest discover -p "test_*.py"` | 2026-11-18 06:30:17 -0600 | 711 | 1 | 0 | 0 | 1 |
| `python -m tests_labs.sin_red` | 2026-11-18 06:30:48 -0600 | 180 | 0 | 0 | 0 | 0 |

Ambas se ejecutaron con `PYTHONIOENCODING=utf-8`, por la misma razón que `guardado`.

**El fallo de `discover`** es `bench.test_bench_puntos_control.TestBenchPuntosControl.test_ejecutar_benchmark_puntos_control`: `AssertionError: False is not true : El benchmark de puntos de control debe cumplir con el límite de 20 ms con K=1`. Es una prueba de tiempo que depende de la máquina, del código sin tocar. Ejecutada sola una vez más (`python -m unittest bench.test_bench_puntos_control -v`), pasa (1 prueba, OK). Este es el resultado de M0 que M2 tiene que repetir (FR-387): 711 ejecutadas en `discover`, más las pruebas de los dos archivos nuevos, sin fallos nuevos; si `test_bench_puntos_control` vuelve a fallar por tiempo, se anota igual que aquí.

### Fin de la fase 3 (código de medición con la carga; producción de `0b031ec`)

| Comando | Fecha y hora | Ejecutadas | Fallos | Errores | Omitidas | Código de salida |
|---|---|---|---|---|---|---|
| `python -m unittest discover -p "test_*.py"` | 2026-11-18 06:53:09 -0600 | 732 | 2 | 0 | 0 | 1 |
| `python -m tests_labs.sin_red` | 2026-11-18 06:53:25 -0600 | 180 | 0 | 0 | 0 | 0 |

732 = las 711 de M0 + 12 de `test_vecindad_equivalencia` + 9 de `test_cache_equivalencia`. Los dos fallos son los esperados, T009 (`test_fr375_salas_vecinas_sin_estructuras_prohibidas`) y T012 (`test_fr386_cache_sin_importaciones_prohibidas`), que pasan después de D1 y D2. No hay fallos nuevos respecto de M0: los cambios del código de medición no rompen ninguna prueba existente. Esta vez `test_bench_puntos_control` pasó.

### Pruebas de equivalencia

**Contra el código de `0b031ec`** (T013 y T014, 2026-11-18; `git diff --stat 0b031ec -- adaptadores` sin salida):

| Comando | Ejecutadas | Pasan | Fallan | Errores | Omitidas | Fallan (cuáles) |
|---|---|---|---|---|---|---|
| `python -m unittest test_vecindad_equivalencia -v` | 12 | 11 | 1 | 0 | 0 | `PrincipioI.test_fr375_salas_vecinas_sin_estructuras_prohibidas` (T009): `salas_vecinas usa ['deque'] (principio I)` |
| `python -m unittest test_cache_equivalencia -v` | 9 | 8 | 1 | 0 | 0 | `PrincipioI.test_fr386_cache_sin_importaciones_prohibidas` (T012): `adaptadores/cache.py importa ['collections'] (principio I)` |

Los dos fallos son los esperados: comprueban el principio I y el código vigente todavía usa la cola de biblioteca. Tienen que pasar después de D1 (T025) y D2 (T028). Todo lo demás pasa, así que las referencias escritas en las pruebas reproducen lo vigente.

- Corrección de la referencia durante T013 (la prueba, no el código): en la cripta con la puerta cerrada, la sala 2 con profundidad 1 da `[3, 1]` y no `[1, 3]`, porque la salida E se recorre antes que la O (orden N, S, E, O).
- Cobertura de las secuencias aleatorias de T010: hay expulsiones en las cuatro capacidades (de 6 021 a 8 116 por capacidad) e inserciones rechazadas con todo en uso en las capacidades 1 (3 029) y 2 (526). Con 5 y 25 no hay rechazos; el caso dirigido de T011 los cubre.

**Contra el código revisado** (2026-11-18):

| Tarea | Comando | Ejecutadas | Fallos | Errores |
|---|---|---|---|---|
| T025 (después de D1) | `python -m unittest test_vecindad_equivalencia -v` | 13 (con T047) | 0 | 0 |
| T028 (después de D2) | `python -m unittest test_cache_equivalencia -v` | 9 | 0 | 0 |
| T030 (07:05:14) | `python -m unittest discover -p "test_*.py"` | 733 | 0 | 0 |
| T030 (07:05:30) | `python -m tests_labs.sin_red` | 180 | 0 | 0 |

T009 y T012 pasan desde D1 y D2. `test_bench_puntos_control` no falló en ninguna de estas ejecuciones. Después del
ajuste de margen de la caché (commit `70c9854`) se repitieron las tres: 9 de 9 en `test_cache_equivalencia`, 733 y
180 sin fallos.

### Cierre (T045)

Código: `cebe5ca` más el cambio de T044 en `tests_labs/sin_red.py`, que agrega `test_vecindad_equivalencia` y
`test_cache_equivalencia` a `PRUEBAS`. El código de producción y el de medición son los de M2 (`70c9854`). Los cuatro
comandos se ejecutaron uno por uno, en primer plano y con `PYTHONIOENCODING=utf-8`, el 2026-11-18:

| Comando | Hora | Ejecutadas | Fallos | Errores | Omitidas | Código de salida |
|---|---|---|---|---|---|---|
| `python -m unittest discover -p "test_*.py"` | 07:30:21 -0600 | 733 | 0 | 0 | 0 | 0 |
| `python -m tests_labs.sin_red` | 07:30:46 -0600 | 202 | 0 | 0 | 0 | 0 |
| `python main.py --bench cache` | 07:30:54 -0600 | — | — | — | — | 0 |
| `python main.py --bench guardado` | 07:31:06 -0600 | — | — | — | — | 0 |

- **`discover`**: 733 = las 711 de M0 + 13 de `test_vecindad_equivalencia` (con T047) + 9 de `test_cache_equivalencia`.
  Hay 0 fallos; en M0 hubo 1 (`test_bench_puntos_control`, por tiempo). Esta vez `test_bench_puntos_control` pasó.
- **`sin_red`**: 202 = las 180 de M0 + las 22 de los dos archivos agregados en T044 (13 + 9), todas con
  `requests.get` bloqueado.
- **`--bench cache`**: las filas de cuenta de las secciones 1 y 6 son iguales a M1 y M2. En la sección 1 da
  64 / 62 / 56 / 46 solicitudes, con 45 / 44 / 44 / 39 disparadas por un cazador. En la sección 6, 64 solicitudes con
  todas las capacidades; con capacidad 25, 553 aciertos y 630 fallos.
- **`--bench guardado`**: las 8 verificaciones dan OK. Los tamaños (12,414, 46,646 y 400,347 bytes) y los bytes y
  entradas leídos por sala son iguales a M1 y M2.
- **Archivos que no se tocan**: `git diff --stat 0b031ec -- DTO/SalaDTO.py DTO/EstadoGuardadoDTO.py
  Logica/EstadoGuardadoLogica.py adaptadores/AlmacenPartidaBinario.py adaptadores/codec_partida.py` no muestra nada.
- **`adaptadores/servicioCripta.py`**: `git diff --stat 0b031ec` da 11 líneas agregadas y 7 quitadas, todas en el cuerpo
  de `salas_vecinas` (D1). La importación de la línea 2 sigue, porque la usa `_armar_salidas` (uso 4, justificado).

## Tabla por bloque

Antes = M0 y Carga = M1 (mediana en las filas de tiempo; valor común en las de cuenta). Después = M2, con el mismo criterio. **Límite** (T033, FR-383 y FR-384): 2 × M0; 2 × M1 en las filas nuevas (sin antes en M0) y en las filas de red que la carga ya llevó a más del doble de M0 (fila 4 y filas 26 a 30, corrección L1 de la spec). En las filas de cuenta de red el límite se aplica a las solicitudes. Los tamaños en disco no tienen límite (FR-384 limita guardar, cargar y leer). **Resultado: todas las filas cumplen.** La más cercana a su límite es la fila 3 (perezosa, prof. 2): 56 solicitudes contra 66 (2 × M0), 1.70 × M0, por la carga (+1 llaves y 44 disparadas por cazadores); el código no la mueve (M2 = M1).

### Bloque `cache`

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

### Bloque `guardado`

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

### T034 · Criterio de cambio de D2: no aplica

Ninguna fila «lista propia lineal» de la sección 2 pasa de 2 × su antes (M0). La más cercana es la **fila 9** (100
fichas, fallo): 2.14 µs en M2 contra 2.13 µs en M0 (1.00 ×, límite 4.26 µs). Las de acierto bajan entre 0.54 × y
0.73 × M0 (por ejemplo, la fila 11, 1 000 fichas: de 33.93 a 18.46 µs). No se pasa a la lista enlazada; la caché
queda como lista propia con la más reciente al final (D2), con la búsqueda sin índice del ajuste de margen
(commit `70c9854`).

### T035 · Leer UNA sala del binario (FR-382, FR-384)

M2, mediana de tres ejecuciones; entre paréntesis, las tres ejecuciones.

| Salas | Archivo | Bytes leídos: primera / medio / última | Entradas (≤ ⌊log₂ n⌋ + 1) | Verificaciones T021 | Una sala: primera | del medio | última | Carga completa |
|---|---|---|---|---|---|---|---|---|
| 10 | 12,414 bytes | 239 / 239 / 262 | 3 / 3 / 4 (≤ 4) | OK, OK | 77.2 µs (77.2 µs / 78.5 µs / 68.1 µs) | 73.5 µs (73.5 µs / 74.6 µs / 65.3 µs) | 72.3 µs (72.3 µs / 73.4 µs / 63.5 µs) | 2.02 ms (2.27 ms / 1.90 ms / 2.02 ms) |
| 100 | 46,646 bytes | 299 / 304 / 334 | 6 / 6 / 7 (≤ 7) | OK, OK | 85.5 µs (85.5 µs / 86.0 µs / 74.9 µs) | 76.1 µs (78.7 µs / 76.1 µs / 66.0 µs) | 76.7 µs (77.0 µs / 76.7 µs / 65.3 µs) | 6.71 ms (7.51 ms / 6.71 ms / 6.24 ms) |
| 1,000 | 400,347 bytes | 359 / 374 / 397 | 9 / 9 / 10 (≤ 10) | OK, OK | 95.4 µs (99.0 µs / 84.3 µs / 95.4 µs) | 81.7 µs (88.8 µs / 73.3 µs / 81.7 µs) | 74.0 µs (81.7 µs / 74.0 µs / 71.7 µs) | 57.61 ms (59.97 ms / 55.73 ms / 57.61 ms) |

- **Bytes leídos**: siempre mucho menos que el archivo (397 de 400 347 bytes en el peor caso) y con crecimiento
  logarítmico: de 239–262 bytes con 10 salas a 359–397 con 1 000, y las entradas leídas suben de 3–4 a 9–10, nunca
  más de ⌊log₂ n⌋ + 1. Las seis verificaciones de T021 dan OK.
- **Una sala contra la carga completa**: leer una sala tarda de 72 a 95 µs y cargar la partida, de 2.02 ms (10 salas) a
  57.61 ms (1 000); la lectura de una sala es siempre más rápida.
- **Tiempo de una sala al crecer n** (Historia 4, escenario 3): la del medio (73.5 → 81.7 µs) y la última
  (72.3 → 74.0 µs) quedan dentro de la variación entre las tres ejecuciones (los rangos de 10 y de 1 000 salas se
  solapan). **La primera crece algo más**: de 77.2 µs (68.1–78.5) con 10 salas a 95.4 µs (84.3–99.0) con 1 000, +24 %
  para 100 veces más salas, y los rangos no se solapan. Es el crecimiento logarítmico de H2 (3 entradas leídas con 10
  salas, 9 con 1 000), no un crecimiento con n: el escenario 3 de la Historia 4 dice «no crece más allá de la variación
  de la máquina», y la primera sala lo cumple solo si ese escenario admite el crecimiento logarítmico que ya fija
  FR-382. Se anota como hallazgo para la sección 012 de `DECISIONES.md`.

## Detalle de M0: las tres ejecuciones

### Bloque `cache`

| # | Sección | Medición | Tipo | M0-1 | M0-2 | M0-3 | Antes (M0) |
|---|---|---|---|---|---|---|---|
| 1 | 1. Solicitudes al recorrer un pasillo de 60 salas | sala por sala (sin precarga) | cuenta | 63 solicitudes (~25.2 s de espera) | 63 solicitudes (~25.2 s de espera) | 63 solicitudes (~25.2 s de espera) | 63 solicitudes (~25.2 s de espera) (igual en las tres) |
| 2 | 1. Solicitudes al recorrer un pasillo de 60 salas | actual + vecinas en cada paso (prof. 2) | cuenta | 61 solicitudes (~24.4 s de espera) | 61 solicitudes (~24.4 s de espera) | 61 solicitudes (~24.4 s de espera) | 61 solicitudes (~24.4 s de espera) (igual en las tres) |
| 3 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, prof. 2 | cuenta | 33 solicitudes (~13.2 s de espera) | 33 solicitudes (~13.2 s de espera) | 33 solicitudes (~13.2 s de espera) | 33 solicitudes (~13.2 s de espera) (igual en las tres) |
| 4 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, por defecto (lote de 10) | cuenta | 9 solicitudes (~3.6 s de espera) | 9 solicitudes (~3.6 s de espera) | 9 solicitudes (~3.6 s de espera) | 9 solicitudes (~3.6 s de espera) (igual en las tres) |
| 5 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, acierto | tiempo | 1.1 µs | 0.99 µs | 1.92 µs | **1.1 µs** (mediana) |
| 6 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, fallo | tiempo | 0.64 µs | 0.54 µs | 1.22 µs | **0.64 µs** (mediana) |
| 7 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 25 fichas, acierto (descartada) | tiempo | 0.2 µs | 0.2 µs | 0.45 µs | **0.2 µs** (mediana) |
| 8 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, acierto | tiempo | 3.07 µs | 3.05 µs | 7.29 µs | **3.07 µs** (mediana) |
| 9 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, fallo | tiempo | 2.13 µs | 1.85 µs | 4.2 µs | **2.13 µs** (mediana) |
| 10 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 100 fichas, acierto (descartada) | tiempo | 0.23 µs | 0.2 µs | 0.48 µs | **0.23 µs** (mediana) |
| 11 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, acierto | tiempo | 31.65 µs | 33.93 µs | 37.62 µs | **33.93 µs** (mediana) |
| 12 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, fallo | tiempo | 19.53 µs | 18.64 µs | 21.42 µs | **19.53 µs** (mediana) |
| 13 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 1000 fichas, acierto (descartada) | tiempo | 0.23 µs | 0.44 µs | 0.27 µs | **0.27 µs** (mediana) |
| 14 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, acierto | tiempo | 169.92 µs | 179.5 µs | 172.4 µs | **172.4 µs** (mediana) |
| 15 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, fallo | tiempo | 97.55 µs | 97.19 µs | 97.48 µs | **97.48 µs** (mediana) |
| 16 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 5000 fichas, acierto (descartada) | tiempo | 0.33 µs | 0.36 µs | 0.29 µs | **0.33 µs** (mediana) |
| 17 | 3. Recuperar una ficha liberada desde disco | catálogo con 25 fichas | tiempo | 0.111 ms por lectura (una solicitud real: ~400 ms) | 0.09 ms por lectura (una solicitud real: ~400 ms) | 0.092 ms por lectura (una solicitud real: ~400 ms) | **0.092 ms por lectura (una solicitud real: ~400 ms)** (mediana) |
| 18 | 3. Recuperar una ficha liberada desde disco | catálogo con 200 fichas | tiempo | 0.167 ms por lectura (una solicitud real: ~400 ms) | 0.154 ms por lectura (una solicitud real: ~400 ms) | 0.168 ms por lectura (una solicitud real: ~400 ms) | **0.167 ms por lectura (una solicitud real: ~400 ms)** (mediana) |
| 19 | 3. Recuperar una ficha liberada desde disco | catálogo con 1000 fichas | tiempo | 0.42 ms por lectura (una solicitud real: ~400 ms) | 0.441 ms por lectura (una solicitud real: ~400 ms) | 0.419 ms por lectura (una solicitud real: ~400 ms) | **0.42 ms por lectura (una solicitud real: ~400 ms)** (mediana) |
| 20 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 25 fichas | tiempo | 2.363 ms | 2.216 ms | 1.995 ms | **2.216 ms** (mediana) |
| 21 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 200 fichas | tiempo | 9.482 ms | 11.131 ms | 9.649 ms | **9.649 ms** (mediana) |
| 22 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 1000 fichas | tiempo | 10.829 ms | 10.84 ms | 10.116 ms | **10.829 ms** (mediana) |
| 23 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 1 paso | tiempo | 22.6 µs | 18.4 µs | 20.2 µs | **20.2 µs** (mediana) |
| 24 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 2 pasos | tiempo | 48.6 µs | 48.6 µs | 50.3 µs | **48.6 µs** (mediana) |
| 25 | 5. Planear la vecindad en una cripta de 1000 salas | precargar_vecinas cuando no hace falta nada | tiempo | 30.9 µs | 27.7 µs | 30.6 µs | **30.6 µs** (mediana) |
| 26 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad    5 | cuenta | 82 aciertos / 938 fallos (8.0 %) 19 solicitudes de red | 82 aciertos / 938 fallos (8.0 %) 19 solicitudes de red | 82 aciertos / 938 fallos (8.0 %) 19 solicitudes de red | 82 aciertos / 938 fallos (8.0 %) 19 solicitudes de red (igual en las tres) |
| 27 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   10 | cuenta | 316 aciertos / 704 fallos (31.0 %) 19 solicitudes de red | 316 aciertos / 704 fallos (31.0 %) 19 solicitudes de red | 316 aciertos / 704 fallos (31.0 %) 19 solicitudes de red | 316 aciertos / 704 fallos (31.0 %) 19 solicitudes de red (igual en las tres) |
| 28 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   25 | cuenta | 487 aciertos / 533 fallos (47.7 %) 19 solicitudes de red | 487 aciertos / 533 fallos (47.7 %) 19 solicitudes de red | 487 aciertos / 533 fallos (47.7 %) 19 solicitudes de red | 487 aciertos / 533 fallos (47.7 %) 19 solicitudes de red (igual en las tres) |
| 29 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad  100 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red (igual en las tres) |
| 30 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad 1000 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red (igual en las tres) |

### Bloque `guardado`

| # | Sección | Medición | Tipo | M0-1 | M0-2 | M0-3 | Antes (M0) |
|---|---|---|---|---|---|---|---|
| G1 | §4.10 | verificación: cargar el binario devuelve exactamente el estado guardado | cuenta | OK | OK | OK | OK (igual en las tres) |
| G2 | §4.10 | verificación: un archivo de otra versión del formato se rechaza | cuenta | OK | OK | OK | OK (igual en las tres) |
| G3 | §4.10 | 10 salas  tamaño en disco  [binario] | cuenta | 12,581 bytes | 12,581 bytes | 12,581 bytes | 12,581 bytes (igual en las tres) |
| G4 | §4.10 | 10 salas  tamaño en disco  [JSON] | cuenta | 28,678 bytes  (2.28× el binario) | 28,678 bytes  (2.28× el binario) | 28,678 bytes  (2.28× el binario) | 28,678 bytes  (2.28× el binario) (igual en las tres) |
| G5 | §4.10 | 10 salas  guardar la partida completa  [binario] | tiempo | 1.71 ms | 1.67 ms | 1.71 ms | **1.71 ms** (mediana) |
| G6 | §4.10 | 10 salas  guardar la partida completa  [JSON] | tiempo | 924.8 µs | 789.9 µs | 833.0 µs | **833.0 µs** (mediana) |
| G7 | §4.10 | 10 salas  cargar la partida completa   [binario → DTO] | tiempo | 2.10 ms | 2.17 ms | 1.89 ms | **2.10 ms** (mediana) |
| G8 | §4.10 | 10 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 300.9 µs | 497.7 µs | 279.6 µs | **300.9 µs** (mediana) |
| G9 | §4.10 | 10 salas  cargar UNA sala (la 6)    [binario, acceso directo] | tiempo | 74.0 µs | 76.1 µs | 66.4 µs | **74.0 µs** (mediana) |
| G10 | §4.10 | 10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo] | tiempo | 282.2 µs | 278.2 µs | 257.5 µs | **278.2 µs** (mediana) |
| G11 | §4.10 | 100 salas  tamaño en disco  [binario] | cuenta | 47,943 bytes | 47,943 bytes | 47,943 bytes | 47,943 bytes (igual en las tres) |
| G12 | §4.10 | 100 salas  tamaño en disco  [JSON] | cuenta | 134,896 bytes  (2.81× el binario) | 134,896 bytes  (2.81× el binario) | 134,896 bytes  (2.81× el binario) | 134,896 bytes  (2.81× el binario) (igual en las tres) |
| G13 | §4.10 | 100 salas  guardar la partida completa  [binario] | tiempo | 5.27 ms | 4.82 ms | 4.97 ms | **4.97 ms** (mediana) |
| G14 | §4.10 | 100 salas  guardar la partida completa  [JSON] | tiempo | 3.40 ms | 3.31 ms | 3.10 ms | **3.31 ms** (mediana) |
| G15 | §4.10 | 100 salas  cargar la partida completa   [binario → DTO] | tiempo | 7.23 ms | 6.89 ms | 6.94 ms | **6.94 ms** (mediana) |
| G16 | §4.10 | 100 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 1.14 ms | 1.21 ms | 1.16 ms | **1.16 ms** (mediana) |
| G17 | §4.10 | 100 salas  cargar UNA sala (la 51)    [binario, acceso directo] | tiempo | 75.6 µs | 75.4 µs | 75.6 µs | **75.6 µs** (mediana) |
| G18 | §4.10 | 100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo] | tiempo | 1.11 ms | 1.22 ms | 1.15 ms | **1.15 ms** (mediana) |
| G19 | §4.10 | 1000 salas  tamaño en disco  [binario] | cuenta | 412,440 bytes | 412,440 bytes | 412,440 bytes | 412,440 bytes (igual en las tres) |
| G20 | §4.10 | 1000 salas  tamaño en disco  [JSON] | cuenta | 1,213,097 bytes  (2.94× el binario) | 1,213,097 bytes  (2.94× el binario) | 1,213,097 bytes  (2.94× el binario) | 1,213,097 bytes  (2.94× el binario) (igual en las tres) |
| G21 | §4.10 | 1000 salas  guardar la partida completa  [binario] | tiempo | 34.94 ms | 36.23 ms | 36.84 ms | **36.23 ms** (mediana) |
| G22 | §4.10 | 1000 salas  guardar la partida completa  [JSON] | tiempo | 28.83 ms | 27.59 ms | 29.57 ms | **28.83 ms** (mediana) |
| G23 | §4.10 | 1000 salas  cargar la partida completa   [binario → DTO] | tiempo | 54.74 ms | 60.94 ms | 60.48 ms | **60.48 ms** (mediana) |
| G24 | §4.10 | 1000 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 9.80 ms | 10.19 ms | 9.26 ms | **9.80 ms** (mediana) |
| G25 | §4.10 | 1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] | tiempo | 240.4 µs | 83.6 µs | 83.4 µs | **83.6 µs** (mediana) |
| G26 | §4.10 | 1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] | tiempo | 9.46 ms | 9.96 ms | 8.84 ms | **9.46 ms** (mediana) |
| G27 | §4.10 | (nota de la salida) El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. | nota | — | — | — | — |

## Detalle de M1: las tres ejecuciones


### Bloque `cache`

| # | Sección | Medición | Tipo | M1-1 | M1-2 | M1-3 | Carga (M1) |
|---|---|---|---|---|---|---|---|
| 1 | 1. Solicitudes al recorrer un pasillo de 60 salas | sala por sala (sin precarga) | cuenta | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador (igual en las tres) |
| 2 | 1. Solicitudes al recorrer un pasillo de 60 salas | actual + vecinas en cada paso (prof. 2) | cuenta | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador (igual en las tres) |
| 3 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, prof. 2 | cuenta | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador (igual en las tres) |
| 4 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, por defecto (lote de 10) | cuenta | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador (igual en las tres) |
| 5 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, acierto | tiempo | 0.99 µs | 1.05 µs | 1.12 µs | **1.05 µs** (mediana) |
| 6 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, fallo | tiempo | 0.51 µs | 0.55 µs | 0.65 µs | **0.55 µs** (mediana) |
| 7 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 25 fichas, acierto (descartada) | tiempo | 0.2 µs | 0.2 µs | 0.23 µs | **0.2 µs** (mediana) |
| 8 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, acierto | tiempo | 3.11 µs | 3.09 µs | 3.1 µs | **3.1 µs** (mediana) |
| 9 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, fallo | tiempo | 1.87 µs | 1.96 µs | 2.01 µs | **1.96 µs** (mediana) |
| 10 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 100 fichas, acierto (descartada) | tiempo | 0.23 µs | 0.19 µs | 0.21 µs | **0.21 µs** (mediana) |
| 11 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, acierto | tiempo | 28.47 µs | 30.34 µs | 30.15 µs | **30.15 µs** (mediana) |
| 12 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, fallo | tiempo | 19.79 µs | 17.76 µs | 18.17 µs | **18.17 µs** (mediana) |
| 13 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 1000 fichas, acierto (descartada) | tiempo | 0.25 µs | 0.28 µs | 0.26 µs | **0.26 µs** (mediana) |
| 14 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, acierto | tiempo | 164.24 µs | 173.42 µs | 174.69 µs | **173.42 µs** (mediana) |
| 15 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, fallo | tiempo | 89.79 µs | 96.81 µs | 103.96 µs | **96.81 µs** (mediana) |
| 16 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 5000 fichas, acierto (descartada) | tiempo | 0.32 µs | 0.36 µs | 0.33 µs | **0.33 µs** (mediana) |
| 17 | 3. Recuperar una ficha liberada desde disco | catálogo con 25 fichas | tiempo | 0.075 ms por lectura (una solicitud real: ~400 ms) | 0.071 ms por lectura (una solicitud real: ~400 ms) | 0.07 ms por lectura (una solicitud real: ~400 ms) | **0.071 ms por lectura (una solicitud real: ~400 ms)** (mediana) |
| 18 | 3. Recuperar una ficha liberada desde disco | catálogo con 200 fichas | tiempo | 0.154 ms por lectura (una solicitud real: ~400 ms) | 0.137 ms por lectura (una solicitud real: ~400 ms) | 0.149 ms por lectura (una solicitud real: ~400 ms) | **0.149 ms por lectura (una solicitud real: ~400 ms)** (mediana) |
| 19 | 3. Recuperar una ficha liberada desde disco | catálogo con 1000 fichas | tiempo | 0.454 ms por lectura (una solicitud real: ~400 ms) | 0.384 ms por lectura (una solicitud real: ~400 ms) | 0.426 ms por lectura (una solicitud real: ~400 ms) | **0.426 ms por lectura (una solicitud real: ~400 ms)** (mediana) |
| 20 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 25 fichas | tiempo | 2.441 ms | 2.165 ms | 2.132 ms | **2.165 ms** (mediana) |
| 21 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 200 fichas | tiempo | 8.709 ms | 9.504 ms | 8.72 ms | **8.72 ms** (mediana) |
| 22 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 1000 fichas | tiempo | 8.499 ms | 8.77 ms | 9.789 ms | **8.77 ms** (mediana) |
| 23 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 1 paso | tiempo | 19.2 µs | 20.4 µs | 18.6 µs | **19.2 µs** (mediana) |
| 24 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 2 pasos | tiempo | 44.4 µs | 49.2 µs | 45.0 µs | **45.0 µs** (mediana) |
| 25 | 5. Planear la vecindad en una cripta de 1000 salas | precargar_vecinas cuando no hace falta nada | tiempo | 27.2 µs | 27.1 µs | 27.5 µs | **27.2 µs** (mediana) |
| 26 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad    5 | cuenta | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 27 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   10 | cuenta | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 28 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   25 | cuenta | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 29 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad  100 | cuenta | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 30 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad 1000 | cuenta | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 31 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 25 fichas, acierto (descartada) | tiempo | 0.73 µs | 0.69 µs | 0.7 µs | **0.7 µs** (mediana) |
| 32 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 100 fichas, acierto (descartada) | tiempo | 2.22 µs | 2.18 µs | 2.13 µs | **2.18 µs** (mediana) |
| 33 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 1000 fichas, acierto (descartada) | tiempo | 20.82 µs | 19.12 µs | 21.07 µs | **20.82 µs** (mediana) |
| 34 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 5000 fichas, acierto (descartada) | tiempo | 96.78 µs | 96.21 µs | 100.53 µs | **96.78 µs** (mediana) |

### Bloque `guardado`

| # | Sección | Medición | Tipo | M1-1 | M1-2 | M1-3 | Carga (M1) |
|---|---|---|---|---|---|---|---|
| G1 | §4.10 | verificación: cargar el binario devuelve exactamente el estado guardado | cuenta | OK | OK | OK | OK (igual en las tres) |
| G2 | §4.10 | verificación: un archivo de otra versión del formato se rechaza | cuenta | OK | OK | OK | OK (igual en las tres) |
| G3 | §4.10 | 10 salas  tamaño en disco  [binario] | cuenta | 12,414 bytes | 12,414 bytes | 12,414 bytes | 12,414 bytes (igual en las tres) |
| G4 | §4.10 | 10 salas  tamaño en disco  [JSON] | cuenta | 28,363 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) (igual en las tres) |
| G5 | §4.10 | 10 salas  guardar la partida completa  [binario] | tiempo | 2.00 ms | 1.61 ms | 1.70 ms | **1.70 ms** (mediana) |
| G6 | §4.10 | 10 salas  guardar la partida completa  [JSON] | tiempo | 876.3 µs | 804.6 µs | 773.6 µs | **804.6 µs** (mediana) |
| G7 | §4.10 | 10 salas  cargar la partida completa   [binario → DTO] | tiempo | 2.14 ms | 2.43 ms | 2.54 ms | **2.43 ms** (mediana) |
| G8 | §4.10 | 10 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 279.7 µs | 286.7 µs | 328.6 µs | **286.7 µs** (mediana) |
| G9 | §4.10 | 10 salas  cargar UNA sala (la 6)    [binario, acceso directo] | tiempo | 73.6 µs | 70.6 µs | 74.8 µs | **73.6 µs** (mediana) |
| G10 | §4.10 | 10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo] | tiempo | 289.5 µs | 279.8 µs | 355.8 µs | **289.5 µs** (mediana) |
| G11 | §4.10 | 100 salas  tamaño en disco  [binario] | cuenta | 46,646 bytes | 46,646 bytes | 46,646 bytes | 46,646 bytes (igual en las tres) |
| G12 | §4.10 | 100 salas  tamaño en disco  [JSON] | cuenta | 133,318 bytes  (2.86× el binario) | 133,318 bytes  (2.86× el binario) | 133,318 bytes  (2.86× el binario) | 133,318 bytes  (2.86× el binario) (igual en las tres) |
| G13 | §4.10 | 100 salas  guardar la partida completa  [binario] | tiempo | 5.00 ms | 4.78 ms | 5.11 ms | **5.00 ms** (mediana) |
| G14 | §4.10 | 100 salas  guardar la partida completa  [JSON] | tiempo | 3.31 ms | 3.05 ms | 4.20 ms | **3.31 ms** (mediana) |
| G15 | §4.10 | 100 salas  cargar la partida completa   [binario → DTO] | tiempo | 7.02 ms | 7.02 ms | 6.65 ms | **7.02 ms** (mediana) |
| G16 | §4.10 | 100 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 1.14 ms | 1.10 ms | 1.12 ms | **1.12 ms** (mediana) |
| G17 | §4.10 | 100 salas  cargar UNA sala (la 51)    [binario, acceso directo] | tiempo | 77.1 µs | 65.5 µs | 75.7 µs | **75.7 µs** (mediana) |
| G18 | §4.10 | 100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo] | tiempo | 1.10 ms | 1.04 ms | 1.10 ms | **1.10 ms** (mediana) |
| G19 | §4.10 | 1000 salas  tamaño en disco  [binario] | cuenta | 400,347 bytes | 400,347 bytes | 400,347 bytes | 400,347 bytes (igual en las tres) |
| G20 | §4.10 | 1000 salas  tamaño en disco  [JSON] | cuenta | 1,199,809 bytes  (3.00× el binario) | 1,199,809 bytes  (3.00× el binario) | 1,199,809 bytes  (3.00× el binario) | 1,199,809 bytes  (3.00× el binario) (igual en las tres) |
| G21 | §4.10 | 1000 salas  guardar la partida completa  [binario] | tiempo | 36.45 ms | 38.03 ms | 36.70 ms | **36.70 ms** (mediana) |
| G22 | §4.10 | 1000 salas  guardar la partida completa  [JSON] | tiempo | 28.10 ms | 28.94 ms | 29.04 ms | **28.94 ms** (mediana) |
| G23 | §4.10 | 1000 salas  cargar la partida completa   [binario → DTO] | tiempo | 59.03 ms | 64.02 ms | 58.25 ms | **59.03 ms** (mediana) |
| G24 | §4.10 | 1000 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 8.77 ms | 9.56 ms | 9.68 ms | **9.56 ms** (mediana) |
| G25 | §4.10 | 1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] | tiempo | 71.1 µs | 75.3 µs | 82.7 µs | **75.3 µs** (mediana) |
| G26 | §4.10 | 1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] | tiempo | 9.52 ms | 10.07 ms | 9.69 ms | **9.69 ms** (mediana) |
| G27 | §4.10 | (nota de la salida) El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. | nota | — | — | — | — |
| G28 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla (igual en las tres) |
| G29 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la del medio, la 6) | cuenta | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla (igual en las tres) |
| G30 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la última, la 10) | cuenta | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | 262 bytes de 12,414 del archivo; 4 entradas de la tabla (igual en las tres) |
| G31 | §4.10 | 10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | 77.8 µs | 95.5 µs | 79.1 µs | **79.1 µs** (mediana) |
| G32 | §4.10 | 10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] | tiempo | 75.0 µs | 83.4 µs | 74.4 µs | **75.0 µs** (mediana) |
| G33 | §4.10 | verificación: 10 salas: leer UNA sala lee menos bytes que el archivo | cuenta | OK | OK | OK | OK (igual en las tres) |
| G34 | §4.10 | verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4 | cuenta | OK | OK | OK | OK (igual en las tres) |
| G35 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | 299 bytes de 46,646 del archivo; 6 entradas de la tabla (igual en las tres) |
| G36 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) | cuenta | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | 304 bytes de 46,646 del archivo; 6 entradas de la tabla (igual en las tres) |
| G37 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la última, la 100) | cuenta | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | 334 bytes de 46,646 del archivo; 7 entradas de la tabla (igual en las tres) |
| G38 | §4.10 | 100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | 85.8 µs | 74.7 µs | 85.5 µs | **85.5 µs** (mediana) |
| G39 | §4.10 | 100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] | tiempo | 75.4 µs | 64.9 µs | 75.8 µs | **75.4 µs** (mediana) |
| G40 | §4.10 | verificación: 100 salas: leer UNA sala lee menos bytes que el archivo | cuenta | OK | OK | OK | OK (igual en las tres) |
| G41 | §4.10 | verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7 | cuenta | OK | OK | OK | OK (igual en las tres) |
| G42 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | 359 bytes de 400,347 del archivo; 9 entradas de la tabla (igual en las tres) |
| G43 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) | cuenta | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | 374 bytes de 400,347 del archivo; 9 entradas de la tabla (igual en las tres) |
| G44 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la última, la 1000) | cuenta | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | 397 bytes de 400,347 del archivo; 10 entradas de la tabla (igual en las tres) |
| G45 | §4.10 | 1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | 103.2 µs | 97.9 µs | 97.9 µs | **97.9 µs** (mediana) |
| G46 | §4.10 | 1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] | tiempo | 74.3 µs | 83.0 µs | 80.6 µs | **80.6 µs** (mediana) |
| G47 | §4.10 | verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo | cuenta | OK | OK | OK | OK (igual en las tres) |
| G48 | §4.10 | verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 | cuenta | OK | OK | OK | OK (igual en las tres) |

## Detalle de M2: las tres ejecuciones


### Bloque `cache`

| # | Sección | Medición | Tipo | M2-1 | M2-2 | M2-3 | Después (M2) |
|---|---|---|---|---|---|---|---|
| 1 | 1. Solicitudes al recorrer un pasillo de 60 salas | sala por sala (sin precarga) | cuenta | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador (igual en las tres) |
| 2 | 1. Solicitudes al recorrer un pasillo de 60 salas | actual + vecinas en cada paso (prof. 2) | cuenta | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador (igual en las tres) |
| 3 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, prof. 2 | cuenta | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador (igual en las tres) |
| 4 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, por defecto (lote de 10) | cuenta | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador (igual en las tres) |
| 5 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 25 fichas, acierto | tiempo | 0.7 µs | 0.85 µs | 0.8 µs | 0.8 µs (mediana) |
| 6 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 25 fichas, fallo | tiempo | 0.6 µs | 0.66 µs | 0.57 µs | 0.6 µs (mediana) |
| 7 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 25 fichas, acierto (descartada) | tiempo | 0.2 µs | 0.24 µs | 0.19 µs | 0.2 µs (mediana) |
| 8 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 100 fichas, acierto | tiempo | 1.98 µs | 2.25 µs | 2.71 µs | 2.25 µs (mediana) |
| 9 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 100 fichas, fallo | tiempo | 1.91 µs | 2.18 µs | 2.14 µs | 2.14 µs (mediana) |
| 10 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 100 fichas, acierto (descartada) | tiempo | 0.22 µs | 0.23 µs | 0.2 µs | 0.22 µs (mediana) |
| 11 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 1000 fichas, acierto | tiempo | 18.46 µs | 20.26 µs | 18.14 µs | 18.46 µs (mediana) |
| 12 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 1000 fichas, fallo | tiempo | 18.29 µs | 20.16 µs | 19.12 µs | 19.12 µs (mediana) |
| 13 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 1000 fichas, acierto (descartada) | tiempo | 0.24 µs | 0.28 µs | 0.26 µs | 0.26 µs (mediana) |
| 14 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 5000 fichas, acierto | tiempo | 104.45 µs | 116.68 µs | 107.81 µs | 107.81 µs (mediana) |
| 15 | 2. Búsqueda en la caché (µs por operación) | lista propia lineal, 5000 fichas, fallo | tiempo | 95.16 µs | 101.23 µs | 96.46 µs | 96.46 µs (mediana) |
| 16 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 5000 fichas, acierto (descartada) | tiempo | 0.31 µs | 0.3 µs | 0.29 µs | 0.3 µs (mediana) |
| 17 | 3. Recuperar una ficha liberada desde disco | catálogo con 25 fichas | tiempo | 0.071 ms por lectura (una solicitud real: ~400 ms) | 0.071 ms por lectura (una solicitud real: ~400 ms) | 0.073 ms por lectura (una solicitud real: ~400 ms) | 0.071 ms por lectura (una solicitud real: ~400 ms) (mediana) |
| 18 | 3. Recuperar una ficha liberada desde disco | catálogo con 200 fichas | tiempo | 0.178 ms por lectura (una solicitud real: ~400 ms) | 0.277 ms por lectura (una solicitud real: ~400 ms) | 0.167 ms por lectura (una solicitud real: ~400 ms) | 0.178 ms por lectura (una solicitud real: ~400 ms) (mediana) |
| 19 | 3. Recuperar una ficha liberada desde disco | catálogo con 1000 fichas | tiempo | 0.456 ms por lectura (una solicitud real: ~400 ms) | 0.437 ms por lectura (una solicitud real: ~400 ms) | 0.436 ms por lectura (una solicitud real: ~400 ms) | 0.437 ms por lectura (una solicitud real: ~400 ms) (mediana) |
| 20 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 25 fichas | tiempo | 3.319 ms | 2.087 ms | 2.331 ms | 2.331 ms (mediana) |
| 21 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 200 fichas | tiempo | 9.793 ms | 9.975 ms | 9.941 ms | 9.941 ms (mediana) |
| 22 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 1000 fichas | tiempo | 11.038 ms | 10.758 ms | 10.459 ms | 10.758 ms (mediana) |
| 23 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 1 paso | tiempo | 17.6 µs | 20.0 µs | 18.6 µs | 18.6 µs (mediana) |
| 24 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 2 pasos | tiempo | 44.2 µs | 54.5 µs | 46.6 µs | 46.6 µs (mediana) |
| 25 | 5. Planear la vecindad en una cripta de 1000 salas | precargar_vecinas cuando no hace falta nada | tiempo | 27.4 µs | 31.8 µs | 27.0 µs | 27.4 µs (mediana) |
| 26 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad    5 | cuenta | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 27 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   10 | cuenta | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 28 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   25 | cuenta | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 29 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad  100 | cuenta | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 30 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad 1000 | cuenta | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) |
| 31 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 25 fichas, acierto (descartada) | tiempo | 0.72 µs | 0.71 µs | 0.83 µs | 0.72 µs (mediana) |
| 32 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 100 fichas, acierto (descartada) | tiempo | 2.17 µs | 2.08 µs | 3.83 µs | 2.17 µs (mediana) |
| 33 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 1000 fichas, acierto (descartada) | tiempo | 18.94 µs | 20.98 µs | 23.61 µs | 20.98 µs (mediana) |
| 34 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 5000 fichas, acierto (descartada) | tiempo | 108.04 µs | 103.79 µs | 109.43 µs | 108.04 µs (mediana) |

### Bloque `guardado`

| # | Sección | Medición | Tipo | M2-1 | M2-2 | M2-3 | Después (M2) |
|---|---|---|---|---|---|---|---|
| G1 | §4.10 | verificación: cargar el binario devuelve exactamente el estado guardado | cuenta | OK | OK | OK | OK (igual en las tres) |
| G2 | §4.10 | verificación: un archivo de otra versión del formato se rechaza | cuenta | OK | OK | OK | OK (igual en las tres) |
| G3 | §4.10 | 10 salas  tamaño en disco  [binario] | cuenta | 12,414 bytes | 12,414 bytes | 12,414 bytes | 12,414 bytes (igual en las tres) |
| G4 | §4.10 | 10 salas  tamaño en disco  [JSON] | cuenta | 28,363 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) | 28,363 bytes  (2.28× el binario) (igual en las tres) |
| G5 | §4.10 | 10 salas  guardar la partida completa  [binario] | tiempo | 1.87 ms | 1.96 ms | 1.70 ms | 1.87 ms (mediana) |
| G6 | §4.10 | 10 salas  guardar la partida completa  [JSON] | tiempo | 825.5 µs | 880.9 µs | 799.1 µs | 825.5 µs (mediana) |
| G7 | §4.10 | 10 salas  cargar la partida completa   [binario → DTO] | tiempo | 2.27 ms | 1.90 ms | 2.02 ms | 2.02 ms (mediana) |
| G8 | §4.10 | 10 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 316.1 µs | 289.7 µs | 277.9 µs | 289.7 µs (mediana) |
| G9 | §4.10 | 10 salas  cargar UNA sala (la 6)    [binario, acceso directo] | tiempo | 73.5 µs | 74.6 µs | 65.3 µs | 73.5 µs (mediana) |
| G10 | §4.10 | 10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo] | tiempo | 279.5 µs | 276.9 µs | 265.3 µs | 276.9 µs (mediana) |
| G11 | §4.10 | 100 salas  tamaño en disco  [binario] | cuenta | 46,646 bytes | 46,646 bytes | 46,646 bytes | 46,646 bytes (igual en las tres) |
| G12 | §4.10 | 100 salas  tamaño en disco  [JSON] | cuenta | 133,318 bytes  (2.86× el binario) | 133,318 bytes  (2.86× el binario) | 133,318 bytes  (2.86× el binario) | 133,318 bytes  (2.86× el binario) (igual en las tres) |
| G13 | §4.10 | 100 salas  guardar la partida completa  [binario] | tiempo | 4.87 ms | 4.56 ms | 4.56 ms | 4.56 ms (mediana) |
| G14 | §4.10 | 100 salas  guardar la partida completa  [JSON] | tiempo | 3.40 ms | 2.96 ms | 3.56 ms | 3.40 ms (mediana) |
| G15 | §4.10 | 100 salas  cargar la partida completa   [binario → DTO] | tiempo | 7.51 ms | 6.71 ms | 6.24 ms | 6.71 ms (mediana) |
| G16 | §4.10 | 100 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 1.22 ms | 1.12 ms | 1.11 ms | 1.12 ms (mediana) |
| G17 | §4.10 | 100 salas  cargar UNA sala (la 51)    [binario, acceso directo] | tiempo | 78.7 µs | 76.1 µs | 66.0 µs | 76.1 µs (mediana) |
| G18 | §4.10 | 100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo] | tiempo | 1.13 ms | 1.21 ms | 1.09 ms | 1.13 ms (mediana) |
| G19 | §4.10 | 1000 salas  tamaño en disco  [binario] | cuenta | 400,347 bytes | 400,347 bytes | 400,347 bytes | 400,347 bytes (igual en las tres) |
| G20 | §4.10 | 1000 salas  tamaño en disco  [JSON] | cuenta | 1,199,809 bytes  (3.00× el binario) | 1,199,809 bytes  (3.00× el binario) | 1,199,809 bytes  (3.00× el binario) | 1,199,809 bytes  (3.00× el binario) (igual en las tres) |
| G21 | §4.10 | 1000 salas  guardar la partida completa  [binario] | tiempo | 37.19 ms | 35.98 ms | 34.93 ms | 35.98 ms (mediana) |
| G22 | §4.10 | 1000 salas  guardar la partida completa  [JSON] | tiempo | 40.78 ms | 27.61 ms | 29.75 ms | 29.75 ms (mediana) |
| G23 | §4.10 | 1000 salas  cargar la partida completa   [binario → DTO] | tiempo | 59.97 ms | 55.73 ms | 57.61 ms | 57.61 ms (mediana) |
| G24 | §4.10 | 1000 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | 10.70 ms | 11.31 ms | 9.44 ms | 10.70 ms (mediana) |
| G25 | §4.10 | 1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] | tiempo | 88.8 µs | 73.3 µs | 81.7 µs | 81.7 µs (mediana) |
| G26 | §4.10 | 1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] | tiempo | 10.13 ms | 10.37 ms | 10.02 ms | 10.13 ms (mediana) |
| G27 | §4.10 | (nota de la salida) El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. | nota | — | — | — | — |
| G28 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla (igual en las tres) |
| G29 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la del medio, la 6) | cuenta | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla | 239 bytes de 12,414 del archivo; 3 entradas de la tabla (igual en las tres) |
| G30 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la última, la 10) | cuenta | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | 262 bytes de 12,414 del archivo; 4 entradas de la tabla | 262 bytes de 12,414 del archivo; 4 entradas de la tabla (igual en las tres) |
| G31 | §4.10 | 10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | 77.2 µs | 78.5 µs | 68.1 µs | 77.2 µs (mediana) |
| G32 | §4.10 | 10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] | tiempo | 72.3 µs | 73.4 µs | 63.5 µs | 72.3 µs (mediana) |
| G33 | §4.10 | verificación: 10 salas: leer UNA sala lee menos bytes que el archivo | cuenta | OK | OK | OK | OK (igual en las tres) |
| G34 | §4.10 | verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4 | cuenta | OK | OK | OK | OK (igual en las tres) |
| G35 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | 299 bytes de 46,646 del archivo; 6 entradas de la tabla | 299 bytes de 46,646 del archivo; 6 entradas de la tabla (igual en las tres) |
| G36 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) | cuenta | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | 304 bytes de 46,646 del archivo; 6 entradas de la tabla | 304 bytes de 46,646 del archivo; 6 entradas de la tabla (igual en las tres) |
| G37 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la última, la 100) | cuenta | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | 334 bytes de 46,646 del archivo; 7 entradas de la tabla | 334 bytes de 46,646 del archivo; 7 entradas de la tabla (igual en las tres) |
| G38 | §4.10 | 100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | 85.5 µs | 86.0 µs | 74.9 µs | 85.5 µs (mediana) |
| G39 | §4.10 | 100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] | tiempo | 77.0 µs | 76.7 µs | 65.3 µs | 76.7 µs (mediana) |
| G40 | §4.10 | verificación: 100 salas: leer UNA sala lee menos bytes que el archivo | cuenta | OK | OK | OK | OK (igual en las tres) |
| G41 | §4.10 | verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7 | cuenta | OK | OK | OK | OK (igual en las tres) |
| G42 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | 359 bytes de 400,347 del archivo; 9 entradas de la tabla | 359 bytes de 400,347 del archivo; 9 entradas de la tabla (igual en las tres) |
| G43 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) | cuenta | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | 374 bytes de 400,347 del archivo; 9 entradas de la tabla | 374 bytes de 400,347 del archivo; 9 entradas de la tabla (igual en las tres) |
| G44 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la última, la 1000) | cuenta | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | 397 bytes de 400,347 del archivo; 10 entradas de la tabla | 397 bytes de 400,347 del archivo; 10 entradas de la tabla (igual en las tres) |
| G45 | §4.10 | 1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | 99.0 µs | 84.3 µs | 95.4 µs | 95.4 µs (mediana) |
| G46 | §4.10 | 1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] | tiempo | 81.7 µs | 74.0 µs | 71.7 µs | 74.0 µs (mediana) |
| G47 | §4.10 | verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo | cuenta | OK | OK | OK | OK (igual en las tres) |
| G48 | §4.10 | verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 | cuenta | OK | OK | OK | OK (igual en las tres) |

## Anexo · Inventario de usos prohibidos (T037 a T039)

### T037 · Búsqueda

- Fecha y hora: 2026-11-18 07:24 -0600. Código: `aeb25a0`. Tiene el mismo código de producción y de medición que M2
  (`70c9854`): el commit `aeb25a0` solo agrega documentos. Los comandos son los de [quickstart.md](quickstart.md#inventario),
  ejecutados con Git Bash desde la raíz del repositorio:

```
P="adaptadores Controlador DTO Logica model Servicio main.py"
X="--exclude=bench_red.py --exclude=bench_red_mejorado.py"
grep -rnE "(import|from) +(heapq|bisect|collections|networkx)" $P --include=*.py $X
grep -rnE "sorted\(|\.sort\(" $P --include=*.py $X
grep -rnE "\bset\(|frozenset|\{[^}:]+\}" $P --include=*.py $X
grep -rnE "\bdict\(|= \{\}|: dict\b" $P --include=*.py $X
```

**1. Importaciones** (4 líneas):

```
adaptadores/servicioCripta.py:2:from collections import deque
DTO/SalaDTO.py:4:from collections import deque
Logica/EstadoGuardadoLogica.py:10:from collections import deque
Logica/GestorEventos.py:2:from collections.abc import Callable
```

**2. `sorted(` y `.sort(`** (2 líneas):

```
Logica/IndiceLlaves.py:9:`id_de` y `cantidad` O(1). Sin `bisect`, `sorted()`, `.sort()`, `dict` ni `set`.
Logica/VerificacionResolubilidad.py:25:Sin dict, set, heapq, bisect, collections, sorted() ni .sort() (principio I).
```

**3. `set(`, `frozenset` y conjuntos literales**: 322 líneas. Ninguna es `set(` ni `frozenset`; todas salen del
patrón de conjunto literal `\{[^}:]+\}`. Para separarlas se usó el tokenizador de Python 3.12: se descarta lo que
está entre `FSTRING_START` y `FSTRING_END`, las cadenas y los comentarios, y se vuelve a buscar el patrón en lo que
queda.

- **Criterio «marcador de f-string no cuenta»**: descarta 317 líneas. En todas, el patrón solo aparece dentro de un
  marcador `{x}` de una cadena con prefijo `f`.
- **Criterio «marcador en un comentario no cuenta»**: descarta 1 línea,
  `adaptadores/servicioCripta.py:160: self._datos: dict | None = None  # respuesta cruda de /criptas/{id}`. El `{id}`
  está en el comentario. La línea sí entra en la búsqueda 4 por `: dict`.
- **Quedan 4 líneas con un conjunto literal en el código**:

```
adaptadores/extension.py:20:    separadores = {os.sep, "/", "\\"}
Logica/EstadoJuegoLogica.py:884:        if tipo in {"RECOGER_OBJETO", "USAR_OBJETO"}:
Logica/EstadoJuegoLogica.py:900:        if tipo in {"ARMAR_TRAMPA", "ACTIVAR_TRAMPA"}:
Logica/EstadoJuegoLogica.py:1248:        elif evento.tipo_accion in {"RECOGER_OBJETO", "USAR_OBJETO"} and evento.datos_extra:
```

**4. `dict(`, `= {}` y `: dict`** (18 líneas, las mismas 18 de `0b031ec` que cuenta research D5):

```
adaptadores/AlmacenDisco.py:74:    def guardar_datos(self, cripta_id: str, datos: dict) -> None:
adaptadores/llaves.py:20:def leer_llaves(respuesta: dict) -> list[dict]:
adaptadores/resolucion.py:30:def resolver_objeto(ficha: dict, id_sala: int | None = None) -> Objeto:
adaptadores/resolucion.py:41:    datos = dict(ficha)
adaptadores/resolucion.py:49:def _rango_de(ficha: dict, advertencias: list[str] | None) -> int:
adaptadores/resolucion.py:68:def resolver_ficha_enemigo(ficha: dict, advertencias: list[str] | None = None) -> EnemigoCatalogoDTO:
adaptadores/resolucion.py:72:    datos = dict(ficha)
adaptadores/resolucion.py:80:def resolver_enemigo(colocacion: dict, ficha: EnemigoCatalogoDTO, id_sala: int) -> EnemigoDTO:
adaptadores/resolucion.py:103:def resolver_trampa(colocacion: dict, ficha: dict, id_sala: int) -> Trampa:
adaptadores/resolucion.py:123:def _ids_necesarios(contenido: dict) -> list[str]:
adaptadores/resolucion.py:194:def _armar_sala(contenido: dict, fichas: list[dict], numero_sala: int, advertencias: list[str] | None = None):
adaptadores/servicioCripta.py:46:def _costo_declarado(salida: dict, advertencias: list[str] | None, sala: int, letra: str) -> int | None:
adaptadores/servicioCripta.py:90:        nueva = dict(sala)
adaptadores/servicioCripta.py:93:            salidas_nuevas = {}
adaptadores/servicioCripta.py:115:                copia = dict(salida)
adaptadores/servicioCripta.py:160:        self._datos: dict | None = None              # respuesta cruda de /criptas/{id}
adaptadores/servicioCripta.py:513:    def _ensamblar(self, esqueleto: dict, contenido) -> SalaDTO:
adaptadores/servicioCripta.py:523:    def _armar_salidas(salidas_api: dict | None) -> deque[SalidaDTO]:
```

**Comprobaciones de FR-375**:
- `adaptadores/cache.py` ya no aparece en ninguna de las cuatro búsquedas (D2).
- `adaptadores/servicioCripta.py` aparece en la búsqueda 1 solo por la importación de la línea 2. Esa cola de
  biblioteca solo se usa en `_armar_salidas` (líneas 523, 524 y 528), que es el uso 4, justificado. `salas_vecinas`
  (líneas 391 a 415) no menciona ninguna estructura de la lista (D1).
- La búsqueda 2 solo encuentra dos docstrings que dicen que el archivo **no** usa `sorted()` ni `.sort()`. No son usos.

### T038 · Revisión a mano

**Las 18 apariciones de `dict`**. Ninguna es índice, caché ni tabla de búsqueda. Todas son la respuesta JSON de la
API o una copia con su misma forma (supuesto de la spec). Por eso, con el criterio de FR-386, ninguna pasa a la tabla
del inventario.

| # | Ubicación | Clasificación | Motivo |
|---|---|---|---|
| 1 | `adaptadores/AlmacenDisco.py:74` | lectura de JSON | anotación del parámetro: recibe la respuesta de `/criptas/{id}` y la escribe tal cual en el archivo indexado |
| 2 | `adaptadores/llaves.py:20` | lectura de JSON | anotación: recibe la respuesta de la API de llaves y devuelve su lista `llaves` sin indexarla |
| 3 | `adaptadores/resolucion.py:30` | lectura de JSON | anotación: la ficha cruda del catálogo, que se convierte en un objeto del juego |
| 4 | `adaptadores/resolucion.py:41` | lectura de JSON | `dict(ficha)`: copia de la ficha para renombrar `id` y quitar `clase` antes de construir el objeto. Se descarta al salir |
| 5 | `adaptadores/resolucion.py:49` | lectura de JSON | anotación: lee `comportamiento` y `rango` de la ficha cruda |
| 6 | `adaptadores/resolucion.py:68` | lectura de JSON | anotación: la ficha cruda de un enemigo |
| 7 | `adaptadores/resolucion.py:72` | lectura de JSON | `dict(ficha)`: copia para quitar las claves que el DTO no conoce. Se descarta al construir el DTO |
| 8 | `adaptadores/resolucion.py:80` | lectura de JSON | anotación: la colocación cruda de `/contenido` |
| 9 | `adaptadores/resolucion.py:103` | lectura de JSON | anotación: la colocación y la ficha crudas de una trampa |
| 10 | `adaptadores/resolucion.py:123` | lectura de JSON | anotación: el contenido crudo de una sala. Los ids se juntan en una lista |
| 11 | `adaptadores/resolucion.py:194` | lectura de JSON | anotación: el contenido crudo y la lista de fichas crudas. Las fichas se buscan en la lista, no por clave |
| 12 | `adaptadores/servicioCripta.py:46` | lectura de JSON | anotación: una salida cruda del esqueleto, de la que se lee `costo` |
| 13 | `adaptadores/servicioCripta.py:90` | lectura de JSON | `dict(sala)` en `normalizar_esqueleto`: copia de la sala cruda con la forma de la API (uso 7 de research D5) |
| 14 | `adaptadores/servicioCripta.py:93` | lectura de JSON | `salidas_nuevas = {}`: el objeto `salidas` de la API rearmado con las mismas letras y el costo resuelto (uso 7) |
| 15 | `adaptadores/servicioCripta.py:115` | lectura de JSON | `dict(salida)`: copia de una salida cruda para fijarle el costo (uso 7) |
| 16 | `adaptadores/servicioCripta.py:160` | lectura de JSON | `self._datos`: la respuesta cruda de `/criptas/{id}` de la cripta actual. Si cambia la cripta se reemplaza entera, y nunca se busca por clave dentro |
| 17 | `adaptadores/servicioCripta.py:513` | lectura de JSON | anotación: la sala cruda del esqueleto, que se ensambla en un `SalaDTO` |
| 18 | `adaptadores/servicioCripta.py:523` | lectura de JSON | anotación: el objeto `salidas` de la API, que se recorre en el orden N, S, E, O |

Los usos 7 y 8 de research D5 son las filas 13 a 15 (`normalizar_esqueleto` en `servicioCripta.py`) y las filas 4 y 7
(`resolucion.py:41, 72`) de esta tabla.

**Conjuntos literales** (las 4 líneas que quedan de la búsqueda 3):

| Ubicación | Clasificación | Motivo |
|---|---|---|
| `adaptadores/extension.py:20` | constante de solo lectura (uso 9) | 3 separadores de ruta (4 si existe `os.altsep`) para comprobar que el nombre de archivo no trae carpetas. No guarda datos del juego |
| `Logica/EstadoJuegoLogica.py:884` | constante de solo lectura (uso 10) | 2 tipos de acción para elegir cómo reconstruir un evento del log |
| `Logica/EstadoJuegoLogica.py:900` | constante de solo lectura (uso 10) | 2 tipos de acción, igual que la anterior |
| `Logica/EstadoJuegoLogica.py:1248` | constante de solo lectura (uso 10) | 2 tipos de acción para saber qué id quedó afectado |

**Resultado**: no hay ningún índice ni caché nuevo. Los únicos usos que van a la tabla del inventario son los 10 de
research D5: 2 corregidos (D1 y D2), 6 justificados (3 a 6, 9 y 10) y 2 excluidos por ser lectura de JSON (7 y 8).

### T039 · Usos 9 y 10: se justifican tal cual

No se cambia el código. Los cuatro conjuntos son constantes de 2 o 3 elementos (4 con `os.altsep`), escritas en la
línea donde se usan, y solo sirven para comprobar pertenencia. No guardan datos del juego, no crecen y nadie los
consulta como índice ni como caché. Pasarlos a tuplas costaría cuatro líneas, pero no cambia nada observable ni la
complejidad: con 2 o 3 elementos, comprobar la pertenencia cuesta lo mismo. Además obligaría a repetir T030 sin
ninguna ganancia. En `extension.py:20` habría que armar la tupla de otra forma, porque el conjunto agrega `os.altsep`
con `add`. T030 no se repite.
