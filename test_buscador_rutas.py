"""BuscadorRutas (Logica/BuscadorRutas.py) sobre una vista falsa de pocas salas. Cada prueba cita el requisito que demuestra."""
import unittest

from Logica.BuscadorRutas import BuscadorRutas


class Arista:
    def __init__(self, origen, destino, costo, abierta=True):
        self.origen, self.destino, self.costo, self.abierta = origen, destino, costo, abierta


class VistaFalsa:
    """Vista de pocas salas escrita a mano: lista de (origen, destino, costo[, abierta])."""

    def __init__(self, tamano, aristas):
        self.tamano = tamano
        self._aristas = [Arista(*a) for a in aristas]

    def salidas(self, sala):
        return [a for a in self._aristas if a.origen == sala]

    def entrantes(self, sala):
        return [a for a in self._aristas if a.destino == sala]

    def transitable(self, arista):
        return arista.abierta


def doble(a, b, costo):
    return [(a, b, costo), (b, a, costo)]


def paso(vista, origen, destino, limite=10 ** 6):
    buscador = BuscadorRutas()
    buscador.distancias_hacia(destino, vista, limite)
    arista = buscador.siguiente_paso(origen)
    return buscador, (None if arista is None else arista.destino)


class TestBuscadorRutas(unittest.TestCase):
    def test_FR111_la_distancia_suma_el_costo_de_cada_salida(self):
        vista = VistaFalsa(4, doble(1, 2, 100) + doble(2, 3, 250))
        buscador, _ = paso(vista, 1, 3)
        self.assertEqual(buscador.costo(3), 0)
        self.assertEqual(buscador.costo(2), 250)
        self.assertEqual(buscador.costo(1), 350)

    def test_FR111_prefiere_menor_costo_aunque_tenga_mas_salas(self):
        vista = VistaFalsa(5, doble(1, 2, 500) + doble(1, 3, 100) + doble(3, 4, 100) + doble(4, 2, 100))
        buscador, siguiente = paso(vista, 1, 2)
        self.assertEqual(buscador.costo(1), 300)
        self.assertEqual(siguiente, 3)

    def test_FR114_con_rutas_de_igual_costo_gana_la_vecina_de_menor_id(self):
        vista = VistaFalsa(5, doble(1, 3, 100) + doble(1, 2, 100) + doble(3, 4, 100) + doble(2, 4, 100))
        _, siguiente = paso(vista, 1, 4)
        self.assertEqual(siguiente, 2)

    def test_FR114_el_desempate_no_depende_del_orden_de_declaracion(self):
        directo = doble(1, 2, 100) + doble(1, 3, 100) + doble(2, 4, 100) + doble(3, 4, 100)
        invertido = list(reversed(directo))
        self.assertEqual(paso(VistaFalsa(5, directo), 1, 4)[1], 2)
        self.assertEqual(paso(VistaFalsa(5, invertido), 1, 4)[1], 2)

    def test_FR111_una_puerta_cerrada_se_trata_como_ruta_inexistente(self):
        vista = VistaFalsa(3, [(1, 2, 100, False), (2, 1, 100)])
        buscador, siguiente = paso(vista, 1, 2)
        self.assertIsNone(buscador.costo(1))
        self.assertIsNone(siguiente)

    def test_FR111_ruta_inexistente_no_da_siguiente_paso(self):
        vista = VistaFalsa(4, doble(1, 2, 100))
        buscador, siguiente = paso(vista, 3, 2)
        self.assertIsNone(buscador.costo(3))
        self.assertIsNone(siguiente)

    def test_FR124_una_conexion_de_un_solo_sentido_solo_se_usa_en_ese_sentido(self):
        vista = VistaFalsa(3, [(1, 2, 100)])
        self.assertEqual(paso(vista, 1, 2)[1], 2)
        self.assertIsNone(paso(vista, 2, 1)[1])

    def test_FR111_el_limite_deja_fuera_las_salas_mas_lejanas(self):
        vista = VistaFalsa(4, doble(1, 2, 100) + doble(2, 3, 100))
        buscador, siguiente = paso(vista, 1, 3, limite=150)
        self.assertEqual(buscador.costo(2), 100)
        self.assertIsNone(buscador.costo(1))
        self.assertIsNone(siguiente)

    def test_FR111_en_el_destino_no_hay_siguiente_paso(self):
        vista = VistaFalsa(3, doble(1, 2, 100))
        self.assertIsNone(paso(vista, 2, 2)[1])

    def test_FR116_consultar_dos_veces_con_destinos_distintos_no_arrastra_lo_anterior(self):
        vista = VistaFalsa(4, doble(1, 2, 100) + doble(2, 3, 100))
        buscador = BuscadorRutas()
        buscador.distancias_hacia(3, vista, 1000)
        self.assertEqual(buscador.costo(1), 200)
        buscador.distancias_hacia(1, vista, 1000)
        self.assertEqual(buscador.costo(1), 0)
        self.assertEqual(buscador.costo(3), 200)
        self.assertEqual(buscador.siguiente_paso(3).destino, 2)

    def test_FR111_destino_inexistente_deja_todo_fuera_de_alcance(self):
        vista = VistaFalsa(3, doble(1, 2, 100))
        buscador = BuscadorRutas()
        buscador.distancias_hacia(99, vista, 1000)
        self.assertIsNone(buscador.costo(1))
        self.assertIsNone(buscador.siguiente_paso(1))


if __name__ == "__main__":
    unittest.main()
