"""«Ir a» (capacidad 006): un viaje no hace solicitudes que caminar la misma ruta a mano no haga (FR-248, principio VI)."""
import unittest

from tests_labs.escenarios_ir_a import escenario_viaje, viajar
from tests_labs.referencia_viaje import caminar_a_mano


class TestViajeSinRed(unittest.TestCase):
    def test_FR248_un_viaje_completo_no_hace_solicitudes_adicionales_a_las_de_caminar_a_mano(self):
        for nombre in ("simple", "b_n3"):
            with self.subTest(escenario=nombre):
                escenario = escenario_viaje(nombre)
                preparado = escenario.jugar(hasta=len(escenario.guion) - 1)
                solicitudes_antes = len(escenario.api.llamadas)
                destino = escenario.guion[-1][1]
                r = viajar(preparado, destino)
                del_viaje = len(escenario.api.llamadas) - solicitudes_antes

                otro = escenario_viaje(nombre)
                a_mano = otro.jugar(hasta=len(otro.guion) - 1)
                antes = len(otro.api.llamadas)
                caminar_a_mano(a_mano, [a_mano.estadoJuego.jugador.id_sala_actual] + r.recorrido)
                de_la_mano = len(otro.api.llamadas) - antes
                self.assertEqual(del_viaje, de_la_mano)


if __name__ == "__main__":
    unittest.main()
