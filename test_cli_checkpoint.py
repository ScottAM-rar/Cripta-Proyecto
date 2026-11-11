"""Pruebas de validación en CLI para la bandera --checkpoint-cada K.
FR-414, FR-415, FR-416, FR-417, SC-006.
"""
from __future__ import annotations
import io
import sys
import unittest
from unittest.mock import patch

from main import leer_argumentos, main


class TestCLICheckpoint(unittest.TestCase):
    def test_k_valido_parseo(self):
        """FR-414: Acepta --checkpoint-cada con un entero válido."""
        args = leer_argumentos(["--checkpoint-cada", "10"])
        self.assertEqual(args.checkpoint_cada, 10)

    def test_k_minimo_uno(self):
        """FR-414, FR-415: Acepta K=1 como el mínimo permitido."""
        args = leer_argumentos(["--checkpoint-cada", "1"])
        self.assertEqual(args.checkpoint_cada, 1)

    def test_k_por_defecto_cuando_no_se_indica(self):
        """FR-416: Si no se indica la bandera, se inicia con valor por defecto."""
        args = leer_argumentos([])
        # Puede ser None en args o el valor por defecto directamente
        self.assertIn(getattr(args, "checkpoint_cada", None), (None, 10))

    def test_k_cero_rechazado_codigo_2(self):
        """FR-417: K=0 se rechaza con código 2 sin iniciar."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as cm:
                leer_argumentos(["--checkpoint-cada", "0"])
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("mayor o igual que 1", stderr.getvalue())

    def test_k_negativo_rechazado_codigo_2(self):
        """FR-417: K negativo se rechaza con código 2 sin iniciar."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as cm:
                leer_argumentos(["--checkpoint-cada", "-5"])
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("mayor o igual que 1", stderr.getvalue())

    def test_k_decimal_rechazado_codigo_2(self):
        """FR-417: K decimal se rechaza con código 2 sin iniciar."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as cm:
                leer_argumentos(["--checkpoint-cada", "2.5"])
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("no es un número entero", stderr.getvalue())

    def test_k_no_numerico_rechazado_codigo_2(self):
        """FR-417: K no numérico se rechaza con código 2 sin iniciar."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as cm:
                leer_argumentos(["--checkpoint-cada", "abc"])
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("no es un número entero", stderr.getvalue())

    def test_k_vigente_en_servicio(self):
        """FR-416, SC-006: El servicio expone k_checkpoint para ser informado al jugador."""
        from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
        srv = EstadoJuegoServicio(k_checkpoint=5)
        self.assertEqual(srv.k_checkpoint, 5)
        srv_default = EstadoJuegoServicio()
        self.assertGreaterEqual(srv_default.k_checkpoint, 1)


if __name__ == "__main__":
    unittest.main()

