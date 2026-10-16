from Logica.EstadoJuegoLogica import *
from DTO.FinPartidaDTO import FinPartidaDTO
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario
from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from adaptadores.fabrica import crear_servicio
from adaptadores.extension import ruta_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS


class EstadoJuegoServicio:
    def __init__(self, semilla: int = None, cripta: str = None, comunicacion=None, offline: bool = False):
        self._offline = offline
        if cripta is not None and comunicacion is None:
            comunicacion = crear_servicio(offline=offline)
        self._estadoJuegoLogica = EstadoJuegoLogica(semilla, cripta, comunicacion)
        self._almacenLog: AlmacenLogTexto | None = None
        if self._estadoJuegoLogica.iniciado:
            self._abrirLog(None)

    def _asegurarServicio(self, offline: bool | None = None) -> None:
        """Arma el servicio de criptas (red o disco) si todavía no hay uno. El modelo solo recibe el resultado.
        offline=True/False cambia el origen de los datos; None conserva el actual."""
        logica = self._estadoJuegoLogica
        if offline is not None and offline != self._offline:
            self._offline = offline
            logica.comunicacion = None
        if logica.comunicacion is None:
            logica.comunicacion = crear_servicio(offline=self._offline)

    def accionJugador(self,evento:EventoDTO):
        return self._estadoJuegoLogica.accionJugador(evento)

    def tieneLlave(self,id_llave:str):
        return self._estadoJuegoLogica.tieneLlave(id_llave)

    def listarCriptas(self) -> list[str]:
        self._asegurarServicio()
        return self._estadoJuegoLogica.listarCriptas()

    def obtenerIdCripta(self, posicion: int) -> str:
        self._asegurarServicio()
        return self._estadoJuegoLogica.obtenerIdCripta(posicion)

    def obtenerSala(self, id_sala: int) -> SalaDTO:
        return self._estadoJuegoLogica.ingresarEnSala(id_sala)

    def iniciarJuego(self, cripta: str, semilla=None, offline: bool | None = None, nombre_log: str | None = None):
        """nombre_log=None: el log de la partida se llama solo (cripta, semilla y fecha-hora)."""
        AlmacenLogTexto(nombre_log).comprobar_nombre()      # antes de empezar: un nombre repetido no deja la partida a medias
        self._asegurarServicio(offline)
        self._estadoJuegoLogica.iniciarJuego(cripta,semilla)
        self._abrirLog(nombre_log)

    def _abrirLog(self, nombre: str | None) -> None:
        """Crea el log (append-only) de la partida en curso y se lo entrega al modelo para que avise cada acción."""
        logica = self._estadoJuegoLogica
        logica.registrador_log = None
        almacen = AlmacenLogTexto(nombre)
        almacen.abrir(logica.exportar_log())
        logica.registrador_log = almacen
        self._almacenLog = almacen

    def nombreLog(self) -> str | None:
        """Nombre del archivo donde se está grabando la partida (para mostrarlo o usarlo con --replay)."""
        return None if self._almacenLog is None else self._almacenLog.nombre

    def repetirPartida(self, archivo: str) -> list[ResultadoEventoDTO]:
        """Reproduce un log. La reproducción no graba un log nuevo."""
        log = AlmacenLogTexto.leer(archivo)
        self._asegurarServicio()
        self._estadoJuegoLogica.registrador_log = None
        self._almacenLog = None
        return self._estadoJuegoLogica.repetirPartida(log)

    def guardarPartida(self, nombre_archivo: str) -> None:
        """Guarda la partida en un archivo binario. El modelo solo entrega su estado; el archivo lo escribe el adaptador."""
        estado = self._estadoJuegoLogica.exportar_estado()
        estado.offline = self._offline      # el modelo no sabe de dónde salen los datos; el servicio sí
        if estado.fin:
            raise ValueError("No se puede guardar una partida que ya terminó")
        ruta = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS, crear_carpeta=True)
        AlmacenPartidaBinario(ruta).guardar(estado)

    def cargarPartida(self, nombre_archivo: str) -> None:
        """Carga una partida guardada. Un archivo inválido se rechaza antes de tocar la partida actual."""
        ruta = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS)
        estado = AlmacenPartidaBinario(ruta).cargar()
        if self._estadoJuegoLogica.comunicacion is None:
            self._offline = estado.offline
            self._asegurarServicio()        # se usa el mismo origen de datos con el que se guardó la partida
        self._estadoJuegoLogica.restaurar_estado(estado)
        self._abrirLog(None)      # la partida cargada sigue en un log nuevo que ya incluye las acciones anteriores

    def getJudador(self):
        return self._estadoJuegoLogica.obtenerJugador()

    def finPartida(self) -> FinPartidaDTO:
        return self._estadoJuegoLogica.finPartida()

    def terminado(self) -> tuple[bool, str]:
        return self._estadoJuegoLogica.terminado()
    