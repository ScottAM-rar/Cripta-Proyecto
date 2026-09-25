from DTO.ActorDTO import JugadorDTO,EnemigoDTO
from DTO.SalaDTO import SalaDTO
from DTO.Objeto import Objeto
import random

class JugadorLogica:
    def __init__(self,jugador : JugadorDTO):
        self.jugador = jugador

    def mover_jugador(self,sala_destino: SalaDTO) -> None:
        if not any(s.sala_destino == sala_destino.id for s in sala_destino.salidas):
            raise ValueError("La sala no es una salida válida.")
        self.jugador.id_sala_actual = sala_destino.id

    def atacarEnemigo(self, enemigo : EnemigoDTO):
        azar = random.Random()
        daño = max(1,self.jugador.ataque+azar.randint(0,4) - enemigo.defensa)
        enemigo.vida_actual-=daño

    def recogerObjeto(self,objeto: Objeto):
        if(len(self.jugador.inventario) == self.jugador.inventario.maxlen):
            raise ValueError("No se puede recoger el objeto, el inventario está al máximo")
        self.jugador.inventario.append(objeto)


    
