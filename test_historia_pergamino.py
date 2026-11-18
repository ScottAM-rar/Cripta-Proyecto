"""Pruebas unitarias para la coherencia de la consulta histórica con el pergamino de retroceso.
User Story 4 (FR-434, plan.md §4, T021 a T023).

Garantiza:
- Las acciones revertidas desaparecen de la línea de tiempo vigente (FR-434).
- N cuenta exclusivamente las acciones vigentes.
- Los instantes que solo existieron en la rama revertida se rechazan como futuros (FR-433).
- Usar un pergamino real inmediatamente después de una consulta historia funciona correctamente (desapila sin corrupción).
- Varios pergaminos consecutivos desapilan sin errores y conservan la coherencia histórica.
- Pergamino justo después de un punto de control y en múltiplos exactos de K (puntos podados).
- Consulta de k que coincide exactamente con un punto de control.
- Comparación contra oráculo independiente: instantáneas capturadas en vivo antes de cada acción.
"""
from __future__ import annotations
from dataclasses import asdict
import tempfile
import unittest

from DTO.EventoDTO import EventoDTO
from DTO.Objeto import PergaminoRetroceso
from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from bench.juego import servicio_sintetico


class TestHistoriaPergamino(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.servicio_cripta, self.cripta_id = servicio_sintetico(
            self.temp_dir.name, enemigos=1, ancho=4, alto=4
        )
        self.servicio = EstadoJuegoServicio(comunicacion=self.servicio_cripta)
        self.servicio.k_checkpoint = 5
        self.servicio.iniciarJuego(self.cripta_id, semilla=999)
        self.logica = self.servicio._estadoJuegoLogica
        self.jugador = self.logica.estadoJuego.jugador
        self.servicio.obtenerSala(self.jugador.id_sala_actual)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _esperar(self, costo: int = 100) -> None:
        ev = EventoDTO(costo, 0, self.jugador, "ESPERAR", [])
        res = self.servicio.accionJugador(ev)
        self.assertTrue(res.exito)

    def _usar_pergamino(self, pergamino: PergaminoRetroceso) -> None:
        ev = EventoDTO(100, 0, self.jugador, "USAR_OBJETO", [pergamino])
        res = self.servicio.accionJugador(ev)
        self.assertTrue(res.exito)

    def test_revertir_3_de_10_acciones_invisibilidad_revertidas_y_linea_vigente(self):
        """Jugar 10 acciones, revertir 3 con pergaminos reales.
        Verificar que N=7 vigentes, las acciones revertidas no aparecen y cada k vigente
        coincide campo por campo con el oráculo capturado en vivo (FR-434)."""
        oraculo_vivo: dict[int, ResumenEstadoDTO] = {}

        # Equipar 3 pergaminos
        pergs = [PergaminoRetroceso(f"p_{i}", f"Pergamino {i}", 0, 0) for i in range(3)]
        for p in pergs:
            self.jugador.inventario.agregar_objeto(p)

        # Jugar 10 acciones, registrando el estado justo antes de cada una
        for i in range(1, 11):
            reloj_turno = self.logica.estadoJuego.reloj.tiempo_actual
            oraculo_vivo[i] = self.logica._extraerResumenEstadoActual(reloj_turno, i - 1)
            self._esperar(100)

        self.assertEqual(self.logica.acciones_linea_tiempo, 10)
        reloj_antes_revertir = self.logica.estadoJuego.reloj.tiempo_actual

        # Revertir 3 acciones
        for p in pergs:
            self._usar_pergamino(p)

        self.assertEqual(self.logica.acciones_linea_tiempo, 7, "N debe ser 7 tras revertir 3 acciones")
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 700)

        # historia #k para todo k entre 1 y 7 debe coincidir exactamente con el oráculo vivo
        for k in range(1, 8):
            res_k = self.servicio.consultarHistoria(accion=k)
            esperado = oraculo_vivo[k]
            self.assertEqual(asdict(res_k), asdict(esperado), f"Fallo en k={k}")

        # historia #8 (N+1) es el estado actual vivo
        res_8 = self.servicio.consultarHistoria(accion=8)
        self.assertEqual(res_8.acciones_jugador, 7)
        self.assertEqual(res_8.instante, 700)

        # historia #9 (> N+1) se rechaza
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(accion=9)

    def test_instante_revertido_rechazado_como_futuro(self):
        """Un instante que solo existió en la rama revertida es posterior al reloj actual y se rechaza (FR-433)."""
        pergamino = PergaminoRetroceso("perg_rev", "Pergamino", 0, 0)
        self.jugador.inventario.agregar_objeto(pergamino)

        self._esperar(100)  # A1: t=100
        self._esperar(200)  # A2: t=300
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 300)

        # Revertir A2
        self._usar_pergamino(pergamino)
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 100)

        # t=300 solo existió en la rama revertida; ahora reloj_actual=100 -> debe rechazarse
        with self.assertRaises(ValueError) as ctx:
            self.servicio.consultarHistoria(instante=300)
        self.assertIn("aún no ha ocurrido", str(ctx.exception))

        # t=200 tampoco existe en la línea vigente
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(instante=200)

        # t=100 y t=0 son válidos
        self.assertEqual(self.servicio.consultarHistoria(instante=100).acciones_jugador, 1)
        self.assertEqual(self.servicio.consultarHistoria(instante=0).acciones_jugador, 0)

    def test_usar_pergamino_despues_de_consulta_historia(self):
        """T023: Consultar historia deja RetrocesoLogica intacto; el pergamino desapila correctamente."""
        pergamino = PergaminoRetroceso("perg_post", "Pergamino", 0, 0)
        self.jugador.inventario.agregar_objeto(pergamino)

        self._esperar(100)  # A1: t=100
        self._esperar(100)  # A2: t=200

        # Ejecutar varias consultas de historia intermedias
        _ = self.servicio.consultarHistoria(instante=100)
        _ = self.servicio.consultarHistoria(accion=1)
        _ = self.servicio.consultarHistoria(accion=2)

        # Usar el pergamino: debe desapilar A2 sin fallos
        self._usar_pergamino(pergamino)
        self.assertEqual(self.logica.acciones_linea_tiempo, 1)
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 100)

        # Las consultas posteriores siguen siendo coherentes
        res1 = self.servicio.consultarHistoria(accion=1)
        self.assertEqual(res1.acciones_jugador, 0)
        res2 = self.servicio.consultarHistoria(accion=2)  # N+1 = estado vivo
        self.assertEqual(res2.acciones_jugador, 1)

    def test_pergamino_justo_despues_de_punto_control_y_multiplo_de_k(self):
        """K=5: Probar pergamino cuando acciones_linea_tiempo está en múltiplo de K (K=5)
        y cuando revierte la primera acción después del punto (K=5 -> acción 6 revertida)."""
        pergamino1 = PergaminoRetroceso("perg_k1", "Pergamino", 0, 0)
        pergamino2 = PergaminoRetroceso("perg_k2", "Pergamino", 0, 0)
        self.jugador.inventario.agregar_objeto(pergamino1)
        self.jugador.inventario.agregar_objeto(pergamino2)

        # 5 acciones: se genera punto en 5
        for _ in range(5):
            self._esperar(100)
        self.assertEqual(self.logica.acciones_linea_tiempo, 5)
        self.assertEqual(len(self.logica.puntos_control), 2)  # punto 0 y punto 1 (acciones=5)

        # Acción 6 (primera acción tras el punto)
        self._esperar(100)
        self.assertEqual(self.logica.acciones_linea_tiempo, 6)

        # Revertir acción 6: N vuelve a 5, punto en 5 se conserva
        self._usar_pergamino(pergamino1)
        self.assertEqual(self.logica.acciones_linea_tiempo, 5)
        self.assertEqual(len(self.logica.puntos_control), 2)

        # Revertir acción 5 (en múltiplo exacto de K): N baja a 4, el punto en 5 debe podarse
        self._usar_pergamino(pergamino2)
        self.assertEqual(self.logica.acciones_linea_tiempo, 4)
        self.assertEqual(len(self.logica.puntos_control), 1, "El punto de control en 5 debe haber sido podado")

        # Consultar historia #4 (estado tras acción 3) y #5 (estado tras acción 4 = actual)
        res4 = self.servicio.consultarHistoria(accion=4)
        self.assertEqual(res4.acciones_jugador, 3)
        res5 = self.servicio.consultarHistoria(accion=5)
        self.assertEqual(res5.acciones_jugador, 4)

    def test_consulta_k_que_cae_exactamente_en_punto_de_control(self):
        """Consulta #k donde k - 1 coincide exactamente con un punto de control (j=0)."""
        # K=5: Puntos en acciones 0 y 5.
        # #6 consulta el estado justo antes de la acción 6 (es decir, tras 5 acciones = punto de control 1).
        for _ in range(7):
            self._esperar(100)

        # #6 tiene k-1 = 5, que es exactamente el punto 1
        res6 = self.servicio.consultarHistoria(accion=6)
        self.assertEqual(res6.acciones_jugador, 5)
        self.assertEqual(res6.instante, 500)

        # #1 tiene k-1 = 0, que es exactamente el punto 0
        res1 = self.servicio.consultarHistoria(accion=1)
        self.assertEqual(res1.acciones_jugador, 0)
        self.assertEqual(res1.instante, 0)


if __name__ == "__main__":
    unittest.main()
