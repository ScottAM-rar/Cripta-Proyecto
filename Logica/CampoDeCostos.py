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

La búsqueda la hace `BuscadorRutas` sobre una vista del mapa real: sale de la sala del jugador, recorre las aristas
ENTRANTES usando solo las abiertas ahora y se detiene al pasar la cota, así que explora la región dentro de la cota y no
toda la cripta. Este módulo solo decide cuándo hay que volver a buscar.

`MapaCripta.version_puertas` lo sube `fijar_cerrada`, el único punto de cambio de puertas; este módulo no lo toca.
"""
from __future__ import annotations

from Logica.BuscadorRutas import BuscadorRutas, VistaMapaReal
from Logica.MapaCripta import MapaCripta


class CampoDeCostos:
    def __init__(self, mapa: MapaCripta, jugador, salas: list) -> None:
        self.mapa = mapa
        self.jugador = jugador          # se lee su sala EN CADA búsqueda: no hay copia que se pueda quedar vieja
        self.salas = salas
        self.buscador = BuscadorRutas()
        self._vista = VistaMapaReal(mapa, salas)
        self._valido = False            # ¿lo guardado sigue siendo lo que daría calcular desde cero ahora?
        self._origen = -1               # sala del jugador con la que se calculó
        self._cota = -1                 # cota con la que se calculó
        self.reutilizar = True          # False: cada consulta calcula desde cero (alternativa que mide --bench)
        self.invalidar_siempre = False  # True: cualquier cambio de puerta invalida (alternativa que mide --bench)
        self.calculos = 0               # contadores para --bench y las pruebas
        self.invalidaciones = 0

    @property
    def salas_fijadas(self) -> int:
        return self.buscador.salas_fijadas

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
        if self.invalidar_siempre or self.buscador.alcanzo(destino):
            self._valido = False
            self.invalidaciones += 1

    def costo(self, sala: int) -> int | None:
        """Costo mínimo de `sala` hasta el jugador, o None si no hay ruta de costo <= cota."""
        return self.buscador.costo(sala)

    def siguiente_paso(self, origen: int):
        """Arista de menor id de destino que sigue una ruta de costo mínimo desde `origen`, o None (FR-114)."""
        return self.buscador.siguiente_paso(origen)

    def _calcular(self, cota: int) -> None:
        self.calculos += 1
        self.buscador.distancias_hacia(self.jugador.id_sala_actual, self._vista, cota)
