"""Arma una partida real del modelo sobre una cripta definida por la prueba (sin red ni vista)."""
from __future__ import annotations

import contextlib
import io

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from DTO.EventoDTO import EventoDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from tests_labs.api_falsa import HttpConfigurable


def nueva_partida(salas, enemigos=None, fichas=None, semilla: int = 1, sala_inicial: int = 1,
                  sala_salida: int | None = None) -> EstadoJuegoLogica:
    """`sala_salida` None: una sala que no existe, para que llegar al final de la cadena no termine la partida."""
    RetrocesoLogica().reiniciar()
    logica = EstadoJuegoLogica()
    logica.comunicacion = ServicioCripta(HttpConfigurable(salas, enemigos, fichas, sala_inicial=sala_inicial,
                                                       sala_salida=sala_salida if sala_salida is not None else len(salas) + 1000), CacheLRU(25))
    logica.iniciarJuego("cripta-01", semilla)
    logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
    return logica


def jugar(logica: EstadoJuegoLogica, tipo: str, datos=None, costo: int = 100):
    jugador = logica.estadoJuego.jugador
    evento = EventoDTO(costo, 0, jugador, tipo, [] if datos is None else datos)
    with contextlib.redirect_stdout(io.StringIO()):
        return logica.accionJugador(evento)


def esperar(logica: EstadoJuegoLogica, veces: int = 1) -> None:
    for _ in range(veces):
        jugar(logica, "ESPERAR")


def pendientes(logica: EstadoJuegoLogica, tipo: str) -> list:
    """Eventos pendientes de un tipo, ordenados por tiempo y número de secuencia."""
    encontrados = [e for e in logica.estadoJuego.reloj.heap if e.tipo_accion == tipo]
    encontrados.sort(key=lambda e: (e.tiempo_ejecucion, e.id_secuencia))
    return encontrados
