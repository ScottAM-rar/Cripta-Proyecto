from DTO.ActorDTO import JugadorDTO,EnemigoDTO
from DTO.SalaDTO import SalaDTO
from DTO.Objeto import Objeto
from Logica.ActorLogica import ActorLogica

class JugadorLogica(ActorLogica):
    def __init__(self,jugador : JugadorDTO):
        self.jugador = jugador

    def mover_jugador(self,sala_destino: SalaDTO) -> None:
        self._mover(self.jugador,sala_destino)

    def atacarEnemigo(self, enemigo : EnemigoDTO):
        self._atacar(self.jugador,enemigo)

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


    
