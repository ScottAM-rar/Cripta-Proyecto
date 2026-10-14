from dataclasses import dataclass
from DTO.EventoDTO import EventoDTO
@dataclass
class FinPartidaDTO:
    id_Cripta: str
    vers_Cripta: str
    acciones_jugador:str
    cantEnemigosDerrotados: int
    tiempoReloj: int
