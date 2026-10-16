from Logica.EstadoJuegoLogica import *
from DTO.FinPartidaDTO import FinPartidaDTO
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario
from adaptadores.extension import ruta_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS


class EstadoJuegoServicio:
    def __init__(self, semilla: int = None, cripta: str = None, comunicacion=None, offline: bool = False):
        self._estadoJuegoLogica = EstadoJuegoLogica(semilla, cripta, comunicacion, offline)

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

    def iniciarJuego(self, cripta: str, semilla=None, offline: bool | None = None):
        self._estadoJuegoLogica.iniciarJuego(cripta,semilla,offline)

    def repetirPartida(self, archivo: str) -> list[ResultadoEventoDTO]:
        return self._estadoJuegoLogica.repetirPartida(archivo)

    def guardarLog(self, nombre_archivo: str) -> None:
        self._estadoJuegoLogica.guardarLog(nombre_archivo)

    def guardarPartida(self, nombre_archivo: str) -> None:
        """Guarda la partida en un archivo binario. El modelo solo entrega su estado; el archivo lo escribe el adaptador."""
        estado = self._estadoJuegoLogica.exportar_estado()
        if estado.fin:
            raise ValueError("No se puede guardar una partida que ya terminó")
        ruta = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS, crear_carpeta=True)
        AlmacenPartidaBinario(ruta).guardar(estado)

    def cargarPartida(self, nombre_archivo: str) -> None:
        """Carga una partida guardada. Un archivo inválido se rechaza antes de tocar la partida actual."""
        ruta = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS)
        estado = AlmacenPartidaBinario(ruta).cargar()
        self._estadoJuegoLogica.restaurar_estado(estado)

    def getJudador(self):
        return self._estadoJuegoLogica.obtenerJugador()

    def finPartida(self) -> FinPartidaDTO:
        return self._estadoJuegoLogica.finPartida()

    def terminado(self) -> tuple[bool, str]:
        return self._estadoJuegoLogica.terminado()
    