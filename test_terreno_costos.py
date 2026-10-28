"""Historia 1 (costo de las salidas) y datos de entrada. Cada prueba cita el requisito que demuestra."""
import contextlib
import io
import os
import tempfile
import unittest

from adaptadores import AlmacenPartidaBinario as modulo_partida
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from Controlador.ControladorJuego import ControladorJuego
from Controlador.Vista import VistaConsola
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RelojVirtual import RelojVirtual
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_lineal, esqueleto_rejilla, ficha_cazador, ficha_enemigo
from tests_labs.partida_prueba import esperar, jugar, nueva_partida, pendientes


def costos_de(logica, sala):
    return [(s.direccion, s.sala_destino, s.costo) for s in logica.estadoJuego.salas[sala].salidas]


class TestCostoDeLasSalidas(unittest.TestCase):
    def test_FR101_salida_sin_costo_declarado_vale_100(self):
        logica = nueva_partida(esqueleto_lineal([None]))
        self.assertEqual(costos_de(logica, 1), [("este", 2, 100)])

    def test_FR101_esqueleto_de_la_parte_I_sin_costos_sigue_siendo_valido(self):
        logica = nueva_partida(esqueleto_rejilla(3, 3))
        self.assertEqual(logica.comunicacion.advertencias, [])
        for sala in range(1, 10):
            logica.ingresarEnSala(sala)
            for _, _, costo in costos_de(logica, sala):
                self.assertEqual(costo, 100)

    def test_FR102_el_costo_es_el_mismo_en_ambos_sentidos(self):
        logica = nueva_partida(esqueleto_lineal([250]))
        logica.ingresarEnSala(2)
        self.assertEqual(costos_de(logica, 1), [("este", 2, 250)])
        self.assertEqual(costos_de(logica, 2), [("oeste", 1, 250)])

    def test_FR102_costos_distintos_en_los_dos_lados_gana_la_sala_de_menor_id_y_se_advierte(self):
        salas = esqueleto_lineal([250])
        salas[1]["salidas"]["O"]["costo"] = 400
        logica = nueva_partida(salas)
        logica.ingresarEnSala(2)
        self.assertEqual(costos_de(logica, 1), [("este", 2, 250)])
        self.assertEqual(costos_de(logica, 2), [("oeste", 1, 250)])
        self.assertEqual(len(logica.comunicacion.advertencias), 1)
        self.assertIn("250", logica.comunicacion.advertencias[0])
        self.assertIn("400", logica.comunicacion.advertencias[0])

    def test_FR102_si_solo_un_lado_declara_costo_vale_para_ambos(self):
        salas = esqueleto_lineal([None])
        salas[1]["salidas"]["O"]["costo"] = 250
        logica = nueva_partida(salas)
        logica.ingresarEnSala(2)
        self.assertEqual(costos_de(logica, 1), [("este", 2, 250)])
        self.assertEqual(costos_de(logica, 2), [("oeste", 1, 250)])
        self.assertEqual(logica.comunicacion.advertencias, [])

    def test_FR124_conexion_de_un_solo_sentido(self):
        salas = esqueleto_lineal([250])
        del salas[1]["salidas"]["O"]
        logica = nueva_partida(salas)
        logica.ingresarEnSala(2)
        self.assertEqual(costos_de(logica, 1), [("este", 2, 250)])
        self.assertEqual(costos_de(logica, 2), [])

    def test_FR101_costo_invalido_vale_100_con_advertencia(self):
        for invalido in (0, -5, 2.5, True, "7"):
            with self.subTest(costo=invalido):
                salas = esqueleto_lineal([None])
                salas[0]["salidas"]["E"]["costo"] = invalido
                logica = nueva_partida(salas)
                logica.ingresarEnSala(2)
                self.assertEqual(costos_de(logica, 1), [("este", 2, 100)])
                self.assertEqual(costos_de(logica, 2), [("oeste", 1, 100)])
                self.assertEqual(len(logica.comunicacion.advertencias), 1)
                self.assertIn(repr(invalido), logica.comunicacion.advertencias[0])
                self.assertIn("Sala 1", logica.comunicacion.advertencias[0])


class TestMovimientoConCosto(unittest.TestCase):
    def evento_de_mover(self, logica, direccion):
        sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
        return ControladorJuego(None)._mapear_entrada_a_evento(direccion, sala, logica.estadoJuego.jugador)

    def test_FR103_el_jugador_tarda_lo_que_cuesta_la_salida(self):
        logica = nueva_partida(esqueleto_lineal([250]))
        evento = self.evento_de_mover(logica, "este")
        self.assertEqual(evento.tiempo_ejecucion, 250)
        logica.accionJugador(evento)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 2)
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 250)

    def test_FR103_sin_costo_declarado_el_jugador_tarda_100(self):
        logica = nueva_partida(esqueleto_lineal([None]))
        logica.accionJugador(self.evento_de_mover(logica, "este"))
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 100)

    def test_FR104_el_intervalo_nunca_baja_de_1(self):
        self.assertEqual(RelojVirtual.intervalo_por_velocidad(1, 100_000), 1)
        logica = nueva_partida(esqueleto_lineal([1]))
        logica.estadoJuego.jugador.velocidad = 100_000
        logica.accionJugador(self.evento_de_mover(logica, "este"))
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 1)

    def test_FR104_la_formula_de_intervalo_usa_el_costo_de_la_salida(self):
        logica = nueva_partida(esqueleto_lineal([250]))
        logica.estadoJuego.jugador.velocidad = 200
        logica.accionJugador(self.evento_de_mover(logica, "este"))
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 250 * 100 // 200)

    def test_FR105_cambio_de_velocidad_en_pleno_cruce_reescala_el_tiempo_restante(self):
        logica = nueva_partida(esqueleto_lineal([250]))
        reloj = logica.estadoJuego.reloj
        jugador = logica.estadoJuego.jugador
        reloj.programar(250, jugador, "TURNO_JUGADOR", [])
        reloj.reajustar_velocidad(jugador, 100, 200)
        turnos = [e for e in reloj.heap if e.actor is jugador and e.tipo_accion == "TURNO_JUGADOR"]
        self.assertEqual(len(turnos), 1)
        self.assertEqual(turnos[0].tiempo_ejecucion, reloj.tiempo_actual + 125)

    def _enemigo_que_queda_solo_en_la_sala_2(self, comportamiento):
        """Cripta 1 --300-- 2. El jugador y el enemigo empiezan en la sala 2; el jugador se va a la sala 1 (cuesta 300),
        así que a t=100 el enemigo ya no comparte sala con él y se mueve por su única salida."""
        logica = nueva_partida(esqueleto_lineal([300]), [(2, "e-1", "ent_prueba", None)],
                               [ficha_enemigo("ent_prueba", comportamiento)], sala_inicial=2)
        enemigo = logica.estadoJuego.salas[2].enemigos[0]
        sala = logica.estadoJuego.salas[2]
        logica.accionJugador(ControladorJuego(None)._mapear_entrada_a_evento("oeste", sala, logica.estadoJuego.jugador))
        return logica, enemigo

    def test_FR106_un_errante_tarda_lo_que_cuesta_la_salida_y_conserva_su_destino(self):
        logica, enemigo = self._enemigo_que_queda_solo_en_la_sala_2("errante")
        self.assertEqual(enemigo.id_sala_actual, 1)                      # su única salida lleva a la sala 1
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 300)
        self.assertEqual(pendientes(logica, "ACCION_ENEMIGO")[0].tiempo_ejecucion, 100 + 300)

    def test_FR106_un_rastreador_tarda_lo_que_cuesta_la_salida_y_conserva_su_destino(self):
        logica, enemigo = self._enemigo_que_queda_solo_en_la_sala_2("rastreador")
        self.assertEqual(enemigo.id_sala_actual, 1)                      # sigue el rastro del jugador
        self.assertEqual(pendientes(logica, "ACCION_ENEMIGO")[0].tiempo_ejecucion, 100 + 300)

    def test_FR107_atacar_y_esperar_siguen_costando_100(self):
        logica = nueva_partida(esqueleto_lineal([300]), [(1, "e-1", "ent_guardian", None)],
                               [ficha_enemigo("ent_guardian", "guardián")])
        esperar(logica)                                  # esperar cuesta 100
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 100)
        # el enemigo comparte sala con el jugador: ataca y su siguiente acción es 100 después, no 300
        self.assertEqual(pendientes(logica, "ACCION_ENEMIGO")[0].tiempo_ejecucion, 200)


class TestVista(unittest.TestCase):
    def mostrar(self, logica):
        jugador = logica.estadoJuego.jugador
        sala = logica.estadoJuego.salas[jugador.id_sala_actual]
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            VistaConsola().mostrar_juego(jugador, sala, None, [])
        return salida.getvalue()

    def test_FR130_cada_salida_muestra_su_costo(self):
        salas = esqueleto_lineal([250, None])
        salas[1]["salidas"]["E"]["costo"] = 70
        texto = self.mostrar(nueva_partida(salas, sala_inicial=2))
        self.assertIn("Sala 3", texto)
        self.assertIn("costo 70", texto)
        self.assertIn("costo 250", texto)

    def test_FR130_una_salida_sin_costo_declarado_muestra_100(self):
        texto = self.mostrar(nueva_partida(esqueleto_lineal([None])))
        self.assertIn("costo 100", texto)

    def test_FR131_el_cazador_se_distingue_de_los_demas_enemigos(self):
        logica = nueva_partida(esqueleto_lineal([100]), [(1, "e-1", "ent_cazador", None), (1, "e-2", "ent_guardian", None)],
                               [ficha_cazador(), ficha_enemigo("ent_guardian", "guardián")])
        lineas = [l for l in self.mostrar(logica).splitlines() if "Vida:" in l and "JUGADOR" not in l]
        cazadores = [l for l in lineas if "[CAZADOR]" in l]
        otros = [l for l in lineas if "[CAZADOR]" not in l]
        self.assertEqual(len(cazadores), 1)
        self.assertEqual(len(otros), 1)

    def test_FR118_las_advertencias_de_datos_se_muestran_una_sola_vez(self):
        class ServicioFalso:
            def __init__(self):
                self.advertencias = ["Sala 1, salida E: costo inválido 0; se usa 100"]

            def advertenciasDeDatos(self):
                return list(self.advertencias)

        servicio = ServicioFalso()
        controlador = ControladorJuego(servicio)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            controlador._mostrar_advertencias_nuevas()
            controlador._mostrar_advertencias_nuevas()
            servicio.advertencias.append("Ficha ent_cazador: cazador sin rango; se usa 0 (solo ataca en su sala)")
            controlador._mostrar_advertencias_nuevas()
        texto = salida.getvalue()
        self.assertEqual(texto.count("costo inválido 0"), 1)
        self.assertEqual(texto.count("sin rango"), 1)


class TestPersistencia(unittest.TestCase):
    def guardar(self, logica):
        carpeta = tempfile.mkdtemp()
        archivo = os.path.join(carpeta, "partida.bin")
        AlmacenPartidaBinario(archivo).guardar(logica.exportar_estado())
        return archivo

    def test_FR119_guardar_y_restaurar_conserva_el_costo_de_cada_salida(self):
        salas = esqueleto_lineal([250, 70])
        logica = nueva_partida(salas)
        logica.ingresarEnSala(2)
        archivo = self.guardar(logica)
        cargada = EstadoJuegoLogica()
        cargada.comunicacion = ServicioCripta(HttpConfigurable(salas), CacheLRU(25))
        cargada.restaurar_estado(AlmacenPartidaBinario(archivo).cargar())
        self.assertEqual(costos_de(cargada, 1), [("este", 2, 250)])
        self.assertEqual(costos_de(cargada, 2), [("este", 3, 70), ("oeste", 1, 250)])

    def test_FR108_FR119_guardar_y_restaurar_conserva_el_rango_y_el_cazador_sigue_decidiendo(self):
        salas = esqueleto_lineal([300])
        fichas = [ficha_cazador(rango=777)]
        logica = nueva_partida(salas, [(2, "e-1", "ent_cazador", None)], fichas, sala_inicial=2)
        archivo = self.guardar(logica)
        cargada = EstadoJuegoLogica()
        cargada.comunicacion = ServicioCripta(HttpConfigurable(salas, [(2, "e-1", "ent_cazador", None)], fichas), CacheLRU(25))
        cargada.restaurar_estado(AlmacenPartidaBinario(archivo).cargar())
        cazador = cargada.estadoJuego.salas[2].enemigos[0]
        self.assertEqual(cazador.rango, 777)
        self.assertEqual(cazador.comportamiento, "cazador")
        sala = cargada.estadoJuego.salas[2]
        cargada.accionJugador(ControladorJuego(None)._mapear_entrada_a_evento("oeste", sala, cargada.estadoJuego.jugador))
        self.assertEqual(cazador.id_sala_actual, 1)                      # persigue con el mapa reconstruido

    def test_FR119_un_archivo_de_la_version_anterior_se_rechaza_con_mensaje_claro(self):
        archivo = self.guardar(nueva_partida(esqueleto_lineal([250])))
        with open(archivo, "r+b") as f:
            f.write(modulo_partida._ENCABEZADO.pack(modulo_partida.MAGIA, 5))
        with self.assertRaises(ErrorPartida) as contexto:
            AlmacenPartidaBinario(archivo).cargar()
        self.assertIn("5", str(contexto.exception))
        self.assertIn(str(modulo_partida.VERSION_FORMATO), str(contexto.exception))


if __name__ == "__main__":
    unittest.main()
