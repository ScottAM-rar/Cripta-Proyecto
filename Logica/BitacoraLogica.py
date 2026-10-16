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

        descartado = None
        self.contador += 1
        if self.contador > self.capacidad:
            descartado = self.frente.resultado
            self.frente = self.frente.siguiente
            self.contador -= 1

        if self.frente is None:
            self.final = None
        return descartado

    def quitar_resultado(self, resultado: ResultadoEventoDTO) -> bool:
        anterior = None
        actual = self.frente
        while actual is not None:
            if actual.resultado is resultado:
                if anterior is None:
                    self.frente = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                if actual is self.final:
                    self.final = anterior
                self.contador -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

    def poner_al_frente(self, resultado: ResultadoEventoDTO):
        nuevo = NodoBitacora(resultado)
        nuevo.siguiente = self.frente
        self.frente = nuevo
        if self.final is None:
            self.final = nuevo
        self.contador += 1

    def obtener_eventos(self):
        resultados = []
        actual = self.frente
        while actual is not None:
            resultados.append(actual.resultado)
            actual = actual.siguiente
        return resultados
