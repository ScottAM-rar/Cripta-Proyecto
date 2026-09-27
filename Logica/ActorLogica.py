from DTO.ActorDTO import ActorDTO
from DTO.SalaDTO import *
import random


class ActorLogica:

    @staticmethod
    def _mover(actor: ActorDTO,sala_destino: SalaDTO) -> None:
        if not any(s.sala_destino == sala_destino.id for s in sala_destino.salidas):
            raise ValueError("La sala no es una salida válida.")
        actor.id_sala_actual = sala_destino.id

    @staticmethod
    def _atacar(actor: ActorDTO, enemigo : ActorDTO):
        azar = random.Random()
        daño = max(1,actor.ataque+azar.randint(0,4) - enemigo.defensa)
        enemigo.vida_actual-=daño   