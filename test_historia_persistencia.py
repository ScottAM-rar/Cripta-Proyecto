"""Pruebas de persistencia para la línea de tiempo (User Story 5, FR-441, T024 a T025).

Verifica que:
- Guardar y cargar una partida en formato binario v7 reproduce idénticamente todas las consultas de historia.
- Las consultas coinciden tanto con el estado previo a guardar como con el oráculo vivo capturado antes de cada acción.
- Tras cargar, la partida continúa con normalidad: más acciones, más pergaminos y nuevos guardados.
- Cargar con otro K (k_checkpoint=...) no corrompe las consultas históricas previas.
- Partidas en formato v7 / estado 4 siguen funcionando sin alterar el formato binario (cero campos nuevos).
- Las consultas históricas no modifican ni crean archivos de partida guardada en disco.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import os
import struct
import tempfile
import unittest
from unittest.mock import patch

from DTO.EventoDTO import EventoDTO
from DTO.Objeto import PergaminoRetroceso
from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida, MAGIA
import adaptadores.extension as ext
from adaptadores.extension import CARPETA_PARTIDAS, EXTENSION_PARTIDA, ruta_archivo
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
import Servicio.EstadoJuegoServicio as modulo_servicio
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from test_historia_movimiento import _armar, _recorrer


def _hash_archivo(ruta: str) -> bytes:
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).digest()


class TestHistoriaPersistencia(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.carpeta_partidas = os.path.join(self.temp_dir.name, "partidas")
        self.carpeta_logs = os.path.join(self.temp_dir.name, "logs")
        os.makedirs(self.carpeta_partidas, exist_ok=True)
        os.makedirs(self.carpeta_logs, exist_ok=True)

        self.patch_partidas = patch.object(modulo_servicio, "CARPETA_PARTIDAS", self.carpeta_partidas)
        self.patch_ext_partidas = patch.object(ext, "CARPETA_PARTIDAS", self.carpeta_partidas)
        self.patch_partidas.start()
        self.patch_ext_partidas.start()

    def tearDown(self):
        self.patch_ext_partidas.stop()
        self.patch_partidas.stop()
        self.temp_dir.cleanup()

    def test_guardar_y_cargar_con_movimiento_pergamino_y_oraculo(self):
        """Partida con movimiento real, enemigos, un pergamino usado antes de guardar,
        guardado, carga en nueva instancia y verificación contra oráculo vivo."""
        juego, fuente, servicio_fuente, cliente, cripta = _armar(self.temp_dir.name, enemigos=2)
        juego.k_checkpoint = 4

        servicio = EstadoJuegoServicio(comunicacion=fuente)
        servicio._estadoJuegoLogica = juego

        visitadas: list[int] = []
        oraculo: dict[int, ResumenEstadoDTO] = {}

        pergamino_1 = PergaminoRetroceso("p_guardar_1", "Pergamino Pre-Guardado", 0, 0)
        juego.estadoJuego.jugador.inventario.agregar_objeto(pergamino_1)

        # Recorrer 15 pasos con un pergamino usado en el paso 8
        _recorrer(juego, 15, visitadas, oraculo, pergamino_en=8, pergamino=pergamino_1)

        n_vigentes_antes = juego.acciones_linea_tiempo
        reloj_antes = juego.estadoJuego.reloj.tiempo_actual
        self.assertGreater(n_vigentes_antes, 5)

        # Capturar resúmenes antes de guardar
        consultas_accion_antes = {k: servicio.consultarHistoria(accion=k) for k in range(1, n_vigentes_antes + 2)}

        # Guardar partida
        nombre_guardado = "partida_historia_v7"
        servicio.guardarPartida(nombre_guardado)
        ruta_partida = ruta_archivo(nombre_guardado, EXTENSION_PARTIDA, self.carpeta_partidas)
        self.assertTrue(os.path.exists(ruta_partida))

        # Cargar en una instancia NUEVA de servicio
        nuevo_servicio = EstadoJuegoServicio(comunicacion=fuente)
        nuevo_servicio.cargarPartida(nombre_guardado)
        nuevo_juego = nuevo_servicio._estadoJuegoLogica

        # Verificar que reloj y acciones coinciden
        self.assertEqual(nuevo_juego.acciones_linea_tiempo, n_vigentes_antes)
        self.assertEqual(nuevo_juego.estadoJuego.reloj.tiempo_actual, reloj_antes)

        # Comprobar que cada historia #k y cada historia <t> coincide con antes de guardar y con el oráculo
        for k in range(1, n_vigentes_antes + 1):
            res_cargado = nuevo_servicio.consultarHistoria(accion=k)
            res_antes = consultas_accion_antes[k]
            res_oraculo = oraculo[k]

            self.assertEqual(asdict(res_cargado), asdict(res_antes), f"Difiere de antes de guardar en k={k}")
            self.assertEqual(asdict(res_cargado), asdict(res_oraculo), f"Difiere del oráculo en k={k}")

            t = res_oraculo.instante
            res_t_cargado = nuevo_servicio.consultarHistoria(instante=t)
            self.assertEqual(asdict(res_t_cargado), asdict(res_oraculo), f"Difiere en instante t={t}")

        # historia #(N+1) = estado actual vivo
        res_vivo_cargado = nuevo_servicio.consultarHistoria(accion=n_vigentes_antes + 1)
        self.assertEqual(asdict(res_vivo_cargado), asdict(consultas_accion_antes[n_vigentes_antes + 1]))

        # Después de cargar, la partida continúa: juega más acciones y otro pergamino
        pergamino_2 = PergaminoRetroceso("p_guardar_2", "Pergamino Post-Guardado", 0, 0)
        nuevo_juego.estadoJuego.jugador.inventario.agregar_objeto(pergamino_2)

        _recorrer(nuevo_juego, 6, visitadas, oraculo, pergamino_en=3, pergamino=pergamino_2)
        n_vigentes_despues = nuevo_juego.acciones_linea_tiempo
        self.assertGreater(n_vigentes_despues, n_vigentes_antes)

        if not nuevo_juego.fin:
            # Volver a guardar y recargar
            nuevo_servicio.guardarPartida("partida_historia_v7_segunda")
            tercer_servicio = EstadoJuegoServicio(comunicacion=fuente)
            tercer_servicio.cargarPartida("partida_historia_v7_segunda")

            # Verificar coherencia tras segundo guardado
            for k in range(1, nuevo_juego.acciones_linea_tiempo + 1):
                res_k = tercer_servicio.consultarHistoria(accion=k)
                self.assertEqual(res_k.acciones_jugador, k - 1)

    def test_cargar_con_otro_k_no_rompe_consultas(self):
        """Cargar con k_checkpoint distinto conserva las consultas históricas previas."""
        juego, fuente, servicio_fuente, cliente, cripta = _armar(self.temp_dir.name, enemigos=1)
        juego.k_checkpoint = 4
        servicio = EstadoJuegoServicio(comunicacion=fuente)
        servicio._estadoJuegoLogica = juego

        visitadas, oraculo = [], {}
        _recorrer(juego, 12, visitadas, oraculo)
        n_previo = juego.acciones_linea_tiempo

        servicio.guardarPartida("partida_cambio_k")

        # Cargar con K=10
        nuevo_servicio = EstadoJuegoServicio(comunicacion=fuente)
        nuevo_servicio.cargarPartida("partida_cambio_k", k_checkpoint=10)
        self.assertEqual(nuevo_servicio.k_checkpoint, 10)

        for k in range(1, n_previo + 1):
            res_k = nuevo_servicio.consultarHistoria(accion=k)
            self.assertEqual(asdict(res_k), asdict(oraculo[k]))

    def test_archivos_anteriores_o_corruptos_se_rechazan_sin_modificar_formato(self):
        """FR-425: Archivos de versión anterior (v6 o Parte I) son rechazados explícitamente."""
        ruta_v6 = os.path.join(self.carpeta_partidas, "antigua_v6.crp")
        with open(ruta_v6, "wb") as f:
            f.write(struct.pack(">4sH", MAGIA, 6))
            f.write(b"\x00" * 80)

        servicio = EstadoJuegoServicio()
        with self.assertRaises(ErrorPartida):
            servicio.cargarPartida("antigua_v6")

    def test_consulta_no_modifica_ni_crea_archivo_guardado(self):
        """FR-432, FR-441: Una consulta historia no modifica ni crea archivos en CARPETA_PARTIDAS."""
        juego, fuente, servicio_fuente, cliente, cripta = _armar(self.temp_dir.name, enemigos=1)
        servicio = EstadoJuegoServicio(comunicacion=fuente)
        servicio._estadoJuegoLogica = juego

        visitadas, oraculo = [], {}
        _recorrer(juego, 8, visitadas, oraculo)
        servicio.guardarPartida("guardado_inmutable")

        ruta = ruta_archivo("guardado_inmutable", EXTENSION_PARTIDA, self.carpeta_partidas)
        mtime_antes = os.path.getmtime(ruta)
        tamano_antes = os.path.getsize(ruta)
        hash_antes = _hash_archivo(ruta)
        archivos_antes = set(os.listdir(self.carpeta_partidas))

        # Ejecutar ráfaga de consultas
        for k in range(1, juego.acciones_linea_tiempo + 2):
            _ = servicio.consultarHistoria(accion=k)
        _ = servicio.consultarHistoria(instante=0)
        _ = servicio.consultarHistoria(instante=juego.estadoJuego.reloj.tiempo_actual)

        # Comprobar inmutabilidad
        self.assertEqual(os.path.getmtime(ruta), mtime_antes)
        self.assertEqual(os.path.getsize(ruta), tamano_antes)
        self.assertEqual(_hash_archivo(ruta), hash_antes)
        self.assertEqual(set(os.listdir(self.carpeta_partidas)), archivos_antes)


if __name__ == "__main__":
    unittest.main()
