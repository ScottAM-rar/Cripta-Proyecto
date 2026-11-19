"""Capacidad 012 · Equivalencia de la planeación de la vecindad (FR-370 a FR-375) y salidas sin `collections` (FR-389).

Compara `ServicioCripta.salas_vecinas` con una referencia escrita aquí: salas, orden, errores, búsquedas en el
esqueleto y descargas del esqueleto. Las pruebas de equivalencia pasan contra el código de `0b031ec` antes de
cambiarlo (T013). La única excepción es la comprobación del principio I (T009), que falla contra `0b031ec` a propósito.

Solo listas (principio I): sin dict ni set como índice, sin sorted ni .sort, sin heapq, bisect, collections ni
networkx. Los esqueletos son la forma del JSON de la API (lectura de JSON, permitida).
"""
import inspect
import io
import os
import random
import tempfile
import tokenize
import unittest

from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from DTO.SalaDTO import Direccion, SalaDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_dirigido_aleatorio
from tests_labs.partida_prueba import nueva_partida

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


# ---------------------------------------------------------------- proporcionalidad (T047)

def rejilla_rodeada() -> list:
    """Cripta de 1 000 salas que contiene la rejilla 3 × 3 en las salas 1 a 9, con las mismas salidas. Las salas 10
    a 1 000 forman una fila (E y O) y solo se conectan con la rejilla por una salida de un solo sentido de la sala 10
    a la sala 1, así que desde la rejilla no se llega a ellas."""
    conexiones = []
    for numero in range(1, 10):
        if numero % 3 != 0:
            conexiones.append((numero, numero + 1, None, "E", "O"))
        if numero <= 6:
            conexiones.append((numero, numero + 3, None, "S", "N"))
    for numero in range(10, 1000):
        conexiones.append((numero, numero + 1, None, "E", "O"))
    conexiones.append((10, 1, None, "O", "E", {"un_sentido": True}))
    return esqueleto_de_conexiones(conexiones, total=1000)


class Proporcionalidad(unittest.TestCase):
    """FR-376 (Historia 2, escenario 2): el trabajo de una consulta crece con las salas alcanzadas y sus salidas, no
    con el total de salas de la cripta. Se mide con las búsquedas en el esqueleto, que no dependen de la máquina."""

    def test_fr376_busquedas_proporcionales_a_las_salas_alcanzadas(self):
        """FR-376 (Historia 2, escenario 2): con profundidad 5, 1 búsqueda más una por sala expandida (10 en la
        rejilla desde la sala 5), y las mismas cuando la misma vecindad está dentro de una cripta de 1 000 salas."""
        servicio_chica, _ = nuevo_servicio(rejilla())
        respuesta_chica, busquedas_chica = consultar(servicio_chica, 5, 5)
        self.assertEqual(busquedas_chica, 1 + 9)                     # las 9 salas tienen nivel menor que 5
        self.assertEqual(busquedas_chica, referencia(rejilla(), 5, 5)[1])

        grande = rejilla_rodeada()
        self.assertEqual(len(grande), 1000)
        servicio_grande, cliente = nuevo_servicio(grande)
        respuesta_grande, busquedas_grande = consultar(servicio_grande, 5, 5)
        self.assertEqual(respuesta_grande, respuesta_chica)
        self.assertEqual(busquedas_grande, busquedas_chica)
        self.assertEqual(cliente.descargas, 1)


# ---------------------------------------------------------------- principio I (T009)

PROHIBIDOS = ("deque", "collections", "OrderedDict", "defaultdict", "Counter", "heapq", "bisect", "networkx",
              "set(", "frozenset(", "dict(", "sorted(", ".sort(")


class PrincipioI(unittest.TestCase):
    """FR-375: el código de `salas_vecinas` no usa ninguna estructura de biblioteca prohibida por el principio I.

    Es la excepción de la fase 2: FALLA contra `0b031ec` a propósito, porque el código vigente recorre con una
    cola de biblioteca, y tiene que pasar después de T024 (D1). Se mira el código fuente del método y no el
    archivo, porque `_armar_salidas` seguía usando la cola (uso justificado entonces). Desde T048 (corrección L3) el
    archivo entero queda sin `collections`, y eso lo comprueba `SinCollectionsEnProduccion`."""

    def test_fr375_salas_vecinas_sin_estructuras_prohibidas(self):
        """FR-375 (Historia 2, escenario 1)."""
        fuente = inspect.getsource(ServicioCripta.salas_vecinas)
        encontrados = [nombre for nombre in PROHIBIDOS if nombre in fuente]
        self.assertEqual(encontrados, [], f"salas_vecinas usa {encontrados} (principio I)")


# ---------------------------------------------------------------- corrección L3 (T048)

ARCHIVOS_SALIDAS = ("DTO/SalaDTO.py", "adaptadores/servicioCripta.py", "Logica/EstadoGuardadoLogica.py",
                    "Logica/GestorEventos.py")
NOMBRES_L3 = ("deque", "collections")
ORDEN_SALIDAS = [Direccion.NORTE, Direccion.SUR, Direccion.ESTE, Direccion.OESTE]


def nombres_en_codigo(ruta: str) -> list:
    """Las apariciones de `NOMBRES_L3` como nombre en el código (no en cadenas ni comentarios): (línea, nombre)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(raiz, ruta), encoding="utf-8") as archivo:
        texto = archivo.read()
    encontrados = []
    for token in tokenize.generate_tokens(io.StringIO(texto).readline):
        if token.type == tokenize.NAME and token.string in NOMBRES_L3:
            encontrados.append((token.start[0], token.string))
    return encontrados


def cripta_cruz() -> list:
    """La sala 1 tiene las cuatro salidas. Se declaran en el orden O, E, S, N para que la API las entregue al revés."""
    return esqueleto_de_conexiones([(1, 5, None, "O", "E"), (1, 4, None, "E", "O"),
                                    (1, 3, None, "S", "N"), (1, 2, None, "N", "S")])


class SinCollectionsEnProduccion(unittest.TestCase):
    """FR-389 (corrección L3 de la spec 012, T048): las salidas de la sala usan una lista y el código de producción no
    nombra `deque` ni `collections`. Mismo comportamiento: orden N, S, E, O al armar y al guardar y cargar."""

    def test_fr389_archivos_de_salidas_sin_deque_ni_collections(self):
        """FR-389: ninguno de los cuatro archivos de los usos 3 a 6 nombra `deque` ni `collections` en su código."""
        for ruta in ARCHIVOS_SALIDAS:
            with self.subTest(archivo=ruta):
                encontrados = nombres_en_codigo(ruta)
                self.assertEqual(encontrados, [], f"{ruta} usa {encontrados} (FR-389, corrección L3)")

    def test_fr389_armar_salidas_devuelve_lista_en_orden(self):
        """FR-389, FR-387: `_armar_salidas` y el DTO usan una lista, en el orden N, S, E, O aunque la API no lo traiga."""
        self.assertIs(type(SalaDTO(id=1, nombre="x").salidas), list)
        salidas_api = cripta_cruz()[0]["salidas"]
        self.assertEqual(list(salidas_api), ["O", "E", "S", "N"])
        salidas = ServicioCripta._armar_salidas(salidas_api)
        self.assertIs(type(salidas), list)
        self.assertEqual([s.direccion for s in salidas], ORDEN_SALIDAS)
        self.assertEqual([s.sala_destino for s in salidas], [2, 3, 4, 5])
        self.assertEqual(ServicioCripta._armar_salidas(None), [])

    def test_fr389_partida_guardada_y_cargada_conserva_el_orden(self):
        """FR-389, FR-387: guardar en binario y cargar rearma una lista con las mismas salidas en el mismo orden."""
        logica = nueva_partida(cripta_cruz())
        antes = logica.estadoJuego.salas[1].salidas
        self.assertEqual([s.direccion for s in antes], ORDEN_SALIDAS)
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = os.path.join(carpeta, "partida.bin")
            AlmacenPartidaBinario(archivo).guardar(logica.exportar_estado())
            cargada = EstadoJuegoLogica()
            cargada.comunicacion = ServicioCripta(HttpConfigurable(cripta_cruz(), sala_salida=1000), CacheLRU(25))
            cargada.restaurar_estado(AlmacenPartidaBinario(archivo).cargar())
        despues = cargada.estadoJuego.salas[1].salidas
        self.assertIs(type(despues), list)
        self.assertEqual([(s.direccion, s.sala_destino, s.cerrada, s.llave, s.cierre_automatico, s.costo) for s in despues],
                         [(s.direccion, s.sala_destino, s.cerrada, s.llave, s.cierre_automatico, s.costo) for s in antes])


if __name__ == "__main__":
    unittest.main()
