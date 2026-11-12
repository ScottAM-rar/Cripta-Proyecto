"""«Ir a» (capacidad 006), historia 4: el pergamino durante un viaje. Caso B-N6 del Apéndice B.
Contrato: specs/006-ir-a/research.md D5. Cada prueba cita el requisito que demuestra."""
import unittest

from DTO.ResultadoViajeDTO import DETENIDO, LLEGADO, PERGAMINO
from tests_labs.escenarios_ir_a import (ESTE, OESTE, caminar, dar_pergamino, partida_de, pasillo, usar_pergamino)
from tests_labs.referencia_viaje import resumen_estado
from test_viaje_ruta import viajar


def sin_reloj(resumen):
    """El pergamino no consume ni devuelve tiempo y no descuenta el contador total de acciones: se compara lo demás (sala,
    vida, conocimiento, salas cargadas y acciones de la línea de tiempo vigente)."""
    return resumen[:1] + resumen[2:7] + resumen[8:]


def pasillo_explorado(n=5):
    logica = partida_de(pasillo(n))
    caminar(logica, [ESTE] * (n - 1) + [OESTE] * (n - 1))        # explora todo y vuelve a la 1
    return logica


class TestPergaminoEnViaje(unittest.TestCase):
    def test_FR244_FR245_APENDICE_B_N6_el_pergamino_revierte_solo_el_ultimo_paso_y_cancela_el_viaje(self):
        logica = pasillo_explorado()
        objeto = dar_pergamino(logica)
        logica.iniciarViaje(5)
        viaje = logica.viaje_activo
        logica.avanzarViaje()
        logica.avanzarViaje()                                       # en la 3
        antes_del_ultimo = sin_reloj(resumen_estado(logica))
        logica.avanzarViaje()                                       # en la 4: el último paso
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 4)
        usar_pergamino(logica, objeto)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 3)               # solo el último paso
        self.assertEqual(sin_reloj(resumen_estado(logica)), antes_del_ultimo)
        self.assertEqual((viaje.estado, viaje.motivo), (DETENIDO, PERGAMINO))
        self.assertIsNone(logica.viaje_activo)
        with self.assertRaises(ValueError):
            logica.avanzarViaje()                                   # el viaje no continúa
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 3)

    def test_FR244_un_segundo_pergamino_revierte_el_paso_anterior_uno_por_uso(self):
        logica = pasillo_explorado()
        primero, segundo = dar_pergamino(logica), dar_pergamino(logica)
        logica.iniciarViaje(5)
        for _ in range(3):
            logica.avanzarViaje()                                   # en la 4
        usar_pergamino(logica, primero)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 3)
        usar_pergamino(logica, segundo)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 2)

    def test_FR245_con_el_viaje_aceptado_y_sin_pasos_el_pergamino_deshace_la_accion_anterior_y_cancela(self):
        logica = partida_de(pasillo(3))
        caminar(logica, [ESTE, ESTE, OESTE, OESTE])
        objeto = dar_pergamino(logica)
        logica.iniciarViaje(3)                                      # aceptado, ningún paso dado
        viaje = logica.viaje_activo
        usar_pergamino(logica, objeto)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 2)               # deshizo la última acción (2 → 1)
        self.assertEqual((viaje.estado, viaje.motivo), (DETENIDO, PERGAMINO))
        self.assertIsNone(logica.viaje_activo)

    def test_FR244_despues_de_un_viaje_terminado_el_pergamino_revierte_su_ultimo_paso(self):
        logica = pasillo_explorado(4)
        objeto = dar_pergamino(logica)
        r = viajar(logica, 4)
        self.assertEqual(r.estado, LLEGADO)
        usar_pergamino(logica, objeto)
        self.assertEqual(logica.estadoJuego.jugador.id_sala_actual, 3)
        self.assertIsNone(logica.viaje_activo)


if __name__ == "__main__":
    unittest.main()
