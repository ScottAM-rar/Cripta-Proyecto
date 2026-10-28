"""Costo mínimo de cada sala hasta la sala actual del jugador, acotado por una cota (el rango del cazador).

Reutilización (principio III): lo calculado se conserva mientras siga siendo exactamente lo que daría calcular desde
cero en este instante. Se invalida por evento (tabla en specs/001-terreno-y-cazador/research.md §4):
  - el jugador cambia de sala (por movimiento, por deshacer o por restaurar): se detecta al consultar, porque cada
    consulta compara la sala actual del jugador con la del cálculo guardado;
  - una puerta cambia de estado: `puerta_cambio` invalida solo si la sala a la que lleva esa salida está dentro de la
    zona calculada (una salida x -> y solo se usa al procesar y, así que si y quedó fuera de la cota no puede cambiar nada);
  - se pide una cota mayor que la guardada: se recalcula con la mayor;
  - moverse, atacar o morir otros actores no cambia ninguna salida ni costo: no invalida.
Un campo nuevo (`CampoDeCostos(...)`) siempre calcula desde cero: es la referencia de las pruebas de equivalencia.

La búsqueda sale de la sala del jugador y recorre las aristas
ENTRANTES, usando solo las que están abiertas ahora; se detiene al pasar la cota, así que explora la región dentro de
la cota y no toda la cripta. El reinicio entre búsquedas es una marca de época: no se limpia ninguna lista.
"""
from __future__ import annotations

from Logica.MapaCripta import MapaCripta
from Logica.MonticuloMinimo import MonticuloMinimo


class CampoDeCostos:
    def __init__(self, mapa: MapaCripta, jugador, salas: list) -> None:
        self.mapa = mapa
        self.jugador = jugador          # se lee su sala EN CADA búsqueda: no hay copia que se pueda quedar vieja
        self.salas = salas
        self._costo: list[int] = [0] * mapa.tamano
        self._marca: list[int] = [0] * mapa.tamano
        self._epoca = 0
        self._monticulo = MonticuloMinimo()
        self._valido = False            # ¿lo guardado sigue siendo lo que daría calcular desde cero ahora?
        self._origen = -1               # sala del jugador con la que se calculó
        self._cota = -1                 # cota con la que se calculó
        self.reutilizar = True          # False: cada consulta calcula desde cero (alternativa que mide --bench)
        self.invalidar_siempre = False  # True: cualquier cambio de puerta invalida (alternativa que mide --bench)
        self.calculos = 0               # contadores para --bench y las pruebas
        self.invalidaciones = 0
        self.salas_fijadas = 0

    def obtener(self, cota: int) -> "CampoDeCostos":
        """Deja listo el campo para consultar con `costo()` (puede reutilizar lo ya calculado). Un valor `costo(sala)`
        mayor que `cota` no cuenta: significa que la sala queda fuera del rango pedido."""
        origen = self.jugador.id_sala_actual
        vigente = self.reutilizar and self._valido and self._origen == origen
        if vigente and cota <= self._cota:
            return self
        nueva = max(cota, self._cota) if vigente else cota          # una cota mayor amplía la zona; nunca la achica
        self._calcular(nueva)
        self._valido = self.reutilizar
        self._origen = origen
        self._cota = nueva
        return self

    def puerta_cambio(self, destino: int) -> None:
        """Avisa que cambió el estado de una salida que lleva a la sala `destino` (abrir, cerrar, deshacer)."""
        if not self._valido:
            return
        if self.invalidar_siempre or (0 <= destino < self.mapa.tamano and self._marca[destino] == self._epoca):
            self._valido = False
            self.invalidaciones += 1

    def costo(self, sala: int) -> int | None:
        """Costo mínimo de `sala` hasta el jugador, o None si no hay ruta de costo <= cota."""
        if 0 <= sala < self.mapa.tamano and self._marca[sala] == self._epoca:
            return self._costo[sala]
        return None

    def _calcular(self, cota: int) -> None:
        self.calculos += 1
        self._epoca += 1
        epoca = self._epoca
        origen = self.jugador.id_sala_actual
        monticulo = self._monticulo
        monticulo.vaciar()
        if not 0 <= origen < self.mapa.tamano or cota < 0:
            return
        costos = self._costo
        marcas = self._marca
        costos[origen] = 0
        marcas[origen] = epoca
        monticulo.insertar(0, origen)
        while not monticulo.vacio():
            costo, sala = monticulo.extraer_minimo()
            if costo > costos[sala]:
                continue                            # entrada vieja: ya se encontró un costo menor
            self.salas_fijadas += 1
            for arista in self.mapa.entrantes[sala]:
                if not self.mapa.esta_abierta(arista, self.salas):
                    continue
                nuevo = costo + arista.costo
                if nuevo > cota:
                    continue
                x = arista.origen
                if marcas[x] != epoca or nuevo < costos[x]:
                    costos[x] = nuevo
                    marcas[x] = epoca
                    monticulo.insertar(nuevo, x)
