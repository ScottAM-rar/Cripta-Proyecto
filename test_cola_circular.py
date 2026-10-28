"""ColaCircular (Logica/ColaCircular.py): orden FIFO, crecimiento al llenarse y cumplimiento del principio I."""
import os
import unittest

from Logica.ColaCircular import ColaCircular
from test_monticulo_minimo import importaciones_prohibidas


class TestColaCircular(unittest.TestCase):
    def test_I_empieza_vacia_con_capacidad_inicial_16(self):
        cola = ColaCircular()
        self.assertTrue(cola.vacia())
        self.assertEqual(len(cola), 0)
        self.assertEqual(cola.capacidad, 16)

    def test_I_sale_en_el_orden_en_que_entra(self):
        cola = ColaCircular()
        for valor in (7, 3, 9, 1):
            cola.agregar(valor)
        self.assertEqual([cola.sacar() for _ in range(4)], [7, 3, 9, 1])
        self.assertTrue(cola.vacia())

    def test_I_mezclar_agregar_y_sacar_da_varias_vueltas_al_almacen_sin_perder_el_orden(self):
        cola = ColaCircular()
        esperado = []
        siguiente = 0
        for ronda in range(200):                    # entran 3 y sale 2: la cola gira muchas veces sobre 16 posiciones
            for _ in range(3):
                cola.agregar(siguiente)
                esperado.append(siguiente)
                siguiente += 1
            for _ in range(2):
                self.assertEqual(cola.sacar(), esperado.pop(0))
        self.assertEqual(len(cola), len(esperado))
        while not cola.vacia():
            self.assertEqual(cola.sacar(), esperado.pop(0))
        self.assertEqual(esperado, [])

    def test_I_al_llenarse_crece_y_conserva_el_orden(self):
        cola = ColaCircular()
        for valor in range(100):
            cola.agregar(valor)
        self.assertGreaterEqual(cola.capacidad, 100)
        self.assertEqual([cola.sacar() for _ in range(100)], list(range(100)))

    def test_I_crecer_con_la_cabeza_en_medio_del_almacen_conserva_el_orden(self):
        cola = ColaCircular()
        for valor in range(10):
            cola.agregar(valor)
        for _ in range(7):
            cola.sacar()                            # la cabeza queda en la posición 7
        for valor in range(10, 40):
            cola.agregar(valor)                     # se llena, pasa por el final del almacén y crece
        self.assertEqual([cola.sacar() for _ in range(33)], list(range(7, 40)))

    def test_I_vaciar_deja_la_cola_reutilizable(self):
        cola = ColaCircular()
        for valor in range(5):
            cola.agregar(valor)
        cola.vaciar()
        self.assertTrue(cola.vacia())
        self.assertEqual(len(cola), 0)
        cola.agregar(42)
        self.assertEqual(cola.sacar(), 42)

    def test_I_sacar_de_una_cola_vacia_lanza_IndexError(self):
        with self.assertRaises(IndexError):
            ColaCircular().sacar()
        cola = ColaCircular()
        cola.agregar(1)
        cola.sacar()
        with self.assertRaises(IndexError):
            cola.sacar()

    def test_I_una_capacidad_inicial_menor_que_1_se_rechaza(self):
        with self.assertRaises(ValueError):
            ColaCircular(0)

    def test_I_el_modulo_no_importa_nada_prohibido(self):
        self.assertEqual(list(importaciones_prohibidas(os.path.join("Logica", "ColaCircular.py"))), [])


if __name__ == "__main__":
    unittest.main()
