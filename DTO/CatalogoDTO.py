from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class EnemigoCatalogoDTO:
    """Ficha estática de /catalogo."""
    id: str
    nombre: str
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    comportamiento: str
    suelta: list[str] = field(default_factory=list)
    rango: int = 0   # solo cazador: entero >= 0 en unidades de costo (FR-108); 0 solo ataca en su sala


@dataclass
class EnemigoContenidoDTO:
    """Instancia concreta en sala de /contenido."""
    instancia: str
    tipo: str
    vida: int
