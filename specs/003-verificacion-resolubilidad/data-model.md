# Modelo de datos (Fase 1): Verificación de resolubilidad

Solo lo que se agrega o cambia. Lo que no aparece aquí (Parte I y capacidades 001, 005 y 009) no cambia. El formato de partida, `EstadoGuardadoDTO`, `AlmacenPartidaBinario` y `codec_partida` **no cambian** (son de la 010).

## 1. Cambio de contrato del mapa: la llave de cada puerta (PRIMERA TAREA)

Detalle y motivo en [research.md §1](research.md) y contrato en [contracts/mapa-con-llaves.md](contracts/mapa-con-llaves.md).

### `AristaMapaDTO` (`DTO/MapaDTO.py`, MODIFICADO)

| Campo | Tipo | Regla |
|---|---|---|
| `direccion` | `str` | Sin cambios |
| `destino` | `int` | Sin cambios |
| `costo` | `int` | Sin cambios |
| `cerrada_inicial` | `bool = False` | Sin cambios |
| **`llave`** | **`str \| None = None`** | **NUEVO**. Id de catálogo de la llave que abre la puerta de esta salida, tal como lo publica la API en la salida (`"llave"`). `None` si la API no lo trae (salida abierta o puerta sin llave). Va al final y con valor por defecto: quien construye con cuatro argumentos sigue funcionando |

### `AristaCripta` (`Logica/MapaCripta.py`, MODIFICADO)

`__slots__` pasa a `("origen", "direccion", "destino", "costo", "cerrada_inicial", "llave")`; el constructor recibe `llave: str | None = None` al final. `MapaCripta.__init__` lo copia de `AristaMapaDTO.llave`. Nada más del mapa cambia (`version_puertas`, `esta_abierta`, salientes y entrantes).

### Quién lo llena

| Origen | Cambio |
|---|---|
| `ServicioCripta.esqueleto()` | Pasa `datos.get("llave")` al construir cada `AristaMapaDTO` |
| `FuenteSoloLocal.esqueleto()` | Ninguno: delega en el `ServicioCripta` que envuelve. Se comprueba con prueba |
| `--offline` (`ClienteOffline` + `AlmacenDisco`) | Ninguno: las salas se guardan tal como llegan y `normalizar_esqueleto` copia cada salida completa. Se comprueba con prueba |
| API falsa v2 (`_puerta_con_llave`) | Ninguno: ya escribe `"llave"` en las dos salidas de la puerta |

**Invariante**: `llave` no cambia el estado de la puerta; una salida con `cerrada_inicial = False` y `llave` no `None` es una salida abierta (la llave solo importa si está cerrada).

## 2. Contrato del modelo (`Logica/FuenteCripta.py`, AMPLIADO)

| Operación | Devuelve | Implementan |
|---|---|---|
| `obtener_sala_inicial(cripta_id)` | `int`: `datos_cripta["sala_inicial"]` | `ServicioCripta`, `FuenteSoloLocal` (con `_leer(..., "los datos generales", ...)`) |
| `obtener_llave_salida(cripta_id)` | `str \| None`: `datos_cripta.get("llave_salida")` | Ídem |

Ninguna hace solicitudes nuevas: los datos generales se piden una vez por cripta y ya se piden al iniciar (Parte I).

## 3. `ResultadoVerificacion` (`DTO/ResultadoVerificacionDTO.py`, NUEVO)

Lo que devuelve la operación de verificación (FR-344). Es un `dataclass`; listas comunes, sin `dict` ni `set`.

| Campo | Tipo | Regla |
|---|---|---|
| `cripta_id` | `str` | Cripta verificada |
| `resoluble` | `bool \| None` | `True` resoluble, `False` no resoluble, `None` si hubo error de datos (FR-343) |
| `orden` | `list[PasoLlaveDTO]` | Solo si `resoluble`: orden válido de obtención de llaves, incluida la llave de salida (FR-336). Vacía en los otros casos |
| `salas_alcanzables` | `list[int]` | Ids en orden creciente. Si es resoluble, las alcanzables al completar; si no, todas las alcanzables (FR-337). Vacía si hubo error |
| `salas_no_alcanzables` | `int` | Salas que existen y no son alcanzables (FR-337). 0 si es resoluble o hubo error |
| `bloqueos` | `list[BloqueoDTO]` | Solo si no es resoluble: puertas que separan lo alcanzable de lo no alcanzable, por sala de origen creciente y N, S, E, O (FR-338) |
| `causas` | `list[str]` | Solo si no es resoluble: causas generales, en este orden fijo y sin repetir: `LLAVE_SALIDA_INEXISTENTE`, `SALIDA_SIN_CAMINO`, `SALIDA_BLOQUEADA`, `LLAVE_SALIDA_INALCANZABLE` ([research.md §6](research.md)) |
| `llave_salida` | `str \| None` | La de los datos generales, para el reporte |
| `sala_salida` | `int \| None` | Ídem |
| `motivo_error` | `str \| None` | Solo si `resoluble is None`: mensaje claro que nombra la cripta y el motivo |

**Operación**: `codigo_salida() -> int`: 0 si `resoluble is True`, 1 si `resoluble is False`, 2 si `resoluble is None` (FR-331).

**Invariantes**:

- `resoluble is None` ⇔ `motivo_error is not None`; en ese caso `orden`, `salas_alcanzables`, `bloqueos` y `causas` están vacías.
- `resoluble is True` ⇒ la llave de salida figura **exactamente una vez** en `orden` (en cualquier posición, según su oleada); `bloqueos` y `causas` vacías.
- `resoluble is False` ⇒ `orden` vacía y `causas` no vacía.
- Cada id de llave aparece como máximo una vez en `orden`.
- Dos verificaciones de los mismos datos dan resultados iguales campo por campo (FR-335).

### `PasoLlaveDTO`

| Campo | Tipo | Regla |
|---|---|---|
| `llave` | `str` | Id de la llave |
| `sala` | `int` | Sala donde se obtiene: la del suelo o la sala inicial del enemigo (FR-334). Si en la oleada es obtenible desde varias salas, la menor |
| `enemigo` | `str \| None` | Instancia del enemigo que la suelta, o `None` si está en el suelo. Con suelo y enemigo en la misma sala, `None`; entre enemigos, la menor instancia |

### `BloqueoDTO`

| Campo | Tipo | Regla |
|---|---|---|
| `sala_origen` | `int` | Sala alcanzable desde la que sale la puerta |
| `direccion` | `str` | `norte`, `sur`, `este` u `oeste` |
| `sala_destino` | `int` | Sala no alcanzable |
| `llave` | `str \| None` | Llave que pide la puerta; `None` si no tiene |
| `salas_de_la_llave` | `list[int]` | Salas de las ubicaciones de esa llave, en orden creciente y sin repetir; vacía si no existe |
| `tipo` | `str` | `SIN_LLAVE`, `LLAVE_INEXISTENTE`, `CICLO` o `LLAVE_SIN_CAMINO` ([research.md §6](research.md)) |

## 4. Estructuras internas de la verificación (`Logica/VerificacionResolubilidad.py`, `Logica/IndiceLlaves.py`)

Viven solo durante una llamada; no se guardan ni entran al log.

| Estructura | Forma | Tamaño | Uso |
|---|---|---|---|
| `IndiceLlaves` | lista de ids ordenada con `ordenar_adaptativo`, sin repetidos; `numero(id)` por búsqueda binaria propia (−1 si no está); `id_de(numero)` | K | Ids de texto → número denso 0..K−1, con el orden de los ids |
| `alcanzable` | `list[bool]` por id de sala | S | Sala ya alcanzada |
| `frontera` | `ColaCircular` | ≤ S | Salas por examinar en la oleada |
| `obtenible`, `obtenida` | `list[bool]` por número de llave | K | Llave con ubicación alcanzable / ya pasada al orden |
| `ubicaciones_por_sala` | `list[list[int]]` por id de sala (posiciones en `UbicacionLlavesDTO`) | S + L | Qué llaves aparecen al alcanzar una sala |
| `ubicaciones_por_llave` | `list[list[int]]` por número de llave | K + L | Elegir sala y enemigo del paso; salas de la llave en un bloqueo |
| `esperando` | `list[list[AristaCripta]]` por número de llave | K + E | Puertas cerradas desde salas alcanzables que esperan esa llave |
| `pendientes` | `MonticuloMinimo` con `(id de sala, número de llave)` | ≤ L | Llaves obtenibles de la oleada en curso, en orden de FR-335 |

Ningún `dict`, `set`, `heapq`, `bisect`, `collections`, `sorted()` ni `.sort()`.

## 5. Estado de la partida (`Logica/EstadoJuegoLogica.py`, MODIFICADO)

| Atributo | Inicial (`__init__`) | Se fija en | Se reinicia en |
|---|---|---|---|
| `resultadoVerificacion` | `None` | `iniciarJuego` cuando hay llaves | Al empezar `iniciarJuego` y al restaurar una partida |
| `avisoResolubilidad` | `None` | `iniciarJuego` con `forzar=True` y cripta no resoluble: `aviso_forzado(resultado)`; o, si la verificación dio error de datos, el `motivo_error` seguido de «La verificación de resolubilidad no está disponible.» (mismo final que el aviso de FR-313) | Ídem |

No entran al `partida.log` ni al estado guardado. La restauración (`EstadoGuardadoLogica.restaurar`) solo los pone en `None`, igual que `llaves` y `avisoLlaves` (009).

### Transiciones de `iniciarJuego(cripta, semilla, pedir_llaves=True, forzar=False)`

```text
pedir_llaves=False ─────────────────────────────────────────────► iniciada, sin verificar
pedir_llaves=True ─► obtenerLlaves()
   llaves = None (FR-313) ──────────────────────────────────────► iniciada, avisoLlaves
   llaves presentes ─► verificar(fuente, cripta, llaves)
       resoluble = True ────────────────────────────────────────► iniciada, sin aviso
       resoluble = False, forzar ───────────────────────────────► iniciada, avisoResolubilidad
       resoluble = False, sin forzar ─► CriptaNoResoluble ──────► NO iniciada (iniciado=False, sin log)
       resoluble = None (error de datos) ───────────────────────► iniciada, avisoResolubilidad = aviso con motivo_error
```

El último caso (llaves presentes pero, por ejemplo, la sala de salida no existe en el esqueleto) sigue la regla de FR-339: sin datos para verificar, la partida no se bloquea y se avisa.

## 6. Errores (`Logica/VerificacionResolubilidad.py`, NUEVO)

| Error | Hereda de | Cuándo | Mensaje |
|---|---|---|---|
| `CriptaNoResoluble` | `RuntimeError` | `iniciarJuego` sin `forzar` y cripta no resoluble (FR-339) | Las líneas de `lineas_reporte(resultado)` unidas con salto de línea. Atributo `resultado` con el `ResultadoVerificacion` |

## 7. Datos sintéticos del bench (`tests_labs/cripta_sintetica.py`, AMPLIADO)

`esqueleto_llaves_encadenadas(n, semilla) -> (esqueleto, llaves, llave_salida, sala_salida)`: pasillo de n salas y n salas laterales; la puerta i → i+1 (en los dos sentidos) se abre con `k_<j>`, ubicada en la lateral de la sala i; los nombres `j` y el orden de las laterales se barajan con `random.Random(semilla)`. La llave de salida está en la lateral de la última sala. Determinista por semilla; ningún tamaño fijo (principio V). Detalle en [contracts/bench-resolubilidad.md](contracts/bench-resolubilidad.md).
