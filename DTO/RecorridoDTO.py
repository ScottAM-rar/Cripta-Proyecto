from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class RecorridoDTO:
    """Resultado de un recorrido por niveles: las salas visitadas, en orden, y el nivel de cada una.

    `salas`: ids de sala en el orden de visita; el primero es el origen; sin repetidos (FR-503).
    `niveles`: mismo largo que `salas`; `niveles[i]` es el nivel de `salas[i]`; no decrece, y dentro de un mismo nivel
    `salas` crece estrictamente (FR-501, FR-502)."""
    salas: list[int] = field(default_factory=list)
    niveles: list[int] = field(default_factory=list)
