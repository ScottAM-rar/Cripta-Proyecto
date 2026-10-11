from Logica.NodoInventario import NodoInventario
from Controlador.ordenamiento import ordenar_adaptativo
from DTO.Objeto import Objeto

CRITERIOS_VALIDOS = ("peso", "valor", "nombre")

class InventarioLogica:
    def __init__(self, capacidad_maxima: int):
        self.cabeza = None
        self.cola = None
        self.actual = None
        self.cantidad_actual = 0
        self.capacidad_maxima = capacidad_maxima
    
    def agregar_objeto(self, objeto: Objeto):
        """Agrega un objeto en la lista"""
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
        
    def eliminar_objeto_utilizado(self, objeto: Objeto): 
        """Busca un objeto en la lista para eliminarlo al usarlo"""
        if self.cabeza is None:
            raise ValueError("El inventario esta vacio") #No se puede eliminar un objeto que no existe
        
        nodo_actual = self.cabeza
        while nodo_actual is not None: # Mientras el nodo actual no sea None busca el objeto indicado
            if nodo_actual.objeto == objeto: #Si lo encontro pasa a conectar-desconectar nodos
                self._desenlazar_nodos(nodo_actual)
                self.actual = self.cabeza  # Se reincia el puntero actual al primer objeto del inventario.
                return
            nodo_actual = nodo_actual.siguiente #Si no lo encontro en este, pasa al siguiente
        raise ValueError("El objeto no se encuentra en el inventario")
    
    def siguiente_objeto(self):
        """Cambia el objeto actual al siguiente"""
        if self.actual is None:
            raise ValueError("El inventario esta vacio")
        if self.actual.siguiente is None:
            return False  # No hay siguiente objeto
        self.actual = self.actual.siguiente
        return True  # Se movió al siguiente objeto
    
    def anterior_objeto(self):
        """Cambia el objeto actual al anterior"""
        if self.actual is None:
            raise ValueError("El inventario esta vacio")
        if self.actual.anterior is None:
            return False  # No hay objeto anterior
        self.actual = self.actual.anterior
        return True  # Se movió al objeto anterior
    
    def _desenlazar_nodos(self, nodo: NodoInventario):
        """Saca el nodo de la lista arreglando los enlaces de sus vecinos, este metodo es privado"""
        if nodo.anterior is not None: #Si el nodo no es el primero en la lista
            nodo.anterior.siguiente = nodo.siguiente
        else: # Si el nodo sí es el primero en la lista
            self.cabeza = nodo.siguiente
        if nodo.siguiente is not None: #Si el nodo no es el ultimo de la lista
            nodo.siguiente.anterior = nodo.anterior
        else: # Si el nodo sí es el ultimo en la lista
            self.cola = nodo.anterior
            
        nodo.anterior = None
        nodo.siguiente = None
        self.cantidad_actual -= 1 #Resta 1 a la cantidad actual en el inventario
    
    def soltar_objeto_actual(self):
        """Elimina el objeto actual del inventario"""
        if self.actual is None:
            raise ValueError("El inventario esta vacio")
        
        objeto = self.actual.objeto
        self._desenlazar_nodos(self.actual)
        self.actual = self.cabeza  # Reinicia el puntero actual al primer objeto del inventario.
        return objeto  # Devuelve el objeto que fue eliminado
    
    def equipar_objeto_actual(self):
        """Mueve el objeto actual al principio de la lista, indicando que esta equipado"""
        if self.actual is None:
            raise ValueError("El inventario esta vacio")
        
        nodo_actual = self.actual
        if nodo_actual is self.cabeza:
            return nodo_actual.objeto  # Ya está equipado, no hacer nada
    
        self._desenlazar_nodos(nodo_actual)
        nodo_actual.siguiente = self.cabeza
        self.cabeza.anterior = nodo_actual
        self.cabeza = nodo_actual
        self.cantidad_actual += 1  # Incrementa la cantidad actual ya que el nodo se ha vuelto a enlazar
        return nodo_actual.objeto  # Devuelve el objeto que fue equipado
    
    def obtener_vista_ordenada(self, criterio: str):
        """Devuelve una lista de objetos ordenados segun el criterio dado"""
        if criterio not in CRITERIOS_VALIDOS:
            raise ValueError(f"Criterio invalido. Los criterios son: {CRITERIOS_VALIDOS}")
        
        objetos = [] #Se crea una lista vacia para poder almacenar los objetos de forma que el metodo de ordenamiento no conozca la lista enlazada, solo ordene.
        nodo_actual = self.cabeza
        while nodo_actual is not None:
            objetos.append(nodo_actual.objeto)
            nodo_actual = nodo_actual.siguiente
        return ordenar_adaptativo(objetos, key=lambda obj: getattr(obj, criterio))  # Ordena la lista de objetos segun el criterio dado