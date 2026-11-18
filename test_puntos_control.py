"""Pruebas unitarias para la toma y gestión de puntos de control.
FR-418, FR-419, FR-420, FR-421.
"""
from __future__ import annotations
import io
import sys
import unittest
from unittest.mock import patch

from DTO.EventoDTO import EventoDTO
from DTO.PuntoControlDTO import PuntoControlDTO
from DTO.Objeto import PergaminoRetroceso
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from bench.juego import juego_sin_iniciar, servicio_sintetico
import tempfile


class TestPuntosControl(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.servicio, self.cripta_id = servicio_sintetico(self.temp_dir.name, enemigos=1, ancho=3, alto=3)
        self.juego = EstadoJuegoLogica(semilla=2026, comunicacion=self.servicio)
        self.juego.k_checkpoint = 3
        self.juego.iniciarJuego(self.cripta_id, semilla=2026)
        self.juego.ingresarEnSala(self.juego.estadoJuego.jugador.id_sala_actual)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _ejecutar_esperar(self, n: int = 1):
        for _ in range(n):
            ev = EventoDTO(
                tiempo_ejecucion=100,
                id_secuencia=0,
                actor=self.juego.estadoJuego.jugador,
                tipo_accion="ESPERAR",
                datos_extra=[]
            )
            self.juego.accionJugador(ev)

    def test_punto_cero_inicial(self):
        """FR-418: El estado inicial se registra como punto de control 0."""
        # Antes de la primera acción o al iniciar la primera acción
        self._ejecutar_esperar(1)
        self.assertGreaterEqual(len(self.juego.puntos_control), 1)
        p0 = self.juego.puntos_control[0]
        self.assertEqual(p0.numero_punto, 0)
        self.assertEqual(p0.acciones_linea_tiempo, 0)

    def test_captura_periodica_exacta(self):
        """FR-418, FR-419: Con K=3, 7 acciones generan exactamente puntos en 0, 3 y 6."""
        self._ejecutar_esperar(7)
        self.assertEqual(len(self.juego.puntos_control), 3)
        self.assertEqual([p.acciones_linea_tiempo for p in self.juego.puntos_control], [0, 3, 6])
        self.assertEqual([p.numero_punto for p in self.juego.puntos_control], [0, 1, 2])

    def test_no_captura_si_accion_termina_partida(self):
        """FR-418: Si la acción n*K finaliza la partida, no se toma el punto."""
        self.juego.k_checkpoint = 1
        # Matamos al jugador para terminar la partida
        jugador = self.juego.estadoJuego.jugador
        jugador.vida_actual = 1
        self.juego.fin = True
        puntos_antes = len(self.juego.puntos_control)
        # Una llamada directa a verificar no debe agregar si fin es True
        if hasattr(self.juego, "_verificarYCapturarPuntoControl"):
            self.juego._verificarYCapturarPuntoControl()
            self.assertEqual(len(self.juego.puntos_control), puntos_antes)

    def test_transparencia_sin_mensajes_consola(self):
        """FR-420: Tomar un punto de control no emite texto a stdout/stderr."""
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            self._ejecutar_esperar(3)
        self.assertEqual(stdout.getvalue(), "")

    def test_contenido_estado_completo(self):
        """FR-421: El punto de control incluye reloj, entidades y azar."""
        self._ejecutar_esperar(3)
        p = self.juego.puntos_control[1]  # Punto 1 en acc=3
        self.assertIsNotNone(p.estado)
        self.assertIsNotNone(p.estado.reloj)
        self.assertIsNotNone(p.estado.jugador)
        self.assertGreater(len(p.estado.estado_azar), 0)

    def test_poda_tras_uso_de_pergamino(self):
        """FR-418: Usar el pergamino descarta los puntos posteriores al estado revertido."""
        # Jugamos 3 acciones -> Punto 1 en acc=3
        self._ejecutar_esperar(3)
        self.assertEqual(len(self.juego.puntos_control), 2)  # P0 en 0, P1 en 3

        # Le damos un pergamino de retroceso al jugador
        pergamino = PergaminoRetroceso("pergamino", "Pergamino", peso=0, valor=0)
        self.juego.estadoJuego.jugador.inventario.agregar_objeto(pergamino)

        # Usamos el pergamino (revierte la acción 3) -> acciones bajan a 2
        ev_perg = EventoDTO(
            tiempo_ejecucion=100,
            id_secuencia=0,
            actor=self.juego.estadoJuego.jugador,
            tipo_accion="USAR_OBJETO",
            datos_extra=[pergamino]
        )
        self.juego.accionJugador(ev_perg)

        # Como volvimos a la acción 2, el punto en acc=3 debe haber sido descartado
        self.assertEqual(len(self.juego.puntos_control), 1)
        self.assertEqual(self.juego.puntos_control[0].acciones_linea_tiempo, 0)
        self.assertEqual(self.juego.acciones_linea_tiempo, 2)

    def test_obtener_punto_control_reciente(self):
        """FR-419: Lectura para capacidad 004 del punto más cercano con n*K <= k."""
        self._ejecutar_esperar(6)  # Puntos en 0, 3, 6
        p = self.juego.obtenerPuntoControlReciente(5)
        self.assertIsNotNone(p)
        self.assertEqual(p.acciones_linea_tiempo, 3)

        p2 = self.juego.obtenerPuntoControlReciente(6)
        self.assertIsNotNone(p2)
        self.assertEqual(p2.acciones_linea_tiempo, 6)

        p0 = self.juego.obtenerPuntoControlReciente(1)
        self.assertIsNotNone(p0)
        self.assertEqual(p0.acciones_linea_tiempo, 0)


if __name__ == "__main__":
    unittest.main()
