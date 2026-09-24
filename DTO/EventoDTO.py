from dataclasses import dataclass, field

@dataclass
class EventoDTO:
    tiempo_ejecucion: int
    id_secuencia: int
    actor: object | None        # Instancia de JugadorDTO, EnemigoDTO o None si es del entorno
    tipo_accion: str           # "MOVER", "ATACAR", "CERRAR_PUERTA", etc.
    datos_extra: list = field(default_factory=list)