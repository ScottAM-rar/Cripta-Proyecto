from dataclasses import dataclass


@dataclass
class FinPartidaDTO:
    id_Cripta: str
    vers_Cripta: str | None
    acciones_jugador: int            # acciones que consumieron tiempo virtual del jugador (§2.12)
    cantEnemigosDerrotados: int
    tiempoReloj: int
    victoria: bool = False
