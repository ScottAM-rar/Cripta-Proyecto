from DTO.EventoDTO import EventoDTO

class RelojVirtual:
    def __init__(self):
        self.tiempo_actual: int = 0
        self.heap: list[EventoDTO] = []
        self.secuencia_actual: int = 0
        self.retroceso = None

    def _es_menor(self, a: EventoDTO, b: EventoDTO) -> bool:
        """Determina cuál evento debe ejecutarse primero."""
        if a.tiempo_ejecucion != b.tiempo_ejecucion:
            return a.tiempo_ejecucion < b.tiempo_ejecucion
        return a.id_secuencia < b.id_secuencia

    def encolar(self, intervalo: int, actor: object , tipo_accion: str, datos_extra: list | None = None) -> int:
        """Calcula el tiempo futuro y coloca el evento en la posición correcta del Heap. Devuelve el tiempo calculado"""
        self.secuencia_actual += 1
        tiempo_futuro = self.tiempo_actual + intervalo
        
        nuevo_evento = EventoDTO(
            tiempo_ejecucion=tiempo_futuro,
            id_secuencia=self.secuencia_actual,
            actor=actor,
            tipo_accion=tipo_accion,
            datos_extra=datos_extra if datos_extra is not None else []
        )
        
        self.heap.append(nuevo_evento)
        self._subir(len(self.heap) - 1)
        if self.retroceso is not None:
            self.retroceso.registrar_encolado(nuevo_evento)
        return tiempo_futuro

    def insertar_evento(self, evento: EventoDTO) -> None:
        self.heap.append(evento)
        self._subir(len(self.heap) - 1)

    def quitar_evento(self, evento: EventoDTO) -> bool:
        posicion = None
        for i in range(len(self.heap)):
            if self.heap[i] is evento:
                posicion = i
                break
        if posicion is None:
            return False
        ultimo = self.heap.pop()
        if posicion < len(self.heap):
            self.heap[posicion] = ultimo
            self._subir(posicion)
            self._bajar(posicion)
        return True

    def _subir(self, i: int):
        padre = (i - 1) // 2
        while i > 0 and self._es_menor(self.heap[i], self.heap[padre]):
            self.heap[i], self.heap[padre] = self.heap[padre], self.heap[i]
            i = padre
            padre = (i - 1) // 2

    def desencolar(self) -> EventoDTO | None:
        """Extrae el evento prioritario y avanza el reloj virtual."""
        if len(self.heap) == 0:
            return None

        # El menor evento siempre es la raíz (índice 0)
        evento_siguiente = self.heap[0]
        ultimo = self.heap.pop()

        if len(self.heap) > 0:
            self.heap[0] = ultimo
            self._bajar(0)

        # Avanzar el tiempo virtual del sistema directamente
        self.tiempo_actual = evento_siguiente.tiempo_ejecucion
        if self.retroceso is not None:
            self.retroceso.registrar_desencolado(evento_siguiente)
        return evento_siguiente

    def _bajar(self, i: int):
        n = len(self.heap)
        while True:
            menor = i
            izq = 2 * i + 1
            der = 2 * i + 2

            if izq < n and self._es_menor(self.heap[izq], self.heap[menor]):
                menor = izq
            if der < n and self._es_menor(self.heap[der], self.heap[menor]):
                menor = der

            if menor != i:
                self.heap[i], self.heap[menor] = self.heap[menor], self.heap[i]
                i = menor
            else:
                break