from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .objeto import Armadura, Arma

class Comportamiento(str, Enum):
    """Estos son lo comportamientos que tendran los enemigos"""

    GUARDIAN = "guardian"
    ERRANTE = "errante"
    RASTREADOR = "rastreador"



#Esta es la clase base para jugador y enemigo
@dataclass
class Actor:
    