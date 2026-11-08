"""La firma provisional de consultarHistoria (capacidad 004) que Fernanda usa mientras no exista la lógica real."""
import unittest

from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio


class TestFirmaConsultarHistoria(unittest.TestCase):
    def setUp(self):
        self.servicio = EstadoJuegoServicio()

    def test_por_instante_y_por_accion_devuelven_un_resumen(self):
        self.assertIsInstance(self.servicio.consultarHistoria(instante=30), ResumenEstadoDTO)
        self.assertIsInstance(self.servicio.consultarHistoria(accion=4), ResumenEstadoDTO)

    def test_exige_exactamente_uno_de_los_dos(self):
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria()
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(instante=1, accion=1)

    def test_rechaza_negativos_y_no_enteros(self):
        for malo in (-1, 2.5, "3", True):
            with self.assertRaises(ValueError):
                self.servicio.consultarHistoria(instante=malo)


if __name__ == "__main__":
    unittest.main()
