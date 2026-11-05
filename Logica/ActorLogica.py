from DTO.ActorDTO import ActorDTO
from DTO.SalaDTO import *
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from DTO.Objeto import Arma, Armadura
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
            respuesta.puntaje = 10
            respuesta.costo = salida.costo     # lo que cuesta cruzar esta salida (FR-103)
        
        return respuesta

    @staticmethod
    def velocidad_efectiva(actor: ActorDTO) -> int:
        """Velocidad base más el modificador temporal de una poción (solo el jugador lo tiene). Nunca menor que 1."""
        return max(1, actor.velocidad + getattr(actor, "modificador_velocidad", 0))

    @staticmethod
    def _equipados(actor: ActorDTO) -> list:
        """Objetos que el inventario muestra como equipados (mostrar_equipado_1 y mostrar_equipado_2)."""
        equipados = []
        inventario = getattr(actor, "inventario", None)   # los enemigos no tienen inventario
        if inventario is None:
            return equipados
        for mostrar in (inventario.mostrar_equipado_1, inventario.mostrar_equipado_2):
            try:
                equipados.append(mostrar())
            except ValueError:
                pass   # inventario vacío o ese lugar no tiene un arma o armadura
        return equipados

    @staticmethod
    def ataque_efectivo(actor: ActorDTO) -> int:
        """Ataque base más el ataque_bonus del arma equipada. Solo cuenta una arma (la primera que aparezca)."""
        for objeto in ActorLogica._equipados(actor):
            if isinstance(objeto, Arma):
                return actor.ataque + objeto.ataque_bonus
        return actor.ataque

    @staticmethod
    def defensa_efectiva(actor: ActorDTO) -> int:
        """Defensa base más el defensa_bonus de la armadura equipada. Solo cuenta una armadura (la primera que aparezca)."""
        for objeto in ActorLogica._equipados(actor):
            if isinstance(objeto, Armadura):
                return actor.defensa + objeto.defensa_bonus
        return actor.defensa

    @staticmethod
    def _atacar(actor: ActorDTO, enemigo : ActorDTO, azar: random.Random):
        daño = max(1, ActorLogica.ataque_efectivo(actor) + azar.randint(0,4) - ActorLogica.defensa_efectiva(enemigo))
        enemigo.vida_actual-=daño
        if enemigo.vida_actual < 0:
            enemigo.vida_actual = 0   