"""Capacidad 012 · Equivalencia de la planeación de la vecindad (FR-370 a FR-375).

Compara `ServicioCripta.salas_vecinas` con una referencia escrita aquí: salas, orden, errores, búsquedas en el
esqueleto y descargas del esqueleto. Las pruebas de equivalencia pasan contra el código de `0b031ec` antes de
cambiarlo (T013). La única excepción es la comprobación del principio I (T009), que falla contra `0b031ec` a propósito.

Solo listas (principio I): sin dict ni set como índice, sin sorted ni .sort, sin heapq, bisect, collections ni
networkx. Los esqueletos son la forma del JSON de la API (lectura de JSON, permitida).
"""
import inspect
import random
import unittest

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_dirigido_aleatorio

CRIPTA = "c012"
LETRAS = ("N", "S", "E", "O")        # el orden vigente de las salidas (FR-371)
PROFUNDIDADES = (0, 1, 2, 5)
SEMILLA = 2026


# ---------------------------------------------------------------- infraestructura (T005)

class ClienteEsqueleto:
    """Cliente sintético (como `ClienteSintetico` del bench): entrega un esqueleto fijo y cuenta las descargas."""

    def __init__(self, salas: list) -> None:
        self.salas = salas
        self.descargas = 0                # llamadas a obtener_salas

    def obtener_criptas(self):
        return [{"id": CRIPTA, "nombre": "Cripta de prueba", "salas": len(self.salas)}]

    def obtener_salas(self, cripta_id):
        self.descargas += 1
        return self.salas


class ServicioEspia(ServicioCripta):
    """Cuenta las búsquedas de una sala dentro del esqueleto en memoria y delega en la original (FR-374)."""

    def __init__(self, cliente) -> None:
        super().__init__(cliente, CacheLRU(5))
        self.busquedas = 0

    def _buscar_esqueleto(self, cripta_id, numero_sala):
        self.busquedas += 1
        return super()._buscar_esqueleto(cripta_id, numero_sala)


def nuevo_servicio(salas: list) -> tuple:
    cliente = ClienteEsqueleto(salas)
    return ServicioEspia(cliente), cliente


def consultar(servicio: ServicioEspia, sala: int, profundidad: int) -> tuple:
    """(respuesta, búsquedas de esta consulta)."""
    servicio.busquedas = 0
    respuesta = servicio.salas_vecinas(CRIPTA, sala, profundidad)
    return respuesta, servicio.busquedas


def salida_de(salas: list, numero: int) -> list:
    """Destinos de la sala `numero` en el orden N, S, E, O (recorrido lineal del esqueleto)."""
    for sala in salas:
        if sala["id"] == numero:
            salidas = sala.get("salidas") or {}
            destinos = []
            for letra in LETRAS:
                if letra in salidas:
                    destinos.append(salidas[letra]["sala"])
            return destinos
    raise ValueError(f"no existe la sala {numero}")


def referencia(salas: list, inicio: int, profundidad: int) -> tuple:
    """Recorrido por niveles escrito en la prueba (FR-370, FR-371, FR-374).

    Cola por índice sobre una lista de pares (sala, nivel); la pertenencia se comprueba recorriendo la lista de
    alcanzadas. Devuelve (salas en orden de descubrimiento sin la de partida, búsquedas = 1 + salas expandidas)."""
    alcanzadas = [inicio]
    pares = [(inicio, 0)]
    lectura = 0
    busquedas = 1                                     # la validación de la sala de partida
    while lectura < len(pares):
        actual, nivel = pares[lectura]
        lectura += 1
        if nivel >= profundidad:
            continue
        busquedas += 1                                # se exploran sus salidas
        for destino in salida_de(salas, actual):
            if destino not in alcanzadas:
                alcanzadas.append(destino)
                pares.append((destino, nivel + 1))
    return alcanzadas[1:], busquedas


def lineal() -> list:
    """Salas 1 a 6 en fila: E a la siguiente y O a la anterior."""
    return esqueleto_de_conexiones([(i, i + 1, None, "E", "O") for i in range(1, 6)])


def rejilla() -> list:
    """3 × 3, salas 1 a 9 por filas: N sube una fila, S baja, E y O se mueven en la fila."""
    conexiones = []
    for numero in range(1, 10):
        if numero % 3 != 0:
            conexiones.append((numero, numero + 1, None, "E", "O"))
        if numero <= 6:
            conexiones.append((numero, numero + 3, None, "S", "N"))
    return esqueleto_de_conexiones(conexiones)


def arbol() -> list:
    """1: S→2 y E→3; 2: S→4 y O→5; 3: E→6; cada hija con la salida de vuelta a su madre."""
    return esqueleto_de_conexiones([(1, 2, None, "S", "N"), (1, 3, None, "E", "O"), (2, 4, None, "S", "N"),
                                    (2, 5, None, "O", "E"), (3, 6, None, "E", "O")])


def ciclos() -> list:
    """2 × 2, salas 1 2 / 3 4, todas las salidas en ambos sentidos."""
    return esqueleto_de_conexiones([(1, 2, None, "E", "O"), (3, 4, None, "E", "O"),
                                    (1, 3, None, "S", "N"), (2, 4, None, "S", "N")])


def puerta_cerrada() -> list:
    """Lineal de 4 con la puerta entre 2 y 3 cerrada."""
    return esqueleto_de_conexiones([(1, 2, None, "E", "O"), (2, 3, None, "E", "O", {"cerrada": True}),
                                    (3, 4, None, "E", "O")])


def un_sentido() -> list:
    """1 → 2 solo de ida; 2 ↔ 3."""
    return esqueleto_de_conexiones([(1, 2, None, "E", "O", {"un_sentido": True}), (2, 3, None, "E", "O")])


def sin_salidas() -> list:
    """1 ↔ 2 y la sala 3 sin salidas."""
    return esqueleto_de_conexiones([(1, 2, None, "E", "O")], total=3)


def a_si_misma() -> list:
    """La sala 1 tiene N→1 y S→1, y E→2."""
    return esqueleto_de_conexiones([(1, 1, None, "N", "S"), (1, 2, None, "E", "O"), (2, 3, None, "E", "O")])


def dos_a_la_misma() -> list:
    """La sala 1 tiene S→2 y E→2."""
    return esqueleto_de_conexiones([(1, 2, None, "E", "O"), (1, 2, None, "S", "N"), (2, 3, None, "E", "O")])


def mil_salas() -> list:
    """Cripta sintética de 1 000 salas, determinista por semilla (ciclos, un sentido, salidas a sí misma)."""
    return esqueleto_dirigido_aleatorio(1000, SEMILLA)


CRIPTAS = (("lineal", lineal), ("rejilla", rejilla), ("arbol", arbol), ("ciclos", ciclos),
           ("puerta_cerrada", puerta_cerrada), ("un_sentido", un_sentido), ("sin_salidas", sin_salidas),
           ("a_si_misma", a_si_misma), ("dos_a_la_misma", dos_a_la_misma))


def ids_de(salas: list) -> list:
    ids = []
    for sala in salas:
        ids.append(sala["id"])
    return ids


# ---------------------------------------------------------------- equivalencia con la referencia (T006)

class EquivalenciaConLaReferencia(unittest.TestCase):
    """FR-370, FR-371, FR-372 y FR-374: misma respuesta, mismo orden y mismas lecturas del esqueleto que la
    referencia, en todas las salas de cada cripta y con las profundidades 0, 1, 2 y 5."""

    def comprobar_cripta(self, nombre: str, salas: list, numeros: list) -> None:
        servicio, cliente = nuevo_servicio(salas)
        for numero in numeros:
            for profundidad in PROFUNDIDADES:
                with self.subTest(cripta=nombre, sala=numero, profundidad=profundidad):
                    esperada, busquedas_esperadas = referencia(salas, numero, profundidad)
                    respuesta, busquedas = consultar(servicio, numero, profundidad)
                    self.assertEqual(respuesta, esperada)                    # FR-370, FR-371
                    self.assertEqual(busquedas, busquedas_esperadas)         # FR-374, búsquedas
                    self.assertEqual(cliente.descargas, 1)                   # FR-374, ninguna descarga adicional
                    if profundidad == 0:                                     # FR-372
                        self.assertEqual(respuesta, [])
                        self.assertEqual(busquedas, 1)

    def test_fr370_fr371_fr372_fr374_criptas_chicas(self):
        """FR-370, FR-371, FR-372, FR-374: las cuatro criptas de la spec y los casos límite, todas sus salas."""
        for nombre, construir in CRIPTAS:
            salas = construir()
            self.comprobar_cripta(nombre, salas, ids_de(salas))

    def test_fr370_fr371_fr374_mil_salas(self):
        """FR-370, FR-371, FR-374 (Historia 1, escenario 13): 50 salas tomadas con la semilla en la de 1 000."""
        salas = mil_salas()
        muestra = random.Random(SEMILLA).sample(ids_de(salas), 50)
        self.comprobar_cripta("mil_salas", salas, muestra)

    def test_fr370_casos_limite_puntuales(self):
        """FR-370, FR-371 (casos límite): puerta cerrada, un sentido, sin salidas, a sí misma, dos a la misma."""
        casos = (
            (puerta_cerrada, 2, 1, [3, 1]),          # la sala tras la puerta cerrada aparece (E antes que O)
            (un_sentido, 1, 5, [2, 3]),              # desde A se llega a B
            (un_sentido, 2, 5, [3]),                 # desde B no se llega a A
            (sin_salidas, 3, 5, []),                 # sala sin salidas: vacía con cualquier profundidad
            (a_si_misma, 1, 5, [2, 3]),              # la propia sala no aparece
            (dos_a_la_misma, 1, 1, [2]),             # el destino aparece una sola vez
        )
        for construir, sala, profundidad, esperada in casos:
            with self.subTest(cripta=construir.__name__, sala=sala, profundidad=profundidad):
                servicio, _ = nuevo_servicio(construir())
                self.assertEqual(consultar(servicio, sala, profundidad)[0], esperada)


# ---------------------------------------------------------------- valores literales de la spec (T007)

class ValoresDeLaHistoria1(unittest.TestCase):
    """FR-371 y FR-374: los valores literales de los escenarios 2 a 8 y 12 de la Historia 1 (orden N, S, E, O)."""

    def comprobar(self, construir, sala: int, por_profundidad: list) -> None:
        servicio, _ = nuevo_servicio(construir())
        for profundidad, esperada in por_profundidad:
            with self.subTest(cripta=construir.__name__, sala=sala, profundidad=profundidad):
                self.assertEqual(consultar(servicio, sala, profundidad)[0], esperada)

    def test_fr371_lineal(self):
        """FR-371, escenarios 2 y 3: lineal, sala 3 y sala 1."""
        self.comprobar(lineal, 3, [(1, [4, 2]), (2, [4, 2, 5, 1]), (5, [4, 2, 5, 1, 6])])
        self.comprobar(lineal, 1, [(5, [2, 3, 4, 5, 6])])

    def test_fr371_rejilla(self):
        """FR-371, escenarios 4 y 5: rejilla, sala 5 y sala 1."""
        self.comprobar(rejilla, 5, [(1, [2, 8, 6, 4]), (2, [2, 8, 6, 4, 3, 1, 9, 7]), (5, [2, 8, 6, 4, 3, 1, 9, 7])])
        self.comprobar(rejilla, 1, [(2, [4, 2, 7, 5, 3])])

    def test_fr371_arbol(self):
        """FR-371, escenarios 6 y 7: árbol, sala 1 y sala 4."""
        self.comprobar(arbol, 1, [(1, [2, 3]), (2, [2, 3, 4, 5, 6]), (5, [2, 3, 4, 5, 6])])
        self.comprobar(arbol, 4, [(5, [2, 1, 5, 3, 6])])

    def test_fr371_ciclos(self):
        """FR-371, escenario 8: con ciclos, sala 1."""
        self.comprobar(ciclos, 1, [(1, [3, 2]), (2, [3, 2, 4]), (5, [3, 2, 4])])

    def test_fr374_busquedas_rejilla(self):
        """FR-374, escenario 12: en la rejilla desde la sala 5, 1, 2 y 6 búsquedas con profundidad 0, 1 y 2."""
        servicio, cliente = nuevo_servicio(rejilla())
        for profundidad, esperadas in ((0, 1), (1, 2), (2, 6)):
            with self.subTest(profundidad=profundidad):
                self.assertEqual(consultar(servicio, 5, profundidad)[1], esperadas)
        self.assertEqual(cliente.descargas, 1)


# ---------------------------------------------------------------- errores (T008)

class Errores(unittest.TestCase):
    """FR-373: mismos errores y mismo orden de comprobación que hoy (primero la profundidad, después la sala)."""

    def test_fr373_profundidad_negativa(self):
        """FR-373 (Historia 1, escenario 10 y caso límite): profundidad −1, también con una sala inexistente,
        se rechaza por la profundidad sin buscar ni descargar el esqueleto."""
        for sala in (1, 99):
            with self.subTest(sala=sala):
                servicio, cliente = nuevo_servicio(rejilla())
                with self.assertRaises(ValueError) as error:
                    servicio.salas_vecinas(CRIPTA, sala, -1)
                self.assertEqual(str(error.exception), "La profundidad no puede ser negativa")
                self.assertEqual(servicio.busquedas, 0)
                self.assertEqual(cliente.descargas, 0)

    def test_fr373_sala_inexistente(self):
        """FR-373 (Historia 1, escenario 11): una sala que no existe se rechaza con profundidad 0, 1, 2 y 5."""
        servicio, _ = nuevo_servicio(rejilla())
        for profundidad in PROFUNDIDADES:
            with self.subTest(profundidad=profundidad):
                with self.assertRaises(ValueError) as error:
                    servicio.salas_vecinas(CRIPTA, 99, profundidad)
                self.assertEqual(str(error.exception), f"La cripta '{CRIPTA}' no tiene la sala 99")

    def test_fr373_cripta_inexistente(self):
        """FR-373: una cripta que no existe se rechaza en la carga del esqueleto, sin descargarlo."""
        servicio, cliente = nuevo_servicio(rejilla())
        with self.assertRaises(ValueError) as error:
            servicio.salas_vecinas("otra", 1, 1)
        self.assertEqual(str(error.exception), "La cripta 'otra' no existe")
        self.assertEqual(cliente.descargas, 0)


# ---------------------------------------------------------------- principio I (T009)

PROHIBIDOS = ("deque", "collections", "OrderedDict", "defaultdict", "Counter", "heapq", "bisect", "networkx",
              "set(", "frozenset(", "dict(", "sorted(", ".sort(")


class PrincipioI(unittest.TestCase):
    """FR-375: el código de `salas_vecinas` no usa ninguna estructura de biblioteca prohibida por el principio I.

    Es la excepción de la fase 2: FALLA contra `0b031ec` a propósito, porque el código vigente recorre con una
    cola de biblioteca, y tiene que pasar después de T024 (D1). Se mira el código fuente del método y no el
    archivo, porque `_armar_salidas` sigue usando la cola (uso justificado en el inventario)."""

    def test_fr375_salas_vecinas_sin_estructuras_prohibidas(self):
        """FR-375 (Historia 2, escenario 1)."""
        fuente = inspect.getsource(ServicioCripta.salas_vecinas)
        encontrados = [nombre for nombre in PROHIBIDOS if nombre in fuente]
        self.assertEqual(encontrados, [], f"salas_vecinas usa {encontrados} (principio I)")


if __name__ == "__main__":
    unittest.main()
