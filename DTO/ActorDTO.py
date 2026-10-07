from __future__ import annotations
from dataclasses import dataclass, field, InitVar
from collections import deque
from DTO.Objeto import *
from Logica.InventarioLogica import InventarioLogica


@dataclass
class ActorDTO:
    """DTO base con las estadísticas comunes."""
    vida_actual: int
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    id_sala_actual: int = field(default=0, kw_only=True)

#TODO agregar un estado de veneno, no se sabe todavía si un booleano o interger 
@dataclass
class JugadorDTO(ActorDTO):
    """DTO con la información inicial y límites del jugador."""
    inventario_max: InitVar[int] = 0
    inventario: InventarioLogica = field(init=False)
    id_sala_actual: int = 0
    armadura: Armadura | None = None
    arma: Arma | None = None
    veneno: bool = False

    def __post_init__(self,inventario_max: int):
        self.inventario = InventarioLogica(inventario_max)

    
@dataclass
class EnemigoDTO(ActorDTO):
    """DTO con la información combinada del catálogo e instancia del enemigo."""
    id_instancia: str
    tipo: str
    nombre: str
    comportamiento: str
    vida_actual: int
    suelta: list[str] = field(default_factory=list)