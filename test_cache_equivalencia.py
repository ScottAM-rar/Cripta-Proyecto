"""Capacidad 012 · Equivalencia de la caché de fichas (FR-386, FR-387).

Compara `CacheLRU` con una LRU de referencia escrita aquí, con la semántica de
specs/012-revision-parte-i/contracts/vecindad-y-cache.md. Las pruebas de equivalencia pasan contra el código de
`0b031ec` antes de cambiarlo (T014). La única excepción es la comprobación del principio I (T012), que falla contra
`0b031ec` a propósito.

Solo listas (principio I): la referencia es una lista de listas [clave, valor, veces] con búsqueda lineal, sin dict
por clave, sin sorted ni .sort, sin heapq, bisect, collections ni networkx.
"""
import os
import random
import unittest

from adaptadores.cache import CacheLRU
from test_monticulo_minimo import importaciones_prohibidas

SEMILLAS = 20
OPERACIONES = 2000
CAPACIDADES = (1, 2, 5, 25)


class LRUReferencia:
    """LRU de referencia (T010). La más reciente va en la posición 0; cada entrada es [clave, valor, veces_en_uso]."""

    def __init__(self, capacidad: int) -> None:
        self.capacidad = capacidad
        self.entradas = []
        self.aciertos = 0
        self.fallos = 0
        self.expulsada = None             # clave expulsada por la última inserción, o None

    def _posicion(self, clave):
        for i in range(len(self.entradas)):
            if self.entradas[i][0] == clave:
                return i
        return -1

    def claves(self) -> list:
        return [entrada[0] for entrada in self.entradas]

    def _al_frente(self, i: int) -> None:
        entrada = self.entradas[i]
        del self.entradas[i]
        self.entradas.insert(0, entrada)

    def obtener(self, clave):
        i = self._posicion(clave)
        if i < 0:
            self.fallos += 1
            return None
        self.aciertos += 1
        self._al_frente(i)
        return self.entradas[0][1]

    def insertar(self, clave, valor) -> bool:
        self.expulsada = None
        i = self._posicion(clave)
        if i >= 0:
            self.entradas[i][1] = valor
            self._al_frente(i)
            return True
        if len(self.entradas) >= self.capacidad:
            libre = -1
            for j in range(len(self.entradas) - 1, -1, -1):    # la menos reciente que no está en uso
                if self.entradas[j][2] == 0:
                    libre = j
                    break
            if libre < 0:
                return False
            self.expulsada = self.entradas[libre][0]
            del self.entradas[libre]
        self.entradas.insert(0, [clave, valor, 0])
        return True

    def marcar_en_uso(self, clave) -> None:
        i = self._posicion(clave)
        if i >= 0:
            self.entradas[i][2] += 1

    def marcar_libre(self, clave) -> None:
        i = self._posicion(clave)
        if i >= 0 and self.entradas[i][2] > 0:
            self.entradas[i][2] -= 1

    def establecer_en_uso(self, claves: list) -> None:
        for entrada in self.entradas:
            veces = 0
            for clave in claves:
                if clave == entrada[0]:
                    veces += 1
            entrada[2] = veces

    def en_uso(self, clave) -> bool:
        i = self._posicion(clave)
        return i >= 0 and self.entradas[i][2] > 0


def falta_en(antes: list, despues: list):
    """La clave de `antes` que ya no está en `despues` (recorrido lineal), o None."""
    for clave in antes:
        if clave not in despues:
            return clave
    return None


# ---------------------------------------------------------------- secuencias aleatorias (T010)

class EquivalenciaAleatoria(unittest.TestCase):
    """FR-386, FR-387: con secuencias aleatorias de semilla fija, `CacheLRU` hace exactamente lo mismo que la
    referencia (valor devuelto, claves, tamaño, aciertos, fallos y qué clave se expulsa)."""

    def comprobar_estado(self, cache, ref, contexto):
        self.assertEqual(cache.claves(), ref.claves(), contexto)
        self.assertEqual(len(cache), len(ref.entradas), contexto)
        self.assertLessEqual(len(cache), ref.capacidad, contexto)
        self.assertEqual(cache.aciertos, ref.aciertos, contexto)
        self.assertEqual(cache.fallos, ref.fallos, contexto)

    def test_fr386_fr387_secuencias_aleatorias(self):
        """FR-386, FR-387 (Historia 5, escenario 2): 20 semillas × 2 000 operaciones con capacidades 1, 2, 5 y 25."""
        for capacidad in CAPACIDADES:
            universo = [f"k{i}" for i in range(2 * capacidad + 3)]           # más claves que la capacidad
            for semilla in range(SEMILLAS):
                with self.subTest(capacidad=capacidad, semilla=semilla):
                    azar = random.Random(semilla * 100 + capacidad)
                    cache, ref = CacheLRU(capacidad), LRUReferencia(capacidad)
                    for paso in range(OPERACIONES):
                        clave = universo[azar.randrange(len(universo))]
                        operacion = azar.choice(("obtener", "obtener", "insertar", "insertar", "insertar",
                                                 "marcar_en_uso", "marcar_libre", "marcar_libre",
                                                 "establecer_en_uso", "en_uso"))
                        contexto = f"capacidad={capacidad} semilla={semilla} paso={paso} {operacion}({clave})"
                        if operacion == "obtener":
                            self.assertEqual(cache.obtener(clave), ref.obtener(clave), contexto)
                        elif operacion == "insertar":
                            antes = cache.claves()
                            llena = len(cache) >= capacidad
                            valor = (clave, paso)
                            self.assertEqual(cache.insertar(clave, valor), ref.insertar(clave, valor), contexto)
                            if llena:
                                self.assertEqual(falta_en(antes, cache.claves()), ref.expulsada, contexto)
                        elif operacion == "marcar_en_uso":
                            cache.marcar_en_uso(clave)
                            ref.marcar_en_uso(clave)
                        elif operacion == "marcar_libre":
                            cache.marcar_libre(clave)
                            ref.marcar_libre(clave)
                        elif operacion == "establecer_en_uso":
                            claves = [universo[azar.randrange(len(universo))] for _ in range(azar.randrange(4))]
                            cache.establecer_en_uso(claves)
                            ref.establecer_en_uso(claves)
                        else:
                            self.assertEqual(cache.en_uso(clave), ref.en_uso(clave), contexto)
                        self.comprobar_estado(cache, ref, contexto)


# ---------------------------------------------------------------- casos dirigidos (T011)

class CasosDirigidos(unittest.TestCase):
    """FR-386, FR-387: los casos del contrato de la caché, uno por uno."""

    def test_fr387_capacidad_invalida(self):
        """FR-387: CacheLRU(0) se rechaza con el mismo mensaje que hoy."""
        with self.assertRaises(ValueError) as error:
            CacheLRU(0)
        self.assertEqual(str(error.exception), "La capacidad de la caché debe ser al menos 1")

    def test_fr387_todo_en_uso_no_inserta(self):
        """FR-387: con todo en uso, insertar devuelve False y no se supera la capacidad."""
        cache = CacheLRU(2)
        cache.insertar("a", 1)
        cache.insertar("b", 2)
        cache.marcar_en_uso("a")
        cache.marcar_en_uso("b")
        self.assertFalse(cache.insertar("c", 3))
        self.assertLessEqual(len(cache), 2)
        self.assertEqual(cache.claves(), ["b", "a"])

    def test_fr387_reinsertar_reemplaza_sin_expulsar(self):
        """FR-387: reinsertar una clave reemplaza el valor, la pone primera y no expulsa nada."""
        cache = CacheLRU(3)
        for clave in ("a", "b", "c"):
            cache.insertar(clave, clave)
        self.assertTrue(cache.insertar("a", "nuevo"))
        self.assertEqual(cache.claves(), ["a", "c", "b"])
        self.assertEqual(len(cache), 3)
        self.assertEqual(cache.obtener("a"), "nuevo")

    def test_fr387_expulsa_la_menos_reciente_libre(self):
        """FR-387: se expulsa la menos reciente libre aunque haya otras más antiguas en uso."""
        cache = CacheLRU(3)
        for clave in ("a", "b", "c"):
            cache.insertar(clave, clave)
        cache.marcar_en_uso("a")                     # la más antigua, en uso
        self.assertTrue(cache.insertar("d", "d"))
        self.assertEqual(cache.claves(), ["d", "c", "a"])          # salió "b"

    def test_fr387_marcar_libre_no_baja_de_cero(self):
        """FR-387: marcar_libre no baja de 0."""
        cache = CacheLRU(2)
        cache.insertar("a", 1)
        cache.marcar_libre("a")
        cache.marcar_en_uso("a")
        self.assertTrue(cache.en_uso("a"))
        cache.marcar_libre("a")
        self.assertFalse(cache.en_uso("a"))

    def test_fr387_establecer_en_uso_cuenta_repeticiones(self):
        """FR-387: establecer_en_uso deja tantas referencias como repeticiones de la clave."""
        cache = CacheLRU(3)
        for clave in ("a", "b", "c"):
            cache.insertar(clave, clave)
        cache.establecer_en_uso(["a", "a", "b"])
        cache.marcar_libre("a")
        self.assertTrue(cache.en_uso("a"))           # le quedaba una referencia
        cache.marcar_libre("a")
        self.assertFalse(cache.en_uso("a"))
        self.assertTrue(cache.en_uso("b"))
        self.assertFalse(cache.en_uso("c"))

    def test_fr387_contadores(self):
        """FR-387: obtener cuenta aciertos y fallos, y un fallo no cambia el orden."""
        cache = CacheLRU(2)
        cache.insertar("a", 1)
        cache.insertar("b", 2)
        self.assertIsNone(cache.obtener("x"))
        self.assertEqual(cache.claves(), ["b", "a"])
        self.assertEqual(cache.obtener("a"), 1)
        self.assertEqual(cache.claves(), ["a", "b"])
        self.assertEqual((cache.aciertos, cache.fallos), (1, 1))


# ---------------------------------------------------------------- principio I (T012)

class PrincipioI(unittest.TestCase):
    """FR-386: `adaptadores/cache.py` no importa ninguna biblioteca prohibida por el principio I.

    Es la excepción de la fase 2: FALLA contra `0b031ec` a propósito, porque la caché vigente usa la cola de
    `collections`, y tiene que pasar después de T027 (D2)."""

    def test_fr386_cache_sin_importaciones_prohibidas(self):
        """FR-386 (Historia 5, escenario 1)."""
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adaptadores", "cache.py")
        encontradas = list(importaciones_prohibidas(ruta))
        self.assertEqual(encontradas, [], f"adaptadores/cache.py importa {encontradas} (principio I)")


if __name__ == "__main__":
    unittest.main()
