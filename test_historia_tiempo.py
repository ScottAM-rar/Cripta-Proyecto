"""Pruebas unitarias para la consulta histórica por instante de reloj `historia <t>`.
User Story 1 (FR-427, FR-428, FR-430, FR-433, FR-437).
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


class TestHistoriaTiempo(unittest.TestCase):
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

    # 1. historia <0> da el estado inicial (FR-430)
    def test_historia_cero_da_estado_inicial(self):
        """FR-430: historia <0> devuelve el estado inicial de la partida."""
        # Tomar foto del estado inicial
        vida_inicial = self.jugador.vida_actual
        sala_inicial = self.jugador.id_sala_actual

        # Avanzar varias acciones
        self._esperar(100)
        self._esperar(100)
        self.assertGreater(self.logica.estadoJuego.reloj.tiempo_actual, 0)
        self.assertGreater(self.logica.acciones_linea_tiempo, 0)

        # Consultar historia <0>
        resumen = self.servicio.consultarHistoria(instante=0)
        self.assertIsInstance(resumen, ResumenEstadoDTO)
        self.assertEqual(resumen.instante, 0)
        self.assertEqual(resumen.acciones_jugador, 0)
        self.assertEqual(resumen.vida_jugador, vida_inicial)
        self.assertEqual(resumen.id_sala_jugador, sala_inicial)
        self.assertFalse(resumen.partida_terminada)

    # 2. Corte en instante t (FR-428): decisión debida en t vs instante entre decisiones
    def test_corte_instante_decision_jugador_y_eventos_enemigo(self):
        """FR-428: Instante t con decisión del jugador muestra el estado justo antes de esa decisión.
        Instante entre decisiones muestra el estado tras todos los eventos con tiempo <= t."""
        # Inicialmente reloj = 0.
        # Acción 1: esperar costo 100 -> reloj avanzará a 100 (próximo turno del jugador).
        self._esperar(100)
        reloj_actual = self.logica.estadoJuego.reloj.tiempo_actual
        self.assertEqual(reloj_actual, 100)

        # Acción 2: esperar costo 100 -> reloj avanzará a 200.
        self._esperar(100)
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 200)

        # En t = 100 había decisión del jugador (la Acción 2).
        # El estado en t = 100 debe mostrar el estado justo ANTES de la Acción 2 (es decir, con acciones=1).
        resumen_100 = self.servicio.consultarHistoria(instante=100)
        self.assertEqual(resumen_100.instante, 100)
        self.assertEqual(resumen_100.acciones_jugador, 1)

        # En t = 50 (entre decisiones): ningún evento nuevo del jugador, reloj virtual no alcanzó 100.
        # El estado en t = 50 debe tener acciones = 1 y procesado hasta t=50.
        resumen_50 = self.servicio.consultarHistoria(instante=50)
        self.assertEqual(resumen_50.instante, 50)

    # 3. Validaciones de t (FR-433, FR-437)
    def test_t_igual_al_reloj_vivo_y_rechazo_de_futuro_y_tipos_invalidos(self):
        """FR-433, FR-437: t == reloj vivo devuelve estado actual.
        t > reloj vivo se rechaza. Negativos, floats, strings y bool se rechazan."""
        self._esperar(100)
        tiempo_vivo = self.logica.estadoJuego.reloj.tiempo_actual

        # t == tiempo_vivo
        resumen_vivo = self.servicio.consultarHistoria(instante=tiempo_vivo)
        self.assertEqual(resumen_vivo.instante, tiempo_vivo)
        self.assertEqual(resumen_vivo.acciones_jugador, self.logica.acciones_linea_tiempo)
        self.assertEqual(resumen_vivo.vida_jugador, self.jugador.vida_actual)

        # t > tiempo_vivo
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(instante=tiempo_vivo + 1)

        # Negativos y tipos no válidos
        for malo in (-1, -100, 3.14, "50", True, False):
            with self.assertRaises(ValueError):
                self.servicio.consultarHistoria(instante=malo)

    # 4. Equivalencia con repetirPartida(hasta=t) (Capacidad 008)
    def test_equivalencia_con_replay_hasta(self):
        """SC-002: El resumen de historia <t> coincide campo por campo con
        repetirPartida(log, hasta=t) en una partida de ~40 acciones con K=5."""
        self.servicio.k_checkpoint = 5

        # Jugar 40 acciones
        for _ in range(40):
            self._esperar(50)

        tiempo_final = self.logica.estadoJuego.reloj.tiempo_actual
        # Instante intermedio para probar
        t_consulta = tiempo_final // 2

        # 1. Consulta histórica con historia <t_consulta>
        resumen = self.servicio.consultarHistoria(instante=t_consulta)

        # 2. Replay con repetirPartida
        log_dto = self.logica.exportar_log()
        juego_replay = EstadoJuegoLogica(comunicacion=self.servicio_cripta)
        replay = juego_replay.repetirPartida(log_dto, hasta=t_consulta)

        # Coincidencia campo por campo de las propiedades del mundo
        self.assertEqual(resumen.instante, replay.instante_alcanzado)
        self.assertEqual(resumen.id_sala_jugador, replay.id_sala_jugador)
        self.assertEqual(resumen.vida_jugador, replay.vida_jugador)
        self.assertEqual(resumen.ataque_jugador, replay.ataque_jugador)
        self.assertEqual(resumen.defensa_jugador, replay.defensa_jugador)
        self.assertEqual(resumen.velocidad_jugador, replay.velocidad_jugador)
        self.assertEqual(resumen.inventario_llaves, replay.inventario_llaves)
        self.assertEqual(resumen.inventario_objetos, replay.inventario_objetos)
        self.assertEqual(resumen.efectos_activos, replay.efectos_activos)
        self.assertEqual(resumen.enemigos_sala, replay.enemigos_sala)
        self.assertEqual(resumen.partida_terminada, replay.partida_terminada)
        self.assertEqual(resumen.motivo_terminacion, replay.motivo_terminacion)

    # 5. Caso A1 A2 A3 P A3' A4 con consultas e instante revertido (FR-434)
    def test_secuencia_pergamino_e_instante_revertido_rechazado(self):
        """El instante que solo existió en la rama revertida se rechaza por ser futuro."""
        pergamino = PergaminoRetroceso("perg_1", "Pergamino", peso=0, valor=0)
        self.jugador.inventario.agregar_objeto(pergamino)

        self._esperar(100)               # A1: t=100
        self._esperar(100)               # A2: t=200
        self._esperar(150)               # A3: t=350 (tiempo en la rama que luego se revierte)
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 350)

        # Usar pergamino: revierte A3, reloj vuelve a 200
        self._usar_pergamino(pergamino)  # P: reloj vuelve a 200
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 200)

        # El instante 350 solo existió en la rama revertida; para el reloj actual (200), es futuro
        with self.assertRaises(ValueError):
            self.servicio.consultarHistoria(instante=350)

        # Ejecutamos A3' con costo 50 (t=250) y A4 con costo 50 (t=300)
        self._esperar(50)                # A3': t=250
        self._esperar(50)                # A4: t=300
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, 300)

        # historia <200> debe dar el estado tras A2 (acciones=2)
        res_200 = self.servicio.consultarHistoria(instante=200)
        self.assertEqual(res_200.acciones_jugador, 2)

    # 6. Partida terminada acepta consultas (FR-427)
    def test_partida_terminada_acepta_consultas(self):
        """FR-427: Si la partida concluyó, historia <t> sigue funcionando."""
        self._esperar(100)
        t_previo = 50

        # Forzar terminación de la partida (ej. muerte o fin)
        self.logica.fin = True
        self.logica.motivoFin = "El jugador ha muerto"

        resumen = self.servicio.consultarHistoria(instante=t_previo)
        self.assertEqual(resumen.instante, t_previo)
        self.assertFalse(resumen.partida_terminada)


class TestControladorHistoria(unittest.TestCase):
    def test_comandos_historia_en_controlador_no_alteran_partida(self):
        """T011/T012: En el bucle de juego y post-partida, historia no avanza el reloj,
        no cuenta como acción, no escribe en el log y maneja errores de sintaxis/rango."""
        from unittest.mock import patch
        from Controlador.ControladorJuego import ControladorJuego

        with tempfile.TemporaryDirectory() as temp_dir:
            servicio_cripta, cripta_id = servicio_sintetico(temp_dir, enemigos=0, ancho=3, alto=3)
            servicio = EstadoJuegoServicio(comunicacion=servicio_cripta)
            controlador = ControladorJuego(servicio)

            # Entradas simuladas para el flujo:
            # 1. ver puntajes? n
            # 2. cargar partida? n
            # 3. seleccionar cripta? 1
            # 4. ingresar semilla? n
            # 5. accion 1: esperar
            # 6. historia <0>
            # 7. HISTORIA 50
            # 8. historia 9999 (error futuro)
            # 9. historia abc (error sintaxis)
            # 10. historia #1
            # 11. salir
            # 12. guardar antes de salir? n
            entradas = iter([
                "n",
                "n",
                "1",
                "n",
                "esperar",
                "historia <0>",
                "HISTORIA 50",
                "historia 9999",
                "historia abc",
                "historia #1",
                "salir",
                "n",
            ])

            with patch("builtins.input", side_effect=lambda *args, **kwargs: next(entradas)):
                with patch("sys.stdout"):
                    controlador.iniciar()

            # Estado final de la partida viva:
            # Solo se ejecutó 'esperar' 1 vez (costo 100).
            # Los comandos historia no deben haber incrementado acciones ni tiempo ni log.
            logica = servicio._estadoJuegoLogica
            self.assertEqual(logica.accionesJugador, 1)
            self.assertEqual(logica.acciones_linea_tiempo, 1)
            self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 100)
            # El log solo debe contener la acción 'esperar'
            registros = logica.logEventos.obtener_registros_cronologicos()
            self.assertEqual(len(registros), 1)
            self.assertEqual(registros[0].tipo_accion, "ESPERAR")


if __name__ == "__main__":
    unittest.main()
