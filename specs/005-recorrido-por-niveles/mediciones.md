# Mediciones: Recorrido por niveles

Generadas con `python main.py --bench recorrido` el 2026-10-28 (Python 3.14.7, macOS arm64, semilla 2026). Criptas sintéticas deterministas por semilla; sin red ni vista. Las cifras cambian algo de una máquina a otra; lo que importa son los conteos, las proporciones y el orden entre alternativas.

## Resumen frente a los criterios

| Criterio | Resultado | Veredicto |
|---|---|---|
| SC-004 (criterio duro, conteo): un recorrido acotado visita las mismas salas y examina las mismas salidas en 400, 4 900 y 40 000 salas | Límite 2: 13 salas y 20 salidas en las tres. Límite 5: 61 salas y 164 salidas en las tres | Cumple |
| SC-004 (informativa): razón de tiempos con límite 2, 40 000 salas / 400 salas | 0,99× (4,5 µs en ambas) | Informativa, sin umbral |
| FR-510: el trabajo depende de lo visitado | Sin límite en la rejilla de 40 000 salas: 33 ms; con límite 2: 4,5 µs | Cumple |
| Equivalencia con la referencia ingenua (sección F) | 300 recorridos, 0 diferencias | Cumple |
| Los cuatro recorridos alternativos dan el mismo resultado que el elegido | Verificado en rejilla de 4 900, de 40 000 y árbol de 29 524 | Cumple |

## Decisiones y la alternativa descartada

| Decisión | Alternativa | Qué se midió | Conclusión |
|---|---|---|---|
| **Cola circular** | `list` con `pop(0)` | Árbol (frontera de 19 683 salas): 25,1 ms frente a 41,1 ms (pop(0) 64 % más lento). Rejilla (frontera de 138 y 398 salas): pop(0) es 3 % a 10 % más rápido | Donde la frontera es ancha, `pop(0)` se degrada; donde es angosta, no importa. La cola circular evita el peor caso |
| **Cola circular** | `list` con índice de cabeza | Árbol: 22,1 ms (12 % más rápido). Rejilla de 40 000: 31,2 ms (5 % más rápido). Rejilla de 4 900: 4,95 ms con mucha dispersión (3,8 a 7,8 ms) | Más rápida en el árbol, pero nunca libera lo sacado. La diferencia es pequeña |
| **Cola circular** | **Dos listas por nivel, sin cola** | Árbol: 21,5 ms (14 % más rápido). Rejilla de 40 000: 30,2 ms (8 % más rápido). Rejilla de 4 900: 2,82 ms (10 % más rápido) | **Gana de forma consistente pero pequeña (8 % a 14 %)** y con menos piezas. Ver la nota de decisión abajo |
| **`ordenar_adaptativo` por nivel** | Montículo con clave `(nivel, id)` | Rejilla de 40 000: 33,8 ms frente a 40,2 ms (el montículo, 19 % más lento). Árbol: 24,5 ms frente a 35,9 ms (46 % más lento) | Se mantiene. Con niveles angostos el orden por nivel paga log del ancho en vez de log V |
| **Marcas de época por id** | Limpiar una lista en cada recorrido | No se midió: limpiar costaría O(N) en cada llamada y haría imposible el conteo de SC-004 (con 40 000 salas, 40 000 escrituras por un recorrido de 13 salas) | Se mantiene por razonamiento; el conteo igual en las tres criptas lo respalda |

### Nota de decisión (T021)

**Las decisiones se mantienen, con una observación abierta para el grupo.**

- **Cola circular:** `plan.md` y `research.md` §3 anticiparon que, como cada nivel se ordena antes de procesarse, la cola contiene un solo nivel a la vez y equivale a «dos listas por nivel». La medición lo confirma: las dos listas son entre 8 % y 14 % más rápidas y más simples. La diferencia es consistente pero pequeña, y la cola circular cumple todos los requisitos y gana de forma clara a `pop(0)` en frontera ancha.
- **Por qué no se cambió el código:** el diseño con cola circular fue una instrucción explícita del grupo y el plan dejaba «si la alternativa gana con claridad, se cambia». Un 8 % a 14 % no lo consideré «con claridad» sin consultarlo. **Es una decisión del grupo**: si se prefiere la versión de dos listas, el cambio es local a `Logica/RecorridoPorNiveles.py` y la prueba de equivalencia lo respalda.
- **Montículo:** descartado con holgura.

### Segunda corrida (`python main.py --bench` completo, mismo día)

| Medición | Cola circular | `pop(0)` | Índice de cabeza | Dos listas |
|---|---|---|---|---|
| Rejilla de 4 900 salas | 3,07 ms | 2,76 ms (−10 %) | 2,69 ms (−12 %) | 2,63 ms (−14 %) |
| Rejilla de 40 000 salas | 32,07 ms | 29,13 ms (−9 %) | 28,42 ms (−11 %) | 27,69 ms (−14 %) |
| Árbol de 29 524 salas | 23,69 ms | 40,23 ms (+70 %) | 21,18 ms (−11 %) | 20,76 ms (−12 %) |

Montículo frente a `ordenar_adaptativo`: 40,07 ms frente a 32,50 ms (rejilla) y 35,40 ms frente a 23,65 ms (árbol). La tendencia es la de la primera corrida. **En frontera angosta la cola circular es la más lenta de las cuatro; en frontera ancha solo pierde `pop(0)`.** Las dos listas son entre 8 % y 14 % más rápidas en las seis mediciones de las dos corridas.

### Lo que hay hoy (sección E, solo informativa)

`ServicioCripta.salas_vecinas` (con `deque` y búsqueda lineal) frente al recorrido nuevo, con límite 5 desde el centro: 0,13 ms frente a 0,02 ms en 400 salas; 1,18 ms frente a 0,02 ms en 4 900; **11,75 ms frente a 0,02 ms en 40 000 salas**. El de hoy crece con el tamaño de la cripta porque busca cada sala en el esqueleto con un recorrido lineal; el nuevo no. No se compararon las secuencias: `salas_vecinas` ordena por letra de dirección y no incluye el origen. Reemplazarlo no forma parte de esta capacidad.

### Limitaciones

- Dos corridas del mismo equipo, con resultados consistentes entre sí. Entre `pop(0)`, índice de cabeza y dos listas las diferencias son de pocos puntos y no se pueden distinguir con seguridad; lo que sí se repite es que la cola circular no es la más rápida.
- La rejilla y el árbol son los dos extremos de frontera angosta y ancha; una cripta real con ramas y salas sueltas queda entre ambos.

## Salida completa del bloque `recorrido`

```text
Recorrido por niveles (A): acotado frente a sin límite al crecer la cripta (SC-004)
  rejilla    400 salas  límite 2 niveles (    13 salas visitadas,     20 salidas examinadas) 4.5 µs  (4.3 µs – 7.7 µs)  mediana (mín – máx)
  rejilla   4900 salas  límite 2 niveles (    13 salas visitadas,     20 salidas examinadas) 4.5 µs  (4.3 µs – 5.0 µs)  mediana (mín – máx)
  rejilla  40000 salas  límite 2 niveles (    13 salas visitadas,     20 salidas examinadas) 4.5 µs  (4.5 µs – 4.8 µs)  mediana (mín – máx)
  verificación: límite 2: mismas salas visitadas y mismas salidas examinadas en 400, 4 900 y 40 000 salas (13, 20) OK
  rejilla    400 salas  límite 5 niveles (    61 salas visitadas,    164 salidas examinadas) 19.9 µs  (19.4 µs – 21.2 µs)  mediana (mín – máx)
  rejilla   4900 salas  límite 5 niveles (    61 salas visitadas,    164 salidas examinadas) 20.3 µs  (20.0 µs – 24.9 µs)  mediana (mín – máx)
  rejilla  40000 salas  límite 5 niveles (    61 salas visitadas,    164 salidas examinadas) 20.0 µs  (19.7 µs – 20.4 µs)  mediana (mín – máx)
  verificación: límite 5: mismas salas visitadas y mismas salidas examinadas en 400, 4 900 y 40 000 salas (61, 164) OK
  rejilla    400 salas  sin límite       (   400 salas visitadas,  1,520 salidas examinadas) 140.5 µs  (137.9 µs – 147.9 µs)  mediana (mín – máx)
  rejilla   4900 salas  sin límite       ( 4,900 salas visitadas, 19,320 salidas examinadas) 3.17 ms  (3.15 ms – 3.27 ms)  mediana (mín – máx)
  rejilla  40000 salas  sin límite       (40,000 salas visitadas, 159,200 salidas examinadas) 33.07 ms  (31.89 ms – 34.03 ms)  mediana (mín – máx)
  razón de tiempos con límite 2: 40 000 salas / 400 salas (INFORMATIVA, sin umbral) 0.99×  se espera cercana a 1; depende de la máquina
  Sin límite el trabajo sí crece con la cripta porque todo es alcanzable; con límite depende solo de la zona alrededor del origen. 

Recorrido por niveles (B): cola circular frente a la alternativa descartada, rejilla
  verificación: rejilla   4900 salas: lista con pop(0) da el mismo recorrido OK
  verificación: rejilla   4900 salas: lista con índice de cabeza da el mismo recorrido OK
  verificación: rejilla   4900 salas: dos listas por nivel, sin cola da el mismo recorrido OK
  rejilla   4900 salas  cola circular (elegida)                      3.12 ms  (3.09 ms – 3.15 ms)  mediana (mín – máx)
  rejilla   4900 salas  lista con pop(0) (descartada)                2.80 ms  (2.76 ms – 2.83 ms)  mediana (mín – máx)
  rejilla   4900 salas  lista con índice de cabeza (descartada)      4.95 ms  (3.81 ms – 7.84 ms)  mediana (mín – máx)
  rejilla   4900 salas  dos listas por nivel, sin cola (descartada)  2.82 ms  (2.61 ms – 3.16 ms)  mediana (mín – máx)
  rejilla   4900 salas  nivel más ancho                              138 salas  tamaño máximo que llega a tener la cola
  verificación: rejilla  40000 salas: lista con pop(0) da el mismo recorrido OK
  verificación: rejilla  40000 salas: lista con índice de cabeza da el mismo recorrido OK
  verificación: rejilla  40000 salas: dos listas por nivel, sin cola da el mismo recorrido OK
  rejilla  40000 salas  cola circular (elegida)                      32.89 ms  (32.04 ms – 33.10 ms)  mediana (mín – máx)
  rejilla  40000 salas  lista con pop(0) (descartada)                31.87 ms  (31.22 ms – 32.37 ms)  mediana (mín – máx)
  rejilla  40000 salas  lista con índice de cabeza (descartada)      31.15 ms  (29.83 ms – 31.27 ms)  mediana (mín – máx)
  rejilla  40000 salas  dos listas por nivel, sin cola (descartada)  30.24 ms  (29.37 ms – 30.89 ms)  mediana (mín – máx)
  rejilla  40000 salas  nivel más ancho                              398 salas  tamaño máximo que llega a tener la cola
  Sin límite, desde el centro. La frontera de una rejilla es angosta: pop(0) desplaza pocos elementos. 

Recorrido por niveles (C): cola circular frente a la alternativa descartada, árbol de frontera ancha
  verificación: árbol 3-ario 29 524 salas: lista con pop(0) da el mismo recorrido OK
  verificación: árbol 3-ario 29 524 salas: lista con índice de cabeza da el mismo recorrido OK
  verificación: árbol 3-ario 29 524 salas: dos listas por nivel, sin cola da el mismo recorrido OK
  árbol 3-ario 29 524 salas  cola circular (elegida)                 25.05 ms  (24.65 ms – 25.80 ms)  mediana (mín – máx)
  árbol 3-ario 29 524 salas  lista con pop(0) (descartada)           41.13 ms  (41.10 ms – 41.42 ms)  mediana (mín – máx)
  árbol 3-ario 29 524 salas  lista con índice de cabeza (descartada) 22.08 ms  (21.95 ms – 22.32 ms)  mediana (mín – máx)
  árbol 3-ario 29 524 salas  dos listas por nivel, sin cola (descartada) 21.50 ms  (21.02 ms – 22.17 ms)  mediana (mín – máx)
  árbol 3-ario 29 524 salas  nivel más ancho                         19,683 salas  tamaño máximo que llega a tener la cola
  En el árbol el último nivel tiene 19 683 salas: cada pop(0) desplaza una cola de ese largo. 

Recorrido por niveles (D): orden dentro del nivel, ordenar_adaptativo frente a montículo (nivel, id)
  verificación: rejilla  40000 salas: el montículo da el mismo recorrido OK
  rejilla  40000 salas  ordenar_adaptativo por nivel (elegida)       33.79 ms  (33.44 ms – 34.22 ms)  mediana (mín – máx)
  rejilla  40000 salas  montículo (nivel, id) (descartada)           40.17 ms  (40.08 ms – 41.57 ms)  mediana (mín – máx)
  verificación: árbol 3-ario 29 524 salas: el montículo da el mismo recorrido OK
  árbol 3-ario 29 524 salas  ordenar_adaptativo por nivel (elegida)  24.54 ms  (23.71 ms – 24.68 ms)  mediana (mín – máx)
  árbol 3-ario 29 524 salas  montículo (nivel, id) (descartada)      35.94 ms  (35.36 ms – 36.73 ms)  mediana (mín – máx)
  El montículo no necesita cola ni ordenar por nivel, pero paga log V por sala en vez de log del ancho del nivel. 

Recorrido por niveles (E): referencia de lo que hay hoy, ServicioCripta.salas_vecinas (solo informativa)
  rejilla    400 salas  límite 2  salas_vecinas (hoy, 12 salas)      16.2 µs  (15.9 µs – 16.8 µs)  mediana (mín – máx)
  rejilla    400 salas  límite 2  recorrido nuevo (12 salas)         4.5 µs  (4.4 µs – 5.3 µs)  mediana (mín – máx)
  rejilla    400 salas  límite 5  salas_vecinas (hoy, 60 salas)      127.0 µs  (126.5 µs – 127.7 µs)  mediana (mín – máx)
  rejilla    400 salas  límite 5  recorrido nuevo (60 salas)         20.6 µs  (20.0 µs – 21.0 µs)  mediana (mín – máx)
  rejilla   4900 salas  límite 2  salas_vecinas (hoy, 12 salas)      170.4 µs  (168.2 µs – 176.9 µs)  mediana (mín – máx)
  rejilla   4900 salas  límite 2  recorrido nuevo (12 salas)         4.6 µs  (4.5 µs – 5.2 µs)  mediana (mín – máx)
  rejilla   4900 salas  límite 5  salas_vecinas (hoy, 60 salas)      1.18 ms  (1.15 ms – 1.20 ms)  mediana (mín – máx)
  rejilla   4900 salas  límite 5  recorrido nuevo (60 salas)         20.0 µs  (19.6 µs – 20.4 µs)  mediana (mín – máx)
  rejilla  40000 salas  límite 2  salas_vecinas (hoy, 12 salas)      1.55 ms  (1.53 ms – 1.61 ms)  mediana (mín – máx)
  rejilla  40000 salas  límite 2  recorrido nuevo (12 salas)         4.6 µs  (4.5 µs – 5.2 µs)  mediana (mín – máx)
  rejilla  40000 salas  límite 5  salas_vecinas (hoy, 60 salas)      11.75 ms  (10.83 ms – 12.49 ms)  mediana (mín – máx)
  rejilla  40000 salas  límite 5  recorrido nuevo (60 salas)         20.4 µs  (19.8 µs – 21.2 µs)  mediana (mín – máx)
  No se compara la secuencia: salas_vecinas ordena por letra de dirección y no incluye el origen. No interviene en el veredicto. 
  salas_vecinas busca cada sala en el esqueleto con un recorrido lineal: su costo depende del tamaño de la cripta. 

Recorrido por niveles (F): equivalencia con la referencia ingenua
  verificación: 300 recorridos frente a la referencia, 0 diferencias OK

Recorrido por niveles (SC-004, equivalencia y verificaciones previas): CUMPLE.
```
