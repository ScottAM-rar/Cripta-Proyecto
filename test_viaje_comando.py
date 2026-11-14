"""«Ir a» (capacidad 006): el comando de consola «ir a <id>». Contrato: specs/006-ir-a/contracts/comando-ir-a.md."""
import contextlib
import io
import unittest

from Controlador.ControladorJuego import ControladorJuego
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from tests_labs.escenarios_ir_a import cuadrado, partida_de, pasillo, recorrer_cuadrado


def controlador_con_partida():
    servicio = EstadoJuegoServicio()
    servicio._estadoJuegoLogica = partida_de(cuadrado(100, 100, 50, 400))
    recorrer_cuadrado(servicio._estadoJuegoLogica)
    return ControladorJuego(servicio), servicio


def ejecutar(controlador, linea):
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        reconocido = controlador._procesar_comando_ir_a(linea)
    return reconocido, salida.getvalue()


class TestComandoIrA(unittest.TestCase):
    def test_FR231_ir_a_una_sala_explorada_viaja_e_imprime_el_resumen(self):
        controlador, servicio = controlador_con_partida()
        reconocido, texto = ejecutar(controlador, "ir a 4")
        self.assertTrue(reconocido)
        self.assertEqual(servicio._estadoJuegoLogica.estadoJuego.jugador.id_sala_actual, 4)
        self.assertIn("Llegaste a la sala 4 tras 2 pasos (tiempo 200).", texto)

    def test_FR231_las_mayusculas_y_los_espacios_sobrantes_no_importan(self):
        controlador, servicio = controlador_con_partida()
        reconocido, _ = ejecutar(controlador, "  IR   A   4 ")
        self.assertTrue(reconocido)
        self.assertEqual(servicio._estadoJuegoLogica.estadoJuego.jugador.id_sala_actual, 4)

    def test_otras_entradas_no_son_el_comando(self):
        controlador, _ = controlador_con_partida()
        for linea in ("norte", "mapa", "ir", "irA 3", "ir al norte"):
            with self.subTest(linea=linea):
                reconocido, texto = ejecutar(controlador, linea)
                self.assertFalse(reconocido)
                self.assertEqual(texto, "")


class ServicioQueNoDebeLlamarse:
    def irA(self, destino):
        raise AssertionError("el controlador no debía llamar al servicio")


class TestComandoRechazado(unittest.TestCase):
    def test_FR237_FR238_B_N1_ir_a_una_sala_no_explorada_imprime_el_motivo_y_el_reloj_queda_igual(self):
        servicio = EstadoJuegoServicio()
        servicio._estadoJuegoLogica = partida_de(pasillo(3))
        controlador = ControladorJuego(servicio)
        reloj = servicio._estadoJuegoLogica.estadoJuego.reloj.tiempo_actual
        reconocido, texto = ejecutar(controlador, "ir a 3")
        self.assertTrue(reconocido)
        self.assertIn("Esa sala no está explorada.", texto)
        self.assertEqual(servicio._estadoJuegoLogica.estadoJuego.reloj.tiempo_actual, reloj)
        self.assertEqual(servicio._estadoJuegoLogica.estadoJuego.jugador.id_sala_actual, 1)
        self.assertEqual(servicio._estadoJuegoLogica.acciones_linea_tiempo, 0)

    def test_FR237_un_destino_que_no_es_un_numero_no_llama_al_servicio(self):
        controlador = ControladorJuego(ServicioQueNoDebeLlamarse())
        for linea in ("ir a x", "ir a", "ir a 3 4", "ir a -2"):
            with self.subTest(linea=linea):
                reconocido, texto = ejecutar(controlador, linea)
                self.assertTrue(reconocido)
                self.assertIn("El destino de 'ir a' debe ser el número de una sala. Ejemplo: ir a 12.", texto)   # texto de la 011 (FR-310)


if __name__ == "__main__":
    unittest.main()
