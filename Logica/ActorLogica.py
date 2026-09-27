from DTO.ActorDTO import ActorDTO
from DTO.SalaDTO import *
import random


class ActorLogica:

    @staticmethod
    def _mover(
        actor: ActorDTO, sala_actual: SalaDTO, direccion: str
    ) -> None:
        salida = next(
            (salida for salida in sala_actual.salidas
             if salida.direccion == direccion),
            None,
        )
        if salida is None:
            raise ValueError("No existe una salida en esa dirección.")
        if salida.cerrada:
            raise ValueError("La puerta está cerrada.")
        actor.id_sala_actual = salida.sala_destino

    @staticmethod
    def _atacar(actor: ActorDTO, enemigo : ActorDTO):
        azar = random.Random()
        daño = max(1,actor.ataque+azar.randint(0,4) - enemigo.defensa)
        enemigo.vida_actual-=daño   