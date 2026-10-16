import random
from abc import ABC, abstractmethod
from DTO.ActorDTO import EnemigoDTO
from DTO.SalaDTO import SalaDTO
class ComportamientoEnemigo(ABC):
    @staticmethod
    @abstractmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], azar: random.Random | None = None, tiempo_actual: int | None = None) -> str:
        pass
