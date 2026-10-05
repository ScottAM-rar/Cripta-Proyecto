from unittest import case

from DTO.DeltaDTO import DeltaDTO
from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import *
from DTO.SalaDTO import *
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from Logica.JugadorLogica import JugadorLogica
from Logica.EnemigosLogica import EnemigoLogica
from Logica.SalasLogica import SalaLogica
# from Logica.RetrocesoLogica import RetrocesoLogica

#Aquí van a ir TODOS los eventos que se pueden manejar, para hacer un acción se va a consultar aquí


class GestorEventos:

    def __init__(self, salas : list[SalaDTO],jugador_logica: JugadorLogica
    ):
        #EnemigosLogica: enemigos_logica: 
        
        self.salas = salas
        # Inyección de dependencias de la capa de lógica
        self.jugador_logica = jugador_logica
        #self.enemigos_logica = enemigos_logica
        self.salas_logica = SalaLogica(salas)
        
        #self.retroceso_logica = RetrocesoLogica() #Historial de cambios (Deltas)

    def procesar_evento(self, evento: EventoDTO, estado_juego: EstadoJuego | None = None) -> ResultadoEventoDTO:
        """ENRUTADOR, REVISA EL EVENTO Y LO MANDA A RESOLVER DONDE SEA CONVENIENTE"""
        
        match evento.tipo_accion:
            
            case "MOVER_JUGADOR":
                # Datos extra: [sala_actual, direccion]
                sala_actual: SalaDTO = evento.datos_extra[0]
                direccion: str = evento.datos_extra[1]
                return self.jugador_logica.mover_jugador(
                    sala_actual, direccion
                )
                
            #case MOVER_JUGADOR:
            #       sala_actual: SalaDTO = evento.datos_extra[0]
            #       direccion: str = evento.datos_extra[1]

            #       sala_anterior = self.jugador_logica.jugador.id_sala_actual #Se guarda antes de mover 
            #       respuesta = self.jugador_logica.mover_jugador(sala_actual, direccion)

            #     if respuesta.exito: #Solo se registra el cambio si el movimiento ocurrio 
            #         self.retroceso_logica.registrar_accion(
            #         DeltaDTO("MOVER_JUGADOR", {"sala_anterior": sala_anterior})
            #         )
            #   return respuesta
            
            case "RECOGER_OBJETO":
                #Datos extra: [objeto]
                objeto: Objeto = evento.datos_extra[0]
                return self.jugador_logica.recogerObjeto(objeto)
            
            #case "RECOGER_OBJETO":
            #    objeto: Objeto = evento.datos_extra[0]
            #    respuesta = self.jugador_logica.recogerObjeto(objeto)
            #    self.retroceso_logica.registrar_accion(
            #        DeltaDTO("RECOGER_OBJETO", {"objeto": objeto})
            #    )
            #    return respuesta

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

        #    case "ATACAR":
        #         objetivo: ActorDTO = evento.datos_extra[0]
        #         atacante: ActorDTO = evento.actor

                  # Si el atacante es el jugador
        #         if isinstance(atacante, JugadorDTO):
        #            vida_antes = objetivo.vida_actual #Se guarda la vida del objetivo antes de atacar para calcular el daño
        #            respuesta = self.jugador_logica.atacarEnemigo(objetivo)
        #            daño = vida_antes - objetivo.vida_actual #Se calcula el daño hecho al objetivo
        #            self.retroceso_logica.registrar_accion(
        #                DeltaDTO("ATACAR", {"objetivo": objetivo, "daño": daño})
        #                )
        #           return respuesta

                  # Si el atacante es un enemigo
        #        elif isinstance(atacante, EnemigoDTO):
        #           enemigo_logica = EnemigoLogica(atacante)
        #           vida_antes = objetivo.vida_actual
        #           respuesta = enemigo_logica.atacarJugador(objetivo)
        #           daño = vida_antes - objetivo.vida_actual
        #           self.retroceso_logica.registrar_accion(
        #               DeltaDTO("ATACAR", {"objetivo": objetivo, "daño": daño})
        #               )
        #            return respuesta

        #        raise ValueError("El atacante no es un actor válido.")

            
            case "ABRIR_PUERTA":
                #Datos Adicionales [Sala, Direccion]

                sala: SalaDTO
                direccion: str
                sala,direccion = evento.datos_extra
                jugador: JugadorDTO = evento.actor
                self.salas_logica.sala = sala
                return self.salas_logica.intentarAbrirPuerta(jugador,direccion)
            
            case "ACCION_ENEMIGO":
                #Datos Adicionales [Jugador] (se necesitan también las salas pero estas se sacan del estado de juego para evitar desfases)
                jugador = evento.datos_extra[0]
                enemigoLogica = EnemigoLogica(evento.actor)
                return enemigoLogica.decidirAccion(jugador,self.salas)
            
          #  case "DESHACER":
                # Esta va a ser la accion que va utilizar el pergamino de retroceso.
                # delta = self.retroceso_logica.deshacer_accion()
                # if delta is None:
                #     return ResultadoEventoDTO(False, "No hay acciones para deshacer")
                # return self._reversa(delta)




   # def _reversa(self, delta: DeltaDTO)-> ResultadoEventoDTO:
   #     """Aplica un delta para revertir un cambio en el juego"""
   #     match delta.tipo_accion:
   #         case "MOVER_JUGADOR":
   #             self.jugador_logica.jugador.id_sala_actual = delta.datos["sala_anterior"]
   #             return ResultadoEventoDTO(True, "Movimiento revertido")
            
   #         case "RECOGER_OBJETO":
   #             #Hay que ver si el objeto se elimina o se vuelve a poner en la sala, por ahora se elimina del inventario
   #             self.jugador_logica.inventario_logica.eliminar_objeto_utilizado(delta.datos["objeto"])
   #             return ResultadoEventoDTO(True, "Objeto eliminado del inventario")
            
   #         case "ATACAR":
   #             # Se revierte el daño hecho al objetivo
   #             delta.datos["objetivo"].vida_actual += delta.datos["daño"]
   #             return ResultadoEventoDTO(True, "Daño revertido")
            
            # Se seguiran los casos

   #         case _:
   #             return ResultadoEventoDTO(False, f"No se puede revertir la acción {delta.tipo_accion}")