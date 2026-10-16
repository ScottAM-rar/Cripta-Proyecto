"""Contenido de un log de reproducción como datos simples. Quien lo guarda o lo lee de un archivo es un adaptador."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class LogPartidaDTO:
    id_cripta: str | None
    semilla: int
    version_cripta: str | None = None
    version_catalogo: str | None = None
    acciones: list = field(default_factory=list)    # una línea (texto JSON) por acción del jugador, en orden
