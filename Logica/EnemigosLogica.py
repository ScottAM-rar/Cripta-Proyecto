
from DTO.ActorDTO import EnemigoDTO
from Logica.ActorLogica import ActorLogica
from DTO.ActorDTO import ActorDTO
from DTO.SalaDTO import SalaDTO
class EnemigoLogica(ActorLogica):


    def __init__(self, enemigo : EnemigoDTO | None):
        self.enemigo: EnemigoDTO | None = enemigo

    def mover_enemigo(self,sala_destino: SalaDTO) -> None:
        self._mover(self.enemigo,sala_destino)

    def atacarJugador(self,jugador: ActorDTO):
        self._atacar(self.enemigo,jugador)
    