from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import *
from DTO.EventoDTO import EventoDTO
from Logica.GestorEventos import GestorEventos
from Logica.JugadorLogica import JugadorLogica
class EstadoJuegoLogica:
    def __init__(self, estadoJuego: EstadoJuego, semilla: int = None):
        self.estadoJuego = estadoJuego
        self.gestorEventos = GestorEventos(
            estadoJuego.salas,
            estadoJuego.jugador,
            semilla
        )
        self.jugadorLogica = JugadorLogica(estadoJuego.jugador)
        self.tiempoMovimientoJugador = 0
        for sala in estadoJuego.salas:
            for enemigo in sala.enemigos:
                self.cargarEvento(
                    EventoDTO(100, 0, enemigo, "ACCION_ENEMIGO", [estadoJuego.jugador])
                )

    def iniciarJuego(self) -> EstadoJuego:
        pass
    #TODO Este va a recibir: el numero de cripta y partir de eso se comunica con comunicador para saber
    #1. Cuantas salas existen (solo reservar la memoria)
    #2. Crear el reloj virtual
    #3. Preguntar al comuniador por el jugador inicial (JugadorDTO)
    # Este lo asigna a self.estadoJuego
    # Devolver en que sala inicial el jugador
    # ejecuta ingresarEnSala(salainicial) y cargar algunas al rededor para el inicio

    def ingresarEnSala(self, sala: int)-> SalaDTO:
        if(sala < 0 or sala >= len(self.estadoJuego.salas)):
            raise ValueError("No existe la sala que se desea consultar")
        if(self.estadoJuego.salas[sala] is not None):
            return self.estadoJuego.salas[sala]
        return None #TODO falta que hace cuando la sala no ha sido cargada 
    #TODO va a revisar la seccion del vector de la memoria
    #si la sala está (no es None) la devuelve
    #si no, se comunica con el comunicador, recibe la sala y la inserta en el vector y la devuelve
    #inicial todos los enemigos de las salas

    def obtenerJugador(self):
        if self.estadoJuego is None:
            return None
        return self.estadoJuego.jugador 



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
        
    