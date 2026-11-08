"""Capacidad 003, T004: la llave de cada puerta llega al mapa (contracts/mapa-con-llaves.md, G1 a G6).

La API publica la llave de una puerta cerrada en la propia salida ("llave": "itm_..."). Estas pruebas comprueban que
`ServicioCripta.esqueleto()` la copia a `AristaMapaDTO.llave`, que `MapaCripta` la copia a `AristaCripta.llave`, y que
llega igual por `--offline` (ClienteOffline) y por la lectura solo local (FuenteSoloLocal), sin solicitudes nuevas.

El campo se lee con getattr(..., "<sin campo>") para que, mientras no exista, la prueba falle por aserción y no por un
AttributeError. Todo corre con requests.get bloqueado: si algo intentara usar la red, la prueba fallaría."""
import shutil
import tempfile
import unittest
from unittest import mock

import requests

from adaptadores import fabrica
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from DTO.MapaDTO import AristaMapaDTO
from Logica.MapaCripta import AristaCripta, MapaCripta
from tests_labs.api_falsa import CASOS_APENDICE_B

CRIPTA = "cripta-01"
SIN_CAMPO = "<sin campo>"

# Ternas (sala de origen, dirección, llave) del caso B-R3 de la API falsa v2: 1-4 se abre con itm_llave_a y 4-5 con
# itm_llave_b, en los dos sentidos; las demás salidas no tienen llave.
TERNAS_B_R3 = [
    (1, "sur", "itm_llave_a"), (1, "este", None), (1, "oeste", None),
    (2, "oeste", None),
    (3, "este", None),
    (4, "norte", "itm_llave_a"), (4, "sur", "itm_llave_b"),
    (5, "norte", "itm_llave_b"),
]

# Línea base de T002 (anotada en checklists/requirements.md antes de cambiar código): listar las criptas y pedir el
# esqueleto del caso B-R3 hace exactamente estas llamadas.
LLAMADAS_BASE = [("criptas", None), ("salas", CRIPTA)]


def _sin_red(*args, **kwargs):
    raise AssertionError("intento de red")


_parche_red = mock.patch.object(requests, "get", side_effect=_sin_red)


def setUpModule():
    _parche_red.start()


def tearDownModule():
    _parche_red.stop()


def http_b_r3():
    """El HttpConfigurable del caso B-R3, construido desde CASOS_APENDICE_B."""
    for codigo, _descripcion, constructor in CASOS_APENDICE_B:
        if codigo == "B-R3":
            http, _guion = constructor()
            return http
    raise AssertionError("CASOS_APENDICE_B no tiene el caso B-R3")


def ternas_de_mapa_dto(mapa) -> list:
    ternas = []
    for sala in mapa.salas:
        if sala is None:
            continue
        for arista in sala.salidas:
            ternas.append((sala.id, arista.direccion, getattr(arista, "llave", SIN_CAMPO)))
    return ternas


def ternas_de_mapa_cripta(mapa: MapaCripta) -> list:
    ternas = []
    for sala in range(mapa.tamano):
        for arista in mapa.salidas(sala):
            ternas.append((arista.origen, arista.direccion, getattr(arista, "llave", SIN_CAMPO)))
    return ternas


class MapaConLlaves(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="cripta_003_mapa_")

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def _guardar_con_persistente(self):
        """Guarda la cripta del caso B-R3 completa en la carpeta temporal por el flujo normal (ClientePersistente), como
        `guardar_cripta_completa` de test_fuente_solo_local: --offline solo acepta criptas guardadas por completo."""
        servicio = ServicioCripta(ClientePersistente(http_b_r3(), AlmacenDisco(self.carpeta)), CacheLRU(25))
        servicio.listar_criptas()
        servicio.crear_jugador(CRIPTA)
        servicio.construir_todas(CRIPTA)
        servicio.ubicacion_llaves(CRIPTA)
        return ternas_de_mapa_dto(servicio.esqueleto(CRIPTA))

    def test_fr333_g1_esqueleto_copia_la_llave(self):
        servicio = ServicioCripta(http_b_r3(), CacheLRU(25))
        servicio.listar_criptas()
        self.assertEqual(ternas_de_mapa_dto(servicio.esqueleto(CRIPTA)), TERNAS_B_R3)

    def test_fr333_g2_mapa_cripta_copia_la_llave(self):
        servicio = ServicioCripta(http_b_r3(), CacheLRU(25))
        servicio.listar_criptas()
        mapa = MapaCripta(servicio.esqueleto(CRIPTA))
        self.assertEqual(ternas_de_mapa_cripta(mapa), TERNAS_B_R3)

    def test_fr342_g3_offline_igual_que_con_red(self):
        con_red = self._guardar_con_persistente()
        offline = ServicioCripta(ClienteOffline(AlmacenDisco(self.carpeta)), CacheLRU(25))
        offline.listar_criptas()
        sin_red = ternas_de_mapa_dto(offline.esqueleto(CRIPTA))
        self.assertEqual(sin_red, con_red)
        self.assertEqual(sin_red, TERNAS_B_R3)

    def test_fr342_g4_fuente_solo_local_igual_sin_solicitudes(self):
        self._guardar_con_persistente()
        fuente = fabrica.crear_fuente_solo_local(carpeta=self.carpeta)
        antes = fuente.fuente.solicitudes_realizadas
        ternas = ternas_de_mapa_dto(fuente.esqueleto(CRIPTA))
        self.assertEqual(ternas, TERNAS_B_R3)
        self.assertEqual(fuente.fuente.solicitudes_realizadas, antes)

    def test_g5_construccion_sin_llave_sigue_funcionando(self):
        dto = AristaMapaDTO("este", 2, 100, False)                  # como lo construyen hoy la 001 y la 005
        self.assertIsNone(getattr(dto, "llave", SIN_CAMPO))
        arista = AristaCripta(1, "este", 2, 100, False)              # cinco argumentos posicionales, como hoy
        self.assertIsNone(getattr(arista, "llave", SIN_CAMPO))
        try:
            con_llave_dto = AristaMapaDTO("este", 2, 100, True, llave="x")
            con_llave = AristaCripta(1, "este", 2, 100, True, "x")
        except TypeError as error:
            self.fail(f"Las aristas todavía no aceptan la llave: {error}")
        self.assertEqual(con_llave_dto.llave, "x")
        self.assertEqual(con_llave.llave, "x")

    def test_fr341_g6_sin_solicitudes_nuevas(self):
        http = http_b_r3()
        servicio = ServicioCripta(http, CacheLRU(25))
        servicio.listar_criptas()
        servicio.esqueleto(CRIPTA)
        servicio.esqueleto(CRIPTA)                                   # la segunda vez sale de lo memorizado
        self.assertEqual(http.veces("salas"), 1)
        self.assertEqual(http.llamadas, LLAMADAS_BASE)


if __name__ == "__main__":
    unittest.main()
