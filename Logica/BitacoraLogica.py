from DTO.ResultadoEventoDTO import ResultadoEventoDTO


class NodoBitacora:
    def __init__(self, resultado: ResultadoEventoDTO):
        self.resultado = resultado
        self.siguiente = None


class BitacoraLogica:
    def __init__(self):
        self.capacidad = 20
        self.frente = None
        self.final = None
        self.contador = 0

    def agregar_evento(self, resultado: ResultadoEventoDTO):
        if not isinstance(resultado, ResultadoEventoDTO):
            raise TypeError("La bitacora solo almacena ResultadoEventoDTO")

        nuevo = NodoBitacora(resultado)
        if self.frente is None:
            self.frente = nuevo
            self.final = nuevo
        else:
            self.final.siguiente = nuevo
            self.final = nuevo

        self.contador += 1
        if self.contador > self.capacidad:
            self.frente = self.frente.siguiente
            self.contador -= 1

        if self.frente is None:
            self.final = None

    def obtener_eventos(self):
        resultados = []
        actual = self.frente
        while actual is not None:
            resultados.append(actual.resultado)
            actual = actual.siguiente
        return resultados

    def imprimir_mensajes(self):
        actual = self.frente
        while actual is not None:
            print(actual.resultado.mensaje)
            actual = actual.siguiente