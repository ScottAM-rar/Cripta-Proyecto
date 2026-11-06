"""Escenarios de reproducción de la capacidad terreno y cazador. Cada uno cita el requisito que demuestra en su nombre.

Los logs de `specs/001-terreno-y-cazador/replays/` se generan con `python -m tests_labs.escenarios_terreno` y los
reproduce test_determinismo_cazador.py sobre la MISMA cripta sintética (no sirven con la cripta real del servicio).
"""
from __future__ import annotations

import os

from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from Controlador.ControladorJuego import ControladorJuego
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_lineal, ficha_cazador
from tests_labs.partida_prueba import esperar, nueva_partida

CARPETA_REPLAYS = os.path.join("specs", "001-terreno-y-cazador", "replays")
SALIDA_INEXISTENTE = 1000          # la partida no termina por llegar a una sala final


class Escenario:
    def __init__(self, nombre, esqueleto, sala_cazador, sala_jugador, rango, velocidad, guion, semilla=1):
        self.nombre = nombre
        self.esqueleto = esqueleto
        self.enemigos = [(sala_cazador, "e-1", "ent_cazador", None)]
        self.fichas = [ficha_cazador(rango=rango, velocidad=velocidad)]
        self.sala_jugador = sala_jugador
        self.guion = guion              # lista de ("mover", direccion) o ("esperar", veces)
        self.semilla = semilla

    def servicio(self):
        api = HttpConfigurable(self.esqueleto, self.enemigos, self.fichas, sala_inicial=self.sala_jugador,
                               sala_salida=SALIDA_INEXISTENTE)
        return ServicioCripta(api, CacheLRU(25))

    def jugar(self, precargar_todas=False):
        """Juega el guion. Devuelve (partida, trayectoria del cazador: salas por las que pasó, en orden).
        `precargar_todas`: antes de jugar se trae el contenido de TODAS las salas (otra historia de descargas)."""
        logica = nueva_partida(self.esqueleto, self.enemigos, self.fichas, semilla=self.semilla,
                               sala_inicial=self.sala_jugador, sala_salida=SALIDA_INEXISTENTE)
        if precargar_todas:
            for sala in self.esqueleto:
                logica.ingresarEnSala(sala["id"])
        cazador = logica.estadoJuego.catalogo_enemigos[0]
        trayectoria = [cazador.id_sala_actual]
        controlador = ControladorJuego(None)
        for orden, argumento in self.guion:
            if orden == "mover":
                sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
                logica.accionJugador(controlador._mapear_entrada_a_evento(argumento, sala, logica.estadoJuego.jugador))
            else:
                esperar(logica, argumento)
            if cazador.id_sala_actual != trayectoria[-1]:
                trayectoria.append(cazador.id_sala_actual)
        return logica, trayectoria

    def repetir(self, log) -> EstadoJuegoLogica:
        logica = EstadoJuegoLogica()
        logica.comunicacion = self.servicio()
        logica.repetirPartida(log)
        return logica


def firma(logica) -> tuple:
    """Todo lo observable de una partida terminada, para compararla con otra."""
    estado = logica.estadoJuego
    enemigos = sorted((e.id_instancia, e.id_sala_actual, e.vida_actual) for e in estado.catalogo_enemigos)
    return (estado.reloj.tiempo_actual, estado.jugador.id_sala_actual, estado.jugador.vida_actual, tuple(enemigos),
            tuple(logica.exportar_log().acciones))


def _diamante():
    # 1 -> 2 -> 4 y 1 -> 3 -> 4, todas de costo 50: dos rutas de igual costo desde la sala 1 hasta la 4
    return esqueleto_de_conexiones([(1, 2, 50, "E", "O"), (1, 3, 50, "S", "N"), (2, 4, 50, "S", "N"), (3, 4, 50, "E", "O")])


ESCENARIOS = (
    Escenario("FR113_persecucion_con_costo", esqueleto_lineal([300]), sala_cazador=2, sala_jugador=2, rango=1000,
              velocidad=100, guion=[("mover", "oeste"), ("esperar", 5)]),
    Escenario("FR112_fuera_de_rango_espera", esqueleto_lineal([300]), sala_cazador=2, sala_jugador=2, rango=299,
              velocidad=100, guion=[("mover", "oeste"), ("esperar", 5)]),
    # el cazador es lento (primer turno en t=1000): para entonces el jugador ya está en la sala 4
    Escenario("FR114_desempate_por_menor_id", _diamante(), sala_cazador=1, sala_jugador=1, rango=1000,
              velocidad=10, guion=[("mover", "este"), ("mover", "sur"), ("esperar", 10)]),
)


def generar() -> None:
    for escenario in ESCENARIOS:
        logica, _ = escenario.jugar()
        ruta = os.path.join(CARPETA_REPLAYS, escenario.nombre + ".log")
        if os.path.exists(ruta):
            os.remove(ruta)
        AlmacenLogTexto(escenario.nombre, CARPETA_REPLAYS).abrir(logica.exportar_log())
        print("escrito", ruta)


if __name__ == "__main__":
    generar()
