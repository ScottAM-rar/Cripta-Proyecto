from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Trampa:
    id_instancia: str
    id_catalogo: str
    id_sala: int
    daño: int
    rearme: int #Unidades virtuales para volver a armarse tras activarse
    armada: bool = True


