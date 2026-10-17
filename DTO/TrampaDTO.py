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
    veneno: int = 0   # daño por pulso del veneno que deja al jugador al activarse (0 = no envenena)


