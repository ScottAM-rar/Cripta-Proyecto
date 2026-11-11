"""Pruebas de determinismo e invarianza de puntos de control.
FR-422, FR-423, FR-419, FR-424.
"""
from __future__ import annotations
import tempfile
import unittest

from DTO.EventoDTO import EventoDTO
from DTO.PuntoControlDTO import PuntoControlDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from bench.juego import servicio_sintetico


class TestDeterminismoPuntosControl(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _crear_juego(self, semilla: int = 2026, k: int = 10):
        servicio, cripta_id = servicio_sintetico(self.temp_dir.name, enemigos=2, ancho=4, alto=4)
        juego = EstadoJuegoLogica(semilla=semilla, comunicacion=servicio)
        juego.k_checkpoint = k
        juego.iniciarJuego(cripta_id, semilla=semilla)
        juego.ingresarEnSala(juego.estadoJuego.jugador.id_sala_actual)
        return juego

    def _accion_esperar(self, juego: EstadoJuegoLogica, costo: int = 100):
        ev = EventoDTO(
            tiempo_ejecucion=costo,
            id_secuencia=0,
            actor=juego.estadoJuego.jugador,
            tipo_accion="ESPERAR",
            datos_extra=[]
        )
        juego.accionJugador(ev)

    def test_invarianza_desenlace_distintos_k(self):
        """FR-423: Distintos valores de K producen exactamente el mismo resultado y estado final."""
        valores_k = [1, 5, 10, 50, 1000]
        estados_finales = []

        for k in valores_k:
            juego = self._crear_juego(semilla=2026, k=k)
            for _ in range(25):
                self._accion_esperar(juego)

            jugador = juego.estadoJuego.jugador
            estado_resumen = (
                jugador.vida_actual,
                jugador.id_sala_actual,
                juego.estadoJuego.puntaje,
                juego.accionesJugador,
                juego.estadoJuego.reloj.tiempo_actual,
                juego.gestorEventos.azar.getstate()
            )
            estados_finales.append(estado_resumen)

        # Todos deben ser exactamente idénticos al primero
        for i in range(1, len(estados_finales)):
            self.assertEqual(estados_finales[0], estados_finales[i], f"K={valores_k[i]} difiere de K={valores_k[0]}")

    def test_reanudacion_desde_punto_control_identico_resultado(self):
        """FR-422, Principio II: Reanudar desde punto de control genera idéntico resultado."""
        # 1. Ejecución continua de 15 acciones con K=5 (puntos en 0, 5, 10, 15)
        juego_continuo = self._crear_juego(semilla=2026, k=5)
        for _ in range(15):
            self._accion_esperar(juego_continuo)

        estado_continuo = juego_continuo.exportar_estado()

        # 2. Ejecución parcial hasta la acción 5 (punto 1)
        juego_reanudado = self._crear_juego(semilla=2026, k=5)
        for _ in range(5):
            self._accion_esperar(juego_reanudado)

        punto_5 = juego_reanudado.obtenerPuntoControlReciente(5)
        self.assertIsNotNone(punto_5)
        self.assertEqual(punto_5.acciones_linea_tiempo, 5)

        # 3. Restaurar desde punto 5 y ejecutar las 10 acciones restantes
        juego_reanudado.restaurarDesdePuntoControl(punto_5)
        for _ in range(10):
            self._accion_esperar(juego_reanudado)

        estado_reanudado = juego_reanudado.exportar_estado()

        # Comparar atributos clave del estado
        self.assertEqual(estado_reanudado.jugador.vida_actual, estado_continuo.jugador.vida_actual)
        self.assertEqual(estado_reanudado.jugador.id_sala_actual, estado_continuo.jugador.id_sala_actual)
        self.assertEqual(estado_reanudado.puntaje, estado_continuo.puntaje)
        self.assertEqual(estado_reanudado.acciones_jugador, estado_continuo.acciones_jugador)
        self.assertEqual(estado_reanudado.reloj.tiempo_actual, estado_continuo.reloj.tiempo_actual)
        self.assertEqual(estado_reanudado.estado_azar, estado_continuo.estado_azar)

    def test_servicio_expone_reanudacion_desde_punto_control(self):
        """FR-422, Principio IV: EstadoJuegoServicio expone restaurarDesdePuntoControl."""
        comunicacion, cripta_id = servicio_sintetico(self.temp_dir.name, enemigos=1, ancho=3, alto=3)
        servicio = EstadoJuegoServicio(semilla=2026, comunicacion=comunicacion, k_checkpoint=5)
        servicio.iniciarJuego(cripta_id, semilla=2026)
        servicio.obtenerSala(servicio.getJudador().id_sala_actual)

        for _ in range(10):
            ev = EventoDTO(100, 0, servicio.getJudador(), "ESPERAR", [])
            servicio.accionJugador(ev)

        punto = servicio.obtenerPuntoControlReciente(5)
        self.assertIsNotNone(punto)
        servicio.restaurarDesdePuntoControl(punto)
        self.assertEqual(servicio._estadoJuegoLogica.acciones_linea_tiempo, 5)

    def test_espaciado_minimo_tras_cambiar_k(self):
        """FR-419, FR-424: Tras cambiar K, dos puntos consecutivos distan al menos el nuevo K."""
        juego = self._crear_juego(semilla=2026, k=2)
        # 4 acciones con K=2 -> puntos en 0, 2, 4
        for _ in range(4):
            self._accion_esperar(juego)

        self.assertEqual([p.acciones_linea_tiempo for p in juego.puntos_control], [0, 2, 4])

        # Cambiamos K a 5
        juego.k_checkpoint = 5
        # Ejecutamos 4 acciones más (acciones 5, 6, 7, 8) -> no debe tomar punto aún (8 - 4 = 4 < 5)
        for _ in range(4):
            self._accion_esperar(juego)
        self.assertEqual([p.acciones_linea_tiempo for p in juego.puntos_control], [0, 2, 4])

        # Acción 9 -> 9 - 4 = 5 >= 5 -> debe tomar punto en acción 9
        self._accion_esperar(juego)
        self.assertEqual([p.acciones_linea_tiempo for p in juego.puntos_control], [0, 2, 4, 9])


if __name__ == "__main__":
    unittest.main()
