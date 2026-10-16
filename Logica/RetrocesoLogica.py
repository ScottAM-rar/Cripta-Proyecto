from contextlib import contextmanager
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
            if reloj is not None and self.reloj is None:
                self.reloj = reloj
            return
        
        self.cabeza = None
        self.cola = None
        self.actual = None
        self.reloj = reloj
        self.cantidad_actual = 0
        self.cantidad_acciones = 0
        self.tiempo_evento = 0
        self.suspensiones = 0
        self._inicializado = True 

    def iniciar_accion(self, tiempo_ejecucion: int | None = None, diferir_recorte: bool = False) -> NodoCambio:
        """Abre una acción del jugador en el historial. Con diferir_recorte=True no se descarta todavía la acción más
        antigua: quien llama debe invocar recortar_historial() cuando la acción sea aceptada (una rechazada se descarta
        con descartar_accion y no debe costarle su lugar a una acción anterior)."""
        if not diferir_recorte and self.cantidad_acciones >= self.MAX_HISTORIAL:
            self._eliminar_accion_mas_antigua()
        if tiempo_ejecucion is None:
            tiempo_ejecucion = self.reloj.tiempo_actual if self.reloj else 0
        self.tiempo_evento = tiempo_ejecucion
        marcador = CambioDTO(
            tipo_accion="INICIO_ACCION",
            objeto_afectado=self.reloj,
            valor_anterior=self.reloj.tiempo_actual if self.reloj else tiempo_ejecucion,
            cantidad=self.reloj.secuencia_actual if self.reloj else 0,
            tiempo_ejecucion=tiempo_ejecucion,
        )
        nodo = NodoCambio([marcador], True)
        self.agregar_al_final(nodo)
        self.cantidad_actual += 1
        self.cantidad_acciones += 1
        return nodo

    def recortar_historial(self) -> None:
        """Deja el historial en MAX_HISTORIAL acciones como máximo, descartando las más antiguas."""
        while self.cantidad_acciones > self.MAX_HISTORIAL:
            self._eliminar_accion_mas_antigua()

    def fijar_tiempo_evento(self, tiempo_ejecucion: int):
        self.tiempo_evento = tiempo_ejecucion

    def descartar_accion(self, marcador: NodoCambio):
        nodo = self.cola
        while nodo is not None and nodo is not marcador:
            nodo = nodo.anterior
        if nodo is None:
            return []
        cambios = []
        while True:
            ultimo = self.cola
            cambios.append(self.pop())
            if ultimo is marcador:
                break
        self.cantidad_acciones -= 1
        return cambios

    @contextmanager
    def sin_registro(self):
        self.suspensiones += 1
        try:
            yield
        finally:
            self.suspensiones -= 1
        
    def registrar_cambio(self, cambio: list[CambioDTO], tiempo_ejecucion: int | None = None):
        if len(cambio) < 1:
            raise ValueError("Un cambio debe contener al menos un cambio.")
        
        if self.cantidad_acciones == 0:
            return 
        
        tiempo = self.tiempo_evento if tiempo_ejecucion is None else tiempo_ejecucion
        for c in cambio:
            c.tiempo_ejecucion = tiempo
        
        nuevo = NodoCambio(cambio, False)
        self.agregar_al_final(nuevo)
        self.cantidad_actual += 1

    def registrar_encolado(self, evento):
        self._registrar_agenda("EVENTO_ENCOLADO", evento)

    def registrar_desencolado(self, evento):
        self._registrar_agenda("EVENTO_DESENCOLADO", evento)

    def _registrar_agenda(self, tipo_accion: str, evento):
        if self.suspensiones > 0 or self.cantidad_acciones == 0 or self.reloj is None:
            return
        self.registrar_cambio(
            [CambioDTO(tipo_accion=tipo_accion, objeto_afectado=self.reloj, elemento=evento)],
            self.reloj.tiempo_actual,
        )
        
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
        self.reloj = None
        self.cantidad_actual = 0
        self.cantidad_acciones = 0
        self.tiempo_evento = 0
        self.suspensiones = 0
