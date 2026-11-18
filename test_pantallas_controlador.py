"""Capacidad 011, historia 2: el controlador usa las pantallas nuevas y conserva la sintaxis de los comandos
(FR-307, FR-309, FR-310, FR-313). Se usa un servicio falso sobre una partida real del modelo. Cada prueba cita el
requisito que demuestra."""
import contextlib
import io
import os
import re
import unittest
from unittest import mock

from Controlador import Pantallas as P
from Controlador.ControladorJuego import ControladorJuego
from DTO.FinPartidaDTO import FinPartidaDTO
from DTO.RegistroPuntajeDTO import RegistroPuntajeDTO
from DTO.ResultadoViajeDTO import RECHAZADO, ResultadoViajeDTO
from tests_labs.cripta_sintetica import esqueleto_lineal
from tests_labs.partida_prueba import nueva_partida

RAIZ = os.path.dirname(os.path.abspath(__file__))
INICIO = ["n", "s", "archivo"]               # puntajes? no · cargar? sí · nombre del archivo
PROMPT = "\n" + P.PROMPT


class ServicioFalso:
    """Lo que el controlador usa del servicio, apoyado en una partida real para la sala, el jugador y el mapa."""
    k_checkpoint = 0
    MAX_NOMBRE_JUGADOR = 15

    def __init__(self, logica, terminado=(False, None)):
        self.logica = logica
        self.fin = terminado
        self.acciones, self.destinos, self.historias, self.consultas_de_ayuda = [], [], [], 0

    def advertenciasDeDatos(self): return []
    def getJudador(self): return self.logica.estadoJuego.jugador
    def terminado(self): return self.fin
    def obtenerSala(self, numero): return self.logica.estadoJuego.salas[numero]
    def vistaSalaActual(self): return self.logica.vistaSalaActual()
    def mapaConocido(self): return self.logica.instantaneaMapaConocido()
    def objetoActualInventario(self): return None
    def ultimosMensajes(self): return []
    def tiempoActual(self): return 250
    def puntaje(self): return 42
    def cargarPartida(self, nombre, **kw): pass
    def accionJugador(self, evento): self.acciones.append(evento.tipo_accion)
    def irA(self, destino):
        self.destinos.append(destino)
        return ResultadoViajeDTO(estado=RECHAZADO, mensaje="Esa sala no está explorada.")
    def consultarHistoria(self, instante=None, accion=None):
        self.historias.append((instante, accion))
        raise ValueError("ese instante aún no ha ocurrido")
    def siguienteObjetoInventario(self): raise ValueError("el inventario está vacío")
    def anteriorObjetoInventario(self): raise ValueError("el inventario está vacío")
    def vistaInventario(self, criterio=None): return []
    def finPartida(self): return FinPartidaDTO("cripta-01", "v3", 14, 4, 1850, True)
    def nombreLog(self): return None
    def registrarPuntaje(self, nombre): return RegistroPuntajeDTO(nombre, "cripta-01", "v3", 14, 4, 1850, True)
    def tablaPuntajes(self): return []


def correr(servicio, teclas):
    """Ejecuta el bucle del controlador con las teclas dadas; devuelve (valor de iniciar(), texto impreso)."""
    pendientes = list(INICIO + teclas)
    salida = io.StringIO()

    def entrada(*_):
        if not pendientes:
            raise AssertionError("el controlador pidió más entradas de las previstas")
        return pendientes.pop(0)

    with mock.patch("builtins.input", entrada), contextlib.redirect_stdout(salida):
        valor = ControladorJuego(servicio).iniciar()
    return valor, salida.getvalue()


def servicio_en_partida(**kw):
    return ServicioFalso(nueva_partida(esqueleto_lineal([100, None])), **kw)


class TestAyudaYPrompt(unittest.TestCase):

    def test_FR309_ayuda_imprime_la_lista_sin_consumir_tiempo_ni_contar_como_accion(self):
        servicio = servicio_en_partida()
        _, texto = correr(servicio, ["ayuda", "AYUDA", "salir", "n"])
        self.assertEqual(texto.count("COMANDOS DISPONIBLES"), 2)
        self.assertIn(P.texto_ayuda(), texto)
        self.assertEqual(servicio.acciones, [])

    def test_FR309_el_prompt_es_el_corto_y_menciona_ayuda(self):
        pedidos = []
        servicio = servicio_en_partida()
        pendientes = INICIO + ["salir", "n"]

        def entrada(texto=""):
            pedidos.append(texto)
            return pendientes.pop(0)

        with mock.patch("builtins.input", entrada), contextlib.redirect_stdout(io.StringIO()):
            ControladorJuego(servicio).iniciar()
        self.assertIn(PROMPT, pedidos)
        self.assertIn("ayuda", PROMPT)

    def test_FR309_despues_de_la_partida_ayuda_lista_solo_historia_ayuda_y_salir(self):
        servicio = servicio_en_partida(terminado=(True, "El jugador ha llegado a la sala final"))
        _, texto = correr(servicio, ["Ana", "ayuda", "salir"])
        self.assertIn(P.texto_ayuda(post_partida=True), texto)
        self.assertNotIn("atacar", P.texto_ayuda(post_partida=True))


class TestResumenAlTerminar(unittest.TestCase):

    def resumen_esperado(self, motivo):
        return P.texto_fin_partida(motivo, 42, 14, 1850, 5000, 1, "cripta-01", "v3", 4)

    def test_FR307_al_llegar_a_la_salida_se_imprime_el_resumen_con_los_seis_datos(self):
        motivo = "El jugador ha llegado a la sala final"
        servicio = servicio_en_partida(terminado=(True, motivo))
        _, texto = correr(servicio, ["Ana", "salir"])
        self.assertIn("HAS LLEGADO A LA SALA DE SALIDA", texto)
        self.assertIn(self.resumen_esperado(motivo), texto)
        for rotulo in ("Motivo:", "Puntaje: 42", "Acciones: 14", "Tiempo: 1850", "Vida final: 5000", "Salas exploradas: 1"):
            self.assertIn(rotulo, texto)

    def test_FR307_al_morir_se_imprime_el_resumen_con_el_motivo_de_muerte(self):
        servicio = servicio_en_partida(terminado=(True, "El jugador ha muerto"))
        servicio.getJudador().vida_actual = 0
        _, texto = correr(servicio, ["Ana", "salir"])
        self.assertIn("HAS MUERTO", texto)
        self.assertIn("Motivo: El jugador ha muerto", texto)
        self.assertIn("Vida final: 0", texto)


class TestRechazosClaros(unittest.TestCase):

    def rechazo(self, entrada, esperado, servicio=None):
        servicio = servicio or servicio_en_partida()
        _, texto = correr(servicio, [entrada, "salir", "n"])
        self.assertIn(esperado, texto, entrada)
        return servicio

    def test_FR310_direccion_sin_salida(self):
        self.rechazo("norte", P.mensaje_sin_salida("norte"))

    def test_FR310_comando_desconocido(self):
        self.rechazo("xyz", P.mensaje_comando_desconocido("xyz"))

    def test_FR310_ir_a_con_destino_invalido_no_llama_al_servicio(self):
        servicio = self.rechazo("ir a x", P.mensaje_ir_a_destino_invalido())
        self.assertEqual(servicio.destinos, [])

    def test_FR310_ir_a_rechazado_por_el_modelo_conserva_el_texto_del_modelo(self):
        servicio = servicio_en_partida()
        _, texto = correr(servicio, ["ir a 3", "salir", "n"])
        self.assertEqual(servicio.destinos, [3])
        self.assertIn("Esa sala no está explorada.", texto)

    def test_FR310_atacar_y_recoger_sin_nadie_ni_nada(self):
        self.rechazo("atacar", P.mensaje_sin_enemigos())
        self.rechazo("recoger", P.mensaje_sin_objetos())

    def test_FR310_usar_y_soltar_con_el_inventario_vacio(self):
        self.rechazo("usar", P.mensaje_inventario_vacio())
        self.rechazo("soltar", P.mensaje_inventario_vacio())

    def test_FR310_historia_mal_escrita_y_historia_fuera_de_rango(self):
        self.rechazo("historia", P.mensaje_historia_sin_parametro())
        self.rechazo("historia abc", P.mensaje_historia_sin_parametro())
        self.rechazo("historia 1.5", P.mensaje_historia_no_entero())
        self.rechazo("historia -3", P.mensaje_historia_negativo())
        self.rechazo("historia #0", P.mensaje_historia_accion_cero())
        self.rechazo("historia 999", P.mensaje_historia_rechazada("ese instante aún no ha ocurrido"))

    def test_FR310_inventario_con_demasiados_argumentos(self):
        self.rechazo("inventario a b c", P.mensaje_inventario_uso())

    def test_FR310_siguiente_con_el_inventario_vacio(self):
        self.rechazo("siguiente", P.mensaje_objeto_rechazado("el inventario está vacío"))

    def test_FR310_el_controlador_no_imprime_rechazos_con_texto_suelto(self):
        """Todo rechazo pasa por el catálogo de Pantallas (hallazgo G1 del análisis): sin `print` con literales de error."""
        with open(os.path.join(RAIZ, "Controlador", "ControladorJuego.py"), encoding="utf-8") as archivo:
            fuente = archivo.read()
        patron = re.compile(r"""print\(\s*f?["'][^"']*(Error|inválid|Por favor|Comando no|Acción no|No hay |No existe|"""
                            r"""No se pudo|No se puede|ya está derrotado|Uso:)""")
        sueltos = [linea.strip() for linea in fuente.splitlines() if patron.search(linea)]
        self.assertEqual(sueltos, [])


class TestComandosExistentesConservanSuSintaxis(unittest.TestCase):
    """FR-313: cada comando de siempre sigue reconocido y hace lo de antes."""

    def correr_comando(self, comando):
        servicio = servicio_en_partida()
        _, texto = correr(servicio, [comando, "salir", "n"])
        return servicio, texto

    def test_FR313_ningun_comando_existente_se_rechaza_como_desconocido(self):
        for comando in ("este", "ESTE", "esperar", "mapa", "ir a 3", "historia 5", "historia #2", "historia <5>",
                        "inventario", "inventario peso", "inventario valor", "inventario nombre", "ayuda", "sig",
                        "siguiente", "ant", "anterior"):
            with self.subTest(comando=comando):
                _, texto = self.correr_comando(comando)
                self.assertNotIn("No reconozco", texto)

    def test_FR313_mover_y_esperar_siguen_siendo_acciones_del_jugador(self):
        servicio, _ = self.correr_comando("este")
        self.assertEqual(servicio.acciones, ["MOVER_JUGADOR"])
        servicio, _ = self.correr_comando("esperar")
        self.assertEqual(servicio.acciones, ["ESPERAR"])

    def test_FR313_mapa_historia_e_ir_a_no_son_acciones(self):
        for comando in ("mapa", "ir a 3", "historia 5", "historia #2", "inventario", "ayuda"):
            servicio, _ = self.correr_comando(comando)
            self.assertEqual(servicio.acciones, [], comando)

    def test_FR313_historia_llega_al_servicio_con_los_mismos_parametros(self):
        servicio, _ = self.correr_comando("historia 5")
        self.assertEqual(servicio.historias, [(5, None)])
        servicio, _ = self.correr_comando("historia #2")
        self.assertEqual(servicio.historias, [(None, 2)])

    def test_FR313_mapear_entrada_a_evento_conserva_su_firma(self):
        servicio = servicio_en_partida()
        sala = servicio.obtenerSala(1)
        jugador = servicio.getJudador()
        controlador = ControladorJuego(None)
        evento = controlador._mapear_entrada_a_evento("este", sala, jugador)
        self.assertEqual(evento.tipo_accion, "MOVER_JUGADOR")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(controlador._mapear_entrada_a_evento("norte", sala, jugador), "IGNORAR")
            self.assertEqual(controlador._mapear_entrada_a_evento("esperar", sala, jugador).tipo_accion, "ESPERAR")
            self.assertIsNone(controlador._mapear_entrada_a_evento("atacar", sala, jugador))


if __name__ == "__main__":
    unittest.main()
