# Contrato: cambios de conocimiento deshacibles

**Consumen**: JP y Scott (entrega el 6 de noviembre). **Produce**: `Logica/MapaConocido.py`. **Requisitos**: FR-214, FR-215, FR-225.

Este contrato fija qué `CambioDTO` registra el conocimiento, cómo se revierten y qué puede suponer quien consuma el historial (reversión, línea de tiempo, guardado). No dice cómo se implementa cada paso.

## 1. Los tres cambios

Todos usan el `CambioDTO` existente. Campos que usa cada uno:

| `tipo_accion` | `objeto_afectado` | `indice` | `valor_anterior` | `valor_nuevo` | Qué representa |
|---|---|---|---|---|---|
| `EXPLORAR_SALA` | el `MapaConocido` de la partida | id de la sala | 0 (desconocida) o 1 (avistada) | 2 | La sala pasa a explorada |
| `AVISTAR_SALA` | el `MapaConocido` | id de la sala | 0 | 1 | La sala desconocida pasa a avistada |
| `OBSERVAR_PUERTA` | el `MapaConocido` | `sala*4 + d` (`d`: 0 norte, 1 sur, 2 este, 3 oeste) | 0 sin observar, 1 abierta o 2 cerrada | 1 abierta o 2 cerrada | Lo recordado de la salida `(sala, d)` cambia |

Reglas de registro:

1. **Solo se registra un cambio real.** `valor_anterior != valor_nuevo`. Volver a entrar a una sala explorada con las puertas igual que se recordaban no registra nada (no se abre ningún nodo).
2. **Un solo nodo por causa.** Entrar a una sala registra **una** llamada a `registrar_cambio` con la lista completa de sus cambios, en este orden: `EXPLORAR_SALA` de la sala, sus `AVISTAR_SALA`, sus `OBSERVAR_PUERTA`, y —con antorcha— por cada vecina su `EXPLORAR_SALA` seguido de sus `AVISTAR_SALA`. Un cambio de puerta junto al jugador registra una llamada con un solo `OBSERVAR_PUERTA`.
3. **Se registra dentro de la acción del jugador en curso.** Los cambios producidos por eventos que ocurren hasta la siguiente decisión del jugador (por ejemplo, un cierre automático) quedan en el grupo de la última acción, como los demás cambios del juego.
4. **El conocimiento del instante 0 y el restaurado de un archivo no se registran** (FR-215): no hay acción abierta, y `registrar_cambio` ya ignora la llamada.

## 2. Cómo se revierten

`PergaminoLogica._revertir_cambio` trata los tres tipos con una sola rama que delega en el conocimiento:

```text
EXPLORAR_SALA | AVISTAR_SALA | OBSERVAR_PUERTA  ->  cambio.objeto_afectado.deshacer(cambio)
```

`MapaConocido.deshacer(cambio)`:

| Tipo | Efecto |
|---|---|
| `EXPLORAR_SALA` | `estado[sala] = valor_anterior`; quita `sala` del **final** de la lista de exploradas (debe ser la última; si no, `ValueError`) |
| `AVISTAR_SALA` | `estado[sala] = valor_anterior` (0) |
| `OBSERVAR_PUERTA` | `puertas[indice] = valor_anterior` |

En los tres casos sube `version_conocimiento`. **No se registra ningún cambio nuevo al deshacer.**

### Orden

`RetrocesoLogica` saca los nodos del final de su lista, y `PergaminoLogica.aplicar_cambios` recorre los `CambioDTO` de cada nodo en orden inverso. Por eso cada `EXPLORAR_SALA` se deshace después de los `AVISTAR_SALA` que registró detrás, y la sala explorada más reciente es siempre la última de la lista. **Quien cambie ese orden rompe el contrato.**

### El aviso de puertas del pergamino no observa

Deshacer un `CAMBIAR_PUERTA` vuelve a pasar por `fijar_cerrada`, que llama al aviso. Ese aviso, cuando lo dispara el pergamino, **solo** invalida el campo de costos de los cazadores; **no** debe llegar a `MapaConocido.puerta_cambio`. La memoria de puertas se restaura únicamente con los `OBSERVAR_PUERTA` de la acción. Los avisos de las acciones hacia adelante (abrir, cerrar, cierre automático) llegan a ambos.

## 3. Qué garantiza a quien consume

1. **Reversión exacta.** Tras `usar_pergamino`, el conocimiento (`estado`, `puertas`, `exploradas`) es idéntico al que había antes de la acción deshecha, incluidas las salas exploradas por la antorcha (SC-003). Probado contra una referencia que reconstruye el conocimiento desde cero.
2. **Costo proporcional a los cambios.** Registrar y revertir cuestan O(r), con r la cantidad de cambios de la acción; no dependen del tamaño del mapa conocido ni de la cripta (FR-225).
3. **Sin copia del conocimiento.** Ningún `CambioDTO` contiene los arreglos.
4. **Las acciones que `recortar_historial` descarta no se deshacen.** Lo descubierto en ellas queda como conocimiento permanente.
5. **Una acción rechazada** (sin éxito) se descarta con `descartar_accion`, que aplica los cambios en orden inverso; el conocimiento queda como antes de intentarla.
6. **`version_conocimiento` es monótona** y sube con cada cambio, adelante o atrás: quien guarde un cálculo sobre el conocimiento (la futura 006) puede compararla.

## 4. Qué NO garantiza (límites)

- **Si otra capacidad restaura estados sin pasar por el pergamino** (línea de tiempo, puntos de control), debe restaurar también el conocimiento; este contrato no lo hace por ella. La forma natural es exportar y restaurar con el mismo contrato de [estado-guardado-niebla.md](estado-guardado-niebla.md).
- El **orden entre dos nodos del mismo grupo** no está fijado más allá del orden de registro; no hay dependencia entre el conocimiento y los demás cambios del grupo (posición, puertas reales, agenda).
- Un `OBSERVAR_PUERTA` con `valor_anterior == 0` se revierte a «sin observar»; la vista debe aceptar ese valor (FR-209).

## 5. Pruebas que lo cubren

`test_niebla_retroceso.py`: entrada sin antorcha, entrada con antorcha (Apéndice B), entrada que observa una puerta cambiada, deshacer sin historial (instante 0), cinco acciones y cinco pergaminos, acción rechazada, historial recortado, y equivalencia con `tests_labs/referencia_conocimiento.py` tras cada deshacer en recorridos aleatorios con semilla.
