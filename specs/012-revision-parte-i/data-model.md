# Modelo de datos (fase 1): Revisión de la Parte I con la carga nueva

Esta capacidad no agrega datos al juego ni cambia el formato de partida. Las entidades de abajo son las de la medición, el inventario y las dos estructuras que se reescriben. Las dos estructuras conservan su interfaz pública (ver [contracts/vecindad-y-cache.md](contracts/vecindad-y-cache.md)).

## Consulta de vecindad (FR-370 a FR-376)

| Campo | Tipo | Regla |
|---|---|---|
| `cripta_id` | str | la cripta debe existir; si no, el error es el vigente de `_cargar_esqueleto` |
| `numero_sala` | int | se valida con una búsqueda en el esqueleto, **después** de comprobar la profundidad (FR-373) |
| `profundidad` | int | `< 0` → `ValueError("La profundidad no puede ser negativa")`, sin búsquedas; `0` → `[]` |
| **respuesta** | list[int] | salas alcanzables en ≤ profundidad pasos, en orden de descubrimiento (nivel y, dentro de cada sala, N, S, E, O), sin repetir y sin la sala de partida |

**Estado interno durante una consulta (D1)**: no persiste entre consultas.

| Variable | Significado | Invariante |
|---|---|---|
| `alcanzadas` | lista de salas descubiertas; la posición 0 es la sala de partida | sin repetidos; su orden es el de la respuesta |
| `lectura` | índice de la próxima sala por expandir | `0 ≤ lectura ≤ len(alcanzadas)`; las salas de `[lectura, len)` forman la cola pendiente |
| `fin_nivel` | índice donde termina el nivel actual | las salas de `[.., fin_nivel)` tienen nivel ≤ `nivel` |
| `nivel` | nivel de la sala en `lectura` | sube en 1 cuando `lectura` alcanza `fin_nivel`, y entonces `fin_nivel = len(alcanzadas)` |

El recorrido termina cuando `lectura == len(alcanzadas)` o `nivel == profundidad`. Cada sala expandida cuesta exactamente una búsqueda en el esqueleto (FR-374).

## Entrada de la caché de fichas (D2)

| Campo | Tipo | Regla |
|---|---|---|
| `clave` | str | única dentro de la caché |
| `valor` | object | la ficha |
| `veces_en_uso` | int ≥ 0 | si es > 0, la entrada no se expulsa |

**Contenedor**: una lista propia de entradas ordenada de **menos a más reciente** (la más reciente al final).
- **Acierto o reinserción**: la entrada sale de su posición y va al final.
- **Inserción nueva con la caché llena**: se expulsa la primera entrada desde el inicio con `veces_en_uso == 0`. Si no hay ninguna, no se inserta y se devuelve `False`.
- **`claves()`** se lee desde el final, de la más reciente a la menos reciente, así que el resultado es el mismo que hoy.
- **Invariantes**: `len ≤ capacidad`, `aciertos + fallos` = llamadas a `obtener`.

## Fila de medición (FR-377 a FR-379)

| Campo | Tipo | Regla |
|---|---|---|
| `numero` | int | posición estable dentro del bloque; empareja M0, M1 y M2 aunque cambie el nombre de la fila |
| `bloque` | `cache` \| `guardado` | — |
| `seccion` | str | la sección del bloque |
| `medicion` | str | el nombre de la fila. Si cambia entre ejecuciones (por ejemplo «deque lineal» → «lista propia lineal»), se anota en `causa` |
| `tipo` | `cuenta` \| `tiempo` | según la tabla de D3 en [research.md](research.md) |
| `m0` | número o texto \| «sin antes en M0» | antes oficial |
| `m1` | número o texto | con la carga y el código vigente |
| `m2` | número o texto | después oficial |
| `diferencia` | absoluta y % | M2 − M0, o M2 − M1 si la fila no está en M0 |
| `causa` | texto | «carga: …» (M0 → M1), «código: …» (M1 → M2), «depende de la máquina» o «sin cambios» |
| `limite` | número | 2 × M0, o 2 × M1 para las filas nuevas (FR-383, FR-384) |
| `cumple` | sí/no | en las filas de tiempo, la mediana de tres ejecuciones (FR-383, FR-384) |

## Revisión de decisión (FR-380, FR-388)

| Campo | Regla |
|---|---|
| `decision` | una de: precarga (solo filas, FR-324), capacidad y búsqueda de la caché, catálogo en disco, formato binario de partida, planeación de la vecindad |
| `filas` | números de fila del después que la respaldan (al menos una) |
| `veredicto` | `se mantiene` \| `cambia` |
| `coincide_con_plan` | sí/no; si no, la medición que motivó el cambio |
| `nota_parte_i` | sección de `DOCUMENTACION_DECISIONES_DISENO.md` donde va la nota (2, 6 u 8) |

## Uso inventariado (FR-385, FR-386)

| Campo | Regla |
|---|---|
| `ubicacion` | archivo:línea o archivo y función |
| `estructura` | lo que se usa (por ejemplo, la cola de biblioteca o un dict) |
| `para_que` | qué hace |
| `problema_evaluado` | sí/no (§5: caché de fichas, planeación de la vecindad) |
| `destino` | `corregido` \| `justificado` \| `excluido (lectura de JSON)` |
| `texto` | justificación (qué hace, por qué no es índice ni caché, qué costaría corregirlo) o referencia a la decisión que lo corrige |

**Transición**: los usos que se corrigen pasan de `pendiente` a `corregido` cuando su prueba de equivalencia pasa y su bloque mide en M2. Los usos justificados pasan de `pendiente` a `justificado` cuando su texto está en `DECISIONES.md`.
