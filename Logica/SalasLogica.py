from DTO.SalaDTO import *
from DTO.ActorDTO import JugadorDTO
from Logica.JugadorLogica import *
from DTO.EventoDTO import EventoDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
class SalaLogica :
    def __init__(self,sala:SalaDTO):
        self.sala: SalaDTO = sala

    def _obtener_salida(self, direccion: Direccion) -> SalidaDTO | None:
        """Recorre la deque del DTO externamente y devuelve la salida o None."""
        return next((s for s in self.sala.salidas if s.direccion == direccion), None)

    
    
    #La dirección se envía como un 
    def intentarAbrirPuerta(self, jugador: JugadorDTO, direccion: str) -> ResultadoEventoDTO:
        respuesta = ResultadoEventoDTO()
        salida: SalidaDTO | None = self._obtener_salida(Direccion(direccion))
        if not salida:
            respuesta.exito, respuesta.mensaje = False, "No existe la salida solicitada"
        elif not salida.cerrada:
            respuesta.exito, respuesta.mensaje = False, "La puerta está abierta"
        else:
            jugadorlog = JugadorLogica(jugador)

            if salida.llave is not None:
                if not jugadorlog.tiene_llave(salida.llave):
                    respuesta.exito,respuesta.mensaje =  False, "No tiene la llave adecuada para abrir la puerta"

            salida.cerrada = False
            respuesta.exito,respuesta.mensaje = True, "La puerta ha sido abierta"
            if(salida.cierre_automatico is not None):
                respuesta.eventoResultado = EventoDTO(salida.cierre_automatico,None,self.sala,"Cerrar Puerta",[direccion])

        return respuesta

    def actualizarTiempo(self,nuevoTiempo: int):
        if nuevoTiempo<self.sala.ultimo_paso:
            return
        self.sala.ultimo_paso = nuevoTiempo



        