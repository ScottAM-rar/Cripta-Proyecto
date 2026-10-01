from dataclasses import dataclass
from DTO.EventoDTO import EventoDTO
@dataclass
class ResultadoEventoDTO:
    exito: bool = None
    mensaje: str = None
    eventoResultado: EventoDTO | None = None