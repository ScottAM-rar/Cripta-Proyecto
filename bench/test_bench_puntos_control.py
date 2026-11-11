"""Prueba del bloque de benchmark puntos_control y exportación a CSV (FR-426, Principio VII).
"""
from __future__ import annotations
import io
import os
import tempfile
import unittest

from bench import puntos_control
from bench.salida import escribir_csv


class TestBenchPuntosControl(unittest.TestCase):
    """Verifica que puntos_control.ejecutar corre programáticamente y produce métricas válidas."""

    def test_ejecutar_benchmark_puntos_control(self):
        filas = []
        salida_io = io.StringIO()
        cumple = puntos_control.ejecutar(filas, imprimir=lambda s="": salida_io.write(s + "\n"), acciones=300)

        self.assertTrue(cumple, "El benchmark de puntos de control debe cumplir con el límite de 20 ms con K=1")
        self.assertGreater(len(filas), 0)

        salida_texto = salida_io.getvalue()
        self.assertIn("Puntos de control", salida_texto)
        self.assertIn("Alternativa B", salida_texto)
        self.assertIn("Alternativa A", salida_texto)
        self.assertIn("Alternativa C", salida_texto)

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
            self.assertIn("Alternativa B", contenido_csv)
            self.assertIn("Alternativa A", contenido_csv)
            self.assertIn("Alternativa C", contenido_csv)
        finally:
            if os.path.exists(ruta_csv):
                os.remove(ruta_csv)


if __name__ == "__main__":
    unittest.main()
