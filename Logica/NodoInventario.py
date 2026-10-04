from DTO.Objeto import Objeto
from __future__ import annotations

class NodoInventario:
    def __init__(self, dato: Objeto):
        self.objeto = dato
        self.anterior = NodoInventario | None = None
        self.siguiente = NodoInventario | None = None   