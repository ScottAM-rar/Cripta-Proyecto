"""§3.6 Puntos de control de la partida (FR-426, SC-004, Principio VII).

Todo lo que se informa se mide jugando partidas sintéticas deterministas por semilla (50 esbirros, rejilla 5x5):
- ciclo de eventos en las acciones que toman un punto de control frente a las que no, con K = 1, 10, 50 y 100;
- tamaño serializado de los puntos de control (Alternativa B, la elegida: el punto guarda solo las longitudes de los
  historiales) frente a la Alternativa A (descartada: cada punto copia la bitácora y el log completos);
- costo de llegar a la acción k desde el punto de control más cercano frente a la Alternativa C (descartada: sin
  puntos de control, reproducir desde el inicio), comprobando que ambos caminos llegan al mismo estado;
- el K por defecto se deriva de esas mediciones: el mayor K probado cuyo peor caso de reconstrucción cabe en los
  50 ms que el enunciado fija para `historia` (§6).
"""
from __future__ import annotations

import gc
import pickle
import tempfile
import time

from DTO.EventoDTO import EventoDTO
from Logica import EstadoGuardadoLogica
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from bench.juego import servicio_sintetico
from bench.medicion import anotar, medir, nota, texto, verificar

SECCION = "Puntos de control (§3.6, FR-426): límite 20 ms y comparativa"
VALORES_K = (1, 10, 50, 100)
K_CON_ALTERNATIVA_A = 10
LIMITE_CICLO_US = 20_000        # ciclo de eventos entre dos decisiones (§6)
LIMITE_HISTORIA_US = 50_000     # historia con 5 000 acciones (§6): tope para reconstruir un estado
ACCIONES = 1_000
SEMILLA_BENCH = 2026
REPETICIONES_RECONSTRUCCION = 3


def _esperar(juego: EstadoJuegoLogica) -> None:
    jugador = juego.estadoJuego.jugador
    juego.accionJugador(EventoDTO(100, 0, jugador, "ESPERAR", []))


def _huella(juego: EstadoJuegoLogica) -> tuple:
    jugador = juego.estadoJuego.jugador
    return (juego.estadoJuego.reloj.tiempo_actual, juego.acciones_linea_tiempo, juego.accionesJugador,
            jugador.id_sala_actual, getattr(jugador, "vida_actual", None), juego.gestorEventos.azar.getstate())


def _tamano(objeto) -> int:
    return len(pickle.dumps(objeto, protocol=pickle.HIGHEST_PROTOCOL))


def _jugar(carpeta: str, k: int, acciones: int, objetivo: int, con_alternativa_a: bool = False) -> dict:
    """Juega `acciones` esperas con intervalo K. Anota el tiempo de cada acción (y si tomó un punto), la huella del
    estado tras `objetivo` acciones y, si se pide, lo que ocuparía la Alternativa A."""
    servicio, cripta = servicio_sintetico(carpeta, enemigos=50, ancho=5, alto=5)
    juego = EstadoJuegoLogica(semilla=SEMILLA_BENCH, comunicacion=servicio)
    juego.k_checkpoint = k
    juego.iniciarJuego(cripta, semilla=SEMILLA_BENCH)
    juego.ingresarEnSala(juego.estadoJuego.jugador.id_sala_actual)
    con_punto, sin_punto, tiempos = [], [], []
    completos = []
    huella = None
    gc.collect()
    gc.disable()               # una pausa del recolector no es costo del punto de control (también aparece sin punto)
    try:
        for i in range(acciones):
            antes = len(juego.puntos_control)
            inicio = time.perf_counter()
            _esperar(juego)
            micros = (time.perf_counter() - inicio) * 1_000_000
            tiempos.append(micros)
            if i > 0:                              # la primera acción incluye el punto 0 y el calentamiento
                (con_punto if len(juego.puntos_control) > antes else sin_punto).append(micros)
            if juego.acciones_linea_tiempo == objetivo:
                huella = _huella(juego)
            if con_alternativa_a and len(juego.puntos_control) > antes:
                completos.append(EstadoGuardadoLogica.exportar(juego))
    finally:
        gc.enable()
    return {"juego": juego, "con_punto": con_punto, "sin_punto": sin_punto, "tiempos": tiempos, "huella": huella,
            "completos": completos}


def _mediana(valores: list) -> float:
    ordenados = list(valores)
    for i in range(1, len(ordenados)):             # inserción: pocas muestras, estructura propia del proyecto
        actual = ordenados[i]
        j = i - 1
        while j >= 0 and ordenados[j] > actual:
            ordenados[j + 1] = ordenados[j]
            j -= 1
        ordenados[j + 1] = actual
    return ordenados[len(ordenados) // 2] if ordenados else 0.0


def _reconstruir(juego: EstadoJuegoLogica, punto, objetivo: int, huella: tuple) -> tuple[float, bool]:
    """Restaura desde `punto` y reaplica las acciones que faltan hasta `objetivo`. Devuelve (µs, mismo estado)."""
    tiempos, igual = [], True
    for _ in range(REPETICIONES_RECONSTRUCCION):
        inicio = time.perf_counter()
        juego.restaurarDesdePuntoControl(punto)
        while juego.acciones_linea_tiempo < objetivo:
            _esperar(juego)
        tiempos.append((time.perf_counter() - inicio) * 1_000_000)
        igual = igual and _huella(juego) == huella
    return _mediana(tiempos), igual


def ejecutar(filas: list, imprimir=print, acciones: int = ACCIONES) -> bool:
    """Mide el bloque puntos_control y agrega los resultados a `filas`. Devuelve False si algo no cumple."""
    cumple = True
    resumen = []            # (k, peor reconstrucción en µs)
    imprimir(f"\n--- Puntos de control: partidas de {acciones} acciones con K en {VALORES_K} ---")
    with tempfile.TemporaryDirectory() as raiz:
        for k in VALORES_K:
            punto_base = ((acciones - k) // k) * k
            objetivo = punto_base + k - 1                      # el peor caso: K-1 acciones después de un punto
            carpeta = tempfile.mkdtemp(dir=raiz)
            corrida = _jugar(carpeta, k, acciones, objetivo, con_alternativa_a=(k == K_CON_ALTERNATIVA_A))
            juego = corrida["juego"]
            tomados = len(juego.puntos_control)

            if k == 1:
                peor = max(corrida["con_punto"])
                ok = peor < LIMITE_CICLO_US
                cumple = cumple and ok
                anotar(filas, SECCION, f"K=1: ciclo de eventos EN acciones con punto de control ({len(corrida['con_punto'])})",
                       (_mediana(corrida["con_punto"]), min(corrida["con_punto"]), peor))
                filas.append((SECCION, "    ¿peor ciclo con punto de control < 20 ms? (FR-426)",
                              "CUMPLE" if ok else "NO CUMPLE", f"(máx {texto(peor)})"))
            else:
                anotar(filas, SECCION, f"K={k}: ciclo de eventos EN acciones con punto de control ({len(corrida['con_punto'])})",
                       (_mediana(corrida["con_punto"]), min(corrida["con_punto"]), max(corrida["con_punto"])))
                anotar(filas, SECCION, f"K={k}: ciclo de eventos SIN punto de control ({len(corrida['sin_punto'])})",
                       (_mediana(corrida["sin_punto"]), min(corrida["sin_punto"]), max(corrida["sin_punto"])))
                cumple = cumple and max(corrida["con_punto"]) < LIMITE_CICLO_US

            punto = juego.obtenerPuntoControlReciente(objetivo)
            tamano_b = _tamano([p.estado for p in juego.puntos_control])
            desde_inicio = sum(corrida["tiempos"][:objetivo])                 # Alternativa C, medida
            desde_punto, igual = _reconstruir(juego, punto, objetivo, corrida["huella"])
            cumple = cumple and verificar(filas, SECCION, f"K={k}: restaurar el punto {punto.acciones_linea_tiempo} y "
                                          f"reaplicar {objetivo - punto.acciones_linea_tiempo} acciones llega al mismo "
                                          f"estado que jugar desde el inicio", igual)
            filas.append((SECCION, f"K={k}: {tomados} puntos tras {acciones} acciones; llegar a la acción {objetivo}",
                          f"desde el punto {texto(desde_punto)}; desde el inicio {texto(desde_inicio)}",
                          f"tamaño serializado de los puntos: {tamano_b / 1024:,.0f} KB"))
            resumen.append((k, desde_punto))

            if corrida["completos"]:
                tamano_a = _tamano(corrida["completos"])
                imprimir("Alternativa B (elegida: el punto guarda solo las longitudes de los historiales)")
                imprimir("Alternativa A (descartada: cada punto copia la bitácora y el log completos)")
                imprimir("Alternativa C (descartada: sin puntos de control, reproducir desde el inicio)")
                filas.append((SECCION, f"Alternativa B (elegida), K={k}: tamaño de los puntos tras {acciones} acciones",
                              f"{tamano_b / 1024:,.0f} KB", "medido (serialización)"))
                filas.append((SECCION, f"Alternativa A (descartada), K={k}: tamaño de los puntos tras {acciones} acciones",
                              f"{tamano_a / 1024:,.0f} KB", f"{tamano_a / max(tamano_b, 1):.1f} veces la B, medido"))
                filas.append((SECCION, f"Alternativa C (descartada), K={k}: llegar a la acción {objetivo} desde el inicio",
                              texto(desde_inicio), f"{desde_inicio / max(desde_punto, 1):.1f} veces el camino con puntos, medido"))
                cumple = cumple and tamano_a > tamano_b
                mitad = len(corrida["completos"]) // 2
                if mitad > 0:
                    tamano_a_mitad = _tamano(corrida["completos"][:mitad])
                    tamano_b_mitad = _tamano([p.estado for p in juego.puntos_control[:mitad]])
                    filas.append((SECCION, f"Alternativa A frente a B con la mitad de la partida ({acciones // 2} acciones)",
                                  f"{tamano_a_mitad / max(tamano_b_mitad, 1):.1f} veces la B",
                                  "la razón crece con la partida (A copia historiales cada vez más largos)"))

    por_defecto = EstadoJuegoLogica().k_checkpoint
    elegido = None
    for k, peor_us in resumen:
        if peor_us <= LIMITE_HISTORIA_US:
            elegido = k
    peor_defecto = None
    for k, peor_us in resumen:
        if k == por_defecto:
            peor_defecto = peor_us
    if elegido is None:
        nota(filas, SECCION, "Ningún K probado reconstruye un estado en 50 ms")
        cumple = False
    else:
        nota(filas, SECCION, f"K por defecto derivado: el mayor K probado cuyo peor caso de reconstrucción cabe en 50 ms "
                             f"(historia, §6) es {elegido}")
        if peor_defecto is not None:
            ok = peor_defecto <= LIMITE_HISTORIA_US
            cumple = cumple and ok
            filas.append((SECCION, f"    K por defecto del programa = {por_defecto}: peor reconstrucción", texto(peor_defecto),
                          "CUMPLE (≤ 50 ms)" if ok else "NO CUMPLE (> 50 ms)"))
    return cumple
