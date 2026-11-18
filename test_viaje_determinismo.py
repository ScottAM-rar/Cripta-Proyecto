"""«Ir a» (capacidad 006), historia 6: el viaje es reproducible y no depende del contenido descargado (FR-247, FR-248,
principio II). Contrato: specs/006-ir-a/spec.md. Cada prueba cita el requisito que demuestra."""
import unittest

from DTO.ResultadoViajeDTO import LLEGADO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from tests_labs.escenarios_ir_a import (ESTE, OESTE, caminar, escenario_viaje, lineas_del_log, partida_de, pasillo,
                                        viajar)
from tests_labs.referencia_viaje import resumen_estado


def cargadas(logica):
    salas = logica.estadoJuego.salas
    return [i for i in range(len(salas)) if salas[i] is not None]


class TestDeterminismoDelViaje(unittest.TestCase):
    def test_FR247_dos_ejecuciones_identicas_dan_el_mismo_viaje_el_mismo_mapa_y_el_mismo_log(self):
        for nombre in ("simple", "b_n3"):
            with self.subTest(escenario=nombre):
                primero, segundo = escenario_viaje(nombre), escenario_viaje(nombre)
                a, b = primero.jugar(), segundo.jugar()
                self.assertEqual(primero.resultados, segundo.resultados)
                self.assertEqual(resumen_estado(a), resumen_estado(b))
                self.assertEqual(lineas_del_log(a), lineas_del_log(b))

    def test_FR247_guardar_y_cargar_a_mitad_de_la_partida_no_cambia_el_viaje(self):
        escenario = escenario_viaje("simple")
        de_corrido = escenario.jugar()
        antes_del_viaje = escenario_viaje("simple")
        x = antes_del_viaje.jugar(hasta=len(antes_del_viaje.guion) - 1)        # todo menos el «ir a»
        estado = x.exportar_estado()
        y = escenario.nueva()
        y.restaurar_estado(estado)
        r = viajar(y, 4)
        self.assertEqual(r.estado, LLEGADO)
        self.assertEqual(r.recorrido, escenario.resultados[0].recorrido)
        self.assertEqual(resumen_estado(y)[:4], resumen_estado(de_corrido)[:4])    # sala, reloj, vida, estados de sala

    def test_FR248_el_calculo_de_la_ruta_no_depende_de_que_las_salas_esten_descargadas(self):
        resultados = []
        for precargar in (False, True):
            logica = partida_de(pasillo(6))
            caminar(logica, [ESTE] * 5 + [OESTE] * 5)
            if precargar:
                for sala in range(1, 7):
                    logica.ingresarEnSala(sala)                 # solo carga el contenido (la activación es de la sala actual)
            resultados.append(viajar(logica, 6))
        self.assertEqual(resultados[0], resultados[1])

    def test_FR248_ordenar_el_viaje_no_descarga_ninguna_sala(self):
        logica = partida_de(pasillo(6))
        caminar(logica, [ESTE] * 5 + [OESTE] * 5)
        antes = cargadas(logica)
        r = logica.iniciarViaje(6)
        self.assertEqual(r.estado, "EN_CURSO")
        self.assertEqual(cargadas(logica), antes)


if __name__ == "__main__":
    unittest.main()
