from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import *
from DTO.SalaDTO import *
from DTO.EstadoJuegoDTO import EstadoJuego
from Logica.JugadorLogica import JugadorLogica
from Logica.EnemigosLogica import EnemigoLogica
from Logica.SalasLogica import SalaLogica

#Aquí van a ir TODOS los eventos que se pueden manejar, para hacer un acción se va a consultar aquí


class GestorEventos:

    def __init__(self, salas : list[SalaDTO],jugador_logica: JugadorLogica, salas_logica: SalaLogica,
    ):
        #EnemigosLogica: enemigos_logica: 
        
        self.salas = salas
        # Inyección de dependencias de la capa de lógica
        self.jugador_logica = jugador_logica
        #self.enemigos_logica = enemigos_logica
        self.salas_logica = salas_logica

    def procesar_evento(self, evento: EventoDTO, estado_juego: EstadoJuego):
        """ENRUTADOR, REVISA EL EVENTO Y LO MANDA A RESOLVER DONDE SEA CONVENIENTE"""
        
        match evento.tipo_accion:
            
            case "MOVER_JUGADOR":
                # Datos extra: [sala_actual, direccion]
                sala_actual: SalaDTO = evento.datos_extra[0]
                direccion: str = evento.datos_extra[1]
                return self.jugador_logica.mover_jugador(
                    sala_actual, direccion
                )
            
            case "RECOGER_OBJETO":
                #Datos extra: [objeto]
                objeto: Objeto = evento.datos_extra[0]
                return self.jugador_logica.recogerObjeto(objeto)

            case "TIENE_LLAVE":
                #Datos extra: [id_llave]
                id_llave = evento.datos_extra[0]
                return self.jugador_logica.tiene_llave(id_llave)

            case "ATACAR":
                # Datos extra: [objetivo]
                objetivo: ActorDTO = evento.datos_extra[0]
                atacante: ActorDTO = evento.actor

                # Si el atacante es el jugador
                if isinstance(atacante, JugadorDTO):
                    return self.jugador_logica.atacarEnemigo(objetivo)

                # Si el atacante es un enemigo
                elif isinstance(atacante, EnemigoDTO):
                    enemigo_logica = EnemigoLogica(atacante)
                    return enemigo_logica.atacarJugador(objetivo)

                raise ValueError("El atacante no es un actor válido.")

            
            case "ABRIR_PUERTA":
                #Datos Adicionales [Jugador, Direccion]

                jugador: JugadorDTO
                direccion: str
                jugador,direccion = evento.datos_extra
                sala: SalaDTO = evento.actor
                self.salas_logica.sala = sala
                return self.salas_logica.intentarAbrirPuerta(jugador,direccion)
                




                

            

            
                