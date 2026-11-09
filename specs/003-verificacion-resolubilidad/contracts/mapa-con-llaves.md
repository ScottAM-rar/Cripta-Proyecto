# Contrato: la llave de cada puerta en el mapa (cambio de contrato del mapa)

Primera tarea de la capacidad. Motivo y alternativas en [../research.md §1](../research.md); campos en [../data-model.md §1](../data-model.md).

## Entrada: salida del esqueleto de la API

```json
{"id": 2, "salidas": {"S": {"sala": 1},
                      "E": {"sala": 5, "cerrada": true, "llave": "itm_llave_bronce", "cierre_automatico": 500}}}
```

`llave` es opcional. Puede venir en una salida cerrada (lo normal) o abierta (se conserva igual, no cambia nada). `cierre_automatico` no es de esta capacidad y se sigue ignorando en el mapa.

## Salida: `AristaMapaDTO` y `AristaCripta`

```python
AristaMapaDTO(direccion="este", destino=5, costo=100, cerrada_inicial=True, llave="itm_llave_bronce")
AristaMapaDTO(direccion="sur", destino=1, costo=100)            # llave=None, cerrada_inicial=False: como hoy
AristaCripta(2, "este", 5, 100, True, "itm_llave_bronce")
AristaCripta(2, "sur", 1, 100, False)                           # llave=None: como hoy
```

## Garantías

| # | Garantía | Prueba (`test_mapa_con_llaves.py`) |
|---|---|---|
| G1 | `ServicioCripta.esqueleto()` copia `llave` de cada salida que la trae y deja `None` en las demás | Con la API falsa v2 (`_b_r3`): las salidas 1→4 y 4→1 traen `itm_llave_a`; 1→2 trae `None` |
| G2 | `MapaCripta` copia `llave` a `AristaCripta` | Mismo caso, leyendo `mapa.salidas(1)` |
| G3 | `--offline` entrega las mismas llaves que el cliente con red | Guardar con `ClientePersistente` sobre la API falsa y leer con `ClienteOffline` |
| G4 | `FuenteSoloLocal.esqueleto()` entrega las mismas llaves, sin solicitudes | Ídem, contador sin cambios |
| G5 | Quien construye aristas sin `llave` sigue funcionando | Construcción con cuatro y cinco argumentos posicionales; la suite de la 001 y la 005 sigue pasando |
| G6 | Sin solicitudes nuevas | El contador de solicitudes del esqueleto no cambia respecto de antes del cambio |

## Lo que no cambia

El formato de `cripta_<id>.bin` (el esqueleto crudo ya guardaba `llave`), el formato de partida, `version_puertas`, `esta_abierta`, el campo de costos de la 001 y el recorrido de la 005 (que no miran `llave`).
