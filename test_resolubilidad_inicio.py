"""Capacidad 003, T043: verificación al iniciar una partida y `--forzar` (FR-313, FR-339, FR-340, FR-344; SC-005;
research.md §7, data-model.md §5).

Se usa EstadoJuegoServicio sobre ServicioCripta + API falsa v2. El log de la partida va a una carpeta temporal (el
servicio crea `AlmacenLogTexto(nombre, carpeta_temporal)`) y `AlmacenLogTexto.abrir` se espía para saber si se abrió el
registro de partida. Todo corre con requests.get bloqueado.

Incluye la aserción que el grupo F dejó pendiente (T040): con ClientePersistente, una partida nueva que arranca sobre la
versión v2 (la puerta de la salida pide una llave inexistente) no inicia sin `forzar`, aunque la verificación de la
versión v1 haya sido resoluble (`Inicio.test_fr339_cambio_de_version_la_partida_nueva_no_inicia_sin_forzar`)."""
import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

import requests

import Servicio.EstadoJuegoServicio as modulo_servicio
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from DTO.EventoDTO import EventoDTO
from Logica import VerificacionResolubilidad
from Logica.ReporteVerificacion import aviso_forzado
from Logica.VerificacionResolubilidad import CriptaNoResoluble
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from tests_labs.api_falsa import CASOS_APENDICE_B, HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_lineal
from tests_labs.referencia_resolubilidad import poner_puerta

CRIPTA = "cripta-01"
S = "itm_llave_salida"
NO_DISPONIBLE = "La verificación de resolubilidad no está disponible."


def caso(codigo: str):
    for cod, _descripcion, constructor in CASOS_APENDICE_B:
        if cod == codigo:
            return constructor()[0]
    raise AssertionError(f"CASOS_APENDICE_B no tiene el caso {codigo}")


class ConJuego(unittest.TestCase):

    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="cripta_003_inicio_")
        self.addCleanup(shutil.rmtree, self.raiz, True)
        self.carpeta_logs = os.path.join(self.raiz, "logs")
        carpeta_logs = self.carpeta_logs
        parches = [
            mock.patch.object(requests, "get", side_effect=AssertionError("intento de red")),
            mock.patch.object(modulo_servicio, "AlmacenLogTexto",
                              lambda nombre=None, carpeta=None: AlmacenLogTexto(nombre, carpeta_logs)),
        ]
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)
        espia = mock.patch.object(AlmacenLogTexto, "abrir", autospec=True, side_effect=AlmacenLogTexto.abrir)
        self.abrir = espia.start()
        self.addCleanup(espia.stop)

    def juego(self, http) -> EstadoJuegoServicio:
        servicio = ServicioCripta(http, CacheLRU(25))
        servicio.listar_criptas()
        return EstadoJuegoServicio(comunicacion=servicio)

    def juego_persistente(self, http) -> EstadoJuegoServicio:
        servicio = ServicioCripta(ClientePersistente(http, AlmacenDisco(os.path.join(self.raiz, "datos"))),
                                  CacheLRU(25))
        servicio.listar_criptas()
        return EstadoJuegoServicio(comunicacion=servicio)

    def iniciar(self, juego, **opciones):
        with contextlib.redirect_stdout(io.StringIO()):
            juego.iniciarJuego(CRIPTA, 1, **opciones)

    def archivos_de_log(self) -> list:
        return os.listdir(self.carpeta_logs) if os.path.isdir(self.carpeta_logs) else []


class Inicio(ConJuego):

    def test_fr339_no_resoluble_no_inicia_y_no_crea_log(self):
        juego = self.juego(caso("B-R1"))
        with self.assertRaises(CriptaNoResoluble) as contexto:
            self.iniciar(juego)
        self.assertIn("NO RESOLUBLE", str(contexto.exception))
        self.assertIs(contexto.exception.resultado.resoluble, False)
        self.assertFalse(juego._estadoJuegoLogica.iniciado)
        self.abrir.assert_not_called()
        self.assertEqual(self.archivos_de_log(), [])
        self.assertIsNone(juego.nombreLog())

    def test_fr339_resoluble_inicia_sin_aviso(self):
        juego = self.juego(caso("B-R3"))
        self.iniciar(juego)
        logica = juego._estadoJuegoLogica
        self.assertTrue(logica.iniciado)
        self.assertIsNotNone(logica.resultadoVerificacion, "iniciarJuego no verificó la cripta")
        self.assertIs(logica.resultadoVerificacion.resoluble, True)
        self.assertIsNone(juego.avisoResolubilidad())
        self.assertEqual(self.abrir.call_count, 1)

    def test_fr339_fr313_sin_llaves_sigue_con_aviso(self):
        juego = self.juego(HttpConfigurable(esqueleto_lineal([None]), sala_salida=2, fallo_llaves="sin_respuesta"))
        self.iniciar(juego)
        logica = juego._estadoJuegoLogica
        self.assertTrue(logica.iniciado)
        self.assertIsNotNone(juego.avisoLlaves())                 # el aviso de la 009 (FR-313)
        self.assertIsNone(logica.resultadoVerificacion)           # sin llaves no se verifica
        self.assertIsNone(juego.avisoResolubilidad())

    def test_fr339_h4_5_datos_invalidos_inicia_con_aviso(self):
        juego = self.juego(HttpConfigurable(esqueleto_lineal([None]), sala_salida=99, llaves=[(S, 1, None)],
                                            llave_salida=S))
        self.iniciar(juego)                                       # no lanza CriptaNoResoluble
        self.assertTrue(juego._estadoJuegoLogica.iniciado)
        aviso = juego.avisoResolubilidad()
        self.assertIsNotNone(aviso, "con datos inválidos la partida debe iniciar con aviso")
        self.assertIn("Datos inválidos", aviso)
        self.assertTrue(aviso.endswith(NO_DISPONIBLE), aviso)
        self.assertIsNone(juego._estadoJuegoLogica.resultadoVerificacion.resoluble)

    def test_fr339_replay_y_partida_cargada_no_verifican(self):
        # Reproducción: pedir_llaves=False no verifica, ni siquiera en una cripta no resoluble.
        juego = self.juego(caso("B-R4"))
        logica = juego._estadoJuegoLogica
        with contextlib.redirect_stdout(io.StringIO()):
            logica.iniciarJuego(CRIPTA, 1, pedir_llaves=False)
        self.assertTrue(logica.iniciado)
        self.assertIsNone(logica.resultadoVerificacion)
        self.assertIsNone(logica.avisoResolubilidad)
        # Partida cargada: restaurar no verifica y no arrastra el resultado ni el aviso de la partida anterior.
        otro = self.juego(caso("B-R1"))
        self.iniciar(otro, forzar=True)
        logica = otro._estadoJuegoLogica
        self.assertIsNotNone(logica.avisoResolubilidad, "la partida forzada debía tener aviso antes de restaurar")
        estado = logica.exportar_estado()
        logica.restaurar_estado(estado)
        self.assertIsNone(logica.resultadoVerificacion)
        self.assertIsNone(logica.avisoResolubilidad)

    def test_fr339_reintento_tras_no_resoluble(self):
        juego = self.juego(caso("B-R1"))
        with self.assertRaises(CriptaNoResoluble):
            self.iniciar(juego)
        self.iniciar(juego, forzar=True)                          # el mismo objeto puede iniciar después
        self.assertTrue(juego._estadoJuegoLogica.iniciado)
        self.assertEqual(self.abrir.call_count, 1)

    def test_fr339_cambio_de_version_la_partida_nueva_no_inicia_sin_forzar(self):
        v1 = HttpConfigurable(esqueleto_lineal([None]), sala_salida=2, llaves=[(S, 2, None)], llave_salida=S,
                              version_cripta="v1")
        self.assertIs(self.juego_persistente(v1).verificar(CRIPTA).resoluble, True)
        salas = esqueleto_lineal([None])
        poner_puerta(salas, 1, 2, "itm_llave_perdida")            # en v2 la puerta de la salida pide una llave inexistente

        def v2():
            return HttpConfigurable(salas, sala_salida=2, llaves=[(S, 2, None)], llave_salida=S, version_cripta="v2")
        juego = self.juego_persistente(v2())
        with self.assertRaises(CriptaNoResoluble):
            self.iniciar(juego)
        self.assertFalse(juego._estadoJuegoLogica.iniciado)
        forzado = self.juego_persistente(v2())
        self.iniciar(forzado, forzar=True)
        self.assertTrue(forzado._estadoJuegoLogica.iniciado)
        self.assertIsNotNone(forzado.avisoResolubilidad())


class Forzar(ConJuego):

    def test_fr340_forzar_inicia_con_aviso_solo_al_iniciar(self):
        juego = self.juego(caso("B-R1"))
        self.iniciar(juego, forzar=True)
        logica = juego._estadoJuegoLogica
        self.assertTrue(logica.iniciado)
        self.assertIsNotNone(logica.resultadoVerificacion, "iniciarJuego no verificó la cripta")
        aviso = juego.avisoResolubilidad()
        self.assertEqual(aviso, aviso_forzado(logica.resultadoVerificacion))
        # Una acción después: el aviso no entra a los mensajes de la partida ni al registro de partida.
        with contextlib.redirect_stdout(io.StringIO()):
            juego.obtenerSala(juego.getJudador().id_sala_actual)       # como el controlador: la sala inicial cargada
            juego.accionJugador(EventoDTO(tiempo_ejecucion=100, id_secuencia=0, actor=juego.getJudador(),
                                          tipo_accion="ESPERAR", datos_extra=[]))
        self.assertNotIn(aviso, juego.ultimosMensajes())
        archivos = self.archivos_de_log()
        self.assertEqual(len(archivos), 1)
        with open(os.path.join(self.carpeta_logs, archivos[0]), encoding="utf-8") as archivo:
            self.assertNotIn("AVISO", archivo.read())

    def test_fr340_forzar_sin_efecto_en_resoluble(self):
        normal = self.juego(caso("B-R3"))
        forzado = self.juego(caso("B-R3"))
        self.iniciar(normal)
        self.iniciar(forzado, forzar=True)
        self.assertIsNotNone(forzado._estadoJuegoLogica.resultadoVerificacion, "iniciarJuego no verificó la cripta")
        self.assertEqual(forzado._estadoJuegoLogica.resultadoVerificacion, normal._estadoJuegoLogica.resultadoVerificacion)
        self.assertIsNone(forzado.avisoResolubilidad())
        self.assertIsNone(normal.avisoResolubilidad())


class MismaOperacion(ConJuego):

    def test_fr344_inicio_y_verificar_dan_el_mismo_resultado(self):
        juego = self.juego(caso("B-R3"))
        with mock.patch.object(VerificacionResolubilidad, "verificar",
                               wraps=VerificacionResolubilidad.verificar) as espia:
            self.iniciar(juego)
        logica = juego._estadoJuegoLogica
        espia.assert_called_once()
        self.assertIs(espia.call_args.kwargs.get("llaves"), logica.llaves)   # reutiliza las llaves de la partida
        self.assertEqual(logica.resultadoVerificacion, self.juego(caso("B-R3")).verificar(CRIPTA))


if __name__ == "__main__":
    unittest.main()
