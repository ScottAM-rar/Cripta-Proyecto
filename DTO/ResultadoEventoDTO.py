from dataclasses import dataclass
from DTO.EventoDTO import EventoDTO
@dataclass
class ResultadoEventoDTO:
    exito: bool = None
    mensaje: str = None
    eventoResultado: EventoDTO | None = None
    puntaje: int = 0
    costo: int | None = None   # costo de la acción realizada (p. ej. el de la salida cruzada); None = no aplica