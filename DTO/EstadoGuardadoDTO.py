"""Instantánea de una partida: solo datos simples, sin objetos vivos del juego.

Es lo que el modelo entrega en exportar_estado() y recibe en restaurar_estado(). No sabe nada de archivos:
quien lo escriba a disco (binario, JSON...) es un adaptador. Los actores y trampas que comparten referencia
(salas y agenda de eventos apuntan a los mismos enemigos) se guardan UNA vez en una tabla global y el resto
los nombra por su posición en esa tabla, así al restaurar vuelven a ser el mismo objeto.
"""
from __future__ import annotations
from dataclasses import dataclass, field

VERSION_ESTADO = 1   # versión de la estructura de este DTO


@dataclass
class ObjetoGuardadoDTO:
    """Un objeto del juego. `clase` es el nombre de su clase ("Arma", "Pocion"...) y `valores` sus campos en el
    orden de la clase. Un id suelto (texto) en el suelo de una sala se guarda con clase "id"."""
    clase: str
    valores: list = field(default_factory=list)


@dataclass
class EnemigoGuardadoDTO:
    id_instancia: str
    tipo: str
    nombre: str
    comportamiento: str
    vida_actual: int
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    id_sala_actual: int
    suelta: list = field(default_factory=list)


@dataclass
class TrampaGuardadaDTO:
    id_instancia: str
    id_catalogo: str
    id_sala: int
    daño: int
    rearme: int
    armada: bool


@dataclass
class SalidaGuardadaDTO:
    direccion: str
    sala_destino: int
    cerrada: bool
    llave: str | None
    cierre_automatico: int | None


@dataclass
class SalaGuardadaDTO:
    id: int
    nombre: str
    ultimo_paso: int
    salidas: list = field(default_factory=list)     # list[SalidaGuardadaDTO], en el orden real
    enemigos: list = field(default_factory=list)    # posiciones en EstadoGuardadoDTO.enemigos
    objetos: list = field(default_factory=list)     # list[ObjetoGuardadoDTO]
    trampas: list = field(default_factory=list)     # posiciones en EstadoGuardadoDTO.trampas


@dataclass
class ReferenciaGuardadaDTO:
    """Apunta a algo del juego desde un evento.
    tipo: "jugador" | "sala" (valor = número) | "enemigo" (valor = posición en la tabla) |
          "trampa" (valor = posición en la tabla) | "dato" (valor = texto o número literal)"""
    tipo: str
    valor: object = None


@dataclass
class EventoGuardadoDTO:
    tiempo_ejecucion: int
    id_secuencia: int
    tipo_accion: str
    actor: ReferenciaGuardadaDTO | None
    datos_extra: list = field(default_factory=list)   # list[ReferenciaGuardadaDTO]


@dataclass
class RelojGuardadoDTO:
    tiempo_actual: int
    secuencia_actual: int
    eventos: list = field(default_factory=list)       # list[EventoGuardadoDTO]


@dataclass
class JugadorGuardadoDTO:
    vida_actual: int
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    id_sala_actual: int
    veneno: bool
    modificador_velocidad: int
    antorcha_encendida: bool
    antorcha_hasta: int
    enemigos_eliminados: int
    inventario_max: int
    inventario: list = field(default_factory=list)    # list[ObjetoGuardadoDTO], en el orden real
    cursor: int = -1                                  # posición del objeto actual del inventario (-1 = vacío)
    arma: ObjetoGuardadoDTO | None = None
    armadura: ObjetoGuardadoDTO | None = None


@dataclass
class MensajeGuardadoDTO:
    exito: bool | None
    mensaje: str | None
    puntaje: int = 0


@dataclass
class EstadoGuardadoDTO:
    # --- identificación ---
    id_cripta: str
    version_cripta: str | None
    version_catalogo: str | None          # lo completa quien conozca la versión del catálogo (el modelo no la consulta)
    version_estado: int = VERSION_ESTADO
    # --- azar y progreso ---
    semilla: int = 0
    estado_azar: list = field(default_factory=list)    # random.Random.getstate() aplanado: [versión, [ints...], gauss]
    puntaje: int = 0
    fin: bool = False
    motivo_fin: str | None = None
    offline: bool = False
    precarga_inicial_hecha: bool = False
    tiempo_movimiento_jugador: int = 0
    # --- mundo ---
    total_salas: int = 0                  # largo de la lista de salas del juego (las no cargadas no se guardan)
    salas: list = field(default_factory=list)          # list[SalaGuardadaDTO] solo de las salas cargadas
    enemigos: list = field(default_factory=list)       # tabla global list[EnemigoGuardadoDTO]
    trampas: list = field(default_factory=list)        # tabla global list[TrampaGuardadaDTO]
    catalogo_enemigos: list = field(default_factory=list)   # posiciones en `enemigos`
    catalogo_objetos: list = field(default_factory=list)    # list[ObjetoGuardadoDTO]
    jugador: JugadorGuardadoDTO | None = None
    reloj: RelojGuardadoDTO | None = None
    # --- historiales ---
    bitacora: list = field(default_factory=list)       # últimos mensajes list[MensajeGuardadoDTO]
    acciones_log: list = field(default_factory=list)   # líneas de la bitácora de reproducción (acciones del jugador)
