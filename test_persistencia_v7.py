"""Pruebas para el formato de persistencia v7 y compatibilidad.
FR-424, FR-425.
"""
from __future__ import annotations
import os
import struct
import tempfile
import unittest
from unittest.mock import patch

from DTO.EstadoGuardadoDTO import EstadoGuardadoDTO, SalaGuardadaDTO
from DTO.EventoDTO import EventoDTO
from DTO.PuntoControlDTO import PuntoControlDTO
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida, MAGIA, VERSION_FORMATO
from bench.juego import servicio_sintetico
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
import Servicio.EstadoJuegoServicio as modulo_servicio
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio


class TestPersistenciaV7(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _crear_juego(self, semilla: int = 2026, k: int = 5, enemigos: int = 1, ancho: int = 3, alto: int = 3):
        comunicacion, cripta_id = servicio_sintetico(self.temp_dir.name, enemigos=enemigos, ancho=ancho, alto=alto)
        juego = EstadoJuegoLogica(semilla=semilla, comunicacion=comunicacion)
        juego.k_checkpoint = k
        juego.iniciarJuego(cripta_id, semilla=semilla)
        juego.ingresarEnSala(juego.estadoJuego.jugador.id_sala_actual)
        return juego, comunicacion, cripta_id

    def _accion_esperar(self, juego: EstadoJuegoLogica, costo: int = 100):
        ev = EventoDTO(
            tiempo_ejecucion=costo,
            id_secuencia=0,
            actor=juego.estadoJuego.jugador,
            tipo_accion="ESPERAR",
            datos_extra=[]
        )
        juego.accionJugador(ev)

    def test_guardar_y_cargar_conserva_n_puntos_k_y_acciones_linea_tiempo(self):
        """FR-424: Guardar y cargar conserva N puntos, K, acciones_linea_tiempo y cada punto es igual al original."""
        juego, comunicacion, cripta_id = self._crear_juego(semilla=2026, k=5)
        for _ in range(15):
            self._accion_esperar(juego)

        estado_original = juego.exportar_estado()
        self.assertEqual(len(estado_original.puntos_control), 4)  # puntos 0, 5, 10, 15
        self.assertEqual(estado_original.acciones_linea_tiempo, 15)
        self.assertEqual(estado_original.k_checkpoint, 5)

        ruta = os.path.join(self.temp_dir.name, "partida_v7.crp")
        almacen = AlmacenPartidaBinario(ruta)
        almacen.guardar(estado_original)

        cargado = almacen.cargar()
        self.assertIsNotNone(cargado)
        self.assertEqual(cargado.k_checkpoint, estado_original.k_checkpoint)
        self.assertEqual(cargado.acciones_linea_tiempo, estado_original.acciones_linea_tiempo)
        self.assertEqual(len(cargado.puntos_control), len(estado_original.puntos_control))

        for orig_pto, carg_pto in zip(estado_original.puntos_control, cargado.puntos_control):
            self.assertEqual(carg_pto.numero_punto, orig_pto.numero_punto)
            self.assertEqual(carg_pto.acciones_linea_tiempo, orig_pto.acciones_linea_tiempo)
            self.assertEqual(carg_pto.instante_reloj, orig_pto.instante_reloj)
            self.assertEqual(carg_pto.longitud_bitacora, orig_pto.longitud_bitacora)
            self.assertEqual(carg_pto.longitud_acciones_log, orig_pto.longitud_acciones_log)
            # El estado dentro del punto
            self.assertEqual(carg_pto.estado.jugador.vida_actual, orig_pto.estado.jugador.vida_actual)
            self.assertEqual(carg_pto.estado.jugador.id_sala_actual, orig_pto.estado.jugador.id_sala_actual)
            self.assertEqual(carg_pto.estado.reloj.tiempo_actual, orig_pto.estado.reloj.tiempo_actual)
            self.assertEqual(carg_pto.estado.puntos_control, [])

    def test_partida_cargada_y_continuada_produce_mismo_log_y_estado_final(self):
        """FR-424, FR-422: Partida cargada y continuada produce el mismo log y estado final que la original sin guardar."""
        # Instancia 1: original continua hasta 20 acciones
        juego_orig, comunicacion, cripta_id = self._crear_juego(semilla=2026, k=5)
        for _ in range(10):
            self._accion_esperar(juego_orig)

        ruta = os.path.join(self.temp_dir.name, "partida_intermedia.crp")
        almacen = AlmacenPartidaBinario(ruta)
        almacen.guardar(juego_orig.exportar_estado())

        for _ in range(10):
            self._accion_esperar(juego_orig)
        estado_final_orig = juego_orig.exportar_estado()
        log_final_orig = list(juego_orig.logEventos.obtener_acciones_cronologicas())

        # Instancia 2: carga en la acción 10 y continúa las mismas 10 acciones
        juego_cargado = EstadoJuegoLogica(semilla=2026, comunicacion=comunicacion)
        estado_guardado = almacen.cargar()
        juego_cargado.restaurar_estado(estado_guardado)

        for _ in range(10):
            self._accion_esperar(juego_cargado)
        estado_final_cargado = juego_cargado.exportar_estado()
        log_final_cargado = list(juego_cargado.logEventos.obtener_acciones_cronologicas())

        self.assertEqual(log_final_cargado, log_final_orig)
        self.assertEqual(estado_final_cargado.jugador.vida_actual, estado_final_orig.jugador.vida_actual)
        self.assertEqual(estado_final_cargado.jugador.id_sala_actual, estado_final_orig.jugador.id_sala_actual)
        self.assertEqual(estado_final_cargado.puntaje, estado_final_orig.puntaje)
        self.assertEqual(estado_final_cargado.acciones_jugador, estado_final_orig.acciones_jugador)
        self.assertEqual(estado_final_cargado.reloj.tiempo_actual, estado_final_orig.reloj.tiempo_actual)
        self.assertEqual(estado_final_cargado.estado_azar, estado_final_orig.estado_azar)

    def test_cargar_sin_bandera_conserva_k_del_archivo(self):
        """FR-424: Cargar sin bandera conserva el K guardado en el archivo."""
        juego, comunicacion, cripta_id = self._crear_juego(semilla=2026, k=7)
        for _ in range(7):
            self._accion_esperar(juego)

        with patch.object(modulo_servicio, "CARPETA_PARTIDAS", self.temp_dir.name):
            servicio = EstadoJuegoServicio(comunicacion=comunicacion)
            servicio._estadoJuegoLogica = juego
            servicio.guardarPartida("guardado_k7")

            nuevo_servicio = EstadoJuegoServicio(comunicacion=comunicacion)
            nuevo_servicio.cargarPartida("guardado_k7", k_checkpoint=None)
            self.assertEqual(nuevo_servicio.k_checkpoint, 7)

    def test_cargar_con_bandera_cambia_k_futuro_y_conserva_puntos(self):
        """FR-424: Cargar con bandera cambia el K futuro y conserva los puntos previos con espaciado correcto."""
        juego, comunicacion, cripta_id = self._crear_juego(semilla=2026, k=5)
        for _ in range(15):
            self._accion_esperar(juego)
        puntos_previos = len(juego.puntos_control)  # 4 puntos (0, 5, 10, 15)

        with patch.object(modulo_servicio, "CARPETA_PARTIDAS", self.temp_dir.name):
            servicio = EstadoJuegoServicio(comunicacion=comunicacion)
            servicio._estadoJuegoLogica = juego
            servicio.guardarPartida("guardado_k5")

            nuevo_servicio = EstadoJuegoServicio(comunicacion=comunicacion)
            nuevo_servicio.cargarPartida("guardado_k5", k_checkpoint=12)
            self.assertEqual(nuevo_servicio.k_checkpoint, 12)

            logica = nuevo_servicio._estadoJuegoLogica
            self.assertEqual(len(logica.puntos_control), puntos_previos)

            # Ejecutar 30 acciones adicionales
            for _ in range(30):
                self._accion_esperar(logica)

            puntos_totales = logica.puntos_control
            self.assertGreater(len(puntos_totales), puntos_previos)

            # Verificar que dos puntos consecutivos nuevos distan al menos el K nuevo (12)
            for i in range(puntos_previos, len(puntos_totales)):
                delta = puntos_totales[i].acciones_linea_tiempo - puntos_totales[i - 1].acciones_linea_tiempo
                self.assertGreaterEqual(delta, 12)

    def test_rechazo_explicito_versiones_anteriores_v6_y_parte_i(self):
        """FR-425: Versiones anteriores (v6 o Parte I) son rechazadas explícitamente con mensaje claro."""
        # Versión 6
        ruta_v6 = os.path.join(self.temp_dir.name, "partida_v6.crp")
        with open(ruta_v6, "wb") as f:
            f.write(struct.pack(">4sH", MAGIA, 6))
            f.write(b"\x00" * 100)

        almacen_v6 = AlmacenPartidaBinario(ruta_v6)
        with self.assertRaises(ErrorPartida) as ctx_v6:
            almacen_v6.cargar()
        mensaje_v6 = str(ctx_v6.exception)
        self.assertIn("Versión del formato de partida no soportada", mensaje_v6)
        self.assertIn("versión anterior", mensaje_v6)

        # Versión 1 (Parte I)
        ruta_v1 = os.path.join(self.temp_dir.name, "partida_v1.crp")
        with open(ruta_v1, "wb") as f:
            f.write(struct.pack(">4sH", MAGIA, 1))
            f.write(b"\x00" * 100)

        almacen_v1 = AlmacenPartidaBinario(ruta_v1)
        with self.assertRaises(ErrorPartida) as ctx_v1:
            almacen_v1.cargar()
        mensaje_v1 = str(ctx_v1.exception)
        self.assertIn("Versión del formato de partida no soportada", mensaje_v1)
        self.assertIn("versión anterior", mensaje_v1)

    def test_guardar_antes_de_primera_accion_deja_punto_0(self):
        """FR-424, FR-418: Guardar antes de la primera acción deja el punto 0 en el archivo."""
        juego, comunicacion, cripta_id = self._crear_juego(semilla=2026, k=5)
        # No se ejecuta ninguna acción del jugador
        ruta = os.path.join(self.temp_dir.name, "partida_inicial.crp")
        almacen = AlmacenPartidaBinario(ruta)
        almacen.guardar(juego.exportar_estado())

        cargado = almacen.cargar()
        self.assertEqual(len(cargado.puntos_control), 1)
        self.assertEqual(cargado.puntos_control[0].numero_punto, 0)
        self.assertEqual(cargado.puntos_control[0].acciones_linea_tiempo, 0)

    def test_leer_sala_sigue_funcionando(self):
        """FR-424: La lectura directa e indexada de salas (leer_sala) sigue funcionando en v7."""
        juego, comunicacion, cripta_id = self._crear_juego(semilla=2026, k=5)
        for _ in range(5):
            self._accion_esperar(juego)

        ruta = os.path.join(self.temp_dir.name, "partida_salas.crp")
        almacen = AlmacenPartidaBinario(ruta)
        almacen.guardar(juego.exportar_estado())

        numeros = almacen.numeros_de_salas()
        self.assertTrue(len(numeros) > 0)
        primera_sala = almacen.leer_sala(numeros[0])
        self.assertIsNotNone(primera_sala)
        self.assertIsInstance(primera_sala, SalaGuardadaDTO)
        self.assertEqual(primera_sala.id, numeros[0])

        # Sala inexistente
        self.assertIsNone(almacen.leer_sala(99999))


if __name__ == "__main__":
    unittest.main()
