from collections import deque 
from DTO.DeltaDTO import DeltaDTO

class RetrocesoLogica:
    MAX_HISTORIAL = 5
    
    def __init__(self):
        self._entradas = [None] * self.MAX_HISTORIAL  # Lista circular para almacenar las entradas
        self._inicio = 0  
        self._cantidad = 0
        self._nueva_accion = False
        
    def nueva_accion(self) -> None:
        """Marca que se ha realizado una nueva accion, lo que permite registrar un nuevo delta."""
        self._nueva_accion = True
    
    def registrar_accion(self, delta: DeltaDTO):
        if self._nueva_accion:
            self._abrir_nueva_entrada()
            self._nueva_accion
        elif self._cantidad == 0:
            return
        self._entradas[self._ultima()].append(delta)
        
    def _abrir_nueva_entrada(self):
        if self._cantidad < self.MAX_HISTORIAL:
            posicion = (self._inicio + self._cantidad) % self.MAX_HISTORIAL
            self._cantidad += 1
        else:
            posicion = self._inicio
            self._inicio = (self._inicio + 1) % self.MAX_HISTORIAL
        self._entradas[posicion] = []
        
    def _ultima(self) -> int:
        return (self._inicio + self._cantidad - 1) % self.MAX_HISTORIAL    

    def hay_acciones_para_deshacer(self) -> bool:
        return self._cantidad > 0 
        
    def deshacer_accion(self) -> DeltaDTO | None:
        if self._cantidad == 0:
            return None
        posicion = self._ultima()
        entrada, self._entradas[posicion] = self._entradas[posicion], None
        self._cantidad -= 1
        return entrada