# Modelo de datos: Niebla de guerra y mapa conocido

**Especificación**: [spec.md](spec.md) | **Decisiones**: [research.md](research.md)

N es el mayor id de sala más uno (los ids van desde 1; la posición 0 no se usa), el mismo `tamano` de `MapaCripta`.

## Estructuras en memoria (`Logica/MapaConocido.py`)

| Campo | Tipo | Tamaño | Significado |
|---|---|---|---|
| `estado` | lista de enteros | N | Estado de cada sala: 0 desconocida, 1 avistada, 2 explorada |
| `puertas` | lista de enteros | 4·N | Puerta recordada de la salida `(sala, d)` en la posición `sala*4 + d`: 0 sin observar, 1 abierta, 2 cerrada |
| `exploradas` | lista de enteros | k | Ids de las salas exploradas en orden de descubrimiento |
| `nombres` | lista de textos | N | Nombre de cada sala del esqueleto; solo se muestra el de las exploradas |
| `version_conocimiento` | entero | 1 | Sube con cada cambio de `estado` o `puertas`, también al deshacer |
| `salas_reveladas`, `salidas_examinadas` | enteros | 2 | Del último `entrar`; para pruebas por conteo y `--bench` |

Direcciones: `d` = 0 norte, 1 sur, 2 este, 3 oeste (el orden N, S, E, O del esqueleto).

Dependencias recibidas (no importa red, disco ni vista): `MapaCripta` (esqueleto, sin modificar), la lista de salas del modelo (para `esta_abierta`), el jugador (su sala actual y su antorcha) y una función para registrar cambios en el historial del pergamino.

## Invariantes

Valen tras cada operación (incluido deshacer y restaurar). Las pruebas las comprueban con un verificador que recorre todo.

| # | Invariante | Requisito |
|---|---|---|
| I1 | Para toda salida adyacente a la sala del jugador (propia o entrante), la puerta recordada es igual a la real | FR-207 |
| I2 | `estado[s] == 2` si y solo si `s` está en `exploradas`, y no hay repetidas | FR-201 |
| I3 | `estado[s] == 1` si y solo si `s` no está explorada y es destino de una salida de una sala explorada | FR-203 |
| I4 | La sala del jugador está explorada | FR-204 |
| I5 | `puertas[sala*4+d] != 0` solo si existe esa salida en el esqueleto | FR-206 |
| I6 | Una puerta nunca observada vale 0 y se muestra «sin observar»; la antorcha no la cambia | FR-209 |

Observar al entrar a `S` también anota las salidas **entrantes** a `S` cuyo origen puede ser una sala solo avistada. Esa memoria existe pero **no se muestra** hasta que el origen esté explorado (el mapa lista solo salidas de salas exploradas), y evita perder lo visto.

## Estados de una sala y transiciones

```text
desconocida --(destino de una salida de una sala que pasa a explorada)--> avistada
desconocida --(entrar la antorcha, o entrar el jugador)-------------------> explorada
avistada    --(entrar la antorcha, o entrar el jugador)-------------------> explorada
explorada   ---------------------------------------------------------------> (sin salida)
```

Solo el pergamino retrocede una transición, y siempre una acción completa a la vez (FR-205, FR-214). El estado de partida nueva es: sala inicial explorada, sus destinos avistados, el resto desconocido (FR-202), sin cambios deshacibles.

| Evento | Cambia |
|---|---|
| Instante 0 | Explora la sala inicial, avista sus destinos, observa sus puertas. **No** se registra |
| El jugador entra a `S` sin antorcha | `S` explorada; destinos de `S` avistados; puertas de `S` y entrantes a `S` observadas |
| El jugador entra a `S` con antorcha | Lo anterior, y cada destino `V` de `S` explorada; destinos de cada `V` avistados. Sin observar puertas de `V` |
| Reentrar a una sala explorada | Solo las puertas cuyo estado real difiere del recordado |
| Puerta cambia adyacente al jugador | `puertas[...]` pasa al estado nuevo |
| Puerta cambia lejos | Nada |
| Encender o apagar la antorcha | Nada |
| Consultar el mapa | Nada (FR-218) |
| Deshacer con el pergamino | Se revierten los cambios de la acción en orden inverso |

## Cambios deshacibles (`CambioDTO`)

Contrato completo en [contracts/cambios-deshacibles.md](contracts/cambios-deshacibles.md).

| `tipo_accion` | `objeto_afectado` | `indice` | `valor_anterior` | `valor_nuevo` |
|---|---|---|---|---|
| `EXPLORAR_SALA` | el `MapaConocido` | id de la sala | 0 o 1 | 2 |
| `AVISTAR_SALA` | el `MapaConocido` | id de la sala | 0 | 1 |
| `OBSERVAR_PUERTA` | el `MapaConocido` | `sala*4 + d` | 0, 1 o 2 | 1 o 2 |

## DTO de lo que ve la vista (`DTO/ConocimientoDTO.py`)

Instantáneas de solo lectura, sin referencias al mapa completo ni a las salas del modelo.

| DTO | Campos |
|---|---|
| `MapaConocidoDTO` | `sala_actual` (id), `salas`: lista de `SalaConocidaDTO` en orden ascendente de id |
| `SalaConocidaDTO` | `id`, `nombre`, `salidas`: lista de `SalidaConocidaDTO` en el orden en que la sala las declara |
| `SalidaConocidaDTO` | `direccion`, `costo`, `puerta` (`"abierta"`, `"cerrada"` o `"sin observar"`), `destino_explorado` (booleano), `destino_id` y `destino_nombre` (solo si `destino_explorado`; si no, vacíos) |

Por construcción, una sala avistada solo existe como `destino_explorado = False`: no hay campo donde caber su id, su nombre ni su contenido, y dos salidas hacia la misma sala avistada son indistinguibles (FR-219).

## Estado guardado

Contrato completo en [contracts/estado-guardado-niebla.md](contracts/estado-guardado-niebla.md).

| DTO guardado | Campos |
|---|---|
| `ConocimientoGuardadoDTO` | `exploradas` (ids, orden de descubrimiento), `avistadas` (ids ascendentes), `puertas` (lista de `PuertaRecordadaDTO`, ascendente por sala y dirección) |
| `PuertaRecordadaDTO` | `sala`, `direccion` (0 a 3), `cerrada` (booleano) |

Solo se guardan las puertas observadas (las 0 se omiten). `EstadoGuardadoDTO.conocimiento` va al final de la clase.

## Validaciones

| Dónde | Regla | Resultado |
|---|---|---|
| Al restaurar | Todo id está entre 1 y el mayor id y existe en el esqueleto | `ValueError` («archivo corrupto»), sin tocar la partida |
| Al restaurar | `exploradas` sin repetidos; `avistadas` disjunta de `exploradas` | ídem |
| Al restaurar | `avistadas` coincide con las derivadas de `exploradas` (I3) | ídem |
| Al restaurar | La sala del jugador está explorada (I4) | ídem |
| Al restaurar | Cada puerta guardada nombra una salida que existe (I5) | ídem |
| `entrar` | La sala existe en el esqueleto | `ValueError` (error de programación, no de juego) |
| `deshacer` | La sala quitada de `exploradas` es la última de la lista | `ValueError` (indica un orden de deshacer roto) |
| Versión | Archivo sin niebla (versión anterior) | Rechazo con versión encontrada y esperada (FR-221) |
