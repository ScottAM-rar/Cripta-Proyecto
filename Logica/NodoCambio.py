from __future__ import annotations
from DTO.CambioDTO import CambioDTO

class NodoCambio:
    def __init__(self, cambios: list[CambioDTO], es_accion: bool = False):
        if len(cambios) <= 0:
            raise ValueError("Un NodoCambio debe contener al menos un cambio.") 
        #Una accion puede afectar a varios actores y estados al mismo tiempo.
        self.objeto = cambios 
        self.es_accion = es_accion
        self.evento_automatico = None
        self.anterior: NodoCambio | None = None
        self.siguiente: NodoCambio | None = None   