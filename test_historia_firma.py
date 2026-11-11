"""Pruebas de la firma y validaciones de consultarHistoria (capacidad 004)."""
from __future__ import annotations
import tempfile
import unittest

from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from bench.juego import servicio_sintetico


class TestFirmaConsultarHistoria(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.servicio_cripta, self.cripta_id = servicio_sintetico(
            self.temp_dir.name, enemigos=0, ancho=3, alto=3
        )
        self.servicio = EstadoJuegoServicio(comunicacion=self.servicio_cripta)
        self.servicio.iniciarJuego(self.cripta_id, semilla=2026)
        self.servicio.obtenerSala(self.servicio.getJudador().id_sala_actual)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_por_instante_y_por_accion_devuelven_un_resumen(self):
        # instante=0 (estado inicial) y accion=1 (N+1, estado actual)
        self.assertIsInstance(self.servicio.consultarHistoria(instante=0), ResumenEstadoDTO)
        self.assertIsInstance(self.servicio.consultarHistoria(accion=1), ResumenEstadoDTO)

    def test_exige_exactamente_uno_de_los_dos(self):
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria()
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(instante=0, accion=1)

    def test_rechaza_negativos_y_no_enteros(self):
        for malo in (-1, 2.5, "3", True, False):
            with self.assertRaises(ValueError):
                self.servicio.consultarHistoria(instante=malo)
            with self.assertRaises(ValueError):
                self.servicio.consultarHistoria(accion=malo)

    def test_sin_iniciar_lanza_value_error(self):
        servicio_limpio = EstadoJuegoServicio()
        with self.assertRaises(ValueError) as cm:
            servicio_limpio.consultarHistoria(instante=0)
        self.assertEqual(str(cm.exception), "El juego no ha sido iniciado")


if __name__ == "__main__":
    unittest.main()
