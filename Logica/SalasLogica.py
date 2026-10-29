from DTO.SalaDTO import *
from DTO.ActorDTO import JugadorDTO
from Logica.JugadorLogica import *
from DTO.EventoDTO import EventoDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.PuertasLogica import fijar_cerrada
class SalaLogica :
    def __init__(self,sala:SalaDTO, avisar_puerta=None):
        self.sala: SalaDTO = sala
        self.avisar_puerta = avisar_puerta     # se llama con la salida cada vez que una puerta cambia de estado
        self.mapa_puertas = None               # MapaCripta cuya versión de puertas sube con cada cambio

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
                    return respuesta
            
            fijar_cerrada(salida, False, self.avisar_puerta, self.mapa_puertas)
            respuesta.exito,respuesta.mensaje, respuesta.puntaje = True, "La puerta ha sido abierta", 25
            if(salida.cierre_automatico is not None):
                respuesta.eventoResultado = EventoDTO(salida.cierre_automatico,None,self.sala,"CERRAR_PUERTA",[direccion])

        return respuesta

    def cerrarPuerta(self,direccion: str):
        respuesta = ResultadoEventoDTO()
        salida: SalidaDTO = self._obtener_salida(Direccion(direccion))
        if not salida:
            respuesta.exito, respuesta.mensaje = False, "No existe la salida a cerrar"
        else:
            fijar_cerrada(salida, True, self.avisar_puerta, self.mapa_puertas)
            respuesta.exito, respuesta.mensaje = True, f"Se ha cerrado la puerta {salida.direccion} de la sala {self.sala.id}"
        return respuesta
    def actualizarTiempo(self,nuevoTiempo: int):
        if nuevoTiempo<self.sala.ultimo_paso:
            return
        self.sala.ultimo_paso = nuevoTiempo



        