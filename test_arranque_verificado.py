"""Capacidad 011, historia 1: arranque verificado (FR-301 a FR-305, FR-315, FR-316; SC-301 a SC-303).

Se corre `main.main(argv)` de punta a punta con una cripta falsa (Apéndice B de la 003): B-R3 es resoluble, B-R1 no lo es.
`input` se simula y `requests.get` está bloqueado. El log de la partida va a una carpeta temporal. Cada prueba cita el
requisito que demuestra."""
import contextlib
import io
import unittest
from unittest import mock

import main
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from Controlador.ControladorJuego import ControladorJuego
from Controlador.Vista import VistaConsola
from DTO.ResultadoVerificacionDTO import ResultadoVerificacion
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_lineal
from tests_labs.partida_prueba import nueva_partida
from test_resolubilidad_inicio import ConJuego, caso

CRIPTA = "cripta-01"
# puntajes? no · cargar? no · cripta 1 · semilla fija · salir · ¿guardar? no
TECLAS_JUGAR = ["n", "n", "1", "7", "salir", "n"]
TECLAS_SOLO_ELEGIR = ["n", "n", "1", "7"]
RESOLUBLE = "Verificación de la cripta cripta-01: RESOLUBLE."
NO_RESOLUBLE = "Verificación de la cripta cripta-01: NO RESOLUBLE."
SIN_VERIFICAR = "NO SE PUDO VERIFICAR."


class ConMain(ConJuego):
    """Corre `main.main` con la cripta falsa; devuelve (código, salida estándar, salida de errores)."""

    def correr(self, http, argv, teclas=()):
        servicio_cripta = ServicioCripta(http, CacheLRU(25))
        servicio_cripta.listar_criptas()
        pendientes = list(teclas)

        def entrada(*_):
            if not pendientes:
                raise AssertionError("el programa pidió más entradas de las previstas")
            return pendientes.pop(0)

        salida, errores = io.StringIO(), io.StringIO()
        with mock.patch.object(main, "crear_servicio", lambda **_: servicio_cripta), \
                mock.patch("builtins.input", entrada), \
                contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
            codigo = main.main(argv)
        return codigo, salida.getvalue(), errores.getvalue()


class TestVerificarSinAbrirPartida(ConMain):

    def verificar(self, http, *extra):
        with mock.patch.object(VistaConsola, "__init__", side_effect=AssertionError("se creó la vista")):
            return self.correr(http, ["--verificar", CRIPTA, *extra])

    def comprobar_sin_partida(self):
        self.abrir.assert_not_called()
        self.assertEqual(self.archivos_de_log(), [])

    def test_FR302_resoluble_sale_con_0_y_muestra_el_reporte(self):
        codigo, salida, _ = self.verificar(caso("B-R3"))
        self.assertEqual(codigo, 0)
        self.assertIn(RESOLUBLE, salida)
        self.comprobar_sin_partida()

    def test_FR302_no_resoluble_sale_con_1_y_muestra_el_reporte(self):
        codigo, salida, _ = self.verificar(caso("B-R1"))
        self.assertEqual(codigo, 1)
        self.assertIn(NO_RESOLUBLE, salida)
        self.comprobar_sin_partida()

    def test_FR302_cripta_inexistente_sale_con_2_y_muestra_el_motivo(self):
        with mock.patch.object(VistaConsola, "__init__", side_effect=AssertionError("se creó la vista")):
            codigo, salida, _ = self.correr(caso("B-R3"), ["--verificar", "cripta-que-no-existe"])
        self.assertEqual(codigo, 2)
        self.assertIn(SIN_VERIFICAR, salida)
        self.assertIn("cripta-que-no-existe", salida)
        self.comprobar_sin_partida()

    def test_FR302_datos_no_disponibles_sale_con_2(self):
        http = HttpConfigurable(esqueleto_lineal([None]), sala_salida=2, fallo_llaves="sin_respuesta")
        codigo, salida, _ = self.verificar(http)
        self.assertEqual(codigo, 2)
        self.assertIn(SIN_VERIFICAR, salida)

    def test_FR302_sin_valor_sale_con_2_y_dice_como_usarlo(self):
        with self.assertRaises(SystemExit) as contexto, contextlib.redirect_stderr(io.StringIO()) as errores:
            main.leer_argumentos(["--verificar"])
        self.assertEqual(contexto.exception.code, 2)
        self.assertIn("--verificar", errores.getvalue())

    def test_FR302_los_codigos_coinciden_con_los_del_resultado_de_la_003(self):
        """Una sola fuente de verdad (research D4): main usa lo que ya decide `ResultadoVerificacion.codigo_salida()`."""
        self.assertEqual((main.SALIDA_RESOLUBLE, main.SALIDA_NO_RESOLUBLE, main.SALIDA_ERROR), (0, 1, 2))
        for resoluble, esperado in ((True, 0), (False, 1), (None, 2)):
            resultado = ResultadoVerificacion(CRIPTA, resoluble, motivo_error="x" if resoluble is None else None)
            self.assertEqual(resultado.codigo_salida(), esperado)

    def test_FR302_forzar_junto_a_verificar_se_ignora(self):
        codigo, salida, _ = self.verificar(caso("B-R1"), "--forzar")
        self.assertEqual(codigo, 1)
        self.assertIn(NO_RESOLUBLE, salida)
        self.comprobar_sin_partida()

    def test_FR302_verificar_con_replay_o_bench_se_rechaza_con_2_y_dice_que_hacer(self):
        for otro in (["--replay", "x.log"], ["--bench"]):
            with self.subTest(otro=otro):
                codigo, salida, errores = self.correr(caso("B-R3"), ["--verificar", CRIPTA, *otro])
                self.assertEqual(codigo, 2)
                texto = salida + errores
                self.assertIn("--verificar", texto)
                self.assertRegex(texto, r"(?i)por separado")           # qué hacer
                self.comprobar_sin_partida()


class TestReporteAlIniciar(ConMain):

    def test_FR301_resoluble_muestra_el_reporte_antes_del_primer_turno_y_abre_la_partida(self):
        codigo, salida, _ = self.correr(caso("B-R3"), [], TECLAS_JUGAR)
        self.assertEqual(codigo, 0)
        self.assertIn(RESOLUBLE, salida)
        self.assertIn("SALA:", salida)
        self.assertLess(salida.index(RESOLUBLE), salida.index("SALA:"))
        self.assertEqual(self.abrir.call_count, 1)

    def test_FR301_FR303_no_resoluble_sin_forzar_muestra_reporte_y_guia_y_no_abre_la_partida(self):
        codigo, salida, _ = self.correr(caso("B-R1"), [], TECLAS_SOLO_ELEGIR)
        self.assertEqual(codigo, 1)
        self.assertIn(NO_RESOLUBLE, salida)
        self.assertIn("La cripta cripta-01 no tiene solución, por eso no se abrió la partida.", salida)
        self.assertIn("--forzar", salida)                                   # qué puede hacer el jugador
        self.assertNotIn("SALA:", salida)
        self.abrir.assert_not_called()
        self.assertEqual(self.archivos_de_log(), [])

    def test_FR303_FR304_no_resoluble_con_forzar_muestra_reporte_y_aviso_antes_del_primer_turno(self):
        codigo, salida, _ = self.correr(caso("B-R1"), ["--forzar"], TECLAS_JUGAR)
        self.assertEqual(codigo, 0)
        aviso = "AVISO: la cripta cripta-01 no es resoluble"
        self.assertIn(NO_RESOLUBLE, salida)
        self.assertIn(aviso, salida)
        self.assertLess(salida.index(NO_RESOLUBLE), salida.index(aviso))
        self.assertLess(salida.index(aviso), salida.index("SALA:"))
        self.assertEqual(salida.count(aviso), 1)                            # el aviso sale una sola vez, al iniciar
        self.assertEqual(self.abrir.call_count, 1)

    def test_FR303_forzar_en_una_cripta_resoluble_no_agrega_aviso_de_forzar(self):
        codigo, salida, _ = self.correr(caso("B-R3"), ["--forzar"], TECLAS_JUGAR)
        self.assertEqual(codigo, 0)
        self.assertIn(RESOLUBLE, salida)
        self.assertNotIn("AVISO: la cripta", salida)
        self.assertNotIn("no es resoluble", salida)

    def test_FR301_sin_llaves_no_hay_reporte_pero_la_partida_abre_con_el_aviso_de_la_009(self):
        http = HttpConfigurable(esqueleto_lineal([None]), sala_salida=2, fallo_llaves="sin_respuesta")
        codigo, salida, _ = self.correr(http, [], TECLAS_JUGAR)
        self.assertEqual(codigo, 0)
        self.assertNotIn("Verificación de la cripta", salida)
        self.assertIn("AVISO:", salida)
        self.assertEqual(self.abrir.call_count, 1)

    def test_FR301_una_partida_cargada_no_muestra_el_reporte(self):
        logica = nueva_partida(esqueleto_lineal([100, None]))
        jugador = logica.estadoJuego.jugador

        class ServicioCargado:
            k_checkpoint = 0

            def advertenciasDeDatos(self): return []
            def getJudador(self): return jugador
            def terminado(self): return (False, None)
            def obtenerSala(self, numero): return logica.estadoJuego.salas[numero]
            def vistaSalaActual(self): return logica.vistaSalaActual()
            def objetoActualInventario(self): return None
            def ultimosMensajes(self): return []
            def tiempoActual(self): return 0
            def cargarPartida(self, nombre, **kw): pass
            def reporteVerificacion(self): raise AssertionError("una partida cargada no muestra el reporte de inicio")
            def avisoResolubilidad(self): raise AssertionError("una partida cargada no muestra el aviso de inicio")

        entradas = iter(["n", "s", "archivo", "salir", "n"])
        salida = io.StringIO()
        with mock.patch("builtins.input", lambda *a: next(entradas)), contextlib.redirect_stdout(salida):
            ControladorJuego(ServicioCargado(), forzar=True).iniciar()
        self.assertNotIn("Verificación de la cripta", salida.getvalue())


class TestViajeDeForzar(ConMain):
    """FR-305: el valor viaja por parámetros, de `main.py` al servicio; ninguna capa lo decide."""

    def forzar_recibido(self, argv, http):
        original = EstadoJuegoServicio.iniciarJuego
        with mock.patch.object(EstadoJuegoServicio, "iniciarJuego", autospec=True, side_effect=original) as espia:
            self.correr(http, argv, TECLAS_JUGAR)
        self.assertEqual(espia.call_count, 1)
        return espia.call_args.kwargs.get("forzar")

    def test_FR305_con_forzar_llega_True_al_servicio(self):
        self.assertIs(self.forzar_recibido(["--forzar"], caso("B-R1")), True)

    def test_FR305_sin_forzar_llega_False_al_servicio(self):
        self.assertIs(self.forzar_recibido([], caso("B-R3")), False)

    def test_FR305_el_controlador_toma_forzar_del_parametro_y_por_defecto_es_False(self):
        self.assertIs(ControladorJuego(None).forzar, False)
        self.assertIs(ControladorJuego(None, forzar=True).forzar, True)
        self.assertIs(ControladorJuego(None, k_checkpoint=5, forzar=False).forzar, False)


class TestSinEfectoEnLogNiGuardado(ConMain):
    """FR-304 y FR-315: forzar no se registra en `partida.log` ni en el estado guardado; el reporte no es el de ayer."""

    def log_de_la_partida(self):
        import os
        archivos = self.archivos_de_log()
        self.assertEqual(len(archivos), 1)
        with open(os.path.join(self.carpeta_logs, archivos[0]), encoding="utf-8") as archivo:
            return archivo.read()

    def test_FR304_el_log_de_una_partida_forzada_no_menciona_forzar(self):
        self.correr(caso("B-R1"), ["--forzar"], TECLAS_JUGAR)
        self.assertNotIn("forzar", self.log_de_la_partida().lower())

    def test_FR304_FR315_dos_partidas_forzadas_iguales_dejan_el_mismo_log(self):
        import os
        import shutil
        self.correr(caso("B-R1"), ["--forzar"], TECLAS_JUGAR)
        primero = self.log_de_la_partida()
        shutil.rmtree(self.carpeta_logs)
        os.makedirs(self.carpeta_logs)
        self.correr(caso("B-R1"), ["--forzar"], TECLAS_JUGAR)
        segundo = self.log_de_la_partida()
        encabezado = lambda texto: [l for l in texto.splitlines() if not l.lower().startswith(("fecha", "#"))]
        self.assertEqual(encabezado(primero), encabezado(segundo))

    def test_FR315_el_estado_guardado_no_tiene_ningun_campo_de_forzar(self):
        http = caso("B-R1")
        servicio_cripta = ServicioCripta(http, CacheLRU(25))
        servicio_cripta.listar_criptas()
        juego = EstadoJuegoServicio(comunicacion=servicio_cripta)
        with contextlib.redirect_stdout(io.StringIO()):
            juego.iniciarJuego(CRIPTA, 7, forzar=True)
        self.assertNotIn("forzar", repr(juego._estadoJuegoLogica.exportar_estado()).lower())


if __name__ == "__main__":
    unittest.main()
