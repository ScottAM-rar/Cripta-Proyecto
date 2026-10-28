"""Esqueleto de la cripta como aristas en listas contiguas, salientes y entrantes por sala.

Se construye una vez al iniciar la partida a partir de MapaDTO. Guarda costos y estado INICIAL de las puertas; el
estado actual de una puerta se lee de la sala del modelo cuando está cargada (única fuente de verdad) y, si no lo
está, vale el inicial: una puerta solo puede cambiar en una sala cargada, así que es equivalente a tenerlas todas.
Sin diccionarios ni ids fijos: todo se dimensiona con el mayor id del esqueleto (los ids son densos desde 1).
"""
from __future__ import annotations

from DTO.MapaDTO import MapaDTO


class AristaCripta:
    __slots__ = ("origen", "direccion", "destino", "costo", "cerrada_inicial")

    def __init__(self, origen: int, direccion: str, destino: int, costo: int, cerrada_inicial: bool) -> None:
        self.origen = origen
        self.direccion = direccion
        self.destino = destino
        self.costo = costo
        self.cerrada_inicial = cerrada_inicial


class MapaCripta:
    def __init__(self, mapa: MapaDTO) -> None:
        self.tamano = len(mapa.salas)                       # mayor id + 1; la posición 0 no se usa
        self.salientes: list[list[AristaCripta]] = [[] for _ in range(self.tamano)]
        self.entrantes: list[list[AristaCripta]] = [[] for _ in range(self.tamano)]
        self.existe: list[bool] = [False] * self.tamano     # existe[i]: el esqueleto tiene una sala con id i (FR-512, FR-513)
        for sala in mapa.salas:
            if sala is None:
                continue
            self.existe[sala.id] = True
            for a in sala.salidas:
                arista = AristaCripta(sala.id, a.direccion, a.destino, a.costo, a.cerrada_inicial)
                self.salientes[sala.id].append(arista)
                if 0 <= a.destino < self.tamano:
                    self.entrantes[a.destino].append(arista)

    def esta_abierta(self, arista: AristaCripta, salas: list) -> bool:
        """Estado de la puerta EN ESTE INSTANTE: el de la sala cargada, o el inicial si la sala no está cargada."""
        sala = salas[arista.origen] if arista.origen < len(salas) else None
        if sala is not None:
            for salida in sala.salidas:
                if salida.direccion == arista.direccion:
                    return not salida.cerrada
        return not arista.cerrada_inicial
