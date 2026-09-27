class NodoInventario:
    def __init__(self, dato): #dato es un ObjetoDTO
        self.objeto = dato
        self.anterior = None
        self.siguiente = None