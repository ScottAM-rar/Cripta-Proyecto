"""Pruebas unitarias para _planificarSegmento (capacidad 004, plan.md §3).
Verifica la pasada 1: clasificación fiel sobre el log con instancia aislada
(sin heurísticas de texto sobre id de objeto) y resolución de acciones vigentes mediante pila local.
"""
from __future__ import annotations
import tempfile
import unittest

from DTO.EventoDTO import EventoDTO
from DTO.Objeto import PergaminoRetroceso, Antorcha
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from bench.juego import servicio_sintetico


class TestHistoriaSegmento(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.servicio, self.cripta_id = servicio_sintetico(
            self.temp_dir.name, enemigos=0, ancho=3, alto=3
        )
        self.juego = EstadoJuegoLogica(semilla=2026, comunicacion=self.servicio)
        self.juego.k_checkpoint = 10
        self.juego.iniciarJuego(self.cripta_id, semilla=2026)
        self.juego.ingresarEnSala(self.juego.estadoJuego.jugador.id_sala_actual)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _esperar(self, costo: int = 100) -> None:
        ev = EventoDTO(
            tiempo_ejecucion=costo,
            id_secuencia=0,
            actor=self.juego.estadoJuego.jugador,
            tipo_accion="ESPERAR",
            datos_extra=[],
        )
        res = self.juego.accionJugador(ev)
        self.assertTrue(res.exito)

    def _usar_pergamino(self, pergamino: PergaminoRetroceso) -> None:
        ev = EventoDTO(
            tiempo_ejecucion=100,
            id_secuencia=0,
            actor=self.juego.estadoJuego.jugador,
            tipo_accion="USAR_OBJETO",
            datos_extra=[pergamino],
        )
        res = self.juego.accionJugador(ev)
        self.assertTrue(res.exito)

    def test_secuencia_a1_a2_a3_p_a3p_a4(self):
        """Secuencia A1 A2 A3 P A3' A4 -> vigentes = [0, 1, 4, 5] (A1, A2, A3', A4)."""
        pergamino = PergaminoRetroceso("perg_1", "Pergamino", peso=0, valor=0)
        self.juego.estadoJuego.jugador.inventario.agregar_objeto(pergamino)

        self._esperar(100)               # A1 (idx 0)
        self._esperar(100)               # A2 (idx 1)
        self._esperar(100)               # A3 (idx 2)
        self._usar_pergamino(pergamino)  # P  (idx 3: revierte A3)
        self._esperar(100)               # A3' (idx 4)
        self._esperar(100)               # A4 (idx 5)

        vigentes = self.juego._planificarSegmento(self.juego.puntos_control[0])
        self.assertEqual(vigentes, [0, 1, 4, 5])

        # Verificar que el log contiene los 6 registros
        registros = self.juego.logEventos.obtener_registros_cronologicos()
        self.assertEqual(len(registros), 6)
        self.assertEqual(registros[0].tipo_accion, "ESPERAR")
        self.assertEqual(registros[1].tipo_accion, "ESPERAR")
        self.assertEqual(registros[2].tipo_accion, "ESPERAR")
        self.assertEqual(registros[3].tipo_accion, "USAR_OBJETO")
        self.assertEqual(registros[4].tipo_accion, "ESPERAR")
        self.assertEqual(registros[5].tipo_accion, "ESPERAR")

    def test_cursor_intercalado(self):
        """Los movimientos de cursor (costo 0) no entran a la pila y se ignoran en vigentes."""
        # Agregar objetos al inventario antes de empezar para que estén en el estado inicial
        inv = self.juego.estadoJuego.jugador.inventario
        pergamino = PergaminoRetroceso("perg_cursor", "Pergamino", peso=0, valor=0)
        inv.agregar_objeto(pergamino)
        inv.agregar_objeto(Antorcha("antorcha_1", "Antorcha", 1, 1))
        inv.agregar_objeto(Antorcha("antorcha_2", "Antorcha Extra", 1, 1))

        self._esperar(100)                           # A1 (idx 0)
        self.juego.siguienteObjetoInventario()       # Cursor SIGUIENTE (idx 1)
        self._esperar(100)                           # A2 (idx 2)
        self.juego.anteriorObjetoInventario()        # Cursor ANTERIOR (idx 3)
        self._esperar(100)                           # A3 (idx 4)
        self._usar_pergamino(pergamino)              # P revierte A3 (idx 5)
        self.juego.siguienteObjetoInventario()       # Cursor SIGUIENTE (idx 6)
        self._esperar(100)                           # A3' (idx 7)

        vigentes = self.juego._planificarSegmento(self.juego.puntos_control[0])
        # Pila desapila A3 (idx 4) tras P (idx 5); los cursores (idx 1, 3, 6) se omiten
        self.assertEqual(vigentes, [0, 2, 7])

    def test_pergamino_justo_despues_de_punto_control_con_poda(self):
        """Un pergamino inmediatamente posterior a un punto de control poda el punto
        y el segmento se evalúa desde el punto base superviviente."""
        self.juego.k_checkpoint = 2
        pergamino = PergaminoRetroceso("perg_poda", "Pergamino", peso=0, valor=0)
        self.juego.estadoJuego.jugador.inventario.agregar_objeto(pergamino)

        self._esperar(100)      # A1 (idx 0)
        self._esperar(100)      # A2 (idx 1) -> Se toma PuntoControl 1 en acc=2

        self.assertEqual(len(self.juego.puntos_control), 2)
        self.assertEqual(self.juego.puntos_control[1].acciones_linea_tiempo, 2)

        # Inmediatamente después del punto de control, usar pergamino
        self._usar_pergamino(pergamino)  # P revierte A2 (idx 2)

        # La poda de la partida viva elimina el PuntoControl 1 porque acciones_linea_tiempo bajó a 1
        self.assertEqual(len(self.juego.puntos_control), 1)
        self.assertEqual(self.juego.puntos_control[0].acciones_linea_tiempo, 0)

        # El jugador realiza A2'
        self._esperar(100)      # A2' (idx 3)

        vigentes = self.juego._planificarSegmento(self.juego.puntos_control[0])
        # A1 (0), A2 (1) desapilada por P (2), A2' (3) -> vigentes [0, 3]
        self.assertEqual(vigentes, [0, 3])

    def test_pergamino_despues_de_punto_control_sin_podar_punto_base(self):
        """Punto de control en acción 2; se ejecuta A3 (acción 3) y luego pergamino revierte A3.
        El PuntoControl 1 (acc=2) sobrevive y el segmento desde PuntoControl 1 queda limpio."""
        self.juego.k_checkpoint = 2
        pergamino = PergaminoRetroceso("perg_sobrevive", "Pergamino", peso=0, valor=0)
        self.juego.estadoJuego.jugador.inventario.agregar_objeto(pergamino)

        self._esperar(100)      # A1 (idx 0)
        self._esperar(100)      # A2 (idx 1) -> Se toma PuntoControl 1 en acc=2

        self.assertEqual(len(self.juego.puntos_control), 2)
        p1 = self.juego.puntos_control[1]
        self.assertEqual(p1.longitud_acciones_log, 2)

        # Acción posterior al punto de control
        self._esperar(100)      # A3 (idx 2)
        self.assertEqual(self.juego.acciones_linea_tiempo, 3)

        # Pergamino revierte A3
        self._usar_pergamino(pergamino)  # P revierte A3 (idx 3)
        self.assertEqual(self.juego.acciones_linea_tiempo, 2)

        # PuntoControl 1 sobrevive porque 2 <= 2
        self.assertEqual(len(self.juego.puntos_control), 2)
        self.assertIs(self.juego.puntos_control[1], p1)

        # Nueva acción A3'
        self._esperar(100)      # A3' (idx 4)

        # Planificar segmento desde PuntoControl 1 (inicio_log = 2)
        vigentes = self.juego._planificarSegmento(p1)
        # En el segmento [2..5): A3 (2) fue revertida por P (3), queda solo A3' (4)
        self.assertEqual(vigentes, [4])


if __name__ == "__main__":
    unittest.main()
