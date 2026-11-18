"""Prueba del bloque de benchmark `pantallas` (capacidad 011, FR-311, constitución VII).
Cada prueba cita el requisito que demuestra."""
from __future__ import annotations

import unittest

from bench import nombres_de_bloques, pantallas


class TestBenchPantallas(unittest.TestCase):

    def test_FR311_el_bloque_cumple_y_mide_la_elegida_y_la_descartada_con_0_10_y_100_enemigos(self):
        filas: list = []
        cumple = pantallas.ejecutar(filas)
        self.assertTrue(cumple, "las dos formas de armar el texto deben coincidir y la sala con 100 enemigos < 20 ms")
        conceptos = [fila[1] for fila in filas]
        for cantidad in pantallas.CANTIDADES:
            self.assertTrue(any(f"{cantidad:>3} enemigos  elegida" in c for c in conceptos), cantidad)
            self.assertTrue(any(f"{cantidad:>3} enemigos  descartada" in c for c in conceptos), cantidad)
        self.assertTrue(any("resumen  elegida" in c for c in conceptos))
        self.assertTrue(any("resumen  descartada" in c for c in conceptos))

    def test_FR311_la_verificacion_previa_compara_el_texto_de_las_dos_formas(self):
        filas: list = []
        pantallas.ejecutar(filas)
        verificaciones = [fila for fila in filas if fila[1].startswith("verificación")]
        self.assertGreaterEqual(len(verificaciones), 5)
        for fila in verificaciones:
            self.assertEqual(fila[2], "OK", fila[1])

    def test_FR311_la_alternativa_descartada_produce_exactamente_el_mismo_texto(self):
        jugador, sala, conocida, llaves, mensajes = pantallas._datos_de_sala(10)
        argumentos = (jugador, 250, sala, conocida, llaves, None, mensajes)
        self.assertEqual(pantallas.texto_sala_concatenado(*argumentos), pantallas.P.texto_sala(*argumentos))

    def test_el_bloque_esta_registrado_en_bench(self):
        self.assertIn("pantallas", nombres_de_bloques())


if __name__ == "__main__":
    unittest.main()
