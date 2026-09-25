from __future__ import annotations
from dataclasses import dataclass, field
from  DTO.ActorDTO import EnemigoDTO


@dataclass
class SalidaDTO:
    """DTO para representar los datos crudos de una salida/conexión."""
    direccion: str                     # "N", "S", "E", "O"
    sala_destino: int                  # ID de la sala receptora
    cerrada: bool = False               # True si requiere llave para abrirse
    llave: str | None = None           # ID de la llave necesaria (ej: "itm_llave_bronce")[cite: 1]
    cierre_automatico: int | None = None # Tiempo virtual de re-cierre si aplica[cite: 1]


@dataclass
class TrampaDTO:
    """DTO para una instancia concreta de trampa en la sala."""
    id_instancia: str                  # Ej: "t-17"[cite: 1]
    tipo: str                          # Ej: "trp_dardos"[cite: 1]


@dataclass
class SalaDTO:
    """DTO principal que reúne los datos del Esqueleto y del Contenido de una sala."""
    id: int                            # ID único de la sala[cite: 1]
    nombre: str                        # Nombre devuelto por el API[cite: 1]
    salidas: list[SalidaDTO] = field(default_factory=list)
    enemigos: list[EnemigoDTO] = field(default_factory=list) # Reutiliza el DTO de enemigos
    objetos: list[str] = field(default_factory=list)          # IDs de catálogo en el suelo (ej: "itm_antorcha")[cite: 1]
    trampas: list[TrampaDTO] = field(default_factory=list)
    ultimo_paso: int | None = None     # Rastro del tiempo virtual de la última visita del jugador[cite: 1]