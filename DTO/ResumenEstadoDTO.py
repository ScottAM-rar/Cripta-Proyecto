"""Resumen del estado de la partida en un instante pasado (capacidad 004: comandos `historia <t>` e `historia #k`).

Es solo la forma de los datos que devolverá `consultarHistoria`; todavía no hay lógica que lo llene. Se publica antes
para que quien muestra el resultado (la vista, y el mapa conocido de la capacidad 002) pueda programar contra ella.
Los campos de jugador y mundo son los mismos que entrega `--replay --hasta` (ResultadoReplayHastaDTO, capacidad 008).

Contrato provisional: puede ganar campos al final con valor por defecto, pero los existentes no cambian de nombre.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ResumenEstadoDTO:
    """Estado de la partida justo en el instante pedido. Consultarlo no cambia la partida en curso."""
    instante: int                          # instante virtual al que corresponde el estado
    acciones_jugador: int                  # acciones del jugador ya ejecutadas en ese estado (línea de tiempo vigente)
    id_sala_jugador: int
    vida_jugador: int
    ataque_jugador: int
    defensa_jugador: int
    velocidad_jugador: int
    inventario_llaves: list[str] = field(default_factory=list)
    inventario_objetos: list[str] = field(default_factory=list)
    efectos_activos: list[str] = field(default_factory=list)
    enemigos_sala: list[tuple[str, str, int]] = field(default_factory=list)    # (id de instancia, nombre, vida)
    partida_terminada: bool = False
    motivo_terminacion: str | None = None
    # Mapa conocido en ese instante (capacidad 002, niebla de guerra). None mientras esa capacidad no exista o no
    # se haya integrado; quien la integre define su tipo (su contrato de estado guardado: exploradas, avistadas, puertas).
    mapa_conocido: object | None = None
