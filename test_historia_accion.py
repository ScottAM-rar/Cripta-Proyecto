"""Pruebas unitarias para la consulta histórica por número de acción `historia #k`.
User Story 2 (FR-429, FR-430, FR-435, FR-436) y equivalencia SC-002.
"""
from __future__ import annotations
import tempfile
import unittest

from DTO.EventoDTO import EventoDTO
from DTO.Objeto import PergaminoRetroceso
from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from bench.juego import servicio_sintetico


# ─────────────────────────────────────────────────────────────────────
#  Helpers reutilizables
# ─────────────────────────────────────────────────────────────────────

class _HistoriaAccionBase(unittest.TestCase):
    """Base con setup sintético compartido."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.servicio_cripta, self.cripta_id = servicio_sintetico(
            self.temp_dir.name, enemigos=1, ancho=3, alto=3
        )
        self.servicio = EstadoJuegoServicio(comunicacion=self.servicio_cripta)
        self.servicio.k_checkpoint = 5
        self.servicio.iniciarJuego(self.cripta_id, semilla=2026)
        self.logica = self.servicio._estadoJuegoLogica
        self.jugador = self.logica.estadoJuego.jugador
        self.servicio.obtenerSala(self.jugador.id_sala_actual)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _esperar(self, costo: int = 100) -> None:
        ev = EventoDTO(
            tiempo_ejecucion=costo,
            id_secuencia=0,
            actor=self.jugador,
            tipo_accion="ESPERAR",
            datos_extra=[],
        )
        res = self.servicio.accionJugador(ev)
        self.assertTrue(res.exito)

    def _usar_pergamino(self, pergamino: PergaminoRetroceso) -> None:
        ev = EventoDTO(
            tiempo_ejecucion=100,
            id_secuencia=0,
            actor=self.jugador,
            tipo_accion="USAR_OBJETO",
            datos_extra=[pergamino],
        )
        res = self.servicio.accionJugador(ev)
        self.assertTrue(res.exito)


# ─────────────────────────────────────────────────────────────────────
#  T013 – Casos de prueba para historia #k
# ─────────────────────────────────────────────────────────────────────

class TestHistoriaAccionBasico(_HistoriaAccionBase):
    """FR-429, FR-430: historia #1 equivale a historia <0> (estado inicial)."""

    def test_historia_1_equivale_a_historia_cero(self):
        """FR-430: historia #1 devuelve el estado inicial == historia <0>."""
        self._esperar(100)
        self._esperar(100)

        res_accion = self.servicio.consultarHistoria(accion=1)
        res_instante = self.servicio.consultarHistoria(instante=0)

        self.assertIsInstance(res_accion, ResumenEstadoDTO)
        self.assertEqual(res_accion.instante, res_instante.instante)
        self.assertEqual(res_accion.acciones_jugador, 0)
        self.assertEqual(res_accion.id_sala_jugador, res_instante.id_sala_jugador)
        self.assertEqual(res_accion.vida_jugador, res_instante.vida_jugador)
        self.assertEqual(res_accion.ataque_jugador, res_instante.ataque_jugador)
        self.assertEqual(res_accion.defensa_jugador, res_instante.defensa_jugador)
        self.assertEqual(res_accion.velocidad_jugador, res_instante.velocidad_jugador)
        self.assertEqual(res_accion.inventario_llaves, res_instante.inventario_llaves)
        self.assertEqual(res_accion.inventario_objetos, res_instante.inventario_objetos)
        self.assertEqual(res_accion.efectos_activos, res_instante.efectos_activos)
        self.assertEqual(res_accion.enemigos_sala, res_instante.enemigos_sala)

    def test_historia_N_mas_1_devuelve_estado_vivo(self):
        """FR-436: historia #(N+1) devuelve el estado actual."""
        self._esperar(100)
        self._esperar(100)
        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 2)

        res = self.servicio.consultarHistoria(accion=N + 1)
        self.assertEqual(res.acciones_jugador, N)
        self.assertEqual(res.instante, self.logica.estadoJuego.reloj.tiempo_actual)
        self.assertEqual(res.vida_jugador, self.jugador.vida_actual)

    def test_historia_mayor_N_mas_1_rechazada(self):
        """FR-436: historia #k con k > N+1 se rechaza."""
        self._esperar(100)
        N = self.logica.acciones_linea_tiempo

        with self.assertRaises(ValueError) as ctx:
            self.servicio.consultarHistoria(accion=N + 2)
        self.assertIn("aún no ha ocurrido", str(ctx.exception))
        self.assertIn(f"acciones vigentes: {N}", str(ctx.exception))


class TestHistoriaAccionValidacion(_HistoriaAccionBase):
    """FR-435, FR-437: Rechazo de k=0, negativos, floats, strings, bool."""

    def test_accion_cero_rechazada(self):
        """FR-435: historia #0 se rechaza."""
        self._esperar(100)
        with self.assertRaises(ValueError) as ctx:
            self.servicio.consultarHistoria(accion=0)
        self.assertIn("mayor o igual que 1", str(ctx.exception))

    def test_negativos_rechazados(self):
        """FR-435: historia #k con k < 0 se rechaza."""
        self._esperar(100)
        for k in (-1, -100):
            with self.assertRaises(ValueError):
                self.servicio.consultarHistoria(accion=k)

    def test_floats_rechazados(self):
        """FR-437: decimales se rechazan."""
        self._esperar(100)
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(accion=3.14)

    def test_strings_rechazados(self):
        """FR-437: strings se rechazan."""
        self._esperar(100)
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(accion="5")

    def test_bool_rechazado(self):
        """FR-437: bool se rechaza."""
        self._esperar(100)
        for val in (True, False):
            with self.assertRaises(ValueError):
                self.servicio.consultarHistoria(accion=val)


class TestHistoriaAccionEquivalencia(_HistoriaAccionBase):
    """SC-002: Para cada k en una partida de ~40 acciones con K=5, historia #k coincide
    campo por campo con historia <t> donde t es el instante de la decisión k."""

    def test_equivalencia_accion_instante_partida_40_acciones(self):
        """SC-002: Equivalencia historia #k == historia <t_k> para varios k."""
        self.servicio.k_checkpoint = 5

        # Registrar el instante justo antes de cada acción
        instantes_pre: list[int] = []
        for i in range(40):
            instantes_pre.append(self.logica.estadoJuego.reloj.tiempo_actual)
            self._esperar(50)

        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 40)

        # Probar en varios puntos de control y entre ellos
        puntos_a_probar = [1, 2, 5, 6, 10, 15, 20, 25, 30, 35, 40]
        for k in puntos_a_probar:
            t_k = instantes_pre[k - 1]  # instante justo antes de la acción k
            res_accion = self.servicio.consultarHistoria(accion=k)
            res_instante = self.servicio.consultarHistoria(instante=t_k)

            self.assertEqual(res_accion.acciones_jugador, k - 1,
                             f"k={k}: acciones_jugador")
            self.assertEqual(res_accion.id_sala_jugador, res_instante.id_sala_jugador,
                             f"k={k}: id_sala_jugador")
            self.assertEqual(res_accion.vida_jugador, res_instante.vida_jugador,
                             f"k={k}: vida_jugador")
            self.assertEqual(res_accion.ataque_jugador, res_instante.ataque_jugador,
                             f"k={k}: ataque_jugador")
            self.assertEqual(res_accion.defensa_jugador, res_instante.defensa_jugador,
                             f"k={k}: defensa_jugador")
            self.assertEqual(res_accion.velocidad_jugador, res_instante.velocidad_jugador,
                             f"k={k}: velocidad_jugador")
            self.assertEqual(res_accion.inventario_llaves, res_instante.inventario_llaves,
                             f"k={k}: inventario_llaves")
            self.assertEqual(res_accion.inventario_objetos, res_instante.inventario_objetos,
                             f"k={k}: inventario_objetos")
            self.assertEqual(res_accion.efectos_activos, res_instante.efectos_activos,
                             f"k={k}: efectos_activos")
            self.assertEqual(res_accion.enemigos_sala, res_instante.enemigos_sala,
                             f"k={k}: enemigos_sala")


class TestHistoriaAccionPergamino(_HistoriaAccionBase):
    """FR-434, Apéndice B Caso 2: A1 A2 A3 P A3' A4:
    historia #4 da el estado tras A3' (NO tras A3);
    #3 da el estado tras A2; N cuenta solo las acciones vigentes."""

    def test_secuencia_A1_A2_A3_P_A3p_A4(self):
        """El pergamino revierte A3; A3' y A4 reemplazan: N=4 vigentes."""
        pergamino = PergaminoRetroceso("perg_1", "Pergamino", peso=0, valor=0)
        self.jugador.inventario.agregar_objeto(pergamino)

        self._esperar(100)   # A1: t=100
        self._esperar(100)   # A2: t=200
        self._esperar(150)   # A3: t=350

        t_antes_A3 = 200     # el instante de la decisión de A3
        self._usar_pergamino(pergamino)  # P: revierte A3, reloj vuelve a 200

        self._esperar(50)    # A3': t=250
        self._esperar(50)    # A4: t=300

        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 4, "Debe haber 4 acciones vigentes: A1, A2, A3', A4")

        # #3 da el estado tras A2 (acciones=2)
        res3 = self.servicio.consultarHistoria(accion=3)
        self.assertEqual(res3.acciones_jugador, 2, "#3 debe tener acciones=2 (estado tras A2)")

        # #4 da el estado tras A3' (acciones=3), NO tras A3 original
        res4 = self.servicio.consultarHistoria(accion=4)
        self.assertEqual(res4.acciones_jugador, 3, "#4 debe tener acciones=3 (estado tras A3')")

        # #5 = N+1 = estado vivo
        res5 = self.servicio.consultarHistoria(accion=5)
        self.assertEqual(res5.acciones_jugador, 4)

        # #6 > N+1, se rechaza
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(accion=6)

    def test_pergamino_justo_despues_de_punto_control(self):
        """Pergamino inmediatamente después del punto de control K=5."""
        pergamino = PergaminoRetroceso("perg_2", "Pergamino", peso=0, valor=0)
        self.jugador.inventario.agregar_objeto(pergamino)

        # 5 acciones para generar un punto de control en accion=5
        for _ in range(5):
            self._esperar(100)

        # Acción 6
        self._esperar(100)

        # Usar pergamino: revierte acción 6, N baja de 6 a 5
        self._usar_pergamino(pergamino)
        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 5)

        # historia #5 da el estado tras acción 4 (acciones=4)
        res5 = self.servicio.consultarHistoria(accion=5)
        self.assertEqual(res5.acciones_jugador, 4)

        # historia #6 = N+1 = estado vivo
        res6 = self.servicio.consultarHistoria(accion=6)
        self.assertEqual(res6.acciones_jugador, 5)

        # historia #7 > N+1, se rechaza
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(accion=7)

    def test_pergamino_revierte_accion_posterior_al_ultimo_punto(self):
        """Revertir una acción que está después del último punto de control."""
        pergamino = PergaminoRetroceso("perg_3", "Pergamino", peso=0, valor=0)
        self.jugador.inventario.agregar_objeto(pergamino)

        # 7 acciones (K=5: punto en 0 y 5)
        for _ in range(7):
            self._esperar(100)

        N_antes = self.logica.acciones_linea_tiempo
        self.assertEqual(N_antes, 7)

        # Usar pergamino: revierte acción 7
        self._usar_pergamino(pergamino)
        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 6)

        # Ejecutar acción 7'
        self._esperar(50)
        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 7)

        # historia #7 da el estado tras la acción 6 (ANTES de A7')
        res7 = self.servicio.consultarHistoria(accion=7)
        self.assertEqual(res7.acciones_jugador, 6)


class TestHistoriaAccionPartidaCero(_HistoriaAccionBase):
    """FR-438: Partida con N=0 (sin acciones): #1 es estado inicial, #2 se rechaza."""

    def test_partida_sin_acciones_accion_1_es_inicial(self):
        """FR-438: historia #1 con N=0 devuelve el estado inicial."""
        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 0)

        # #1 = N+1 = estado vivo (que es el estado inicial)
        res = self.servicio.consultarHistoria(accion=1)
        self.assertIsInstance(res, ResumenEstadoDTO)
        self.assertEqual(res.acciones_jugador, 0)
        self.assertEqual(res.instante, 0)

    def test_partida_sin_acciones_accion_2_rechazada(self):
        """FR-438: historia #2 con N=0 se rechaza."""
        N = self.logica.acciones_linea_tiempo
        self.assertEqual(N, 0)

        with self.assertRaises(ValueError) as ctx:
            self.servicio.consultarHistoria(accion=2)
        self.assertIn("aún no ha ocurrido", str(ctx.exception))


class TestHistoriaAccionPartidaTerminada(_HistoriaAccionBase):
    """FR-429: Partida terminada: #N+1 devuelve el estado final."""

    def test_partida_terminada_N_mas_1_devuelve_estado_final(self):
        """FR-429: En una partida terminada, historia #(N+1) da el estado final."""
        self._esperar(100)
        self._esperar(100)
        N = self.logica.acciones_linea_tiempo

        # Forzar terminación
        self.logica.fin = True
        self.logica.motivoFin = "El jugador ha muerto"

        res = self.servicio.consultarHistoria(accion=N + 1)
        self.assertEqual(res.acciones_jugador, N)
        self.assertTrue(res.partida_terminada)

    def test_partida_terminada_acepta_consultas_intermedias(self):
        """FR-429: En una partida terminada, historia #k con k < N+1 sigue funcionando."""
        self._esperar(100)
        self._esperar(100)

        self.logica.fin = True
        self.logica.motivoFin = "El jugador ha muerto"

        res1 = self.servicio.consultarHistoria(accion=1)
        self.assertEqual(res1.acciones_jugador, 0)
        self.assertFalse(res1.partida_terminada)

        res2 = self.servicio.consultarHistoria(accion=2)
        self.assertEqual(res2.acciones_jugador, 1)


class TestControladorNoPenetraCapaServicio(unittest.TestCase):
    """Principio IV: ningún archivo de Controlador/ debe referenciar atributos
    con guion bajo del servicio (grep sobre el código fuente)."""

    def test_controlador_no_accede_atributos_privados_del_servicio(self):
        """Verifica que ControladorJuego.py y Vista.py no usan servicio._xxx."""
        import os
        controlador_dir = os.path.join(
            os.path.dirname(__file__), "Controlador"
        )
        for archivo in os.listdir(controlador_dir):
            if not archivo.endswith(".py"):
                continue
            ruta = os.path.join(controlador_dir, archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            lineas = contenido.splitlines()
            for i, linea in enumerate(lineas, 1):
                # Buscar patrones como servicio._algo o self.servicio._algo
                if "servicio._" in linea and not linea.strip().startswith("#"):
                    self.fail(
                        f"Controlador/{archivo}:{i} accede a un atributo privado del servicio: {linea.strip()}"
                    )


if __name__ == "__main__":
    unittest.main()
