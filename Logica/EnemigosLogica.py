
from DTO.ActorDTO import EnemigoDTO
from Logica.ActorLogica import ActorLogica
from DTO.ActorDTO import ActorDTO
from DTO.SalaDTO import SalaDTO
from Logica.ComportamientoEnemigo import ComportamientoEnemigo
from Logica.ComportamientoFactory import ComportamientoFactory
from DTO.EventoDTO import EventoDTO
class EnemigoLogica(ActorLogica):


    def __init__(self, enemigo : EnemigoDTO | None):
        self.enemigo: EnemigoDTO | None = enemigo
        comp =  ComportamientoFactory.crearComportamiento(enemigo.comportamiento)
        if comp == None:
            raise ValueError("El comportamiento del enemigo NO existe")
        self._comportamiento: ComportamientoEnemigo = comp

    def mover_enemigo(self, sala_actual: SalaDTO, direccion: str) -> None:
        self._mover(self.enemigo, sala_actual, direccion)

    def atacarJugador(self,jugador: ActorDTO):
        self._atacar(self.enemigo,jugador)

    def decidirAccion(self,jugador: ActorDTO, salas: list[SalaDTO]):
        if self.enemigo.vida_actual <= 0:
            return False, "ESTA MUERTO", None
        mensaje = ""
        if jugador.id_sala_actual == self.enemigo.id_sala_actual:
            self.atacarJugador(jugador)
            mensaje = "ATACÓ AL JUGADOR"
        else:
            mensaje = self._comportamiento.acción(self.enemigo,salas)

        eventoNuevo = EventoDTO(100,0,self.enemigo,"ACCION_ENEMIGO",[jugador])

        return True, mensaje, eventoNuevo

        
    