"""Recorrido por niveles (Logica/RecorridoPorNiveles.py). Cada prueba cita el requisito que demuestra.

Los resultados esperados de los escenarios están escritos a mano; la equivalencia con una referencia ingenua se prueba
aparte, con criptas aleatorias."""
import unittest

from Logica.RecorridoPorNiveles import RecorridoPorNiveles
from tests_labs.cripta_sintetica import (esqueleto_de_conexiones, esqueleto_dirigido_aleatorio, esqueleto_lineal,
                                         mapa_desde_esqueleto)
from tests_labs.referencia_recorrido import recorrer_referencia


def sala(id_sala, **salidas):
    """Sala del esqueleto crudo. Las salidas se dan por letra: sala(1, N=5, S=3)."""
    return {"id": id_sala, "nombre": f"Sala {id_sala}", "salidas": {letra: {"sala": destino} for letra, destino in salidas.items()}}


def recorrer(esqueleto, origen, **opciones):
    resultado = RecorridoPorNiveles(mapa_desde_esqueleto(esqueleto)).recorrer(origen, **opciones)
    return resultado.salas, resultado.niveles


def criterio_por_par(semilla):
    """Criterio de transitabilidad de prueba: función del par (origen, destino), no de la arista."""
    return lambda origen, destino: (origen * 7 + destino * 13 + semilla) % 4 != 0


def adaptar(criterio):
    """Lo mismo, pero con la forma que recibe el recorrido real: una arista."""
    return lambda arista: criterio(arista.origen, arista.destino)


class TestOrdenYAlcance(unittest.TestCase):
    def test_FR501_una_linea_de_5_salas_se_visita_en_orden_de_cercania_desde_un_extremo(self):
        self.assertEqual(recorrer(esqueleto_lineal([None] * 4), 1), ([1, 2, 3, 4, 5], [0, 1, 2, 3, 4]))

    def test_FR501_desde_el_medio_de_la_linea_el_origen_va_primero_y_luego_los_dos_lados_por_nivel(self):
        self.assertEqual(recorrer(esqueleto_lineal([None] * 4), 3), ([3, 2, 4, 1, 5], [0, 1, 1, 2, 2]))

    def test_FR502_con_dos_vecinas_al_mismo_nivel_va_primero_la_de_menor_id_aunque_se_declare_despues(self):
        esqueleto = [sala(1, N=5, S=3), sala(3), sala(5)]                 # 5 está declarada antes que 3
        self.assertEqual(recorrer(esqueleto, 1), ([1, 3, 5], [0, 1, 1]))

    def test_FR502_el_orden_por_id_vale_dentro_de_cada_nivel_no_solo_en_el_primero(self):
        # el hijo de la 3 (la 9) se descubre antes que el de la 5 (la 4), pero la 4 tiene menor id
        esqueleto = [sala(1, N=5, S=3), sala(3, E=9), sala(5, E=4), sala(4), sala(9)]
        self.assertEqual(recorrer(esqueleto, 1), ([1, 3, 5, 4, 9], [0, 1, 1, 2, 2]))

    def test_FR503_un_ciclo_no_repite_ninguna_sala(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, None, "E", "O"), (2, 3, None, "E", "O"), (3, 1, None, "E", "O")])
        self.assertEqual(recorrer(esqueleto, 1), ([1, 2, 3], [0, 1, 1]))

    def test_FR503_dos_caminos_hacia_la_misma_sala_la_visitan_una_vez_en_el_nivel_mas_cercano(self):
        # 1 -> 4 directo (nivel 1) y 1 -> 2 -> 4 (nivel 2): la 4 va en el nivel 1
        esqueleto = [sala(1, E=2, S=4), sala(2, O=1, E=4), sala(4, N=1, O=2)]
        self.assertEqual(recorrer(esqueleto, 1), ([1, 2, 4], [0, 1, 1]))

    def test_FR503_dos_salidas_distintas_hacia_la_misma_sala_la_visitan_una_vez(self):
        self.assertEqual(recorrer([sala(1, N=2, S=2), sala(2)], 1), ([1, 2], [0, 1]))

    def test_FR503_una_salida_de_una_sala_a_si_misma_no_la_repite(self):
        self.assertEqual(recorrer([sala(1, E=1, S=2), sala(2)], 1), ([1, 2], [0, 1]))

    def test_FR501_FR503_el_origen_dentro_de_un_ciclo_aparece_una_vez_al_principio(self):
        esqueleto = [sala(1, E=2), sala(2, E=3), sala(3, E=1)]
        salas, niveles = recorrer(esqueleto, 2)
        self.assertEqual((salas, niveles), ([2, 3, 1], [0, 1, 2]))

    def test_FR508_un_origen_sin_salidas_da_un_recorrido_de_una_sola_sala(self):
        self.assertEqual(recorrer([sala(1), sala(2)], 1), ([1], [0]))

    def test_FR505_las_salas_sin_camino_desde_el_origen_no_aparecen(self):
        esqueleto = [sala(1, E=2), sala(2, O=1), sala(3, E=4), sala(4, O=3)]
        self.assertEqual(recorrer(esqueleto, 1), ([1, 2], [0, 1]))

    def test_FR506_una_salida_de_un_solo_sentido_no_se_recorre_al_reves(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"un_sentido": True})])
        self.assertEqual(recorrer(esqueleto, 1), ([1, 2], [0, 1]))
        self.assertEqual(recorrer(esqueleto, 2), ([2], [0]))

    def test_FR507_una_salida_no_declarada_transitable_no_se_recorre_ni_sus_salas_exclusivas(self):
        esqueleto = esqueleto_lineal([None] * 3)                          # 1 - 2 - 3 - 4
        sin_2_a_3 = lambda arista: not (arista.origen == 2 and arista.destino == 3)
        self.assertEqual(recorrer(esqueleto, 1, transitable=sin_2_a_3), ([1, 2], [0, 1]))

    def test_FR507_una_sala_con_otro_camino_transitable_sigue_apareciendo(self):
        esqueleto = [sala(1, E=2, S=3), sala(2, E=4), sala(3, E=4), sala(4)]
        sin_2_a_4 = lambda arista: not (arista.origen == 2 and arista.destino == 4)
        self.assertEqual(recorrer(esqueleto, 1, transitable=sin_2_a_4), ([1, 2, 3, 4], [0, 1, 1, 2]))

    def test_FR507_sin_criterio_valen_todas_las_salidas(self):
        esqueleto = esqueleto_lineal([None] * 3)
        self.assertEqual(recorrer(esqueleto, 1), recorrer(esqueleto, 1, transitable=None))
        self.assertEqual(recorrer(esqueleto, 1)[0], [1, 2, 3, 4])

    def test_FR507_el_criterio_se_evalua_con_la_arista_que_se_examina(self):
        vistas = []
        esqueleto = [sala(1, E=2), sala(2)]
        recorrer(esqueleto, 1, transitable=lambda arista: vistas.append((arista.origen, arista.destino, arista.direccion)) or True)
        self.assertEqual(vistas, [(1, 2, "este")])

    def test_FR508_si_ninguna_salida_del_origen_es_transitable_solo_queda_el_origen(self):
        esqueleto = esqueleto_lineal([None] * 3)
        self.assertEqual(recorrer(esqueleto, 1, transitable=lambda arista: False), ([1], [0]))


class TestOrigenYSalasInexistentes(unittest.TestCase):
    ESQUELETO_CON_HUECO = [sala(1, N=2, S=99, E=3), sala(2, E=4), sala(4)]      # la sala 3 no existe; la 99 tampoco

    def test_FR512_un_origen_que_no_existe_se_rechaza_con_un_error_claro(self):
        mapa = mapa_desde_esqueleto(self.ESQUELETO_CON_HUECO)
        recorridor = RecorridoPorNiveles(mapa)
        for origen in (3, 0, -1, 99, 1000):
            with self.subTest(origen=origen):
                with self.assertRaises(ValueError) as contexto:
                    recorridor.recorrer(origen)
                self.assertIn(str(origen), str(contexto.exception))

    def test_FR512_un_origen_que_no_es_un_entero_se_rechaza(self):
        recorridor = RecorridoPorNiveles(mapa_desde_esqueleto(self.ESQUELETO_CON_HUECO))
        for origen in (True, "1", 1.0, None):
            with self.subTest(origen=origen):
                with self.assertRaises(ValueError):
                    recorridor.recorrer(origen)

    def test_FR513_una_salida_hacia_una_sala_que_no_existe_se_ignora_y_el_resto_no_cambia(self):
        # la sala 1 tiene salidas hacia la 3 (hueco) y hacia la 99 (fuera de rango): no aparecen ni se rechaza el recorrido
        self.assertEqual(recorrer(self.ESQUELETO_CON_HUECO, 1), ([1, 2, 4], [0, 1, 2]))

    def test_FR513_el_criterio_no_se_consulta_para_salidas_hacia_salas_que_no_existen(self):
        consultas = []
        recorrer(self.ESQUELETO_CON_HUECO, 1, transitable=lambda arista: consultas.append(arista.destino) or True)
        self.assertEqual(consultas, [2, 4])

    def test_FR512_existe_distingue_ids_con_y_sin_sala(self):
        mapa = mapa_desde_esqueleto(self.ESQUELETO_CON_HUECO)
        self.assertEqual(mapa.existe, [False, True, True, False, True])


class TestEquivalenciaConLaReferencia(unittest.TestCase):
    def test_FR501_FR502_FR503_FR505_FR506_FR507_FR513_coincide_con_la_referencia_en_200_criptas_aleatorias(self):
        for semilla in range(200):
            total = 1 + (semilla * 37) % 300
            esqueleto = esqueleto_dirigido_aleatorio(total, semilla, 0.25, 0.3 if semilla % 2 else 0.0)
            ids = [s["id"] for s in esqueleto]
            origen = ids[(semilla * 11) % len(ids)]
            criterio = criterio_por_par(semilla) if semilla % 3 else None
            with self.subTest(semilla=semilla):
                esperado = recorrer_referencia(esqueleto, origen, transitable=criterio)
                obtenido = recorrer(esqueleto, origen, transitable=None if criterio is None else adaptar(criterio))
                self.assertEqual(obtenido, esperado)
                self.comprobar_invariantes(obtenido, origen)

    def comprobar_invariantes(self, resultado, origen):
        salas, niveles = resultado
        self.assertEqual(len(salas), len(niveles))
        self.assertEqual((salas[0], niveles[0]), (origen, 0))
        vista = [False] * (max(salas) + 1)
        for s in salas:                                                          # sin repetidos
            self.assertFalse(vista[s], f"la sala {s} aparece dos veces")
            vista[s] = True
        for i in range(1, len(salas)):
            self.assertGreaterEqual(niveles[i], niveles[i - 1])
            self.assertLessEqual(niveles[i] - niveles[i - 1], 1)               # no se salta ningún nivel
            if niveles[i] == niveles[i - 1]:
                self.assertGreater(salas[i], salas[i - 1])                       # dentro de un nivel, ids crecientes


class TestLimiteDeNiveles(unittest.TestCase):
    LINEA = esqueleto_lineal([None] * 6)                                      # 7 salas en línea: 1 - 2 - ... - 7

    def test_FR504_un_limite_de_2_niveles_no_incluye_las_salas_a_3_saltos_o_mas(self):
        self.assertEqual(recorrer(self.LINEA, 1, limite=2), ([1, 2, 3], [0, 1, 2]))
        self.assertEqual(recorrer(self.LINEA, 4, limite=2), ([4, 3, 5, 2, 6], [0, 1, 1, 2, 2]))

    def test_FR504_un_limite_de_0_deja_solo_el_origen(self):
        self.assertEqual(recorrer(self.LINEA, 4, limite=0), ([4], [0]))

    def test_FR504_un_limite_de_1_deja_el_origen_y_sus_vecinas(self):
        self.assertEqual(recorrer(self.LINEA, 4, limite=1), ([4, 3, 5], [0, 1, 1]))

    def test_FR504_un_limite_mayor_que_la_distancia_a_la_sala_mas_lejana_da_lo_mismo_que_sin_limite(self):
        sin_limite = recorrer(self.LINEA, 1)
        for limite in (6, 7, 100):
            self.assertEqual(recorrer(self.LINEA, 1, limite=limite), sin_limite)

    def test_FR504_el_limite_se_aplica_al_nivel_mas_cercano_de_cada_sala(self):
        # la 4 está a 1 salto por el atajo y a 3 por la línea: con límite 1 aparece, en el nivel 1
        esqueleto = [sala(1, E=2, S=4), sala(2, E=3), sala(3, E=4), sala(4)]
        self.assertEqual(recorrer(esqueleto, 1, limite=1), ([1, 2, 4], [0, 1, 1]))

    def test_FR504_un_limite_invalido_se_rechaza_con_un_error_que_nombra_el_valor(self):
        recorridor = RecorridoPorNiveles(mapa_desde_esqueleto(self.LINEA))
        for invalido in (-1, 1.5, True, False, "2", [2]):
            with self.subTest(limite=invalido):
                with self.assertRaises(ValueError) as contexto:
                    recorridor.recorrer(1, limite=invalido)
                self.assertIn(repr(invalido), str(contexto.exception))

    def test_FR504_sin_limite_se_recorre_todo_lo_alcanzable(self):
        self.assertEqual(recorrer(self.LINEA, 1)[0], [1, 2, 3, 4, 5, 6, 7])

    def test_FR504_FR510_un_limite_de_0_no_examina_ninguna_salida_del_origen(self):
        consultas = []
        recorrer(self.LINEA, 4, limite=0, transitable=lambda arista: consultas.append(arista) or True)
        self.assertEqual(consultas, [])

    def test_FR504_con_limite_coincide_con_la_referencia_en_criptas_aleatorias(self):
        for semilla in range(100):
            total = 1 + (semilla * 29) % 250
            esqueleto = esqueleto_dirigido_aleatorio(total, 1000 + semilla, 0.25, 0.3 if semilla % 2 else 0.0)
            ids = [s["id"] for s in esqueleto]
            origen = ids[(semilla * 5) % len(ids)]
            limite = None if semilla % 10 == 0 else semilla % 9
            criterio = criterio_por_par(semilla) if semilla % 3 else None
            with self.subTest(semilla=semilla, limite=limite):
                esperado = recorrer_referencia(esqueleto, origen, limite=limite, transitable=criterio)
                obtenido = recorrer(esqueleto, origen, limite=limite, transitable=None if criterio is None else adaptar(criterio))
                self.assertEqual(obtenido, esperado)
                if limite is not None:
                    self.assertLessEqual(max(obtenido[1]), limite)


if __name__ == "__main__":
    unittest.main()
