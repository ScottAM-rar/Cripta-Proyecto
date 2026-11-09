"""Capacidad 003, T038: datos y solicitudes de la verificación (FR-333, FR-339, FR-341, FR-343; SC-003, SC-004).

- `Solicitudes`: con las llaves guardadas la verificación no pide llaves, salas ni contenido; sin ellas, solo la
  consulta de llaves de la 009; nunca pide contenido.
- `ErroresDeDatos`: sin datos no hay resultado inventado: `resoluble is None`, código 2 y un motivo que nombra la cripta.
- `CasosLimite`: casos límite de spec.md que no tenían prueba.
La prueba de que el inicio de partida reutiliza las llaves (T045) se agrega en el grupo G.

Todo corre con requests.get bloqueado."""
import shutil
import tempfile
import unittest
from unittest import mock

import requests

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from Logica.VerificacionResolubilidad import verificar, verificar_resolubilidad
from tests_labs.api_falsa import CASOS_APENDICE_B, HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_lineal
from tests_labs.referencia_resolubilidad import mapa_desde_salas, poner_puerta, ubicaciones

CRIPTA = "cripta-01"
S = "itm_llave_salida"
ARRANQUE = [("criptas", None), ("datos", CRIPTA)]       # lo que pide cualquier sesión nueva (Parte I: lista y versión)


def _sin_red(*args, **kwargs):
    raise AssertionError("intento de red")


_parche_red = mock.patch.object(requests, "get", side_effect=_sin_red)


def setUpModule():
    _parche_red.start()


def tearDownModule():
    _parche_red.stop()


def caso(codigo: str):
    for cod, _descripcion, constructor in CASOS_APENDICE_B:
        if cod == codigo:
            return constructor()[0]
    raise AssertionError(f"CASOS_APENDICE_B no tiene el caso {codigo}")


def servicio_directo(http):
    servicio = ServicioCripta(http, CacheLRU(25))
    servicio.listar_criptas()
    return servicio


def nombres(llamadas, nombre):
    return [llamada for llamada in llamadas if llamada[0] == nombre]


class HttpSinDatoGeneral(HttpConfigurable):
    """API falsa v2 cuyos datos generales no traen el campo `falta` (T065: «sala_inicial» o «sala_salida»).
    Subclase de la prueba: tests_labs/api_falsa.py no cambia."""

    def __init__(self, falta: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.falta = falta

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        del datos[self.falta]
        return datos


def sin_dato_general(falta: str) -> HttpSinDatoGeneral:
    """Pasillo 1-2 abierto con la llave de salida en la sala 1: resoluble si el dato estuviera."""
    return HttpSinDatoGeneral(falta, esqueleto_lineal([None]), sala_salida=2, llaves=[(S, 1, None)], llave_salida=S)


class ConCarpeta(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="cripta_003_datos_")

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def persistente(self, http):
        servicio = ServicioCripta(ClientePersistente(http, AlmacenDisco(self.carpeta)), CacheLRU(25))
        servicio.listar_criptas()
        return servicio


class Solicitudes(ConCarpeta):

    def test_fr341_llaves_guardadas_cero_solicitudes(self):
        primera = self.persistente(caso("B-R3"))
        self.assertIs(verificar(primera, CRIPTA).resoluble, True)       # guarda esqueleto y llaves
        http = caso("B-R3")
        segunda = self.persistente(http)
        resultado = verificar(segunda, CRIPTA)
        self.assertIs(resultado.resoluble, True)
        # La sesión nueva solo hace el arranque de la Parte I (lista de criptas y datos generales con la versión);
        # la verificación no agrega ninguna solicitud de llaves, salas ni contenido (FR-341, SC-003).
        self.assertEqual(http.llamadas, ARRANQUE)
        self.assertEqual(segunda.solicitudes_realizadas, len(ARRANQUE))

    def test_fr341_sin_llaves_solo_la_consulta_de_la_009(self):
        http = caso("B-R3")
        servicio = self.persistente(http)
        antes = len(http.llamadas)
        verificar(servicio, CRIPTA)
        nuevas = http.llamadas[antes:]
        self.assertEqual(nombres(nuevas, "llaves"), [("llaves", CRIPTA)])
        self.assertEqual(nombres(nuevas, "contenido"), [])
        self.assertEqual([n for n, _ in nuevas], ["datos", "salas", "llaves"])   # mapa y datos: lo existente

    def test_fr341_inicio_reutiliza_las_llaves_de_la_partida(self):
        """T045 (grupo G): una partida nueva hace una sola consulta de llaves en total y la verificación al iniciar no
        vuelve a pedir la ubicación de las llaves (usa las que ya pidió la partida)."""
        import contextlib
        import io
        import os
        import Servicio.EstadoJuegoServicio as modulo_servicio
        from adaptadores.AlmacenLogTexto import AlmacenLogTexto
        from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
        carpeta_logs = os.path.join(self.carpeta, "logs")
        http = caso("B-R3")
        servicio = servicio_directo(http)
        juego = EstadoJuegoServicio(comunicacion=servicio)
        with mock.patch.object(modulo_servicio, "AlmacenLogTexto",
                               lambda nombre=None, carpeta=None: AlmacenLogTexto(nombre, carpeta_logs)), \
                mock.patch.object(ServicioCripta, "ubicacion_llaves", autospec=True,
                                  side_effect=ServicioCripta.ubicacion_llaves) as ubicacion, \
                contextlib.redirect_stdout(io.StringIO()):
            juego.iniciarJuego(CRIPTA, 1)
        self.assertTrue(juego._estadoJuegoLogica.iniciado)
        self.assertEqual(nombres(http.llamadas, "llaves"), [("llaves", CRIPTA)])
        self.assertEqual(ubicacion.call_count, 1)

    def test_fr341_nunca_pide_contenido(self):
        for codigo in ("B-R1", "B-R2", "B-R3", "B-R4"):
            http = caso(codigo)
            verificar(servicio_directo(http), CRIPTA)
            self.assertEqual(nombres(http.llamadas, "contenido"), [], codigo)


class ErroresDeDatos(ConCarpeta):

    def assertErrorDeDatos(self, resultado, *fragmentos):
        self.assertIsNone(resultado.resoluble)
        self.assertEqual(resultado.codigo_salida(), 2)
        self.assertEqual((resultado.orden, resultado.salas_alcanzables, resultado.bloqueos, resultado.causas),
                         ([], [], [], []))
        for fragmento in fragmentos:
            self.assertIn(fragmento, resultado.motivo_error)

    def test_fr343_servicio_sin_respuesta(self):
        http = HttpConfigurable(esqueleto_lineal([None]), sala_salida=2, fallo_llaves="sin_respuesta")
        self.assertErrorDeDatos(verificar(servicio_directo(http), CRIPTA), CRIPTA)

    def test_fr343_offline_sin_llaves_sin_solicitudes(self):
        servicio = self.persistente(caso("B-R3"))
        servicio.crear_jugador(CRIPTA)
        servicio.construir_todas(CRIPTA)                       # todo guardado menos las llaves
        offline = ServicioCripta(ClienteOffline(AlmacenDisco(self.carpeta)), CacheLRU(25))
        offline.listar_criptas()
        self.assertErrorDeDatos(verificar(offline, CRIPTA), CRIPTA)
        self.assertEqual(offline.solicitudes_realizadas, 0)

    def test_fr343_cripta_inexistente(self):
        self.assertErrorDeDatos(verificar(servicio_directo(caso("B-R3")), "cripta-99"), "cripta-99", "no existe")

    def test_fr343_h4_5_sala_de_salida_inexistente(self):
        http = HttpConfigurable(esqueleto_lineal([None]), sala_salida=99, llaves=[(S, 1, None)], llave_salida=S)
        self.assertErrorDeDatos(verificar(servicio_directo(http), CRIPTA), CRIPTA, "Datos inválidos", "99")

    def test_fr343_t065_datos_generales_sin_sala_inicial_ni_sala_salida(self):
        # Antes lanzaba KeyError desde ServicioCripta.obtener_sala_inicial / obtener_sala_salida.
        for falta in ("sala_inicial", "sala_salida"):
            with self.subTest(falta=falta):
                try:
                    resultado = verificar(servicio_directo(sin_dato_general(falta)), CRIPTA)
                except KeyError as error:
                    self.fail(f"verificar lanzó KeyError({error}) en vez de devolver un error de datos")
                self.assertErrorDeDatos(resultado, CRIPTA, "Datos inválidos", f"«{falta}»")

    def test_fr339_h4_5_t065_sin_sala_salida_la_partida_inicia_con_aviso(self):
        # Sin «sala_inicial» la partida no puede ubicar al jugador (crear_jugador, Parte I), así que solo se
        # comprueba el inicio sin «sala_salida».
        RetrocesoLogica().reiniciar()
        logica = EstadoJuegoLogica(comunicacion=servicio_directo(sin_dato_general("sala_salida")))
        try:
            logica.iniciarJuego(CRIPTA, 1)
        except KeyError as error:
            self.fail(f"iniciarJuego lanzó KeyError({error}) en vez de iniciar con aviso")
        self.assertTrue(logica.iniciado)
        self.assertIsNone(logica.resultadoVerificacion.resoluble)
        self.assertIn("«sala_salida»", logica.avisoResolubilidad)
        self.assertTrue(logica.avisoResolubilidad.endswith("La verificación de resolubilidad no está disponible."),
                        logica.avisoResolubilidad)


class CasosLimite(ConCarpeta):

    def test_fr333_salida_a_sala_inexistente_se_ignora(self):
        def cripta(con_salida_rota: bool):
            salas = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (2, 3, 100, "E", "O")])
            poner_puerta(salas, 2, 3, None)
            if con_salida_rota:
                salas[0]["salidas"]["N"] = {"sala": 99}            # id sin sala
                salas[1]["salidas"]["S"] = {"sala": 77, "cerrada": True, "llave": "itm_k"}
            return mapa_desde_salas(salas)
        llaves = ubicaciones(CRIPTA, [(S, 2, None)])
        for salida in (2, 3):                                       # resoluble y no resoluble
            sin = verificar_resolubilidad(cripta(False), 1, salida, S, llaves, CRIPTA)
            con = verificar_resolubilidad(cripta(True), 1, salida, S, llaves, CRIPTA)
            self.assertIsNotNone(con.resoluble)
            self.assertNotIn(99, con.salas_alcanzables)
            self.assertEqual(con, sin, f"salida {salida}")

    def test_fr343_ubicacion_de_llave_en_sala_inexistente_es_error_de_datos(self):
        http = HttpConfigurable(esqueleto_lineal([None]), sala_salida=2, llaves=[(S, 99, None)], llave_salida=S)
        resultado = verificar(servicio_directo(http), CRIPTA)
        self.assertIsNone(resultado.resoluble)
        self.assertEqual(resultado.codigo_salida(), 2)
        self.assertIn(CRIPTA, resultado.motivo_error)

    def test_fr339_cambio_de_version_entre_verificar_y_la_partida(self):
        # v1: pasillo 1-2 abierto, resoluble.
        v1 = HttpConfigurable(esqueleto_lineal([None]), sala_salida=2, llaves=[(S, 2, None)], llave_salida=S,
                              version_cripta="v1")
        self.assertIs(verificar(self.persistente(v1), CRIPTA).resoluble, True)
        # v2: la puerta 1-2 pide una llave que no existe. La sesión siguiente invalida lo guardado (validación de
        # versión existente) y la verificación usa los datos vigentes, no los de v1.
        salas = esqueleto_lineal([None])
        poner_puerta(salas, 1, 2, "itm_llave_perdida")
        v2 = HttpConfigurable(salas, sala_salida=2, llaves=[(S, 2, None)], llave_salida=S, version_cripta="v2")
        resultado = verificar(self.persistente(v2), CRIPTA)
        self.assertIs(resultado.resoluble, False)
        self.assertEqual(resultado.bloqueos[0].llave, "itm_llave_perdida")
        self.assertEqual(nombres(v2.llamadas, "llaves"), [("llaves", CRIPTA)])   # se volvió a consultar con v2


if __name__ == "__main__":
    unittest.main()
