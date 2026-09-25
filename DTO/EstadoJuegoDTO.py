from __future__ import annotations
from dataclasses import dataclass, field
from Logica.RelojVirtual import RelojVirtual
from DTO.ActorDTO import JugadorDTO, EnemigoDTO
from DTO.CatalogoDTO import EnemigoCatalogoDTO
from DTO.SalaDTO import SalaDTO


@dataclass
class EstadoJuego:
    """
    Contenedor global del estado de la partida.
    Almacena únicamente las listas maestras y referencias del mundo sin lógica.
    """
    reloj: RelojVirtual | None = None
    jugador: JugadorDTO | None = None
    
    # Catálogos globales (Fichas estáticas de la API)
    catalogo_enemigos: list[EnemigoCatalogoDTO] = field(default_factory=list)
    catalogo_objetos: list = field(default_factory=list)
    
    # Estado dinámico de la partida
    salas: list[SalaDTO] = field(default_factory=list)
    enemigos_vivos: list[EnemigoDTO] = field(default_factory=list)