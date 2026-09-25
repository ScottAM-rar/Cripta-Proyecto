from __future__ import annotations
from dataclasses import dataclass, field, InitVar
from collections import deque


@dataclass
class ActorDTO:
    """DTO base con las estadísticas comunes."""
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int


@dataclass
class JugadorDTO(ActorDTO):
    """DTO con la información inicial y límites del jugador."""
    inventario_max: InitVar[int] = 0
    inventario: deque = field(init=False)
    id_sala_actual: int = 0

    def __post_init__(self,inventario_max: int):
        self.inventario = deque(maxlen=inventario_max)
        '''Holder, JP tiene que definir como se va a usar el inventario
            aqui solo definde que estructura es, en LogicaJugador se define como se comporta
        '''




@dataclass
class EnemigoDTO(ActorDTO):
    """DTO con la información combinada del catálogo e instancia del enemigo."""
    id_instancia: str
    tipo: str
    nombre: str
    comportamiento: str
    vida_actual: int
    suelta: list[str] = field(default_factory=list)