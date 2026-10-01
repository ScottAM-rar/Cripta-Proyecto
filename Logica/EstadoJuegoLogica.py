from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import *
from DTO.EventoDTO import EventoDTO
from Logica.GestorEventos import GestorEventos
from Logica.JugadorLogica import JugadorLogica
class EstadoJuegoLogica:
    def __init__(self, estadoJuego: EstadoJuego):
        self.estadoJuego = estadoJuego
        self.gestorEventos = GestorEventos(estadoJuego.salas,JugadorLogica(estadoJuego.jugador))
        self.jugadorLogica = JugadorLogica(estadoJuego.jugador)
        self.tiempoMovimientoJugador = 0

    def tieneLlave(self,id_llave : str):
        return self.jugadorLogica.tiene_llave(id_llave)

    def _siguienteAccion(self):
        while True:
            evento = self.estadoJuego.reloj.desencolar()

            if not evento:
                break

            print(
                f"Evento: {evento.tipo_accion} | "
                f"Tiempo: {evento.tiempo_ejecucion}"
            )
            accion = self.gestorEventos.procesar_evento(evento)

            if (
                isinstance(accion, tuple)
                and len(accion) == 3
                and accion[2] is not None
            ):
                newEvento = accion[2]
                self.estadoJuego.reloj.encolar(
                    newEvento.tiempo_ejecucion,
                    newEvento.actor,
                    newEvento.tipo_accion,
                    newEvento.datos_extra)
            if evento.actor == self.estadoJuego.jugador:
                break

        
           




   

    def cargarEvento(self, evento : EventoDTO) -> int:
        return self.estadoJuego.reloj.encolar(evento.tiempo_ejecucion,evento.actor,evento.tipo_accion,evento.datos_extra)

    def accionJugador(self, evento: EventoDTO):
        self.tiempoMovimientoJugador = self.cargarEvento(evento)
        self._siguienteAccion()
        
    