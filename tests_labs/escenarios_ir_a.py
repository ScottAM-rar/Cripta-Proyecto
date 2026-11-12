"""Criptas y ayudas de prueba de «ir a» (capacidad 006). Sin red; ningún id de la cripta real: todo sale de
criptas sintéticas armadas aquí. Contrato: specs/006-ir-a/quickstart.md.

Los casos B-N1, B-N2, B-N3 y B-N6 de `tests_labs/api_falsa.py` (CASOS_APENDICE_B) nombran la misma situación con
pasos de guion; aquí se arman con el modelo real para ejecutarlos."""
from __future__ import annotations

import contextlib
import io

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from DTO.EventoDTO import EventoDTO
from DTO.Objeto import PergaminoRetroceso
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_lineal, ficha_enemigo
from tests_labs.partida_prueba import jugar, nueva_partida

NORTE, SUR, ESTE, OESTE = "norte", "sur", "este", "oeste"


# ---------------------------------------------------------------- criptas

def cuadrado(a: int = 100, b: int = 100, c: int = 100, d: int = 100) -> list:
    """Ciclo 1-2-4-3-1: 1-2 cuesta a, 2-4 cuesta b, 1-3 cuesta c, 3-4 cuesta d. Rutas de 1 a 4: por 2 (a+b) y por 3 (c+d).
    Letras: 1: E→2, S→3; 2: O→1, S→4; 3: N→1, E→4; 4: N→2, O→3."""
    return esqueleto_de_conexiones([(1, 2, a, "E", "O"), (2, 4, b, "S", "N"), (1, 3, c, "S", "N"), (3, 4, d, "E", "O")])


def recorrer_cuadrado(logica) -> None:
    """Explora las cuatro salas del cuadrado y vuelve a la sala 1: este, sur, oeste, norte."""
    caminar(logica, [ESTE, SUR, OESTE, NORTE])


def pasillo(n: int, costo: int | None = None) -> list:
    """Cadena 1 - 2 - ... - n, de este a oeste."""
    return esqueleto_lineal([costo] * (n - 1))


def circuito_con_puerta(con_alterna: bool) -> list:
    """Pasillo 1-2-3-4 (la puerta que se va a cerrar es la salida este de la sala 3, a dos salas del jugador cuando está en
    la 1) y, si `con_alterna`, un rodeo 1-5-6-4 más caro (el tramo 5-6 cuesta 200). Letras: 1: E→2, S→5; 2: O→1, E→3;
    3: O→2, E→4; 4: O→3, S→6; 5: N→1, E→6; 6: O→5, N→4."""
    conexiones = [(1, 2, 100, "E", "O"), (2, 3, 100, "E", "O"), (3, 4, 100, "E", "O")]
    if con_alterna:
        conexiones += [(1, 5, 100, "S", "N"), (5, 6, 200, "E", "O"), (6, 4, 100, "N", "S")]
    return esqueleto_de_conexiones(conexiones)


def recorrer_circuito(logica, con_alterna: bool) -> None:
    """Explora todo el circuito y vuelve a la sala 1."""
    if con_alterna:
        caminar(logica, [ESTE, ESTE, ESTE, SUR, OESTE, NORTE])     # 1→2→3→4→6→5→1
    else:
        caminar(logica, [ESTE, ESTE, ESTE, OESTE, OESTE, OESTE])   # 1→2→3→4→3→2→1


def pasillo_con_enemigos(n: int, sala_enemigos: int, cantidad: int = 1, comportamiento: str = "guardián"):
    """Pasillo de n salas con `cantidad` enemigos dormidos en `sala_enemigos`. Devuelve (salas, enemigos, fichas)."""
    enemigos = [(sala_enemigos, f"e-{i}", "ent_ir_a", None) for i in range(cantidad)]
    return pasillo(n), enemigos, [ficha_enemigo("ent_ir_a", comportamiento)]


# ---------------------------------------------------------------- partidas

def partida_con_trampa(salas: list, sala_trampa: int, vida: int | None = None) -> EstadoJuegoLogica:
    """Partida real con una trampa armada (daño 3, de la API falsa) en `sala_trampa`; `vida` fija la vida máxima."""
    from tests_labs.api_falsa import _caso
    http = _caso(salas, trampas=[(sala_trampa, "t-ir-a", "trp_dardos")], sala_salida=len(salas) + 1000)
    if vida is not None:
        http.vida_jugador = vida
    RetrocesoLogica().reiniciar()
    logica = EstadoJuegoLogica()
    logica.comunicacion = ServicioCripta(http, CacheLRU(25))
    logica.iniciarJuego("cripta-01", 1)
    logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
    return logica


def partida_de(salas: list, enemigos=None, fichas=None, semilla: int = 1) -> EstadoJuegoLogica:
    return nueva_partida(salas, enemigos, fichas, semilla=semilla)


# ---------------------------------------------------------------- ayudas de juego

def _sala_actual(logica):
    return logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)


def mover(logica, direccion: str):
    """Un movimiento como lo hace el controlador: `ingresarEnSala` al empezar el turno, luego la acción."""
    sala = _sala_actual(logica)
    resultado = jugar(logica, "MOVER_JUGADOR", [sala, direccion])
    logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
    return resultado


def caminar(logica, direcciones: list) -> None:
    for direccion in direcciones:
        mover(logica, direccion)


def abrir(logica, direccion: str):
    return jugar(logica, "ABRIR_PUERTA", [_sala_actual(logica), direccion])


def cerrar_fuera(logica, sala: int, direccion: str) -> None:
    """Cierra la puerta (salida `direccion` de `sala`) por el mismo camino que el cierre automático: el jugador no la
    ve si no está en una de las dos salas que conecta."""
    gestor = logica.gestorEventos
    gestor.salas_logica.sala = logica.estadoJuego.salas[sala]
    gestor.salas_logica.cerrarPuerta(direccion)


def dar_pergamino(logica):
    objeto = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
    logica.estadoJuego.jugador.inventario.agregar_objeto(objeto)
    return objeto


def usar_pergamino(logica, objeto=None):
    if objeto is None:
        objeto = dar_pergamino(logica)
    return jugar(logica, "USAR_OBJETO", [objeto])


def encender_antorcha(logica) -> None:
    logica.estadoJuego.jugador.antorcha_encendida = True


def apagar_antorcha(logica) -> None:
    logica.estadoJuego.jugador.antorcha_encendida = False


def lineas_del_log(logica) -> list:
    """Los registros del log de la partida como texto JSON, en orden cronológico."""
    nodo = logica.logEventos.cabeza
    lineas = []
    while nodo is not None:
        lineas.append(nodo.accion)
        nodo = nodo.siguiente
    return lineas


# ---------------------------------------------------------------- viajes reproducibles (guion con «ir_a»)

def viajar(logica, destino):
    """Lo que hace el servicio con la orden «ir a»: valida y, si procede, recorre el viaje completo."""
    resultado = logica.iniciarViaje(destino)
    if logica.viaje_activo is None:
        return resultado
    return logica.ejecutarViaje()


def _clase_escenario_viaje():
    from tests_labs.escenarios_niebla import ApiNiebla, Escenario, FICHAS_OBJETOS
    from tests_labs.partida_prueba import esperar

    class EscenarioViaje(Escenario):
        """Escenario de la 002 con un paso más: ("ir_a", sala). Los enemigos son guardianes. Guarda la API para contar
        solicitudes y los resultados de los viajes."""

        def servicio(self):
            fichas = FICHAS_OBJETOS + ([ficha_enemigo("ent_x", "guardián")] if self.enemigos else [])
            self.api = ApiNiebla(self.esqueleto, self.objetos, enemigos=list(self.enemigos), fichas=fichas,
                                 sala_inicial=1, sala_salida=1000)
            return ServicioCripta(self.api, CacheLRU(25))

        def jugar(self, hasta: int | None = None):
            """Ejecuta los primeros `hasta` pasos del guion (todos si es None)."""
            logica = self.nueva()
            self.resultados = []
            jugador = logica.estadoJuego.jugador
            pasos = self.guion if hasta is None else self.guion[:hasta]
            for orden, argumento in pasos:
                sala = logica.estadoJuego.salas[jugador.id_sala_actual]
                if orden == "mover":
                    jugar(logica, "MOVER_JUGADOR", [sala, argumento])
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
                elif orden == "ir_a":
                    self.resultados.append(viajar(logica, argumento))
            return logica

    return EscenarioViaje


def escenario_viaje(nombre: str):
    """Escenarios reproducibles con «ir a»: 'simple' (pasillo de 4, ida y vuelta, ir a la 4) y 'b_n3' (el caso B-N3: la
    antorcha explora la sala 3 sin despertar a sus dormidos y el viaje entra a ella)."""
    EscenarioViaje = _clase_escenario_viaje()
    if nombre == "simple":
        return EscenarioViaje("simple", pasillo(4), [("mover", ESTE)] * 3 + [("mover", OESTE)] * 3 + [("ir_a", 4)])
    if nombre == "b_n3":
        recorrido = [("mover", ESTE), ("mover", OESTE), ("mover", SUR), ("mover", ESTE), ("mover", NORTE),
                     ("mover", SUR), ("mover", OESTE), ("mover", NORTE)]
        return EscenarioViaje("b_n3", circuito_con_puerta(True),
                              [("recoger", "itm_antorcha"), ("usar", "itm_antorcha")] + recorrido + [("ir_a", 4)],
                              objetos=["itm_antorcha"],
                              enemigos=[(3, "e-0", "ent_x", None), (3, "e-1", "ent_x", None)])
    raise ValueError(f"Escenario desconocido: {nombre!r}")
