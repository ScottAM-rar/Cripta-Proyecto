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
        for enemigo in estadoJuego.enemigos_vivos:
            self.cargarEvento(
                EventoDTO(100, 0, enemigo, "ACCION_ENEMIGO", [estadoJuego.jugador])
            )

    def tieneLlave(self,id_llave : str):
        return self.jugadorLogica.tiene_llave(id_llave)

    def _siguienteAccion(self):
        respuesta = None
        while True:
            evento = self.estadoJuego.reloj.desencolar()

            if not evento:
                break

            print(
                f"Evento: {evento.tipo_accion} | "
                f"Tiempo: {evento.tiempo_ejecucion}"
            )
            accion = self.gestorEventos.procesar_evento(evento)
            respuesta = accion
            print(accion.mensaje)
            if (
                accion.eventoResultado is not None
            ):
                self.cargarEvento(accion.eventoResultado)
            if evento.actor == self.estadoJuego.jugador:
                break

        return respuesta

        
    
    def cargarEvento(self, evento : EventoDTO) -> int:
        return self.estadoJuego.reloj.encolar(evento.tiempo_ejecucion,evento.actor,evento.tipo_accion,evento.datos_extra)

    def accionJugador(self, evento: EventoDTO):
        self.tiempoMovimientoJugador = self.cargarEvento(evento)
        return self._siguienteAccion()
        
    