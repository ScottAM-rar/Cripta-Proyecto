from DTO.ActorDTO import ActorDTO
from DTO.SalaDTO import *
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
import random


class ActorLogica:

    @staticmethod
    def _mover(
        actor: ActorDTO, sala_actual: SalaDTO, direccion: str
    ) -> ResultadoEventoDTO:
        respuesta = ResultadoEventoDTO()
        salida = next(
            (salida for salida in sala_actual.salidas
             if salida.direccion == direccion),
            None,
        )
        if salida is None:
            respuesta.exito = False
            respuesta.mensaje = "No existe una salida con la dirección indicada"
        elif salida.cerrada:
            respuesta.exito = False
            respuesta.mensaje = "La salida por donde intenta volve está cerrada"
        else:
            actor.id_sala_actual = salida.sala_destino
            respuesta.exito = True #no se pone mensaje porque cada logica se lo agrega dependiendo de quien se mueva
        
        return respuesta
    @staticmethod
    def _atacar(actor: ActorDTO, enemigo : ActorDTO):
        azar = random.Random()
        daño = max(1,actor.ataque+azar.randint(0,4) - enemigo.defensa)
        enemigo.vida_actual-=daño   