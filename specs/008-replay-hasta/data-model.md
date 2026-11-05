# Modelo de Datos (Fase 1): Reproducir partida grabada hasta un instante dado (replay-hasta)

Este documento define las estructuras de datos, tipos y contratos de datos introducidos para la capacidad de reproducción acotada. Se respeta el Principio I de la constitución: sin estructuras prohibidas, empleando únicamente tipos de datos estándar autorizados (`int`, `str`, `bool`, `list`, `tuple`) y dataclasses.

---

## 1. Entidades nuevas

### `ResultadoReplayHastaDTO` (`DTO/ResultadoReplayHastaDTO.py`)

Estructura de transporte que encapsula el estado exhaustivo del juego al detenerse la reproducción acotada (FR-404).

```python
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ResultadoReplayHastaDTO:
    """Resultado exhaustivo de reproducir una partida grabada hasta un instante virtual dado."""
    instante_alcanzado: int
    acciones_reproducidas: int
    id_sala_jugador: int
    vida_jugador: int
    inventario_llaves: list[str] = field(default_factory=list)
    inventario_objetos: list[str] = field(default_factory=list)
    enemigos_sala: list[tuple[str, int]] = field(default_factory=list)
    partida_terminada: bool = False
    motivo_terminacion: str | None = None
    log_agotado: bool = False
```

#### Descripción de campos y reglas

| Campo | Tipo | Requisito | Regla / Invariante |
|---|---|---|---|
| `instante_alcanzado` | `int` | FR-404 | Tiempo virtual del reloj tras el último evento ejecutado. Cumple $0 \le \text{instante\_alcanzado} \le t$. |
| `acciones_reproducidas` | `int` | FR-404 | Cantidad de acciones de jugador extraídas del log y efectivamente ejecutadas. |
| `id_sala_jugador` | `int` | FR-404 | Identificador numérico de la sala donde quedó situado el jugador en el instante alcanzado. |
| `vida_jugador` | `int` | FR-404 | Salud actual del jugador al momento del corte ($\ge 0$). |
| `inventario_llaves` | `list[str]` | FR-404 | Lista de identificadores de llaves en posesión del jugador. |
| `inventario_objetos` | `list[str]` | FR-404 | Lista con los nombres o descripciones de objetos que el jugador porta en su inventario. |
| `enemigos_sala` | `list[tuple[str, int]]` | FR-404 | Lista de tuplas `(nombre_o_tipo, vida_actual)` de los enemigos vivos presentes en la misma sala del jugador, ordenada por identificador/nombre para garantizar determinismo. |
| `partida_terminada` | `bool` | FR-404, FR-405 | `True` si la partida concluyó (por muerte del jugador o victoria) en o antes del instante alcanzado; `False` si continúa en curso. |
| `motivo_terminacion` | `str | None` | FR-404, FR-405 | Descripción del desenlace si `partida_terminada` es `True` (ej. `"El jugador murió por ataque de Murciélago"`). `None` si la partida sigue en curso. |
| `log_agotado` | `bool` | FR-405 | `True` si el archivo de registro se terminó antes de que el reloj virtual alcanzara el valor de $t$; `False` en caso contrario. |

---

## 2. Invariantes del modelo de datos

1. **Invariante temporal (FR-402, FR-403)**:
   $$\text{instante\_alcanzado} \le t$$
   Ningún evento ejecutado en la simulación tiene un tiempo virtual estrictamente superior a $t$.
2. **Invariante de instante cero (FR-406)**:
   $$\text{Si } t = 0 \implies \text{instante\_alcanzado} = 0 \land \text{acciones\_reproducidas} = 0$$
   El estado reflejado es el estado inicial puro antes de aplicar cualquier acción del archivo de registro.
3. **Invariante de consistencia de término (FR-404, FR-405)**:
   $$\text{partida\_terminada} = \text{True} \implies \text{motivo\_terminacion} \text{ no es None}$$
4. **Determinismo de representación (FR-411, Principio II)**:
   La lista `enemigos_sala` se genera con ordenamiento estable por identificador de entidad, evitando variaciones dependientes del orden de iteración de diccionarios o conjuntos no ordenados.

---

## 3. Firmas de métodos adaptados en las capas

### Capa de Lógica (`Logica/EstadoJuegoLogica.py`)

```python
def repetirPartida(
    self, 
    log: LogPartidaDTO, 
    hasta: int | None = None
) -> list[ResultadoEventoDTO] | ResultadoReplayHastaDTO:
    """Reproduce el log. Si hasta is None, reproduce todo y devuelve lista de resultados (FR-409).
    Si hasta is not None, reproduce acotado hasta ese instante y devuelve ResultadoReplayHastaDTO (FR-404)."""

def accionJugador(
    self, 
    evento: EventoDTO, 
    tope: int | None = None
) -> ResultadoEventoDTO:
    """Ejecuta la acción del jugador y propaga el tope al avance de turnos."""

def _avanzarHastaProximoTurno(
    self, 
    tope: int | None = None
) -> None:
    """Avanza los eventos en el reloj hasta el próximo turno del jugador, deteniéndose si el próximo
    evento supera el tope indicado."""

def _armarResultadoReplayHasta(
    self, 
    hasta: int, 
    acciones_reproducidas: int, 
    log_agotado: bool
) -> ResultadoReplayHastaDTO:
    """Construye el DTO con el estado exhaustivo en el instante de detención."""
```

### Capa de Servicio (`Servicio/EstadoJuegoServicio.py`)

```python
def repetirPartida(
    self, 
    archivo: str, 
    hasta: int | None = None
) -> list[ResultadoEventoDTO] | ResultadoReplayHastaDTO:
    """Punto de entrada del servicio para reproducción completa o acotada."""
```
