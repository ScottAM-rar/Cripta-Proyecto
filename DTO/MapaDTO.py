from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class AristaMapaDTO:
    """Una salida del esqueleto: de una sala a otra, con su costo ya resuelto (>= 1) y el estado inicial de su puerta."""
    direccion: str          # "norte", "sur", "este", "oeste"
    destino: int
    costo: int
    cerrada_inicial: bool = False


@dataclass
class SalaMapaDTO:
    id: int
    salidas: list[AristaMapaDTO] = field(default_factory=list)   # en el orden N, S, E, O


@dataclass
class MapaDTO:
    """Esqueleto completo de la cripta, sin contenido de salas. `salas[i]` es la sala de id i (None si no existe ese id)."""
    salas: list = field(default_factory=list)                    # list[SalaMapaDTO | None]
    advertencias: list[str] = field(default_factory=list)       # datos inválidos que se corrigieron al leer
