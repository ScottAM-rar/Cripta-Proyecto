"""Recorrido por niveles de la cripta (capacidad 005).

Visita las salas alcanzables desde un origen en orden creciente de nivel (cantidad de salidas del camino más corto) y,
dentro de cada nivel, por menor id de sala. Cada sala una sola vez. Lee las aristas salientes de MapaCripta; no pide
nada a la red ni modifica nada.

Estructuras (principio I): una cola circular propia con el nivel en curso; dos listas indexadas por id de sala (marca
de época y nivel) para saber si una sala ya fue visitada sin `dict` ni `set`; y `ordenar_adaptativo` para ordenar cada
nivel, porque el orden en que se descubren las salas sigue al de sus padres y no al de sus ids. Reiniciar entre
recorridos es subir la época: O(1), así que el costo depende de lo visitado y no del tamaño de la cripta (FR-510).
"""
from __future__ import annotations

from DTO.RecorridoDTO import RecorridoDTO
from Logica.ColaCircular import ColaCircular
from Logica.MapaCripta import MapaCripta
from Logica.ordenamiento import ordenar_adaptativo


class RecorridoPorNiveles:
    def __init__(self, mapa: MapaCripta) -> None:
        self.mapa = mapa
        self._marca: list[int] = [0] * mapa.tamano       # época en que se visitó cada sala; 0 = nunca
        self._nivel: list[int] = [0] * mapa.tamano       # nivel de la sala; solo vale si _marca es la época actual
        self._epoca = 0
        self._cola = ColaCircular()                      # contiene el nivel en curso
        self.salas_visitadas = 0                         # del ÚLTIMO recorrido (para pruebas y --bench)
        self.salidas_examinadas = 0                      # del ÚLTIMO recorrido: salientes de las salas con nivel < límite

    def recorrer(self, origen, limite=None, transitable=None) -> RecorridoDTO:
        """Recorrido desde `origen`.

        `transitable`: función que recibe una arista y devuelve verdadero o falso; sin ella, todas las salidas lo son.
        `limite`: cantidad máxima de niveles, entero mayor o igual que 0, o None para recorrer todo lo alcanzable. Las
        salas con nivel mayor que el límite no se visitan y las salidas de las salas que están justo en el límite no se
        examinan, así que el costo es proporcional a lo visitado (FR-504, FR-510)."""
        mapa = self.mapa
        if isinstance(origen, bool) or not isinstance(origen, int) or not 0 <= origen < mapa.tamano or not mapa.existe[origen]:
            raise ValueError(f"El origen {origen!r} no existe en la cripta")
        if limite is not None and (isinstance(limite, bool) or not isinstance(limite, int) or limite < 0):
            raise ValueError(f"El límite de niveles debe ser un entero mayor o igual que 0, o ausente (se recibió {limite!r})")

        self._epoca += 1
        epoca = self._epoca
        marca, nivel, cola = self._marca, self._nivel, self._cola
        existe, salientes, tamano = mapa.existe, mapa.salientes, mapa.tamano
        salas: list[int] = []
        niveles: list[int] = []
        examinadas = 0
        self.salas_visitadas = 0
        self.salidas_examinadas = 0
        cola.vaciar()
        try:
            marca[origen] = epoca
            nivel[origen] = 0
            cola.agregar(origen)
            while not cola.vacia():
                siguiente: list[int] = []                # lo que se descubre del nivel que viene
                for _ in range(len(cola)):
                    sala = cola.sacar()
                    salas.append(sala)
                    niveles.append(nivel[sala])
                    if limite is not None and nivel[sala] >= limite:
                        continue                         # en el límite: no se examinan sus salidas (FR-504, FR-510)
                    for arista in salientes[sala]:
                        examinadas += 1
                        destino = arista.destino
                        if not 0 <= destino < tamano or not existe[destino]:
                            continue                     # sala que no existe: se ignora (FR-513)
                        if transitable is not None and not transitable(arista):
                            continue                     # salida no declarada transitable (FR-507)
                        if marca[destino] == epoca:
                            continue                     # ya visitada: en su nivel más cercano (FR-503)
                        marca[destino] = epoca
                        nivel[destino] = nivel[sala] + 1
                        siguiente.append(destino)
                for destino in ordenar_adaptativo(siguiente):     # menor id dentro del nivel (FR-502)
                    cola.agregar(destino)
        finally:
            cola.vaciar()                                # también si el criterio de transitabilidad lanza un error
            self.salas_visitadas = len(salas)
            self.salidas_examinadas = examinadas
        return RecorridoDTO(salas, niveles)
