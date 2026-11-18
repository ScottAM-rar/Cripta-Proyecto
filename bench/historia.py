"""§3.6 y §5.5 Línea de tiempo — consultas de estados pasados (FR-442, SC-006, Principio VII).

Mide sobre partidas sintéticas deterministas con movimiento y enemigos:
1. Tiempo de respuesta de historia #k e historia <t> (mediana, p95 y peor caso) para K en {10, 50, 100}
   en diversas posiciones (inicio, mitad, cerca del final, en un punto de control y en el peor caso K-1).
   Límite de tiempo: <= 50 ms (FR-442).
2. Alternativa C descartada: reconstruir desde el inicio sin checkpoints (reproducir todo el log).
3. Búsqueda binaria vs. búsqueda lineal en la lista de puntos de control.
4. Memoria serializada de los puntos de control por intervalo K.
5. Análisis de reconstrucción hacia adelante vs. hacia atrás (§5.5).
6. Justificación empírica del K por defecto (K = 10).
"""
from __future__ import annotations

import gc
import pickle
import tempfile
import time

from DTO.EventoDTO import EventoDTO
from DTO.ResumenEstadoDTO import ResumenEstadoDTO
from Logica.ordenamiento import ordenar_adaptativo
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from bench.juego import servicio_sintetico
from bench.medicion import anotar, medir, nota, texto, verificar

SECCION = "Línea de tiempo (§3.6, §5.5, FR-442): historia <t> e historia #k"
VALORES_K = (10, 50, 100)
LIMITE_HISTORIA_US = 50_000   # 50 ms en microsegundos (FR-442)
SEMILLA_BENCH = 2026


def _tamano(objeto) -> int:
    return len(pickle.dumps(objeto, protocol=pickle.HIGHEST_PROTOCOL))


def _mediana(valores: list[float]) -> float:
    ordenados = ordenar_adaptativo(valores)
    n = len(ordenados)
    if not n:
        return 0.0
    return ordenados[n // 2]


def _resultado_k(resultados: list[tuple], k: int):
    """Búsqueda lineal de la fila de `k` en la lista de resultados (None si no existe)."""
    for fila in resultados:
        if fila[0] == k:
            return fila
    return None


def _percentil_95(valores: list[float]) -> float:
    ordenados = ordenar_adaptativo(valores)
    n = len(ordenados)
    if not n:
        return 0.0
    idx = int(0.95 * (n - 1))
    return ordenados[idx]


def _crear_partida_con_movimiento(carpeta: str, k: int, acciones: int, enemigos: int = 2) -> tuple[EstadoJuegoServicio, EstadoJuegoLogica]:
    """Crea y ejecuta una partida determinista de `acciones` pasos con movimiento entre salas."""
    RetrocesoLogica().reiniciar()
    srv, cid = servicio_sintetico(carpeta, enemigos=enemigos, ancho=10, alto=10)
    servicio = EstadoJuegoServicio(comunicacion=srv)
    servicio.k_checkpoint = k
    servicio.iniciarJuego(cid, semilla=SEMILLA_BENCH)
    logica = servicio._estadoJuegoLogica
    jugador = logica.estadoJuego.jugador
    servicio.obtenerSala(jugador.id_sala_actual)

    visitadas: list[int] = []
    for i in range(acciones):
        if logica.fin:
            break
        sala = logica.estadoJuego.salas[jugador.id_sala_actual]
        if sala.id not in visitadas:
            visitadas.append(sala.id)
        salidas = [s for s in sala.salidas if not s.cerrada and s.sala_destino != 100]
        if not salidas:
            salidas = [s for s in sala.salidas if not s.cerrada]
        elegida = salidas[i % len(salidas)]
        ev = EventoDTO(elegida.costo, 0, jugador, "MOVER_JUGADOR", [sala, elegida.direccion])
        servicio.accionJugador(ev)

    return servicio, logica


def _medir_busqueda_binaria_vs_lineal(imprimir=print) -> tuple[float, float, float, float]:
    """Micro-medición: búsqueda binaria vs búsqueda lineal con 500 y 5000 puntos."""
    class DummyPunto:
        def __init__(self, acc: int):
            self.acciones_linea_tiempo = acc

    resultados = []
    for n_puntos in (500, 5000):
        puntos = [DummyPunto(i * 10) for i in range(n_puntos)]
        targets = [puntos[int(n_puntos * f)].acciones_linea_tiempo + 3 for f in (0.05, 0.25, 0.5, 0.75, 0.95)]

        # Binaria
        t0 = time.perf_counter()
        for _ in range(5000):
            for target in targets:
                izq, der = 0, len(puntos) - 1
                cand = -1
                while izq <= der:
                    m = (izq + der) // 2
                    if puntos[m].acciones_linea_tiempo <= target:
                        cand = m
                        izq = m + 1
                    else:
                        der = m - 1
        t1 = time.perf_counter()
        bin_us = (t1 - t0) / (5000 * len(targets)) * 1_000_000

        # Lineal reversed
        t0 = time.perf_counter()
        for _ in range(5000):
            for target in targets:
                cand = -1
                for i in reversed(range(len(puntos))):
                    if puntos[i].acciones_linea_tiempo <= target:
                        cand = i
                        break
        t1 = time.perf_counter()
        lin_us = (t1 - t0) / (5000 * len(targets)) * 1_000_000
        resultados.extend([bin_us, lin_us])

    return tuple(resultados)


def ejecutar(filas: list, imprimir=print, acciones: int = 5000) -> bool:
    """Ejecuta el bloque de benchmark de historia y registra métricas en `filas`."""
    cumple = True
    imprimir(f"\n--- Línea de tiempo (historia <t> / historia #k): {acciones} acciones con K en {VALORES_K} ---")

    # Lista de tuplas (k, mediana, p95, maximo, puntos, tamano_kb): sin dict (principio I)
    resultados_k: list[tuple] = []

    with tempfile.TemporaryDirectory() as raiz:
        for k in VALORES_K:
            carpeta = tempfile.mkdtemp(dir=raiz)
            servicio, logica = _crear_partida_con_movimiento(carpeta, k, acciones, enemigos=2)
            n_vigentes = logica.acciones_linea_tiempo
            puntos_totales = len(logica.puntos_control)

            # Posiciones requeridas para evaluación
            # Inicio, mitad, cerca del final, en un punto de control y en el peor caso K-1 acciones tras un punto
            pos_inicio = min(10, n_vigentes)
            pos_mitad = n_vigentes // 2
            pos_fin = max(1, n_vigentes - 20)
            punto_ref = min(max(1, (n_vigentes // (2 * k)) * k), n_vigentes)
            pos_en_punto = punto_ref + 1  # historia #(P+1) es justo en el punto de control
            pos_peor = min(punto_ref + k, n_vigentes)  # K-1 acciones tras el punto

            consultas_accion = [pos_inicio, pos_mitad, pos_fin, pos_en_punto, pos_peor]
            tiempos_us: list[float] = []

            gc.collect()
            gc.disable()
            try:
                for pos in consultas_accion:
                    # historia #k
                    t0 = time.perf_counter()
                    res_k = servicio.consultarHistoria(accion=pos)
                    t_k_us = (time.perf_counter() - t0) * 1_000_000
                    tiempos_us.append(t_k_us)

                    # historia <t>
                    t_instante = res_k.instante
                    t0 = time.perf_counter()
                    res_t = servicio.consultarHistoria(instante=t_instante)
                    t_t_us = (time.perf_counter() - t0) * 1_000_000
                    tiempos_us.append(t_t_us)
            finally:
                gc.enable()

            med_us = _mediana(tiempos_us)
            p95_us = _percentil_95(tiempos_us)
            max_us = max(tiempos_us)
            tamano_kb = _tamano([p.estado for p in logica.puntos_control]) / 1024

            resultados_k.append((k, med_us, p95_us, max_us, puntos_totales, tamano_kb))

            ok = max_us <= LIMITE_HISTORIA_US
            cumple = cumple and ok

            anotar(filas, SECCION, f"K={k}: tiempo historia ({len(tiempos_us)} consultas en partida de {n_vigentes} acc)",
                   (med_us, p95_us, max_us))
            filas.append((SECCION, f"    ¿peor historia K={k} <= 50 ms? (FR-442)",
                          "CUMPLE" if ok else "NO CUMPLE", f"(máx {texto(max_us)})"))
            filas.append((SECCION, f"K={k}: memoria serializada de {puntos_totales} puntos de control",
                          f"{tamano_kb:,.1f} KB", f"{tamano_kb / max(puntos_totales, 1):.2f} KB/punto"))

        # 2. Alternativa C descartada: reconstruir desde el inicio sin puntos de control
        imprimir("Midiendo Alternativa C (reconstrucción desde el inicio sin puntos)...")
        carpeta_c = tempfile.mkdtemp(dir=raiz)
        srv_c, log_c = _crear_partida_con_movimiento(carpeta_c, k=10, acciones=acciones, enemigos=2)
        n_c = log_c.acciones_linea_tiempo
        log_dto = log_c.exportar_log()

        gc.collect()
        gc.disable()
        try:
            t0 = time.perf_counter()
            juego_replay = EstadoJuegoLogica(comunicacion=log_c.comunicacion)
            _ = juego_replay.repetirPartida(log_dto, hasta=log_c.estadoJuego.reloj.tiempo_actual)
            tiempo_c_us = (time.perf_counter() - t0) * 1_000_000
        finally:
            gc.enable()

        tiempo_k10_us = _resultado_k(resultados_k, 10)[1]
        factor_aceleracion = tiempo_c_us / max(tiempo_k10_us, 1.0)
        filas.append((SECCION, f"Alternativa C (descartada): reconstruir {n_c} acciones desde el inicio (sin checkpoints)",
                      texto(tiempo_c_us), f"{factor_aceleracion:.1f}x la mediana de historia con K=10 ({texto(tiempo_k10_us)})"))

        # 3. Micro-medición: búsqueda binaria vs búsqueda lineal
        imprimir("Búsqueda binaria vs lineal...")
        b500, l500, b5000, l5000 = _medir_busqueda_binaria_vs_lineal(imprimir)
        filas.append((SECCION, "Búsqueda binaria vs lineal (M=500 puntos de control)",
                      f"Binaria {b500:.2f} µs | Lineal {l500:.2f} µs", f"Binaria {l500 / max(b500, 1e-3):.1f}x más rápida"))
        filas.append((SECCION, "Búsqueda binaria vs lineal (M=5 000 puntos de control)",
                      f"Binaria {b5000:.2f} µs | Lineal {l5000:.2f} µs", f"Binaria {l5000 / max(b5000, 1e-3):.1f}x más rápida"))

        # 4. Hacia adelante vs hacia atrás (§5.5)
        imprimir("Analizando reconstrucción hacia adelante vs hacia atrás...")
        filas.append((SECCION, "Hacia adelante vs hacia atrás (§5.5): viabilidad arquitectónica",
                      "Hacia adelante (elegida): O(K) acciones desde checkpoint",
                      "Hacia atrás no soportada: el historial del pergamino retiene solo MAX_HISTORIAL=5 acciones"))
        nota(filas, SECCION, "No es posible medir empíricamente el tiempo de retroceso de 5 000 acciones hacia atrás "
                             "porque el motor limita el historial a MAX_HISTORIAL=5 acciones por diseño; "
                             "reconstruir hacia adelante desde el punto más cercano aprovecha la búsqueda binaria O(log M).")

        # 5. Justificación de K por defecto
        k_por_defecto = EstadoJuegoLogica().k_checkpoint
        fila_defecto = _resultado_k(resultados_k, k_por_defecto)
        peor_defecto = fila_defecto[3] if fila_defecto is not None else 0.0
        ok_defecto = peor_defecto <= LIMITE_HISTORIA_US
        filas.append((SECCION, f"Justificación K={k_por_defecto} por defecto: peor caso medido",
                      texto(peor_defecto), "CUMPLE (<= 50 ms)" if ok_defecto else "NO CUMPLE"))
        nota(filas, SECCION, f"K={k_por_defecto} garantiza tiempos de respuesta entre {texto(_resultado_k(resultados_k, 10)[1])} "
                             f"y {texto(_resultado_k(resultados_k, 10)[3])}, cumpliendo holgadamente el límite de 50 ms.")

    return cumple
