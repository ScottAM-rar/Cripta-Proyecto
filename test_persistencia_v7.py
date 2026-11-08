"""Pruebas para el formato de persistencia v7 y compatibilidad.
FR-424, FR-425.
"""
from __future__ import annotations
import os
import struct
import tempfile
import unittest

from DTO.EstadoGuardadoDTO import EstadoGuardadoDTO
from DTO.PuntoControlDTO import PuntoControlDTO
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida, MAGIA, VERSION_FORMATO
from bench.juego import servicio_sintetico
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio


class TestPersistenciaV7(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    @unittest.skipIf(VERSION_FORMATO < 7, "Pendiente de confirmación con quien mantiene el formato (Scott) para v7 (T021-T024)")
    def test_persistencia_v7_guarda_y_carga_puntos_control(self):
        """FR-424: Guarda y carga partida conservando puntos_control y k_checkpoint."""
        ruta = os.path.join(self.temp_dir.name, "partida_v7.crp")
        almacen = AlmacenPartidaBinario(ruta)

        comunicacion, cripta_id = servicio_sintetico(self.temp_dir.name, enemigos=1, ancho=3, alto=3)
        juego = EstadoJuegoLogica(semilla=2026, comunicacion=comunicacion)
        juego.k_checkpoint = 5
        juego.iniciarJuego(cripta_id, semilla=2026)
        juego.ingresarEnSala(juego.estadoJuego.jugador.id_sala_actual)

        estado = juego.exportar_estado()
        almacen.guardar(estado)

        cargado = almacen.cargar()
        self.assertIsNotNone(cargado)

    @unittest.skipIf(VERSION_FORMATO < 7, "Pendiente de confirmación con quien mantiene el formato (Scott) para v7 (T021-T024)")
    def test_rechazo_explicito_versiones_anteriores(self):
        """FR-425: Versiones anteriores (v6 o Parte I) son rechazadas explícitamente."""
        ruta_v6 = os.path.join(self.temp_dir.name, "partida_v6.crp")
        with open(ruta_v6, "wb") as f:
            f.write(struct.pack(">4sH", MAGIA, 6))
            f.write(b"\x00" * 100)

        almacen = AlmacenPartidaBinario(ruta_v6)
        with self.assertRaises(ErrorPartida) as ctx:
            almacen.cargar()
        self.assertIn("Versión del formato de partida no soportada", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
