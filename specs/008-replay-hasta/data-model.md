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
    instante_pedido: int
    instante_alcanzado: int
    acciones_reproducidas: int
    id_sala_jugador: int
    vida_jugador: int
    ataque_jugador: int
    defensa_jugador: int
    velocidad_jugador: int
    inventario_llaves: list[str] = field(default_factory=list)
    inventario_objetos: list[str] = field(default_factory=list)
    efectos_activos: list[str] = field(default_factory=list)
    enemigos_sala: list[tuple[str, int]] = field(default_factory=list)
    partida_terminada: bool = False
    motivo_terminacion: str | None = None
    log_agotado: bool = False
```

#### Descripción de campos y reglas

| Campo | Tipo | Requisito | Regla / Invariante |
|---|---|---|---|
| `instante_pedido` | `int` | FR-404, FR-405 | El valor $t$ solicitado con `--hasta`. Permite a la presentación decidir si la partida terminó antes de alcanzar $t$. |
| `instante_alcanzado` | `int` | FR-404 | Tiempo virtual del reloj tras el último evento ejecutado. Cumple $0 \le \text{instante\_alcanzado} \le t$. |
| `acciones_reproducidas` | `int` | FR-404 | Cantidad de acciones del jugador extraídas del log y efectivamente ejecutadas. |
| `id_sala_jugador` | `int` | FR-404 | Sala donde quedó el jugador en el instante alcanzado. |
| `vida_jugador` | `int` | FR-404 | Salud actual del jugador al momento del corte ($\ge 0$). |
| `ataque_jugador`, `defensa_jugador`, `velocidad_jugador` | `int` | FR-404 | Estadísticas vigentes del jugador según las reglas de la Parte I (con bonos de arma y armadura equipadas y modificadores temporales de velocidad). |
| `inventario_llaves` | `list[str]` | FR-404 | Identificadores de llaves en posesión del jugador. |
| `inventario_objetos` | `list[str]` | FR-404 | Nombres de los objetos que el jugador porta. |
| `efectos_activos` | `list[str]` | FR-404 | Efectos vigentes sobre el jugador en ese instante (veneno, velocidad temporal por poción, antorcha encendida), en un orden fijo para garantizar determinismo. |
| `enemigos_sala` | `list[tuple[str, int]]` | FR-404 | Pares `(nombre_o_tipo, vida_actual)` de los enemigos vivos presentes en la sala del jugador, ordenados por identificador de instancia. |
| `partida_terminada` | `bool` | FR-404, FR-405 | `True` si la partida concluyó (muerte o victoria) en o antes del instante alcanzado. |
| `motivo_terminacion` | `str | None` | FR-404, FR-405 | Descripción del desenlace si `partida_terminada` es `True`; `None` si sigue en curso. |
| `log_agotado` | `bool` | FR-405 | `True` si el registro se terminó con el reloj estrictamente antes de $t$ y la partida sin concluir. |

El mapa conocido del jugador no forma parte del DTO: depende de la capacidad de niebla de guerra (diferido, Assumptions de `spec.md`).

---

## 2. Invariantes del modelo de datos

1. **Invariante temporal (FR-402, FR-403)**:
   $$\text{instante\_alcanzado} \le t$$
   Ningún evento ejecutado en la simulación tiene un tiempo virtual estrictamente superior a $t$.
2. **Decisión del jugador en $t$ (FR-403)**: la decisión del jugador cuyo instante es mayor o igual que $t$ no se ejecuta; solo se ejecutan decisiones con instante $< t$ y los eventos de los demás actores con tiempo $\le t$.
3. **Invariante de instante cero (FR-406)**:
   $$\text{Si } t = 0 \implies \text{instante\_alcanzado} = 0 \land \text{acciones\_reproducidas} = 0$$
   Es consecuencia de la regla anterior, no una excepción: el estado es el inicial, previo a la primera decisión del jugador.
4. **Consistencia de término (FR-404, FR-405)**:
   $$\text{partida\_terminada} = \text{True} \implies \text{motivo\_terminacion} \text{ no es None}$$
5. **Determinismo de representación (FR-411, Principio II)**:
   `enemigos_sala` y `efectos_activos` se generan con un orden fijo (por identificador de instancia y por un orden de efectos definido), sin depender del orden de iteración de estructuras no ordenadas.

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
