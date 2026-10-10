from Logica.EstadoJuegoLogica import *


class EstadoJuegoServicio:
    def __init__(self, estadoJuego: EstadoJuego, semilla: int = None):
        self._estadoJuegoLogica = EstadoJuegoLogica(estadoJuego, semilla)

    def accionJugador(self,evento:EventoDTO):
        return self._estadoJuegoLogica.accionJugador(evento)

    def tieneLlave(self,id_llave:str):
        return self._estadoJuegoLogica.tieneLlave(id_llave)