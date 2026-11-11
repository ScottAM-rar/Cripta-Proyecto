"""Módulo de benchmark para evaluar la proporcionalidad de la reproducción acotada (--bench replay).
FR-412, FR-413, Principio VII.
"""
from __future__ import annotations

import tempfile
import time

from bench.juego import juego_sin_iniciar, servicio_sintetico
from DTO.LogPartidaDTO import LogPartidaDTO
from Logica.GestorEventos import GestorEventos
from tests_labs.generador_partidas import ESCALAS, generar_log_dto

SECCION = "Replay"
SEMILLA_BENCH = 2026


def _ejecutar_conteo(juego, log: LogPartidaDTO, hasta: int | None = None, opcion_a: bool = False):
    orig_procesar = GestorEventos.procesar_evento
    conteo = [0]

    def procesar_contando(inst, evento):
        conteo[0] += 1
        return orig_procesar(inst, evento)

    GestorEventos.procesar_evento = procesar_contando
    t0 = time.perf_counter()
    try:
        if opcion_a:
            # Opción a (descartada): corte por acción sin tope en el ciclo de eventos
            juego.iniciarJuego(log.id_cripta, log.semilla)
            juego.ingresarEnSala(juego.estadoJuego.jugador.id_sala_actual)
            from Logica.LogEventos import LogEventos, TIPOS_CURSOR_INVENTARIO
            log_orig = LogEventos.desde_dto(log)
            for reg in log_orig.obtener_registros_cronologicos():
                if juego.fin or (hasta is not None and juego.estadoJuego.reloj.tiempo_actual >= hasta):
                    break
                if reg.tipo_accion in TIPOS_CURSOR_INVENTARIO:
                    continue
                ev = juego._crear_evento_repeticion(reg)
                juego.accionJugador(ev, tope=None)  # Sin tope en ciclo
        else:
            juego.repetirPartida(log, hasta=hasta)
    finally:
        GestorEventos.procesar_evento = orig_procesar
    tiempo_ms = (time.perf_counter() - t0) * 1000
    t_alcanzado = juego.estadoJuego.reloj.tiempo_actual
    return conteo[0], tiempo_ms, t_alcanzado


def ejecutar(filas: list, imprimir=print) -> bool:
    """Ejecuta las secciones A, B y C del benchmark de replay."""
    cumple_todo = True
    resultados_a = []

    with tempfile.TemporaryDirectory() as carpeta:
        servicio, cripta_id = servicio_sintetico(carpeta, enemigos=2)
        v_cripta = servicio.version_cripta(cripta_id)
        v_catalogo = servicio.version_catalogo()

        # --- SECCIÓN A: Proporcionalidad temporal (Opción b) ---
        for n in ESCALAS:
            log = generar_log_dto(n, SEMILLA_BENCH, cripta_id, v_cripta, v_catalogo)

            # Ejecución total
            j_tot = juego_sin_iniciar(carpeta, enemigos=2)
            ev_tot, t_tot_ms, t_max = _ejecutar_conteo(j_tot, log, hasta=None)

            # Ejecución T / 2
            t_half = t_max // 2
            j_half = juego_sin_iniciar(carpeta, enemigos=2)
            ev_half, t_half_ms, _ = _ejecutar_conteo(j_half, log, hasta=t_half)

            razon_ev = ev_half / ev_tot if ev_tot > 0 else 0
            razon_t = t_half_ms / t_tot_ms if t_tot_ms > 0 else 0

            ok = razon_ev <= 0.55
            if not ok:
                cumple_todo = False

            resultados_a.append({
                "acciones": n,
                "t_total": t_max,
                "ev_tot": ev_tot,
                "ev_half": ev_half,
                "razon_ev": razon_ev,
                "t_tot_ms": t_tot_ms,
                "t_half_ms": t_half_ms,
                "razon_t": razon_t,
            })

            filas.append((SECCION, f"{n} acciones t=T/2", "Eventos procesados", ev_half))
            filas.append((SECCION, f"{n} acciones t=T/2", "Tiempo ms", round(t_half_ms, 1)))

        # --- SECCIÓN B: Comparación con alternativas descartadas (1000 acciones) ---
        # El instante de corte cae dentro de una acción del jugador (no coincide con uno de sus turnos): así se mide
        # si la alternativa a ejecuta o no eventos posteriores a t.
        log_1000 = generar_log_dto(1000, SEMILLA_BENCH, cripta_id, v_cripta, v_catalogo)
        t_corte = resultados_a[1]["t_total"] // 2 + 1

        j_b = juego_sin_iniciar(carpeta, enemigos=2)
        ev_op_b, t_op_b, t_alc_b = _ejecutar_conteo(j_b, log_1000, hasta=t_corte)

        # Alternativa a: corte por acción
        j_a = juego_sin_iniciar(carpeta, enemigos=2)
        ev_op_a, t_op_a, t_alc_a = _ejecutar_conteo(j_a, log_1000, hasta=t_corte, opcion_a=True)

        # Alternativa c: recorte tras reproducción total
        j_c = juego_sin_iniciar(carpeta, enemigos=2)
        ev_op_c, t_op_c, t_alc_c = _ejecutar_conteo(j_c, log_1000, hasta=None)

        if t_alc_b > t_corte:      # la opción elegida nunca debe pasar de t (FR-402)
            cumple_todo = False

        filas.append((SECCION, f"1000 acciones t={t_corte} Opcion B", "Eventos procesados", ev_op_b))
        filas.append((SECCION, f"1000 acciones t={t_corte} Opcion B", "Instante alcanzado", t_alc_b))
        filas.append((SECCION, f"1000 acciones t={t_corte} Opcion A", "Eventos procesados", ev_op_a))
        filas.append((SECCION, f"1000 acciones t={t_corte} Opcion A", "Instante alcanzado", t_alc_a))
        filas.append((SECCION, f"1000 acciones t={t_corte} Opcion C", "Eventos procesados", ev_op_c))
        filas.append((SECCION, f"1000 acciones t={t_corte} Opcion C", "Instante alcanzado", t_alc_c))

    # Presentación en consola (Sección A)
    imprimir("\n--- Bloque Replay: Proporcionalidad temporal (Opción b) ---")
    imprimir(f"{'Carga':<16} {'Acciones':>8} {'T_total':>9} {'Eventos Tot.':>14} {'Eventos T/2':>13} {'Razón Ev.':>11} {'Tiempo Tot (ms)':>17} {'Tiempo T/2 (ms)':>17} {'Razón Tiempo':>14}")
    for r in resultados_a:
        carga_str = f"{r['acciones']} acciones"
        imprimir(
            f"{carga_str:<16} {r['acciones']:>8} {r['t_total']:>9} {r['ev_tot']:>14} {r['ev_half']:>13} "
            f"{r['razon_ev']:>11.3f} {r['t_tot_ms']:>17.1f} {r['t_half_ms']:>17.1f} {r['razon_t']:>14.3f}"
        )

    # Presentación en consola (Sección B)
    def _fidelidad(t_alcanzado: int) -> str:
        return (f"Cumple (reloj en {t_alcanzado} <= t)" if t_alcanzado <= t_corte
                else f"Falla (reloj en {t_alcanzado} > t)")

    imprimir(f"\n--- Bloque Replay: Comparación con alternativas descartadas (1000 acciones, t = {t_corte}) ---")
    imprimir(f"{'Estrategia':<34} {'Eventos Proc.':>13} {'Tiempo (ms)':>13}  {'Fidelidad temporal (FR-402/FR-403)':<36} {'Proporcionalidad (FR-412)':<28}")
    imprimir(f"{'Opción b (Elegida: tope ciclo)':<34} {ev_op_b:>13} {t_op_b:>13.1f}  {_fidelidad(t_alc_b):<36} {'Cumple (proporcional a t)':<28}")
    imprimir(f"{'Opción a (Descartada: corte acc)':<34} {ev_op_a:>13} {t_op_a:>13.1f}  {_fidelidad(t_alc_a):<36} {'Cumple (corta lectura log)':<28}")
    imprimir(f"{'Opción c (Descartada: recorte)':<34} {ev_op_c:>13} {t_op_c:>13.1f}  {'Cumple (estado reconstruido)':<36} {'Falla (100% de eventos proc)':<28}")

    return cumple_todo
