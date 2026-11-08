"""Capacidad 009, T013 y T048: la consulta de llaves dentro del presupuesto de solicitudes (FR-301, FR-304, FR-309,
FR-313, SC-005).

Sin red: la cripta la arma HttpConfigurable en una carpeta temporal, o requests.get se sustituye con
unittest.mock.patch (T048). Ninguna prueba espera de verdad: time.sleep también se sustituye."""
import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import adaptadores.cliente_http as cliente_http
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_http import ClienteCripta, MAX_REINTENTOS_429
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.FuenteCripta import LlavesNoDisponibles
from Logica.RetrocesoLogica import RetrocesoLogica
from tests_labs.api_falsa import HttpConfigurable

SALAS = [{"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
         {"id": 2, "nombre": "Pasillo", "salidas": {"S": {"sala": 1}, "N": {"sala": 3}}},
         {"id": 3, "nombre": "Salida", "salidas": {"S": {"sala": 2}}}]
ENEMIGOS = [(3, "e-301", "ent_guardian_oseo", 15)]

# Línea base de la partida de (a), medida el 2026-11-07 con el código anterior a esta capacidad (sin consulta de
# llaves): HttpConfigurable(SALAS, ENEMIGOS) + ClientePersistente en una carpeta vacía + ServicioCripta,
# iniciarJuego("cripta-01", 1) e ingresarEnSala(sala inicial). Llamadas por nombre, en orden de aparición:
LINEA_BASE = [("criptas", 1), ("datos", 1), ("version_catalogo", 1), ("salas", 1), ("contenido", 1), ("catalogo", 1)]
TOTAL_LINEA_BASE = 6          # reporte: «Solicitudes a la API: 6 de 9»


class HttpConPresupuesto(HttpConfigurable):
    """HttpConfigurable con el presupuesto_solicitudes que pide la prueba."""

    def __init__(self, *args, presupuesto=9, **kwargs):
        super().__init__(*args, **kwargs)
        self.presupuesto = presupuesto

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["presupuesto_solicitudes"] = self.presupuesto
        return datos


class ConCarpeta(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = os.path.join(self._tmp.name, "datos_cripta")

    def tearDown(self):
        self._tmp.cleanup()

    def servicio(self, http):
        return ServicioCripta(ClientePersistente(http, AlmacenDisco(self.carpeta)), CacheLRU(25))


class PrimeraPartida(ConCarpeta):

    def test_fr301_fr304_a_h1_1_primera_partida_hace_una_consulta_de_llaves_ademas_de_la_linea_base(self):
        RetrocesoLogica().reiniciar()
        http = HttpConfigurable(SALAS, ENEMIGOS)
        servicio = self.servicio(http)
        logica = EstadoJuegoLogica(comunicacion=servicio)
        with contextlib.redirect_stdout(io.StringIO()):
            logica.iniciarJuego("cripta-01", 1)
            logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)

        self.assertEqual(http.veces("llaves"), 1)
        sin_llaves = [(nombre, http.veces(nombre)) for nombre in http.nombres() if nombre != "llaves"]
        self.assertEqual(sin_llaves, LINEA_BASE)
        self.assertEqual(http.solicitudes_realizadas, TOTAL_LINEA_BASE + 1)
        self.assertIn(f"Solicitudes a la API: {TOTAL_LINEA_BASE + 1} de 9", servicio.reporte("cripta-01").texto())


class UnaVezPorSesion(ConCarpeta):

    def test_fr301_b_h1_4_dos_consultas_en_la_misma_sesion_hacen_una_sola_solicitud(self):
        http = HttpConfigurable(SALAS, ENEMIGOS)
        servicio = self.servicio(http)
        primera = servicio.ubicacion_llaves("cripta-01")
        segunda = servicio.ubicacion_llaves("cripta-01")
        self.assertEqual(http.veces("llaves"), 1)
        self.assertEqual((segunda.ids, segunda.salas, segunda.enemigos),
                         (primera.ids, primera.salas, primera.enemigos))


class PresupuestoAgotado(ConCarpeta):

    def test_fr309_c_sc005_sin_presupuesto_ni_llaves_guardadas_no_consulta_y_avisa_con_la_cripta(self):
        http = HttpConPresupuesto(SALAS, ENEMIGOS, presupuesto=3)
        servicio = self.servicio(http)
        servicio.total_salas("cripta-01")                    # criptas + datos + salas = 3 = presupuesto
        self.assertEqual(servicio.solicitudes_realizadas, 3)
        with self.assertRaises(LlavesNoDisponibles) as error:
            servicio.ubicacion_llaves("cripta-01")
        self.assertEqual(http.veces("llaves"), 0)
        self.assertEqual(servicio.solicitudes_realizadas, 3)
        self.assertIn("cripta-01", str(error.exception))

    def test_fr301_d_sin_presupuesto_con_llaves_guardadas_las_devuelve_sin_solicitudes(self):
        primera = self.servicio(HttpConfigurable(SALAS, ENEMIGOS)).ubicacion_llaves("cripta-01")

        http = HttpConPresupuesto(SALAS, ENEMIGOS, presupuesto=2)
        servicio = self.servicio(http)
        servicio.total_salas("cripta-01")                    # criptas + datos (las salas salen del disco) = 2
        antes = servicio.solicitudes_realizadas
        self.assertEqual(antes, 2)
        dto = servicio.ubicacion_llaves("cripta-01")
        self.assertEqual(http.veces("llaves"), 0)
        self.assertEqual(servicio.solicitudes_realizadas, antes)
        self.assertEqual((dto.ids, dto.salas, dto.enemigos), (primera.ids, primera.salas, primera.enemigos))


# ----------------------------------------------------------------------------------------------------------------
# T048: 429 con el presupuesto al límite, con requests.get sustituido (reintentar_en: 0)
# ----------------------------------------------------------------------------------------------------------------
class Respuesta:
    def __init__(self, codigo, cuerpo):
        self.status_code = codigo
        self._cuerpo = cuerpo

    def json(self):
        return self._cuerpo


R429 = Respuesta(429, {"reintentar_en": 0})


class ServidorFalso:
    """Responde por ruta y apunta cada llamada a requests.get. `llaves`: respuestas de /llaves, en orden."""

    def __init__(self, presupuesto, llaves):
        self.presupuesto = presupuesto
        self.llaves = list(llaves)
        self.urls: list[str] = []

    def __call__(self, url, headers=None, timeout=None):
        self.urls.append(url)
        ruta = url.split("/v1", 1)[1]
        if ruta == "/criptas":
            return Respuesta(200, {"criptas": [{"id": "cripta-01", "nombre": "Prueba", "salas": 3, "dificultad": 1}]})
        if ruta == "/criptas/cripta-01":
            return Respuesta(200, {"id": "cripta-01", "salas_total": 3, "sala_inicial": 1, "sala_salida": 3,
                                   "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": self.presupuesto,
                                   "inventario_max": 10, "version": "c1",
                                   "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}})
        if ruta == "/criptas/cripta-01/salas?pagina=1":
            return Respuesta(200, {"salas": SALAS, "total_paginas": 1})
        if ruta == "/criptas/cripta-01/llaves":
            return self.llaves.pop(0)
        raise AssertionError(f"ruta inesperada {ruta}")

    def veces_llaves(self):
        total = 0
        for url in self.urls:
            if url.endswith("/llaves"):
                total += 1
        return total


class LimiteDeReintentos(unittest.TestCase):

    def servicio_con(self, servidor):
        servicio = ServicioCripta(ClienteCripta("http://falso/v1"), CacheLRU(25))
        with mock.patch.object(cliente_http.requests, "get", side_effect=servidor):
            servicio.total_salas("cripta-01")                # criptas + salas
            servicio.datos_cripta("cripta-01")               # + datos = 3
        return servicio

    def test_sc005_e_con_1_restante_un_429_no_se_reintenta_y_avisa_con_la_cripta(self):
        servidor = ServidorFalso(presupuesto=4, llaves=[R429])
        servicio = self.servicio_con(servidor)
        antes = len(servidor.urls)
        with mock.patch.object(cliente_http.requests, "get", side_effect=servidor), \
                mock.patch.object(cliente_http.time, "sleep") as dormir:
            with self.assertRaises(LlavesNoDisponibles) as error:
                servicio.ubicacion_llaves("cripta-01")
        self.assertEqual(len(servidor.urls) - antes, 1)
        self.assertEqual(servidor.veces_llaves(), 1)
        self.assertEqual(dormir.call_count, 0)
        self.assertIn("cripta-01", str(error.exception))
        self.assertLessEqual(servicio.solicitudes_realizadas, 4)

    def test_sc005_f_con_3_restantes_429_429_200_hace_3_llamadas_y_devuelve_las_llaves(self):
        llaves = Respuesta(200, {"llaves": [{"id": "itm_llave_negra", "sala": 3}]})
        servidor = ServidorFalso(presupuesto=6, llaves=[R429, R429, llaves])
        servicio = self.servicio_con(servidor)
        with mock.patch.object(cliente_http.requests, "get", side_effect=servidor), \
                mock.patch.object(cliente_http.time, "sleep"):
            dto = servicio.ubicacion_llaves("cripta-01")
        self.assertEqual(servidor.veces_llaves(), 3)
        self.assertEqual((dto.ids, dto.salas, dto.enemigos), (["itm_llave_negra"], [3], [None]))
        self.assertLessEqual(servicio.solicitudes_realizadas, 6)

    def test_sc005_g_sin_limite_las_demas_consultas_conservan_max_reintentos_429(self):
        cliente = ClienteCripta("http://falso/v1")
        respuestas = [R429] * (MAX_REINTENTOS_429 + 1)
        with mock.patch.object(cliente_http.requests, "get", side_effect=respuestas) as get, \
                mock.patch.object(cliente_http.time, "sleep") as dormir:
            with self.assertRaises(RuntimeError) as error:
                cliente.obtener_criptas()
        self.assertEqual(get.call_count, MAX_REINTENTOS_429 + 1)
        self.assertEqual(dormir.call_count, MAX_REINTENTOS_429)
        self.assertIn(f"tras {MAX_REINTENTOS_429} reintentos", str(error.exception))


if __name__ == "__main__":
    unittest.main()
