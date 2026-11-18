"""Pruebas de rendimiento proporcional (FR-412, SC-003, Principio VII).
Verifica que el costo computacional (medido en eventos procesados) para t = T / 2
sea estrictamente <= 0.55 * eventos totales en escalas de 250, 1 000 y 4 000 acciones.
"""
from __future__ import annotations

import tempfile
import unittest

from bench.juego import juego_sin_iniciar, servicio_sintetico
from Logica.GestorEventos import GestorEventos
from tests_labs.generador_partidas import generar_log_dto


class TestRendimientoReplay(unittest.TestCase):
    """FR-412, SC-003: Proporcionalidad temporal por conteo de eventos."""

    def _medir_eventos(self, num_acciones: int, semilla: int = 2026):
        with tempfile.TemporaryDirectory() as carpeta:
            servicio, cripta_id = servicio_sintetico(carpeta, enemigos=2)
            version_c = servicio.version_cripta(cripta_id)
            version_k = servicio.version_catalogo()

            log = generar_log_dto(
                num_acciones=num_acciones,
                semilla=semilla,
                id_cripta=cripta_id,
                version_cripta=version_c,
                version_catalogo=version_k,
            )

            # Instrumentamos GestorEventos.procesar_evento
            orig_procesar = GestorEventos.procesar_evento
            conteo = [0]

            def procesar_contando(inst, evento):
                conteo[0] += 1
                return orig_procesar(inst, evento)

            GestorEventos.procesar_evento = procesar_contando
            try:
                # 1. Reproducción completa
                conteo[0] = 0
                j_tot = juego_sin_iniciar(carpeta, enemigos=2)
                j_tot.repetirPartida(log)
                eventos_totales = conteo[0]
                t_total = j_tot.estadoJuego.reloj.tiempo_actual

                # 2. Reproducción acotada a t = T / 2
                conteo[0] = 0
                j_half = juego_sin_iniciar(carpeta, enemigos=2)
                t_corte = t_total // 2
                res = j_half.repetirPartida(log, hasta=t_corte)
                eventos_corte = conteo[0]
            finally:
                GestorEventos.procesar_evento = orig_procesar

            razon = eventos_corte / eventos_totales
            return eventos_totales, eventos_corte, razon, res.instante_alcanzado, t_corte

    def test_FR412_SC003_escala_250_acciones(self):
        tot, corte, razon, t_alcanzado, t_pedido = self._medir_eventos(250)
        self.assertLessEqual(t_alcanzado, t_pedido)
        self.assertLessEqual(razon, 0.55, f"Razón de eventos en 250 acciones excedió 0.55: {razon:.3f}")

    def test_FR412_SC003_escala_1000_acciones(self):
        tot, corte, razon, t_alcanzado, t_pedido = self._medir_eventos(1000)
        self.assertLessEqual(t_alcanzado, t_pedido)
        self.assertLessEqual(razon, 0.55, f"Razón de eventos en 1000 acciones excedió 0.55: {razon:.3f}")

    def test_FR412_SC003_escala_4000_acciones(self):
        tot, corte, razon, t_alcanzado, t_pedido = self._medir_eventos(4000)
        self.assertLessEqual(t_alcanzado, t_pedido)
        self.assertLessEqual(razon, 0.55, f"Razón de eventos en 4000 acciones excedió 0.55: {razon:.3f}")


if __name__ == "__main__":
    unittest.main()
