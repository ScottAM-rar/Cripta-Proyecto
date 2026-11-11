from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import *
from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import JugadorDTO, EnemigoDTO
from DTO.FinPartidaDTO import FinPartidaDTO
from DTO.Objeto import Llave
from DTO.ResultadoReplayHastaDTO import ResultadoReplayHastaDTO
from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Logica.GestorEventos import GestorEventos, PERIODO_REGENERACION
from Logica.ActorLogica import ActorLogica
from Logica.JugadorLogica import JugadorLogica
from DTO.LogPartidaDTO import LogPartidaDTO
from Logica.LogEventos import LogEventos, ReferenciaEvento, RegistroEvento, TIPOS_CURSOR_INVENTARIO
from Logica.BitacoraLogica import BitacoraLogica
from Logica.RelojVirtual import RelojVirtual
from Logica.RetrocesoLogica import RetrocesoLogica
from DTO.CambioDTO import CambioDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.FuenteCripta import FuenteCripta
from Logica.FuenteCripta import LlavesNoDisponibles
from DTO.LlavesDTO import UbicacionLlavesDTO
from Logica.CampoDeCostos import CampoDeCostos
from Logica.MapaCripta import MapaCripta
from Logica.MapaConocido import MapaConocido
from Logica.ordenamiento import ordenar_adaptativo
from DTO.EstadoGuardadoDTO import EstadoGuardadoDTO
from DTO.PuntoControlDTO import PuntoControlDTO
from Logica import EstadoGuardadoLogica
from Logica import VerificacionResolubilidad
from Logica.ReporteVerificacion import aviso_forzado

class EstadoJuegoLogica:
    def __init__(self,semilla: int = None, cripta: str = None, comunicacion: FuenteCripta | None = None):
        self.tiempoMovimientoJugador = 0
        self.accionesJugador = 0       # acciones del jugador que consumieron tiempo virtual (§2.12)
        self.acciones_linea_tiempo = 0  # acciones en la línea de tiempo vigente (reducido por pergamino)
        self.k_checkpoint = 10          # intervalo configurable de puntos de control (FR-414, FR-416)
        self.puntos_control: list[PuntoControlDTO] = []  # lista contigua ordenada de puntos de control (Principio I)
        # Quien arma el juego entrega el servicio de criptas ya listo; al modelo no le importa de dónde saca los datos.
        self.comunicacion = comunicacion
        
        self.iniciado = False
        self.fin = False
        self.motivoFin = None
        self.idCripta = None           # se fija al iniciar o restaurar una partida; None = todavía no hay cripta elegida
        self.precargaInicialHecha = False
        self.mapaConocido = None       # conocimiento del jugador (niebla de guerra, 002); None si la fuente no entrega el mapa
        self.registrador_log = None    # opcional: algo con agregar(linea); el modelo solo le avisa cada acción
        self.llaves = None             # UbicacionLlavesDTO de la cripta, o None si no se pidió o no se pudo (capacidad 009)
        self.avisoLlaves = None        # mensaje del último LlavesNoDisponibles, para mostrarlo (FR-313)
        
        if(cripta is not None):
            self.iniciarJuego(cripta)

    def exportar_estado(self) -> EstadoGuardadoDTO:
        """Instantánea de la partida en datos simples; no toca archivos ni red."""
        self._asegurarPuntoControlInicial()
        dto = EstadoGuardadoLogica.exportar(self)
        dto.k_checkpoint = self.k_checkpoint
        dto.acciones_linea_tiempo = self.acciones_linea_tiempo
        dto.puntos_control = list(self.puntos_control)
        return dto

    def _asegurarPuntoControlInicial(self) -> None:
        if getattr(self, "_es_repeticion", False):
            return
        if not self.puntos_control and self.iniciado and self.estadoJuego is not None:
            estado_dto = EstadoGuardadoLogica.exportar(self)
            long_bitacora = len(estado_dto.bitacora)
            long_log = len(estado_dto.acciones_log)
            estado_dto.bitacora = []
            estado_dto.acciones_log = []
            estado_dto.puntos_control = []
            reloj = getattr(self.estadoJuego, 'reloj', None)
            tiempo_reloj = reloj.tiempo_actual if reloj is not None else 0
            p0 = PuntoControlDTO(
                numero_punto=0,
                acciones_linea_tiempo=0,
                instante_reloj=tiempo_reloj,
                estado=estado_dto,
                longitud_bitacora=long_bitacora,
                longitud_acciones_log=long_log,
            )
            self.puntos_control.append(p0)

    def _verificarYCapturarPuntoControl(self) -> None:
        if self.fin or getattr(self, "_es_repeticion", False):
            return
        if not self.puntos_control:
            self._asegurarPuntoControlInicial()
        if not self.puntos_control:
            return
        ultimo_punto = self.puntos_control[-1]
        if self.acciones_linea_tiempo - ultimo_punto.acciones_linea_tiempo >= self.k_checkpoint:
            numero_punto = len(self.puntos_control)
            estado_dto = EstadoGuardadoLogica.exportar(self)
            long_bitacora = len(estado_dto.bitacora)
            long_log = len(estado_dto.acciones_log)
            estado_dto.bitacora = []
            estado_dto.acciones_log = []
            estado_dto.puntos_control = []
            reloj = getattr(self.estadoJuego, 'reloj', None)
            tiempo_reloj = reloj.tiempo_actual if reloj is not None else 0
            punto = PuntoControlDTO(
                numero_punto=numero_punto,
                acciones_linea_tiempo=self.acciones_linea_tiempo,
                instante_reloj=tiempo_reloj,
                estado=estado_dto,
                longitud_bitacora=long_bitacora,
                longitud_acciones_log=long_log,
            )
            self.puntos_control.append(punto)

    def _podarPuntosControlPosteriores(self, limite_acciones: int) -> None:
        """Poda los puntos de control con acciones_linea_tiempo > limite_acciones.
        Invariante plan.md §4 (T022): La poda asegura que los puntos de control supervivientes
        nunca tengan por delante acciones revertidas que ocurrieron antes de ellos.
        Cualquier acción revertida por el pergamino ocurrió estrictamente después del último punto superviviente,
        garantizando que la reconstrucción desde dicho punto base sea siempre coherente con la
        línea de tiempo vigente."""
        while self.puntos_control and self.puntos_control[-1].acciones_linea_tiempo > limite_acciones:
            self.puntos_control.pop()

    def obtenerPuntoControlReciente(self, k: int) -> PuntoControlDTO | None:
        """Retorna el punto de control más reciente con acciones_linea_tiempo <= k.
        Delega en la búsqueda binaria (T003)."""
        return self._buscarPuntoPorAcciones(k)

    # ------------------------------------------------------------------ T003 / PASO 0
    def _indicePuntoPorAcciones(self, k: int) -> int:
        """Búsqueda binaria manual (sin bisect) del índice del último punto con acciones_linea_tiempo <= k.
        Retorna -1 si no hay ningún punto que cumpla la condición.
        La lista puntos_control está ordenada de forma no decreciente por acciones_linea_tiempo.
        O(log M) donde M = len(puntos_control)."""
        izq, der = 0, len(self.puntos_control) - 1
        candidato = -1
        while izq <= der:
            medio = (izq + der) // 2
            if self.puntos_control[medio].acciones_linea_tiempo <= k:
                candidato = medio
                izq = medio + 1
            else:
                der = medio - 1
        return candidato

    def _buscarPuntoPorAcciones(self, k: int) -> 'PuntoControlDTO | None':
        """Retorna el último punto de control con acciones_linea_tiempo <= k, o None."""
        idx = self._indicePuntoPorAcciones(k)
        return self.puntos_control[idx] if idx >= 0 else None

    # ------------------------------------------------------------------ T004 / PASO 0
    def _indicePuntoPorInstante(self, t: int) -> int:
        """Búsqueda binaria manual (sin bisect) del índice del último punto con instante_reloj <= t.
        Retorna -1 si no hay ningún punto que cumpla la condición.
        La lista puntos_control está ordenada de forma no decreciente por instante_reloj.
        O(log M) donde M = len(puntos_control)."""
        izq, der = 0, len(self.puntos_control) - 1
        candidato = -1
        while izq <= der:
            medio = (izq + der) // 2
            if self.puntos_control[medio].instante_reloj <= t:
                candidato = medio
                izq = medio + 1
            else:
                der = medio - 1
        return candidato

    def _buscarPuntoPorInstante(self, t: int) -> 'PuntoControlDTO | None':
        """Retorna el último punto de control con instante_reloj <= t, o None."""
        idx = self._indicePuntoPorInstante(t)
        return self.puntos_control[idx] if idx >= 0 else None

    # ------------------------------------------------------------------ T005
    def _extraerResumenEstadoActual(self, instante: int, acciones: int) -> ResumenEstadoDTO:
        """Empaqueta el estado vivo de la instancia (self) en un ResumenEstadoDTO.
        Se llama tanto desde _armarResultadoReplayHasta (que añade sus propios campos en
        ResultadoReplayHastaDTO) como desde consultarHistoria (que devuelve ResumenEstadoDTO
        directamente).  No toca el log ni el reloj."""
        jugador = self.estadoJuego.jugador
        reloj   = self.estadoJuego.reloj

        id_sala   = jugador.id_sala_actual
        vida      = jugador.vida_actual
        ataque    = ActorLogica.ataque_efectivo(jugador)
        defensa   = ActorLogica.defensa_efectiva(jugador)
        velocidad = ActorLogica.velocidad_efectiva(jugador)

        inventario_llaves: list[str] = []
        inventario_objetos: list[str] = []
        if getattr(jugador, "inventario", None) is not None:
            nodo = jugador.inventario.cabeza
            while nodo is not None:
                obj = nodo.objeto
                if isinstance(obj, Llave):
                    inventario_llaves.append(obj.id_catalogo)
                else:
                    inventario_objetos.append(obj.nombre)
                nodo = nodo.siguiente

        efectos_activos: list[str] = []
        if getattr(jugador, "veneno", False):
            efectos_activos.append("veneno")
        if getattr(jugador, "modificador_velocidad", 0) != 0:
            efectos_activos.append("velocidad temporal")
        if getattr(jugador, "antorcha_encendida", False):
            efectos_activos.append("antorcha encendida")

        enemigos_sala: list[tuple[str, str, int]] = []
        if id_sala < len(self.estadoJuego.salas):
            sala = self.estadoJuego.salas[id_sala]
            if sala is not None and getattr(sala, "enemigos", None):
                for e in sala.enemigos:
                    if e.vida_actual > 0:
                        enemigos_sala.append((e.id_instancia, e.nombre, e.vida_actual))
                enemigos_sala = ordenar_adaptativo(enemigos_sala, key=lambda t: t[0])

        return ResumenEstadoDTO(
            instante=instante,
            acciones_jugador=acciones,
            id_sala_jugador=id_sala,
            vida_jugador=vida,
            ataque_jugador=ataque,
            defensa_jugador=defensa,
            velocidad_jugador=velocidad,
            inventario_llaves=inventario_llaves,
            inventario_objetos=inventario_objetos,
            efectos_activos=efectos_activos,
            enemigos_sala=enemigos_sala,
            partida_terminada=self.fin,
            motivo_terminacion=self.motivoFin if self.fin else None,
            mapa_conocido=None,
        )

    # ------------------------------------------------------------------ T005b
    def _planificarSegmento(
        self,
        punto_base: PuntoControlDTO | int | None = None,
        fin_log: int | None = None,
    ) -> list[int]:
        """Pasada 1 (simulación de clasificación, plan.md §3):
        Determina qué índices de registro del log corresponden a acciones vigentes en la
        línea de tiempo.

        No inspecciona el texto del id del objeto (Principio V). El tipo real se conoce hidratando
        una instancia aislada desde el punto base (bajo la guarda try/finally del singleton RetrocesoLogica)
        y construyendo cada evento con _crear_evento_repeticion para evaluar
        GestorEventos.es_uso_de_pergamino(evento).

        Por cada registro del segmento se anota si fue cursor, uso de pergamino u otra acción,
        más el reloj antes de aplicarlo. Una pila local (push por acción, pop por pergamino)
        da la lista de índices de acciones vigentes (E[0..m-1]).
        """
        # 1. Resolver el punto base (PuntoControlDTO) y el inicio del segmento
        if punto_base is None:
            if not self.puntos_control:
                self._asegurarPuntoControlInicial()
            base_dto = self.puntos_control[0] if self.puntos_control else None
            inicio_log = 0 if base_dto is None else base_dto.longitud_acciones_log
        elif isinstance(punto_base, PuntoControlDTO):
            base_dto = punto_base
            inicio_log = base_dto.longitud_acciones_log
        else:
            inicio_log = int(punto_base)
            base_dto = None
            for p in reversed(self.puntos_control):
                if p.longitud_acciones_log <= inicio_log:
                    base_dto = p
                    break
            if base_dto is None:
                if not self.puntos_control:
                    self._asegurarPuntoControlInicial()
                base_dto = self.puntos_control[0] if self.puntos_control else None

        # 2. Resolver el fin del segmento
        total_log = self.logEventos.cantidad
        if fin_log is None:
            fin_log = total_log
            if base_dto is not None:
                idx_base = self._indicePuntoPorAcciones(base_dto.acciones_linea_tiempo)
                if idx_base >= 0 and idx_base + 1 < len(self.puntos_control):
                    fin_log = self.puntos_control[idx_base + 1].longitud_acciones_log

        tope_fin = min(fin_log, total_log)
        if inicio_log >= tope_fin or base_dto is None:
            return []

        # 3. Pasada 1: Clasificación mediante instancia aislada hidratada
        snapshot, reloj_retro_ref = self._guardarSingletonRetroceso()
        try:
            aislada = self._hidratarInstanciaAislada(base_dto)

            registros_segmento = self.logEventos.obtener_registros_rango(inicio_log, tope_fin)
            marcas: list[tuple[int, str, int]] = []

            for offset, reg in enumerate(registros_segmento):
                idx = inicio_log + offset
                reloj_antes = aislada.estadoJuego.reloj.tiempo_actual

                if reg.tipo_accion in TIPOS_CURSOR_INVENTARIO:
                    aislada._repetirMovimientoDeCursor(reg.tipo_accion)
                    marcas.append((idx, "cursor", reloj_antes))
                    continue

                evento = aislada._crear_evento_repeticion(reg)
                es_pergamino = GestorEventos.es_uso_de_pergamino(evento)

                resultado = aislada.accionJugador(evento)
                if resultado.exito is False:
                    raise ValueError(
                        f"La reproducción no es fiel: {evento.tipo_accion} fue rechazada ({resultado.mensaje})"
                    )

                if es_pergamino:
                    marcas.append((idx, "pergamino", reloj_antes))
                else:
                    marcas.append((idx, "accion", reloj_antes))

            # 4. Pila local que produce los índices vigentes
            pila: list[int] = []
            for idx, tipo_marca, reloj_antes in marcas:
                if tipo_marca == "cursor":
                    continue
                elif tipo_marca == "pergamino":
                    if pila:
                        pila.pop()
                else:
                    pila.append(idx)

            return pila
        finally:
            self._restaurarSingletonRetroceso(snapshot, reloj_retro_ref)

    # ------------------------------------------------------------------ T014 / PASO 0 helper
    def _hidratarInstanciaAislada(self, punto_base: PuntoControlDTO) -> 'EstadoJuegoLogica':
        """Crea e hidrata una instancia aislada desde un punto de control.
        Código compartido entre _reconstruirHastaInstante y _reconstruirHastaAccion
        para evitar duplicación (plan.md §3).
        Configura _es_aislada = True para inhibir llamadas a la red/caché (T019/T020)."""
        aislada = EstadoJuegoLogica(comunicacion=self.comunicacion)
        aislada._es_aislada = True
        aislada._es_repeticion = True
        aislada.registrador_log = None

        EstadoGuardadoLogica.restaurar(aislada, punto_base.estado)
        aislada.acciones_linea_tiempo = punto_base.acciones_linea_tiempo
        aislada._es_aislada = True
        aislada._es_repeticion = True
        aislada.registrador_log = None
        aislada.puntos_control = []
        return aislada

    def _resolverSegmentoPorIndice(self, idx: int) -> tuple[PuntoControlDTO, int, int]:
        """Devuelve (punto_base, inicio_log, fin_log) del segmento delimitado por puntos_control[idx]
        y el siguiente punto de control (idx + 1), sin ningún recorrido lineal (O(1))."""
        if idx < 0:
            if not self.puntos_control:
                self._asegurarPuntoControlInicial()
            idx = 0 if self.puntos_control else -1
            if idx < 0:
                raise ValueError("No hay un punto de control disponible para la reconstrucción")
        punto_base = self.puntos_control[idx]
        inicio_log = punto_base.longitud_acciones_log
        if idx + 1 < len(self.puntos_control):
            fin_log = self.puntos_control[idx + 1].longitud_acciones_log
        else:
            fin_log = self.logEventos.cantidad
        return punto_base, inicio_log, fin_log

    def _resolverPuntoBaseYFinLog(self, punto_base: PuntoControlDTO) -> tuple[int, int]:
        """Mantiene compatibilidad con la firma anterior devolviendo (inicio_log, fin_log)."""
        idx = self._indicePuntoPorAcciones(punto_base.acciones_linea_tiempo)
        if idx >= 0 and self.puntos_control[idx] is punto_base:
            _, inicio, fin = self._resolverSegmentoPorIndice(idx)
            return inicio, fin
        inicio_log = punto_base.longitud_acciones_log
        fin_log = self.logEventos.cantidad
        return inicio_log, fin_log

    def _ejecutarPasada2(
        self,
        punto_base: PuntoControlDTO,
        inicio_log: int,
        fin_log: int,
        indices_vigentes: list[int],
        *,
        tope_instante: int | None = None,
        tope_vigente: int | None = None,
    ) -> 'EstadoJuegoLogica':
        """Ejecuta la pasada 2 fiel en una instancia aislada sobre el segmento [inicio_log, fin_log).
        Cuerpo común compartido entre _reconstruirHastaAccion y _reconstruirHastaInstante (PASO 0).
        Protege y restaura los 8 atributos del singleton global RetrocesoLogica y reloj.retroceso
        de forma determinista en un bloque try...finally."""
        snapshot, reloj_retro_ref = self._guardarSingletonRetroceso()
        try:
            aislada = self._hidratarInstanciaAislada(punto_base)
            tope_fin = min(fin_log, self.logEventos.cantidad)
            registros = self.logEventos.obtener_registros_rango(inicio_log, tope_fin)
            p_vigente = 0

            for offset, reg in enumerate(registros):
                idx = inicio_log + offset
                if aislada.fin:
                    break

                if reg.tipo_accion in TIPOS_CURSOR_INVENTARIO:
                    aislada._repetirMovimientoDeCursor(reg.tipo_accion)
                    continue

                evento = aislada._crear_evento_repeticion(reg)
                es_vigente = (p_vigente < len(indices_vigentes) and indices_vigentes[p_vigente] == idx)

                if es_vigente:
                    if tope_vigente is not None and p_vigente >= tope_vigente:
                        break
                    p_vigente += 1

                    if tope_instante is not None:
                        if aislada.estadoJuego.reloj.tiempo_actual >= tope_instante:
                            break
                        resultado = aislada.accionJugador(evento, tope=tope_instante)
                        if resultado.exito is False:
                            raise ValueError(
                                f"La reproducción no es fiel: {evento.tipo_accion} fue rechazada ({resultado.mensaje})"
                            )
                        if aislada.fin:
                            break
                        # Si el turno del jugador sigue pendiente en la agenda, su decisión es posterior a t: ya
                        # está todo lo que ocurre hasta t. Si ya salió de la agenda, el jugador decide en el reloj
                        # actual (<= t): se sigue leyendo el log, porque lo que viene antes de la próxima acción
                        # vigente (acciones revertidas y pergaminos de esa misma decisión) también es parte del
                        # estado en ese instante. La próxima acción vigente se detiene sola si reloj >= t.
                        if any(e.tipo_accion == "TURNO_JUGADOR" for e in aislada.estadoJuego.reloj.heap):
                            break
                    else:
                        resultado = aislada.accionJugador(evento)
                        if resultado.exito is False:
                            raise ValueError(
                                f"La reproducción no es fiel: {evento.tipo_accion} fue rechazada ({resultado.mensaje})"
                            )
                        if aislada.fin:
                            break
                else:
                    # Acción revertida o pergamino: aplicar sin tope para fidelidad de azar y estado
                    resultado = aislada.accionJugador(evento)
                    if resultado.exito is False:
                        raise ValueError(
                            f"La reproducción no es fiel: {evento.tipo_accion} fue rechazada ({resultado.mensaje})"
                        )
                    if aislada.fin:
                        break

            if tope_instante is not None and not aislada.fin and aislada.estadoJuego.reloj.tiempo_actual <= tope_instante:
                aislada._completarInstante(tope_instante)

            return aislada
        finally:
            self._restaurarSingletonRetroceso(snapshot, reloj_retro_ref)

    # ------------------------------------------------------------------ T014
    def _reconstruirHastaAccion(self, k: int) -> ResumenEstadoDTO:
        """Reconstruye el estado de la partida justo antes de la acción número k
        (1 <= k <= N) de la línea de tiempo vigente, mediante reproducción
        acotada y aislada desde el punto de control previo más cercano (plan.md §3).
        No altera en absoluto la partida viva.
        """
        # El estado justo antes de la acción k es aquel con k-1 acciones vigentes completadas.
        idx = self._indicePuntoPorAcciones(k - 1)
        punto_base, inicio_log, fin_log = self._resolverSegmentoPorIndice(idx)

        # Pasada 1: Clasificación de registros vigentes en el segmento
        indices_vigentes = self._planificarSegmento(punto_base, fin_log)

        # j = (k-1) - c : número de acciones vigentes a aplicar desde el punto base
        c = punto_base.acciones_linea_tiempo
        j = (k - 1) - c  # parar justo ANTES de aplicar la acción vigente E[j]

        # Pasada 2: Reproducción fiel en una nueva instancia aislada
        aislada = self._ejecutarPasada2(punto_base, inicio_log, fin_log, indices_vigentes, tope_vigente=j)
        instante_aislada = aislada.estadoJuego.reloj.tiempo_actual
        return aislada._extraerResumenEstadoActual(instante_aislada, k - 1)

    # ------------------------------------------------------------------ T008
    def _reconstruirHastaInstante(self, t: int) -> ResumenEstadoDTO:
        """Reconstruye el estado de la partida en el instante virtual t (0 <= t <= reloj_actual)
        mediante una reproducción acotada y aislada desde el punto de control previo más cercano (plan.md §3).
        No altera en absoluto la partida viva ni consume tiempo ni recursos de red.
        """
        reloj_vivo = self.estadoJuego.reloj.tiempo_actual
        if t > reloj_vivo:
            raise ValueError(f"El instante {t} aún no ha ocurrido (reloj actual: {reloj_vivo}).")
        if t == reloj_vivo:
            return self._extraerResumenEstadoActual(t, self.acciones_linea_tiempo)

        idx = self._indicePuntoPorInstante(t)
        punto_base, inicio_log, fin_log = self._resolverSegmentoPorIndice(idx)

        # Pasada 1: Clasificación de registros vigentes en el segmento
        indices_vigentes = self._planificarSegmento(punto_base, fin_log)

        # Pasada 2: Reproducción fiel en una nueva instancia aislada
        aislada = self._ejecutarPasada2(punto_base, inicio_log, fin_log, indices_vigentes, tope_instante=t)
        return aislada._extraerResumenEstadoActual(t, aislada.acciones_linea_tiempo)

    # ------------------------------------------------------------------ T006
    def _guardarSingletonRetroceso(self):
        """Captura los 8 atributos del singleton RetrocesoLogica y el puntero reloj.retroceso
        de la partida viva.  Devuelve (snapshot_tuple, reloj_retroceso_ref)."""
        retro = RetrocesoLogica()
        snapshot = (
            retro.cabeza,
            retro.cola,
            retro.actual,
            retro.reloj,
            retro.cantidad_actual,
            retro.cantidad_acciones,
            retro.tiempo_evento,
            retro.suspensiones,
        )
        reloj_retro_ref = None
        if self.iniciado and getattr(self, "estadoJuego", None) is not None:
            reloj_retro_ref = getattr(self.estadoJuego.reloj, "retroceso", None)
        return snapshot, reloj_retro_ref

    def _restaurarSingletonRetroceso(self, snapshot, reloj_retro_ref) -> None:
        """Reestablece el singleton RetrocesoLogica y el puntero reloj.retroceso de la partida
        viva a los valores capturados antes de la reconstrucción aislada.
        Invariante plan.md §1 y §4 (T023): Conservar íntegro el puntero reloj.retroceso y los 8
        atributos de RetrocesoLogica garantiza que los usos subsecuentes del pergamino de
        retroceso desapilen correctamente sin corrupción tras cualquier consulta historia."""
        retro = RetrocesoLogica()
        (
            retro.cabeza,
            retro.cola,
            retro.actual,
            retro.reloj,
            retro.cantidad_actual,
            retro.cantidad_acciones,
            retro.tiempo_evento,
            retro.suspensiones,
        ) = snapshot
        # Restaurar el puntero reloj.retroceso de la partida viva
        if self.iniciado and getattr(self, "estadoJuego", None) is not None:
            if reloj_retro_ref is not None:
                self.estadoJuego.reloj.retroceso = reloj_retro_ref

    def restaurarDesdePuntoControl(self, punto: PuntoControlDTO) -> None:
        """Restaura el estado completo del juego a partir de un punto de control y preserva los puntos hasta él."""
        self._exigirServicio()
        self._podarPuntosControlPosteriores(punto.acciones_linea_tiempo)

        bitacora_prefijo = []
        if getattr(self, "logEventosJuego", None) is not None:
            bitacora_prefijo = self.logEventosJuego.obtener_eventos()[:punto.longitud_bitacora]

        acciones_prefijo = []
        if getattr(self, "logEventos", None) is not None:
            acciones_prefijo = self.logEventos.obtener_acciones_cronologicas()[:punto.longitud_acciones_log]

        EstadoGuardadoLogica.restaurar(self, punto.estado)
        self.acciones_linea_tiempo = punto.acciones_linea_tiempo
        self._actualizarFichasEnUso()

        if bitacora_prefijo and not punto.estado.bitacora:
            self.logEventosJuego = BitacoraLogica()
            for ev in bitacora_prefijo:
                self.logEventosJuego.agregar_evento(ev)

        if acciones_prefijo and not punto.estado.acciones_log:
            for acc in acciones_prefijo:
                self.logEventos.agregar(acc)

    def restaurar_estado(self, estado: EstadoGuardadoDTO) -> None:
        """Deja la partida como estaba cuando se exportó `estado`. El historial del pergamino empieza vacío."""
        self._exigirServicio()
        EstadoGuardadoLogica.restaurar(self, estado)
        self.k_checkpoint = getattr(estado, "k_checkpoint", 10)
        self.acciones_linea_tiempo = getattr(estado, "acciones_linea_tiempo", 0)
        self.puntos_control = list(getattr(estado, "puntos_control", []))
        self._actualizarFichasEnUso()

    def _exigirServicio(self) -> None:
        if self.comunicacion is None:
            raise ValueError("El juego no tiene un servicio de criptas")

    def iniciarJuego(self, cripta: str, semilla: int = None, pedir_llaves: bool = True, forzar: bool = False):
        """pedir_llaves=False: la usa la reproducción, que no es una partida nueva (T058): no consulta las llaves ni
        avisa; si después hacen falta, se piden bajo demanda con obtenerLlaves().
        forzar (capacidad 003, FR-340): iniciar aunque la cripta no sea resoluble (ver _verificarAlIniciar). Una partida
        nueva verifica la cripta; pedir_llaves=False (reproducción) no verifica."""
        if self.iniciado:
            raise ValueError("No se puede iniciar un juego ya iniciado")
        self.resultadoVerificacion = None  # capacidad 003: cada inicio verifica de nuevo (o no verifica)
        self.avisoResolubilidad = None
        self._exigirServicio()
        if not self.comunicacion.existe_cripta(cripta):
            raise ValueError("No existe la cripta solicitada")
        self.semilla = 0 if semilla is None else semilla
        self.logEventos = LogEventos(self.semilla, cripta)
        self.logEventos.version_cripta = self.comunicacion.version_cripta(cripta)
        self.logEventos.version_catalogo = self.comunicacion.version_catalogo()
        self.logEventosJuego = BitacoraLogica()
        
        cantSalas = self.comunicacion.total_salas(cripta)
        salas = [None] * (cantSalas+1)
        relojvirtual = RelojVirtual()
        retroceso = RetrocesoLogica()
        retroceso.reiniciar()
        retroceso.reloj = relojvirtual
        relojvirtual.retroceso = retroceso
        jugador =self.comunicacion.crear_jugador(cripta)
        self.estadoJuego = EstadoJuego(relojvirtual,jugador,[],[],salas)
        self.gestorEventos = GestorEventos(
            self.estadoJuego.salas,
            jugador,
            self.ingresarEnSala,
            self.semilla,
            obtener_botin=self.comunicacion.objetos_que_suelta,
        )
        self.gestorEventos.reloj = relojvirtual
        campo, conocimiento = self._crearMapaYConocimiento(cripta, salas, jugador)
        self.gestorEventos.campo_de_costos = campo
        self.mapaConocido = conocimiento
        self.gestorEventos.mapa_conocido = conocimiento
        if conocimiento is not None:
            conocimiento.iniciar(jugador.id_sala_actual)       # conocimiento del instante 0: sin historial, no se deshace (FR-202, FR-215)
        self.jugadorLogica = JugadorLogica(jugador,self.semilla,self.gestorEventos.azar)
        self.logEventos.vaciar()
        self.idCripta = cripta
        if pedir_llaves:
            self.obtenerLlaves()       # partida nueva: la ubicación de las llaves se pide enseguida (FR-301)
            self._verificarAlIniciar(cripta, forzar)   # capacidad 003; puede lanzar CriptaNoResoluble (FR-339)
        self.iniciado = True
        self.registrador_log = None
        self.fin = False
        self.motivoFin = None

    def _crearMapaYConocimiento(self, cripta: str, salas: list, jugador):
        """Obtiene el esqueleto UNA vez y arma, compartiendo el mismo MapaCripta, el campo de costos de los cazadores y el
        conocimiento del jugador. Devuelve (campo, conocimiento); ambos None si la fuente no entrega el mapa."""
        obtener = getattr(self.comunicacion, "obtener_mapa", None)
        if obtener is None:
            return None, None
        mapa_dto = obtener(cripta)
        mapa = MapaCripta(mapa_dto)
        nombres = []
        for sala in mapa_dto.salas:
            nombres.append("" if sala is None else getattr(sala, "nombre", ""))
        conocimiento = MapaConocido(mapa, nombres, salas, jugador, RetrocesoLogica().registrar_cambio)
        return CampoDeCostos(mapa, jugador, salas), conocimiento

    def _verificarAlIniciar(self, cripta: str, forzar: bool) -> None:
        """Verificación de resolubilidad de una partida nueva (capacidad 003; data-model.md §5, research.md §7).

        Va después de obtenerLlaves() y antes de marcar la partida como iniciada, así que, si lanza, la partida no
        queda iniciada y el servicio no llega a abrir el registro de partida. Usa la misma operación que --verificar
        (FR-344) con las llaves que la partida ya pidió: no hace solicitudes nuevas (FR-341).
        - Sin llaves (FR-313): no verifica; queda el aviso de la 009 en avisoLlaves.
        - Resoluble: sin aviso.
        - No resoluble con forzar: aviso de una línea, que se muestra solo al iniciar (FR-340).
        - No resoluble sin forzar: CriptaNoResoluble (FR-339).
        - Error de datos: la partida no se bloquea; aviso con el motivo (FR-339, escenario H4-5).
        El resultado y el aviso no entran al log ni al estado guardado."""
        if self.llaves is None:
            return
        resultado = VerificacionResolubilidad.verificar(self.comunicacion, cripta, llaves=self.llaves)
        self.resultadoVerificacion = resultado
        if resultado.resoluble is None:
            self.avisoResolubilidad = f"{resultado.motivo_error} La verificación de resolubilidad no está disponible."
        elif resultado.resoluble is False:
            if not forzar:
                raise VerificacionResolubilidad.CriptaNoResoluble(resultado)
            self.avisoResolubilidad = aviso_forzado(resultado)

    def _crearCampoDeCostos(self, cripta: str, salas: list, jugador) -> CampoDeCostos | None:
        """Mapa del esqueleto completo + campo de costos hacia el jugador, para los cazadores (FR-117). Si la fuente
        no entrega el mapa, los cazadores no pueden decidir y fallan con un error claro."""
        return self._crearMapaYConocimiento(cripta, salas, jugador)[0]

    def obtenerLlaves(self) -> UbicacionLlavesDTO | None:
        """Único punto por el que el modelo pide la ubicación de las llaves (capacidad 009). Si ya la tiene, no pide
        nada. Si la fuente no puede darla, guarda el aviso en avisoLlaves y la partida sigue (FR-313). El fallo no se
        memoriza: otra llamada vuelve a pedir, y la fuente decide con lo guardado y el presupuesto si hace la solicitud.
        Las llaves y el aviso no entran al log ni al estado guardado."""
        if self.llaves is not None:
            return self.llaves
        # Con getattr, por compatibilidad con las fuentes de prueba antiguas que no lo tienen (como obtener_mapa).
        obtener = getattr(self.comunicacion, "ubicacion_llaves", None)
        if obtener is None:
            return None
        try:
            self.llaves = obtener(self.idCripta)
            self.avisoLlaves = None
        except LlavesNoDisponibles as error:
            self.llaves = None
            self.avisoLlaves = str(error)
        return self.llaves

    def _comprobarFinal(self):
        if self.jugadorLogica.esta_muerto():
            self.fin = True
            self.motivoFin = "El jugador ha muerto"
        elif self.jugadorLogica.estaEnSalaFinal(
            self.comunicacion.obtener_sala_salida(self.idCripta)
        ):
            self.fin = True
            self.motivoFin = "El jugador ha llegado a la sala final"

    def terminado(self):
        return self.fin, (
            self.motivoFin if self.motivoFin is not None else "No ha terminado"
        )

    def reporteSolicitudes(self):
        """Reporte de red de la cripta que se está jugando (§5.1): solicitudes realizadas, presupuesto,
        aciertos y fallos de caché. Solo lee contadores, así que consultarlo no cuesta ninguna solicitud.
        Devuelve None mientras todavía no se haya elegido una cripta."""
        if self.comunicacion is None or self.idCripta is None:
            return None
        return self.comunicacion.reporte(self.idCripta)
        
    def exportar_log(self) -> LogPartidaDTO:
        """Log de reproducción de la partida en datos simples; no toca archivos."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.logEventos.a_dto()

    def repetirPartida(self, log: LogPartidaDTO, hasta: int | None = None) -> list[ResultadoEventoDTO] | ResultadoReplayHastaDTO:
        self._es_repeticion = True
        try:
            return self._repetirPartidaInterno(log, hasta=hasta)
        finally:
            self._es_repeticion = False

    def _repetirPartidaInterno(self, log: LogPartidaDTO, hasta: int | None = None) -> list[ResultadoEventoDTO] | ResultadoReplayHastaDTO:
        log_original = LogEventos.desde_dto(log)

        if log_original.id_cripta is None:
            raise ValueError("El log no contiene el ID de la cripta")
        if self.iniciado:
            raise ValueError("No se puede repetir una partida durante otra partida")

        self.iniciarJuego(log_original.id_cripta, log_original.semilla, pedir_llaves=False)   # no es una partida nueva
        try:
            self._verificarVersionesReplay(log_original)
        except ValueError:
            self.iniciado = False
            raise
        self.ingresarEnSala(self.estadoJuego.jugador.id_sala_actual)

        if hasta is None:
            resultados = []
            for registro in log_original.obtener_registros_cronologicos():
                if registro.tipo_accion in TIPOS_CURSOR_INVENTARIO:
                    self._repetirMovimientoDeCursor(registro.tipo_accion)
                    continue
                evento = self._crear_evento_repeticion(registro)
                resultado = self.accionJugador(evento)
                if resultado.exito is False:     # el log solo guarda acciones aceptadas: si ahora se rechaza, ya no es fiel
                    raise ValueError(
                        f"La reproducción no es fiel: {evento.tipo_accion} fue rechazada ({resultado.mensaje})"
                    )
                resultados.append(resultado)
            return resultados

        # Caso con hasta is not None (FR-401 a FR-406)
        reloj = self.estadoJuego.reloj
        acciones_reproducidas = 0
        log_agotado = False

        for registro in log_original.obtener_registros_cronologicos():
            if self.fin or reloj.tiempo_actual >= hasta:
                break
            if registro.tipo_accion in TIPOS_CURSOR_INVENTARIO:
                self._repetirMovimientoDeCursor(registro.tipo_accion)
                continue
            evento = self._crear_evento_repeticion(registro)
            resultado = self.accionJugador(evento, tope=hasta)
            if resultado.exito is False:     # el log solo guarda acciones aceptadas: si ahora se rechaza, ya no es fiel
                raise ValueError(
                    f"La reproducción no es fiel: {evento.tipo_accion} fue rechazada ({resultado.mensaje})"
                )
            acciones_reproducidas += 1
            if self.fin:
                break
            sig = reloj.siguiente()
            if (sig is not None and sig.tiempo_ejecucion > hasta) or reloj.tiempo_actual >= hasta:
                break
        else:
            if not self.fin and reloj.tiempo_actual < hasta:
                log_agotado = True

        if not self.fin and reloj.tiempo_actual == hasta:
            self._completarInstante(hasta)

        return self._armarResultadoReplayHasta(hasta, acciones_reproducidas, log_agotado)

    def _armarResultadoReplayHasta(
        self, hasta: int, acciones_reproducidas: int, log_agotado: bool
    ) -> ResultadoReplayHastaDTO:
        reloj = self.estadoJuego.reloj
        # Reutiliza el empaquetado común de estado: evita duplicación (T005).
        resumen = self._extraerResumenEstadoActual(
            instante=reloj.tiempo_actual,
            acciones=self.acciones_linea_tiempo,
        )
        return ResultadoReplayHastaDTO(
            instante_pedido=hasta,
            instante_alcanzado=reloj.tiempo_actual,
            acciones_reproducidas=acciones_reproducidas,
            id_sala_jugador=resumen.id_sala_jugador,
            vida_jugador=resumen.vida_jugador,
            ataque_jugador=resumen.ataque_jugador,
            defensa_jugador=resumen.defensa_jugador,
            velocidad_jugador=resumen.velocidad_jugador,
            inventario_llaves=resumen.inventario_llaves,
            inventario_objetos=resumen.inventario_objetos,
            efectos_activos=resumen.efectos_activos,
            enemigos_sala=resumen.enemigos_sala,
            partida_terminada=self.fin,
            motivo_terminacion=self.motivoFin if self.fin else None,
            log_agotado=log_agotado,
        )

    def _verificarVersionesReplay(self, log: LogEventos) -> None:
        """Solo se reproduce si cripta y catálogo son exactamente los del log (§4.11)."""
        actuales = (
            ("cripta", log.version_cripta, self.logEventos.version_cripta),
            ("catálogo", log.version_catalogo, self.logEventos.version_catalogo),
        )
        for nombre, guardada, actual in actuales:
            if guardada is None or actual is None:
                raise ValueError(
                    f"No se puede garantizar una reproducción fiel: falta la versión de {nombre} "
                    f"(en el log: {guardada or 'desconocida'}, disponible: {actual or 'desconocida'})"
                )
            if guardada != actual:
                raise ValueError(
                    f"No se puede garantizar una reproducción fiel: la versión de {nombre} cambió "
                    f"({guardada} en el log, {actual} disponible)"
                )

    def _crear_evento_repeticion(self, registro: RegistroEvento) -> EventoDTO:
        tipo = registro.tipo_accion
        datos = registro.datos_extra
        actor_registro = registro.actor
        if not isinstance(tipo, str) or not isinstance(datos, list):
            raise ValueError("El registro del log no contiene un evento válido")
        costo = registro.tiempo_ejecucion   # en el log se guarda el costo (o retraso) original del evento
        if not isinstance(costo, int) or isinstance(costo, bool) or costo <= 0:
            raise ValueError("El registro del log no contiene un costo válido")

        jugador = self.estadoJuego.jugador
        if tipo == "MOVER_JUGADOR":
            sala, direccion = self._datos_sala_direccion(datos)
            return EventoDTO(costo, 0, jugador, tipo, [sala, direccion])

        if tipo == "ABRIR_PUERTA":
            sala, direccion = self._datos_sala_direccion(datos)
            return EventoDTO(costo, 0, jugador, tipo, [sala, direccion])

        if tipo == "ATACAR":
            enemigo = self._buscar_enemigo(self._id_referencia(datos, "enemigo"))
            return EventoDTO(costo, 0, jugador, tipo, [enemigo])

        if tipo in {"RECOGER_OBJETO", "USAR_OBJETO"}:
            objeto = self._buscar_objeto(
                self._id_referencia(datos, "objeto"),
                tipo == "USAR_OBJETO",
            )
            return EventoDTO(costo, 0, jugador, tipo, [objeto])

        if tipo == "SOLTAR_OBJETO":
            if not datos:       # los logs anteriores no guardaban el objeto: se suelta el del cursor
                return EventoDTO(costo, 0, jugador, tipo, [])
            objeto = self._buscar_objeto(self._id_referencia(datos, "objeto"), True)
            return EventoDTO(costo, 0, jugador, tipo, [objeto])

        if tipo == "ESPERAR":
            return EventoDTO(costo, 0, jugador, tipo, [])

        if tipo in {"ARMAR_TRAMPA", "ACTIVAR_TRAMPA"}:
            id_trampa = self._id_actor(actor_registro, "trampa")
            trampa = self._buscar_trampa(id_trampa)
            sala, = self._datos_sala(datos)
            return EventoDTO(costo, 0, trampa, tipo, [sala])

        if tipo == "CERRAR_PUERTA":
            id_sala = self._id_actor(actor_registro, "sala")
            sala = self.ingresarEnSala(id_sala)
            direccion, = datos
            return EventoDTO(costo, 0, sala, tipo, [direccion])

        raise ValueError(f"No se puede repetir el evento {tipo!r}")

    def _datos_sala_direccion(self, datos: list) -> tuple[SalaDTO, str]:
        if len(datos) != 2 or not isinstance(datos[1], str):
            raise ValueError("El evento requiere una sala y una dirección")
        sala, direccion = datos
        if not isinstance(sala, ReferenciaEvento) or sala.tipo != "sala":
            raise ValueError("El evento no contiene una referencia de sala válida")
        return self.ingresarEnSala(sala.id), direccion

    def _datos_sala(self, datos: list) -> tuple[SalaDTO]:
        if len(datos) != 1:
            raise ValueError("El evento requiere una sala")
        sala = datos[0]
        if not isinstance(sala, ReferenciaEvento) or sala.tipo != "sala":
            raise ValueError("El evento no contiene una referencia de sala válida")
        return (self.ingresarEnSala(sala.id),)

    @staticmethod
    def _id_referencia(datos: list, tipo: str) -> str | int:
        if len(datos) != 1 or not isinstance(datos[0], ReferenciaEvento):
            raise ValueError("El evento no contiene un objetivo válido")
        referencia = datos[0]
        if referencia.tipo != tipo or referencia.id is None:
            raise ValueError(f"El evento no contiene un objetivo de tipo {tipo}")
        return referencia.id

    @staticmethod
    def _id_actor(actor, tipo: str) -> str | int:
        if not isinstance(actor, ReferenciaEvento) or actor.tipo != tipo:
            raise ValueError(f"El evento no contiene un actor de tipo {tipo}")
        if actor.id is None:
            raise ValueError("El actor no contiene un identificador")
        return actor.id

    def _buscar_enemigo(self, id_enemigo: str | int):
        for sala in self.estadoJuego.salas:
            if sala is not None:
                for enemigo in sala.enemigos:
                    if enemigo.id_instancia == id_enemigo:
                        return enemigo
        raise ValueError(f"No se encontró el enemigo {id_enemigo!r}")

    def _buscar_objeto(self, id_objeto: str | int, en_inventario: bool):
        if en_inventario:
            actual = self.estadoJuego.jugador.inventario.actual
            if actual is not None and actual.objeto.id_catalogo == id_objeto:
                return actual.objeto        # con ids repetidos manda el cursor, que es lo que eligió el jugador
            nodo = self.estadoJuego.jugador.inventario.cabeza
            while nodo is not None:
                if nodo.objeto.id_catalogo == id_objeto:
                    return nodo.objeto
                nodo = nodo.siguiente

        # Recoger solo ocurre en la sala del jugador: se busca ahí primero para no tomar un objeto con el mismo id
        # de otra sala (la reproducción divergería).
        sala_actual = self.estadoJuego.salas[self.estadoJuego.jugador.id_sala_actual]
        if sala_actual is not None:
            for objeto in sala_actual.objetos:
                if objeto.id_catalogo == id_objeto:
                    return objeto
        for sala in self.estadoJuego.salas:
            if sala is not None:
                for objeto in sala.objetos:
                    if objeto.id_catalogo == id_objeto:
                        return objeto
        raise ValueError(f"No se encontró el objeto {id_objeto!r}")

    def _buscar_trampa(self, id_trampa: str | int):
        for sala in self.estadoJuego.salas:
            if sala is not None:
                for trampa in sala.trampas:
                    if trampa.id_instancia == id_trampa:
                        return trampa
        raise ValueError(f"No se encontró la trampa {id_trampa!r}")

    

    def listarCriptas(self) -> list[str]:
        self._exigirServicio()
        return self.comunicacion.listar_criptas()

    def obtenerIdCripta(self, posicion: int) -> str:
        self._exigirServicio()
        return self.comunicacion.obtener_id_cripta(posicion)
        
    #TODO Este va a recibir: el numero de cripta y partir de eso se comunica con comunicador para saber
    #1. Cuantas salas existen (solo reservar la memoria)
    #2. Crear el reloj virtual
    #3. Preguntar al comuniador por el jugador inicial (JugadorDTO)
    # Este lo asigna a self.estadoJuego
    # Devolver en que sala inicial el jugador
    # ejecuta ingresarEnSala(salainicial) y cargar algunas al rededor para el inicio

    def ingresarEnSala(self, sala: int)-> SalaDTO:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if(sala < 1 or sala >= len(self.estadoJuego.salas)):
            raise ValueError("No existe la sala que se desea consultar")
        if(self.estadoJuego.salas[sala] is None):
            self._cargarSala(sala)
        sala_cargada = self.estadoJuego.salas[sala]
        if sala == self.estadoJuego.jugador.id_sala_actual:
            if sala_cargada.ultimo_paso < 0 and self.accionesJugador == 0:
                sala_cargada.ultimo_paso = self.estadoJuego.reloj.tiempo_actual
            self._activarEnemigos(sala_cargada)
            self._actualizarFichasEnUso()
        return sala_cargada

    def fichasEnUso(self) -> list[str]:
        """Ids de catálogo referenciados por instancias activas (§4.4), uno por instancia: enemigos vivos y
        activos, los dormidos de la sala actual, el inventario y los objetos y trampas del suelo de la sala actual."""
        ids: list[str] = []
        jugador = self.estadoJuego.jugador
        sala_actual = None
        if 0 <= jugador.id_sala_actual < len(self.estadoJuego.salas):
            sala_actual = self.estadoJuego.salas[jugador.id_sala_actual]
        for enemigo in self.estadoJuego.catalogo_enemigos:
            if enemigo.vida_actual > 0 and (enemigo.activo or enemigo.id_sala_actual == jugador.id_sala_actual):
                ids.append(enemigo.tipo)
        nodo = jugador.inventario.cabeza
        while nodo is not None:
            ids.append(nodo.objeto.id_catalogo)
            nodo = nodo.siguiente
        if sala_actual is not None:
            for objeto in sala_actual.objetos:
                ids.append(objeto.id_catalogo)
            for trampa in sala_actual.trampas:
                ids.append(trampa.id_catalogo)
        return ids

    def _actualizarFichasEnUso(self) -> None:
        """Le dice a la fuente qué fichas no puede liberar. El modelo no conoce la caché.
        Inhibido solo en instancias aisladas de consulta histórica (T019/T020): el --replay real sí lo usa."""
        if getattr(self, "_es_aislada", False):
            return
        fijar = getattr(self.comunicacion, "fijar_fichas_en_uso", None)
        if fijar is not None:
            fijar(self.fichasEnUso())

    def _cargarSala(self, sala: int) -> None:
        """Incorpora el contenido de la sala al modelo. Cargar una sala NO activa a sus enemigos (§2.4)."""
        # El jugador acaba de entrar (o empieza aquí): se trae el contenido por adelantado y en lotes antes de armar la sala.
        # Una sola vez, al inicio, se precarga profundo (3); después el entorno cercano (profundidad 2),
        # y precargar_vecinas únicamente pide las salas que todavía no estaban guardadas. Si la sala la carga un enemigo
        # al desplazarse (no es la del jugador) no se precarga nada para no gastar presupuesto.
        # En instancias aisladas (consulta histórica) se inhibe la precarga para no alterar el reporte de red (T020).
        # El --replay real NO se inhibe: precarga en lotes como en la partida original.
        if sala == self.estadoJuego.jugador.id_sala_actual and not getattr(self, "_es_aislada", False):
            if getattr(self, "precargaInicialHecha", False):
                self.comunicacion.precargar_vecinas(self.idCripta, sala, 2)
            else:
                self.comunicacion.precargar_vecinas(self.idCripta, sala, 3)
                self.precargaInicialHecha = True
        self.estadoJuego.salas[sala] = self.comunicacion.construir_sala(self.idCripta,sala) 
        sala_cargada = self.estadoJuego.salas[sala]
        for enemigo in sala_cargada.enemigos:
            self.estadoJuego.catalogo_enemigos.append(enemigo)
        for objeto in sala_cargada.objetos:
            self.estadoJuego.catalogo_objetos.append(objeto)

    def _activarEnemigos(self, sala: SalaDTO) -> None:
        """Activa a los enemigos dormidos (y vivos) de `sala`, en orden ascendente de id de instancia, para que reciban
        números de secuencia deterministas (§2.4). Su primera acción se programa desde el reloj actual con costo 100.
        Un enemigo que ya está activo no se toca. Dentro de una acción del jugador, la activación se puede deshacer."""
        pendientes = [e for e in sala.enemigos if not e.activo and e.vida_actual > 0]
        while pendientes:
            menor = pendientes[0]
            for candidato in pendientes:
                if candidato.id_instancia < menor.id_instancia:
                    menor = candidato
            pendientes.remove(menor)
            menor.activo = True
            self.jugadorLogica.retroceso.registrar_cambio([CambioDTO(
                tipo_accion="ACTIVAR_ENEMIGO",
                objeto_afectado=menor,
                valor_anterior=False,
                valor_nuevo=True,
            )])
            self.cargarEvento(EventoDTO(100, 0, menor, "ACCION_ENEMIGO", [self.estadoJuego.jugador]))
            if menor.regeneracion > 0:      # §2.10: recupera vida cada PERIODO_REGENERACION mientras esté activo y vivo
                self.cargarEvento(EventoDTO(PERIODO_REGENERACION, 0, None, "REGENERAR", [menor]))

    #TODO va a revisar la seccion del vector de la memoria
    #si la sala está (no es None) la devuelve
    #si no, se comunica con el comunicador, recibe la sala y la inserta en el vector y la devuelve
    #inicial todos los enemigos de las salas

    def instantaneaMapaConocido(self):
        """El mapa conocido del jugador en formato de lectura (FR-216). No avanza el reloj ni abre ninguna acción (FR-218)."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.mapaConocido is None:
            raise ValueError("Esta cripta no entrega el esqueleto: no hay mapa conocido")
        return self.mapaConocido.instantanea()

    def vistaSalaActual(self):
        """La sala actual con sus salidas según lo que el jugador conoce (FR-219)."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.mapaConocido is None:
            raise ValueError("Esta cripta no entrega el esqueleto: no hay mapa conocido")
        return self.mapaConocido.sala_conocida(self.estadoJuego.jugador.id_sala_actual)

    def obtenerJugador(self):
        if self.estadoJuego is None:
            return None
        return self.estadoJuego.jugador 
        

    def tieneLlave(self,id_llave : str):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.jugadorLogica.tiene_llave(id_llave)

    def _procesarEventoReloj(self, evento) -> None:
        jugador = self.estadoJuego.jugador
        reloj = self.estadoJuego.reloj
        velocidad_antes = ActorLogica.velocidad_efectiva(jugador)
        accion = self.gestorEventos.procesar_evento(evento)
        # Si un efecto (el vencimiento de una poción) cambió la velocidad del jugador, su turno ya programado
        # conserva el progreso realizado (§2.3).
        velocidad_despues = ActorLogica.velocidad_efectiva(jugador)
        if velocidad_despues != velocidad_antes:
            reloj.reajustar_velocidad(jugador, velocidad_antes, velocidad_despues)
        if accion.mensaje:              # los eventos silenciosos (p. ej. regenerar con la vida llena) no ensucian la bitácora
            self._registrarEnBitacora(accion)
        self._comprobarFinal()
        if not self.fin and accion.eventoResultado is not None:
            self.cargarEvento(accion.eventoResultado)

    def _completarInstante(self, hasta: int) -> None:
        reloj = self.estadoJuego.reloj
        while not self.fin:
            siguiente = reloj.siguiente()
            if siguiente is None or siguiente.tiempo_ejecucion > hasta:
                break
            if siguiente.tipo_accion == "TURNO_JUGADOR":
                break
            evento = reloj.desencolar()
            self._procesarEventoReloj(evento)

    def _avanzarHastaProximoTurno(self, tope: int | None = None) -> None:
        """Ejecuta, en orden, los eventos que ocurren mientras el jugador espera su próximo turno (§2.3, §2.5).
        Termina sacando el evento TURNO_JUGADOR: el reloj queda en el instante en que el jugador vuelve a decidir.
        Si la partida termina por el camino (el jugador muere), se corta ahí: el reloj se queda en ese instante y el
        turno NO se saca, así el tiempo final es el de la muerte y los eventos posteriores no se ejecutan."""
        reloj = self.estadoJuego.reloj
        jugador = self.estadoJuego.jugador
        while not self.fin:
            siguiente = reloj.siguiente()
            if siguiente is None:
                break
            if tope is not None and siguiente.tiempo_ejecucion > tope:
                break
            if siguiente.tipo_accion == "TURNO_JUGADOR":
                reloj.desencolar()
                return
            evento = reloj.desencolar()
            self._procesarEventoReloj(evento)

    def _registrarEnBitacora(self, accion: ResultadoEventoDTO):
        descartado = self.logEventosJuego.agregar_evento(accion)
        self.jugadorLogica.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="BITACORA_AGREGADA",
            objeto_afectado=self.logEventosJuego,
            valor_anterior=descartado,
            elemento=accion,
        )])

    def ultimosMensajes(self) -> list[str]:
        """Los mensajes de la bitácora de la partida (máximo 20, §4.8), del más viejo al más reciente.
        Solo lee: no reproduce ni modifica nada."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return [r.mensaje for r in self.logEventosJuego.obtener_eventos() if r.mensaje]

    def _sumarPuntaje(self, puntaje: int):
        if not puntaje:
            return
        anterior = self.estadoJuego.puntaje
        self.estadoJuego.puntaje += puntaje
        self.jugadorLogica.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="ACTUALIZAR_PUNTAJE",
            objeto_afectado=self.estadoJuego,
            valor_anterior=anterior,
            valor_nuevo=self.estadoJuego.puntaje,
        )])

    @staticmethod
    def _obtener_id_afectado(evento: EventoDTO) -> str | int | None:
        """Obtiene el identificador del objeto que recibió la acción."""
        if evento.tipo_accion == "ATACAR" and evento.datos_extra:
            afectado = evento.datos_extra[0]
        elif evento.tipo_accion in {"RECOGER_OBJETO", "USAR_OBJETO"} and evento.datos_extra:
            afectado = evento.datos_extra[0]
        elif evento.tipo_accion == "MOVER_JUGADOR" and evento.datos_extra:
            afectado = evento.datos_extra[0]
        elif evento.tipo_accion == "ABRIR_PUERTA" and evento.datos_extra:
            afectado = evento.datos_extra[0]
        else:
            afectado = evento.actor

        for nombre in ("id_instancia", "id_catalogo", "id"):
            identificador = getattr(afectado, nombre, None)
            if identificador is not None:
                return identificador
        return None

        
    
    @staticmethod
    def _intervalo(evento: EventoDTO) -> int:
        """Tiempo que tarda el evento en ocurrir desde el reloj actual.
        Si el actor es el jugador o un enemigo, tiempo_ejecucion trae el COSTO de la acción y el intervalo
        sale de la velocidad del actor (§2.3). Los eventos del entorno (cierre de puerta, trampas,
        vencimiento de efectos) traen el retraso exacto y no dependen de ninguna velocidad."""
        if isinstance(evento.actor, (JugadorDTO, EnemigoDTO)):
            return RelojVirtual.intervalo_por_velocidad(
                evento.tiempo_ejecucion, ActorLogica.velocidad_efectiva(evento.actor)
            )
        return evento.tiempo_ejecucion

    def cargarEvento(self, evento : EventoDTO) -> int:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.estadoJuego.reloj.encolar(self._intervalo(evento),evento.actor,evento.tipo_accion,evento.datos_extra)

    def accionJugador(self, evento: EventoDTO, tope: int | None = None):
        """El jugador decide en el instante actual del reloj y su acción ocurre AHORA (§2.3). El costo (que viene en
        evento.tiempo_ejecucion) solo sirve para programar su próximo turno. Después se ejecuta todo lo que pasa antes
        de ese turno. Una acción rechazada no cambia nada ni consume tiempo (Apéndice B)."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.fin:
            raise ValueError("El juego ha finalizado, no se generan más acciones")
        self._asegurarPuntoControlInicial()
        costo = evento.tiempo_ejecucion
        if not isinstance(costo, int) or isinstance(costo, bool) or costo <= 0:
            raise ValueError("El costo de la acción del jugador debe ser un entero positivo")
        reloj = self.estadoJuego.reloj
        jugador = self.estadoJuego.jugador

        accion = self.gestorEventos.procesar_evento(evento)
        self._registrarEnBitacora(accion)
        if accion.exito is False:
            return accion                       # rechazada: sin tiempo, sin historial y fuera del log
        if GestorEventos.es_uso_de_pergamino(evento):
            self._registrarAccionEnLog(evento)  # el retroceso no consume tiempo, pero sí es parte de la partida
            self.acciones_linea_tiempo = max(0, self.acciones_linea_tiempo - 1)
            self._podarPuntosControlPosteriores(self.acciones_linea_tiempo)
            self.tiempoMovimientoJugador = reloj.tiempo_actual
            self._actualizarFichasEnUso()
            return accion

        respuesta = accion
        resultados_trampas = []
        # Entrar a una sala con trampas armadas las activa justo al terminar el movimiento, antes del siguiente evento
        if evento.tipo_accion == "MOVER_JUGADOR" and accion.exito:
            resultados_trampas = self.gestorEventos.activar_trampas(self.estadoJuego.salas[jugador.id_sala_actual])
            for resultado in resultados_trampas:
                self._registrarEnBitacora(resultado)
            if resultados_trampas:
                mensajes = "\n".join(r.mensaje for r in resultados_trampas)
                respuesta = ResultadoEventoDTO(accion.exito, f"{accion.mensaje}\n{mensajes}", accion.eventoResultado, accion.puntaje)

        self.accionesJugador += 1
        self.acciones_linea_tiempo += 1
        self._sumarPuntaje(accion.puntaje)
        self._comprobarFinal()
        if not self.fin:
            if accion.eventoResultado is not None:
                self.cargarEvento(accion.eventoResultado)
            for resultado in resultados_trampas:
                if resultado.eventoResultado is not None:
                    self.cargarEvento(resultado.eventoResultado)
            # El próximo turno usa la velocidad con que el jugador termina esta acción (p. ej. la que dio una poción)
            intervalo = RelojVirtual.intervalo_por_velocidad(costo, ActorLogica.velocidad_efectiva(jugador))
            reloj.programar(intervalo, jugador, "TURNO_JUGADOR", [])
            self._avanzarHastaProximoTurno(tope=tope)
        self.tiempoMovimientoJugador = reloj.tiempo_actual
        self._registrarAccionEnLog(evento)
        self._actualizarFichasEnUso()
        self._verificarYCapturarPuntoControl()
        return respuesta

    def vistaInventario(self, criterio: str | None = None) -> list:
        """Objetos del inventario en su orden real (criterio=None) o en una vista ordenada por "peso", "valor" o "nombre"
        (§4.5). Solo lee: no cambia el orden real, el cursor, el reloj ni el log."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        inventario = self.estadoJuego.jugador.inventario
        if criterio is None:
            return inventario.listar_objetos()
        return inventario.obtener_vista_ordenada(criterio)

    def siguienteObjetoInventario(self) -> bool:
        """Mueve el cursor del inventario al siguiente objeto. False si ya estaba en el último; ValueError si está vacío.
        No consume tiempo ni entra al retroceso, pero queda en el log: usar y soltar actúan sobre el objeto del cursor."""
        return self._moverCursorInventario(siguiente=True)

    def anteriorObjetoInventario(self) -> bool:
        """Mueve el cursor del inventario al objeto anterior. False si ya estaba en el primero; ValueError si está vacío."""
        return self._moverCursorInventario(siguiente=False)

    def _moverCursorInventario(self, siguiente: bool) -> bool:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.fin:
            raise ValueError("El juego ha finalizado, no se generan más acciones")
        inventario = self.estadoJuego.jugador.inventario
        movido = inventario.siguiente_objeto() if siguiente else inventario.anterior_objeto()
        if movido:      # si el cursor no se movió el estado no cambió: no hay nada que repetir
            self.logEventos.registrar_cursor("SIGUIENTE_OBJETO" if siguiente else "ANTERIOR_OBJETO")
            if self.registrador_log is not None:
                self.registrador_log.agregar(self.logEventos.cola.accion)
        return movido

    def _repetirMovimientoDeCursor(self, tipo_accion: str) -> None:
        movido = self.siguienteObjetoInventario() if tipo_accion == "SIGUIENTE_OBJETO" else self.anteriorObjetoInventario()
        if not movido:
            raise ValueError(f"El log pide {tipo_accion} pero el cursor no se pudo mover: la reproducción no es fiel")

    def _registrarAccionEnLog(self, evento: EventoDTO) -> None:
        self.logEventos.registrar_evento(evento)
        if self.registrador_log is not None:
            self.registrador_log.agregar(self.logEventos.cola.accion)

    def obtenerPuntaje(self) -> int:
        return self.estadoJuego.puntaje

    def finPartida(self) -> FinPartidaDTO:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")

        if not self.fin:
            raise ValueError(
                "No se puede tener el resultado final de una partida si no ha terminado"
            )

        return FinPartidaDTO(
            self.idCripta,
            self.comunicacion.version_cripta(self.idCripta) if self.comunicacion is not None else None,
            self.accionesJugador,
            self.jugadorLogica.enemigos_eliminados(),
            self.estadoJuego.reloj.tiempo_actual,
            not self.jugadorLogica.esta_muerto(),
        )