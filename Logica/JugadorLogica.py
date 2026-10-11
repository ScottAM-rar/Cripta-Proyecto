from DTO.ActorDTO import JugadorDTO,EnemigoDTO
from DTO.SalaDTO import SalaDTO
from DTO.Objeto import Objeto
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.ActorLogica import ActorLogica
import random

class JugadorLogica(ActorLogica):
    def __init__(self,jugador : JugadorDTO, semilla: int = None):
        self.jugador = jugador
        self.semilla = semilla

    def mover_jugador(self, sala_actual: SalaDTO, direccion: str) -> ResultadoEventoDTO:
        respuesta = self._mover(self.jugador, sala_actual, direccion)
        if(respuesta.exito == True):
            respuesta.mensaje = f"El jugador se ha movido a la sala {self.jugador.id_sala_actual}"
        return respuesta

    def atacarEnemigo(self, enemigo : EnemigoDTO)-> ResultadoEventoDTO:
        if enemigo.vida_actual <= 0:
            return ResultadoEventoDTO(False, f"El jugador {self.jugador.id_instancia} no atacó al enemigo ya que está muerto")
        self._atacar(self.jugador,enemigo,self.semilla)
        return ResultadoEventoDTO(True,f"El jugador ha atacado al enemigo causando daño")

    def recogerObjeto(self,objeto: Objeto):
        try:
            self.jugador.inventario.agregar_objeto(objeto)
        except ValueError as e:
            return ResultadoEventoDTO(False, str(e))
        return ResultadoEventoDTO(True, f"El jugador ha recogido el objeto {objeto.nombre}")

    def soltarObjeto(self):
        try:
            self.jugador.inventario.soltar_objeto_actual()
        except ValueError as e:
            return ResultadoEventoDTO(False, str(e))
        return ResultadoEventoDTO(True, f"El jugador ha soltado el objeto {self.jugador.inventario.actual.objeto.nombre}")
        
    def tiene_llave(self, id_llave: int) -> bool:
        """Comprueba si el jugador posee en su inventario un objeto llave con el ID dado."""
        nodo = self.jugador.inventario.cabeza
        while nodo is not None:
            if nodo.objeto.id_catalogo == id_llave:
                return True
            nodo = nodo.siguiente
        return False


    
