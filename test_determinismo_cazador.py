"""Historia 4: misma cripta, semilla y acciones con cazadores dan la misma partida (FR-120, FR-117).

Los logs de specs/001-terreno-y-cazador/replays/ citan en su nombre el requisito que demuestran; se generan con
`python -m tests_labs.escenarios_terreno` y aquí se reproducen sin vista, como hace --replay."""
import os
import unittest

from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from tests_labs.escenarios_terreno import CARPETA_REPLAYS, ESCENARIOS, firma


def escenario(nombre):
    return next(e for e in ESCENARIOS if e.nombre == nombre)


class TestDeterminismoDelCazador(unittest.TestCase):
    def test_FR120_dos_partidas_con_la_misma_cripta_semilla_y_acciones_son_identicas(self):
        for e in ESCENARIOS:
            with self.subTest(escenario=e.nombre):
                a, ruta_a = e.jugar()
                b, ruta_b = e.jugar()
                self.assertEqual(firma(a), firma(b))
                self.assertEqual(ruta_a, ruta_b)

    def test_FR117_la_decision_no_depende_de_que_contenido_ya_este_descargado(self):
        for e in ESCENARIOS:
            with self.subTest(escenario=e.nombre):
                pocas, ruta_pocas = e.jugar(precargar_todas=False)
                todas, ruta_todas = e.jugar(precargar_todas=True)
                self.assertEqual(ruta_pocas, ruta_todas)
                self.assertEqual(firma(pocas), firma(todas))

    def test_FR120_cada_log_de_reproduccion_existe_y_reproduce_la_misma_partida(self):
        for e in ESCENARIOS:
            with self.subTest(log=e.nombre):
                ruta = os.path.join(CARPETA_REPLAYS, e.nombre + ".log")
                self.assertTrue(os.path.exists(ruta), f"falta {ruta}: ejecuta python -m tests_labs.escenarios_terreno")
                original, _ = e.jugar()
                log = AlmacenLogTexto.leer(e.nombre, CARPETA_REPLAYS)
                self.assertEqual(log.acciones, original.exportar_log().acciones)       # el log guardado sigue siendo fiel
                primera = e.repetir(log)
                segunda = e.repetir(log)
                self.assertEqual(firma(primera), firma(original))
                self.assertEqual(firma(segunda), firma(original))

    def test_FR113_el_log_de_persecucion_termina_con_el_cazador_atacando_al_jugador(self):
        e = escenario("FR113_persecucion_con_costo")
        logica, ruta = e.jugar()
        self.assertEqual(ruta, [2, 1])
        self.assertLess(logica.estadoJuego.jugador.vida_actual, logica.estadoJuego.jugador.vida_max)

    def test_FR112_el_log_fuera_de_rango_deja_al_cazador_quieto_y_al_jugador_sano(self):
        e = escenario("FR112_fuera_de_rango_espera")
        logica, ruta = e.jugar()
        self.assertEqual(ruta, [2])
        self.assertEqual(logica.estadoJuego.jugador.vida_actual, logica.estadoJuego.jugador.vida_max)

    def test_FR114_el_log_de_desempate_hace_que_el_cazador_pase_por_la_sala_2_y_no_por_la_3(self):
        e = escenario("FR114_desempate_por_menor_id")
        logica, ruta = e.jugar()
        self.assertEqual(ruta[:2], [1, 2])
        self.assertNotIn(3, ruta)


if __name__ == "__main__":
    unittest.main()
