from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import *
from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import JugadorDTO
from Logica.GestorEventos import GestorEventos
from Logica.JugadorLogica import JugadorLogica
from Logica.RelojVirtual import RelojVirtual
from adaptadores.cache import CacheLRU
from adaptadores.cliente_http import ClienteCripta
from adaptadores.servicioCripta import ServicioCripta
class EstadoJuegoLogica:
    def __init__(self,semilla: int = None, cripta: str = None):
        self.tiempoMovimientoJugador = 0
        self.comunicacion = ServicioCripta(ClienteCripta("https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"),
                                            CacheLRU(25))
        self.semilla = semilla
        self.iniciado = False
        if(cripta is not None):
            self.iniciarJuego(cripta)
        
        


    def iniciarJuego(self, cripta: str):
        if not self.comunicacion.existe_cripta(cripta):
            raise ValueError("No existe la cripta solicitada")
        cantSalas = self.comunicacion.total_salas(cripta)
        salas = [None] * cantSalas
        relojvirtual = RelojVirtual()
        jugador =self.comunicacion.crear_jugador(cripta)
        self.estadoJuego = EstadoJuego(relojvirtual,jugador,[],[],salas)
        self.gestorEventos = GestorEventos(self.estadoJuego.salas,jugador,self.ingresarEnSala,self.semilla)
        self.jugadorLogica = JugadorLogica(jugador,self.semilla)
        self.idCripta = cripta
        self.iniciado = True

    def listarCriptas(self) -> list[str]:
        return self.comunicacion.listar_criptas()

    def obtenerIdCripta(self, posicion: int) -> str:
        return self.comunicacion.obtener_id_cripta(posicion)
        
    #TODO Este va a recibir: el numero de cripta y partir de eso se comunica con comunicador para saber
    #1. Cuantas salas existen (solo reservar la memoria)
    #2. Crear el reloj virtual
    #3. Preguntar al comuniador por el jugador inicial (JugadorDTO)
    # Este lo asigna a self.estadoJuego
    # Devolver en que sala inicial el jugador
    # ejecuta ingresarEnSala(salainicial) y cargar algunas al rededor para el inicio

    def ingresarEnSala(self, sala: int)-> SalaDTO:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if(sala < 0 or sala >= len(self.estadoJuego.salas)):
            raise ValueError("No existe la sala que se desea consultar")
        if(self.estadoJuego.salas[sala] is not None):
            return self.estadoJuego.salas[sala]
        self.estadoJuego.salas[sala] = self.comunicacion.construir_sala(self.idCripta,sala) 
        for enemigo in self.estadoJuego.salas[sala].enemigos:
            self.cargarEvento(
                EventoDTO(
                    100,
                    0,
                    enemigo,
                    "ACCION_ENEMIGO",
                    [self.estadoJuego.jugador]
                )
            )
        return self.estadoJuego.salas[sala]

    #TODO va a revisar la seccion del vector de la memoria
    #si la sala está (no es None) la devuelve
    #si no, se comunica con el comunicador, recibe la sala y la inserta en el vector y la devuelve
    #inicial todos los enemigos de las salas

    def obtenerJugador(self):
        if self.estadoJuego is None:
            return None
        return self.estadoJuego.jugador 
        

    def tieneLlave(self,id_llave : str):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.jugadorLogica.tiene_llave(id_llave)

    def _siguienteAccion(self):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
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
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.estadoJuego.reloj.encolar(evento.tiempo_ejecucion,evento.actor,evento.tipo_accion,evento.datos_extra)

    def accionJugador(self, evento: EventoDTO):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        self.tiempoMovimientoJugador = self.cargarEvento(evento)
        return self._siguienteAccion()
        
    