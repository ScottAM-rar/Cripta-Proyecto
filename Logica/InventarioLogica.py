from NodoInventario import NodoInventario

class InventarioLogica:
    def __init__(self, capacidad_maxima: int):
        self.cabeza = None
        self.cola = None
        self.actual = None
        self.cantidad_actual = 0
        self.capacidad_maxima = capacidad_maxima
    
    def agregar_objeto(self, objeto):
        if self.cantidad_actual >= self.capacidad_maxima:
            raise ValueError("No se puede agregar el objeto, el inventario está al máximo")
        
        nuevo_nodo = NodoInventario(objeto)
        if self.cabeza is None:  # Si el inventario esta vacio
            self.cabeza = nuevo_nodo
            self.cola = nuevo_nodo
            self.actual = nuevo_nodo
        else:
            nuevo_nodo.anterior = self.cola
            self.cola.siguiente = nuevo_nodo
            self.cola = nuevo_nodo
        
        self.cantidad_actual += 1
        
    def eliminar_objeto(self, objeto):
        if self.cabeza is None:
            raise ValueError("El inventario está vacío")
        
        nodo_actual = self.cabeza
        while nodo_actual is not None:
            if nodo_actual.objeto == objeto:
                if nodo_actual.anterior is not None:
                    nodo_actual.anterior.siguiente = nodo_actual.siguiente
                else:  # Si es la cabezilla
                    self.cabeza = nodo_actual.siguiente
                if nodo_actual.siguiente is not None:
                    nodo_actual.siguiente.anterior = nodo_actual.anterior
                else:  # Si es la colita
                    self.cola = nodo_actual.anterior
                self.cantidad_actual -= 1
                self.actual = self.cabeza  # Se reincia el puntero actual al primer objeto del inventario.
                return
            nodo_actual = nodo_actual.siguiente
        raise ValueError("El objeto no se encuentra en el inventario")
    
    def siguiente_objeto(self):
        if self.actual is None:
            raise ValueError("El inventario está vacío")
        if self.actual.siguiente is None:
            return False  # No hay siguiente objeto
        self.actual = self.actual.siguiente
        return True  # Se movió al siguiente objeto
    
    def anterior_objeto(self):
        if self.actual is None:
            raise ValueError("El inventario está vacío")
        if self.actual.anterior is None:
            return False  # No hay objeto anterior
        self.actual = self.actual.anterior
        return True  # Se movió al objeto anterior