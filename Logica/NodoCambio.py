from __future__ import annotations
from DTO.CambioDTO import CambioDTO

class NodoCambio:
    def __init__(self, cambios: list[CambioDTO], es_accion: bool = False):
        if len(cambios) > 2 or len(cambios) <= 0:
            raise ValueError("Un NodoCambio debe contener al menos un cambio y como maximo dos cambios.") 
        #Todos almacenan un cambio, pero en el caso de objetos como la 
        #pocion, se puede tener un cambio de vida y un cambio de inventario, por eso se permite hasta dos cambios.
        self.objeto = cambios 
        self.es_accion = es_accion
        self.anterior: NodoCambio | None = None
        self.siguiente: NodoCambio | None = None   