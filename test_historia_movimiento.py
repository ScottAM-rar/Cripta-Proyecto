"""Consultas históricas con movimiento real entre salas (capacidad 004, FR-432, FR-440, SC-005).

Los otros tests de historia solo usan ESPERAR, así que nunca entran a una sala nueva dentro de un segmento
reproducido. Aquí el jugador recorre muchas salas, combate y usa un pergamino, y cada `historia #k` / `historia <t>`
se compara con el estado que la partida viva tenía de verdad (oráculo capturado antes de cada acción).
También se comprueba el efecto en la red/caché y que el --replay real NO queda inhibido.
"""
from __future__ import annotations

import tempfile
import unittest

from DTO.EventoDTO import EventoDTO
from DTO.Objeto import PergaminoRetroceso
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from bench.juego import ClienteDeBatalla


class FuenteContadora:
    """Envoltorio que cuenta las llamadas que una consulta histórica no debería provocar."""

    def __init__(self, fuente):
        self._fuente = fuente
        self.precargar_vecinas_llamadas = 0
        self.fijar_fichas_llamadas = 0
        self.construir_sala_llamadas = 0

    def precargar_vecinas(self, *args, **kwargs):
        self.precargar_vecinas_llamadas += 1
        return self._fuente.precargar_vecinas(*args, **kwargs)

    def fijar_fichas_en_uso(self, *args, **kwargs):
        self.fijar_fichas_llamadas += 1
        return self._fuente.fijar_fichas_en_uso(*args, **kwargs)

    def construir_sala(self, *args, **kwargs):
        self.construir_sala_llamadas += 1
        return self._fuente.construir_sala(*args, **kwargs)

    def __getattr__(self, nombre):
        return getattr(self._fuente, nombre)


def _armar(carpeta: str, capacidad_cache: int = 25, enemigos: int = 2):
    RetrocesoLogica().reiniciar()
    cliente = ClienteDeBatalla(5, 5, enemigos)
    servicio = ServicioCripta(ClientePersistente(cliente, AlmacenDisco(carpeta)), CacheLRU(capacidad_cache))
    servicio.listar_criptas()
    cripta = servicio.obtener_id_cripta(1)
    fuente = FuenteContadora(servicio)
    juego = EstadoJuegoLogica(1, cripta, fuente)
    juego.k_checkpoint = 4
    juego.ingresarEnSala(juego.estadoJuego.jugador.id_sala_actual)
    return juego, fuente, servicio, cliente, cripta


def _recorrer(juego: EstadoJuegoLogica, pasos: int, visitadas: list, oraculo: dict, pergamino_en=None, pergamino=None):
    """Camina prefiriendo salas nuevas. Antes de cada acción guarda el resumen vivo (oráculo) de esa acción k."""
    for paso in range(pasos):
        if juego.fin:
            break
        jugador = juego.estadoJuego.jugador
        sala = juego.estadoJuego.salas[jugador.id_sala_actual]
        if sala.id not in visitadas:
            visitadas.append(sala.id)
        k = juego.acciones_linea_tiempo + 1
        oraculo[k] = juego._extraerResumenEstadoActual(juego.estadoJuego.reloj.tiempo_actual, k - 1)
        if pergamino_en is not None and paso == pergamino_en:
            res = juego.accionJugador(EventoDTO(100, 0, jugador, "USAR_OBJETO", [pergamino]))
            assert res.exito, res.mensaje
            continue
        salidas = list(sala.salidas)
        nuevas = [s for s in salidas if s.sala_destino not in visitadas and not s.cerrada]
        elegida = nuevas[0] if nuevas else salidas[(paso * 7) % len(salidas)]
        res = juego.accionJugador(EventoDTO(elegida.costo, 0, jugador, "MOVER_JUGADOR", [sala, elegida.direccion]))
        assert res.exito is not False, res.mensaje


class TestHistoriaConMovimiento(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def _verificar_contra_oraculo(self, juego, oraculo):
        n = juego.acciones_linea_tiempo
        self.assertGreater(n, 10)
        for k in range(1, n + 1):
            self.assertEqual(juego._reconstruirHastaAccion(k), oraculo[k], f"historia #{k} difiere del estado vivo")
            t = oraculo[k].instante
            if juego.fin and k == n:
                # La última acción terminó la partida en el mismo instante t en que se decidió: ya no hay decisión
                # pendiente en t, así que historia <t> muestra el estado final y historia #N el estado previo.
                vivo = juego._extraerResumenEstadoActual(t, n)
                self.assertEqual(juego._reconstruirHastaInstante(t), vivo)
                continue
            self.assertEqual(juego._reconstruirHastaInstante(t), oraculo[k], f"historia <{t}> difiere del estado vivo")

    def test_recorrido_largo_coincide_con_el_estado_vivo_y_no_toca_la_red(self):
        juego, fuente, servicio, cliente, cripta = _armar(self.temp.name)
        visitadas, oraculo = [], {}
        _recorrer(juego, 120, visitadas, oraculo)
        self.assertGreaterEqual(len(visitadas), 20, "el recorrido debe pasar por muchas salas")
        self.assertGreater(len(juego.puntos_control), 3)

        reporte_antes = servicio.reporte(cripta)
        llamadas_cliente = cliente.llamadas
        precargas, fichas = fuente.precargar_vecinas_llamadas, fuente.fijar_fichas_llamadas

        self._verificar_contra_oraculo(juego, oraculo)

        self.assertEqual(servicio.reporte(cripta), reporte_antes, "el reporte de red/caché cambió con una consulta")
        self.assertEqual(cliente.llamadas, llamadas_cliente, "una consulta histórica hizo solicitudes al cliente")
        self.assertEqual(fuente.precargar_vecinas_llamadas, precargas)
        self.assertEqual(fuente.fijar_fichas_llamadas, fichas)

    def test_con_pergamino_a_mitad_del_recorrido(self):
        juego, fuente, servicio, cliente, cripta = _armar(self.temp.name)
        pergamino = PergaminoRetroceso("p_mov", "Pergamino", 0, 0)
        juego.estadoJuego.jugador.inventario.agregar_objeto(pergamino)
        visitadas, oraculo = [], {}
        _recorrer(juego, 60, visitadas, oraculo, pergamino_en=15, pergamino=pergamino)
        self.assertGreaterEqual(len(visitadas), 15)
        self.assertTrue(any('USAR_OBJETO' in linea for linea in juego.logEventos.obtener_acciones_cronologicas()),
                        'el recorrido debe incluir el uso real del pergamino')
        reporte_antes = servicio.reporte(cripta)
        self._verificar_contra_oraculo(juego, oraculo)
        self.assertEqual(servicio.reporte(cripta), reporte_antes)

    def test_cache_muy_pequena_no_provoca_solicitudes(self):
        """La caché LRU guarda fichas de catálogo; las salas ya visitadas viven en el almacén persistente. Con una
        capacidad menor que las salas visitadas, una consulta antigua tampoco pide nada a la red."""
        juego, fuente, servicio, cliente, cripta = _armar(self.temp.name, capacidad_cache=3)
        visitadas, oraculo = [], {}
        _recorrer(juego, 120, visitadas, oraculo)
        self.assertGreater(len(visitadas), 3)
        reporte_antes = servicio.reporte(cripta)
        llamadas_cliente = cliente.llamadas
        self._verificar_contra_oraculo(juego, oraculo)
        self.assertEqual(cliente.llamadas, llamadas_cliente)
        self.assertEqual(servicio.reporte(cripta), reporte_antes)

    def test_la_consulta_no_usa_el_azar_ni_el_log_vivos_con_combate(self):
        juego, fuente, servicio, cliente, cripta = _armar(self.temp.name, enemigos=3)
        visitadas, oraculo = [], {}
        _recorrer(juego, 40, visitadas, oraculo)
        azar = juego.gestorEventos.azar.getstate()
        log = juego.logEventos.obtener_acciones_cronologicas()
        bitacora = len(juego.logEventosJuego.obtener_eventos())
        for k in range(1, juego.acciones_linea_tiempo + 1):
            juego._reconstruirHastaAccion(k)
        self.assertEqual(juego.gestorEventos.azar.getstate(), azar)
        self.assertEqual(juego.logEventos.obtener_acciones_cronologicas(), log)
        self.assertEqual(len(juego.logEventosJuego.obtener_eventos()), bitacora)


class TestReplayRealNoInhibido(unittest.TestCase):
    """El --replay real debe comportarse como siempre: precarga en lotes y fija las fichas en uso."""

    def test_repetir_partida_si_precarga_y_fija_fichas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            juego, fuente, servicio, cliente, cripta = _armar(carpeta)
            _recorrer(juego, 15, [], {})
            log = juego.exportar_log()

            RetrocesoLogica().reiniciar()
            fuente2 = FuenteContadora(servicio)
            repeticion = EstadoJuegoLogica(None, None, fuente2)
            repeticion.repetirPartida(log)
            self.assertGreater(fuente2.precargar_vecinas_llamadas, 0, "la repetición real dejó de precargar")
            self.assertGreater(fuente2.fijar_fichas_llamadas, 0, "la repetición real dejó de fijar fichas en uso")


if __name__ == "__main__":
    unittest.main()
