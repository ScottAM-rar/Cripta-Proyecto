# Modelo de datos (Fase 1): Terreno y cazador

Solo lo que cambia o se agrega. Las entidades de la Parte I no mencionadas aquí no cambian.

## Entidades existentes que reciben campos

### SalidaDTO (`DTO/SalaDTO.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `costo` (nuevo) | entero ≥ 1 | Por defecto 100 (FR-101). Inválido (cero, negativo, no entero, booleano) → 100 con advertencia. Estático durante la partida. |

Los demás campos (`direccion`, `sala_destino`, `cerrada`, `llave`, `cierre_automatico`) no cambian. `cerrada` es el **único estado mutable** que afecta a los cazadores y solo se modifica por el punto único de cambio de puertas.

### EnemigoCatalogoDTO y EnemigoDTO (`DTO/CatalogoDTO.py`, `DTO/ActorDTO.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `rango` (nuevo) | entero ≥ 0 | Por defecto 0. Solo se usa si `comportamiento == "cazador"`. Ausente o inválido → 0 con advertencia; 0 declarado es válido (FR-108). |

`comportamiento` admite ahora el valor `"cazador"`; la fábrica lo reconoce. Un valor desconocido sigue produciendo el error actual.

### ResultadoEventoDTO (`DTO/ResultadoEventoDTO.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `costo` (nuevo) | entero ≥ 1 o ausente | Costo de la acción realizada. Lo informa el movimiento (costo de la salida). Ausente = no aplica. |

## Entidades nuevas

### AccionEnemigoDTO (`DTO/AccionEnemigoDTO.py`)

Resultado de la decisión de un enemigo en su turno.

| Campo | Tipo | Regla |
|---|---|---|
| `mensaje` | texto | El mismo texto que hoy devolvían los comportamientos. |
| `costo` | entero ≥ 1 | Costo de la acción: el de la salida cruzada si se movió; 100 si esperó, atacó o no se movió (FR-107). |

### MapaDTO (`DTO/MapaDTO.py`)

Esqueleto completo tal como lo entrega la fuente de datos, sin contenido de salas.

| Campo | Tipo | Regla |
|---|---|---|
| `salas` | lista de registros de sala, posición = id | Una entrada por sala del esqueleto. |
| cada salida | `(destino, costo, cerrada_inicial)` en orden N, S, E, O | `costo` ya normalizado (≥ 1). |
| `advertencias` | lista de textos | Costos y rangos inválidos encontrados al leer. |

### MapaCripta (`Logica/MapaCripta.py`)

Vista de lectura sobre el esqueleto, construida una vez.

| Elemento | Descripción |
|---|---|
| Aristas salientes por sala | Para cada sala, sus salidas con destino y costo, en orden de dirección. |
| Aristas entrantes por sala | Para cada sala, las salidas de otras salas que llegan a ella, con su costo y un puntero a la salida de origen para leer el estado real de la puerta. |
| Estado de puerta | Se consulta sobre el `SalidaDTO` de la sala cargada; si la sala no está cargada, se usa `cerrada_inicial`. |

Invariantes: cantidad de salas = longitud del esqueleto; ningún id ni cantidad fijos en el código; no se guardan diccionarios.

### CampoDeCostos (`Logica/CampoDeCostos.py`)

Costo mínimo hacia la sala del jugador, acotado.

| Campo | Descripción |
|---|---|
| `origen` | Sala del jugador con la que se calculó. |
| `cota` | Mayor costo explorado (mayor rango consultado). |
| `costos` / `marcas` | Dos listas de tamaño N; un costo solo vale si su marca es la época actual. |
| `epoca` | Contador que sustituye a limpiar las listas. |
| `version_puertas` | Contador de cambios de puertas con el que se calculó el campo. |

Operaciones: `costo_hasta_jugador(sala)` → costo o "fuera de alcance"; `invalidar(...)` por evento (tabla en `research.md` §4).

### ComportamientoCazador (`Logica/CompCazador.py`)

Sin estado propio y sin azar. Orden de decisión, por regla de la especificación:

1. Misma sala que el jugador → ataca (FR-110).
2. Si no, obtiene `d` del campo para su sala (FR-111). Sin ruta, o `d` > rango → espera con costo 100 (FR-112).
3. Si no, entre las salidas abiertas de su sala `u` hacia `v` con `costo(u,v) + costo_hasta_jugador(v) == d`, elige el menor id de `v` (FR-114), cruza y devuelve el costo de esa salida (FR-113).

Las puertas cerradas nunca se abren (FR-115). El estado de las puertas se lee en el instante de decidir (FR-109, FR-116).

## Transiciones de estado relevantes

| Estado | Cambia por | Efecto en el campo |
|---|---|---|
| `SalidaDTO.cerrada` | abrir (jugador), cierre automático, deshacer con pergamino, restaurar partida | Ver tabla de invalidación |
| Sala del jugador | movimiento, deshacer con pergamino, restaurar partida | Invalida |
| Activación de un cazador | el jugador entra a su sala | Si su rango > cota, recalcula con cota mayor |

## Persistencia

Ver `contracts/formato-partida.md`. El cazador no guarda estado propio: su decisión se deduce del mundo en cada turno, por lo que no hay estado aleatorio que guardar (principio II).
