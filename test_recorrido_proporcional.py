"""FR-510 / SC-004: el trabajo de un recorrido acotado depende de lo visitado, no del tamaño de la cripta.

Es una prueba de CONTEO (salas visitadas y salidas examinadas), no de tiempo, para que no dependa de la máquina."""
import unittest

from Logica.RecorridoPorNiveles import RecorridoPorNiveles
from tests_labs.cripta_sintetica import esqueleto_rejilla, mapa_desde_esqueleto

LADOS = (20, 70, 200)                          # 400, 4 900 y 40 000 salas


def centro(lado):
    return (lado // 2) * lado + lado // 2 + 1


class TestTrabajoProporcionalALoVisitado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recorridores = []
        for lado in LADOS:
            mapa = mapa_desde_esqueleto(esqueleto_rejilla(lado, lado))
            cls.recorridores.append((lado, RecorridoPorNiveles(mapa)))

    def contar(self, recorridor, origen, limite):
        resultado = recorridor.recorrer(origen, limite=limite)
        return len(resultado.salas), recorridor.salas_visitadas, recorridor.salidas_examinadas

    def test_FR510_SC004_un_recorrido_de_2_niveles_visita_y_examina_lo_mismo_en_400_4900_y_40000_salas(self):
        conteos = [self.contar(recorridor, centro(lado), 2) for lado, recorridor in self.recorridores]
        self.assertEqual(conteos[0], conteos[1])
        self.assertEqual(conteos[1], conteos[2])
        largo, visitadas, examinadas = conteos[0]
        self.assertEqual((largo, visitadas), (13, 13))                    # 1 origen + 4 a un salto + 8 a dos saltos
        self.assertEqual(examinadas, 4 + 4 * 4)                           # las del origen y las de las 4 de nivel 1

    def test_FR510_las_salidas_examinadas_son_a_lo_sumo_4_por_sala_visitada(self):
        for lado, recorridor in self.recorridores:
            for limite in (0, 1, 2, 5, None):
                with self.subTest(salas=lado * lado, limite=limite):
                    _, visitadas, examinadas = self.contar(recorridor, centro(lado), limite)
                    self.assertLessEqual(examinadas, 4 * visitadas)

    def test_FR510_un_limite_de_0_visita_solo_el_origen_y_no_examina_ninguna_salida(self):
        for lado, recorridor in self.recorridores:
            self.assertEqual(self.contar(recorridor, centro(lado), 0), (1, 1, 0))

    def test_FR510_los_contadores_se_reinician_en_cada_recorrido(self):
        _, recorridor = self.recorridores[0]
        self.contar(recorridor, centro(20), None)                         # un recorrido grande antes
        self.assertEqual(self.contar(recorridor, centro(20), 1), (5, 5, 4))

    def test_FR510_sin_limite_el_trabajo_si_crece_con_la_cripta_porque_todo_es_alcanzable(self):
        visitadas = [self.contar(recorridor, centro(lado), None)[1] for lado, recorridor in self.recorridores]
        self.assertEqual(visitadas, [400, 4900, 40000])


if __name__ == "__main__":
    unittest.main()
