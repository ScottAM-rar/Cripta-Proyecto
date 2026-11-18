"""Niebla de guerra (capacidad 002), historia 4: el pergamino de retroceso también deshace lo descubierto.
Contrato: specs/002-niebla-de-guerra/contracts/cambios-deshacibles.md. Cada prueba cita el requisito que demuestra."""
import random
import unittest

from DTO.Objeto import PergaminoRetroceso
from Logica.MapaConocido import DESCONOCIDA, AVISTADA, EXPLORADA, ABIERTA, CERRADA
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_rejilla
from tests_labs.partida_prueba import esperar, jugar, nueva_partida
from tests_labs.referencia_conocimiento import capturar_reales, comprobar_invariantes, diferencias, reconstruir

ESTE = 2


def mover(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "MOVER_JUGADOR", [sala, direccion])


def abrir(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "ABRIR_PUERTA", [sala, direccion])


def pergamino(logica):
    objeto = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
    logica.estadoJuego.jugador.inventario.agregar_objeto(objeto)
    return jugar(logica, "USAR_OBJETO", [objeto])


def foto(logica):
    c = logica.mapaConocido
    return (list(c.estado), list(c.puertas), list(c.exploradas))


def cripta_en_cruz():
    return esqueleto_de_conexiones([
        (1, 2, None, "E", "O"), (2, 3, None, "E", "O"),
        (2, 4, None, "S", "N", {"cerrada": True}), (2, 5, None, "N", "S"),
    ])


class TestPergaminoYConocimiento(unittest.TestCase):
    def test_FR214_APENDICE_B_el_pergamino_revierte_una_entrada_con_antorcha(self):
        logica = nueva_partida(cripta_en_cruz())
        logica.estadoJuego.jugador.antorcha_encendida = True
        antes = foto(logica)
        mover(logica, "este")
        c = logica.mapaConocido
        self.assertEqual([c.estado_de(i) for i in (2, 3, 4, 5)], [EXPLORADA] * 4)
        pergamino(logica)
        self.assertEqual(foto(logica), antes)
        self.assertEqual([c.estado_de(i) for i in (1, 2, 3, 4, 5)], [EXPLORADA, AVISTADA, DESCONOCIDA, DESCONOCIDA, DESCONOCIDA])

    def test_FR214_entrada_sin_antorcha_la_sala_vuelve_a_avistada_y_sus_avistadas_a_desconocidas(self):
        logica = nueva_partida(cripta_en_cruz())
        antes = foto(logica)
        mover(logica, "este")
        pergamino(logica)
        self.assertEqual(foto(logica), antes)
        c = logica.mapaConocido
        self.assertEqual(c.estado_de(2), AVISTADA)
        self.assertEqual(c.estado_de(3), DESCONOCIDA)

    def test_FR214_el_mapa_vuelve_a_recordar_el_estado_anterior_de_una_puerta_observada(self):
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"cerrada": True}), (2, 3, None, "E", "O")])
        salas[0]["salidas"]["E"]["cierre_automatico"] = 300
        logica = nueva_partida(salas)
        c = logica.mapaConocido
        abrir(logica, "este")
        mover(logica, "este")
        mover(logica, "este")
        esperar(logica, 3)                                                  # la puerta 1->2 se cerró lejos
        self.assertEqual(c.puerta_recordada(1, ESTE), ABIERTA)
        antes = foto(logica)
        mover(logica, "oeste")                                              # la observa cerrada
        self.assertEqual(c.puerta_recordada(1, ESTE), CERRADA)
        pergamino(logica)
        self.assertEqual(foto(logica), antes)
        self.assertEqual(c.puerta_recordada(1, ESTE), ABIERTA)

    def test_FR214_deshacer_la_apertura_de_una_puerta_junto_al_jugador_restaura_lo_recordado(self):
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"cerrada": True})])
        logica = nueva_partida(salas)
        c = logica.mapaConocido
        antes = foto(logica)
        abrir(logica, "este")
        self.assertEqual(c.puerta_recordada(1, ESTE), ABIERTA)
        pergamino(logica)
        self.assertEqual(foto(logica), antes)
        self.assertTrue(logica.estadoJuego.salas[1].salidas[0].cerrada)
        self.assertEqual(comprobar_invariantes(c, c.mapa, logica.estadoJuego.salas, logica.estadoJuego.jugador), [])

    def test_FR215_sin_historial_el_conocimiento_del_instante_cero_sigue_intacto(self):
        logica = nueva_partida(cripta_en_cruz())
        antes = foto(logica)
        resultado = pergamino(logica)
        self.assertFalse(resultado.exito)
        self.assertEqual(foto(logica), antes)
        c = logica.mapaConocido
        self.assertEqual((c.estado_de(1), c.estado_de(2)), (EXPLORADA, AVISTADA))

    def test_FR215_el_conocimiento_del_instante_cero_no_se_deshace_ni_con_cinco_pergaminos(self):
        logica = nueva_partida(cripta_en_cruz())
        inicial = foto(logica)
        mover(logica, "este")
        for _ in range(5):
            pergamino(logica)
        self.assertEqual(foto(logica), inicial)

    def test_FR214_cinco_acciones_y_cinco_pergaminos_devuelven_el_conocimiento_previo_a_la_primera(self):
        logica = nueva_partida(esqueleto_rejilla(4, 4, semilla=5))
        inicial = foto(logica)
        for direccion in ("este", "este", "sur", "sur", "oeste"):
            mover(logica, direccion)
        self.assertNotEqual(foto(logica), inicial)
        for _ in range(5):
            pergamino(logica)
        self.assertEqual(foto(logica), inicial)

    def test_FR214_una_accion_rechazada_no_cambia_el_conocimiento(self):
        logica = nueva_partida(cripta_en_cruz())
        antes = foto(logica)
        version = logica.mapaConocido.version_conocimiento
        resultado = mover(logica, "norte")                                  # la sala 1 no tiene salida al norte
        self.assertFalse(resultado.exito)
        self.assertEqual(foto(logica), antes)
        self.assertEqual(logica.mapaConocido.version_conocimiento, version)

    def test_FR214_lo_descubierto_en_acciones_que_salen_del_historial_se_conserva(self):
        logica = nueva_partida(esqueleto_rejilla(5, 1))
        for _ in range(4):
            mover(logica, "este")                                           # llega a la sala 5
        esperar(logica, 4)                                                  # 8 acciones; el historial guarda solo las últimas 5
        for _ in range(5):
            pergamino(logica)                                               # deshace el último paso y las cuatro esperas
        c = logica.mapaConocido
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 4)
        self.assertEqual(c.estado_de(4), EXPLORADA)                         # esa exploración ya había salido del historial
        self.assertEqual(c.estado_de(5), AVISTADA)                          # la de la sala 5 sí se deshizo
        self.assertEqual(c.estado_de(1), EXPLORADA)

    def test_FR225_la_version_del_conocimiento_sube_tambien_al_deshacer(self):
        logica = nueva_partida(cripta_en_cruz())
        mover(logica, "este")
        version = logica.mapaConocido.version_conocimiento
        pergamino(logica)
        self.assertGreater(logica.mapaConocido.version_conocimiento, version)


class TestEquivalenciaConLaReferencia(unittest.TestCase):
    """SC-003 y principio III: el conocimiento incremental coincide con el reconstruido desde cero tras cada acción
    y cada deshacer, en recorridos aleatorios con semilla fija."""

    def recorrido(self, semilla):
        azar = random.Random(semilla)
        logica = nueva_partida(esqueleto_rejilla(5, 5, semilla=semilla, fraccion_cerradas=0.0), semilla=semilla)
        c = logica.mapaConocido
        salas = logica.estadoJuego.salas
        jugador = logica.estadoJuego.jugador
        grupos = [[("entrar", jugador.id_sala_actual, False, capturar_reales(c.mapa, salas, jugador.id_sala_actual))]]
        deshacibles = 0
        for _ in range(60):
            opcion = azar.random()
            if opcion < 0.15:
                resultado = pergamino(logica)
                if deshacibles > 0:
                    self.assertTrue(resultado.exito)
                    grupos.pop()
                    deshacibles -= 1
                else:
                    self.assertFalse(resultado.exito)
            elif opcion < 0.25:
                esperar(logica)
                grupos.append([])
                deshacibles = min(5, deshacibles + 1)
            else:
                antorcha = azar.random() < 0.4
                jugador.antorcha_encendida = antorcha
                sala = salas[jugador.id_sala_actual]
                direccion = azar.choice([s.direccion for s in sala.salidas])
                mover(logica, str(direccion.value if hasattr(direccion, "value") else direccion))
                actual = jugador.id_sala_actual
                grupos.append([("entrar", actual, antorcha, capturar_reales(c.mapa, salas, actual))])
                deshacibles = min(5, deshacibles + 1)
            historia = []
            for grupo in grupos:
                historia.extend(grupo)
            self.assertEqual(diferencias(c, reconstruir(c.mapa, historia)), [])
            self.assertEqual(comprobar_invariantes(c, c.mapa, salas, jugador, con_puertas=True), [])

    def test_FR214_SC003_recorridos_aleatorios_coinciden_con_la_referencia(self):
        for semilla in (1, 2, 3, 4, 5):
            with self.subTest(semilla=semilla):
                self.recorrido(semilla)


if __name__ == "__main__":
    unittest.main()
