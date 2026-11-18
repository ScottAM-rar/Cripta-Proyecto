"""Lo que el jugador ve de su conocimiento de la cripta (capacidad 002, FR-216 a FR-219).

Instantáneas de solo lectura. No guardan referencias al mapa completo ni a las salas del modelo: lo que no está aquí no se
puede mostrar. Una sala avistada solo existe como `destino_explorado = False`; no hay campo donde quepan su id, su nombre
ni su contenido, y dos salidas hacia la misma sala avistada son indistinguibles.
"""
from __future__ import annotations
from dataclasses import dataclass, field

PUERTA_ABIERTA = "abierta"
PUERTA_CERRADA = "cerrada"
PUERTA_SIN_OBSERVAR = "sin observar"


@dataclass
class SalidaConocidaDTO:
    direccion: str
    costo: int
    puerta: str = PUERTA_SIN_OBSERVAR          # "abierta", "cerrada" o "sin observar"
    destino_explorado: bool = False
    destino_id: int | None = None              # solo si destino_explorado
    destino_nombre: str = ""                   # solo si destino_explorado


@dataclass
class SalaConocidaDTO:
    id: int
    nombre: str
    salidas: list = field(default_factory=list)   # list[SalidaConocidaDTO], en el orden en que la sala las declara


@dataclass
class MapaConocidoDTO:
    sala_actual: int
    salas: list = field(default_factory=list)     # list[SalaConocidaDTO], exploradas, ascendentes por id
