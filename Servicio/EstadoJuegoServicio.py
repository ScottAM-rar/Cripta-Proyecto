from Logica.EstadoJuegoLogica import *


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

    def iniciarJuego(self, cripta: str):
        self._estadoJuegoLogica.iniciarJuego(cripta)
    