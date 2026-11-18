"""«Ir a» (capacidad 006), historia 4: el viaje se detiene ante el peligro. Caso B-N3 del Apéndice B.
Contrato: specs/006-ir-a/research.md D4 y contracts/viaje-logica.md §3. Cada prueba cita el requisito que demuestra."""
import unittest

from Logica.ordenamiento import insertion_sort
from DTO.ResultadoViajeDTO import (DANO, DETENIDO, ENEMIGO_ACTIVO, ENEMIGOS_DORMIDOS, LLEGADO, MUERTE)
from tests_labs.cripta_sintetica import ficha_enemigo
from tests_labs.escenarios_ir_a import (ESTE, NORTE, OESTE, SUR, caminar, circuito_con_puerta, encender_antorcha,
                                        partida_con_trampa, partida_de, pasillo, pasillo_con_enemigos)
from tests_labs.partida_prueba import esperar
from tests_labs.referencia_viaje import caminar_a_mano, resumen_estado
from test_viaje_ruta import viajar


def agenda(logica):
    """Agenda de eventos pendientes (tiempo, secuencia, tipo), en orden."""
    eventos = [(e.tiempo_ejecucion, e.id_secuencia, e.tipo_accion) for e in logica.estadoJuego.reloj.heap]
    insertion_sort(eventos)
    return eventos


def circuito_con_dormidos():
    """Circuito 1-2-3-4 con el rodeo 1-5-6-4 y dos enemigos dormidos en la sala 3. El jugador deja la sala 3 explorada por la
    antorcha (sin entrar) y todas las puertas a su alrededor observadas, y termina en la sala 1."""
    enemigos = [(3, "e-0", "ent_ir_a", None), (3, "e-1", "ent_ir_a", None)]
    fichas = [ficha_enemigo("ent_ir_a", "guardián")]
    logica = partida_de(circuito_con_puerta(True), enemigos, fichas)
    encender_antorcha(logica)
    caminar(logica, [ESTE, OESTE])               # en 2 la antorcha explora la 3 sin despertar a nadie
    caminar(logica, [SUR, ESTE, NORTE])          # 1→5→6→4: observa las puertas de la 3 desde la 4
    caminar(logica, [SUR, OESTE, NORTE])         # 4→6→5→1
    return logica, enemigos, fichas


class TestDetencionPorPeligro(unittest.TestCase):
    def test_FR242_FR243_APENDICE_B_N3_entrar_a_una_sala_con_dormidos_los_activa_y_detiene_el_viaje(self):
        logica, enemigos, fichas = circuito_con_dormidos()
        self.assertEqual(logica.mapaConocido.estado_de(3), 2)
        self.assertIsNone(logica.estadoJuego.salas[3])             # explorada por la antorcha: su contenido no se descargó
        r = viajar(logica, 4)                                      # la ruta más barata pasa por la 3
        sala3 = logica.estadoJuego.salas[3]
        self.assertEqual((r.estado, r.motivo), (DETENIDO, ENEMIGOS_DORMIDOS))
        self.assertEqual(r.recorrido, [2, 3])
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 3)
        self.assertTrue(all(e.activo for e in sala3.enemigos))
        self.assertEqual(logica.activaciones_enemigos, 2)

    def test_FR242_los_enemigos_se_activan_exactamente_como_en_una_entrada_a_mano(self):
        viaje, _, _ = circuito_con_dormidos()
        mano, _, _ = circuito_con_dormidos()
        r = viajar(viaje, 4)
        caminar_a_mano(mano, [1] + r.recorrido)
        self.assertEqual(resumen_estado(viaje), resumen_estado(mano))
        self.assertEqual(agenda(viaje), agenda(mano))               # mismas activaciones y números de secuencia
        self.assertEqual([e.activo for e in viaje.estadoJuego.salas[3].enemigos],
                         [e.activo for e in mano.estadoJuego.salas[3].enemigos])

    def test_FR242_cuando_la_sala_con_dormidos_es_el_destino_se_activan_y_el_viaje_termina_alli(self):
        enemigos, fichas = [(3, "e-0", "ent_ir_a", None)], [ficha_enemigo("ent_ir_a", "guardián")]
        logica = partida_de(pasillo(3), enemigos, fichas)
        encender_antorcha(logica)
        caminar(logica, [ESTE])                                     # en 2 la antorcha explora la 3 sin despertarlos
        self.assertIsNone(logica.estadoJuego.salas[3])
        r = viajar(logica, 3)
        self.assertEqual(r.estado, LLEGADO)
        self.assertTrue(logica.estadoJuego.salas[3].enemigos[0].activo)

    def test_FR243_una_sala_sin_enemigos_dormidos_no_detiene_el_viaje(self):
        logica, _, _ = circuito_con_dormidos()                      # los dormidos están en la 3, fuera de esta ruta
        r = viajar(logica, 6)                                       # 1→5→6 no pasa por la 3
        self.assertEqual((r.estado, r.recorrido), (LLEGADO, [5, 6]))
        self.assertEqual(logica.activaciones_enemigos, 0)

    def test_FR249_un_enemigo_ya_activo_en_una_sala_del_trayecto_detiene_el_viaje(self):
        enemigos = [(2, "e-0", "ent_ir_a", None)]
        fichas = [ficha_enemigo("ent_ir_a", "guardián", ataque=0)]
        logica = partida_de(pasillo(4), enemigos, fichas)
        caminar(logica, [ESTE, ESTE, ESTE, OESTE, OESTE, OESTE])   # despierta al guardián de la 2, explora hasta la 4 y vuelve
        r = viajar(logica, 4)
        self.assertEqual((r.estado, r.motivo), (DETENIDO, ENEMIGO_ACTIVO))   # el enemigo, no el daño que causa, es la causa
        self.assertEqual(r.sala_final, 2)
        self.assertEqual(logica.activaciones_enemigos, 1)                     # no se despertó a nadie en este viaje

    def test_FR249_recibir_dano_detiene_el_viaje(self):
        logica = partida_con_trampa(pasillo(4), 2)
        caminar(logica, [ESTE, ESTE, ESTE, OESTE, OESTE, OESTE])   # la trampa de la 2 se activa y luego se rearma
        esperar(logica, 8)
        antes = logica.estadoJuego.jugador.vida_actual
        r = viajar(logica, 4)
        self.assertEqual((r.estado, r.motivo), (DETENIDO, DANO))
        self.assertEqual(r.sala_final, 2)
        self.assertLess(logica.estadoJuego.jugador.vida_actual, antes)

    def test_FR249_morir_detiene_el_viaje_y_termina_la_partida(self):
        logica = partida_con_trampa(pasillo(4), 2, vida=4)         # la trampa quita 3: sobrevive la primera vez
        caminar(logica, [ESTE, ESTE, ESTE, OESTE, OESTE, OESTE])
        esperar(logica, 8)
        r = viajar(logica, 4)
        self.assertEqual((r.estado, r.motivo), (DETENIDO, MUERTE))
        self.assertTrue(logica.fin)


if __name__ == "__main__":
    unittest.main()
