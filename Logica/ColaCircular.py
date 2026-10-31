"""Cola de enteros sobre una lista que gira (cola circular) y crece al llenarse.

Hecha a mano (principio I): sin `deque` ni nada de `collections`. Guarda el índice de la cabeza y la cantidad de
elementos; la posición de la cola se deduce con módulo. Al llenarse duplica la capacidad y copia los elementos en
orden desde la cabeza, así que agregar y sacar son O(1) amortizado y la memoria sigue a la frontera más ancha.
"""
from __future__ import annotations

CAPACIDAD_INICIAL = 16      # pequeña y sin relación con ninguna cripta


class ColaCircular:
    def __init__(self, capacidad: int = CAPACIDAD_INICIAL) -> None:
        if capacidad < 1:
            raise ValueError("La capacidad inicial debe ser al menos 1")
        self._almacen: list[int] = [0] * capacidad
        self._cabeza = 0
        self._tamano = 0

    @property
    def capacidad(self) -> int:
        return len(self._almacen)

    def __len__(self) -> int:
        return self._tamano

    def vacia(self) -> bool:
        return self._tamano == 0

    def vaciar(self) -> None:
        self._cabeza = 0
        self._tamano = 0

    def agregar(self, valor: int) -> None:
        if self._tamano == len(self._almacen):
            self._crecer()
        self._almacen[(self._cabeza + self._tamano) % len(self._almacen)] = valor
        self._tamano += 1

    def sacar(self) -> int:
        if self._tamano == 0:
            raise IndexError("La cola está vacía")
        valor = self._almacen[self._cabeza]
        self._cabeza = (self._cabeza + 1) % len(self._almacen)
        self._tamano -= 1
        return valor

    def _crecer(self) -> None:
        """Duplica la capacidad y deja los elementos en orden desde la posición 0."""
        capacidad = len(self._almacen)
        nuevo: list[int] = [0] * (2 * capacidad)
        for i in range(self._tamano):
            nuevo[i] = self._almacen[(self._cabeza + i) % capacidad]
        self._almacen = nuevo
        self._cabeza = 0
