"""Historia 2: el cazador persigue por la ruta de menor costo. Cada prueba cita el requisito que demuestra."""
import unittest

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from Controlador.ControladorJuego import ControladorJuego
from Logica.CampoDeCostos import CampoDeCostos
from Logica.CompCazador import ComportamientoCazador
from Logica.MapaCripta import MapaCripta
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_lineal, ficha_cazador
from tests_labs.partida_prueba import esperar, nueva_partida, pendientes


class Escenario:
    """Un cazador y un jugador sobre un esqueleto, con las salas del modelo armadas por el servicio real."""

    def __init__(self, esqueleto, sala_jugador, sala_cazador, rango=600, cargadas=None):
        api = HttpConfigurable(esqueleto, [(sala_cazador, "e-1", "ent_cazador", None)], [ficha_cazador(rango=rango)],
                               sala_inicial=sala_jugador)
        self.servicio = ServicioCripta(api, CacheLRU(25))
        self.servicio.listar_criptas()
        cripta = self.servicio.obtener_id_cripta(1)
        self.jugador = self.servicio.crear_jugador(cripta)
        construidas = self.servicio.construir_salas(cripta, [s["id"] for s in esqueleto])
        self.salas = [None] * (len(esqueleto) + 1)
        for sala in construidas:
            if cargadas is None or sala.id in cargadas or sala.id in (sala_jugador, sala_cazador):
                self.salas[sala.id] = sala
        self.cazador = construidas[sala_cazador - 1].enemigos[0]
        self.campo = CampoDeCostos(MapaCripta(self.servicio.obtener_mapa(cripta)), self.jugador, self.salas)

    def turno(self):
        return ComportamientoCazador.acción(self.cazador, self.salas, None, None, self.campo)


class TestDecisionDelCazador(unittest.TestCase):
    def test_FR111_FR113_sigue_la_ruta_de_menor_costo_aunque_tenga_mas_salas(self):
        # 1 -> 2 directo cuesta 500; 1 -> 3 -> 4 -> 2 cuesta 300
        esqueleto = esqueleto_de_conexiones([(1, 2, 500, "E", "O"), (1, 3, 100, "S", "N"),
                                             (3, 4, 100, "E", "O"), (4, 2, 100, "N", "S")])
        e = Escenario(esqueleto, sala_jugador=2, sala_cazador=1)
        accion = e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 3)
        self.assertEqual(accion.costo, 100)

    def test_FR113_el_costo_de_la_accion_es_el_costo_de_la_salida_que_cruza(self):
        e = Escenario(esqueleto_lineal([250]), sala_jugador=2, sala_cazador=1)
        accion = e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 2)
        self.assertEqual(accion.costo, 250)

    def test_FR114_con_rutas_de_igual_costo_va_a_la_vecina_de_menor_id(self):
        esqueleto = esqueleto_de_conexiones([(1, 3, 100, "E", "O"), (1, 2, 100, "S", "N"),
                                             (3, 4, 100, "E", "O"), (2, 4, 100, "S", "N")])
        e = Escenario(esqueleto, sala_jugador=4, sala_cazador=1)
        e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 2)

    def test_FR114_con_muchas_rutas_de_igual_costo_siempre_gana_el_menor_id(self):
        conexiones = []
        letras = ("N", "S", "E", "O")
        for vecina in range(2, 6):
            conexiones.append((1, vecina, 100, letras[vecina - 2], "X"))
            conexiones.append((vecina, 6, 100, "S", letras[vecina - 2]))
        esqueleto = esqueleto_de_conexiones(conexiones)
        e = Escenario(esqueleto, sala_jugador=6, sala_cazador=1)
        e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 2)

    def test_FR114_el_menor_id_solo_cuenta_entre_las_rutas_de_costo_minimo(self):
        # la vecina 2 lleva al jugador por 100 + 900; la vecina 3 por 100 + 100
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (1, 3, 100, "S", "N"),
                                             (2, 4, 900, "E", "O"), (3, 4, 100, "E", "O")])
        e = Escenario(esqueleto, sala_jugador=4, sala_cazador=1, rango=2000)
        e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 3)

    def test_FR112_sin_ruta_abierta_espera_con_costo_100(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O", {"cerrada": True})])
        e = Escenario(esqueleto, sala_jugador=2, sala_cazador=1)
        accion = e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 1)
        self.assertEqual(accion.costo, 100)

    def test_FR115_no_abre_puertas_cerradas(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O", {"cerrada": True})])
        e = Escenario(esqueleto, sala_jugador=2, sala_cazador=1)
        e.turno()
        self.assertTrue(all(s.cerrada for s in e.salas[1].salidas))

    def test_FR115_con_la_ruta_corta_cerrada_toma_la_abierta_aunque_cueste_mas(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O", {"cerrada": True}), (1, 3, 100, "S", "N"),
                                             (3, 2, 400, "E", "O")])
        e = Escenario(esqueleto, sala_jugador=2, sala_cazador=1, rango=1000)
        e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 3)

    def test_FR112_si_el_costo_minimo_supera_el_rango_espera_con_costo_100(self):
        e = Escenario(esqueleto_lineal([300]), sala_jugador=2, sala_cazador=1, rango=299)
        accion = e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 1)
        self.assertEqual(accion.costo, 100)

    def test_FR112_si_el_costo_minimo_es_igual_al_rango_se_mueve(self):
        e = Escenario(esqueleto_lineal([300]), sala_jugador=2, sala_cazador=1, rango=300)
        e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 2)

    def test_FR108_rango_0_declarado_solo_ataca_en_su_sala(self):
        e = Escenario(esqueleto_lineal([100]), sala_jugador=2, sala_cazador=1, rango=0)
        accion = e.turno()
        self.assertEqual(e.cazador.rango, 0)
        self.assertEqual(e.cazador.id_sala_actual, 1)
        self.assertEqual(accion.costo, 100)
        self.assertEqual(e.servicio.advertencias, [])

    def test_FR108_rango_ausente_o_invalido_vale_0_con_advertencia(self):
        for rango in (None, -5, 2.5, True):
            with self.subTest(rango=rango):
                e = Escenario(esqueleto_lineal([100]), sala_jugador=2, sala_cazador=1, rango=rango)
                self.assertEqual(e.cazador.rango, 0)
                e.turno()
                self.assertEqual(e.cazador.id_sala_actual, 1)
                self.assertEqual(len(e.servicio.advertencias), 1)
                self.assertIn("ent_cazador", e.servicio.advertencias[0])

    def test_FR117_la_decision_no_depende_de_que_salas_esten_descargadas(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (1, 3, 100, "S", "N"),
                                             (2, 4, 100, "E", "O"), (3, 4, 100, "S", "N")])
        todas = Escenario(esqueleto, sala_jugador=4, sala_cazador=1)
        pocas = Escenario(esqueleto, sala_jugador=4, sala_cazador=1, cargadas=[])
        self.assertIsNone(pocas.salas[2])
        self.assertIsNone(pocas.salas[3])
        a, b = todas.turno(), pocas.turno()
        self.assertEqual(todas.cazador.id_sala_actual, pocas.cazador.id_sala_actual)
        self.assertEqual(a.costo, b.costo)

    def test_FR124_una_conexion_de_un_solo_sentido_solo_se_usa_en_ese_sentido(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O", {"un_sentido": True})])
        de_ida = Escenario(esqueleto, sala_jugador=2, sala_cazador=1)
        de_ida.turno()
        self.assertEqual(de_ida.cazador.id_sala_actual, 2)
        de_vuelta = Escenario(esqueleto, sala_jugador=1, sala_cazador=2)
        accion = de_vuelta.turno()
        self.assertEqual(de_vuelta.cazador.id_sala_actual, 2)
        self.assertEqual(accion.costo, 100)

    def test_FR111_el_estado_de_las_puertas_se_lee_en_el_instante_de_decidir(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (1, 3, 100, "S", "N"), (3, 2, 100, "E", "O")])
        e = Escenario(esqueleto, sala_jugador=2, sala_cazador=1, rango=1000)
        for salida in e.salas[1].salidas:             # la salida directa a la sala 2 se cierra antes de su turno
            if salida.sala_destino == 2:
                salida.cerrada = True
        e.turno()
        self.assertEqual(e.cazador.id_sala_actual, 3)


class TestCazadorEnPartida(unittest.TestCase):
    """El cazador integrado al reloj, al gestor de eventos y a la fábrica de comportamientos."""

    def partida(self, esqueleto, sala_cazador, sala_jugador, rango=1000):
        return nueva_partida(esqueleto, [(sala_cazador, "e-1", "ent_cazador", None)], [ficha_cazador(rango=rango)],
                             sala_inicial=sala_jugador)

    def test_FR110_en_la_misma_sala_que_el_jugador_ataca_y_su_siguiente_accion_cuesta_100(self):
        logica = self.partida(esqueleto_lineal([300]), sala_cazador=1, sala_jugador=1)
        vida = logica.estadoJuego.jugador.vida_actual
        esperar(logica)
        self.assertLess(logica.estadoJuego.jugador.vida_actual, vida)
        self.assertEqual(logica.estadoJuego.salas[1].enemigos[0].id_sala_actual, 1)
        self.assertEqual(pendientes(logica, "ACCION_ENEMIGO")[0].tiempo_ejecucion, 200)

    def test_FR113_el_cazador_persigue_y_su_siguiente_accion_se_programa_con_el_costo_de_la_salida(self):
        # el cazador y el jugador empiezan en la sala 2; el jugador se va a la 1 (cuesta 300)
        logica = self.partida(esqueleto_lineal([300]), sala_cazador=2, sala_jugador=2)
        cazador = logica.estadoJuego.salas[2].enemigos[0]
        sala = logica.estadoJuego.salas[2]
        logica.accionJugador(ControladorJuego(None)._mapear_entrada_a_evento("oeste", sala, logica.estadoJuego.jugador))
        self.assertEqual(cazador.id_sala_actual, 1)                      # a t=100 lo siguió
        self.assertEqual(pendientes(logica, "ACCION_ENEMIGO")[0].tiempo_ejecucion, 100 + 300)

    def test_FR109_la_puerta_que_se_cierra_despues_de_iniciar_el_cruce_no_lo_cancela(self):
        logica = self.partida(esqueleto_lineal([300]), sala_cazador=2, sala_jugador=2)
        cazador = logica.estadoJuego.salas[2].enemigos[0]
        sala = logica.estadoJuego.salas[2]
        logica.accionJugador(ControladorJuego(None)._mapear_entrada_a_evento("oeste", sala, logica.estadoJuego.jugador))
        for s in logica.estadoJuego.salas[2].salidas:               # la puerta se cierra con el cruce ya iniciado
            s.cerrada = True
        self.assertEqual(cazador.id_sala_actual, 1)                      # el cruce ya está hecho
        self.assertIn(cazador, logica.estadoJuego.salas[1].enemigos)

    def test_FR120_el_cazador_no_usa_azar_la_misma_partida_da_lo_mismo(self):
        def jugar_dos_turnos(semilla):
            logica = nueva_partida(esqueleto_lineal([100, 100]), [(3, "e-1", "ent_cazador", None)],
                                   [ficha_cazador(rango=1000)], semilla=semilla, sala_inicial=3)
            sala = logica.estadoJuego.salas[3]
            logica.accionJugador(ControladorJuego(None)._mapear_entrada_a_evento("oeste", sala, logica.estadoJuego.jugador))
            esperar(logica, 3)
            cazador = logica.estadoJuego.catalogo_enemigos[0]
            return (cazador.id_sala_actual, cazador.vida_actual, logica.estadoJuego.jugador.vida_actual,
                    logica.estadoJuego.reloj.tiempo_actual)
        self.assertEqual(jugar_dos_turnos(1), jugar_dos_turnos(1))


if __name__ == "__main__":
    unittest.main()
