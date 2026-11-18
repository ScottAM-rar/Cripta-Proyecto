"""DTO que representa un punto de control inmutable de la partida.
FR-421, Principio I, Principio IV.
"""
from __future__ import annotations
from dataclasses import dataclass
from DTO.EstadoGuardadoDTO import EstadoGuardadoDTO


@dataclass(frozen=True)
class PuntoControlDTO:
    """Instantánea inmutable de un punto de control en la línea de tiempo."""
    numero_punto: int
    acciones_linea_tiempo: int
    instante_reloj: int
    estado: EstadoGuardadoDTO
    longitud_bitacora: int = 0
    longitud_acciones_log: int = 0
