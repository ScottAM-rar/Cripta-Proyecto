"""FR-509: misma cripta, mismo origen, mismo límite y mismo criterio dan exactamente la misma secuencia."""
import unittest

from Logica.RecorridoPorNiveles import RecorridoPorNiveles
from tests_labs.cripta_sintetica import esqueleto_dirigido_aleatorio, esqueleto_rejilla, mapa_desde_esqueleto


def como_tupla(resultado):
    return tuple(resultado.salas), tuple(resultado.niveles)


class TestDeterminismoDelRecorrido(unittest.TestCase):
    def setUp(self):
        self.esqueleto = esqueleto_dirigido_aleatorio(150, 7, 0.2, 0.1)
        self.ids = [s["id"] for s in self.esqueleto]

    def test_FR509_el_mismo_recorrido_repetido_100_veces_da_100_veces_la_misma_secuencia(self):
        recorridor = RecorridoPorNiveles(mapa_desde_esqueleto(self.esqueleto))
        origen = self.ids[len(self.ids) // 3]
        referencia = como_tupla(recorridor.recorrer(origen))
        for _ in range(100):
            self.assertEqual(como_tupla(recorridor.recorrer(origen)), referencia)

    def test_FR509_alternar_con_recorridos_de_otros_origenes_y_limites_no_deja_rastro_entre_llamadas(self):
        recorridor = RecorridoPorNiveles(mapa_desde_esqueleto(self.esqueleto))
        origen = self.ids[5]
        referencia = como_tupla(recorridor.recorrer(origen, limite=4))
        for vuelta in range(100):
            recorridor.recorrer(self.ids[(vuelta * 13) % len(self.ids)], limite=vuelta % 7 or None)
            self.assertEqual(como_tupla(recorridor.recorrer(origen, limite=4)), referencia)

    def test_FR509_un_recorridor_nuevo_da_lo_mismo_que_uno_ya_usado(self):
        usado = RecorridoPorNiveles(mapa_desde_esqueleto(self.esqueleto))
        for origen in self.ids[:20]:
            usado.recorrer(origen)
        mapa = mapa_desde_esqueleto(self.esqueleto)
        for origen in self.ids[::11]:
            self.assertEqual(como_tupla(usado.recorrer(origen)), como_tupla(RecorridoPorNiveles(mapa).recorrer(origen)))

    def test_FR509_el_resultado_no_depende_del_orden_en_que_llegan_las_salas_del_esqueleto(self):
        al_reves = list(reversed(self.esqueleto))
        for sala in al_reves:                                     # y tampoco del orden en que se declararon las salidas
            sala["salidas"] = {letra: sala["salidas"][letra] for letra in reversed(list(sala["salidas"]))}
        normal = RecorridoPorNiveles(mapa_desde_esqueleto(esqueleto_dirigido_aleatorio(150, 7, 0.2, 0.1)))
        otro = RecorridoPorNiveles(mapa_desde_esqueleto(al_reves))
        for origen in self.ids[::7]:
            self.assertEqual(como_tupla(normal.recorrer(origen)), como_tupla(otro.recorrer(origen)))

    def test_FR509_dos_recorridos_con_el_mismo_criterio_dan_lo_mismo(self):
        recorridor = RecorridoPorNiveles(mapa_desde_esqueleto(self.esqueleto))
        criterio = lambda arista: (arista.origen + arista.destino) % 3 != 0
        origen = self.ids[2]
        self.assertEqual(como_tupla(recorridor.recorrer(origen, transitable=criterio)),
                         como_tupla(recorridor.recorrer(origen, transitable=criterio)))

    def test_FR509_la_secuencia_de_una_rejilla_es_la_misma_en_dos_construcciones_independientes(self):
        a = RecorridoPorNiveles(mapa_desde_esqueleto(esqueleto_rejilla(12, 12, semilla=3, costo_max=300)))
        b = RecorridoPorNiveles(mapa_desde_esqueleto(esqueleto_rejilla(12, 12, semilla=3, costo_max=300)))
        self.assertEqual(como_tupla(a.recorrer(70)), como_tupla(b.recorrer(70)))


if __name__ == "__main__":
    unittest.main()
