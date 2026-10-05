from dataclasses import dataclass, field

@dataclass
class DeltaDTO:
    """Cambios genericos para el pergamino"""
    tipo_accion: str
    datos: dict = field(default_factory=dict)