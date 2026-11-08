"""Capacidad 009, T046: las llaves de una partida cargada se piden bajo demanda (FR-325, FR-301, FR-313).

La partida guardada es un EstadoGuardadoDTO en memoria (exportar_estado / restaurar_estado): no se escriben archivos de
partida. Sin red: la cripta la arma HttpConfigurable y, cuando hace falta disco, ClientePersistente en una carpeta
temporal por prueba."""
import contextlib
import io
import os
import tempfile
import unittest

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.partida_prueba import jugar

SALAS = [{"id": 1, "nombre": "Entrada", "salidas": {"E": {"sala": 2}}},
         {"id": 2, "nombre": "Pasillo", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
         {"id": 3, "nombre": "Fondo", "salidas": {"O": {"sala": 2}}}]
CRIPTA = "cripta-01"
LLAVES = [("itm_llave_bronce", 2, None), ("itm_llave_negra", 3, None)]


class HttpDosCriptas(HttpConfigurable):
    """Dos criptas con el mismo esqueleto y llaves distintas: `llaves_por_cripta` es una lista de (id, tuplas)."""

    def __init__(self, llaves_por_cripta, **kwargs):
        super().__init__(SALAS, **kwargs)
        self.llaves_por_cripta = llaves_por_cripta

    def obtener_criptas(self):
        self.llamadas.append(("criptas", None))
        return [{"id": cid, "nombre": cid, "salas": len(SALAS), "dificultad": 1} for cid, _ in self.llaves_por_cripta]

    def obtener_llaves(self, cripta_id, solo_guardadas=False, limite_solicitudes=None):
        self.llaves = [llaves for cid, llaves in self.llaves_por_cripta if cid == cripta_id][0]
        return super().obtener_llaves(cripta_id, solo_guardadas, limite_solicitudes)


class HttpSinPresupuesto(HttpConfigurable):
    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["presupuesto_solicitudes"] = 0
        return datos


def servicio_en(carpeta, http):
    return ServicioCripta(ClientePersistente(http, AlmacenDisco(carpeta)), CacheLRU(25))


def jugar_y_exportar(servicio, cripta=CRIPTA):
    """Partida nueva con algunas acciones; devuelve (lógica, estado exportado)."""
    logica = EstadoJuegoLogica(comunicacion=servicio)
    with contextlib.redirect_stdout(io.StringIO()):
        logica.iniciarJuego(cripta, 1)
        logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
    jugar(logica, "ESPERAR")
    jugar(logica, "ESPERAR")
    return logica, logica.exportar_estado()


def cargar(servicio, estado, logica=None):
    logica = logica or EstadoJuegoLogica(comunicacion=servicio)
    logica.comunicacion = servicio
    with contextlib.redirect_stdout(io.StringIO()):
        logica.restaurar_estado(estado)
    return logica


class ConCarpeta(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.raiz = tmp.name
        self.carpeta = os.path.join(tmp.name, "datos_cripta")


class CargarNoPide(ConCarpeta):

    def test_fr325_a_cargar_no_hace_solicitudes_y_deja_llaves_y_aviso_en_none(self):
        http = HttpConfigurable(SALAS, llaves=LLAVES)
        servicio = servicio_en(self.carpeta, http)
        _, estado = jugar_y_exportar(servicio)
        antes = list(http.llamadas)
        cargada = cargar(servicio, estado)
        self.assertEqual(http.llamadas, antes)
        self.assertIsNone(cargada.llaves)
        self.assertIsNone(cargada.avisoLlaves)

        # En frío (servicio nuevo, misma carpeta) la restauración sí consulta lo básico de la cripta, pero nunca las llaves.
        # Medido el 2026-11-07: [('criptas', None), ('datos', 'cripta-01')].
        frio = HttpConfigurable(SALAS, llaves=LLAVES)
        cargar(servicio_en(self.carpeta, frio), estado)
        self.assertEqual(frio.veces("llaves"), 0)


class LlavesGuardadas(ConCarpeta):

    def test_fr325_b_h2_4_con_llaves_guardadas_de_la_misma_version_cero_solicitudes(self):
        jugada, estado = jugar_y_exportar(servicio_en(self.carpeta, HttpConfigurable(SALAS, llaves=LLAVES)))
        self.assertIsNotNone(AlmacenDisco(self.carpeta).leer_llaves(CRIPTA))

        http = HttpConfigurable(SALAS, llaves=LLAVES)
        cargada = cargar(servicio_en(self.carpeta, http), estado)
        llaves = cargada.obtenerLlaves()
        self.assertEqual(http.veces("llaves"), 0)
        self.assertEqual((llaves.ids, llaves.salas, llaves.enemigos),
                         (jugada.llaves.ids, jugada.llaves.salas, jugada.llaves.enemigos))


class SinLlavesGuardadas(ConCarpeta):

    def test_fr325_c_h2_5_sin_llaves_guardadas_la_primera_pide_una_vez_y_la_segunda_ninguna(self):
        # La partida se jugó sin disco: la carpeta de la carga no tiene llaves.
        _, estado = jugar_y_exportar(ServicioCripta(HttpConfigurable(SALAS, llaves=LLAVES), CacheLRU(25)))
        http = HttpConfigurable(SALAS, llaves=LLAVES)
        cargada = cargar(servicio_en(self.carpeta, http), estado)
        self.assertEqual(http.veces("llaves"), 0)
        primera = cargada.obtenerLlaves()
        self.assertEqual(http.veces("llaves"), 1)
        segunda = cargada.obtenerLlaves()
        self.assertEqual(http.veces("llaves"), 1)
        self.assertIs(segunda, primera)
        self.assertEqual(primera.ids, ["itm_llave_bronce", "itm_llave_negra"])


class SinLlavesYSinPoderPedirlas(ConCarpeta):

    def comprobar_aviso_y_partida_sigue(self, cargada):
        self.assertIsNone(cargada.obtenerLlaves())
        self.assertIn(CRIPTA, cargada.avisoLlaves)
        tiempo = cargada.estadoJuego.reloj.tiempo_actual
        jugar(cargada, "ESPERAR")                       # la partida sigue: se puede ejecutar una acción
        self.assertGreater(cargada.estadoJuego.reloj.tiempo_actual, tiempo)

    def test_fr313_fr325_d_h2_6_sin_presupuesto_no_pide_y_avisa(self):
        _, estado = jugar_y_exportar(ServicioCripta(HttpConfigurable(SALAS, llaves=LLAVES), CacheLRU(25)))
        http = HttpSinPresupuesto(SALAS, llaves=LLAVES)
        cargada = cargar(servicio_en(self.carpeta, http), estado)
        self.comprobar_aviso_y_partida_sigue(cargada)
        self.assertEqual(http.veces("llaves"), 0)

    def test_fr313_fr325_d_h2_6_sin_respuesta_avisa_y_la_partida_sigue(self):
        _, estado = jugar_y_exportar(ServicioCripta(HttpConfigurable(SALAS, llaves=LLAVES), CacheLRU(25)))
        http = HttpConfigurable(SALAS, llaves=LLAVES, fallo_llaves="sin_respuesta")
        cargada = cargar(servicio_en(self.carpeta, http), estado)
        self.comprobar_aviso_y_partida_sigue(cargada)
        self.assertEqual(http.veces("llaves"), 1)


class OtraCripta(ConCarpeta):

    def test_fr325_e_restaurar_otra_cripta_no_arrastra_las_llaves_anteriores(self):
        llaves_a = [("itm_llave_a", 2, None)]
        llaves_b = [("itm_llave_b", 3, None)]
        http = HttpDosCriptas([("cripta-A", llaves_a), ("cripta-B", llaves_b)])
        servicio = servicio_en(self.carpeta, http)
        _, estado_b = jugar_y_exportar(servicio, "cripta-B")

        logica = EstadoJuegoLogica(comunicacion=servicio)
        with contextlib.redirect_stdout(io.StringIO()):
            logica.iniciarJuego("cripta-A", 1)
        self.assertEqual(logica.llaves.ids, ["itm_llave_a"])

        cargar(servicio, estado_b, logica)               # sobre la MISMA lógica, que ya tenía las llaves de A
        self.assertEqual(logica.idCripta, "cripta-B")
        self.assertIsNone(logica.llaves)
        self.assertIsNone(logica.avisoLlaves)
        llaves = logica.obtenerLlaves()
        self.assertEqual((llaves.cripta_id, llaves.ids), ("cripta-B", ["itm_llave_b"]))


class Reproduccion(ConCarpeta):
    """T058 (pedido de la capacidad 007): una reproducción no es una partida nueva y no pide las llaves."""

    def log_de_una_partida(self):
        """Juega una partida corta en su propia carpeta y devuelve (log, acciones del log, resultados de las acciones)."""
        servicio = servicio_en(os.path.join(self.raiz, "original"), HttpConfigurable(SALAS, llaves=LLAVES))
        logica, _ = jugar_y_exportar(servicio)
        log = logica.exportar_log()
        return log, list(log.acciones)

    def reproducir(self, log, carpeta):
        http = HttpConfigurable(SALAS, llaves=LLAVES)
        logica = EstadoJuegoLogica(comunicacion=servicio_en(carpeta, http))
        with contextlib.redirect_stdout(io.StringIO()):
            resultados = logica.repetirPartida(log)
        return http, logica, resultados

    def test_fr325_t058_a_reproducir_en_carpeta_vacia_no_pide_llaves_ni_avisa(self):
        log, acciones = self.log_de_una_partida()
        http, logica, resultados = self.reproducir(log, self.carpeta)
        self.assertEqual(http.veces("llaves"), 0)
        self.assertIsNone(logica.llaves)
        self.assertIsNone(logica.avisoLlaves)
        self.assertEqual(len(resultados), len(acciones))                    # la reproducción sigue siendo fiel
        self.assertEqual(list(logica.exportar_log().acciones), acciones)    # y el log no cambia

    def test_fr301_fr325_t058_b_tras_reproducir_las_llaves_se_piden_bajo_demanda_una_vez(self):
        log, _ = self.log_de_una_partida()
        http, logica, _ = self.reproducir(log, self.carpeta)
        primera = logica.obtenerLlaves()
        self.assertEqual(http.veces("llaves"), 1)
        self.assertIs(logica.obtenerLlaves(), primera)
        self.assertEqual(http.veces("llaves"), 1)
        # Una partida nueva de la misma cripta, en una carpeta vacía, sigue haciendo su consulta la primera vez.
        http_nueva = HttpConfigurable(SALAS, llaves=LLAVES)
        jugar_y_exportar(servicio_en(os.path.join(self.raiz, "nueva"), http_nueva))
        self.assertEqual(http_nueva.veces("llaves"), 1)

    def test_fr301_t058_c_una_partida_nueva_sigue_pidiendo_las_llaves_al_iniciar(self):
        http = HttpConfigurable(SALAS, llaves=LLAVES)
        logica = EstadoJuegoLogica(comunicacion=servicio_en(self.carpeta, http))
        with contextlib.redirect_stdout(io.StringIO()):
            logica.iniciarJuego(CRIPTA, 1)
        self.assertEqual(http.veces("llaves"), 1)
        self.assertEqual(logica.llaves.ids, ["itm_llave_bronce", "itm_llave_negra"])


class LogicaNueva(unittest.TestCase):

    def test_fr325_f_logica_recien_creada_sin_llaves_ni_aviso(self):
        logica = EstadoJuegoLogica()
        self.assertIsNone(logica.llaves)
        self.assertIsNone(logica.avisoLlaves)


if __name__ == "__main__":
    unittest.main()
