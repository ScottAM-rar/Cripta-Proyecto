from Logica.EstadoJuegoLogica import *
from DTO.FinPartidaDTO import FinPartidaDTO
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario
from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from adaptadores.AlmacenPuntajes import AlmacenPuntajes, MAX_NOMBRE
from DTO.RegistroPuntajeDTO import RegistroPuntajeDTO
from Logica.ordenamiento import ordenar_adaptativo
from adaptadores.fabrica import crear_servicio
from adaptadores.extension import ruta_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS


class EstadoJuegoServicio:
    MAX_NOMBRE_JUGADOR = MAX_NOMBRE      # largo máximo del nombre en la tabla de puntajes

    def __init__(self, semilla: int = None, cripta: str = None, comunicacion=None, offline: bool = False):
        self._offline = offline
        if cripta is not None and comunicacion is None:
            comunicacion = crear_servicio(offline=offline)
        self._estadoJuegoLogica = EstadoJuegoLogica(semilla, cripta, comunicacion)
        self._almacenLog: AlmacenLogTexto | None = None
        self.almacenPuntajes = AlmacenPuntajes()       # reemplazable (p. ej. para pruebas con otra ruta)
        self._puntajeRegistrado = False
        self._esRepeticion = False
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
        self._puntajeRegistrado = self._esRepeticion = False
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
        self._esRepeticion = True       # una repetición no es una partida nueva: no entra a la tabla de puntajes
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
        self._puntajeRegistrado = self._esRepeticion = False
        self._abrirLog(None)      # la partida cargada sigue en un log nuevo que ya incluye las acciones anteriores

    def siguienteObjetoInventario(self) -> bool:
        """Mueve el cursor del inventario al siguiente objeto. False si ya estaba en el último; ValueError si está vacío."""
        return self._estadoJuegoLogica.siguienteObjetoInventario()

    def anteriorObjetoInventario(self) -> bool:
        """Mueve el cursor del inventario al objeto anterior. False si ya estaba en el primero; ValueError si está vacío."""
        return self._estadoJuegoLogica.anteriorObjetoInventario()

    def vistaInventario(self, criterio: str | None = None) -> list:
        """Los objetos del inventario en su orden real, o en una vista ordenada por "peso", "valor" o "nombre" (§4.5).
        ValueError si el criterio no es válido."""
        return self._estadoJuegoLogica.vistaInventario(criterio)

    def objetoActualInventario(self):
        """El objeto donde está el cursor del inventario, o None si el inventario está vacío."""
        inventario = self._estadoJuegoLogica.obtenerJugador().inventario
        return None if inventario.actual is None else inventario.mostrar_objeto_actual()

    def getJudador(self):
        return self._estadoJuegoLogica.obtenerJugador()

    def finPartida(self) -> FinPartidaDTO:
        return self._estadoJuegoLogica.finPartida()

    def registrarPuntaje(self, nombre: str) -> RegistroPuntajeDTO:
        """Guarda en la tabla de puntajes local la partida que acaba de terminar, a nombre de `nombre` (máx. 15 caracteres).
        Falla si la partida no terminó, si es una repetición (--replay), si ya se registró o si el nombre no es válido."""
        if self._esRepeticion:
            raise ValueError("Una repetición no se registra en la tabla de puntajes")
        if self._puntajeRegistrado:
            raise ValueError("El puntaje de esta partida ya fue registrado")
        fin = self._estadoJuegoLogica.finPartida()      # falla si la partida no ha terminado
        registro = RegistroPuntajeDTO(
            AlmacenPuntajes.validar_nombre(nombre), fin.id_Cripta, fin.vers_Cripta or "",
            fin.acciones_jugador, fin.cantEnemigosDerrotados, fin.tiempoReloj, fin.victoria,
        )
        self.almacenPuntajes.agregar(registro)
        self._puntajeRegistrado = True
        return registro

    def tablaPuntajes(self) -> list[RegistroPuntajeDTO]:
        """La tabla de puntajes, del mejor al peor: primero las victorias, luego menos tiempo, menos acciones y más
        enemigos derrotados."""
        registros = self.almacenPuntajes.leer_todos()
        return ordenar_adaptativo(
            registros,
            key=lambda r: (0 if r.victoria else 1, r.tiempo_final, r.acciones_jugador, -r.enemigos_derrotados),
        )

    def terminado(self) -> tuple[bool, str]:
        return self._estadoJuegoLogica.terminado()

    def ultimosMensajes(self) -> list[str]:
        """Los últimos mensajes del juego (máximo 20, §4.8), del más viejo al más reciente."""
        return self._estadoJuegoLogica.ultimosMensajes()

    def reporteSolicitudes(self):
        """Solicitudes de red, presupuesto y caché de la cripta en juego (§5.1), o None si aún no hay cripta."""
        return self._estadoJuegoLogica.reporteSolicitudes()
    