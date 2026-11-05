import random
from abc import ABC, abstractmethod
from DTO.ActorDTO import EnemigoDTO
from DTO.AccionEnemigoDTO import AccionEnemigoDTO
from DTO.SalaDTO import SalaDTO
class ComportamientoEnemigo(ABC):
    @staticmethod
    @abstractmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], azar: random.Random | None = None, tiempo_actual: int | None = None,
               campo_de_costos=None) -> AccionEnemigoDTO:
        """Decide y ejecuta el turno del enemigo. Devuelve el mensaje y lo que cuesta la acción: moverse cuesta lo que
        cuesta la salida cruzada; esperar o no moverse, 100 (FR-107). `campo_de_costos` solo lo usa el cazador."""
        pass
