"""Capacidad 009, T012: la consulta de llaves por los tres clientes y por ServicioCripta (FR-302, FR-303, FR-304).

Sin red: requests.get se sustituye con unittest.mock.patch y la cripta la arma HttpConfigurable en una carpeta temporal."""
import os
import tempfile
import unittest
from unittest import mock

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_http import ClienteCripta
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from Logica.FuenteCripta import LlavesNoDisponibles
from tests_labs.api_falsa import HttpConfigurable


def pasillo(n):
    """Salas 1..n en fila, unidas norte-sur."""
    salas = []
    for i in range(1, n + 1):
        salidas = {}
        if i > 1:
            salidas["S"] = {"sala": i - 1}
        if i < n:
            salidas["N"] = {"sala": i + 1}
        salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})
    return salas


class Respuesta:
    def __init__(self, codigo, cuerpo):
        self.status_code = codigo
        self._cuerpo = cuerpo

    def json(self):
        return self._cuerpo


class ConCarpeta(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = os.path.join(self._tmp.name, "datos_cripta")

    def tearDown(self):
        self._tmp.cleanup()

    def servicio(self, http, carpeta=None):
        cliente = ClientePersistente(http, AlmacenDisco(carpeta or self.carpeta))
        return ServicioCripta(cliente, CacheLRU(25))


class ClienteHttpObtenerLlaves(unittest.TestCase):

    def test_fr304_a_http_pide_la_ruta_de_llaves_con_el_encabezado_y_cuenta_una_solicitud(self):
        cuerpo = {"llaves": [{"id": "itm_llave_bronce", "sala": 3}]}
        cliente = ClienteCripta("http://falso/v1")
        with mock.patch("adaptadores.cliente_http.requests.get", return_value=Respuesta(200, cuerpo)) as get:
            llaves = cliente.obtener_llaves("cripta-07")
        self.assertEqual(llaves, cuerpo["llaves"])
        self.assertEqual(get.call_count, 1)
        self.assertEqual(get.call_args.args[0], "http://falso/v1/criptas/cripta-07/llaves")
        self.assertEqual(get.call_args.kwargs["headers"]["X-Cripta-Client-Id"], cliente.client_id)
        self.assertEqual(cliente.solicitudes_realizadas, 1)

    def test_fr304_a_http_con_solo_guardadas_no_hace_la_solicitud(self):
        cliente = ClienteCripta("http://falso/v1")
        with mock.patch("adaptadores.cliente_http.requests.get") as get:
            with self.assertRaises(LlavesNoDisponibles) as error:
                cliente.obtener_llaves("cripta-07", solo_guardadas=True)
        self.assertEqual(get.call_count, 0)
        self.assertEqual(cliente.solicitudes_realizadas, 0)
        self.assertIn("cripta-07", str(error.exception))


class UbicacionLlavesDelServicio(ConCarpeta):

    def test_fr302_b_h1_2_llave_soltada_por_enemigo_trae_su_sala_inicial(self):
        http = HttpConfigurable(pasillo(9), [(7, "e-701", "ent_guardian_oseo", None)],
                                llaves=[("itm_llave_L", 7, "e-701")])
        dto = self.servicio(http).ubicacion_llaves("cripta-01")
        self.assertEqual((dto.ids, dto.salas, dto.enemigos), (["itm_llave_L"], [7], ["e-701"]))
        self.assertEqual(dto.cripta_id, "cripta-01")

    def test_fr302_c_h1_3_llave_en_el_suelo_no_tiene_enemigo(self):
        http = HttpConfigurable(pasillo(9), llaves=[("itm_llave_M", 3, None)])
        dto = self.servicio(http).ubicacion_llaves("cripta-01")
        self.assertEqual((dto.ids, dto.salas, dto.enemigos), (["itm_llave_M"], [3], [None]))

    def test_fr302_d_h1_5_misma_llave_en_dos_salas_da_dos_ubicaciones(self):
        http = HttpConfigurable(pasillo(9), llaves=[("itm_llave_B", 3, None), ("itm_llave_B", 9, None)])
        dto = self.servicio(http).ubicacion_llaves("cripta-01")
        posiciones = dto.ubicaciones_de("itm_llave_B")
        self.assertEqual(len(posiciones), 2)
        self.assertEqual([dto.salas[i] for i in posiciones], [3, 9])


class MismaListaPorLosTresClientes(ConCarpeta):

    def test_fr303_e_h5_5_http_persistente_y_offline_dan_la_misma_lista(self):
        crudas = [{"id": "itm_llave_bronce", "sala": 3},
                  {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"},
                  {"id": "itm_llave_bronce", "sala": 9}]
        tuplas = [("itm_llave_bronce", 3, None), ("itm_llave_negra", 4, "e-401"), ("itm_llave_bronce", 9, None)]

        cliente_http = ClienteCripta("http://falso/v1")
        with mock.patch("adaptadores.cliente_http.requests.get", return_value=Respuesta(200, {"llaves": crudas})):
            por_http = cliente_http.obtener_llaves("cripta-01")

        http = HttpConfigurable(pasillo(9), [(4, "e-401", "ent_guardian_oseo", None)], llaves=tuplas)
        servicio_persistente = self.servicio(http)
        servicio_persistente.construir_todas("cripta-01")      # deja la cripta completa en disco para --offline
        dto_persistente = servicio_persistente.ubicacion_llaves("cripta-01")
        por_persistente = servicio_persistente.cliente.obtener_llaves("cripta-01")

        offline = ClienteOffline(AlmacenDisco(self.carpeta))
        por_offline = offline.obtener_llaves("cripta-01")
        dto_offline = ServicioCripta(offline, CacheLRU(25)).ubicacion_llaves("cripta-01")

        self.assertEqual(por_http, crudas)
        self.assertEqual(por_persistente, crudas)
        self.assertEqual(por_offline, crudas)
        self.assertEqual((dto_offline.ids, dto_offline.salas, dto_offline.enemigos),
                         (dto_persistente.ids, dto_persistente.salas, dto_persistente.enemigos))
        self.assertEqual(offline.solicitudes_realizadas, 0)


if __name__ == "__main__":
    unittest.main()
