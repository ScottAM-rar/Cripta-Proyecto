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
    regeneracion: int = 0   # vida que recupera cada 200 unidades (§2.10); 0 = no regenera


@dataclass
class EnemigoContenidoDTO:
    """Instancia concreta en sala de /contenido."""
    instancia: str
    tipo: str
    vida: int
