"""Pruebas exhaustivas de aislamiento para la consulta histórica (User Story 3, T018 a T020).
Garantiza que `historia <t>` e `historia #k` no alteran la partida viva:
- Reloj, acciones, puntaje, bitácora y logs (en memoria y en disco).
- Estado del generador de azar.
- Singleton RetrocesoLogica y puntero reloj.retroceso.
- Puntos de control y fichas en uso.
- Estado completo exportado (EstadoGuardadoDTO).
- Red: cero solicitudes adicionales, sin llamadas a precargar_vecinas ni fijar_fichas_en_uso.
- Determinismo de consultas y fidelidad de repetición posterior.
- Manejo seguro de errores en la reconstrucción (try/finally).
"""
from __future__ import annotations
import copy
from dataclasses import asdict
import os
import tempfile
import unittest
import uuid
from unittest.mock import patch

from DTO.EventoDTO import EventoDTO
from DTO.Objeto import PergaminoRetroceso
from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from bench.juego import servicio_sintetico


class FuenteWrapper:
    """Envoltorio sobre la fuente de la cripta para auditar llamadas de red y métodos protegidos."""

    def __init__(self, fuente_real):
        self._fuente = fuente_real
        self.llamadas_precargar_vecinas = 0
        self.llamadas_fijar_fichas_en_uso = 0

    def precargar_vecinas(self, *args, **kwargs):
        self.llamadas_precargar_vecinas += 1
        return self._fuente.precargar_vecinas(*args, **kwargs)

    def fijar_fichas_en_uso(self, *args, **kwargs):
        self.llamadas_fijar_fichas_en_uso += 1
        return getattr(self._fuente, "fijar_fichas_en_uso", lambda *a, **k: None)(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self._fuente, item)


class TestHistoriaAislamiento(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.servicio_cripta, self.cripta_id = servicio_sintetico(
            self.temp_dir.name, enemigos=1, ancho=4, alto=4
        )
        self.fuente_auditada = FuenteWrapper(self.servicio_cripta)

        # Nombre de log único para no colisionar en logs/
        self.nombre_log = f"test_aislamiento_{uuid.uuid4().hex[:8]}"
        self.servicio = EstadoJuegoServicio(comunicacion=self.fuente_auditada)
        self.servicio.k_checkpoint = 5
        self.servicio.iniciarJuego(self.cripta_id, semilla=12345, nombre_log=self.nombre_log)
        self.logica = self.servicio._estadoJuegoLogica
        self.jugador = self.logica.estadoJuego.jugador
        self.servicio.obtenerSala(self.jugador.id_sala_actual)
        self.log_path = self.servicio._almacenLog.ruta

    def tearDown(self):
        # Limpiar archivo de log creado en logs/
        # La ruta del log se crea al escribir la primera acción: se lee aquí, no en setUp (que la dejaba en None)
        ruta = getattr(self.servicio._almacenLog, "ruta", None) or self.log_path
        if ruta and os.path.exists(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass
        self.temp_dir.cleanup()

    def _esperar(self, costo: int = 100) -> None:
        ev = EventoDTO(costo, 0, self.jugador, "ESPERAR", [])
        res = self.servicio.accionJugador(ev)
        self.assertTrue(res.exito)

    def _realizar_bateria_consultas(self) -> list[ResumenEstadoDTO]:
        """Ejecuta una batería mixta de consultas históricas pasadas, vivas y repetidas."""
        reloj = self.logica.estadoJuego.reloj.tiempo_actual
        N = self.logica.acciones_linea_tiempo
        consultas = []
        # Consulta en t=0 y acción #1
        consultas.append(self.servicio.consultarHistoria(instante=0))
        consultas.append(self.servicio.consultarHistoria(accion=1))
        # Consultas intermedias
        if reloj >= 100:
            consultas.append(self.servicio.consultarHistoria(instante=100))
        if N >= 2:
            consultas.append(self.servicio.consultarHistoria(accion=2))
        # Consulta del estado vivo
        consultas.append(self.servicio.consultarHistoria(instante=reloj))
        consultas.append(self.servicio.consultarHistoria(accion=N + 1))
        # Repetición idéntica
        consultas.append(self.servicio.consultarHistoria(instante=0))
        consultas.append(self.servicio.consultarHistoria(accion=1))
        return consultas

    def test_invariancia_reloj_acciones_y_puntaje(self):
        """FR-432: Las consultas no modifican tiempo_actual, acciones_linea_tiempo, accionesJugador ni puntaje."""
        for _ in range(8):
            self._esperar(100)

        tiempo_antes = self.logica.estadoJuego.reloj.tiempo_actual
        acciones_linea_antes = self.logica.acciones_linea_tiempo
        acciones_jugador_antes = self.logica.accionesJugador
        puntaje_antes = self.logica.obtenerPuntaje()

        self._realizar_bateria_consultas()

        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, tiempo_antes)
        self.assertEqual(self.logica.acciones_linea_tiempo, acciones_linea_antes)
        self.assertEqual(self.logica.accionesJugador, acciones_jugador_antes)
        self.assertEqual(self.logica.obtenerPuntaje(), puntaje_antes)

    def test_invariancia_bitacora_y_log_memoria_y_disco(self):
        """FR-432: La bitácora, el log en memoria y el archivo de log en disco son bit a bit idénticos."""
        for _ in range(6):
            self._esperar(100)

        # Capturar bitácora
        bitacora_antes = [(r.exito, r.mensaje, r.puntaje, r.costo) for r in self.logica.logEventosJuego.obtener_eventos()]
        # Capturar log en memoria
        log_memoria_antes = list(self.logica.logEventos.obtener_acciones_cronologicas())
        # Capturar archivo de log en disco
        with open(self.log_path, "rb") as f:
            contenido_disco_antes = f.read()

        self._realizar_bateria_consultas()

        # Verificar bitácora
        bitacora_despues = [(r.exito, r.mensaje, r.puntaje, r.costo) for r in self.logica.logEventosJuego.obtener_eventos()]
        self.assertEqual(bitacora_antes, bitacora_despues)

        # Verificar log en memoria
        log_memoria_despues = list(self.logica.logEventos.obtener_acciones_cronologicas())
        self.assertEqual(log_memoria_antes, log_memoria_despues)

        # Verificar archivo en disco
        with open(self.log_path, "rb") as f:
            contenido_disco_despues = f.read()
        self.assertEqual(contenido_disco_antes, contenido_disco_despues)

    def test_invariancia_generadores_de_azar(self):
        """FR-432: El estado del generador de azar del gestor y del jugador no avanza por consultar."""
        for _ in range(6):
            self._esperar(100)

        azar_gestor_antes = self.logica.gestorEventos.azar.getstate()
        azar_jugador_antes = self.logica.jugadorLogica.azar.getstate()

        self._realizar_bateria_consultas()

        self.assertEqual(self.logica.gestorEventos.azar.getstate(), azar_gestor_antes)
        self.assertEqual(self.logica.jugadorLogica.azar.getstate(), azar_jugador_antes)

    def test_invariancia_singleton_retroceso_y_puntero_reloj(self):
        """T006/FR-432: Los 8 atributos de RetrocesoLogica y el puntero reloj.retroceso son idénticos."""
        for _ in range(6):
            self._esperar(100)

        retro = RetrocesoLogica()
        snap_antes = (
            retro.cabeza,
            retro.cola,
            retro.actual,
            retro.reloj,
            retro.cantidad_actual,
            retro.cantidad_acciones,
            retro.tiempo_evento,
            retro.suspensiones,
        )
        reloj_retro_antes = self.logica.estadoJuego.reloj.retroceso

        self._realizar_bateria_consultas()

        snap_despues = (
            retro.cabeza,
            retro.cola,
            retro.actual,
            retro.reloj,
            retro.cantidad_actual,
            retro.cantidad_acciones,
            retro.tiempo_evento,
            retro.suspensiones,
        )
        reloj_retro_despues = self.logica.estadoJuego.reloj.retroceso

        # Comprobar identidad exacta de nodos y reloj
        self.assertIs(snap_antes[0], snap_despues[0], "cabeza")
        self.assertIs(snap_antes[1], snap_despues[1], "cola")
        self.assertIs(snap_antes[2], snap_despues[2], "actual")
        self.assertIs(snap_antes[3], snap_despues[3], "reloj")
        self.assertEqual(snap_antes[4:], snap_despues[4:], "contadores")
        self.assertIs(reloj_retro_antes, reloj_retro_despues, "reloj.retroceso")

    def test_invariancia_puntos_control_y_fichas_en_uso(self):
        """Los puntos de control y las fichas en uso no sufren modificaciones."""
        for _ in range(12):
            self._esperar(100)

        puntos_antes = list(self.logica.puntos_control)
        fichas_antes = list(self.logica.fichasEnUso())

        self._realizar_bateria_consultas()

        self.assertEqual(len(self.logica.puntos_control), len(puntos_antes))
        for p1, p2 in zip(puntos_antes, self.logica.puntos_control):
            self.assertIs(p1, p2)
        self.assertEqual(self.logica.fichasEnUso(), fichas_antes)

    def test_invariancia_exportar_estado_completo(self):
        """El DTO completo de guardado (exportar_estado) es idéntico antes y después de consultar."""
        for _ in range(7):
            self._esperar(100)

        # Llamar una vez para asegurar punto 0 si no estaba ya
        _ = self.logica.exportar_estado()

        estado_antes = asdict(self.logica.exportar_estado())
        self._realizar_bateria_consultas()
        estado_despues = asdict(self.logica.exportar_estado())

        self.assertEqual(estado_antes, estado_despues)

    def test_auditoria_red_cero_solicitudes_y_sin_llamadas_prohibidas(self):
        """FR-440, T019, T020: Delta de solicitudes de red = 0.
        precargar_vecinas y fijar_fichas_en_uso no son invocadas desde la reconstrucción."""
        for _ in range(8):
            self._esperar(100)

        reporte_antes = self.servicio.reporteSolicitudes()
        solicitudes_antes = reporte_antes.solicitudes
        llamadas_precarga_antes = self.fuente_auditada.llamadas_precargar_vecinas
        llamadas_fichas_antes = self.fuente_auditada.llamadas_fijar_fichas_en_uso

        self._realizar_bateria_consultas()

        reporte_despues = self.servicio.reporteSolicitudes()
        delta_solicitudes = reporte_despues.solicitudes - solicitudes_antes
        delta_precarga = self.fuente_auditada.llamadas_precargar_vecinas - llamadas_precarga_antes
        delta_fichas = self.fuente_auditada.llamadas_fijar_fichas_en_uso - llamadas_fichas_antes

        self.assertEqual(delta_solicitudes, 0, "No debe realizar ninguna solicitud de red adicional")
        self.assertEqual(delta_precarga, 0, "No debe llamar a precargar_vecinas en reconstrucción")
        self.assertEqual(delta_fichas, 0, "No debe llamar a fijar_fichas_en_uso en reconstrucción")

        # Registro explícito de comportamiento de caché para reporte
        delta_aciertos = reporte_despues.aciertos_cache - reporte_antes.aciertos_cache
        delta_fallos = reporte_despues.fallos_cache - reporte_antes.fallos_cache
        print(f"\n[Auditoría Caché] Delta solicitudes: {delta_solicitudes}, "
              f"Delta aciertos: {delta_aciertos}, Delta fallos: {delta_fallos}")

    def test_determinismo_consultas_identicas(self):
        """Determinismo: Dos llamadas idénticas devuelven resúmenes equivalentes campo por campo."""
        for _ in range(8):
            self._esperar(100)

        r1 = self.servicio.consultarHistoria(instante=200)
        r2 = self.servicio.consultarHistoria(instante=200)
        self.assertEqual(asdict(r1), asdict(r2))

        k1 = self.servicio.consultarHistoria(accion=3)
        k2 = self.servicio.consultarHistoria(accion=3)
        self.assertEqual(asdict(k1), asdict(k2))

    def test_partida_continua_y_replay_fiel_tras_consultas(self):
        """Tras intercalar consultas, la partida sigue jugando y el replay reproduce fielmente."""
        for _ in range(5):
            self._esperar(100)

        # Intercalar consultas
        self._realizar_bateria_consultas()

        # Seguir jugando
        for _ in range(5):
            self._esperar(100)

        self.assertEqual(self.logica.acciones_linea_tiempo, 10)

        # Replay completo con repetirPartida
        log_dto = self.logica.exportar_log()
        juego_replay = EstadoJuegoLogica(comunicacion=self.servicio_cripta)
        resultados = juego_replay.repetirPartida(log_dto)
        self.assertEqual(len(resultados), 10)
        self.assertEqual(juego_replay.estadoJuego.reloj.tiempo_actual, self.logica.estadoJuego.reloj.tiempo_actual)
        self.assertEqual(juego_replay.estadoJuego.jugador.vida_actual, self.jugador.vida_actual)

    def test_error_en_reconstruccion_deja_intacto_singleton_y_partida(self):
        """Si ocurre un error inesperado a mitad de la pasada 2, el singleton RetrocesoLogica
        y la partida viva se restauran íntegramente."""
        for _ in range(5):
            self._esperar(100)

        retro = RetrocesoLogica()
        snap_antes = (
            retro.cabeza,
            retro.cola,
            retro.actual,
            retro.reloj,
            retro.cantidad_actual,
            retro.cantidad_acciones,
            retro.tiempo_evento,
            retro.suspensiones,
        )
        reloj_retro_antes = self.logica.estadoJuego.reloj.retroceso
        tiempo_antes = self.logica.estadoJuego.reloj.tiempo_actual

        # Inyectar error a mitad de _ejecutarPasada2
        with patch.object(self.logica, "_hidratarInstanciaAislada", side_effect=RuntimeError("Fallo simulado")):
            with self.assertRaises(RuntimeError):
                self.servicio.consultarHistoria(instante=100)

        snap_despues = (
            retro.cabeza,
            retro.cola,
            retro.actual,
            retro.reloj,
            retro.cantidad_actual,
            retro.cantidad_acciones,
            retro.tiempo_evento,
            retro.suspensiones,
        )
        self.assertIs(snap_antes[0], snap_despues[0])
        self.assertIs(reloj_retro_antes, self.logica.estadoJuego.reloj.retroceso)
        self.assertEqual(self.logica.estadoJuego.reloj.tiempo_actual, tiempo_antes)


if __name__ == "__main__":
    unittest.main()
