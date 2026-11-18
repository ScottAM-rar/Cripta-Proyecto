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

Pendiente (T031): tres ejecuciones de cada bloque con `bench-cache-M2-{1,2,3}.csv` y `bench-guardado-M2-{1,2,3}.csv`.

## Comprobación de las filas de cuenta

- **M0**: las 10 filas de cuenta de `cache` y las 8 de `guardado` son idénticas en las tres ejecuciones.
- **M1**: las 10 filas de cuenta de `cache` y las 26 de `guardado` (8 existentes y 18 nuevas: bytes leídos y verificaciones) son idénticas en las tres ejecuciones.
- **M2** (idénticas en las tres) y **M1 = M2** en las secciones 1 y 6 de `cache`: pendiente (T032).

## Medición manual

Pendiente (T036).

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

**Contra el código revisado**: pendiente (T025, T028 y T030).

## Tabla por bloque

Antes = M0 (mediana en las filas de tiempo). Carga (M1) = mediana de M1 en las filas de tiempo. En las filas nuevas (sin antes en M0) el antes es M1 y el límite es 2 × M1 (FR-377, FR-384). Las columnas de M2, diferencia, cumple y el límite de las demás filas se completan en T033.

### Bloque `cache`

| # | Sección | Medición | Tipo | Antes (M0) | Carga (M1) | Después (M2) | Diferencia | Límite (2×) | Cumple | Causa |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1. Solicitudes al recorrer un pasillo de 60 salas | sala por sala (sin precarga) | cuenta | 63 solicitudes (~25.2 s de espera) (igual en las tres) | 64 solicitudes (~25.6 s de espera); de ellas, 45 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +1 solicitudes; +1 consulta de llaves y 45 disparadas por cazadores (activos desde el inicio, peor caso), que además adelantan salas que el jugador ya no pide |
| 2 | 1. Solicitudes al recorrer un pasillo de 60 salas | actual + vecinas en cada paso (prof. 2) | cuenta | 61 solicitudes (~24.4 s de espera) (igual en las tres) | 62 solicitudes (~24.8 s de espera); de ellas, 44 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +1 solicitudes; +1 consulta de llaves y 44 disparadas por cazadores (activos desde el inicio, peor caso), que además adelantan salas que el jugador ya no pide |
| 3 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, prof. 2 | cuenta | 33 solicitudes (~13.2 s de espera) (igual en las tres) | 56 solicitudes (~22.4 s de espera); de ellas, 44 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +23 solicitudes; +1 consulta de llaves y 44 disparadas por cazadores (activos desde el inicio, peor caso), que además adelantan salas que el jugador ya no pide |
| 4 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, por defecto (lote de 10) | cuenta | 9 solicitudes (~3.6 s de espera) (igual en las tres) | 46 solicitudes (~18.4 s de espera); de ellas, 39 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +37 solicitudes; +1 consulta de llaves y 39 disparadas por cazadores (activos desde el inicio, peor caso), que además adelantan salas que el jugador ya no pide |
| 5 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, acierto | tiempo | **1.1 µs** (mediana) | **1.05 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 6 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, fallo | tiempo | **0.64 µs** (mediana) | **0.55 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 7 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 25 fichas, acierto (descartada) | tiempo | **0.2 µs** (mediana) | **0.2 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 8 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, acierto | tiempo | **3.07 µs** (mediana) | **3.1 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 9 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, fallo | tiempo | **2.13 µs** (mediana) | **1.96 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 10 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 100 fichas, acierto (descartada) | tiempo | **0.23 µs** (mediana) | **0.21 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 11 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, acierto | tiempo | **33.93 µs** (mediana) | **30.15 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 12 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, fallo | tiempo | **19.53 µs** (mediana) | **18.17 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 13 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 1000 fichas, acierto (descartada) | tiempo | **0.27 µs** (mediana) | **0.26 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 14 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, acierto | tiempo | **172.4 µs** (mediana) | **173.42 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 15 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, fallo | tiempo | **97.48 µs** (mediana) | **96.81 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 16 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 5000 fichas, acierto (descartada) | tiempo | **0.33 µs** (mediana) | **0.33 µs** (mediana) | — | — | — | — | sin carga (operación aislada); la diferencia depende de la máquina |
| 17 | 3. Recuperar una ficha liberada desde disco | catálogo con 25 fichas | tiempo | **0.092 ms por lectura (una solicitud real: ~400 ms)** (mediana) | **0.071 ms por lectura (una solicitud real: ~400 ms)** (mediana) | — | — | — | — | carga: la ficha que se lee es de cazador; la diferencia depende de la máquina |
| 18 | 3. Recuperar una ficha liberada desde disco | catálogo con 200 fichas | tiempo | **0.167 ms por lectura (una solicitud real: ~400 ms)** (mediana) | **0.149 ms por lectura (una solicitud real: ~400 ms)** (mediana) | — | — | — | — | carga: la ficha que se lee es de cazador; la diferencia depende de la máquina |
| 19 | 3. Recuperar una ficha liberada desde disco | catálogo con 1000 fichas | tiempo | **0.42 ms por lectura (una solicitud real: ~400 ms)** (mediana) | **0.426 ms por lectura (una solicitud real: ~400 ms)** (mediana) | — | — | — | — | carga: la ficha que se lee es de cazador; la diferencia depende de la máquina |
| 20 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 25 fichas | tiempo | **2.216 ms** (mediana) | **2.165 ms** (mediana) | — | — | — | — | sin carga en esta sección; la diferencia depende de la máquina |
| 21 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 200 fichas | tiempo | **9.649 ms** (mediana) | **8.72 ms** (mediana) | — | — | — | — | sin carga en esta sección; la diferencia depende de la máquina |
| 22 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 1000 fichas | tiempo | **10.829 ms** (mediana) | **8.77 ms** (mediana) | — | — | — | — | sin carga en esta sección; la diferencia depende de la máquina |
| 23 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 1 paso | tiempo | **20.2 µs** (mediana) | **19.2 µs** (mediana) | — | — | — | — | carga: esqueleto con costos; la diferencia depende de la máquina |
| 24 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 2 pasos | tiempo | **48.6 µs** (mediana) | **45.0 µs** (mediana) | — | — | — | — | carga: esqueleto con costos; la diferencia depende de la máquina |
| 25 | 5. Planear la vecindad en una cripta de 1000 salas | precargar_vecinas cuando no hace falta nada | tiempo | **30.6 µs** (mediana) | **27.2 µs** (mediana) | — | — | — | — | carga: esqueleto con costos; la diferencia depende de la máquina |
| 26 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad    5 | cuenta | 82 aciertos / 938 fallos (8.0 %) 19 solicitudes de red (igual en las tres) | 83 aciertos / 1100 fallos (7.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +45 solicitudes; +1 consulta de llaves y 45 disparadas por cazadores; la ficha del cazador y las salas que construyen los cazadores mueven aciertos y fallos |
| 27 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   10 | cuenta | 316 aciertos / 704 fallos (31.0 %) 19 solicitudes de red (igual en las tres) | 327 aciertos / 856 fallos (27.6 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +45 solicitudes; +1 consulta de llaves y 45 disparadas por cazadores; la ficha del cazador y las salas que construyen los cazadores mueven aciertos y fallos |
| 28 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   25 | cuenta | 487 aciertos / 533 fallos (47.7 %) 19 solicitudes de red (igual en las tres) | 553 aciertos / 630 fallos (46.7 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +45 solicitudes; +1 consulta de llaves y 45 disparadas por cazadores; la ficha del cazador y las salas que construyen los cazadores mueven aciertos y fallos |
| 29 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad  100 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red (igual en las tres) | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +45 solicitudes; +1 consulta de llaves y 45 disparadas por cazadores; la ficha del cazador y las salas que construyen los cazadores mueven aciertos y fallos |
| 30 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad 1000 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red (igual en las tres) | 1112 aciertos / 71 fallos (94.0 %) 64 solicitudes de red; de ellas, 45 disparadas por un cazador (igual en las tres) | — | — | — | — | carga: +45 solicitudes; +1 consulta de llaves y 45 disparadas por cazadores; la ficha del cazador y las salas que construyen los cazadores mueven aciertos y fallos |
| 31 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 25 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **0.7 µs** (mediana) | — | — | 1.40 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| 32 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 100 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **2.18 µs** (mediana) | — | — | 4.36 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| 33 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 1000 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **20.82 µs** (mediana) | — | — | 41.64 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| 34 | 2. Búsqueda en la caché (µs por operación) | lista enlazada propia, 5000 fichas, acierto (descartada) | tiempo | sin antes en M0: fila nueva (FR-378) | **96.78 µs** (mediana) | — | — | 193.56 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |

### Bloque `guardado`

| # | Sección | Medición | Tipo | Antes (M0) | Carga (M1) | Después (M2) | Diferencia | Límite (2×) | Cumple | Causa |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | §4.10 | verificación: cargar el binario devuelve exactamente el estado guardado | cuenta | OK (igual en las tres) | OK (igual en las tres) | — | — | — | — | sin cambios |
| G2 | §4.10 | verificación: un archivo de otra versión del formato se rechaza | cuenta | OK (igual en las tres) | OK (igual en las tres) | — | — | — | — | sin cambios |
| G3 | §4.10 | 10 salas  tamaño en disco  [binario] | cuenta | 12,581 bytes (igual en las tres) | 12,414 bytes (igual en las tres) | — | — | — | — | carga: un cazador con rango por sala (nombre más corto que el de la rata), costos de 1 a 9 en lugar de 100 y el conocimiento de la mitad de las salas cambian el contenido guardado |
| G4 | §4.10 | 10 salas  tamaño en disco  [JSON] | cuenta | 28,678 bytes  (2.28× el binario) (igual en las tres) | 28,363 bytes  (2.28× el binario) (igual en las tres) | — | — | — | — | carga: un cazador con rango por sala (nombre más corto que el de la rata), costos de 1 a 9 en lugar de 100 y el conocimiento de la mitad de las salas cambian el contenido guardado |
| G5 | §4.10 | 10 salas  guardar la partida completa  [binario] | tiempo | **1.71 ms** (mediana) | **1.70 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G6 | §4.10 | 10 salas  guardar la partida completa  [JSON] | tiempo | **833.0 µs** (mediana) | **804.6 µs** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G7 | §4.10 | 10 salas  cargar la partida completa   [binario → DTO] | tiempo | **2.10 ms** (mediana) | **2.43 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G8 | §4.10 | 10 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **300.9 µs** (mediana) | **286.7 µs** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G9 | §4.10 | 10 salas  cargar UNA sala (la 6)    [binario, acceso directo] | tiempo | **74.0 µs** (mediana) | **73.6 µs** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G10 | §4.10 | 10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo] | tiempo | **278.2 µs** (mediana) | **289.5 µs** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G11 | §4.10 | 100 salas  tamaño en disco  [binario] | cuenta | 47,943 bytes (igual en las tres) | 46,646 bytes (igual en las tres) | — | — | — | — | carga: un cazador con rango por sala (nombre más corto que el de la rata), costos de 1 a 9 en lugar de 100 y el conocimiento de la mitad de las salas cambian el contenido guardado |
| G12 | §4.10 | 100 salas  tamaño en disco  [JSON] | cuenta | 134,896 bytes  (2.81× el binario) (igual en las tres) | 133,318 bytes  (2.86× el binario) (igual en las tres) | — | — | — | — | carga: un cazador con rango por sala (nombre más corto que el de la rata), costos de 1 a 9 en lugar de 100 y el conocimiento de la mitad de las salas cambian el contenido guardado |
| G13 | §4.10 | 100 salas  guardar la partida completa  [binario] | tiempo | **4.97 ms** (mediana) | **5.00 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G14 | §4.10 | 100 salas  guardar la partida completa  [JSON] | tiempo | **3.31 ms** (mediana) | **3.31 ms** (mediana) | — | — | — | — | sin cambios |
| G15 | §4.10 | 100 salas  cargar la partida completa   [binario → DTO] | tiempo | **6.94 ms** (mediana) | **7.02 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G16 | §4.10 | 100 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **1.16 ms** (mediana) | **1.12 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G17 | §4.10 | 100 salas  cargar UNA sala (la 51)    [binario, acceso directo] | tiempo | **75.6 µs** (mediana) | **75.7 µs** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G18 | §4.10 | 100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo] | tiempo | **1.15 ms** (mediana) | **1.10 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G19 | §4.10 | 1000 salas  tamaño en disco  [binario] | cuenta | 412,440 bytes (igual en las tres) | 400,347 bytes (igual en las tres) | — | — | — | — | carga: un cazador con rango por sala (nombre más corto que el de la rata), costos de 1 a 9 en lugar de 100 y el conocimiento de la mitad de las salas cambian el contenido guardado |
| G20 | §4.10 | 1000 salas  tamaño en disco  [JSON] | cuenta | 1,213,097 bytes  (2.94× el binario) (igual en las tres) | 1,199,809 bytes  (3.00× el binario) (igual en las tres) | — | — | — | — | carga: un cazador con rango por sala (nombre más corto que el de la rata), costos de 1 a 9 en lugar de 100 y el conocimiento de la mitad de las salas cambian el contenido guardado |
| G21 | §4.10 | 1000 salas  guardar la partida completa  [binario] | tiempo | **36.23 ms** (mediana) | **36.70 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G22 | §4.10 | 1000 salas  guardar la partida completa  [JSON] | tiempo | **28.83 ms** (mediana) | **28.94 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G23 | §4.10 | 1000 salas  cargar la partida completa   [binario → DTO] | tiempo | **60.48 ms** (mediana) | **59.03 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G24 | §4.10 | 1000 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **9.80 ms** (mediana) | **9.56 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G25 | §4.10 | 1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] | tiempo | **83.6 µs** (mediana) | **75.3 µs** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G26 | §4.10 | 1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] | tiempo | **9.46 ms** (mediana) | **9.69 ms** (mediana) | — | — | — | — | carga: la misma partida con la carga; la diferencia depende de la máquina |
| G27 | §4.10 | (nota de la salida) El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. | nota | — | — | — | — | — | — | — |
| G28 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | sin antes en M0: fila nueva (FR-378) | 239 bytes de 12,414 del archivo; 3 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G29 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la del medio, la 6) | cuenta | sin antes en M0: fila nueva (FR-378) | 239 bytes de 12,414 del archivo; 3 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G30 | §4.10 | 10 salas  bytes leídos al cargar UNA sala (la última, la 10) | cuenta | sin antes en M0: fila nueva (FR-378) | 262 bytes de 12,414 del archivo; 4 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G31 | §4.10 | 10 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **79.1 µs** (mediana) | — | — | 158.20 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G32 | §4.10 | 10 salas  cargar UNA sala (la última, la 10)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **75.0 µs** (mediana) | — | — | 150.00 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G33 | §4.10 | verificación: 10 salas: leer UNA sala lee menos bytes que el archivo | cuenta | sin antes en M0: fila nueva (FR-378) | OK (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G34 | §4.10 | verificación: 10 salas: entradas leídas (4) ≤ ⌊log₂ n⌋ + 1 = 4 | cuenta | sin antes en M0: fila nueva (FR-378) | OK (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G35 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | sin antes en M0: fila nueva (FR-378) | 299 bytes de 46,646 del archivo; 6 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G36 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la del medio, la 51) | cuenta | sin antes en M0: fila nueva (FR-378) | 304 bytes de 46,646 del archivo; 6 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G37 | §4.10 | 100 salas  bytes leídos al cargar UNA sala (la última, la 100) | cuenta | sin antes en M0: fila nueva (FR-378) | 334 bytes de 46,646 del archivo; 7 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G38 | §4.10 | 100 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **85.5 µs** (mediana) | — | — | 171.00 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G39 | §4.10 | 100 salas  cargar UNA sala (la última, la 100)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **75.4 µs** (mediana) | — | — | 150.80 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G40 | §4.10 | verificación: 100 salas: leer UNA sala lee menos bytes que el archivo | cuenta | sin antes en M0: fila nueva (FR-378) | OK (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G41 | §4.10 | verificación: 100 salas: entradas leídas (7) ≤ ⌊log₂ n⌋ + 1 = 7 | cuenta | sin antes en M0: fila nueva (FR-378) | OK (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G42 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la primera, la 1) | cuenta | sin antes en M0: fila nueva (FR-378) | 359 bytes de 400,347 del archivo; 9 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G43 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la del medio, la 501) | cuenta | sin antes en M0: fila nueva (FR-378) | 374 bytes de 400,347 del archivo; 9 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G44 | §4.10 | 1000 salas  bytes leídos al cargar UNA sala (la última, la 1000) | cuenta | sin antes en M0: fila nueva (FR-378) | 397 bytes de 400,347 del archivo; 10 entradas de la tabla (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G45 | §4.10 | 1000 salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **97.9 µs** (mediana) | — | — | 195.80 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G46 | §4.10 | 1000 salas  cargar UNA sala (la última, la 1000)    [binario, acceso directo] | tiempo | sin antes en M0: fila nueva (FR-378) | **80.6 µs** (mediana) | — | — | 161.20 µs | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G47 | §4.10 | verificación: 1000 salas: leer UNA sala lee menos bytes que el archivo | cuenta | sin antes en M0: fila nueva (FR-378) | OK (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |
| G48 | §4.10 | verificación: 1000 salas: entradas leídas (10) ≤ ⌊log₂ n⌋ + 1 = 10 | cuenta | sin antes en M0: fila nueva (FR-378) | OK (igual en las tres) | — | — | — | — | sin antes en M0: fila nueva (FR-378); su antes es M1 |

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
