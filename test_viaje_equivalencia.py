"""«Ir a» (capacidad 006): un viaje deja la partida como caminar la misma ruta a mano (FR-233, FR-236) y reutilizar el
campo de costos entre pasos no cambia ninguna decisión (principio III). Contrato: research.md D2 y D3."""
import unittest

from DTO.ResultadoViajeDTO import LLEGADO, EN_CURSO
from Logica.BuscadorRutas import BuscadorRutas
from Logica.MapaConocido import VistaMapaConocido
from Logica.ViajeLogica import LIMITE_SIN_COTA
from tests_labs.cripta_sintetica import esqueleto_rejilla
from tests_labs.escenarios_ir_a import (ESTE, OESTE, SUR, caminar, cerrar_fuera, circuito_con_puerta, cuadrado,
                                        encender_antorcha, partida_de, recorrer_circuito, recorrer_cuadrado)
from tests_labs.referencia_viaje import caminar_a_mano, resumen_estado
from test_viaje_ruta import viajar


class TestViajeEsCaminar(unittest.TestCase):
    def _dos_partidas(self, salas, preparar, enemigos=None, fichas=None):
        a = partida_de(salas, enemigos, fichas)
        b = partida_de(salas, enemigos, fichas)
        preparar(a)
        preparar(b)
        return a, b

    def test_FR233_FR236_el_viaje_deja_el_mismo_estado_que_caminar_la_ruta_a_mano(self):
        a, b = self._dos_partidas(cuadrado(100, 100, 50, 400), recorrer_cuadrado)
        r = viajar(a, 4)
        caminar_a_mano(b, [1] + r.recorrido)
        self.assertEqual(r.estado, LLEGADO)
        self.assertEqual(resumen_estado(a), resumen_estado(b))

    def test_FR246_con_antorcha_el_conocimiento_final_es_el_de_caminar_a_mano(self):
        def preparar(logica):
            encender_antorcha(logica)
            recorrer_cuadrado(logica)
        a, b = self._dos_partidas(cuadrado(), preparar)
        r = viajar(a, 4)
        caminar_a_mano(b, [1] + r.recorrido)
        self.assertEqual(resumen_estado(a), resumen_estado(b))

    def test_FR244_cada_paso_del_viaje_es_una_accion(self):
        a, b = self._dos_partidas(cuadrado(), recorrer_cuadrado)
        antes = a.acciones_linea_tiempo
        r = viajar(a, 4)
        self.assertEqual(a.acciones_linea_tiempo - antes, r.pasos)
        self.assertEqual(a.accionesJugador, b.accionesJugador + r.pasos)


def decisiones_iguales_a_recalcular(logica, destino):
    """Recorre el viaje paso a paso y, antes de cada paso, calcula desde cero (otro buscador) el siguiente paso; devuelve
    cuántos pasos se dieron y cuántas veces el viaje recalculó."""
    logica.iniciarViaje(destino)
    viaje = logica.viaje_activo
    recalculos = []
    original = viaje.buscador.distancias_hacia

    def contando(d, vista, limite):
        recalculos.append(1)
        return original(d, vista, limite)
    viaje.buscador.distancias_hacia = contando
    pasos = 0
    while logica.viaje_activo is not None:
        origen = logica.estadoJuego.jugador.id_sala_actual
        fresco = BuscadorRutas()
        fresco.distancias_hacia(destino, VistaMapaConocido(logica.mapaConocido), LIMITE_SIN_COTA)
        esperado = fresco.siguiente_paso(origen)
        resultado = logica.avanzarViaje()
        if esperado is None:
            assert resultado.estado != EN_CURSO
        elif resultado.estado == EN_CURSO or resultado.pasos > pasos:
            assert logica.estadoJuego.jugador.id_sala_actual == esperado.destino, (origen, esperado.destino)
        pasos = resultado.pasos
    return pasos, len(recalculos)


class TestReusoDelCampo(unittest.TestCase):
    def test_III_sin_cambios_de_conocimiento_no_se_recalcula_y_la_decision_es_la_misma(self):
        esqueleto = esqueleto_rejilla(4, 4, semilla=5, costo_max=3)
        logica = partida_de(esqueleto)
        caminar(logica, [ESTE, ESTE, ESTE, SUR, OESTE, OESTE, OESTE, SUR, ESTE, ESTE, ESTE, SUR, OESTE, OESTE, OESTE])
        pasos, recalculos = decisiones_iguales_a_recalcular(logica, 16)
        self.assertGreater(pasos, 3)
        self.assertEqual(recalculos, 0)

    def test_III_una_puerta_que_resulta_cerrada_recalcula_y_decide_como_desde_cero(self):
        for con_alterna in (True, False):
            with self.subTest(con_alterna=con_alterna):
                logica = partida_de(circuito_con_puerta(con_alterna))
                recorrer_circuito(logica, con_alterna)
                cerrar_fuera(logica, 3, "este")
                pasos, recalculos = decisiones_iguales_a_recalcular(logica, 4)
                self.assertEqual(recalculos, 1)

    def test_III_con_antorcha_cada_entrada_recalcula_y_decide_como_desde_cero(self):
        logica = partida_de(esqueleto_rejilla(4, 4, semilla=2, costo_max=3))
        encender_antorcha(logica)
        caminar(logica, [ESTE, ESTE, ESTE, SUR, OESTE, OESTE, OESTE])
        pasos, recalculos = decisiones_iguales_a_recalcular(logica, 4)
        self.assertGreaterEqual(pasos, 1)


if __name__ == "__main__":
    unittest.main()
