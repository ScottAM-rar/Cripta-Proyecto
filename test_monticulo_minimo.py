"""MonticuloMinimo (Logica/MonticuloMinimo.py): orden por (costo, id) y cumplimiento del principio I."""
import ast
import os
import random
import unittest

from Logica.MonticuloMinimo import MonticuloMinimo

MODULOS_PROHIBIDOS = ("heapq", "bisect", "collections", "networkx")


def importaciones_prohibidas(ruta):
    with open(ruta, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            nombres = [nodo.module or ""]
        else:
            continue
        for nombre in nombres:
            if nombre.split(".")[0] in MODULOS_PROHIBIDOS:
                yield nombre


class TestMonticuloMinimo(unittest.TestCase):
    def test_I_empieza_vacio(self):
        m = MonticuloMinimo()
        self.assertTrue(m.vacio())
        self.assertEqual(len(m), 0)

    def test_I_extrae_en_orden_de_costo_y_desempata_por_id(self):
        m = MonticuloMinimo()
        for costo, sala in ((300, 4), (100, 9), (100, 2), (200, 1), (100, 5)):
            m.insertar(costo, sala)
        self.assertEqual(m.minimo(), (100, 2))
        salida = []
        while not m.vacio():
            salida.append(m.extraer_minimo())
        self.assertEqual(salida, [(100, 2), (100, 5), (100, 9), (200, 1), (300, 4)])

    def test_I_acepta_entradas_repetidas(self):
        m = MonticuloMinimo()
        for _ in range(3):
            m.insertar(50, 7)
        self.assertEqual([m.extraer_minimo() for _ in range(3)], [(50, 7)] * 3)

    def test_I_equivale_a_ordenar_con_datos_aleatorios_deterministas(self):
        azar = random.Random(42)
        pares = [(azar.randint(1, 50), azar.randint(1, 50)) for _ in range(500)]
        m = MonticuloMinimo()
        for costo, sala in pares:
            m.insertar(costo, sala)
        self.assertEqual([m.extraer_minimo() for _ in range(len(pares))], sorted(pares))

    def test_I_extraer_o_mirar_un_monticulo_vacio_falla(self):
        with self.assertRaises(IndexError):
            MonticuloMinimo().extraer_minimo()
        with self.assertRaises(IndexError):
            MonticuloMinimo().minimo()

    def test_I_vaciar_deja_el_monticulo_reutilizable(self):
        m = MonticuloMinimo()
        m.insertar(1, 1)
        m.vaciar()
        self.assertTrue(m.vacio())
        m.insertar(5, 2)
        self.assertEqual(m.extraer_minimo(), (5, 2))

    def test_I_los_modulos_nuevos_no_importan_nada_prohibido(self):
        for nombre in ("MonticuloMinimo", "MapaCripta", "CampoDeCostos", "CompCazador"):
            ruta = os.path.join("Logica", nombre + ".py")
            if os.path.exists(ruta):
                self.assertEqual(list(importaciones_prohibidas(ruta)), [], ruta)


if __name__ == "__main__":
    unittest.main()
