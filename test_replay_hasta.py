"""Pruebas unitarias para la capacidad de reproducción acotada (--replay PARTIDA.log --hasta t).
Cubre US1 (corte temporal y estado reportado) y US2 (argumentos CLI y compatibilidad).
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from adaptadores.cache import CacheLRU
from adaptadores.extension import CARPETA_LOGS
from adaptadores.servicioCripta import ServicioCripta
from DTO.ActorDTO import EnemigoDTO
from DTO.EventoDTO import EventoDTO
from DTO.Objeto import Llave, Objeto
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from DTO.ResultadoReplayHastaDTO import ResultadoReplayHastaDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.GestorEventos import GestorEventos
from Logica.RetrocesoLogica import RetrocesoLogica
import main
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_lineal
from tests_labs.partida_prueba import esperar, jugar, nueva_partida


def _crear_juego_sin_iniciar(esqueleto, enemigos=None, fichas=None, semilla: int = 1, sala_inicial: int = 1):
    RetrocesoLogica().reiniciar()
    logica = EstadoJuegoLogica()
    logica.comunicacion = ServicioCripta(
        HttpConfigurable(
            esqueleto,
            enemigos if enemigos is not None else [],
            fichas if fichas is not None else [],
            sala_inicial=sala_inicial,
            sala_salida=len(esqueleto) + 1000,
        ),
        CacheLRU(25),
    )
    return logica


class TestTruncamientoTemporal(unittest.TestCase):
    """FR-402, FR-403: Corte temporal estricto en el ciclo de eventos y regla de la decisión del jugador."""

    def test_FR402_no_desapila_eventos_posteriores_al_tope(self):
        esqueleto = esqueleto_lineal([100, 100])
        juego = nueva_partida(esqueleto)
        reloj = juego.estadoJuego.reloj

        # Mockeamos procesar_evento para admitir eventos sintéticos
        juego.gestorEventos.procesar_evento = lambda e: ResultadoEventoDTO(True, "ok", None, 0)

        # Programamos eventos artificiales en el reloj:
        # e1 en t=50, e2 en t=120
        reloj.programar(50, None, "EVENTO_PRUEBA_50", [])
        reloj.programar(120, None, "EVENTO_PRUEBA_120", [])

        # Avanzamos con tope 80
        juego._avanzarHastaProximoTurno(tope=80)

        # El reloj no debe superar 80; se procesó el de 50
        self.assertLessEqual(reloj.tiempo_actual, 80)
        siguiente = reloj.siguiente()
        self.assertIsNotNone(siguiente)
        self.assertEqual(siguiente.tiempo_ejecucion, 120)

    def test_FR402_turno_jugador_posterior_permanece_en_reloj(self):
        esqueleto = esqueleto_lineal([100])
        juego = nueva_partida(esqueleto)
        reloj = juego.estadoJuego.reloj

        # El turno inicial del jugador está en t=0 o programamos acción que agenda el turno a t=100
        juego.accionJugador(EventoDTO(100, 0, juego.estadoJuego.jugador, "ESPERAR", []), tope=60)

        # El turno del jugador para t=100 no debe haberse consumido porque 100 > 60
        siguiente = reloj.siguiente()
        self.assertIsNotNone(siguiente)
        self.assertEqual(siguiente.tipo_accion, "TURNO_JUGADOR")
        self.assertEqual(siguiente.tiempo_ejecucion, 100)

    def test_FR403_completar_instante_ejecuta_eventos_de_otros_actores_en_tope(self):
        esqueleto = esqueleto_lineal([100])
        juego = nueva_partida(esqueleto)
        reloj = juego.estadoJuego.reloj
        ejecutados = []

        # Interceptamos procesar_evento para registrar qué se ejecuta
        original_procesar = juego.gestorEventos.procesar_evento

        def mock_procesar(evento):
            if evento.tipo_accion == "EVENTO_ENEMIGO_100":
                ejecutados.append(evento.tipo_accion)
                return ResultadoEventoDTO(True, "enemigo ejecutado", None, 0)
            return original_procesar(evento)

        juego.gestorEventos.procesar_evento = mock_procesar

        # En t=100 programamos turno del jugador (secuencia 1) y evento de enemigo (secuencia 2)
        reloj.programar(100, juego.estadoJuego.jugador, "TURNO_JUGADOR", [])
        reloj.programar(100, None, "EVENTO_ENEMIGO_100", [])

        # _avanzarHastaProximoTurno desapila TURNO_JUGADOR y para
        juego._avanzarHastaProximoTurno(tope=100)
        self.assertEqual(reloj.tiempo_actual, 100)
        self.assertNotIn("EVENTO_ENEMIGO_100", ejecutados)

        # _completarInstante debe ejecutar el evento restante de t=100
        juego._completarInstante(100)
        self.assertIn("EVENTO_ENEMIGO_100", ejecutados)

    def test_FR403_decision_jugador_en_tope_no_se_ejecuta(self):
        esqueleto = esqueleto_lineal([100])
        j1 = nueva_partida(esqueleto)
        esperar(j1, 3)  # 3 acciones ESPERAR de costo 100: t=0, t=100, t=200
        log = j1.exportar_log()

        j2 = _crear_juego_sin_iniciar(esqueleto)
        # hasta=100: la acción en t=0 se ejecuta, pero la decisión en t=100 no se ejecuta
        res = j2.repetirPartida(log, hasta=100)
        self.assertEqual(res.acciones_reproducidas, 1)
        self.assertEqual(res.instante_alcanzado, 100)

    def test_FR402_FR403_accion_jugador_anterior_a_tope_se_ejecuta_completa(self):
        esqueleto = esqueleto_lineal([100])
        juego = nueva_partida(esqueleto)
        # Acción con costo 150 en t=0; el próximo turno queda en t=150
        # Con tope=100, la acción en t=0 se ejecuta completa aunque su costo la lleve a 150
        res = juego.accionJugador(EventoDTO(150, 0, juego.estadoJuego.jugador, "ESPERAR", []), tope=100)
        self.assertTrue(res.exito)
        self.assertEqual(juego.accionesJugador, 1)
        # El turno de t=150 permanece en el reloj
        self.assertEqual(juego.estadoJuego.reloj.siguiente().tiempo_ejecucion, 150)


class TestEstadoReportado(unittest.TestCase):
    """FR-401, FR-404: Reporte exhaustivo de estado en ResultadoReplayHastaDTO."""

    def test_FR401_FR404_campos_exhaustivos(self):
        esqueleto = esqueleto_lineal([100, 100])
        fichas = [
            {"id": "ent_e1", "clase": "enemigo", "nombre": "Orco", "vida_max": 20, "ataque": 2, "defensa": 0, "velocidad": 100, "comportamiento": "guardián", "suelta": []},
            {"id": "ent_e2", "clase": "enemigo", "nombre": "Orco", "vida_max": 15, "ataque": 2, "defensa": 0, "velocidad": 100, "comportamiento": "guardián", "suelta": []},
        ]
        enemigos = [
            (1, "inst_b", "ent_e1", None),
            (1, "inst_a", "ent_e2", None),
        ]
        j1 = nueva_partida(esqueleto, enemigos=enemigos, fichas=fichas)
        esperar(j1, 2)
        log = j1.exportar_log()

        j2 = _crear_juego_sin_iniciar(esqueleto, enemigos=enemigos, fichas=fichas)
        resultado = j2.repetirPartida(log, hasta=100)

        self.assertIsInstance(resultado, ResultadoReplayHastaDTO)
        self.assertEqual(resultado.instante_pedido, 100)
        self.assertEqual(resultado.instante_alcanzado, 100)
        self.assertEqual(resultado.acciones_reproducidas, 1)
        self.assertEqual(resultado.id_sala_jugador, 1)
        self.assertGreater(resultado.vida_jugador, 0)
        self.assertIsInstance(resultado.ataque_jugador, int)
        self.assertIsInstance(resultado.defensa_jugador, int)
        self.assertIsInstance(resultado.velocidad_jugador, int)
        self.assertIsInstance(resultado.inventario_llaves, list)
        self.assertIsInstance(resultado.inventario_objetos, list)
        self.assertIsInstance(resultado.efectos_activos, list)
        self.assertFalse(resultado.partida_terminada)
        self.assertIsNone(resultado.motivo_terminacion)
        self.assertFalse(resultado.log_agotado)

        # Distinción de dos enemigos del mismo tipo por id y ordenación por id_instancia
        self.assertEqual(len(resultado.enemigos_sala), 2)
        self.assertEqual(resultado.enemigos_sala[0][0], "inst_a")
        self.assertEqual(resultado.enemigos_sala[1][0], "inst_b")
        self.assertEqual(resultado.enemigos_sala[0][1], "Orco")
        self.assertEqual(resultado.enemigos_sala[1][1], "Orco")


class TestCasosLimite(unittest.TestCase):
    """FR-405, FR-406: Casos de frontera (t=0, log agotado, muerte antes de t, término en t)."""

    def test_FR406_hasta_cero_no_ejecuta_ninguna_accion(self):
        esqueleto = esqueleto_lineal([100])
        j1 = nueva_partida(esqueleto)
        esperar(j1, 3)
        log = j1.exportar_log()

        j2 = _crear_juego_sin_iniciar(esqueleto)
        res = j2.repetirPartida(log, hasta=0)

        self.assertEqual(res.instante_pedido, 0)
        self.assertEqual(res.instante_alcanzado, 0)
        self.assertEqual(res.acciones_reproducidas, 0)
        self.assertFalse(res.partida_terminada)
        self.assertFalse(res.log_agotado)

    def test_FR405_log_agotado_antes_de_alcanzar_t(self):
        esqueleto = esqueleto_lineal([100])
        j1 = nueva_partida(esqueleto)
        esperar(j1, 2)  # Log solo llega a t=200
        log = j1.exportar_log()

        j2 = _crear_juego_sin_iniciar(esqueleto)
        res = j2.repetirPartida(log, hasta=1000)

        self.assertEqual(res.instante_pedido, 1000)
        self.assertEqual(res.instante_alcanzado, 200)
        self.assertEqual(res.acciones_reproducidas, 2)
        self.assertTrue(res.log_agotado)
        self.assertFalse(res.partida_terminada)

    def test_FR404_FR405_muerte_antes_de_alcanzar_t_congela_reloj(self):
        esqueleto = esqueleto_lineal([100])
        fichas = [
            {"id": "ent_asesino", "clase": "enemigo", "nombre": "Asesino", "vida_max": 100, "ataque": 99999, "defensa": 0, "velocidad": 100, "comportamiento": "guardián", "suelta": []}
        ]
        enemigos = [(1, "e1", "ent_asesino", None)]
        j1 = nueva_partida(esqueleto, enemigos=enemigos, fichas=fichas)
        # El jugador espera y el enemigo lo mata
        esperar(j1, 1)
        self.assertTrue(j1.fin)
        log = j1.exportar_log()

        j2 = _crear_juego_sin_iniciar(esqueleto, enemigos=enemigos, fichas=fichas)
        res = j2.repetirPartida(log, hasta=500)

        self.assertTrue(res.partida_terminada)
        self.assertIsNotNone(res.motivo_terminacion)
        self.assertLess(res.instante_alcanzado, 500)
        self.assertFalse(res.log_agotado)

    def test_terminacion_exactamente_en_t(self):
        esqueleto = esqueleto_lineal([100])
        fichas = [
            {"id": "ent_asesino", "clase": "enemigo", "nombre": "Asesino", "vida_max": 100, "ataque": 99999, "defensa": 0, "velocidad": 100, "comportamiento": "guardián", "suelta": []}
        ]
        enemigos = [(1, "e1", "ent_asesino", None)]
        j1 = nueva_partida(esqueleto, enemigos=enemigos, fichas=fichas)
        esperar(j1, 1)
        log = j1.exportar_log()

        j2 = _crear_juego_sin_iniciar(esqueleto, enemigos=enemigos, fichas=fichas)
        instante_muerte = j1.estadoJuego.reloj.tiempo_actual
        res = j2.repetirPartida(log, hasta=instante_muerte)

        self.assertTrue(res.partida_terminada)
        self.assertEqual(res.instante_alcanzado, instante_muerte)
        self.assertEqual(res.instante_pedido, instante_muerte)


class TestArgumentosCLI(unittest.TestCase):
    """FR-407, FR-408, SC-004: Validación robusta de la CLI y latencia < 0.1s."""

    def test_FR407_rechaza_valor_negativo(self):
        import argparse
        with self.assertRaises(argparse.ArgumentTypeError) as ctx:
            main._instante_hasta("-5")
        self.assertIn("el instante virtual debe ser mayor o igual que 0", str(ctx.exception))

    def test_FR407_rechaza_valor_no_entero(self):
        import argparse
        with self.assertRaises(argparse.ArgumentTypeError) as ctx:
            main._instante_hasta("abc")
        self.assertIn("no es un número entero", str(ctx.exception))

    def test_FR408_rechaza_hasta_sin_replay(self):
        buffer_err = io.StringIO()
        with patch("sys.stderr", buffer_err):
            codigo = main.main(["--hasta", "100"])
        self.assertEqual(codigo, 2)
        self.assertIn("Error: el argumento --hasta requiere especificar una partida con --replay.", buffer_err.getvalue())

    def test_SC004_latencia_rechazo_menor_a_100ms(self):
        t0 = time.perf_counter()
        buffer_err = io.StringIO()
        with patch("sys.stderr", buffer_err):
            main.main(["--hasta", "100"])
        latencia = time.perf_counter() - t0
        self.assertLess(latencia, 0.1)


class TestCompatibilidadReplay(unittest.TestCase):
    """FR-409, FR-410: Preservación del comportamiento clásico y ausencia de efectos colaterales."""

    def test_FR409_replay_sin_hasta_retorna_lista_eventos(self):
        esqueleto = esqueleto_lineal([100])
        j1 = nueva_partida(esqueleto)
        esperar(j1, 2)
        log = j1.exportar_log()

        j2 = _crear_juego_sin_iniciar(esqueleto)
        res = j2.repetirPartida(log, hasta=None)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 2)
        self.assertIsInstance(res[0], ResultadoEventoDTO)


class TestAislamientoReplay(unittest.TestCase):
    """FR-410: La reproducción no genera nuevos logs, no modifica puntajes ni abre la vista."""

    def test_FR410_no_crea_nuevos_logs_ni_puntajes(self):
        esqueleto = esqueleto_lineal([100])
        j1 = nueva_partida(esqueleto)
        esperar(j1, 2)
        log = j1.exportar_log()

        archivos_logs_antes = set(os.listdir(CARPETA_LOGS)) if os.path.exists(CARPETA_LOGS) else set()

        j2 = _crear_juego_sin_iniciar(esqueleto)
        j2.repetirPartida(log, hasta=100)

        archivos_logs_despues = set(os.listdir(CARPETA_LOGS)) if os.path.exists(CARPETA_LOGS) else set()
        self.assertEqual(archivos_logs_antes, archivos_logs_despues)


if __name__ == "__main__":
    unittest.main()
