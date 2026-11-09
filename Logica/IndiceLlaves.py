"""Índice de ids de llave a número denso (capacidad 003; research.md §4, data-model.md §4).

Los ids de llave son textos sin un orden denso, y sin `dict` ni `set` (principio I) no hay tabla directa de id a
posición. El índice guarda los ids distintos en una lista ordenada y resuelve `numero(id)` con una búsqueda binaria
escrita a mano. Como la lista está ordenada por id, comparar números es comparar ids: es el orden que usa la
verificación para el desempate dentro de una sala (FR-335).

Costos: construir O(K log K) (`ordenar_adaptativo` + quitar repetidos comparando vecinos); `numero` O(log K);
`id_de` y `cantidad` O(1). Sin `bisect`, `sorted()`, `.sort()`, `dict` ni `set`.
"""
from __future__ import annotations

from Logica.ordenamiento import ordenar_adaptativo


class IndiceLlaves:
    def __init__(self, ids: list[str]) -> None:
        ordenados = ordenar_adaptativo(ids)
        self._ids: list[str] = []
        for id_llave in ordenados:                  # los repetidos quedan juntos: basta compararlo con el último
            if not self._ids or self._ids[-1] != id_llave:
                self._ids.append(id_llave)

    def cantidad(self) -> int:
        """Cantidad de ids distintos."""
        return len(self._ids)

    def id_de(self, numero: int) -> str:
        """Id que corresponde al número (0 .. cantidad() - 1)."""
        return self._ids[numero]

    def numero(self, id_llave: str) -> int:
        """Posición de `id_llave` en el índice, o -1 si no está. Búsqueda binaria propia: O(log K)."""
        bajo = 0
        alto = len(self._ids) - 1
        while bajo <= alto:
            medio = (bajo + alto) // 2
            actual = self._ids[medio]
            if actual == id_llave:
                return medio
            if actual < id_llave:
                bajo = medio + 1
            else:
                alto = medio - 1
        return -1
