from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ResultadoReplayHastaDTO:
    """Resultado exhaustivo de reproducir una partida grabada hasta un instante virtual dado."""
    instante_pedido: int
    instante_alcanzado: int
    acciones_reproducidas: int
    id_sala_jugador: int
    vida_jugador: int
    ataque_jugador: int
    defensa_jugador: int
    velocidad_jugador: int
    inventario_llaves: list[str] = field(default_factory=list)
    inventario_objetos: list[str] = field(default_factory=list)
    efectos_activos: list[str] = field(default_factory=list)
    enemigos_sala: list[tuple[str, str, int]] = field(default_factory=list)
    partida_terminada: bool = False
    motivo_terminacion: str | None = None
    log_agotado: bool = False
