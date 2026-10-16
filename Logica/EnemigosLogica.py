
from DTO.ActorDTO import EnemigoDTO
import random
from Logica.ActorLogica import ActorLogica
from DTO.ActorDTO import ActorDTO
from DTO.SalaDTO import SalaDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.ComportamientoEnemigo import ComportamientoEnemigo
from Logica.ComportamientoFactory import ComportamientoFactory
from DTO.EventoDTO import EventoDTO
class EnemigoLogica(ActorLogica):


    def __init__(self, enemigo : EnemigoDTO | None, semilla: int = None, azar: random.Random | None = None):
        self.setEnemigo(enemigo)
        self.semilla = semilla
        # Misma fuente de azar que usa el jugador (la crea GestorEventos)
        self.azar = azar if azar is not None else random.Random(semilla)

    def setEnemigo(self,enemigo: EnemigoDTO | None):
        self.enemigo: EnemigoDTO | None = enemigo
        if enemigo is None:
            self._comportamiento: ComportamientoEnemigo | None = None
            return

        comp = ComportamientoFactory.crearComportamiento(enemigo.comportamiento)
        if comp is None:
            raise ValueError("No existe el comportamiento creado")
        self._comportamiento = comp

    def mover_enemigo(self, sala_actual: SalaDTO, direccion: str) -> None:
        respuesta = self._mover(self.enemigo, sala_actual, direccion)
        if(respuesta.exito == True):
            respuesta.mensaje = f"El enemigo {self.enemigo.id_instancia} se ha movido a la sala {self.enemigo.id_sala_actual}"
        return respuesta

    def atacarJugador(self,jugador: ActorDTO):
        if jugador.vida_actual <= 0:
            return ResultadoEventoDTO(False, f"El enemigo {self.enemigo.id_instancia} no atacó al jugador ya que está muerto")
        if self.enemigo.id_sala_actual != jugador.id_sala_actual:
            return ResultadoEventoDTO(False, f"El enemigo {self.enemigo.id_instancia} no puede atacar: el jugador no está en su sala")
        self._atacar(self.enemigo, jugador, self.azar)
        return ResultadoEventoDTO(True,f"El enemigo {self.enemigo.id_instancia} ha atacado al jugador causando daño")

    def decidirAccion(self,jugador: ActorDTO, salas: list[SalaDTO], tiempo_actual: int | None = None)-> ResultadoEventoDTO:
        if self.enemigo is None:
            raise ValueError("No se puede decidir acciones sobre un enemigo que no existe")
        if self.enemigo.vida_actual <= 0:
            return ResultadoEventoDTO(False, "ESTA MUERTO")
        if jugador.id_sala_actual == self.enemigo.id_sala_actual:
            accion = self.atacarJugador(jugador)
        else:
            mensaje = f"El enemigo {self.enemigo.id_instancia} " + self._comportamiento.acción(self.enemigo,salas,self.azar,tiempo_actual)
            accion = ResultadoEventoDTO(True, mensaje)
        eventoNuevo = EventoDTO(100,0,self.enemigo,"ACCION_ENEMIGO",[jugador])

        accion.eventoResultado = eventoNuevo
        return accion

        
    