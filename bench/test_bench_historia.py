"""Prueba del bloque de benchmark historia (FR-442, SC-006, Principio VII).
"""
from __future__ import annotations
import io
import unittest

from bench import historia


class TestBenchHistoria(unittest.TestCase):
    """Verifica que historia.ejecutar corre programáticamente con una partida reducida
    y produce métricas válidas conformes a FR-442."""

    def test_ejecutar_benchmark_historia(self):
        filas: list = []
        salida_io = io.StringIO()
        cumple = historia.ejecutar(filas, imprimir=lambda s="": salida_io.write(s + "\n"), acciones=300)

        self.assertTrue(cumple, "El benchmark de historia debe cumplir el límite de 50 ms (FR-442)")
        self.assertGreater(len(filas), 0)

        salida_texto = salida_io.getvalue()
        self.assertIn("Línea de tiempo", salida_texto)
        self.assertIn("Alternativa C", salida_texto)
        self.assertIn("Búsqueda binaria vs lineal", salida_texto)

        # Comprobar que todas las secciones esperadas existen en filas
        conceptos = [f[1] for f in filas]
        self.assertTrue(any("K=10" in c for c in conceptos))
        self.assertTrue(any("K=50" in c for c in conceptos))
        self.assertTrue(any("K=100" in c for c in conceptos))
        self.assertTrue(any("Alternativa C" in c for c in conceptos))
        self.assertTrue(any("Búsqueda binaria vs lineal" in c for c in conceptos))
        self.assertTrue(any("Hacia adelante vs hacia atrás" in c for c in conceptos))

    def test_resumen_tiempos_respeta_mediana_entre_minimo_y_maximo(self):
        """La fila 'mediana (mín – máx)' debe cumplir mín <= mediana <= máx (antes se pasaba el p95 como mínimo)."""
        mediana, minimo, maximo = historia._resumen_tiempos([9.0, 3.0, 7.0, 5.0, 100.0, 4.0, 6.0, 8.0, 2.0, 50.0])
        self.assertEqual((minimo, maximo), (2.0, 100.0))
        self.assertLessEqual(minimo, mediana)
        self.assertLessEqual(mediana, maximo)
        self.assertEqual(historia._resumen_tiempos([]), (0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
