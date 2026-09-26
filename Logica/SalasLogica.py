from DTO.SalaDTO import *
from DTO.ActorDTO import JugadorDTO
from Logica.JugadorLogica import *
from DTO.EventoDTO import EventoDTO
class SalaLogica :
    def __init__(self,sala:SalaDTO):
        self.sala: SalaDTO = sala

    def _obtener_salida(self, direccion: Direccion) -> SalidaDTO | None:
        """Recorre la deque del DTO externamente y devuelve la salida o None."""
        return next((s for s in self.sala.salidas if s.direccion == direccion), None)
    
    #La dirección se envía como un 
    def intentarAbrirPuerta(self, jugador: JugadorDTO, direccion: str) -> tuple[bool, str, EventoDTO | None]:
        salida: SalidaDTO | None = self._obtener_salida(Direccion(direccion))
        if not salida:
            raise ValueError("No existe la salida solicitada")

        if not salida.cerrada:
            return True, "La puerta está abierta"

        jugadorlog = JugadorLogica(jugador)

        if salida.llave is not None:
            if not jugadorlog.tiene_llave(salida.llave):
                return False, "No tiene la llave adecuada para abrir la puerta"

        salida.cerrada = False
        evento = None
        if(salida.cierre_automatico is not None):
            evento = EventoDTO(salida.cierre_automatico,None,self.sala,"Cerrar Puerta",[direccion])

        return True, "La puerta ha sido abierta", evento


        