"""Pruebas de determinismo estricto y propiedad de prefijo (FR-411, Principio II, Principio III).
"""
from __future__ import annotations

import io
from unittest.mock import patch
import unittest

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from DTO.EventoDTO import EventoDTO
from DTO.ResultadoReplayHastaDTO import ResultadoReplayHastaDTO
from Logica.ActorLogica import ActorLogica
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
import main
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_lineal
from tests_labs.partida_prueba import esperar, nueva_partida


def _crear_juego_sin_iniciar(esqueleto, enemigos=None, fichas=None, semilla: int = 1):
    RetrocesoLogica().reiniciar()
    logica = EstadoJuegoLogica()
    logica.comunicacion = ServicioCripta(
        HttpConfigurable(
            esqueleto,
            enemigos if enemigos is not None else [],
            fichas if fichas is not None else [],
            sala_inicial=1,
            sala_salida=len(esqueleto) + 1000,
        ),
        CacheLRU(25),
    )
    return logica


class TestDeterminismoReplay(unittest.TestCase):
    """FR-411: Reproducibilidad carácter por carácter y propiedad de prefijo."""

    def test_FR411_determinismo_estricto_dos_ejecuciones_identicas(self):
        esqueleto = esqueleto_lineal([100, 100, 100])
        fichas = [
            {"id": "ent_e1", "clase": "enemigo", "nombre": "Goblin", "vida_max": 25, "ataque": 3, "defensa": 1, "velocidad": 100, "comportamiento": "guardián", "suelta": []},
            {"id": "ent_e2", "clase": "enemigo", "nombre": "Goblin", "vida_max": 20, "ataque": 3, "defensa": 1, "velocidad": 100, "comportamiento": "guardián", "suelta": []},
        ]
        enemigos = [
            (1, "goblin-2", "ent_e2", None),
            (1, "goblin-1", "ent_e1", None),
        ]
        j1 = nueva_partida(esqueleto, enemigos=enemigos, fichas=fichas, semilla=42)
        esperar(j1, 4)
        log = j1.exportar_log()

        # Primera reproducción
        j2 = _crear_juego_sin_iniciar(esqueleto, enemigos=enemigos, fichas=fichas, semilla=42)
        res1 = j2.repetirPartida(log, hasta=200)

        # Segunda reproducción independiente
        j3 = _crear_juego_sin_iniciar(esqueleto, enemigos=enemigos, fichas=fichas, semilla=42)
        res2 = j3.repetirPartida(log, hasta=200)

        # Igualdad estricta de DTO
        self.assertEqual(res1, res2)

    def test_FR411_propiedad_de_prefijo(self):
        """El estado en t al reproducir hasta t coincide exactamente con el estado en t de la ejecución completa."""
        esqueleto = esqueleto_lineal([100, 100])
        fichas = [
            {"id": "ent_e1", "clase": "enemigo", "nombre": "Orco", "vida_max": 30, "ataque": 2, "defensa": 1, "velocidad": 100, "comportamiento": "guardián", "suelta": []}
        ]
        enemigos = [(1, "e-1", "ent_e1", None)]

        # Partida completa de 4 acciones (t=0, t=100, t=200, t=300)
        j_completo = nueva_partida(esqueleto, enemigos=enemigos, fichas=fichas, semilla=2026)
        # Queremos observar el estado justo en t=200 antes de ejecutar la acción de t=200:
        esperar(j_completo, 2)  # ejecuta t=0 y t=100; el reloj queda en t=200
        self.assertEqual(j_completo.estadoJuego.reloj.tiempo_actual, 200)

        # Capturamos el estado en el instante t=200
        jugador_ref = j_completo.estadoJuego.jugador
        sala_ref = jugador_ref.id_sala_actual
        vida_ref = jugador_ref.vida_actual
        ataque_ref = ActorLogica.ataque_efectivo(jugador_ref)
        defensa_ref = ActorLogica.defensa_efectiva(jugador_ref)
        velocidad_ref = ActorLogica.velocidad_efectiva(jugador_ref)
        enemigos_ref = [
            (e.id_instancia, e.nombre, e.vida_actual)
            for e in j_completo.estadoJuego.salas[sala_ref].enemigos
            if e.vida_actual > 0
        ]
        enemigos_ref.sort(key=lambda t: t[0])

        # Continuamos la partida hasta el final para armar el log completo
        esperar(j_completo, 2)
        log_completo = j_completo.exportar_log()

        # Ahora reproducimos el log completo acotado hasta t=200
        j_replay = _crear_juego_sin_iniciar(esqueleto, enemigos=enemigos, fichas=fichas, semilla=2026)
        res_replay = j_replay.repetirPartida(log_completo, hasta=200)

        # Verificamos que el corte reproduce fielmente el prefijo
        self.assertEqual(res_replay.instante_alcanzado, 200)
        self.assertEqual(res_replay.id_sala_jugador, sala_ref)
        self.assertEqual(res_replay.vida_jugador, vida_ref)
        self.assertEqual(res_replay.ataque_jugador, ataque_ref)
        self.assertEqual(res_replay.defensa_jugador, defensa_ref)
        self.assertEqual(res_replay.velocidad_jugador, velocidad_ref)
        self.assertEqual(res_replay.enemigos_sala, enemigos_ref)
        self.assertEqual(res_replay.acciones_reproducidas, 2)


if __name__ == "__main__":
    unittest.main()
