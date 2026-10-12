from __future__ import annotations
from DTO.CambioDTO import CambioDTO

class NodoCambio:
    def __init__(self, dato: list[CambioDTO], es_accion: bool = False):
        if len(dato) > 2 or len(dato) <= 0:
            raise ValueError("tu maire")
        self.objeto = dato
        self.es_accion = es_accion
        self.anterior: NodoCambio | None = None
        self.siguiente: NodoCambio | None = None   