from DTO.CambioDTO import CambioDTO
from Logica.NodoCambio import NodoCambio
from Logica.RelojVirtual import RelojVirtual

class RetrocesoLogica:
    MAX_HISTORIAL = 5
    _instancia = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    def __init__(self, reloj: RelojVirtual | None = None):
        if getattr(self, "_inicializado", False):
            return
        
        self.cabeza = None
        self.cola = None
        self.actual = None
        self.reloj = reloj
        self.cantidad_actual = 0
        self.cantidad_acciones = 0
        self._inicializado = True 
        self.accion_pendiente = False  # Indica si se ha iniciado una nueva accion
        

    def nueva_accion(self):
        self.accion_pendiente = True
        self.tiempo_inicio_accion = self.reloj.tiempo_actual() if self.reloj else None
        
    def registrar_cambio(self, cambio: list[CambioDTO]):
        if not 1 <= len(cambio) <= 2:
            raise ValueError("Un cambio debe contener al menos un cambio y como maximo dos cambios.")
        
        inicia_accion = self.accion_pendiente
        
        if inicia_accion:
            if self.cantidad_acciones >= self.MAX_HISTORIAL:
                self._eliminar_accion_mas_antigua()
            self.cantidad_acciones += 1
            self.accion_pendiente = False
            
        if self.cantidad_acciones == 0:
            return 
        
        for c in cambio:
            c.tiempo_ejecucion = self.reloj.tiempo_actual() if self.reloj else 0
        self.tiempo_inicio_accion = cambio[0].tiempo_ejecucion
            
        if self.cantidad_acciones == 0:
            return
        
        nuevo = NodoCambio(cambio, inicia_accion)
        self.agregar_al_final(nuevo)
        self.cantidad_actual += 1
        
    def agregar_al_final(self, nodo: NodoCambio):
        if self.cabeza is None:
            self.cabeza = nodo
            self.cola = nodo
            self.actual = nodo
        else:
            nodo.anterior = self.cola
            self.cola.siguiente = nodo
            self.cola = nodo
            

    def _eliminar_accion_mas_antigua(self):
        if self.cabeza is None:
            return
        
        nodo = self.cabeza
        while nodo is not None:
            siguiente = nodo.siguiente
            fin = siguiente is None or siguiente.es_accion
            self.cabeza = siguiente
            self.cantidad_actual -= 1
            if siguiente is not None:
                siguiente.anterior = None
            if fin:
                break
            nodo = siguiente
        if self.cabeza is None:
            self.cola = None
            self.actual = None
        self.cantidad_acciones -= 1
        
    def deshacer_accion(self):
        if self.cantidad_acciones == 0:
            return []
        
        cambios = []
        while self.cola is not None:
            nodo = self.cola
            cambios.append(nodo.objeto)
            
            self.cola = nodo.anterior
            
            if self.cola is not None:
                self.cola.siguiente = None
            else:
                self.cabeza = None
                
            self.cantidad_actual -= 1
            if nodo.es_accion:
                break
        self.actual = self.cola
        self.cantidad_acciones -= 1
        return cambios
        
    def obtener_cambios_retroceso(self):
        """Devuelve una lista de cambios que se pueden revertir, hasta el inicio de la ultima accion registrada."""
        if self.cantidad_acciones == 0:
            return []
        cambios = []
        while True:
            nodo = self.cola
            if nodo is None:
                break
            cambios.append(self.pop())
            if nodo.es_accion:   
                break
        self.actual = self.cola
        self.cantidad_acciones -= 1
        return cambios

    def pop(self):
        """Comportamiento de pila, elimina el ultimo agregado"""
        if self.cola is None:
            return None
        nodo = self.cola
        self.cola = nodo.anterior
        if self.cola is not None:
            self.cola.siguiente = None
        else:
            self.cabeza = None
        self.cantidad_actual -= 1
        self.actual = self.cola
        return nodo.objeto
        
    def hay_algo_para_deshacer(self) -> bool:
        """Verifica si hay acciones registradas en el historial de retroceso."""
        return self.cantidad_acciones > 0

    def reiniciar(self):
        self.cabeza = None
        self.cola = None
        self.actual = None
        self.cantidad_actual = 0
        self.cantidad_acciones = 0
        self.accion_pendiente = False