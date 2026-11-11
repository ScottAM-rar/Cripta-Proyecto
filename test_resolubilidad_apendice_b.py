"""Capacidad 003, T026: casos del Apéndice B de resolubilidad (B-R1 a B-R4) con CASOS_APENDICE_B.

Cada caso se busca por código, se arma un ServicioCripta sobre su HttpConfigurable y se ejecutan los pasos
("verificar",) del guion con la operación `verificar`, que se importa dentro de cada prueba con
`try/except ImportError: self.fail(...)`. El paso ("iniciar_sin_forzar",) de B-R4 lo ejecuta T044 (grupo G).
Todo corre con requests.get bloqueado."""
import importlib
import unittest
from unittest import mock

import requests

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from DTO.ResultadoVerificacionDTO import CICLO, LLAVE_INEXISTENTE, SALIDA_BLOQUEADA, BloqueoDTO, PasoLlaveDTO
from tests_labs.api_falsa import CASOS_APENDICE_B

CRIPTA = "cripta-01"
S = "itm_llave_salida"


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
            return constructor()
    raise AssertionError(f"CASOS_APENDICE_B no tiene el caso {codigo}")


class CasosB(unittest.TestCase):

    def verificaciones(self, codigo: str) -> list:
        """Ejecuta los pasos ("verificar",) del guion del caso y devuelve un resultado por paso."""
        try:
            modulo = importlib.import_module("Logica.VerificacionResolubilidad")
        except ImportError as error:
            self.fail(f"Logica.VerificacionResolubilidad todavía no existe: {error}")
        http, guion = caso(codigo)
        servicio = ServicioCripta(http, CacheLRU(25))
        servicio.listar_criptas()
        resultados = []
        for paso in guion:
            if paso[0] == "verificar":
                resultados.append(modulo.verificar(servicio, CRIPTA))
        self.assertTrue(resultados, f"el guion de {codigo} no tiene pasos de verificación")
        return resultados

    def test_b_r1_fr338_ciclo(self):
        r = self.verificaciones("B-R1")[0]
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.causas, [SALIDA_BLOQUEADA])
        self.assertEqual(r.bloqueos, [BloqueoDTO(1, "este", 2, S, [2], CICLO)])
        self.assertEqual(r.salas_alcanzables, [1])
        self.assertEqual(r.salas_no_alcanzables, 1)
        self.assertEqual(r.codigo_salida(), 1)

    def test_b_r2_fr334_llave_de_errante_en_su_sala_inicial(self):
        r = self.verificaciones("B-R2")[0]
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO(S, 3, "e-errante")])

    def test_b_r3_fr335_dos_ejecuciones_mismo_orden(self):
        resultados = self.verificaciones("B-R3")
        self.assertEqual(len(resultados), 2)
        primero, segundo = resultados
        self.assertIs(primero.resoluble, True)
        self.assertEqual(primero.orden, [PasoLlaveDTO("itm_llave_a", 2), PasoLlaveDTO("itm_llave_b", 3),
                                         PasoLlaveDTO(S, 5)])
        self.assertEqual(primero, segundo)

    def test_b_r4_fr338_llave_inexistente(self):
        # El guion de B-R4 solo tiene ("iniciar_sin_forzar",), que ejecuta T044: el bloqueo se comprueba con una
        # verificación directa sobre la misma cripta.
        r = self._verificar_directo("B-R4")
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.bloqueos, [BloqueoDTO(1, "este", 2, "itm_llave_perdida", [], LLAVE_INEXISTENTE)])

    def test_b_r4_fr339_no_inicia_sin_forzar(self):
        """T044 (grupo G): ejecuta el paso ("iniciar_sin_forzar",) del guion de B-R4 con EstadoJuegoServicio. El log va a
        una carpeta temporal y AlmacenLogTexto.abrir se espía: no debe abrirse el registro de partida."""
        import contextlib
        import io
        import os
        import shutil
        import tempfile
        import Servicio.EstadoJuegoServicio as modulo_servicio
        from adaptadores.AlmacenLogTexto import AlmacenLogTexto
        from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
        verificacion = importlib.import_module("Logica.VerificacionResolubilidad")

        carpeta_logs = os.path.join(tempfile.mkdtemp(prefix="cripta_003_b_r4_"), "logs")
        self.addCleanup(shutil.rmtree, os.path.dirname(carpeta_logs), True)
        http, guion = caso("B-R4")
        self.assertIn(("iniciar_sin_forzar",), guion)
        servicio = ServicioCripta(http, CacheLRU(25))
        servicio.listar_criptas()
        juego = EstadoJuegoServicio(comunicacion=servicio)
        with mock.patch.object(modulo_servicio, "AlmacenLogTexto",
                               lambda nombre=None, carpeta=None: AlmacenLogTexto(nombre, carpeta_logs)), \
                mock.patch.object(AlmacenLogTexto, "abrir", autospec=True, side_effect=AlmacenLogTexto.abrir) as abrir:
            for paso in guion:
                if paso[0] == "iniciar_sin_forzar":
                    with self.assertRaises(verificacion.CriptaNoResoluble) as contexto, \
                            contextlib.redirect_stdout(io.StringIO()):
                        juego.iniciarJuego(CRIPTA, 1)
        self.assertFalse(juego._estadoJuegoLogica.iniciado)
        abrir.assert_not_called()
        self.assertFalse(os.path.isdir(carpeta_logs) and os.listdir(carpeta_logs))
        self.assertIn("itm_llave_perdida", str(contexto.exception))         # el mensaje es el reporte

    def _verificar_directo(self, codigo: str):
        try:
            modulo = importlib.import_module("Logica.VerificacionResolubilidad")
        except ImportError as error:
            self.fail(f"Logica.VerificacionResolubilidad todavía no existe: {error}")
        http, _guion = caso(codigo)
        servicio = ServicioCripta(http, CacheLRU(25))
        servicio.listar_criptas()
        return modulo.verificar(servicio, CRIPTA)


if __name__ == "__main__":
    unittest.main()
