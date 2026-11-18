"""«Ir a» (capacidad 006), historia 1: viajar a una sala explorada por la ruta más barata que el jugador conoce.
Contrato: specs/006-ir-a/contracts/viaje-logica.md. Cada prueba cita el requisito que demuestra."""
import unittest

from DTO.ResultadoViajeDTO import LLEGADO, RECHAZADO, YA_ESTAS_ALLI
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_rejilla, esqueleto_lineal
from tests_labs.escenarios_ir_a import (ESTE, NORTE, OESTE, SUR, caminar, cuadrado, encender_antorcha, partida_de,
                                        recorrer_cuadrado)
from tests_labs.referencia_viaje import ruta_minima_lexicografica


def viajar(logica, destino):
    """Lo que hace el servicio con la orden «ir a»: valida y, si procede, recorre el viaje completo."""
    resultado = logica.iniciarViaje(destino)
    if logica.viaje_activo is None:
        return resultado
    return logica.ejecutarViaje()


class TestRutaMasBarata(unittest.TestCase):
    def test_FR231_FR232_FR233_recorre_la_ruta_de_menor_costo_y_el_reloj_avanza_la_suma(self):
        logica = partida_de(cuadrado(a=100, b=100, c=50, d=400))     # por 2: 200; por 3: 450
        recorrer_cuadrado(logica)
        antes = logica.estadoJuego.reloj.tiempo_actual
        r = viajar(logica, 4)
        self.assertEqual(r.estado, LLEGADO)
        self.assertEqual(r.recorrido, [2, 4])
        self.assertEqual(r.pasos, 2)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 4)
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual - antes, 200)
        self.assertEqual(r.tiempo, 200)

    def test_FR232_elige_la_ruta_barata_aunque_tenga_mas_pasos(self):
        # 1-2-3-4 en cadena (3 pasos de 10) frente a una salida directa 1-4 de costo 100
        salas = esqueleto_de_conexiones([(1, 2, 10, "E", "O"), (2, 3, 10, "E", "O"), (3, 4, 10, "S", "N"), (1, 4, 100, "S", "N")])
        logica = partida_de(salas)
        caminar(logica, [ESTE, ESTE, SUR, NORTE, OESTE, OESTE])       # explora 1, 2, 3, 4 y vuelve a 1
        r = viajar(logica, 4)
        self.assertEqual(r.recorrido, [2, 3, 4])

    def test_FR234_empate_gana_la_ruta_de_menor_id_en_la_primera_posicion_que_difiere(self):
        logica = partida_de(cuadrado())                              # por 2 y por 3 cuestan lo mismo
        recorrer_cuadrado(logica)
        r = viajar(logica, 4)
        self.assertEqual(r.recorrido, [2, 4])
        self.assertEqual([1] + r.recorrido, ruta_minima_lexicografica(cuadrado(), 1, 4))

    def test_FR234_coincide_con_la_ruta_minima_lexicografica_en_rejillas_con_muchos_empates(self):
        camino_serpiente = [ESTE, ESTE, SUR, OESTE, OESTE, SUR, ESTE, ESTE]     # recorre las 9 salas de una rejilla 3x3
        for semilla in range(1, 9):
            with self.subTest(semilla=semilla):
                esqueleto = esqueleto_rejilla(3, 3, semilla=semilla, costo_max=2)
                logica = partida_de(esqueleto)
                caminar(logica, camino_serpiente)                    # termina en la sala 9, con todo explorado
                esperada = ruta_minima_lexicografica(esqueleto, 9, 1)
                r = viajar(logica, 1)
                self.assertEqual(r.estado, LLEGADO)
                self.assertEqual([9] + r.recorrido, esperada)

    def test_FR231_ir_a_la_sala_actual_no_mueve_ni_consume_tiempo(self):
        logica = partida_de(cuadrado())
        recorrer_cuadrado(logica)
        reloj = logica.estadoJuego.reloj.tiempo_actual
        r = logica.iniciarViaje(1)
        self.assertEqual((r.estado, r.motivo), (RECHAZADO, YA_ESTAS_ALLI))
        self.assertIsNone(logica.viaje_activo)
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, reloj)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 1)

    def test_FR235_no_usa_una_puerta_recordada_cerrada_como_paso(self):
        salas = esqueleto_de_conexiones([(1, 2, 50, "E", "O", {"cerrada": True}), (2, 4, 50, "S", "N"),
                                         (1, 3, 100, "S", "N"), (3, 4, 300, "E", "O")])
        logica = partida_de(salas)
        caminar(logica, [SUR, ESTE, NORTE])                          # 1→3→4→2: la puerta 1-2 queda recordada cerrada
        r = viajar(logica, 1)
        self.assertEqual(r.estado, LLEGADO)
        self.assertEqual(r.recorrido, [4, 3, 1])                     # no cruza la puerta cerrada 2→1

    def test_FR231_un_destino_explorado_solo_por_la_antorcha_es_valido(self):
        logica = partida_de(esqueleto_lineal([None, None, None]))
        encender_antorcha(logica)
        caminar(logica, [ESTE])                                      # en 2: la antorcha explora 3 sin entrar a ella
        self.assertEqual(logica.mapaConocido.estado_de(3), 2)
        r = viajar(logica, 3)
        self.assertEqual(r.estado, LLEGADO)
        self.assertEqual(r.recorrido, [3])


if __name__ == "__main__":
    unittest.main()
