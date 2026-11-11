"""Capacidad 009, T020 (y la parte (g) de T021): fallos claros de la consulta de llaves; nada inválido se guarda y la
partida sigue (FR-309 a FR-313).

Sin red: las criptas se guardan con la API falsa por el flujo normal (ServicioCripta sobre ClientePersistente) en una
carpeta temporal por prueba, y el modo sin red se arma con crear_servicio(offline=True, carpeta=...)."""
import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import Servicio.EstadoJuegoServicio as modulo_servicio
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.fabrica import crear_servicio
from adaptadores.servicioCripta import ServicioCripta
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.FuenteCripta import LlavesNoDisponibles
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from tests_labs.api_falsa import HttpConfigurable

CRIPTA = "cripta-01"
SALAS = [{"id": i, "nombre": f"Sala {i}",
          "salidas": ({"O": {"sala": i - 1}} if i > 1 else {}) | ({"E": {"sala": i + 1}} if i < 5 else {})}
         for i in range(1, 6)]
ENEMIGOS = [(3, "e-301", "ent_guardian_oseo", 15)]
LLAVES_BUENAS = [("itm_llave_bronce", 2, None), ("itm_llave_negra", 3, "e-301")]


class ConCarpeta(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.raiz = tmp.name
        self.carpeta = os.path.join(tmp.name, "datos_cripta")

    def ejecucion(self, llaves=None, fallo_llaves=None):
        http = HttpConfigurable(SALAS, ENEMIGOS, llaves=LLAVES_BUENAS if llaves is None else llaves,
                                fallo_llaves=fallo_llaves)
        almacen = AlmacenDisco(self.carpeta)
        return http, almacen, ServicioCripta(ClientePersistente(http, almacen), CacheLRU(25))

    def guardar_cripta(self, con_llaves):
        """Deja la cripta completa en disco por el flujo normal; con o sin la clave llaves."""
        _, almacen, servicio = self.ejecucion()
        servicio.listar_criptas()
        servicio.crear_jugador(CRIPTA)
        servicio.construir_todas(CRIPTA)
        if con_llaves:
            servicio.ubicacion_llaves(CRIPTA)
        self.assertEqual(almacen.leer_llaves(CRIPTA) is not None, con_llaves)

    def partida_offline(self):
        logica = EstadoJuegoLogica(comunicacion=crear_servicio(offline=True, carpeta=self.carpeta))
        with contextlib.redirect_stdout(io.StringIO()):
            logica.iniciarJuego(CRIPTA, 1)
        return logica


class SinRespuesta(ConCarpeta):

    def test_fr309_fr310_a_h3_1_sin_respuesta_avisa_con_la_cripta_y_no_guarda(self):
        http, almacen, servicio = self.ejecucion(fallo_llaves="sin_respuesta")
        with self.assertRaises(LlavesNoDisponibles) as error:
            servicio.ubicacion_llaves(CRIPTA)
        self.assertIn(CRIPTA, str(error.exception))
        self.assertEqual(http.veces("llaves"), 1)
        self.assertIsNone(almacen.leer_llaves(CRIPTA))


class HttpSinPresupuesto(HttpConfigurable):
    """Datos generales con presupuesto_solicitudes en 0: nunca queda presupuesto para la consulta de llaves."""

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["presupuesto_solicitudes"] = 0
        return datos


class AvisoUniforme(ConCarpeta):
    """T055: sin presupuesto el aviso tiene la misma forma que los demás fallos (FR-313, FR-309)."""

    def test_fr313_fr309_t055_sin_presupuesto_el_aviso_nombra_la_cripta_el_motivo_y_la_verificacion(self):
        http = HttpSinPresupuesto(SALAS, ENEMIGOS, llaves=LLAVES_BUENAS)
        servicio = ServicioCripta(ClientePersistente(http, AlmacenDisco(self.carpeta)), CacheLRU(25))
        with self.assertRaises(LlavesNoDisponibles) as error:
            servicio.ubicacion_llaves(CRIPTA)
        mensaje = str(error.exception)
        self.assertEqual(http.veces("llaves"), 0)
        self.assertTrue(mensaje.startswith("No se pudieron obtener las llaves"), mensaje)
        self.assertEqual(mensaje.count(CRIPTA), 1, mensaje)                 # la cripta, una sola vez
        self.assertIn("sin presupuesto", mensaje)                           # el motivo
        self.assertTrue(mensaje.endswith("La verificación de resolubilidad no está disponible."), mensaje)
        self.assertNotIn("..", mensaje)


class RespuestaInvalida(ConCarpeta):

    def test_fr310_fr311_b_h3_2_respuestas_invalidas_avisan_y_no_guardan_nada(self):
        casos = (("sala inexistente", [("itm_llave_bronce", 99, None)], False),
                 ("entrada idéntica repetida", [("itm_llave_bronce", 2, None), ("itm_llave_bronce", 2, None)], False),
                 ("enemigo ausente del contenido guardado", [("itm_llave_negra", 3, "e-999")], True))
        for nombre, llaves, precargar_sala in casos:
            with self.subTest(caso=nombre):
                self.carpeta = os.path.join(self.raiz, nombre.replace(" ", "_"))
                http, almacen, servicio = self.ejecucion(llaves=llaves)
                if precargar_sala:
                    servicio.construir_sala(CRIPTA, 3)
                    self.assertIsNotNone(almacen.leer_contenido(CRIPTA, 3))
                with self.assertRaises(LlavesNoDisponibles) as error:
                    servicio.ubicacion_llaves(CRIPTA)
                self.assertIn(CRIPTA, str(error.exception))
                self.assertEqual(http.veces("llaves"), 1)
                self.assertIsNone(almacen.leer_llaves(CRIPTA))


class ModoSinRed(ConCarpeta):

    def test_fr312_fr313_c_h3_3_offline_sin_llaves_la_partida_sigue_con_aviso(self):
        self.guardar_cripta(con_llaves=False)
        logica = self.partida_offline()
        self.assertTrue(logica.iniciado)
        self.assertIsNone(logica.llaves)
        self.assertIn(CRIPTA, logica.avisoLlaves)
        self.assertEqual(logica.comunicacion.solicitudes_realizadas, 0)

    def test_fr312_d_h3_4_offline_con_llaves_las_entrega_sin_solicitudes(self):
        self.guardar_cripta(con_llaves=True)
        logica = self.partida_offline()
        self.assertIsNotNone(logica.llaves)
        self.assertEqual(logica.llaves.ids, ["itm_llave_bronce", "itm_llave_negra"])
        self.assertIsNone(logica.avisoLlaves)
        self.assertEqual(logica.comunicacion.solicitudes_realizadas, 0)


class FalloNoMemorizado(ConCarpeta):

    def test_fr309_e_tras_un_fallo_la_segunda_llamada_vuelve_a_intentar(self):
        http, almacen, servicio = self.ejecucion(fallo_llaves="sin_respuesta")
        with self.assertRaises(LlavesNoDisponibles):
            servicio.ubicacion_llaves(CRIPTA)
        http.fallo_llaves = None                      # el servicio vuelve a responder
        dto = servicio.ubicacion_llaves(CRIPTA)
        self.assertEqual(http.veces("llaves"), 2)
        self.assertEqual(dto.ids, ["itm_llave_bronce", "itm_llave_negra"])
        self.assertIsNotNone(almacen.leer_llaves(CRIPTA))

    def test_fr313_e_la_logica_tampoco_memoriza_el_fallo(self):
        http, _, servicio = self.ejecucion(fallo_llaves="sin_respuesta")
        logica = EstadoJuegoLogica(comunicacion=servicio)
        with contextlib.redirect_stdout(io.StringIO()):
            logica.iniciarJuego(CRIPTA, 1)
        self.assertIsNone(logica.llaves)
        self.assertIn(CRIPTA, logica.avisoLlaves)
        http.fallo_llaves = None
        self.assertIsNotNone(logica.obtenerLlaves())
        self.assertIsNone(logica.avisoLlaves)
        self.assertEqual(http.veces("llaves"), 2)


class TemporalSobrante(ConCarpeta):

    def test_fr310_f_un_tmp_sobrante_se_ignora_y_las_llaves_se_guardan(self):
        self.guardar_cripta(con_llaves=False)
        ruta_bin = os.path.join(self.carpeta, f"cripta_{CRIPTA}.bin")
        ruta_tmp = ruta_bin + ".tmp"                  # el temporal de ArchivoIndexado._escribir_todo
        with open(ruta_tmp, "wb") as archivo:
            archivo.write(b"CRIX corte a mitad de una escritura anterior")
        datos_antes = AlmacenDisco(self.carpeta).leer_datos(CRIPTA)

        http, almacen, servicio = self.ejecucion()
        dto = servicio.ubicacion_llaves(CRIPTA)
        self.assertEqual(http.veces("llaves"), 1)
        self.assertEqual(http.veces("salas") + http.veces("contenido"), 0)      # lo demás salió del .bin válido
        self.assertEqual(almacen.leer_datos(CRIPTA), datos_antes)
        self.assertEqual(dto.ids, ["itm_llave_bronce", "itm_llave_negra"])
        self.assertIsNotNone(almacen.leer_llaves(CRIPTA))


# (g) T021: el aviso llega a la capa de servicio, que es la que usa el controlador.
class AvisoEnElServicio(ConCarpeta):

    def servicio_offline(self):
        carpeta_logs = os.path.join(self.raiz, "logs")
        parche = mock.patch.object(modulo_servicio, "AlmacenLogTexto",
                                   lambda nombre=None, carpeta=None: AlmacenLogTexto(nombre, carpeta_logs))
        parche.start()
        self.addCleanup(parche.stop)
        return EstadoJuegoServicio(comunicacion=crear_servicio(offline=True, carpeta=self.carpeta), offline=True)

    def test_fr313_g_aviso_llaves_none_antes_de_iniciar_y_con_la_cripta_si_faltan(self):
        self.guardar_cripta(con_llaves=False)
        servicio = self.servicio_offline()
        self.assertIsNone(servicio.avisoLlaves())
        with contextlib.redirect_stdout(io.StringIO()):
            servicio.iniciarJuego(CRIPTA, 1)
        self.assertIn(CRIPTA, servicio.avisoLlaves())

    def test_fr313_g_aviso_llaves_none_si_hay_llaves(self):
        self.guardar_cripta(con_llaves=True)
        servicio = self.servicio_offline()
        with contextlib.redirect_stdout(io.StringIO()):
            servicio.iniciarJuego(CRIPTA, 1)
        self.assertIsNone(servicio.avisoLlaves())


if __name__ == "__main__":
    unittest.main()
