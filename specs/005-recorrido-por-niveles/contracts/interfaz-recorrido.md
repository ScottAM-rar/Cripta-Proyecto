# Contrato: cómo se pide un recorrido y qué devuelve

Interfaz interna de la capa de lógica. La usarán después la precarga de vecinas y la verificación de resolubilidad; en esta capacidad solo la usan las pruebas y `--bench`.

## Petición

`recorrer(origen, limite=None, transitable=None)`

| Parámetro | Obligatorio | Valores aceptados | Si no cumple |
|---|---|---|---|
| `origen` | sí | id de una sala que existe en el esqueleto | `ValueError` (FR-512) |
| `limite` | no | entero no booleano, mayor o igual que 0 | `ValueError` que nombra el valor recibido (FR-504) |
| `transitable` | no | función `arista -> verdadero/falso`; la arista expone `origen`, `direccion`, `destino`, `costo` y `cerrada_inicial` | — |

Si `transitable` es `None`, todas las salidas existentes son transitables (FR-507). Para tener en cuenta el estado actual de las puertas, quien invoca pasa una función que consulta `MapaCripta.esta_abierta`.

## Respuesta

Un `RecorridoDTO` con dos listas paralelas `salas` y `niveles` (ver `data-model.md`).

## Garantías

| Garantía | Requisito |
|---|---|
| Orden creciente de nivel; el origen primero, en el nivel 0 | FR-501 |
| Dentro de un nivel, ids estrictamente crecientes | FR-502 |
| Cada sala una sola vez, en el nivel de su camino más corto | FR-503 |
| Ninguna sala con nivel mayor que `limite` | FR-504 |
| Ninguna sala sin camino desde el origen por salidas transitables | FR-505 |
| Las salidas de un solo sentido se recorren solo en su sentido | FR-506 |
| Solo se recorren salidas transitables | FR-507 |
| Sin salidas transitables, solo el origen | FR-508 |
| Misma cripta, origen, límite y criterio ⇒ misma secuencia | FR-509 |
| Costo proporcional a lo visitado, no a N | FR-510 |

## Lo que el recorrido NO hace

- No pide nada a la red ni al disco.
- No modifica el mapa, las salas ni las puertas.
- No usa los costos de las salidas (capacidad 001): el nivel cuenta salidas.
- No guarda resultados entre llamadas.
