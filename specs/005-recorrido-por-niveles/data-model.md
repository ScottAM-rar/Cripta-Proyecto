# Modelo de datos (Fase 1): Recorrido por niveles

Solo lo que se agrega o cambia. Las entidades de la Parte I y de la capacidad 001 no mencionadas aquí no cambian.

## Entidades nuevas

### RecorridoDTO (`DTO/RecorridoDTO.py`)

Resultado de un recorrido: las salas visitadas, en orden, con su nivel.

| Campo | Tipo | Regla |
|---|---|---|
| `salas` | lista de enteros | Ids de sala en el orden de visita. El primero es el origen. Sin repetidos (FR-503) |
| `niveles` | lista de enteros | `niveles[i]` es el nivel de `salas[i]`. Mismo largo que `salas`. No decrece; dentro de un mismo nivel `salas` crece estrictamente (FR-501, FR-502) |

Invariantes: `salas[0]` es el origen y `niveles[0] == 0`; si hubo límite L, todo `niveles[i] <= L` (FR-504); ninguna sala sin camino desde el origen aparece (FR-505).

### ColaCircular (`Logica/ColaCircular.py`)

Cola de enteros sobre una `list`.

| Elemento | Descripción |
|---|---|
| Almacén | `list` de capacidad fija; al llenarse se duplica y los elementos se copian en orden desde la cabeza |
| Cabeza y tamaño | Índice del siguiente a sacar y cantidad de elementos; la posición de cola se deduce de ambos con módulo |
| Capacidad inicial | Pequeña (16); no depende de ninguna cripta |
| Operaciones | `agregar(valor)`, `sacar()` (falla con `IndexError` si está vacía), `vacia()`, `vaciar()`, longitud |

Orden FIFO estricto. No usa `deque` ni `collections`.

### RecorridoPorNiveles (`Logica/RecorridoPorNiveles.py`)

Servicio de recorrido asociado a un `MapaCripta`. Se crea una vez por mapa y se reutiliza.

| Campo | Tipo | Regla |
|---|---|---|
| `mapa` | `MapaCripta` | Fuente de las aristas salientes. Solo se lee |
| `_marca` | lista de enteros, tamaño `mapa.tamano` | Época en que se visitó cada sala. 0 = nunca |
| `_nivel` | lista de enteros, tamaño `mapa.tamano` | Nivel de la sala; solo vale si `_marca` es la época actual |
| `_epoca` | entero | Sube en 1 en cada recorrido |
| `_cola` | `ColaCircular` | Contiene el nivel en curso |
| `salas_visitadas` | entero | Salas que visitó el **último** recorrido. Se pone en 0 al empezar cada recorrido |
| `salidas_examinadas` | entero | Salidas que examinó el **último** recorrido: las salientes de cada sala visitada cuyo nivel es menor que el límite, se haya recorrido o no la salida (no transitable, ya visitada, hacia sí misma o hacia una sala inexistente). Las salidas de las salas con nivel igual al límite no se cuentan. Se pone en 0 al empezar cada recorrido |

Operación pública: `recorrer(origen, limite=None, transitable=None) -> RecorridoDTO`. Detalle en `contracts/interfaz-recorrido.md`.

**Validaciones** (se citan verbatim para que no queden al criterio de quien implemente):

- `origen`: "ha de existir en el esqueleto"; si no, `ValueError` (FR-512).
- `limite`: "entero mayor o igual que 0, o ausente"; un booleano, un negativo o un no entero se rechazan con `ValueError` (FR-504).
- `transitable`: "función que recibe una arista y devuelve verdadero o falso", o ausente (todas las salidas son transitables, FR-507).
- Una salida hacia una sala que no existe: se ignora; esa sala no aparece y el recorrido no se rechaza (FR-513).

## Entidades existentes que cambian

### MapaCripta (`Logica/MapaCripta.py`, capacidad 001)

| Campo | Tipo | Regla |
|---|---|---|
| `existe` (nuevo) | lista de booleanos, tamaño `tamano` | `existe[i]` es verdadero si el esqueleto tiene una sala con id `i`. Sirve para FR-512 (origen inexistente) y FR-513 (ignorar salidas hacia salas inexistentes) |

El resto de `MapaCripta` (aristas salientes y entrantes, `esta_abierta`) no cambia.

## Estados y transiciones

| Estado | Cambia por | Efecto |
|---|---|---|
| `_epoca` | cada llamada a `recorrer` | Invalida en O(1) todas las marcas anteriores |
| `_cola` | durante `recorrer` | Termina vacía; queda lista para el siguiente recorrido. Si `recorrer` falla a mitad (por ejemplo, el criterio de transitabilidad lanza una excepción), se vacía antes de propagar el error |

El recorrido no guarda ni reutiliza resultados entre llamadas: lo que se reutilizan son los buffers.

## Persistencia

Ninguna. No cambia el formato de partida ni la caché; no hay versiones que subir.
