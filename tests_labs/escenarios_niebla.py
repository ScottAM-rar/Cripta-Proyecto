"""Escenarios de reproducción de la capacidad niebla de guerra (002). Cada uno cita el requisito que demuestra en su nombre.

Los logs de `specs/002-niebla-de-guerra/replays/` se generan con `python -m tests_labs.escenarios_niebla` y los reproduce
test_niebla_determinismo.py sobre la MISMA cripta sintética (no sirven con la cripta real del servicio). Incluyen los tres
casos del Apéndice B: puerta recordada abierta que está cerrada (FR-208), antorcha que explora vecinas sin activar enemigos
(FR-210) y pergamino que revierte una entrada con antorcha (FR-214). El guardado y la carga con niebla (FR-220) esperan a
que se cierre la numeración del formato (P3 del plan).
"""
from __future__ import annotations

import os

from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from DTO.EventoDTO import EventoDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, ficha_enemigo
from tests_labs.partida_prueba import esperar, jugar

CARPETA_REPLAYS = os.path.join("specs", "002-niebla-de-guerra", "replays")
SALIDA_INEXISTENTE = 1000

FICHAS_OBJETOS = [
    {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha", "peso": 1, "valor": 1, "duracion": 5000},
    {"id": "itm_pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino", "peso": 1, "valor": 1},
]


class ApiNiebla(HttpConfigurable):
    """HttpConfigurable que además deja objetos (ids de catálogo) en el suelo de la sala 1."""

    def __init__(self, salas, objetos_sala_1, **kw):
        super().__init__(salas, **kw)
        self.objetos_sala_1 = objetos_sala_1

    def obtener_contenido(self, cripta_id, salas):
        contenidos = super().obtener_contenido(cripta_id, salas)
        for contenido in contenidos:
            if contenido["sala"] == 1:
                contenido["objetos"] = list(self.objetos_sala_1)
        return contenidos


def _cruz():
    """1 -E- 2 -E- 3 ; 2 -S- 4 (puerta cerrada) ; 2 -N- 5."""
    return esqueleto_de_conexiones([(1, 2, None, "E", "O"), (2, 3, None, "E", "O"),
                                    (2, 4, None, "S", "N", {"cerrada": True}), (2, 5, None, "N", "S")])


def _puerta_con_cierre_automatico():
    salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"cerrada": True}), (2, 3, None, "E", "O")])
    salas[0]["salidas"]["E"]["cierre_automatico"] = 300
    return salas


class Escenario:
    def __init__(self, nombre, esqueleto, guion, objetos=(), enemigos=(), semilla=1):
        self.nombre = nombre
        self.esqueleto = esqueleto
        self.guion = guion            # ("mover", dir) | ("abrir", dir) | ("esperar", n) | ("recoger", id) | ("usar", id)
        self.objetos = list(objetos)
        self.enemigos = list(enemigos)
        self.semilla = semilla

    def servicio(self):
        fichas = FICHAS_OBJETOS + ([ficha_enemigo("ent_x", "errante")] if self.enemigos else [])
        api = ApiNiebla(self.esqueleto, self.objetos, enemigos=list(self.enemigos), fichas=fichas, sala_inicial=1,
                        sala_salida=SALIDA_INEXISTENTE)
        return ServicioCripta(api, CacheLRU(25))

    def nueva(self) -> EstadoJuegoLogica:
        RetrocesoLogica().reiniciar()
        logica = EstadoJuegoLogica()
        logica.comunicacion = self.servicio()
        logica.iniciarJuego("cripta-01", self.semilla)
        logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
        return logica

    def jugar(self):
        logica = self.nueva()
        jugador = logica.estadoJuego.jugador
        for orden, argumento in self.guion:
            sala = logica.estadoJuego.salas[jugador.id_sala_actual]
            if orden == "mover":
                jugar(logica, "MOVER_JUGADOR", [sala, argumento])
            elif orden == "abrir":
                jugar(logica, "ABRIR_PUERTA", [sala, argumento])
            elif orden == "esperar":
                esperar(logica, argumento)
            elif orden == "recoger":
                objeto = [o for o in sala.objetos if o.id_catalogo == argumento][0]
                jugar(logica, "RECOGER_OBJETO", [objeto])
            elif orden == "usar":
                nodo = jugador.inventario.cabeza
                while nodo is not None and nodo.objeto.id_catalogo != argumento:
                    nodo = nodo.siguiente
                jugar(logica, "USAR_OBJETO", [nodo.objeto])
        return logica

    def repetir(self, log) -> EstadoJuegoLogica:
        RetrocesoLogica().reiniciar()
        logica = EstadoJuegoLogica()
        logica.comunicacion = self.servicio()
        logica.repetirPartida(log)
        return logica


def firma(logica) -> tuple:
    """El conocimiento del jugador y lo observable de la partida, para compararla con otra."""
    c = logica.mapaConocido
    estado = logica.estadoJuego
    return (tuple(c.estado), tuple(c.puertas), tuple(c.exploradas), estado.reloj.tiempo_actual,
            estado.jugador.id_sala_actual, tuple(logica.exportar_log().acciones))


ENEMIGOS_VECINAS = [(3, "e-3", "ent_x", None), (4, "e-4", "ent_x", None), (5, "e-5", "ent_x", None)]

ESCENARIOS = (
    Escenario("FR203_avistar_por_una_salida", _cruz(), [("mover", "este")]),
    Escenario("FR204_entrar_a_una_sala_nueva", _cruz(), [("mover", "este"), ("mover", "este")]),
    Escenario("FR208_APENDICE_B_puerta_recordada_abierta_que_esta_cerrada", _puerta_con_cierre_automatico(),
              [("abrir", "este"), ("mover", "este"), ("mover", "este"), ("esperar", 3), ("mover", "oeste")]),
    Escenario("FR210_APENDICE_B_antorcha_explora_vecinas_sin_activar_enemigos", _cruz(),
              [("recoger", "itm_antorcha"), ("usar", "itm_antorcha"), ("mover", "este")],
              objetos=["itm_antorcha"], enemigos=ENEMIGOS_VECINAS),
    Escenario("FR214_APENDICE_B_pergamino_revierte_una_entrada_con_antorcha", _cruz(),
              [("recoger", "itm_antorcha"), ("recoger", "itm_pergamino"), ("usar", "itm_antorcha"),
               ("mover", "este"), ("usar", "itm_pergamino")],
              objetos=["itm_antorcha", "itm_pergamino"], enemigos=ENEMIGOS_VECINAS),
    Escenario("FR216_mapa_tras_explorar", _cruz(), [("mover", "este"), ("mover", "este"), ("mover", "oeste")]),
)


def generar() -> None:
    for escenario in ESCENARIOS:
        logica = escenario.jugar()
        ruta = os.path.join(CARPETA_REPLAYS, escenario.nombre + ".log")
        if os.path.exists(ruta):
            os.remove(ruta)
        AlmacenLogTexto(escenario.nombre, CARPETA_REPLAYS).abrir(logica.exportar_log())
        print("escrito", ruta)


if __name__ == "__main__":
    generar()
