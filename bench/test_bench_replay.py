"""Prueba del bloque de benchmark replay y exportación a CSV (FR-412, FR-413).
"""
from __future__ import annotations

import io
import tempfile
import unittest

from bench import replay
from bench.salida import escribir_csv


class TestBenchReplay(unittest.TestCase):
    """Verifica que replay.ejecutar corre programáticamente y produce filas válidas."""

    def test_ejecutar_benchmark_replay(self):
        filas = []
        salida_io = io.StringIO()
        cumple = replay.ejecutar(filas, imprimir=lambda s="": salida_io.write(s + "\n"))

        self.assertTrue(cumple)
        self.assertGreater(len(filas), 0)

        # Verificamos secciones en la salida de consola
        salida_texto = salida_io.getvalue()
        self.assertIn("Bloque Replay: Proporcionalidad temporal (Opción b)", salida_texto)
        self.assertIn("Bloque Replay: Comparación con alternativas descartadas", salida_texto)
        self.assertIn("Opción b (Elegida: tope ciclo)", salida_texto)
        self.assertIn("Opción a (Descartada: corte acc)", salida_texto)
        self.assertIn("Opción c (Descartada: recorte)", salida_texto)

        # Verificamos exportación a CSV
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            ruta_csv = tmp.name

        try:
            escribir_csv(filas, ruta_csv)
            with open(ruta_csv, "r", encoding="utf-8") as f:
                lineas = f.readlines()
            self.assertGreater(len(lineas), 1)
            self.assertEqual(lineas[0].strip(), "seccion,medicion,resultado,unidad")
            contenido_csv = "".join(lineas)
            self.assertIn("250 acciones t=T/2", contenido_csv)
            self.assertIn("1000 acciones t=T/2", contenido_csv)
            self.assertIn("4000 acciones t=T/2", contenido_csv)
            self.assertIn("Opcion B", contenido_csv)
            self.assertIn("Opcion A", contenido_csv)
            self.assertIn("Opcion C", contenido_csv)
        finally:
            import os
            if os.path.exists(ruta_csv):
                os.remove(ruta_csv)

    def test_alternativa_a_ejecuta_eventos_posteriores_a_t(self):
        """FR-402: la opción elegida (b) nunca pasa de t; la alternativa a descartada termina con el reloj después de t."""
        import re
        filas = []
        replay.ejecutar(filas, imprimir=lambda s="": None)
        instantes = {}
        for _seccion, medicion, resultado, valor in filas:
            if resultado == "Instante alcanzado":
                m = re.match(r"1000 acciones t=(\d+) Opcion ([ABC])$", medicion)
                self.assertIsNotNone(m, medicion)
                instantes[m.group(2)] = (int(m.group(1)), valor)
        t_corte = instantes["B"][0]
        self.assertLessEqual(instantes["B"][1], t_corte)
        self.assertGreater(instantes["A"][1], t_corte)


if __name__ == "__main__":
    unittest.main()
