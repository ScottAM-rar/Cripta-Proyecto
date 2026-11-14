"""Niebla de guerra (capacidad 002), historia 5: ver el mapa conocido. Contrato: contracts/interfaz-vista.md.
Cada prueba cita el requisito que demuestra."""
import contextlib
import io
import unittest
from unittest import mock

from Controlador.ControladorJuego import ControladorJuego
from Controlador.Vista import VistaConsola
from DTO.ActorDTO import JugadorDTO
from DTO.ConocimientoDTO import MapaConocidoDTO, SalaConocidaDTO, SalidaConocidaDTO
from DTO.SalaDTO import SalaDTO
from Logica.RetrocesoLogica import RetrocesoLogica
from tests_labs.cripta_sintetica import esqueleto_de_conexiones
from tests_labs.partida_prueba import esperar, jugar, nueva_partida


def mover(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "MOVER_JUGADOR", [sala, direccion])


def imprimir(funcion, *args):
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        funcion(*args)
    return salida.getvalue()


def texto_mapa(logica):
    return imprimir(VistaConsola().mostrar_mapa_conocido, logica.instantaneaMapaConocido())


def texto_sala(logica):
    jugador = logica.estadoJuego.jugador
    sala = logica.estadoJuego.salas[jugador.id_sala_actual]
    return imprimir(VistaConsola().mostrar_juego, jugador, sala, logica.vistaSalaActual(), None, [])


def cadena(nombres=None, extra=None):
    """1 -E- 2 -E- 3 -E- 4; `nombres` cambia los nombres de las salas; `extra` agrega salidas a la sala 2 y a la 3."""
    salas = esqueleto_de_conexiones([(1, 2, None, "E", "O"), (2, 3, None, "E", "O"), (3, 4, None, "E", "O")])
    if nombres:
        for numero, nombre in nombres.items():
            salas[numero - 1]["nombre"] = nombre
    if extra:
        salas[1]["salidas"]["N"] = {"sala": 4}
        salas[2]["salidas"]["S"] = {"sala": 1}
    return salas


class TestMapaConocido(unittest.TestCase):
    def test_FR216_FR217_se_listan_las_exploradas_ascendentes_con_sus_salidas_y_las_avistadas_sin_nombre(self):
        logica = nueva_partida(cadena())
        mover(logica, "este")
        mover(logica, "este")
        mover(logica, "oeste")                                              # exploradas en orden 1, 2, 3; ahora en la 2
        texto = texto_mapa(logica)
        self.assertLess(texto.index("Sala 1 (id 1)"), texto.index("Sala 2 (id 2)"))
        self.assertLess(texto.index("Sala 2 (id 2)"), texto.index("Sala 3 (id 3)"))
        self.assertIn("sala sin explorar", texto)                            # la 4 está avistada
        self.assertNotIn("Sala 4", texto)
        self.assertIn(" * Sala 2 (id 2)", texto)                             # la sala actual lleva *

    def test_FR217_una_sala_desconocida_no_aparece_de_ninguna_forma(self):
        logica = nueva_partida(cadena({4: "Osario-secreto"}))
        mover(logica, "este")
        texto = texto_mapa(logica) + texto_sala(logica)
        self.assertNotIn("Osario-secreto", texto)
        self.assertNotIn("id 4", texto)

    def test_FR216_cada_salida_muestra_direccion_costo_y_puerta_recordada(self):
        salas = esqueleto_de_conexiones([(1, 2, 250, "E", "O", {"cerrada": True})])
        logica = nueva_partida(salas)
        texto = texto_mapa(logica)
        self.assertIn("este", texto)
        self.assertIn("costo 250", texto)
        self.assertIn("cerrada", texto)

    def test_FR209_FR216_una_puerta_sin_observar_se_muestra_tal_cual(self):
        dto = MapaConocidoDTO(1, [SalaConocidaDTO(1, "Sala 1", [SalidaConocidaDTO("este", 100, "sin observar")])])
        self.assertIn("sin observar", imprimir(VistaConsola().mostrar_mapa_conocido, dto))

    def test_FR219_SC002_dos_partidas_que_difieren_solo_en_lo_no_explorado_imprimen_lo_mismo(self):
        a = nueva_partida(cadena())
        b = nueva_partida(cadena({2: "Secreta", 3: "Escondida", 4: "Nunca vista"}, extra=True))
        for logica in (a, b):
            esperar(logica)                                                  # un instante cualquiera, el mismo en las dos
        self.assertEqual(texto_mapa(a), texto_mapa(b))
        self.assertEqual(texto_sala(a), texto_sala(b))

    def test_FR219_el_texto_no_contiene_nombre_ni_id_de_salas_avistadas_o_desconocidas(self):
        logica = nueva_partida(cadena({2: "Calabozo-dos", 3: "Calabozo-tres", 4: "Calabozo-cuatro"}))
        texto = texto_mapa(logica) + texto_sala(logica)                      # solo la 1 explorada; la 2 avistada
        for prohibido in ("Calabozo-dos", "Calabozo-tres", "Calabozo-cuatro", "id 2", "id 3", "id 4", "Sala 2", "Sala 3"):
            self.assertNotIn(prohibido, texto)

    def test_FR219_dos_salidas_hacia_la_misma_avistada_se_ven_identicas(self):
        salas = esqueleto_de_conexiones([(1, 2, None, "E", "O"), (1, 3, None, "S", "N", {"un_sentido": True}),
                                         (2, 3, None, "S", "N", {"un_sentido": True})])
        logica = nueva_partida(salas)
        mover(logica, "este")                                                # exploradas 1 y 2, ambas con salida a la 3
        texto = texto_mapa(logica)
        self.assertEqual(texto.count("sala sin explorar"), 2)
        self.assertNotIn("Sala 3", texto)

    def test_FR219_la_pantalla_de_la_sala_actual_nombra_el_destino_solo_si_esta_explorado(self):
        logica = nueva_partida(cadena())
        antes = texto_sala(logica)
        self.assertIn("sala sin explorar", antes)
        self.assertNotIn("Sala 2", antes)
        mover(logica, "este")
        mover(logica, "oeste")                                               # de vuelta en la 1, con la 2 ya explorada
        self.assertIn("Sala 2", texto_sala(logica))

    def test_FR219_la_vista_funciona_con_el_grafo_completo_apagado(self):
        """La vista solo recibe DTO de conocimiento y la sala actual: no hay mapa completo ni lista de salas a mano."""
        dto = MapaConocidoDTO(1, [
            SalaConocidaDTO(1, "Entrada", [SalidaConocidaDTO("este", 100, "abierta", True, 2, "Pasillo"),
                                           SalidaConocidaDTO("sur", 250, "cerrada", False, None, "")]),
            SalaConocidaDTO(2, "Pasillo", [SalidaConocidaDTO("oeste", 100, "abierta", True, 1, "Entrada")]),
        ])
        jugador = JugadorDTO(1, 1, 1, 1, 100, id_sala_actual=1)
        sala = SalaDTO(1, "Entrada")
        texto = imprimir(VistaConsola().mostrar_mapa_conocido, dto) + imprimir(VistaConsola().mostrar_juego, jugador, sala, dto.salas[0], None, [])
        self.assertIn("Pasillo (id 2)", texto)
        self.assertIn("sala sin explorar", texto)
        self.assertIn("costo 250", texto)

    def test_FR306_una_puerta_sin_observar_se_muestra_en_la_sala_como_sin_observar(self):
        """FR-306 y el supuesto de la 011: una puerta que el jugador no ha visto no se muestra ni abierta ni cerrada."""
        dto = MapaConocidoDTO(1, [
            SalaConocidaDTO(1, "Entrada", [SalidaConocidaDTO("este", 100, "abierta", True, 2, "Pasillo"),
                                           SalidaConocidaDTO("sur", 250, "sin observar", False, None, "")]),
            SalaConocidaDTO(2, "Pasillo", [SalidaConocidaDTO("oeste", 100, "abierta", True, 1, "Entrada")]),
        ])
        jugador = JugadorDTO(1, 1, 1, 1, 100, id_sala_actual=1)
        texto = imprimir(VistaConsola().mostrar_juego, jugador, SalaDTO(1, "Entrada"), dto.salas[0], None, [])
        linea_sur = [l for l in texto.splitlines() if "sur" in l.lower() and "costo" in l]
        self.assertEqual(len(linea_sur), 1)
        self.assertIn("sin observar", linea_sur[0].lower())
        self.assertNotIn("abierta", linea_sur[0].lower())
        self.assertNotIn("cerrada", linea_sur[0].lower())
        self.assertNotIn("Secreta", texto)


class TestConsultarNoEsUnaAccion(unittest.TestCase):
    def test_FR218_consultar_el_mapa_no_cambia_reloj_acciones_historial_ni_conocimiento(self):
        logica = nueva_partida(cadena())
        mover(logica, "este")
        retroceso = RetrocesoLogica()
        antes = (logica.estadoJuego.reloj.tiempo_actual, logica.accionesJugador, retroceso.cantidad_acciones,
                 retroceso.cantidad_actual, len(logica.logEventos.lineas) if hasattr(logica.logEventos, "lineas") else None,
                 list(logica.mapaConocido.estado), logica.mapaConocido.version_conocimiento)
        texto_mapa(logica)
        texto_sala(logica)
        despues = (logica.estadoJuego.reloj.tiempo_actual, logica.accionesJugador, retroceso.cantidad_acciones,
                   retroceso.cantidad_actual, len(logica.logEventos.lineas) if hasattr(logica.logEventos, "lineas") else None,
                   list(logica.mapaConocido.estado), logica.mapaConocido.version_conocimiento)
        self.assertEqual(antes, despues)

    def test_FR218_el_comando_mapa_del_controlador_no_llama_a_accionJugador(self):
        logica = nueva_partida(cadena())
        jugador = logica.estadoJuego.jugador

        class ServicioFalso:
            acciones = 0
            k_checkpoint = 0
            def advertenciasDeDatos(self): return []
            def getJudador(self): return jugador
            def terminado(self): return (False, None)
            def obtenerSala(self, numero): return logica.estadoJuego.salas[numero]
            def vistaSalaActual(self): return logica.vistaSalaActual()
            def mapaConocido(self): return logica.instantaneaMapaConocido()
            def objetoActualInventario(self): return None
            def ultimosMensajes(self): return []
            def tiempoActual(self): return 0
            def puntaje(self): return 0
            def reporteVerificacion(self): return None
            def avisoResolubilidad(self): return None
            def avisoLlaves(self): return None
            def cargarPartida(self, nombre, **kw): pass
            def accionJugador(self, evento): ServicioFalso.acciones += 1

        entradas = iter(["n", "s", "archivo", "mapa", "salir", "n"])
        salida = io.StringIO()
        with mock.patch("builtins.input", lambda *a: next(entradas)), contextlib.redirect_stdout(salida):
            ControladorJuego(ServicioFalso()).iniciar()
        self.assertIn("MAPA CONOCIDO", salida.getvalue())
        self.assertEqual(ServicioFalso.acciones, 0)


if __name__ == "__main__":
    unittest.main()
