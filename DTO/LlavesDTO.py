"""Ubicación de las llaves de una cripta (capacidad 009, FR-302).

Son listas paralelas: la posición i describe una ubicación (id de la llave, sala y enemigo que la suelta o None).
No hay dict ni set (principio I). El orden es el de la respuesta del servicio y se conserva tal cual (principio II)."""
from __future__ import annotations


class UbicacionLlavesDTO:
    """`salas[i]` es la sala donde está la llave si `enemigos[i]` es None; si no, la sala donde inicia ese enemigo.
    Una misma llave puede aparecer en varias posiciones (otra sala u otro enemigo). Una lista vacía es válida:
    la cripta no tiene llaves."""

    def __init__(self, cripta_id: str, version: str | None, ids: list[str], salas: list[int],
                 enemigos: list[str | None]):
        if not (len(ids) == len(salas) == len(enemigos)):
            raise ValueError(f"Las listas de llaves de la cripta {cripta_id} no tienen el mismo largo: "
                             f"ids={len(ids)}, salas={len(salas)}, enemigos={len(enemigos)}")
        self.cripta_id = cripta_id
        self.version = version
        self.ids = ids
        self.salas = salas
        self.enemigos = enemigos

    def cantidad(self) -> int:
        """Cantidad de ubicaciones. O(1)."""
        return len(self.ids)

    def ubicaciones_de(self, id_llave: str) -> list[int]:
        """Posiciones donde aparece `id_llave`, en el orden de la respuesta. O(k)."""
        posiciones: list[int] = []
        for i in range(len(self.ids)):
            if self.ids[i] == id_llave:
                posiciones.append(i)
        return posiciones

    def __repr__(self) -> str:
        return (f"UbicacionLlavesDTO(cripta_id={self.cripta_id!r}, version={self.version!r}, ids={self.ids!r}, "
                f"salas={self.salas!r}, enemigos={self.enemigos!r})")
