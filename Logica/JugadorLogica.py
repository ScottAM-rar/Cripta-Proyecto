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
        self._atacar(self.jugador,enemigo,self.semilla)
        return ResultadoEventoDTO(True,f"El jugador ha atacado al enemigo causando daño")

    def recogerObjeto(self,objeto: Objeto):
        self.jugador.inventario.agregar_objeto(objeto)

    def soltarObjeto(self, objeto: Objeto):
        self.jugador.inventario.soltar_objeto_actual(objeto)
        
    def tiene_llave(self, id_llave: int) -> bool:
        """Comprueba si el jugador posee en su inventario un objeto llave con el ID dado."""
        nodo = self.jugador.inventario.cabeza
        while nodo is not None:
            if nodo.objeto.id_catalogo == id_llave:
                return True
            nodo = nodo.siguiente
        return False


    
