from Logica.EstadoJuegoLogica import *
from DTO.FinPartidaDTO import FinPartidaDTO


class EstadoJuegoServicio:
    def __init__(self, semilla: int = None, cripta: str = None):
        self._estadoJuegoLogica = EstadoJuegoLogica(semilla,cripta)

    def accionJugador(self,evento:EventoDTO):
        return self._estadoJuegoLogica.accionJugador(evento)

    def tieneLlave(self,id_llave:str):
        return self._estadoJuegoLogica.tieneLlave(id_llave)

    def listarCriptas(self) -> list[str]:
        return self._estadoJuegoLogica.listarCriptas()

    def obtenerIdCripta(self, posicion: int) -> str:
        return self._estadoJuegoLogica.obtenerIdCripta(posicion)

    def obtenerSala(self, id_sala: int) -> SalaDTO:
        return self._estadoJuegoLogica.ingresarEnSala(id_sala)

    def iniciarJuego(self, cripta: str, semilla=None, offline: bool = False):
        self._estadoJuegoLogica.iniciarJuego(cripta,semilla,offline)

    def repetirPartida(self, archivo: str) -> list[ResultadoEventoDTO]:
        return self._estadoJuegoLogica.repetirPartida(archivo)

    def guardarLog(self, nombre_archivo: str) -> None:
        self._estadoJuegoLogica.guardarLog(nombre_archivo)

    def guardarPartida(self, nombre_archivo: str) -> None:
        self._estadoJuegoLogica.guardarPartida(nombre_archivo)

    def cargarPartida(self, nombre_archivo: str) -> None:
        self._estadoJuegoLogica.cargarPartida(nombre_archivo)

    def getJudador(self):
        return self._estadoJuegoLogica.obtenerJugador()

    def finPartida(self) -> FinPartidaDTO:
        return self._estadoJuegoLogica.finPartida()

    def terminado(self) -> tuple[bool, str]:
        return self._estadoJuegoLogica.terminado()
    