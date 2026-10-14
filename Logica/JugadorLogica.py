from DTO.ActorDTO import JugadorDTO,EnemigoDTO
from DTO.SalaDTO import SalaDTO
from DTO.Objeto import Objeto
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.ActorLogica import ActorLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from DTO.CambioDTO import CambioDTO
import random

class JugadorLogica(ActorLogica):
    def __init__(self,jugador : JugadorDTO, semilla: int = None):
        self.jugador = jugador
        self.semilla = semilla
        self.retroceso = RetrocesoLogica()

    def mover_jugador(self, sala_actual: SalaDTO, direccion: str) -> ResultadoEventoDTO:
        respuesta = self._mover(self.jugador, sala_actual, direccion)
        if(respuesta.exito == True):
            self.retroceso.nueva_accion()
            self.retroceso.registrar_cambio([
                CambioDTO(
                    tipo_accion="MOVER",
                    objeto_afectado=self.jugador,
                    valor_anterior=sala_actual.id,
                    valor_nuevo=self.jugador.id_sala_actual,
                )
            ])
            respuesta.mensaje = f"El jugador se ha movido a la sala {self.jugador.id_sala_actual}"
        return respuesta

    def esta_muerto(self):
        return self.jugador.vida_actual <= 0
    def atacarEnemigo(self, enemigo : EnemigoDTO)-> ResultadoEventoDTO:
        if enemigo.vida_actual <= 0:
            return ResultadoEventoDTO(False, f"El jugador {self.jugador.id_instancia} no atacó al enemigo ya que está muerto")
        self._atacar(self.jugador,enemigo,self.semilla)
        if(enemigo.vida_actual<=0):
            self.jugador.enemigos_eliminados+=1
        return ResultadoEventoDTO(True,f"El jugador ha atacado al enemigo causando daño",puntaje=50)

    def recogerObjeto(self, objeto: Objeto, sala_actual: SalaDTO):
        try:
            self.jugador.inventario.agregar_objeto(objeto)
            self.retroceso.nueva_accion()
            self.retroceso.registrar_cambio([
                CambioDTO(
                    tipo_accion="RECOGER_OBJETO",
                    objeto_afectado=self.jugador,
                    valor_anterior=sala_actual.id,
                    elemento=objeto,
                )
            ])

        except ValueError as e:
            return ResultadoEventoDTO(False, str(e))
        return ResultadoEventoDTO(True, f"El jugador ha recogido el objeto {objeto.nombre}",puntaje=15)

    def soltarObjeto(self, salaActual: SalaDTO):
        try:
            salaActual.objetos.append(self.jugador.inventario.soltar_objeto_actual())
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

    def enemigos_eliminados(self):
        return self.jugador.enemigos_eliminados

    
