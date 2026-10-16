"""Convierte la partida en vivo a un EstadoGuardadoDTO (datos simples) y de vuelta.

Aquí no hay archivos ni red: solo el modelo. Las referencias compartidas (un enemigo está en una sala y también
en la agenda de eventos) se conservan guardando cada enemigo/trampa una vez en una tabla y nombrándolo por su
posición; al restaurar, todas las referencias vuelven a apuntar al mismo objeto.
"""
from __future__ import annotations

import dataclasses
from collections import deque

from DTO.ActorDTO import JugadorDTO, EnemigoDTO
from DTO.EstadoGuardadoDTO import (
    VERSION_ESTADO, EstadoGuardadoDTO, ObjetoGuardadoDTO, EnemigoGuardadoDTO, TrampaGuardadaDTO,
    SalidaGuardadaDTO, SalaGuardadaDTO, ReferenciaGuardadaDTO, EventoGuardadoDTO, RelojGuardadoDTO,
    JugadorGuardadoDTO, MensajeGuardadoDTO,
)
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.EventoDTO import EventoDTO
from DTO.Objeto import Objeto, Arma, Armadura, Pocion, Antidoto, Llave, Antorcha, PergaminoRetroceso
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.TrampaDTO import Trampa
from Logica.BitacoraLogica import BitacoraLogica
from Logica.GestorEventos import GestorEventos
from Logica.JugadorLogica import JugadorLogica
from Logica.LogEventos import LogEventos
from Logica.RelojVirtual import RelojVirtual
from Logica.RetrocesoLogica import RetrocesoLogica

_CLASES_OBJETO = (Objeto, Arma, Armadura, Pocion, Antidoto, Llave, Antorcha, PergaminoRetroceso)


def _posicion(tabla: list, elemento: object) -> int:
    """Posición de `elemento` en `tabla` comparando por identidad (-1 si no está)."""
    for i in range(len(tabla)):
        if tabla[i] is elemento:
            return i
    return -1


def _version_cripta(servicio, id_cripta: str):
    """Versión de la cripta tal como la trae el servicio en sus datos generales (sin pedir nada nuevo a la red)."""
    leer = getattr(servicio, "datos_cripta", None)
    if leer is None:
        return None
    datos = leer(id_cripta)
    return datos.get("version") if hasattr(datos, "get") else None


# ----------------------------------------------------------------------------- objetos

def _guardar_objeto(objeto) -> ObjetoGuardadoDTO:
    if isinstance(objeto, str):
        return ObjetoGuardadoDTO("id", [objeto])
    if type(objeto) not in _CLASES_OBJETO:
        raise ValueError(f"No se puede guardar un objeto de tipo {type(objeto).__name__}")
    return ObjetoGuardadoDTO(
        type(objeto).__name__,
        [getattr(objeto, campo.name) for campo in dataclasses.fields(objeto)],
    )


def _leer_objeto(guardado: ObjetoGuardadoDTO):
    if guardado.clase == "id":
        return guardado.valores[0]
    for clase in _CLASES_OBJETO:
        if clase.__name__ == guardado.clase:
            return clase(*guardado.valores)
    raise ValueError(f"Clase de objeto desconocida en la partida guardada: {guardado.clase!r}")


# ----------------------------------------------------------------------------- exportar

class _Tablas:
    """Enemigos y trampas únicos, en el orden en que aparecen; la posición es su nombre en el archivo."""

    def __init__(self):
        self.enemigos: list = []
        self.trampas: list = []

    def enemigo(self, enemigo) -> int:
        posicion = _posicion(self.enemigos, enemigo)
        if posicion < 0:
            self.enemigos.append(enemigo)
            posicion = len(self.enemigos) - 1
        return posicion

    def trampa(self, trampa) -> int:
        posicion = _posicion(self.trampas, trampa)
        if posicion < 0:
            self.trampas.append(trampa)
            posicion = len(self.trampas) - 1
        return posicion


def _referencia(valor, jugador, tablas: _Tablas) -> ReferenciaGuardadaDTO:
    if valor is jugador:
        return ReferenciaGuardadaDTO("jugador")
    if isinstance(valor, SalaDTO):
        return ReferenciaGuardadaDTO("sala", valor.id)
    if isinstance(valor, EnemigoDTO):
        return ReferenciaGuardadaDTO("enemigo", tablas.enemigo(valor))
    if isinstance(valor, Trampa):
        return ReferenciaGuardadaDTO("trampa", tablas.trampa(valor))
    if isinstance(valor, (str, int, float)):
        return ReferenciaGuardadaDTO("dato", valor)
    raise ValueError(f"No se puede guardar un evento que apunta a un {type(valor).__name__}")


def exportar(logica) -> EstadoGuardadoDTO:
    if not logica.iniciado:
        raise ValueError("El juego no ha sido iniciado")
    estado = logica.estadoJuego
    jugador = estado.jugador
    tablas = _Tablas()

    salas = []
    for numero in range(len(estado.salas)):
        sala = estado.salas[numero]
        if sala is None:
            continue
        if sala.id != numero:
            raise ValueError(f"La sala {sala.id} está en la posición {numero} de la lista de salas")
        salas.append(SalaGuardadaDTO(
            id=sala.id,
            nombre=sala.nombre,
            ultimo_paso=sala.ultimo_paso,
            salidas=[
                SalidaGuardadaDTO(s.direccion, s.sala_destino, s.cerrada, s.llave, s.cierre_automatico)
                for s in sala.salidas
            ],
            enemigos=[tablas.enemigo(e) for e in sala.enemigos],
            objetos=[_guardar_objeto(o) for o in sala.objetos],
            trampas=[tablas.trampa(t) for t in sala.trampas],
        ))

    eventos = []
    for e in estado.reloj.heap:
        eventos.append(EventoGuardadoDTO(
            tiempo_ejecucion=e.tiempo_ejecucion,
            id_secuencia=e.id_secuencia,
            tipo_accion=e.tipo_accion,
            actor=None if e.actor is None else _referencia(e.actor, jugador, tablas),
            datos_extra=[_referencia(d, jugador, tablas) for d in e.datos_extra],
        ))
    reloj = RelojGuardadoDTO(estado.reloj.tiempo_actual, estado.reloj.secuencia_actual, eventos)

    inventario = []
    cursor = -1
    nodo = jugador.inventario.cabeza
    while nodo is not None:
        if nodo is jugador.inventario.actual:
            cursor = len(inventario)
        inventario.append(_guardar_objeto(nodo.objeto))
        nodo = nodo.siguiente
    jugador_guardado = JugadorGuardadoDTO(
        vida_actual=jugador.vida_actual, vida_max=jugador.vida_max, ataque=jugador.ataque,
        defensa=jugador.defensa, velocidad=jugador.velocidad, id_sala_actual=jugador.id_sala_actual,
        veneno=jugador.veneno, modificador_velocidad=jugador.modificador_velocidad,
        antorcha_encendida=jugador.antorcha_encendida, antorcha_hasta=jugador.antorcha_hasta,
        enemigos_eliminados=jugador.enemigos_eliminados,
        inventario_max=jugador.inventario.capacidad_maxima,
        inventario=inventario, cursor=cursor,
        arma=None if jugador.arma is None else _guardar_objeto(jugador.arma),
        armadura=None if jugador.armadura is None else _guardar_objeto(jugador.armadura),
    )

    catalogo_enemigos = [tablas.enemigo(e) for e in estado.catalogo_enemigos]
    catalogo_objetos = [_guardar_objeto(o) for o in estado.catalogo_objetos]

    bitacora = [
        MensajeGuardadoDTO(r.exito, r.mensaje, r.puntaje)
        for r in logica.logEventosJuego.obtener_eventos()
    ]
    acciones = []
    nodo_log = logica.logEventos.cabeza
    while nodo_log is not None:
        acciones.append(nodo_log.accion)
        nodo_log = nodo_log.siguiente

    azar = logica.gestorEventos.azar.getstate()
    enemigos = [
        EnemigoGuardadoDTO(
            e.id_instancia, e.tipo, e.nombre, e.comportamiento, e.vida_actual, e.vida_max, e.ataque,
            e.defensa, e.velocidad, e.id_sala_actual, list(e.suelta),
        )
        for e in tablas.enemigos
    ]
    trampas = [
        TrampaGuardadaDTO(t.id_instancia, t.id_catalogo, t.id_sala, t.daño, t.rearme, t.armada)
        for t in tablas.trampas
    ]

    return EstadoGuardadoDTO(
        id_cripta=logica.idCripta,
        version_cripta=_version_cripta(logica.comunicacion, logica.idCripta),
        version_catalogo=getattr(logica.logEventos, "version_catalogo", None),
        version_estado=VERSION_ESTADO,
        semilla=logica.semilla,
        estado_azar=[azar[0], list(azar[1]), azar[2]],
        puntaje=estado.puntaje,
        fin=logica.fin,
        motivo_fin=logica.motivoFin,
        offline=False,      # de dónde salen los datos lo sabe quien arma el servicio; él completa este campo
        precarga_inicial_hecha=getattr(logica, "precargaInicialHecha", False),
        tiempo_movimiento_jugador=logica.tiempoMovimientoJugador,
        total_salas=len(estado.salas),
        salas=salas,
        enemigos=enemigos,
        trampas=trampas,
        catalogo_enemigos=catalogo_enemigos,
        catalogo_objetos=catalogo_objetos,
        jugador=jugador_guardado,
        reloj=reloj,
        bitacora=bitacora,
        acciones_log=acciones,
    )


# ----------------------------------------------------------------------------- restaurar

def _resolver(ref: ReferenciaGuardadaDTO, jugador, salas, enemigos, trampas):
    if ref.tipo == "jugador":
        return jugador
    if ref.tipo == "sala":
        if not isinstance(ref.valor, int) or not 0 <= ref.valor < len(salas) or salas[ref.valor] is None:
            raise ValueError(f"Un evento guardado apunta a la sala {ref.valor!r}, que no está en la partida")
        return salas[ref.valor]
    if ref.tipo == "enemigo":
        return enemigos[ref.valor]
    if ref.tipo == "trampa":
        return trampas[ref.valor]
    if ref.tipo == "dato":
        return ref.valor
    raise ValueError(f"Referencia desconocida en la partida guardada: {ref.tipo!r}")


def restaurar(logica, estado: EstadoGuardadoDTO) -> None:
    """Deja `logica` exactamente como estaba al exportar `estado`. Se arma todo primero y recién al final se
    reemplaza el estado de `logica`, así un archivo inválido no la deja a medias."""
    if not isinstance(estado, EstadoGuardadoDTO):
        raise TypeError("Se esperaba un EstadoGuardadoDTO")
    if estado.version_estado != VERSION_ESTADO:
        raise ValueError(
            f"Versión del estado guardado no soportada: {estado.version_estado!r} (se esperaba {VERSION_ESTADO})"
        )
    if logica.comunicacion is None:
        raise ValueError("No hay un servicio de cripta para restaurar la partida")
    if not logica.comunicacion.existe_cripta(estado.id_cripta):
        raise ValueError(f"La cripta {estado.id_cripta!r} de la partida guardada ya no existe")
    actual = _version_cripta(logica.comunicacion, estado.id_cripta)
    if estado.version_cripta is not None and actual is not None and actual != estado.version_cripta:
        raise ValueError(
            f"La cripta cambió de versión ({estado.version_cripta} -> {actual}); "
            "no se puede garantizar que la partida guardada siga siendo válida"
        )

    enemigos = [
        EnemigoDTO(
            vida_actual=g.vida_actual, vida_max=g.vida_max, ataque=g.ataque, defensa=g.defensa,
            velocidad=g.velocidad, id_sala_actual=g.id_sala_actual, id_instancia=g.id_instancia, tipo=g.tipo,
            nombre=g.nombre, comportamiento=g.comportamiento, suelta=list(g.suelta),
        )
        for g in estado.enemigos
    ]
    trampas = [
        Trampa(g.id_instancia, g.id_catalogo, g.id_sala, g.daño, g.rearme, g.armada)
        for g in estado.trampas
    ]

    salas: list = [None] * estado.total_salas
    for g in estado.salas:
        if not 0 <= g.id < len(salas):
            raise ValueError(f"La sala guardada {g.id} no cabe en la cripta")
        sala = SalaDTO(id=g.id, nombre=g.nombre)
        sala.salidas = deque(
            [SalidaDTO(s.direccion, s.sala_destino, s.cerrada, s.llave, s.cierre_automatico) for s in g.salidas],
            maxlen=4,
        )
        sala.enemigos = [enemigos[i] for i in g.enemigos]
        sala.objetos = [_leer_objeto(o) for o in g.objetos]
        sala.trampas = [trampas[i] for i in g.trampas]
        sala.ultimo_paso = g.ultimo_paso
        salas[g.id] = sala

    gj = estado.jugador
    jugador = JugadorDTO(
        vida_actual=gj.vida_actual, vida_max=gj.vida_max, ataque=gj.ataque, defensa=gj.defensa,
        velocidad=gj.velocidad, inventario_max=gj.inventario_max, id_sala_actual=gj.id_sala_actual,
    )
    jugador.veneno = gj.veneno
    jugador.modificador_velocidad = gj.modificador_velocidad
    jugador.antorcha_encendida = gj.antorcha_encendida
    jugador.antorcha_hasta = gj.antorcha_hasta
    jugador.enemigos_eliminados = gj.enemigos_eliminados
    jugador.arma = None if gj.arma is None else _leer_objeto(gj.arma)
    jugador.armadura = None if gj.armadura is None else _leer_objeto(gj.armadura)
    for guardado in gj.inventario:
        jugador.inventario.agregar_objeto(_leer_objeto(guardado))
    nodo = jugador.inventario.cabeza
    for _ in range(max(0, gj.cursor)):
        nodo = nodo.siguiente
    jugador.inventario.actual = nodo

    reloj = RelojVirtual()
    reloj.tiempo_actual = estado.reloj.tiempo_actual
    reloj.secuencia_actual = estado.reloj.secuencia_actual
    for g in estado.reloj.eventos:
        actor = None if g.actor is None else _resolver(g.actor, jugador, salas, enemigos, trampas)
        datos = [_resolver(d, jugador, salas, enemigos, trampas) for d in g.datos_extra]
        reloj.insertar_evento(EventoDTO(g.tiempo_ejecucion, g.id_secuencia, actor, g.tipo_accion, datos))

    retroceso = RetrocesoLogica()
    retroceso.reiniciar()          # el historial del pergamino no se guarda: empieza vacío
    retroceso.reloj = reloj
    reloj.retroceso = retroceso

    estado_juego = EstadoJuego(
        reloj, jugador,
        [enemigos[i] for i in estado.catalogo_enemigos],
        [_leer_objeto(o) for o in estado.catalogo_objetos],
        salas,
    )
    estado_juego.puntaje = estado.puntaje

    gestor = GestorEventos(salas, jugador, logica.ingresarEnSala, estado.semilla)
    gestor.azar.setstate((estado.estado_azar[0], tuple(estado.estado_azar[1]), estado.estado_azar[2]))

    bitacora = BitacoraLogica()
    for m in estado.bitacora:
        bitacora.agregar_evento(ResultadoEventoDTO(m.exito, m.mensaje, None, m.puntaje))
    log = LogEventos(estado.semilla, estado.id_cripta)
    log.version_cripta = estado.version_cripta
    log.version_catalogo = estado.version_catalogo
    for linea in estado.acciones_log:
        log.agregar(linea)

    # --- todo armado: ahora sí se reemplaza el estado de la lógica
    logica.idCripta = estado.id_cripta
    logica.semilla = estado.semilla
    logica.estadoJuego = estado_juego
    logica.gestorEventos = gestor
    logica.jugadorLogica = JugadorLogica(jugador, estado.semilla, gestor.azar)
    logica.logEventos = log
    logica.logEventosJuego = bitacora
    logica.fin = estado.fin
    logica.motivoFin = estado.motivo_fin
    logica.precargaInicialHecha = estado.precarga_inicial_hecha
    logica.tiempoMovimientoJugador = estado.tiempo_movimiento_jugador
    logica.iniciado = True
