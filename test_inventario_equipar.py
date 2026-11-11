"""Equipar desde el inventario: un objeto en la segunda posición no está 'ya equipado' salvo que la primera guarde el
otro tipo de equipo (arma + armadura). Regresión del caso arma que no es el cursor actual."""
import unittest

from DTO.Objeto import Arma, Armadura, Objeto
from Logica.InventarioLogica import InventarioLogica


def _ids(inv):
    nodo, ids = inv.cabeza, []
    while nodo is not None:
        ids.append(nodo.objeto.id_catalogo)
        nodo = nodo.siguiente
    return ids


class TestEquipar(unittest.TestCase):
    def setUp(self):
        self.inv = InventarioLogica(capacidad_maxima=6)

    def test_arma_en_segunda_posicion_con_objeto_cualquiera_sube_a_la_cabeza(self):
        daga = Arma("daga", "Daga", 1, 1, 3)
        self.inv.agregar_objeto(Objeto("antorcha", "Antorcha", 1, 1))
        self.inv.agregar_objeto(daga)
        self.inv.equipar_objeto(daga)
        self.assertEqual(_ids(self.inv), ["daga", "antorcha"])

    def test_segunda_arma_reemplaza_a_la_equipada(self):
        daga, espada = Arma("daga", "Daga", 1, 1, 0), Arma("espada", "Espada", 1, 1, 0)
        self.inv.agregar_objeto(daga)
        self.inv.agregar_objeto(espada)
        self.inv.equipar_objeto(espada)
        self.assertEqual(_ids(self.inv), ["espada", "daga"])

    def test_armadura_en_segunda_posicion_junto_a_un_arma_ya_esta_equipada(self):
        daga, cota = Arma("daga", "Daga", 1, 1, 0), Armadura("cota", "Cota", 1, 1, 0)
        self.inv.agregar_objeto(daga)
        self.inv.agregar_objeto(cota)
        self.inv.agregar_objeto(Objeto("llave", "Llave", 1, 1))
        self.inv.equipar_objeto(cota)
        self.assertEqual(_ids(self.inv), ["daga", "cota", "llave"])

    def test_objeto_ya_en_la_cabeza_no_cambia_nada(self):
        daga = Arma("daga", "Daga", 1, 1, 0)
        self.inv.agregar_objeto(daga)
        self.inv.agregar_objeto(Objeto("antorcha", "Antorcha", 1, 1))
        self.inv.equipar_objeto(daga)
        self.assertEqual(_ids(self.inv), ["daga", "antorcha"])


if __name__ == "__main__":
    unittest.main()
