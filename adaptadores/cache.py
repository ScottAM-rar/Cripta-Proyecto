from __future__ import annotations
from collections import deque

class CacheLRU:

    def __init__(self, capacidad: int = 25) -> None:
        self._capacidad = capacidad
        self._entradas: deque[list] = deque()

    def _buscar(self, clave: str) -> list | None:
        for entrada in self._entradas:
            if entrada[0] == clave:
                return entrada
        return None

    def obtener(self, clave: str) -> object | None:
        entrada = self._buscar(clave)
        if entrada is None:
            return None
        self._entradas.remove(entrada)
        self._entradas.appendleft(entrada)
        return entrada[1]

    def insertar(self, clave: str, valor: object) -> None:
        existente = self._buscar(clave)
        if existente is not None:
            existente[1] = valor
            self._entradas.remove(existente)
            self._entradas.appendleft(existente)
            return

        if len(self._entradas) >= self._capacidad:
            self._desalojar()

        self._entradas.appendleft([clave, valor, 0])

    def marcar_en_uso(self, clave: str) -> None:
        entrada = self._buscar(clave)
        if entrada is not None:
            entrada[2] += 1

    def marcar_libre(self, clave: str) -> None:
        entrada = self._buscar(clave)
        if entrada is not None:
            entrada[2] -= 1

    def _desalojar(self) -> str | None:
        for entrada in reversed(self._entradas):
            if entrada[2] == 0:
                self._entradas.remove(entrada)
                return entrada[0]
        return None

    