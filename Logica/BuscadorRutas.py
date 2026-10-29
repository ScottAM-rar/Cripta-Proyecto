"""Búsqueda de rutas de menor costo hacia un destino, sobre una vista del mapa (FR-111, FR-114).

Calcula, desde el destino y por las aristas ENTRANTES, el costo mínimo de cada sala hasta él, sin pasar de un límite; y
elige el siguiente paso de una sala: entre las salidas transitables v con costo(u,v) + costo(v) = costo(u), la de menor
id de destino. Es la búsqueda que usa el campo de costos del cazador, generalizada para aceptar cualquier vista.

Vista: objeto con `tamano` (cota de ids; la posición 0 no se usa), `salidas(sala)`, `entrantes(sala)` y
`transitable(arista)`; cada arista tiene `origen`, `destino` y `costo`. Una vista puede ser el mapa real (estado actual
de las puertas) o, para otras capacidades, el mapa que el jugador conoce.

Sin `dict` ni `set` (principio I): el costo y la marca de cada sala están en listas indexadas por id; reiniciar entre
búsquedas es subir una época (O(1)), así que el trabajo es proporcional a la región explorada y no al tamaño del mapa.
"""
from __future__ import annotations

from Logica.MonticuloMinimo import MonticuloMinimo


class VistaMapaReal:
    """Vista del mapa completo con el estado ACTUAL de las puertas: el de la sala cargada, o el inicial si no lo está."""

    def __init__(self, mapa, salas: list) -> None:
        self.mapa = mapa
        self.salas = salas

    @property
    def tamano(self) -> int:
        return self.mapa.tamano

    def salidas(self, sala: int) -> list:
        return self.mapa.salidas(sala)

    def entrantes(self, sala: int) -> list:
        return self.mapa.entrantes(sala)

    def transitable(self, arista) -> bool:
        return self.mapa.esta_abierta(arista, self.salas)


class BuscadorRutas:
    def __init__(self) -> None:
        self._costo: list[int] = []
        self._marca: list[int] = []
        self._epoca = 0
        self._monticulo = MonticuloMinimo()
        self._vista = None
        self.salas_fijadas = 0          # acumulado, para --bench y las pruebas

    def distancias_hacia(self, destino: int, vista, limite: int) -> None:
        """Calcula el costo mínimo de cada sala hasta `destino` por salidas transitables, sin pasar de `limite`.
        Reemplaza lo calculado antes; se consulta con `costo` y `siguiente_paso`."""
        tamano = vista.tamano
        if len(self._costo) < tamano:
            falta = tamano - len(self._costo)
            self._costo.extend([0] * falta)
            self._marca.extend([0] * falta)
        self._vista = vista
        self._epoca += 1
        epoca = self._epoca
        monticulo = self._monticulo
        monticulo.vaciar()
        if not 0 <= destino < tamano or limite < 0:
            return
        costos, marcas = self._costo, self._marca
        costos[destino] = 0
        marcas[destino] = epoca
        monticulo.insertar(0, destino)
        while not monticulo.vacio():
            costo, sala = monticulo.extraer_minimo()
            if costo > costos[sala]:
                continue                            # entrada vieja: ya se encontró un costo menor
            self.salas_fijadas += 1
            for arista in vista.entrantes(sala):
                if not vista.transitable(arista):
                    continue
                nuevo = costo + arista.costo
                if nuevo > limite:
                    continue
                x = arista.origen
                if marcas[x] != epoca or nuevo < costos[x]:
                    costos[x] = nuevo
                    marcas[x] = epoca
                    monticulo.insertar(nuevo, x)

    def costo(self, sala: int) -> int | None:
        """Costo mínimo de `sala` hasta el destino, o None si no hay ruta de costo <= límite."""
        if 0 <= sala < len(self._marca) and self._marca[sala] == self._epoca and self._epoca > 0:
            return self._costo[sala]
        return None

    def alcanzo(self, sala: int) -> bool:
        """¿Quedó `sala` dentro de la zona calculada? (lo usa el campo para invalidar solo lo que corresponde)"""
        return 0 <= sala < len(self._marca) and self._marca[sala] == self._epoca and self._epoca > 0

    def siguiente_paso(self, origen: int):
        """Arista que sigue la ruta de menor costo desde `origen`, o None si no hay ruta o ya está en el destino.
        Entre varias de igual costo gana la de menor id de destino (FR-114)."""
        d = self.costo(origen)
        if d is None or d == 0:
            return None
        elegida = None
        for arista in self._vista.salidas(origen):
            if not self._vista.transitable(arista):
                continue
            restante = self.costo(arista.destino)
            if restante is None or arista.costo + restante != d:
                continue
            if elegida is None or arista.destino < elegida.destino:
                elegida = arista
        return elegida
