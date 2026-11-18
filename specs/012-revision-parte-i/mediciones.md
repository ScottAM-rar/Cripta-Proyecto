# Mediciones: Revisión de la Parte I con la carga nueva (012)

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Tareas**: [tasks.md](tasks.md) · **Formato**: [contracts/filas-medicion.md](contracts/filas-medicion.md)

Cada paso (M0, M1 y M2) son tres ejecuciones de cada bloque. En las filas de **tiempo** el valor del paso es la **mediana de las tres** (FR-383, FR-384); las filas de **cuenta** tienen que salir iguales en las tres (FR-379). Los tiempos dependen de la máquina: Windows AMD64, Python 3.12.10.

## Catálogo de filas (ajuste con M0, T004)

- **Bloque `cache`**: M0 da 30 filas y coincide con el catálogo (filas 1 a 30, en el orden de salida). Las filas 31 a 34 quedan reservadas para la lista enlazada propia (descartada) que agrega T019.
- **Bloque `guardado`**: el catálogo no las numeraba. Gana M0: 27 líneas, numeradas **G1 a G27** en el orden de salida. G1 y G2 son las verificaciones; G3 a G26, ocho filas por tamaño (10, 100 y 1 000 salas); **G27 no es una medición** sino la nota de texto con que termina el bloque, y no se compara. Las filas nuevas de T021 (bytes leídos y tiempo de la primera y la última sala) se agregarán desde **G28**.
- **Tipos** (research D3): cuenta = `cache` 1 a 4 y 26 a 30, `guardado` G1 a G4, G11, G12, G19 y G20; tiempo = `cache` 5 a 25 y el resto de `guardado`.

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

Pendiente (T022): tres ejecuciones de cada bloque con `bench-cache-M1-{1,2,3}.csv` y `bench-guardado-M1-{1,2,3}.csv`.

## M2 · el después

Pendiente (T031): tres ejecuciones de cada bloque con `bench-cache-M2-{1,2,3}.csv` y `bench-guardado-M2-{1,2,3}.csv`.

## Comprobación de las filas de cuenta

- **M0**: las 10 filas de cuenta de `cache` y las 8 de `guardado` son idénticas en las tres ejecuciones.
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

### Pruebas de equivalencia

Pendiente: contra `0b031ec` (T013 y T014) y contra el código revisado (T025, T028 y T030).

## Tabla por bloque

Antes = M0 (mediana en las filas de tiempo). Las columnas de M1, M2, diferencia, límite, cumple y causa se completan en T022, T023 y T033.

### Bloque `cache`

| # | Sección | Medición | Tipo | Antes (M0) | Carga (M1) | Después (M2) | Diferencia | Límite (2×) | Cumple | Causa |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1. Solicitudes al recorrer un pasillo de 60 salas | sala por sala (sin precarga) | cuenta | 63 solicitudes (~25.2 s de espera) (igual en las tres) | — | — | — | — | — | — |
| 2 | 1. Solicitudes al recorrer un pasillo de 60 salas | actual + vecinas en cada paso (prof. 2) | cuenta | 61 solicitudes (~24.4 s de espera) (igual en las tres) | — | — | — | — | — | — |
| 3 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, prof. 2 | cuenta | 33 solicitudes (~13.2 s de espera) (igual en las tres) | — | — | — | — | — | — |
| 4 | 1. Solicitudes al recorrer un pasillo de 60 salas | perezosa, por defecto (lote de 10) | cuenta | 9 solicitudes (~3.6 s de espera) (igual en las tres) | — | — | — | — | — | — |
| 5 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, acierto | tiempo | **1.1 µs** (mediana) | — | — | — | — | — | — |
| 6 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 25 fichas, fallo | tiempo | **0.64 µs** (mediana) | — | — | — | — | — | — |
| 7 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 25 fichas, acierto (descartada) | tiempo | **0.2 µs** (mediana) | — | — | — | — | — | — |
| 8 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, acierto | tiempo | **3.07 µs** (mediana) | — | — | — | — | — | — |
| 9 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 100 fichas, fallo | tiempo | **2.13 µs** (mediana) | — | — | — | — | — | — |
| 10 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 100 fichas, acierto (descartada) | tiempo | **0.23 µs** (mediana) | — | — | — | — | — | — |
| 11 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, acierto | tiempo | **33.93 µs** (mediana) | — | — | — | — | — | — |
| 12 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 1000 fichas, fallo | tiempo | **19.53 µs** (mediana) | — | — | — | — | — | — |
| 13 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 1000 fichas, acierto (descartada) | tiempo | **0.27 µs** (mediana) | — | — | — | — | — | — |
| 14 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, acierto | tiempo | **172.4 µs** (mediana) | — | — | — | — | — | — |
| 15 | 2. Búsqueda en la caché (µs por operación) | deque lineal, 5000 fichas, fallo | tiempo | **97.48 µs** (mediana) | — | — | — | — | — | — |
| 16 | 2. Búsqueda en la caché (µs por operación) | tabla hash propia, 5000 fichas, acierto (descartada) | tiempo | **0.33 µs** (mediana) | — | — | — | — | — | — |
| 17 | 3. Recuperar una ficha liberada desde disco | catálogo con 25 fichas | tiempo | **0.092 ms por lectura (una solicitud real: ~400 ms)** (mediana) | — | — | — | — | — | — |
| 18 | 3. Recuperar una ficha liberada desde disco | catálogo con 200 fichas | tiempo | **0.167 ms por lectura (una solicitud real: ~400 ms)** (mediana) | — | — | — | — | — | — |
| 19 | 3. Recuperar una ficha liberada desde disco | catálogo con 1000 fichas | tiempo | **0.42 ms por lectura (una solicitud real: ~400 ms)** (mediana) | — | — | — | — | — | — |
| 20 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 25 fichas | tiempo | **2.216 ms** (mediana) | — | — | — | — | — | — |
| 21 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 200 fichas | tiempo | **9.649 ms** (mediana) | — | — | — | — | — | — |
| 22 | 4. Guardar 10 fichas nuevas (reescribe el archivo completo) | catálogo con 1000 fichas | tiempo | **10.829 ms** (mediana) | — | — | — | — | — | — |
| 23 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 1 paso | tiempo | **20.2 µs** (mediana) | — | — | — | — | — | — |
| 24 | 5. Planear la vecindad en una cripta de 1000 salas | salas_vecinas, 2 pasos | tiempo | **48.6 µs** (mediana) | — | — | — | — | — | — |
| 25 | 5. Planear la vecindad en una cripta de 1000 salas | precargar_vecinas cuando no hace falta nada | tiempo | **30.6 µs** (mediana) | — | — | — | — | — | — |
| 26 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad    5 | cuenta | 82 aciertos / 938 fallos (8.0 %) 19 solicitudes de red (igual en las tres) | — | — | — | — | — | — |
| 27 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   10 | cuenta | 316 aciertos / 704 fallos (31.0 %) 19 solicitudes de red (igual en las tres) | — | — | — | — | — | — |
| 28 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad   25 | cuenta | 487 aciertos / 533 fallos (47.7 %) 19 solicitudes de red (igual en las tres) | — | — | — | — | — | — |
| 29 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad  100 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red (igual en las tres) | — | — | — | — | — | — |
| 30 | 6. Caché en una partida completa (150 pasos por una rejilla de 10x10) | capacidad 1000 | cuenta | 950 aciertos / 70 fallos (93.1 %) 19 solicitudes de red (igual en las tres) | — | — | — | — | — | — |

### Bloque `guardado`

| # | Sección | Medición | Tipo | Antes (M0) | Carga (M1) | Después (M2) | Diferencia | Límite (2×) | Cumple | Causa |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | §4.10 | verificación: cargar el binario devuelve exactamente el estado guardado | cuenta | OK (igual en las tres) | — | — | — | — | — | — |
| G2 | §4.10 | verificación: un archivo de otra versión del formato se rechaza | cuenta | OK (igual en las tres) | — | — | — | — | — | — |
| G3 | §4.10 | 10 salas  tamaño en disco  [binario] | cuenta | 12,581 bytes (igual en las tres) | — | — | — | — | — | — |
| G4 | §4.10 | 10 salas  tamaño en disco  [JSON] | cuenta | 28,678 bytes  (2.28× el binario) (igual en las tres) | — | — | — | — | — | — |
| G5 | §4.10 | 10 salas  guardar la partida completa  [binario] | tiempo | **1.71 ms** (mediana) | — | — | — | — | — | — |
| G6 | §4.10 | 10 salas  guardar la partida completa  [JSON] | tiempo | **833.0 µs** (mediana) | — | — | — | — | — | — |
| G7 | §4.10 | 10 salas  cargar la partida completa   [binario → DTO] | tiempo | **2.10 ms** (mediana) | — | — | — | — | — | — |
| G8 | §4.10 | 10 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **300.9 µs** (mediana) | — | — | — | — | — | — |
| G9 | §4.10 | 10 salas  cargar UNA sala (la 6)    [binario, acceso directo] | tiempo | **74.0 µs** (mediana) | — | — | — | — | — | — |
| G10 | §4.10 | 10 salas  conseguir UNA sala (la 6) [JSON: hay que leer todo] | tiempo | **278.2 µs** (mediana) | — | — | — | — | — | — |
| G11 | §4.10 | 100 salas  tamaño en disco  [binario] | cuenta | 47,943 bytes (igual en las tres) | — | — | — | — | — | — |
| G12 | §4.10 | 100 salas  tamaño en disco  [JSON] | cuenta | 134,896 bytes  (2.81× el binario) (igual en las tres) | — | — | — | — | — | — |
| G13 | §4.10 | 100 salas  guardar la partida completa  [binario] | tiempo | **4.97 ms** (mediana) | — | — | — | — | — | — |
| G14 | §4.10 | 100 salas  guardar la partida completa  [JSON] | tiempo | **3.31 ms** (mediana) | — | — | — | — | — | — |
| G15 | §4.10 | 100 salas  cargar la partida completa   [binario → DTO] | tiempo | **6.94 ms** (mediana) | — | — | — | — | — | — |
| G16 | §4.10 | 100 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **1.16 ms** (mediana) | — | — | — | — | — | — |
| G17 | §4.10 | 100 salas  cargar UNA sala (la 51)    [binario, acceso directo] | tiempo | **75.6 µs** (mediana) | — | — | — | — | — | — |
| G18 | §4.10 | 100 salas  conseguir UNA sala (la 51) [JSON: hay que leer todo] | tiempo | **1.15 ms** (mediana) | — | — | — | — | — | — |
| G19 | §4.10 | 1000 salas  tamaño en disco  [binario] | cuenta | 412,440 bytes (igual en las tres) | — | — | — | — | — | — |
| G20 | §4.10 | 1000 salas  tamaño en disco  [JSON] | cuenta | 1,213,097 bytes  (2.94× el binario) (igual en las tres) | — | — | — | — | — | — |
| G21 | §4.10 | 1000 salas  guardar la partida completa  [binario] | tiempo | **36.23 ms** (mediana) | — | — | — | — | — | — |
| G22 | §4.10 | 1000 salas  guardar la partida completa  [JSON] | tiempo | **28.83 ms** (mediana) | — | — | — | — | — | — |
| G23 | §4.10 | 1000 salas  cargar la partida completa   [binario → DTO] | tiempo | **60.48 ms** (mediana) | — | — | — | — | — | — |
| G24 | §4.10 | 1000 salas  cargar la partida completa   [JSON, solo analiza el texto] | tiempo | **9.80 ms** (mediana) | — | — | — | — | — | — |
| G25 | §4.10 | 1000 salas  cargar UNA sala (la 501)    [binario, acceso directo] | tiempo | **83.6 µs** (mediana) | — | — | — | — | — | — |
| G26 | §4.10 | 1000 salas  conseguir UNA sala (la 501) [JSON: hay que leer todo] | tiempo | **9.46 ms** (mediana) | — | — | — | — | — | — |
| G27 | §4.10 | (nota de la salida) El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala. | nota | — | — | — | — | — | — | — |

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
