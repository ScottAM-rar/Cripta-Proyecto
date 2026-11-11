"""Capacidad 009, T051: la ayuda de tests_labs/sin_red.py bloquea requests.get y lo restaura al salir (SC-006)."""
import unittest
from unittest import mock

import requests

from tests_labs.sin_red import sin_red


class BloqueoDeRed(unittest.TestCase):

    def test_sc006_dentro_de_la_ayuda_requests_get_lanza_intento_de_red(self):
        original = requests.get
        with sin_red():
            self.assertIsNot(requests.get, original)
            with self.assertRaises(AssertionError) as error:
                requests.get("http://ejemplo.invalido/")
            self.assertEqual(str(error.exception), "intento de red")
        self.assertIs(requests.get, original)

    def test_sc006_restaura_requests_get_aunque_falle_lo_de_adentro(self):
        original = requests.get
        with self.assertRaises(ValueError):
            with sin_red():
                raise ValueError("una prueba que falla")
        self.assertIs(requests.get, original)

    def test_sc006_mock_patch_dentro_de_la_ayuda_sigue_funcionando(self):
        with sin_red():
            bloqueo = requests.get
            with mock.patch.object(requests, "get", return_value="respuesta falsa"):
                self.assertEqual(requests.get("http://ejemplo.invalido/"), "respuesta falsa")
            self.assertIs(requests.get, bloqueo)            # al salir del mock vuelve el bloqueo, no la red


if __name__ == "__main__":
    unittest.main()
