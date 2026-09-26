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
        #TODO tecnicamente es de JP así que puede cambiar

    def usarObjeto(self, objeto: Objeto):
        return
        #TODO falta toda la lógica, es de inventario así que es de JP Rico

    
    def tiene_llave(self, id_llave: int) -> bool:
        """Comprueba si el jugador posee en su inventario (deque) un objeto llave con el ID dado."""
        return any(item.id_catalogo == id_llave for item in self.jugador.inventario)


    
