from __future__ import annotations
from dataclasses import dataclass, field


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
    inventario_max: int


@dataclass
class EnemigoDTO(ActorDTO):
    """DTO con la información combinada del catálogo e instancia del enemigo."""
    id_instancia: str
    tipo: str
    nombre: str
    comportamiento: str
    vida_actual: int
    suelta: list[str] = field(default_factory=list)