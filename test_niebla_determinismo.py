"""Niebla de guerra (capacidad 002), historia 7: determinismo y neutralidad para los enemigos (FR-213, FR-222)."""
import os
import random
import unittest

from tests_labs.cripta_sintetica import esqueleto_rejilla, ficha_enemigo
from tests_labs.partida_prueba import esperar, jugar, nueva_partida


def mover(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "MOVER_JUGADOR", [sala, direccion])


def foto(logica):
    c = logica.mapaConocido
    return (list(c.estado), list(c.puertas), list(c.exploradas))


def jugar_guion(logica, semilla, pasos=40):
    """Misma secuencia de acciones para la misma semilla; devuelve la foto del conocimiento tras cada acción."""
    azar = random.Random(semilla)
    jugador = logica.estadoJuego.jugador
    fotos = [foto(logica)]
    for _ in range(pasos):
        if azar.random() < 0.2:
            esperar(logica)
        else:
            jugador.antorcha_encendida = azar.random() < 0.3
            sala = logica.estadoJuego.salas[jugador.id_sala_actual]
            direcciones = [s.direccion for s in sala.salidas if not s.cerrada]
            if direcciones:
                direccion = azar.choice(direcciones)
                mover(logica, str(getattr(direccion, "value", direccion)))
        fotos.append(foto(logica))
    return fotos


class TestDeterminismo(unittest.TestCase):
    def partida(self, descargar_todo=False):
        salas = esqueleto_rejilla(6, 6, semilla=4, fraccion_cerradas=0.2)
        logica = nueva_partida(salas, [(20, "e-1", "ent_x", None), (30, "e-2", "ent_x", None)], [ficha_enemigo("ent_x", "errante")])
        if descargar_todo:
            logica.comunicacion.precargar("cripta-01")                       # todo el contenido ya descargado
        return logica

    def test_FR222_la_misma_partida_dos_veces_da_el_mismo_conocimiento_en_cada_instante(self):
        self.assertEqual(jugar_guion(self.partida(), 7), jugar_guion(self.partida(), 7))

    def test_FR222_con_el_contenido_descargado_o_sin_descargar_el_conocimiento_es_el_mismo(self):
        self.assertEqual(jugar_guion(self.partida(False), 11), jugar_guion(self.partida(True), 11))


class TestNeutralidadParaEnemigos(unittest.TestCase):
    def estado_de_enemigos(self, logica):
        return [(e.id_instancia, e.id_sala_actual, e.vida_actual, e.activo) for e in logica.estadoJuego.catalogo_enemigos]

    def test_FR213_los_enemigos_actuan_igual_con_el_conocimiento_desactivado_o_activado(self):
        def partida(con_conocimiento):
            salas = esqueleto_rejilla(5, 5, semilla=2)
            logica = nueva_partida(salas, [(8, "e-1", "ent_x", None), (14, "e-2", "ent_x", None)],
                                   [ficha_enemigo("ent_x", "errante")], semilla=9)
            if not con_conocimiento:
                logica.mapaConocido = None
                logica.gestorEventos.mapa_conocido = None
            return logica
        resultados = []
        for con in (True, False):
            logica = partida(con)
            jugar_guion(logica, 3, pasos=30) if con else self.guion_sin_conocimiento(logica, 3, 30)
            resultados.append((self.estado_de_enemigos(logica), logica.estadoJuego.reloj.tiempo_actual,
                               logica.estadoJuego.jugador.id_sala_actual, logica.estadoJuego.jugador.vida_actual))
        self.assertEqual(resultados[0], resultados[1])

    @staticmethod
    def guion_sin_conocimiento(logica, semilla, pasos):
        azar = random.Random(semilla)
        jugador = logica.estadoJuego.jugador
        for _ in range(pasos):
            if azar.random() < 0.2:
                esperar(logica)
            else:
                jugador.antorcha_encendida = azar.random() < 0.3
                sala = logica.estadoJuego.salas[jugador.id_sala_actual]
                direcciones = [s.direccion for s in sala.salidas if not s.cerrada]
                if direcciones:
                    direccion = azar.choice(direcciones)
                    mover(logica, str(getattr(direccion, "value", direccion)))


class TestReproduccion(unittest.TestCase):
    """Los logs de specs/002-niebla-de-guerra/replays/ citan en su nombre el requisito; se generan con
    `python -m tests_labs.escenarios_niebla` y aqui se reproducen sin vista, como hace --replay (FR-222)."""

    def test_FR222_reproducir_cada_log_da_el_mismo_conocimiento_que_jugarlo(self):
        from adaptadores.AlmacenLogTexto import AlmacenLogTexto
        from tests_labs.escenarios_niebla import CARPETA_REPLAYS, ESCENARIOS, firma
        for escenario in ESCENARIOS:
            with self.subTest(escenario=escenario.nombre):
                ruta = os.path.join(CARPETA_REPLAYS, escenario.nombre + ".log")
                self.assertTrue(os.path.exists(ruta), f"falta {ruta}: ejecuta python -m tests_labs.escenarios_niebla")
                log = AlmacenLogTexto.leer(escenario.nombre, CARPETA_REPLAYS)
                self.assertEqual(firma(escenario.repetir(log)), firma(escenario.jugar()))

    def escenario(self, prefijo):
        from tests_labs.escenarios_niebla import ESCENARIOS
        return [e for e in ESCENARIOS if e.nombre.startswith(prefijo)][0]

    def test_FR208_APENDICE_B_el_escenario_deja_la_puerta_recordada_cerrada_tras_volver(self):
        logica = self.escenario("FR208").jugar()
        self.assertEqual(logica.mapaConocido.puerta_recordada(1, 2), 2)

    def test_FR210_APENDICE_B_el_escenario_explora_las_vecinas_sin_activar_enemigos(self):
        logica = self.escenario("FR210").jugar()
        self.assertEqual([logica.mapaConocido.estado_de(i) for i in (3, 4, 5)], [2, 2, 2])
        self.assertTrue(all(not e.activo for e in logica.estadoJuego.catalogo_enemigos))

    def test_FR214_APENDICE_B_el_escenario_deja_las_vecinas_como_antes_de_entrar(self):
        logica = self.escenario("FR214").jugar()
        self.assertEqual([logica.mapaConocido.estado_de(i) for i in (1, 2, 3, 4, 5)], [2, 1, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
