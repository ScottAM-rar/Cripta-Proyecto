from Logica.EstadoJuegoLogica import *
from DTO.FinPartidaDTO import FinPartidaDTO
from DTO.ResultadoVerificacionDTO import ResultadoVerificacion
from Logica import VerificacionResolubilidad
from Logica.ReporteVerificacion import lineas_reporte
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario
from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from adaptadores.AlmacenPuntajes import AlmacenPuntajes, MAX_NOMBRE
from DTO.RegistroPuntajeDTO import RegistroPuntajeDTO
from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Logica.ordenamiento import ordenar_adaptativo
from adaptadores.fabrica import crear_servicio
from adaptadores.extension import ruta_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS


# El controlador atrapa este rechazo sin importar la lógica (capacidad 011, research D1).
CriptaNoResoluble = VerificacionResolubilidad.CriptaNoResoluble


class EstadoJuegoServicio:
    MAX_NOMBRE_JUGADOR = MAX_NOMBRE      # largo máximo del nombre en la tabla de puntajes

    def __init__(self, semilla: int = None, cripta: str = None, comunicacion=None, offline: bool = False, k_checkpoint: int | None = None):
        self._offline = offline
        if cripta is not None and comunicacion is None:
            comunicacion = crear_servicio(offline=offline)
        self._estadoJuegoLogica = EstadoJuegoLogica(semilla, cripta, comunicacion)
        if k_checkpoint is not None:
            self._estadoJuegoLogica.k_checkpoint = k_checkpoint
        self._almacenLog: AlmacenLogTexto | None = None
        self.almacenPuntajes = AlmacenPuntajes()       # reemplazable (p. ej. para pruebas con otra ruta)
        self._puntajeRegistrado = False
        self._esRepeticion = False
        if self._estadoJuegoLogica.iniciado:
            self._abrirLog(None)

    @property
    def k_checkpoint(self) -> int:
        return self._estadoJuegoLogica.k_checkpoint

    @k_checkpoint.setter
    def k_checkpoint(self, valor: int) -> None:
        self._estadoJuegoLogica.k_checkpoint = valor

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

    def iniciarJuego(self, cripta: str, semilla=None, offline: bool | None = None, nombre_log: str | None = None,
                     forzar: bool = False):
        """nombre_log=None: el log de la partida se llama solo (cripta, semilla y fecha-hora).
        forzar (capacidad 003, FR-340): iniciar aunque la cripta no sea resoluble; se pasa a la lógica."""
        AlmacenLogTexto(nombre_log).comprobar_nombre()      # antes de empezar: un nombre repetido no deja la partida a medias
        self._asegurarServicio(offline)
        self._estadoJuegoLogica.iniciarJuego(cripta, semilla, forzar=forzar)
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

    def repetirPartida(self, archivo: str, hasta: int | None = None) -> list[ResultadoEventoDTO] | ResultadoReplayHastaDTO:
        """Reproduce un log. La reproducción no graba un log nuevo."""
        log = AlmacenLogTexto.leer(archivo)
        self._asegurarServicio()
        self._estadoJuegoLogica.registrador_log = None
        self._almacenLog = None
        self._esRepeticion = True       # una repetición no es una partida nueva: no entra a la tabla de puntajes
        return self._estadoJuegoLogica.repetirPartida(log, hasta=hasta)

    def consultarHistoria(self, instante: int | None = None, accion: int | None = None) -> ResumenEstadoDTO:
        """Consulta el estado de la partida en un instante virtual o acción pasados (capacidad 004).
        No altera en absoluto la partida en curso.

        Lanza ValueError si:
        - El juego no ha sido iniciado ("El juego no ha sido iniciado").
        - No se indica exactamente uno de los dos parámetros.
        - instante o accion es bool o no es entero.
        - instante < 0 o instante > reloj.tiempo_actual.
        - accion < 1 o accion > N + 1.
        """
        if not self._estadoJuegoLogica.iniciado:
            raise ValueError("El juego no ha sido iniciado")

        if (instante is None) == (accion is None):
            raise ValueError("Indica exactamente uno: instante (historia <t>) o accion (historia #k)")

        if instante is not None:
            if isinstance(instante, bool) or not isinstance(instante, int) or instante < 0:
                raise ValueError("El instante debe ser un entero mayor o igual que 0")
            reloj_actual = self._estadoJuegoLogica.estadoJuego.reloj.tiempo_actual
            if instante > reloj_actual:
                raise ValueError(f"El instante {instante} aún no ha ocurrido (reloj actual: {reloj_actual}).")
            return self._estadoJuegoLogica._reconstruirHastaInstante(instante)

        if accion is not None:
            if isinstance(accion, bool) or not isinstance(accion, int):
                raise ValueError("El número de acción debe ser un entero mayor o igual que 1")
            if accion < 1:
                raise ValueError("El número de acción debe ser mayor o igual que 1.")
            N = self._estadoJuegoLogica.acciones_linea_tiempo
            if accion > N + 1:
                raise ValueError(f"La acción #{accion} aún no ha ocurrido (acciones vigentes: {N}).")
            if accion == N + 1:
                return self._estadoJuegoLogica._extraerResumenEstadoActual(
                    self._estadoJuegoLogica.estadoJuego.reloj.tiempo_actual, N
                )
            return self._estadoJuegoLogica._reconstruirHastaAccion(accion)

    def guardarPartida(self, nombre_archivo: str) -> None:
        """Guarda la partida en un archivo binario. El modelo solo entrega su estado; el archivo lo escribe el adaptador."""
        estado = self._estadoJuegoLogica.exportar_estado()
        estado.offline = self._offline      # el modelo no sabe de dónde salen los datos; el servicio sí
        if estado.fin:
            raise ValueError("No se puede guardar una partida que ya terminó")
        ruta = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS, crear_carpeta=True)
        AlmacenPartidaBinario(ruta).guardar(estado)

    def obtenerPuntoControlReciente(self, k: int) -> PuntoControlDTO | None:
        """Obtiene el punto de control más reciente con acciones <= k."""
        return self._estadoJuegoLogica.obtenerPuntoControlReciente(k)

    def restaurarDesdePuntoControl(self, punto: PuntoControlDTO) -> None:
        """Restaura la partida desde un punto de control."""
        self._estadoJuegoLogica.restaurarDesdePuntoControl(punto)

    def cargarPartida(self, nombre_archivo: str, k_checkpoint: int | None = None) -> None:
        """Carga una partida guardada. Un archivo inválido se rechaza antes de tocar la partida actual."""
        ruta = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS)
        estado = AlmacenPartidaBinario(ruta).cargar()
        if self._estadoJuegoLogica.comunicacion is None:
            self._offline = estado.offline
            self._asegurarServicio()        # se usa el mismo origen de datos con el que se guardó la partida
        self._estadoJuegoLogica.restaurar_estado(estado)
        if k_checkpoint is not None:
            self._estadoJuegoLogica.k_checkpoint = k_checkpoint
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

    def mapaConocido(self):
        """Mapa conocido del jugador (MapaConocidoDTO): solo salas exploradas con sus salidas; las avistadas, como destino sin
        nombre. Consultarlo no es una acción: no avanza el reloj, no entra al historial del pergamino ni al log (FR-218)."""
        return self._estadoJuegoLogica.instantaneaMapaConocido()

    def iniciarViaje(self, destino: int):
        """Valida la orden «ir a» y deja el viaje en curso sin dar pasos (API paso a paso; ver avanzarViaje)."""
        return self._estadoJuegoLogica.iniciarViaje(destino)

    def avanzarViaje(self):
        """Da un paso del viaje en curso. Para pruebas, la API falsa y --bench; la consola usa irA."""
        return self._estadoJuegoLogica.avanzarViaje()

    def cancelarViaje(self) -> None:
        self._estadoJuegoLogica.cancelarViaje()

    def irA(self, destino: int):
        """Viaja hasta la sala explorada `destino` por la ruta más barata conocida (capacidad 006). Una orden rechazada
        no consume tiempo ni cuenta como acción. Devuelve un ResultadoViajeDTO."""
        resultado = self._estadoJuegoLogica.iniciarViaje(destino)
        if self._estadoJuegoLogica.viaje_activo is None:
            return resultado
        return self._estadoJuegoLogica.ejecutarViaje()

    def vistaSalaActual(self):
        """La sala actual en formato de conocimiento (SalaConocidaDTO), para mostrar sus salidas sin revelar lo no explorado."""
        return self._estadoJuegoLogica.vistaSalaActual()

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

    def advertenciasDeDatos(self) -> list[str]:
        """Datos inválidos de la cripta que se corrigieron al leerlos (costos de salida, rangos de cazador). Solo lee."""
        comunicacion = self._estadoJuegoLogica.comunicacion
        return list(getattr(comunicacion, "advertencias", []))

    def avisoLlaves(self) -> str | None:
        """Aviso de que no se pudo obtener la ubicación de las llaves (capacidad 009, FR-313), o None si no hay partida
        o no hay aviso. Solo lee."""
        logica = self._estadoJuegoLogica
        if not logica.iniciado:
            return None
        return logica.avisoLlaves

    def verificar(self, cripta_id: str, offline: bool | None = None) -> ResultadoVerificacion:
        """Verificación de resolubilidad de una cripta (capacidad 003, FR-330, FR-344). No inicia partida, no abre log
        ni usa la vista. Nunca lanza por falta de datos: devuelve resoluble=None con motivo_error (FR-343)."""
        self._asegurarServicio(offline)
        return VerificacionResolubilidad.verificar(self._estadoJuegoLogica.comunicacion, cripta_id)

    def avisoResolubilidad(self) -> str | None:
        """Aviso de la verificación al iniciar (cripta no resoluble iniciada con --forzar, o verificación no
        disponible), o None si no hay partida o no hay aviso. Se muestra solo al iniciar (FR-340). Solo lee."""
        logica = self._estadoJuegoLogica
        if not logica.iniciado:
            return None
        return logica.avisoResolubilidad

    def lineasDeReporte(self, resultado: ResultadoVerificacion) -> list[str]:
        """Las líneas del reporte de resolubilidad de un resultado (capacidad 011, FR-301, FR-302). Es el mismo texto de la
        003, sin cambios; sirve a `--verificar` (que ya tiene el resultado) y a la pantalla de inicio. Solo lee."""
        return lineas_reporte(resultado)

    def reporteVerificacion(self) -> list[str] | None:
        """Líneas del reporte de la verificación de la partida recién iniciada (capacidad 011, FR-301), o None si no hay
        partida o no se verificó (sin llaves, FR-313 de la 009; partida cargada o repetida). Solo lee."""
        logica = self._estadoJuegoLogica
        resultado = getattr(logica, "resultadoVerificacion", None)
        if not logica.iniciado or resultado is None:
            return None
        return lineas_reporte(resultado)

    def tiempoActual(self) -> int:
        """Instante del reloj virtual de la partida en curso, para la pantalla de sala (capacidad 011, FR-306). Solo lee."""
        return self._estadoJuegoLogica.estadoJuego.reloj.tiempo_actual

    def puntaje(self) -> int:
        """Puntaje de la partida en curso, para el resumen de fin de partida (capacidad 011, FR-307). Solo lee."""
        return self._estadoJuegoLogica.obtenerPuntaje()

    def terminado(self) -> tuple[bool, str]:
        return self._estadoJuegoLogica.terminado()

    def ultimosMensajes(self) -> list[str]:
        """Los últimos mensajes del juego (máximo 20, §4.8), del más viejo al más reciente."""
        return self._estadoJuegoLogica.ultimosMensajes()

    def reporteSolicitudes(self):
        """Solicitudes de red, presupuesto y caché de la cripta en juego (§5.1), o None si aún no hay cripta."""
        return self._estadoJuegoLogica.reporteSolicitudes()
    