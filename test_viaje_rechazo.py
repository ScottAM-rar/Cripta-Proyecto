"""«Ir a» (capacidad 006), historia 2: una orden que no se puede cumplir con lo que el jugador sabe se rechaza sin tocar la
partida. Caso B-N1 del Apéndice B. Contrato: specs/006-ir-a/contracts/viaje-logica.md §2."""
import unittest

from DTO.ResultadoViajeDTO import (DESTINO_INEXISTENTE, NO_EXPLORADO, RECHAZADO, SIN_RUTA_INICIAL)
from tests_labs.cripta_sintetica import esqueleto_de_conexiones
from tests_labs.escenarios_ir_a import ESTE, caminar, lineas_del_log, mover, partida_de, pasillo, usar_pergamino
from tests_labs.referencia_viaje import resumen_estado


def foto(logica):
    return (resumen_estado(logica), lineas_del_log(logica), logica.viaje_activo)


class TestRechazoSinCosto(unittest.TestCase):
    def _rechazado(self, logica, destino, motivo):
        antes = foto(logica)
        r = logica.iniciarViaje(destino)
        self.assertEqual((r.estado, r.motivo), (RECHAZADO, motivo))
        self.assertTrue(r.mensaje)
        self.assertEqual(foto(logica), antes)                      # reloj, conocimiento, log y acciones intactos
        self.assertIsNone(logica.viaje_activo)
        for linea in lineas_del_log(logica):
            self.assertNotIn("IR_A", linea)

    def test_FR237_FR238_APENDICE_B_N1_ir_a_una_sala_no_explorada_se_rechaza_sin_consumir_tiempo(self):
        logica = partida_de(pasillo(3))                             # la sala 2 está avistada y la 3 desconocida
        self._rechazado(logica, 2, NO_EXPLORADO)
        self._rechazado(logica, 3, NO_EXPLORADO)

    def test_FR237_una_sala_explorada_sin_ruta_conocida_se_rechaza(self):
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"un_sentido": True})])     # solo existe 1 → 2
        logica = partida_de(salas)
        mover(logica, ESTE)                                         # en 2: la sala 1 está explorada, pero no hay salida a ella
        self.assertEqual(logica.mapaConocido.estado_de(1), 2)
        self._rechazado(logica, 1, SIN_RUTA_INICIAL)

    def test_FR237_un_destino_que_no_es_una_sala_se_rechaza(self):
        logica = partida_de(pasillo(3))
        for destino in (0, -1, 99, "abc", None):
            with self.subTest(destino=destino):
                self._rechazado(logica, destino, DESTINO_INEXISTENTE)

    def test_FR238_tras_un_rechazo_el_pergamino_deshace_la_accion_anterior_no_el_rechazo(self):
        logica = partida_de(pasillo(3))
        mover(logica, ESTE)                                         # la única acción: de 1 a 2
        self._rechazado(logica, 3, NO_EXPLORADO)
        self.assertEqual(logica.acciones_linea_tiempo, 1)
        usar_pergamino(logica)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 1)


if __name__ == "__main__":
    unittest.main()
