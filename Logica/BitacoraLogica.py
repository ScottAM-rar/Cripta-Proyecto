class BitacoraLogica:
    def __init__(self):
        self.capacidad = 20
        self.datos = [None] * self.capacidad
        self.siguiente_posicion = 0
        self.contador = 0

    def agregar_evento(self, evento):
        self.datos[self.siguiente_posicion] = evento
        self.siguiente_posicion = (self.siguiente_posicion + 1) % self.capacidad
        if self.contador < self.capacidad:
            self.contador += 1
            
    def obtener_eventos(self):
        datos_ordenados = []
        for i in range(self.contador):
            tmp = (self.siguiente_posicion - self.contador + i) % self.capacidad
            datos_ordenados.append(self.datos[tmp])
        return datos_ordenados