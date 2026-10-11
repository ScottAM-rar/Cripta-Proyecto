from abc import ABC, abstractmethod
from DTO.ActorDTO import EnemigoDTO
from DTO.EventoDTO import EventoDTO
from DTO.SalaDTO import SalaDTO
from Logica.SalasLogica import SalaLogica
class ComportamientoEnemigo(ABC):
    @staticmethod
    @abstractmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], semilla: int = None) -> str:
        pass
