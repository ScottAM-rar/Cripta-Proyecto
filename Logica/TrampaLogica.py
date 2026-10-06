from DTO.TrampaDTO import Trampa
from DTO.ResultadoEventoDTO import *
from DTO.SalaDTO import SalaDTO
from DTO.ActorDTO import *
class TrampaLogica:

    def __init__(self, Trampa: Trampa):
        self.trampa = Trampa
    #Aplica el daño y queda desarmada. Devuelve el daño a infligir;
    #quien llame es responsable de aplicarlo al jugador y de programar el evento de rearme
    def activar(self, jugador: JugadorDTO, sala: SalaDTO) -> ResultadoEventoDTO:
        evento = EventoDTO(self.trampa.rearme,None,self.trampa,"ARMAR_TRAMPA",[sala])
        if not self.trampa.armada:
            return ResultadoEventoDTO(False,f"La trampa {self.trampa.id_instancia} no se pudo armar ya que no está activada",evento)

        if jugador.id_sala_actual == sala.id:
            jugador.vida_actual -= self.trampa.daño

        for x in sala.enemigos:
            x.vida_actual-=self.trampa.daño
        self.trampa.armada = False
        return ResultadoEventoDTO(True, f"La trampa {self.trampa.id_instancia} afectó a los actores de la sala {sala.id}", evento)

    def rearmar(self, sala: SalaDTO) -> ResultadoEventoDTO:
        mensaje = ""
        exito = not self.trampa.armada
        if exito:
            self.trampa.armada = True
            mensaje = f"Se ha rearmado la trampa"
        else:
           mensaje = f"Se intentó rearmar la trampa {self.trampa.id_instancia} pero ya está armada"
        return ResultadoEventoDTO(exito,mensaje,EventoDTO(50,None,self.trampa,"ACTIVAR_TRAMPA",[sala]))
        