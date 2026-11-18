"""«Ir a» (capacidad 006), historia 3: una puerta que el mapa recuerda abierta resulta cerrada. Caso B-N2 del Apéndice B.
Contrato: specs/006-ir-a/research.md D3 y contracts/viaje-logica.md §3."""
import unittest

from DTO.ResultadoViajeDTO import LLEGADO, DETENIDO, RECHAZADO, SIN_RUTA, SIN_RUTA_INICIAL
from Logica.MapaConocido import ABIERTA, CERRADA
from tests_labs.escenarios_ir_a import (cerrar_fuera, circuito_con_puerta, lineas_del_log, partida_de,
                                        recorrer_circuito)
from test_viaje_ruta import viajar

ESTE_INDICE = 2          # norte 0, sur 1, este 2, oeste 3


def circuito_listo(con_alterna: bool):
    """Circuito explorado, el jugador en la sala 1 y la puerta este de la sala 3 cerrada lejos de él."""
    logica = partida_de(circuito_con_puerta(con_alterna))
    recorrer_circuito(logica, con_alterna)
    c = logica.mapaConocido
    assert c.puerta_recordada(3, ESTE_INDICE) == ABIERTA
    cerrar_fuera(logica, 3, "este")
    assert c.puerta_recordada(3, ESTE_INDICE) == ABIERTA          # el mapa sigue recordándola abierta (FR-208)
    return logica


class TestPuertaRecordadaAbierta(unittest.TestCase):
    def test_FR239_FR240_con_ruta_alterna_el_mapa_se_actualiza_y_el_viaje_sigue_por_la_alterna(self):
        logica = circuito_listo(con_alterna=True)
        antes = logica.estadoJuego.reloj.tiempo_actual
        r = viajar(logica, 4)
        self.assertEqual(r.estado, LLEGADO)
        self.assertEqual(r.recorrido, [2, 3, 2, 1, 5, 6, 4])       # llega a 3, ve la puerta cerrada y rodea
        self.assertEqual(logica.mapaConocido.puerta_recordada(3, ESTE_INDICE), CERRADA)
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual - antes, 800)     # solo las salidas atravesadas

    def test_FR239_FR241_APENDICE_B_N2_sin_alterna_el_viaje_se_detiene_sin_tiempo_adicional(self):
        logica = circuito_listo(con_alterna=False)
        antes = logica.estadoJuego.reloj.tiempo_actual
        acciones = logica.acciones_linea_tiempo
        r = viajar(logica, 4)
        self.assertEqual((r.estado, r.motivo), (DETENIDO, SIN_RUTA))
        self.assertEqual(r.recorrido, [2, 3])
        self.assertEqual(r.sala_final, 3)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 3)
        self.assertEqual(logica.mapaConocido.puerta_recordada(3, ESTE_INDICE), CERRADA)
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual - antes, 200)     # solo los pasos que sí se dieron
        self.assertEqual(logica.acciones_linea_tiempo - acciones, 2)               # el paso no dado no es una acción
        self.assertIsNone(logica.viaje_activo)

    def test_FR241_FR237_un_nuevo_ir_a_se_evalua_con_el_mapa_ya_actualizado(self):
        logica = circuito_listo(con_alterna=False)
        viajar(logica, 4)                                          # se detiene en 3
        reloj = logica.estadoJuego.reloj.tiempo_actual
        r = logica.iniciarViaje(4)
        self.assertEqual((r.estado, r.motivo), (RECHAZADO, SIN_RUTA_INICIAL))
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, reloj)

    def test_FR239_una_puerta_recordada_abierta_que_sigue_abierta_no_provoca_recalculo_ni_detencion(self):
        logica = partida_de(circuito_con_puerta(True))
        recorrer_circuito(logica, True)
        logica.iniciarViaje(4)
        viaje = logica.viaje_activo
        llamadas = []
        original = viaje.buscador.distancias_hacia

        def contando(destino, vista, limite):
            llamadas.append(destino)
            return original(destino, vista, limite)
        viaje.buscador.distancias_hacia = contando
        r = logica.ejecutarViaje()
        self.assertEqual((r.estado, r.recorrido), (LLEGADO, [2, 3, 4]))
        self.assertEqual(llamadas, [])                              # el conocimiento no cambió: se reutilizó el campo

    def test_FR241_la_detencion_deja_el_log_sin_el_paso_no_dado(self):
        logica = circuito_listo(con_alterna=False)
        antes = len(lineas_del_log(logica))
        viajar(logica, 4)
        nuevas = lineas_del_log(logica)[antes:]
        movimientos = [linea for linea in nuevas if "MOVER_JUGADOR" in linea]
        self.assertEqual(len(movimientos), 2)


if __name__ == "__main__":
    unittest.main()
