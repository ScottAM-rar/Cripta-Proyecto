from collections import deque 
from DTO.DeltaDTO import DeltaDTO

class RetrocesoLogica:
    MAX_HISTORIAL = 10
    
    def __init__(self):
        self.historial: deque[DeltaDTO] =deque(maxlen=self.MAX_HISTORIAL)
        
    def registrar_accion(self, delta: DeltaDTO):
        self.historial.append(delta)
        
    def deshacer_accion(self) -> DeltaDTO | None:
        if self.historial:
            return self.historial.pop()
        return None