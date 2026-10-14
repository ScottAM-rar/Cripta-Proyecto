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
            if nodo_actual.objeto is objeto: #Si lo encontro pasa a conectar-desconectar nodos
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
    
    def soltar_objeto_actual(self):
        """Elimina el objeto actual del inventario"""
        if self.actual is None:
            raise ValueError("El inventario esta vacio")
        
        objeto = self.actual.objeto
        self._desenlazar_nodos(self.actual)
        self.actual = self.cabeza  # Reinicia el puntero actual al primer objeto del inventario.
        return objeto  # Devuelve el objeto que fue eliminado
    
    def eliminar_objeto_por_retroceso(self, objeto: Objeto):
        if objeto is None:
            raise ValueError("El inventario esta vacio")
        nodo = self.buscar_objeto(objeto)
        if nodo is None:
            raise ValueError("El objeto no se encuentra en el inventario")
        self._desenlazar_nodos(nodo)

    def equipar_objeto_actual(self):
        """Mueve el objeto actual al principio de la lista, indicando que esta equipado"""
        if self.actual is None:
            raise ValueError("El inventario esta vacio")
        
        nodo_actual = self.actual
        if nodo_actual is self.cabeza:
            return nodo_actual.objeto  # Ya está equipado, no hacer nada

        self._desenlazar_nodos(nodo_actual)
        self._reenlazar_nodo(nodo_actual, None, self.cabeza)
        self.actual = nodo_actual
        return nodo_actual.objeto

    def equipar_objeto_por_retroceso(self, objeto: Objeto):
        """Mueve el objeto indicado al principio de la lista, indicando que esta equipado"""
        if self.cabeza is None:
            raise ValueError("El inventario esta vacio")
        
        nodo_a_mover = self.buscar_objeto(objeto)
        if nodo_a_mover is None:
            raise ValueError("No hay objeto para mover")
        
        if nodo_a_mover is self.cabeza:
            return  # Ya está equipado, no hacer nada
        
        self._desenlazar_nodos(nodo_a_mover)
        self._reenlazar_nodo(nodo_a_mover, None, self.cabeza)  # Mueve el nodo al principio de la lista

    def insertar_en_indice(self, indice: int, objeto: Objeto):
        """Mueve el objeto equipado (cabeza o cabeza.siguiente) al indice indicado"""
        if self.cabeza is None:
            raise ValueError("El inventario esta vacio")
        if indice < 0 or indice >= self.cantidad_actual:
            raise ValueError("Indice fuera de rango")
        
        nodo_a_mover = self.buscar_objeto(objeto)
        if nodo_a_mover is None:
            raise ValueError("No hay objeto para mover")

        nodo_equivalente = self.cabeza.siguiente if self.cabeza is not None else None
        if nodo_a_mover is not self.cabeza and nodo_a_mover is not nodo_equivalente:
            raise ValueError("El objeto no esta equipado")

        if self.cantidad_actual == 1:
            return

        # Se elimina primero para no mezclar la lista original con la nueva posición
        self._desenlazar_nodos(nodo_a_mover)

        # Se busca la posición destino sobre la lista ya modificada
        nodo_destino = self.cabeza
        for _ in range(indice):
            if nodo_destino is None:
                raise ValueError("Indice fuera de rango")
            nodo_destino = nodo_destino.siguiente

        if nodo_destino is None:
            self._reenlazar_nodo(nodo_a_mover, self.cola, None)
        else:
            self._reenlazar_nodo(nodo_a_mover, nodo_destino.anterior, nodo_destino)
        
    def insertar_en_indice_por_retroceso(self, indice: int, objeto: Objeto):
        """Restaura objetos eliminados en el inventario en la posición indicada"""
        if indice < 0 or indice > self.cantidad_actual:
            raise ValueError("Indice fuera de rango")

        nuevo_nodo = NodoInventario(objeto)

        if self.cabeza is None:
            self.cabeza = nuevo_nodo
            self.cola = nuevo_nodo
            self.actual = nuevo_nodo
            self.cantidad_actual += 1
        elif indice == 0:
            self._reenlazar_nodo(nuevo_nodo, None, self.cabeza)
            self.cabeza = nuevo_nodo
        elif indice == self.cantidad_actual:
            self._reenlazar_nodo(nuevo_nodo, self.cola, None)
            self.cola = nuevo_nodo
        else:
            nodo_destino = self.cabeza
            for _ in range(indice):
                nodo_destino = nodo_destino.siguiente
            self._reenlazar_nodo(
                nuevo_nodo,
                nodo_destino.anterior,
                nodo_destino
            )
        
    def indice_de_objeto(self, objeto: Objeto) -> int:
        """Devuelve el indice del objeto en la lista, o -1 si no se encuentra"""
        nodo_actual = self.cabeza
        indice = 0
        while nodo_actual is not None:
            if nodo_actual.objeto is objeto:
                return indice
            nodo_actual = nodo_actual.siguiente
            indice += 1
        return -1  # No se encontro el objeto en la lista

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
    
    def _desenlazar_nodos(self, nodo: NodoInventario):
        """Saca el nodo de la lista arreglando los enlaces de sus vecinos"""
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
        
    def buscar_objeto(self, objeto: Objeto) -> NodoInventario | None:
        """Busca un nodo en la lista que contenga el objeto dado"""
        nodo_actual = self.cabeza
        while nodo_actual is not None:
            if nodo_actual.objeto is objeto:
                return nodo_actual
            nodo_actual = nodo_actual.siguiente
        return None  # No se encontro el objeto en la lista
    
    def _reenlazar_nodo(self, nodo, anterior, siguiente) -> None:
        """Reenlaza un nodo en la lista"""
        nodo.anterior, nodo.siguiente = anterior, siguiente
        if anterior is not None:
            anterior.siguiente = nodo
        else:
            self.cabeza = nodo
        if siguiente is not None:
            siguiente.anterior = nodo
        else:
            self.cola = nodo
        if self.actual is None:
            self.actual = nodo  
        self.cantidad_actual += 1 
        
    def _mover_entre(self, nodo, anterior, siguiente) -> None:
        """Mueve un nodo entre dos nodos dados"""
        self._desenlazar_nodos(nodo)
        self._reenlazar_nodo(nodo, anterior, siguiente)