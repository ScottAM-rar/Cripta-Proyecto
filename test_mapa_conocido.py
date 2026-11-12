"""Niebla de guerra (capacidad 002), historias 1 a 3: estados de sala, memoria de puertas y antorcha.
Cada prueba cita el requisito que demuestra."""
import os
import re
import unittest

from DTO.EventoDTO import EventoDTO
from Logica.MapaConocido import MapaConocido, DESCONOCIDA, AVISTADA, EXPLORADA, SIN_OBSERVAR, ABIERTA, CERRADA
from Logica.MapaCripta import MapaCripta
from Logica.PuertasLogica import fijar_cerrada
from tests_labs.cripta_sintetica import (esqueleto_de_conexiones, esqueleto_rejilla, ficha_enemigo,
                                         mapa_dto_desde_esqueleto)
from tests_labs.partida_prueba import esperar, jugar, nueva_partida
from tests_labs.referencia_conocimiento import (capturar_reales, comprobar_invariantes, diferencias, reconstruir)

NORTE, SUR, ESTE, OESTE = 0, 1, 2, 3


def mover(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "MOVER_JUGADOR", [sala, direccion])


def abrir(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "ABRIR_PUERTA", [sala, direccion])


def invariantes(prueba, logica, con_puertas=False):
    c = logica.mapaConocido
    prueba.assertEqual(comprobar_invariantes(c, c.mapa, logica.estadoJuego.salas, logica.estadoJuego.jugador, con_puertas), [])


def estados(logica, ids):
    return [logica.mapaConocido.estado_de(i) for i in ids]


def cripta_en_cruz():
    """1 -E- 2 -E- 3 ; 2 -S- 4 (puerta cerrada) ; 2 -N- 5."""
    return esqueleto_de_conexiones([
        (1, 2, None, "E", "O"), (2, 3, None, "E", "O"),
        (2, 4, None, "S", "N", {"cerrada": True}), (2, 5, None, "N", "S"),
    ])


class TestNombresDelEsqueleto(unittest.TestCase):
    def test_FR206_obtener_mapa_conserva_el_nombre_de_cada_sala(self):
        mapa_dto = mapa_dto_desde_esqueleto(cripta_en_cruz())
        for i in range(1, 6):
            self.assertEqual(mapa_dto.salas[i].nombre, f"Sala {i}")

    def test_FR206_el_mapa_del_esqueleto_responde_igual_que_antes(self):
        mapa = MapaCripta(mapa_dto_desde_esqueleto(cripta_en_cruz()))
        self.assertEqual([(a.direccion, a.destino) for a in mapa.salidas(2)],
                         [("norte", 5), ("sur", 4), ("este", 3), ("oeste", 1)])
        self.assertEqual(mapa.total_salas(), 5)


class TestExplorarYAvistar(unittest.TestCase):
    def test_FR201_FR202_FR203_instante_cero(self):
        logica = nueva_partida(cripta_en_cruz())
        self.assertEqual(estados(logica, [1, 2, 3, 4, 5]), [EXPLORADA, AVISTADA, DESCONOCIDA, DESCONOCIDA, DESCONOCIDA])
        invariantes(self, logica)

    def test_FR204_FR206_entrar_a_una_avistada_la_explora(self):
        logica = nueva_partida(cripta_en_cruz())
        mover(logica, "este")
        self.assertEqual(logica.mapaConocido.estado_de(2), EXPLORADA)
        sala = logica.mapaConocido.sala_conocida(2)
        self.assertEqual(sala.nombre, "Sala 2")
        self.assertEqual([(s.direccion, s.costo) for s in sala.salidas],
                         [("norte", 100), ("sur", 100), ("este", 100), ("oeste", 100)])
        invariantes(self, logica)

    def test_FR203_FR204_las_tres_vecinas_quedan_avistadas_incluida_la_de_puerta_cerrada(self):
        logica = nueva_partida(cripta_en_cruz())
        mover(logica, "este")
        self.assertEqual(estados(logica, [3, 4, 5]), [AVISTADA, AVISTADA, AVISTADA])
        invariantes(self, logica)

    def test_FR203_de_una_avistada_solo_se_sabe_que_existe(self):
        logica = nueva_partida(cripta_en_cruz())
        mover(logica, "este")
        for s in logica.mapaConocido.sala_conocida(2).salidas:
            if s.destino_id is None:
                self.assertFalse(s.destino_explorado)
                self.assertEqual(s.destino_nombre, "")
        mapa = logica.mapaConocido.instantanea()
        self.assertEqual([s.id for s in mapa.salas], [1, 2])               # las avistadas no son salas del mapa

    def test_FR204_FR205_una_sala_ya_explorada_no_pasa_a_avistada(self):
        logica = nueva_partida(cripta_en_cruz())
        mover(logica, "este")
        mover(logica, "este")                                               # sala 3, con salida de vuelta a la 2
        self.assertEqual(logica.mapaConocido.estado_de(2), EXPLORADA)
        invariantes(self, logica)

    def test_FR205_FR207_reentrar_no_cambia_ningun_estado(self):
        logica = nueva_partida(cripta_en_cruz())
        mover(logica, "este")
        mover(logica, "oeste")
        antes = (list(logica.mapaConocido.estado), list(logica.mapaConocido.puertas), logica.mapaConocido.version_conocimiento)
        mover(logica, "este")
        despues = (list(logica.mapaConocido.estado), list(logica.mapaConocido.puertas), logica.mapaConocido.version_conocimiento)
        self.assertEqual(antes, despues)

    def test_FR203_una_salida_de_un_solo_sentido_no_avista_a_quien_no_tiene_salida(self):
        # la sala 2 tiene salida hacia la 1, pero la 1 no tiene salida hacia la 2
        salas = esqueleto_de_conexiones([(1, 3, None, "E", "O"), (2, 1, None, "N", "S", {"un_sentido": True})])
        logica = nueva_partida(salas)
        self.assertEqual(logica.mapaConocido.estado_de(2), DESCONOCIDA)
        self.assertEqual(logica.mapaConocido.estado_de(3), AVISTADA)
        invariantes(self, logica)

    def test_FR201_FR203_recorrido_largo_coincide_con_la_referencia(self):
        logica = nueva_partida(esqueleto_rejilla(4, 4, semilla=3))
        historia = []
        c = logica.mapaConocido
        salas = logica.estadoJuego.salas
        historia.append(("entrar", 1, False, capturar_reales(c.mapa, salas, 1)))
        for direccion in ("este", "este", "sur", "sur", "oeste", "norte", "este", "este", "sur"):
            mover(logica, direccion)
            actual = logica.estadoJuego.jugador.id_sala_actual
            historia.append(("entrar", actual, False, capturar_reales(c.mapa, salas, actual)))
            invariantes(self, logica, con_puertas=True)
            self.assertEqual(diferencias(c, reconstruir(c.mapa, historia)), [])


class TestMemoriaDePuertas(unittest.TestCase):
    def cripta(self):
        """1 -E- 2 -E- 3 -E- 4, con la puerta 1->2 cerrada y de cierre automático a los 300."""
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"cerrada": True}), (2, 3, None, "E", "O"), (3, 4, None, "E", "O")])
        salas[0]["salidas"]["E"]["cierre_automatico"] = 300
        return salas

    def test_FR208_APENDICE_B_el_mapa_recuerda_abierta_una_puerta_que_se_cerro_y_al_observarla_se_actualiza(self):
        logica = nueva_partida(self.cripta())
        c = logica.mapaConocido
        abrir(logica, "este")                                               # t=0; se cerrará sola a los 300
        mover(logica, "este")                                               # sala 2: observa la salida 1->2 (entrante) abierta
        self.assertEqual(c.puerta_recordada(1, ESTE), ABIERTA)
        mover(logica, "este")                                               # sala 3: lejos de la puerta 1->2
        esperar(logica, 3)                                                  # pasa el tiempo; la puerta se cierra sola
        real_cerrada = logica.estadoJuego.salas[1].salidas[0].cerrada
        self.assertTrue(real_cerrada)
        self.assertEqual(c.puerta_recordada(1, ESTE), ABIERTA)              # FR-208: el mapa conserva lo que recuerda
        mover(logica, "oeste")                                              # vuelve a la sala 2: observa la puerta
        self.assertEqual(c.puerta_recordada(1, ESTE), CERRADA)
        invariantes(self, logica, con_puertas=True)

    def test_FR208_FR219_desde_una_sala_lejana_la_puerta_figura_abierta_aunque_este_cerrada(self):
        logica = nueva_partida(self.cripta())
        abrir(logica, "este")
        mover(logica, "este")
        mover(logica, "este")
        esperar(logica, 3)
        mapa = logica.mapaConocido.instantanea()
        sala1 = [s for s in mapa.salas if s.id == 1][0]
        self.assertEqual(sala1.salidas[0].puerta, "abierta")

    def test_FR207_la_puerta_que_cambia_junto_al_jugador_se_observa_en_ese_instante(self):
        logica = nueva_partida(self.cripta())
        c = logica.mapaConocido
        self.assertEqual(c.puerta_recordada(1, ESTE), CERRADA)             # observada al iniciar
        abrir(logica, "este")
        self.assertEqual(c.puerta_recordada(1, ESTE), ABIERTA)             # la abre él
        esperar(logica, 3)                                                  # se cierra sola con él en la sala
        self.assertEqual(c.puerta_recordada(1, ESTE), CERRADA)
        invariantes(self, logica, con_puertas=True)

    def test_FR206_FR207_la_salida_hacia_una_avistada_se_recuerda_como_parte_de_la_sala_actual(self):
        logica = nueva_partida(self.cripta())
        mapa = logica.mapaConocido.instantanea()
        self.assertEqual(logica.mapaConocido.estado_de(2), AVISTADA)
        self.assertEqual([(s.direccion, s.puerta, s.destino_explorado) for s in mapa.salas[0].salidas], [("este", "cerrada", False)])

    def test_FR207_cada_salida_se_recuerda_por_separado_aunque_conecten_las_mismas_salas(self):
        logica = nueva_partida(self.cripta())
        c = logica.mapaConocido
        abrir(logica, "este")                                               # abre 1->2; la 2->1 sigue cerrada
        self.assertEqual(c.puerta_recordada(1, ESTE), ABIERTA)
        self.assertEqual(c.puerta_recordada(2, OESTE), CERRADA)             # observada como entrante a la sala 1

    def test_FR209_una_puerta_nunca_observada_figura_sin_observar(self):
        logica = nueva_partida(self.cripta())
        c = logica.mapaConocido
        self.assertEqual(c.puerta_recordada(2, ESTE), SIN_OBSERVAR)
        self.assertEqual(c.instantanea().salas[0].salidas[0].puerta, "cerrada")
        invariantes(self, logica, con_puertas=True)


class TestCaminosDeCambioDePuertas(unittest.TestCase):
    def cripta(self):
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"cerrada": True}), (2, 3, None, "E", "O")])
        salas[0]["salidas"]["E"]["cierre_automatico"] = 300
        return salas

    def contar(self, logica):
        llamadas = []
        original = logica.mapaConocido.puerta_cambio
        logica.mapaConocido.puerta_cambio = lambda salida: (llamadas.append(salida), original(salida))[1]
        return llamadas

    def test_FR207_todo_cambio_hacia_adelante_llega_al_conocimiento_y_el_del_pergamino_no(self):
        from DTO.Objeto import PergaminoRetroceso
        logica = nueva_partida(self.cripta())
        llamadas = self.contar(logica)
        abrir(logica, "este")
        self.assertEqual(len(llamadas), 1)                                  # abrir
        esperar(logica, 3)
        self.assertEqual(len(llamadas), 2)                                  # cierre automático
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        logica.estadoJuego.jugador.inventario.agregar_objeto(pergamino)
        jugar(logica, "USAR_OBJETO", [pergamino])                           # deshace una acción con cambios de puerta
        self.assertEqual(len(llamadas), 2)                                  # el aviso del pergamino no observa

    def test_FR208_un_cambio_de_puerta_lejos_del_jugador_no_registra_nada(self):
        logica = nueva_partida(self.cripta())
        abrir(logica, "este")
        mover(logica, "este")
        mover(logica, "este")                                               # sala 3
        antes = logica.mapaConocido.version_conocimiento
        esperar(logica, 3)                                                  # se cierra la puerta 1->2, lejos
        self.assertEqual(logica.mapaConocido.version_conocimiento, antes)

    def test_FR207_el_conocimiento_nunca_escribe_el_estado_de_una_puerta(self):
        ruta = os.path.join("Logica", "MapaConocido.py")
        patron = re.compile(r"\.cerrada\s*=(?!=)|setattr\([^)]*['\"]cerrada['\"]")
        with open(ruta, encoding="utf-8") as f:
            infractores = [l for l in f if patron.search(l.split("#")[0])]
        self.assertEqual(infractores, [])


def antorcha_encendida(logica):
    logica.estadoJuego.jugador.antorcha_encendida = True


class TestAntorcha(unittest.TestCase):
    def cripta(self):
        return cripta_en_cruz()

    def partida(self, antorcha):
        fichas = [ficha_enemigo("ent_x", "errante")]
        enemigos = [(3, "e-3", "ent_x", None), (4, "e-4", "ent_x", None), (5, "e-5", "ent_x", None)]
        logica = nueva_partida(self.cripta(), enemigos, fichas)
        if antorcha:
            antorcha_encendida(logica)
        return logica

    def test_FR210_FR211_FR213_APENDICE_B_la_antorcha_explora_las_vecinas_sin_activar_enemigos(self):
        logica = self.partida(True)
        mover(logica, "este")
        self.assertEqual(estados(logica, [1, 2, 3, 4, 5]), [EXPLORADA] * 5)
        for sala in (3, 4, 5):
            self.assertIsNone(logica.estadoJuego.salas[sala], "la antorcha no debe cargar el contenido de las vecinas")
        self.assertTrue(all(not e.activo for e in logica.estadoJuego.catalogo_enemigos))
        self.assertEqual([e for e in logica.estadoJuego.reloj.heap if e.tipo_accion == "ACCION_ENEMIGO"], [])
        invariantes(self, logica, con_puertas=True)

    def test_FR211_la_antorcha_no_gasta_solicitudes(self):
        con = self.partida(True)
        sin = self.partida(False)
        mover(con, "este")
        mover(sin, "este")
        self.assertEqual(con.comunicacion.cliente.solicitudes_realizadas, sin.comunicacion.cliente.solicitudes_realizadas)

    def test_FR211_FR206_de_una_vecina_explorada_solo_se_conoce_nombre_salidas_y_costos(self):
        logica = self.partida(True)
        mover(logica, "este")
        sala3 = [s for s in logica.mapaConocido.instantanea().salas if s.id == 3][0]
        self.assertEqual(sala3.nombre, "Sala 3")
        self.assertEqual([(s.direccion, s.costo) for s in sala3.salidas], [("oeste", 100)])

    def test_FR203_FR210_las_salidas_de_las_vecinas_quedan_avistadas(self):
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O"), (2, 3, None, "E", "O"), (3, 6, None, "E", "O")])
        logica = nueva_partida(salas)
        antorcha_encendida(logica)
        mover(logica, "este")
        self.assertEqual(estados(logica, [1, 2, 3, 6]), [EXPLORADA, EXPLORADA, EXPLORADA, AVISTADA])
        invariantes(self, logica, con_puertas=True)

    def test_FR210_una_vecina_detras_de_una_puerta_cerrada_tambien_queda_explorada(self):
        logica = self.partida(True)
        mover(logica, "este")
        self.assertEqual(logica.mapaConocido.estado_de(4), EXPLORADA)

    def test_FR204_FR210_con_la_antorcha_apagada_las_vecinas_solo_pasan_a_avistadas(self):
        logica = self.partida(False)
        mover(logica, "este")
        self.assertEqual(estados(logica, [3, 4, 5]), [AVISTADA] * 3)

    def test_FR212_encender_la_antorcha_dentro_de_una_sala_no_explora_hasta_la_siguiente_entrada(self):
        logica = self.partida(False)
        mover(logica, "este")
        antes = list(logica.mapaConocido.estado)
        antorcha_encendida(logica)
        esperar(logica, 2)
        self.assertEqual(list(logica.mapaConocido.estado), antes)
        mover(logica, "este")                                               # sala 3 con la antorcha encendida
        self.assertEqual(logica.mapaConocido.estado_de(3), EXPLORADA)

    def test_FR205_FR212_apagar_la_antorcha_no_quita_lo_explorado(self):
        logica = self.partida(True)
        mover(logica, "este")
        logica.estadoJuego.jugador.antorcha_encendida = False
        esperar(logica, 2)
        self.assertEqual(estados(logica, [3, 4, 5]), [EXPLORADA] * 3)

    def test_FR209_FR207_las_puertas_de_la_vecina_que_no_comparte_el_jugador_figuran_sin_observar(self):
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O"), (2, 3, None, "E", "O"), (3, 4, None, "E", "O")])
        logica = nueva_partida(salas)
        antorcha_encendida(logica)
        mover(logica, "este")                                               # entra a 2; la antorcha explora 3
        c = logica.mapaConocido
        self.assertEqual(c.puerta_recordada(3, OESTE), ABIERTA)             # comparte la conexión con la sala 2: observada
        self.assertEqual(c.puerta_recordada(3, ESTE), SIN_OBSERVAR)         # no la comparte
        logica.estadoJuego.jugador.antorcha_encendida = False
        mover(logica, "este")                                               # entra a 3: ahora la observa
        self.assertEqual(c.puerta_recordada(3, ESTE), ABIERTA)


class TestSinConocimiento(unittest.TestCase):
    def test_FR213_sin_conocimiento_el_juego_funciona_como_antes(self):
        from DTO.Objeto import PergaminoRetroceso
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"cerrada": True}), (2, 3, None, "E", "O")])
        logica = nueva_partida(salas)
        logica.mapaConocido = None
        logica.gestorEventos.mapa_conocido = None
        abrir(logica, "este")
        mover(logica, "este")
        mover(logica, "este")
        esperar(logica, 2)
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        logica.estadoJuego.jugador.inventario.agregar_objeto(pergamino)
        jugar(logica, "USAR_OBJETO", [pergamino])
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 3)      # el pergamino deshizo la espera


class TestSinProhibidos(unittest.TestCase):
    PROHIBIDOS = re.compile(r"\bdict\(|\bset\(|\bsorted\(|\.sort\(|heapq|bisect|collections|networkx|import requests|import socket")
    MODELO = re.compile(r"^\s*(import|from)\s+(Controlador|adaptadores|Servicio|requests|socket|input)\b", re.M)

    def test_I_IV_los_archivos_nuevos_no_usan_estructuras_prohibidas_ni_importan_vista_o_red(self):
        for ruta in (os.path.join("Logica", "MapaConocido.py"), os.path.join("DTO", "ConocimientoDTO.py")):
            with open(ruta, encoding="utf-8") as f:
                texto = f.read()
            codigo = "\n".join(l.split("#")[0] for l in texto.splitlines())
            self.assertIsNone(self.PROHIBIDOS.search(codigo), ruta)
            self.assertIsNone(self.MODELO.search(codigo), ruta)


class TestPuertaQueNoConectaLaSalaDelJugador(unittest.TestCase):
    """FR-207: el jugador solo observa las puertas de las dos salas que conecta cada una."""

    def test_FR207_una_puerta_ajena_no_se_observa_y_una_que_llega_a_la_sala_actual_si(self):
        logica = nueva_partida(esqueleto_de_conexiones([(1, 2, None, "E", "O"), (2, 3, None, "E", "O")]))
        mover(logica, "este")
        mover(logica, "oeste")                                              # la 2 queda explorada y el jugador en la 1
        c = logica.mapaConocido
        sala2 = logica.estadoJuego.salas[2]
        hacia_3 = [s for s in sala2.salidas if s.sala_destino == 3][0]      # no conecta con la sala 1
        hacia_1 = [s for s in sala2.salidas if s.sala_destino == 1][0]      # llega a la sala 1
        self.assertEqual(c.puerta_recordada(2, ESTE), ABIERTA)
        version = c.version_conocimiento
        fijar_cerrada(hacia_3, True, avisar=c.puerta_cambio)
        self.assertEqual(c.puerta_recordada(2, ESTE), ABIERTA)              # sigue recordando la anterior
        self.assertEqual(c.version_conocimiento, version)
        fijar_cerrada(hacia_1, True, avisar=c.puerta_cambio)
        self.assertEqual(c.puerta_recordada(2, OESTE), CERRADA)             # esta sí se observa desde la sala 1


if __name__ == "__main__":
    unittest.main()
