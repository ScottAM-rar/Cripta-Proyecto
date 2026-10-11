from collections import deque 
from DTO.DeltaDTO import DeltaDTO

class RetrocesoLogica:
    MAX_HISTORIAL = 10
    
    def __init__(self):
        self.historial: deque[DeltaDTO] =deque(maxlen=self.MAX_HISTORIAL)
        self._nueva_accion = False
        
    def nueva_accion(self) -> None:
        """Marca que se ha realizado una nueva acción, lo que permite registrar un nuevo delta."""
        self._nueva_accion = True
    
    def registrar_accion(self, delta: DeltaDTO):
        if self._nueva_accion or not self.historial:
            self.historial.append([])
            self._nueva_accion = False
        self.historial[-1].append(delta)
        
    def hay_acciones_para_deshacer(self) -> bool:
        return len(self.historial) > 0
        
    def deshacer_accion(self) -> DeltaDTO | None:
        return self.historial.pop() if self.historial else None