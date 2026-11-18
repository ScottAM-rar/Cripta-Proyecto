"""«Ir a» (capacidad 006): el registro del viaje en `partida.log` y su reproducción (FR-252). Contrato:
specs/006-ir-a/contracts/registro-viaje.md. Cada prueba cita el requisito que demuestra."""
import json
import unittest

from DTO.LogPartidaDTO import LogPartidaDTO
from DTO.ResultadoViajeDTO import DETENIDO, LLEGADO, PERGAMINO
from adaptadores.AlmacenPartidaBinario import VERSION_FORMATO
from DTO.EstadoGuardadoDTO import VERSION_ESTADO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from tests_labs.escenarios_ir_a import (ESTE, OESTE, caminar, dar_pergamino, escenario_viaje, lineas_del_log,
                                        partida_de, pasillo, usar_pergamino, viajar)
from tests_labs.referencia_viaje import resumen_estado


def registros(lineas):
    return [json.loads(linea) for linea in lineas]


def tipos(lineas):
    return [r["tipo_accion"] for r in registros(lineas)]


def viaje_en_el_log(nombre="simple"):
    """(escenario, partida jugada, líneas del log que añadió el viaje)."""
    escenario = escenario_viaje(nombre)
    previa = escenario.jugar(hasta=len(escenario.guion) - 1)
    antes = len(lineas_del_log(previa))
    escenario = escenario_viaje(nombre)
    logica = escenario.jugar()
    return escenario, logica, lineas_del_log(logica)[antes:]


class TestRegistroDelViaje(unittest.TestCase):
    def test_FR252_el_log_lleva_la_orden_los_pasos_y_el_resultado_en_ese_orden(self):
        escenario, logica, nuevas = viaje_en_el_log("simple")
        r = escenario.resultados[0]
        self.assertEqual(tipos(nuevas), ["IR_A"] + ["MOVER_JUGADOR"] * r.pasos + ["FIN_IR_A"])
        orden, fin = registros(nuevas)[0], registros(nuevas)[-1]
        self.assertEqual(orden["datos_extra"], [4])
        self.assertEqual(fin["datos_extra"], ["LLEGADO", "ninguno", 4])
        self.assertEqual((orden["tiempo_ejecucion"], fin["tiempo_ejecucion"]), (0, 0))

    def test_FR252_un_viaje_detenido_anota_el_motivo_y_la_sala_final(self):
        escenario, logica, nuevas = viaje_en_el_log("b_n3")
        fin = registros(nuevas)[-1]
        self.assertEqual(fin["tipo_accion"], "FIN_IR_A")
        self.assertEqual(fin["datos_extra"], ["DETENIDO", "ENEMIGOS_DORMIDOS", 3])

    def test_FR238_FR252_un_rechazo_no_escribe_nada_en_el_log(self):
        logica = partida_de(pasillo(3))
        antes = lineas_del_log(logica)
        logica.iniciarViaje(3)
        self.assertEqual(lineas_del_log(logica), antes)

    def test_FR252_un_viaje_cancelado_por_pergamino_deja_el_pergamino_antes_de_la_marca_final(self):
        logica = partida_de(pasillo(5))
        caminar(logica, [ESTE] * 4 + [OESTE] * 4)
        objeto = dar_pergamino(logica)
        antes = len(lineas_del_log(logica))
        logica.iniciarViaje(5)
        for _ in range(3):
            logica.avanzarViaje()
        usar_pergamino(logica, objeto)
        nuevas = lineas_del_log(logica)[antes:]
        self.assertEqual(tipos(nuevas), ["IR_A", "MOVER_JUGADOR", "MOVER_JUGADOR", "MOVER_JUGADOR", "USAR_OBJETO", "FIN_IR_A"])
        self.assertEqual(registros(nuevas)[-1]["datos_extra"], [DETENIDO, PERGAMINO, 3])

    def test_FR252_repetir_el_log_de_un_viaje_da_el_mismo_estado(self):
        for nombre in ("simple", "b_n3"):
            with self.subTest(escenario=nombre):
                escenario = escenario_viaje(nombre)
                original = escenario.jugar()
                repetida = escenario.repetir(original.exportar_log())
                self.assertEqual(resumen_estado(original), resumen_estado(repetida))
                self.assertEqual(lineas_del_log(original), lineas_del_log(repetida))

    def test_FR252_un_resultado_que_no_coincide_con_el_registrado_falla_como_no_fiel(self):
        escenario = escenario_viaje("simple")
        log = escenario.jugar().exportar_log()
        acciones = list(log.acciones)
        fin = json.loads(acciones[-1])
        fin["datos_extra"][2] = 3                               # el log dice que terminó en la 3, pero termina en la 4
        acciones[-1] = json.dumps(fin, ensure_ascii=False)
        manipulado = LogPartidaDTO(log.id_cripta, log.semilla, log.version_cripta, log.version_catalogo, acciones)
        with self.assertRaises(ValueError) as contexto:
            escenario.repetir(manipulado)
        self.assertIn("no es fiel", str(contexto.exception))

    def test_FR252_historia_por_accion_a_mitad_de_un_viaje_es_la_de_caminar_a_mano_esos_pasos(self):
        escenario = escenario_viaje("simple")
        logica = escenario.jugar()                              # 6 movimientos a mano y 3 pasos del viaje (acciones 7 a 9)
        resumen = logica._reconstruirHastaAccion(9)        # el estado tras 8 acciones
        mano = escenario_viaje("simple")
        mano.guion = mano.guion[:-1] + [("mover", ESTE), ("mover", ESTE)]       # 6 + 2 movimientos
        a_mano = mano.jugar()
        esperado = a_mano._extraerResumenEstadoActual(a_mano.estadoJuego.reloj.tiempo_actual, a_mano.acciones_linea_tiempo)
        self.assertEqual((resumen.id_sala_jugador, resumen.instante, resumen.acciones_jugador),
                         (esperado.id_sala_jugador, esperado.instante, esperado.acciones_jugador))
        self.assertEqual(resumen.id_sala_jugador, 3)

    def test_FR252_replay_hasta_un_instante_a_mitad_de_un_viaje_es_el_de_caminar_a_mano(self):
        escenario = escenario_viaje("simple")
        log = escenario.jugar().exportar_log()
        mano = escenario_viaje("simple")
        mano.guion = mano.guion[:-1] + [("mover", ESTE), ("mover", ESTE)]
        a_mano = mano.jugar()
        instante = a_mano.estadoJuego.reloj.tiempo_actual
        RetrocesoLogica().reiniciar()
        otra = EstadoJuegoLogica()
        otra.comunicacion = escenario.servicio()
        resultado = otra.repetirPartida(log, hasta=instante)
        self.assertEqual(resultado.id_sala_jugador, 3)
        self.assertEqual(resultado.instante_alcanzado, instante)

    def test_D8_guardar_y_cargar_con_un_viaje_ya_hecho_no_cambia_el_formato_ni_el_log(self):
        self.assertEqual((VERSION_FORMATO, VERSION_ESTADO), (8, 5))
        escenario = escenario_viaje("simple")
        original = escenario.jugar()
        estado = original.exportar_estado()
        cargada = escenario.nueva()
        cargada.restaurar_estado(estado)
        self.assertEqual(resumen_estado(cargada)[:7], resumen_estado(original)[:7])
        self.assertEqual(lineas_del_log(cargada), lineas_del_log(original))
        self.assertIsNone(cargada.viaje_activo)


if __name__ == "__main__":
    unittest.main()
