from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import *
from DTO.SalaDTO import *
from DTO.EstadoJuegoDTO import EstadoJuego
from Logica.JugadorLogica import JugadorLogica
from Logica.SalasLogica import SalaLogica

#Aquí van a ir TODOS los eventos que se pueden manejar, para hacer un acción se va a consultar aquí


class GestorEventos:

    def __init__(self, jugador_logica: JugadorLogica, salas_logica: SalaLogica,
    ):
        #EnemigosLogica: enemigos_logica: 

        # Inyección de dependencias de la capa de lógica
        self.jugador_logica = jugador_logica
        #self.enemigos_logica = enemigos_logica
        self.salas_logica = salas_logica

    def procesar_evento(self, evento: EventoDTO, estado_juego: EstadoJuego):
        """ENRUTADOR, REVISA EL EVENTO Y LO MANDA A RESOLVER DONDE SEA CONVENIENTE"""

        match evento.tipo_accion:

            case "MOVER_JUGADOR":
                #Datos extra: [dirección]
                sala: SalaDTO = evento.datos_extra[0]
                return self.jugador_logica.mover_jugador(sala)
            
            case "RECOGER_OBJETO":
                #Datos extra: [objeto]
                objeto: Objeto = evento.datos_extra[0]
                return self.jugador_logica.recogerObjeto(objeto)

            case "TIENE_LLAVE":
                #Datos extra: [id_llave]
                id_llave = evento.datos_extra[0]
                return self.jugador_logica.tiene_llave(id_llave)

            

            
                