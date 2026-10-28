from __future__ import annotations
from dataclasses import dataclass


@dataclass
class AccionEnemigoDTO:
    """Lo que decidió hacer un enemigo en su turno: el mensaje para la bitácora y lo que cuesta la acción.
    Moverse cuesta lo que cuesta la salida cruzada; esperar, atacar o no moverse cuestan 100 (FR-107)."""
    mensaje: str
    costo: int = 100
