from DTO.EventoDTO import EventoDTO

class RelojVirtual:
    def __init__(self):
        self.tiempo_actual: int = 0
        self.heap: list[EventoDTO] = []
        self.secuencia_actual: int = 0
        self.retroceso = None

    @staticmethod
    def intervalo_por_velocidad(costo: int, velocidad: int) -> int:
        """Tiempo hasta la próxima acción de un actor (§2.3): max(1, costo * 100 // velocidad)."""
        return max(1, costo * 100 // max(1, velocidad))

    @staticmethod
    def restante_por_cambio_de_velocidad(restante: int, velocidad_anterior: int, velocidad_nueva: int) -> int:
        """Tiempo que le queda a una acción ya programada cuando cambia la velocidad (§2.3).
        Conserva el progreso ya realizado: max(1, restante * velocidad_anterior // velocidad_nueva)."""
        return max(1, restante * velocidad_anterior // max(1, velocidad_nueva))

    def reprogramar(self, evento: EventoDTO, nuevo_tiempo: int) -> EventoDTO | None:
        """Cambia el instante de un evento ya programado. Se reemplaza por un evento nuevo con número de
        secuencia nuevo (§2.3) y ambos movimientos quedan en el historial para poder deshacerlos."""
        if not self.quitar_evento(evento):
            return None
        if self.retroceso is not None:
            self.retroceso.registrar_desencolado(evento)
        self.secuencia_actual += 1
        nuevo = EventoDTO(nuevo_tiempo, self.secuencia_actual, evento.actor, evento.tipo_accion, evento.datos_extra)
        self.insertar_evento(nuevo)
        if self.retroceso is not None:
            self.retroceso.registrar_encolado(nuevo)
        return nuevo

    def reajustar_velocidad(self, actor: object, velocidad_anterior: int, velocidad_nueva: int) -> None:
        """Un efecto cambió la velocidad de `actor`: sus acciones ya programadas conservan el progreso hecho (§2.3)."""
        pendientes = [e for e in self.heap if e.actor is actor]   # barrido lineal; solo ocurre al empezar o terminar un efecto
        for evento in pendientes:
            restante = max(0, evento.tiempo_ejecucion - self.tiempo_actual)
            nuevo_restante = self.restante_por_cambio_de_velocidad(restante, velocidad_anterior, velocidad_nueva)
            self.reprogramar(evento, self.tiempo_actual + nuevo_restante)

    def _es_menor(self, a: EventoDTO, b: EventoDTO) -> bool:
        """Determina cuál evento debe ejecutarse primero."""
        if a.tiempo_ejecucion != b.tiempo_ejecucion:
            return a.tiempo_ejecucion < b.tiempo_ejecucion
        return a.id_secuencia < b.id_secuencia

    def encolar(self, intervalo: int, actor: object , tipo_accion: str, datos_extra: list | None = None) -> int:
        """Calcula el tiempo futuro y coloca el evento en la posición correcta del Heap. Devuelve el tiempo calculado"""
        return self.programar(intervalo, actor, tipo_accion, datos_extra).tiempo_ejecucion

    def siguiente(self) -> EventoDTO | None:
        """El evento que se ejecutaría a continuación, sin sacarlo."""
        return self.heap[0] if self.heap else None

    def programar(self, intervalo: int, actor: object , tipo_accion: str, datos_extra: list | None = None) -> EventoDTO:
        """Igual que encolar, pero devuelve el evento creado."""
        self.secuencia_actual += 1
        tiempo_futuro = self.tiempo_actual + intervalo
        
        nuevo_evento = EventoDTO(
            tiempo_ejecucion=tiempo_futuro,
            id_secuencia=self.secuencia_actual,
            actor=actor,
            tipo_accion=tipo_accion,
            datos_extra=datos_extra if datos_extra is not None else []
        )
        
        self.insertar_evento(nuevo_evento)
        if self.retroceso is not None:
            self.retroceso.registrar_encolado(nuevo_evento)
        return nuevo_evento

    def insertar_evento(self, evento: EventoDTO) -> None:
        evento.posicion = len(self.heap)
        self.heap.append(evento)
        self._subir(len(self.heap) - 1)

    def quitar_evento(self, evento: EventoDTO) -> bool:
        """Saca un evento pendiente en O(log n): el evento recuerda su posición en el heap."""
        posicion = evento.posicion
        if posicion < 0 or posicion >= len(self.heap) or self.heap[posicion] is not evento:
            return False
        ultimo = self.heap.pop()
        evento.posicion = -1
        if posicion < len(self.heap):
            self.heap[posicion] = ultimo
            ultimo.posicion = posicion
            self._subir(posicion)
            self._bajar(ultimo.posicion)
        return True

    def _intercambiar(self, i: int, j: int) -> None:
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.heap[i].posicion = i
        self.heap[j].posicion = j

    def _subir(self, i: int):
        padre = (i - 1) // 2
        while i > 0 and self._es_menor(self.heap[i], self.heap[padre]):
            self._intercambiar(i, padre)
            i = padre
            padre = (i - 1) // 2

    def desencolar(self) -> EventoDTO | None:
        """Extrae el evento prioritario y avanza el reloj virtual."""
        if len(self.heap) == 0:
            return None

        # El menor evento siempre es la raíz (índice 0)
        evento_siguiente = self.heap[0]
        ultimo = self.heap.pop()

        evento_siguiente.posicion = -1
        if len(self.heap) > 0:
            self.heap[0] = ultimo
            ultimo.posicion = 0
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
                self._intercambiar(i, menor)
                i = menor
            else:
                break