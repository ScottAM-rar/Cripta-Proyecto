from DTO.ActorDTO import JugadorDTO,EnemigoDTO
from DTO.SalaDTO import SalaDTO
from DTO.Objeto import Objeto
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.ActorLogica import ActorLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from DTO.CambioDTO import CambioDTO

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

    def estaEnSalaFinal(self, salaFinal: int):
        return self.jugador.id_sala_actual == salaFinal
    def atacarEnemigo(self, enemigo : EnemigoDTO)-> ResultadoEventoDTO:
        if enemigo.vida_actual <= 0:
            return ResultadoEventoDTO(False, f"El jugador {self.jugador} no atacó al enemigo {enemigo.id_instancia} ya que está muerto")
        vida_anterior = enemigo.vida_actual
        self.retroceso.nueva_accion()
        self._atacar(self.jugador,enemigo,self.semilla)
        self.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="ACTUALIZAR_VIDA",
            objeto_afectado=enemigo,
            valor_anterior=vida_anterior,
            valor_nuevo=enemigo.vida_actual,
        )])
        if(enemigo.vida_actual<=0):
            self.jugador.enemigos_eliminados+=1
        return ResultadoEventoDTO(True,f"El jugador ha atacado al enemigo causando daño",puntaje=50)

    def recogerObjeto(self, objeto: Objeto, sala_actual: SalaDTO):
        try:
            if objeto not in sala_actual.objetos:
                raise ValueError("El objeto no se encuentra en la sala actual")
            if (
                self.jugador.inventario.cantidad_actual
                >= self.jugador.inventario.capacidad_maxima
            ):
                raise ValueError(
                    "No se puede agregar el objeto, el inventario está al máximo"
                )
            self.jugador.inventario.agregar_objeto(objeto)
            sala_actual.objetos.remove(objeto)
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
            if self.jugador.inventario.actual is None:
                raise ValueError("El inventario esta vacio")
            objeto_actual = self.jugador.inventario.actual.objeto
            indice_original = self.jugador.inventario.indice_de_objeto(objeto_actual)
            objeto = self.jugador.inventario.soltar_objeto_actual()
        except ValueError as e:
            return ResultadoEventoDTO(False, str(e))
        salaActual.objetos.append(objeto)
        self.retroceso.nueva_accion()
        self.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="SOLTAR_OBJETO",
            objeto_afectado=self.jugador,
            valor_anterior=salaActual.id,
            elemento=objeto,
            indice=indice_original,
        )])
        return ResultadoEventoDTO(True, f"El jugador ha soltado el objeto {objeto.nombre}")
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

    
