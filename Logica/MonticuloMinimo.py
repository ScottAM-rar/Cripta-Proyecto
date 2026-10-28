"""Montículo binario mínimo sobre una lista, con clave (costo, id de sala).

Hecho a mano (principio I). No es el del reloj virtual: aquel está unido a EventoDTO y a su posición en la agenda
(ver specs/001-terreno-y-cazador/research.md §3). Este admite entradas repetidas: una búsqueda de menor costo
inserta de nuevo una sala cuando encuentra un costo menor y descarta la entrada vieja al sacarla.
"""
from __future__ import annotations


class MonticuloMinimo:
    def __init__(self) -> None:
        self._items: list[tuple[int, int]] = []

    def __len__(self) -> int:
        return len(self._items)

    def vacio(self) -> bool:
        return len(self._items) == 0

    def vaciar(self) -> None:
        self._items.clear()

    def minimo(self) -> tuple[int, int]:
        if not self._items:
            raise IndexError("El montículo está vacío")
        return self._items[0]

    def insertar(self, costo: int, sala: int) -> None:
        self._items.append((costo, sala))
        self._subir(len(self._items) - 1)

    def extraer_minimo(self) -> tuple[int, int]:
        if not self._items:
            raise IndexError("El montículo está vacío")
        raiz = self._items[0]
        ultimo = self._items.pop()
        if self._items:
            self._items[0] = ultimo
            self._bajar(0)
        return raiz

    def _subir(self, i: int) -> None:
        items = self._items
        elemento = items[i]
        while i > 0:
            padre = (i - 1) // 2
            if elemento < items[padre]:
                items[i] = items[padre]
                i = padre
            else:
                break
        items[i] = elemento

    def _bajar(self, i: int) -> None:
        items = self._items
        n = len(items)
        elemento = items[i]
        while True:
            izq = 2 * i + 1
            if izq >= n:
                break
            menor = izq
            der = izq + 1
            if der < n and items[der] < items[izq]:
                menor = der
            if items[menor] < elemento:
                items[i] = items[menor]
                i = menor
            else:
                break
        items[i] = elemento
