"""«Ir a» (capacidad 006), historia 5: con la antorcha encendida, cada entrada del viaje explora las vecinas como una entrada a
mano (002, FR-210 a FR-212). Contrato: specs/006-ir-a/spec.md FR-246."""
import unittest

from DTO.ResultadoViajeDTO import LLEGADO
from Logica.MapaConocido import EXPLORADA
from tests_labs.cripta_sintetica import ficha_enemigo
from tests_labs.escenarios_ir_a import (ESTE, NORTE, OESTE, SUR, apagar_antorcha, caminar, cerrar_fuera,
                                        circuito_con_puerta, encender_antorcha, partida_de, pasillo, recorrer_circuito)
from tests_labs.referencia_viaje import caminar_a_mano, resumen_estado
from test_viaje_ruta import viajar


class TestViajeConAntorcha(unittest.TestCase):
    def test_FR246_FR211_el_conocimiento_es_el_de_caminar_a_mano_y_no_se_activa_a_nadie_en_las_vecinas(self):
        enemigos, fichas = [(5, "e-0", "ent_ir_a", None)], [ficha_enemigo("ent_ir_a", "guardián")]
        a = partida_de(pasillo(6), enemigos, fichas)
        b = partida_de(pasillo(6), enemigos, fichas)
        for logica in (a, b):
            encender_antorcha(logica)
            caminar(logica, [ESTE, ESTE, ESTE])                      # en la 4 la antorcha explora la 5 sin despertar a nadie
            caminar(logica, [OESTE, OESTE, OESTE])
        r = viajar(a, 4)
        caminar_a_mano(b, [1] + r.recorrido)
        self.assertEqual(r.estado, LLEGADO)
        self.assertEqual(resumen_estado(a), resumen_estado(b))
        self.assertEqual(a.activaciones_enemigos, 0)
        self.assertIsNone(a.estadoJuego.salas[5])                    # su contenido nunca se descargó

    def test_FR246_las_vecinas_de_cada_sala_del_trayecto_quedan_exploradas(self):
        logica = partida_de(pasillo(6))
        encender_antorcha(logica)
        caminar(logica, [ESTE])                                      # la antorcha ya exploró la 3
        caminar(logica, [ESTE, ESTE])                                # en la 4: exploradas hasta la 5
        caminar(logica, [OESTE, OESTE, OESTE])                       # de vuelta en la 1
        r = viajar(logica, 4)
        self.assertEqual(r.estado, LLEGADO)
        for sala in (1, 2, 3, 4, 5):
            self.assertEqual(logica.mapaConocido.estado_de(sala), EXPLORADA)

    def test_FR246_FR240_tras_una_puerta_cerrada_el_recalculo_puede_usar_salas_que_exploro_la_antorcha(self):
        # Pasillo 1-2-3-4 y rodeo 1-5-6-4. El jugador solo entra a 1, 2 y 5 con la antorcha: la 3 y la 6 quedan exploradas por
        # la antorcha (no entradas) y la 4 solo avistada hasta que el viaje la alcance.
        logica = partida_de(circuito_con_puerta(True))
        encender_antorcha(logica)
        caminar(logica, [SUR, NORTE, ESTE, OESTE])                   # entra a 5, 1 y 2, vuelve a la 1
        self.assertEqual(logica.mapaConocido.estado_de(6), EXPLORADA)
        self.assertEqual(logica.mapaConocido.estado_de(3), EXPLORADA)
        self.assertNotEqual(logica.mapaConocido.estado_de(4), EXPLORADA)
        r = logica.iniciarViaje(6)
        self.assertEqual(r.estado, "EN_CURSO")
        r = logica.ejecutarViaje()
        self.assertEqual((r.estado, r.recorrido), (LLEGADO, [5, 6]))

    def test_FR246_si_la_antorcha_se_apaga_a_mitad_del_viaje_las_entradas_siguientes_no_exploran(self):
        logica = partida_de(pasillo(7))
        encender_antorcha(logica)
        caminar(logica, [ESTE, ESTE, ESTE])                          # explora hasta la 5
        caminar(logica, [OESTE, OESTE, OESTE])                       # de vuelta en la 1
        apagar_antorcha(logica)
        logica.iniciarViaje(5)
        logica.avanzarViaje()
        logica.avanzarViaje()
        self.assertEqual(logica.mapaConocido.estado_de(6), 1)        # la 6 sigue solo avistada
        encender_antorcha(logica)
        logica.avanzarViaje()                                        # entra a la 4 con la antorcha encendida
        logica.avanzarViaje()                                        # entra a la 5 con la antorcha encendida
        self.assertEqual(logica.mapaConocido.estado_de(6), EXPLORADA)


if __name__ == "__main__":
    unittest.main()
