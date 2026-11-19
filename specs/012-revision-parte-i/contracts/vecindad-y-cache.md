# Contrato: planeación de la vecindad y caché de fichas (lo que NO cambia)

Las dos interfaces se conservan tal cual. Este contrato fija el comportamiento observable que las pruebas D4 comparan contra la versión vigente (`0b031ec`).

## `ServicioCripta.salas_vecinas(cripta_id: str, numero_sala: int, profundidad: int = 1) -> list[int]`

| Caso | Resultado | Búsquedas en el esqueleto | Descargas del esqueleto |
|---|---|---|---|
| `profundidad < 0` | `ValueError("La profundidad no puede ser negativa")` | 0 | 0 |
| la cripta no existe (con profundidad ≥ 0) | `ValueError` de `_cargar_esqueleto` («La cripta '…' no existe») | 1 (la llamada de validación falla dentro de la carga) | 0 |
| la sala no existe (con profundidad ≥ 0) | `ValueError("La cripta '…' no tiene la sala …")` | 1 | ≤ 1, solo la primera vez por cripta |
| `profundidad == 0` | `[]` | 1 | ≤ 1 |
| `profundidad ≥ 1` | salas en orden de descubrimiento: por nivel y, en cada sala, salidas N, S, E, O (`_LETRAS_EN_ORDEN`); sin repetir y sin `numero_sala`. Se siguen todas las salidas, aunque la puerta esté cerrada | 1 + (salas de nivel < profundidad) | ≤ 1 |

**Quién la llama** (sin cambios): `precargar_vecinas` (con profundidad 1 y con `alcance`) y los scripts de `tests_labs/`. **No se modifica** `precargar_vecinas` (FR-324).

**Principio I (FR-375)**: el código del método no menciona `deque`, `collections`, `heapq`, `bisect`, `set`, `dict(` ni `sorted`/`.sort`. Se comprueba sobre el código fuente del método, no sobre el archivo, porque `_armar_salidas` seguía usando la cola de biblioteca (uso justificado entonces). Desde la corrección L3 (FR-389, T048) usa una lista y el archivo ya no importa `collections`.

## `CacheLRU` (`adaptadores/cache.py`)

La interfaz pública no cambia: `CacheLRU(capacidad=25)`, `len`, `capacidad`, `aciertos`, `fallos`, `claves()`, `obtener(clave)`, `insertar(clave, valor)`, `marcar_en_uso(clave)`, `marcar_libre(clave)`, `establecer_en_uso(claves)` y `en_uso(clave)`.

| Operación | Resultado observable (igual que hoy) |
|---|---|
| `CacheLRU(c)` con `c < 1` | `ValueError("La capacidad de la caché debe ser al menos 1")` |
| `obtener(k)`, si k no está | `None`; `fallos += 1`; el orden no cambia |
| `obtener(k)`, si k está | el valor; `aciertos += 1`; k pasa a ser la más reciente |
| `insertar(k, v)`, si k ya está | reemplaza el valor, k pasa a ser la más reciente y devuelve `True`; no expulsa nada |
| `insertar(k, v)`, si k es nueva y hay lugar | k entra como la más reciente y devuelve `True` |
| `insertar(k, v)`, si k es nueva y la caché está llena | expulsa la **menos reciente que no está en uso** y después hace lo anterior. Si todas están en uso, no inserta y devuelve `False` |
| `claves()` | de la más reciente a la menos reciente |
| `marcar_en_uso`, `marcar_libre`, `establecer_en_uso`, `en_uso` | igual que hoy (`marcar_libre` no baja de 0; `establecer_en_uso` recalcula desde cero contando las repeticiones) |
| `len(cache)` | ≤ `capacidad`, siempre |

**Principio I**: el módulo no importa `collections` ni ninguna otra cosa de la lista.
