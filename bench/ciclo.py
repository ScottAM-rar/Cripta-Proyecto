"""§5.2 Presupuesto de procesamiento: un ciclo completo de eventos entre dos decisiones del jugador, en menos de 20 ms.

Se usa el modelo real (EstadoJuegoLogica) sobre una cripta sintética ya cargada, sin red ni vista (la salida del modelo
se descarta: es renderizado). Cada ciclo es una acción ESPERAR del jugador; entre una decisión y la siguiente cada
esbirro de la sala actúa una vez, así que con E esbirros el ciclo procesa E eventos de enemigo más los del entorno.
"""
from __future__ import annotations

import contextlib
import gc
import tempfile

from DTO.EventoDTO import EventoDTO
from bench.datos import salida_muda
from bench.juego import juego_sin_iniciar, nuevo_juego
from bench.medicion import anotar, medir, nota, texto

SECCION = "Ciclo de eventos entre dos decisiones (§5.2): límite 20 ms"
ENEMIGOS = (10, 100, 300, 1_000)
ESCALA_DE_REFERENCIA = 300      # "varios cientos de eventos" (§12); 1 000 es una prueba de estrés, informativa
LIMITE_US = 20_000
CICLOS = 30
ACCIONES_DE_REPETICION = 300


def _esperar(juego):
    jugador = juego.estadoJuego.jugador
    juego.accionJugador(EventoDTO(100, 0, jugador, "ESPERAR", []))


def ejecutar(filas: list) -> bool:
    cumple_todo = True
    with tempfile.TemporaryDirectory() as carpeta, contextlib.redirect_stdout(salida_muda()):
        for enemigos in ENEMIGOS:
            juego = nuevo_juego(carpeta, enemigos)
            _esperar(juego)                                   # un ciclo previo, para no medir el arranque
            gc.collect()
            gc.freeze()                                       # lo ya creado deja de recorrerse
            pendientes = len(juego.estadoJuego.reloj.heap)
            resultado = medir(lambda: _esperar(juego), repeticiones=CICLOS)
            mediana, _, maximo = resultado
            cumple = maximo < LIMITE_US
            if enemigos <= ESCALA_DE_REFERENCIA:
                cumple_todo = cumple_todo and cumple
            anotar(filas, SECCION, f"{enemigos:>5} esbirros activos ({pendientes:>5} eventos pendientes)  1 ciclo completo", resultado)
            filas.append((SECCION, f"    ¿el peor de {CICLOS} ciclos < 20 ms?", "CUMPLE" if cumple else "NO CUMPLE", f"(máx {texto(maximo)})" + ("" if enemigos <= ESCALA_DE_REFERENCIA else "  prueba de estrés, no decide el veredicto")))

        gc.unfreeze()
        # Reproducción: se juegan N acciones, se exporta el log y se repite en un juego nuevo.
        juego = nuevo_juego(carpeta, 10)
        for _ in range(ACCIONES_DE_REPETICION):
            _esperar(juego)
        log = juego.exportar_log()
        def reproducir(_):
            otro = juego_sin_iniciar(carpeta, 10)
            otro.repetirPartida(log)
        try:
            anotar(filas, SECCION, f"reproducir un log de {ACCIONES_DE_REPETICION} acciones (incluye armar el juego)", medir(reproducir, lambda: None, repeticiones=3))
        except Exception as error:                            # el bench no debe caerse por una medición opcional
            filas.append((SECCION, f"reproducir un log de {ACCIONES_DE_REPETICION} acciones", "no disponible", str(error)))
    nota(filas, SECCION, "Un ciclo = la acción ESPERAR del jugador + todos los eventos que ocurren hasta su siguiente decisión.")
    return cumple_todo
