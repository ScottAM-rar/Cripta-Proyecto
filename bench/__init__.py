"""Modo --bench (§5.3): cargas sintéticas que miden cada subsistema y su alternativa descartada.

    py main.py --bench                    todos los bloques
    py main.py --bench agenda,guardado    solo algunos
    py main.py --bench --bench-csv r.csv  además, guarda los resultados en un CSV

No usa la red ni la vista interactiva. Los archivos temporales van a una carpeta que se borra al terminar.
"""
from __future__ import annotations

import platform
import sys
import tempfile
from datetime import datetime

from bench import agenda, bitacora, ciclo, guardado, historia, inventario, mapa, ordenamiento, puntos_control, recorrido, replay, retroceso, salas, terreno
from bench import llaves
from bench import resolubilidad
from bench.datos import SEMILLA
from bench.salida import escribir_csv, imprimir_tabla


def _red(filas: list) -> None:
    from adaptadores import bench_red_mejorado as bench_red
    bench_red_filas = []
    with tempfile.TemporaryDirectory() as raiz:
        bench_red.solicitudes_por_estrategia(bench_red_filas, raiz)
        bench_red.busqueda_en_cache(bench_red_filas)
        bench_red.ficha_liberada(bench_red_filas, raiz)
        bench_red.guardado_en_lote(bench_red_filas, raiz)
        bench_red.planear_vecindad(bench_red_filas, raiz)
        bench_red.cache_en_partida(bench_red_filas, raiz)
    for fila in bench_red_filas:
        filas.append(("Red, caché y disco (§4.2–§4.4, §5.1): " + str(fila[0]), fila[1], fila[2], fila[3]))


BLOQUES = (
    ("agenda", agenda.ejecutar),
    ("cache", _red),
    ("salas", salas.ejecutar),
    ("inventario", inventario.ejecutar),
    ("retroceso", retroceso.ejecutar),
    ("ordenamiento", ordenamiento.ejecutar),
    ("guardado", guardado.ejecutar),
    ("bitacora", bitacora.ejecutar),
    ("ciclo", ciclo.ejecutar),
    ("terreno", terreno.ejecutar),
    ("recorrido", recorrido.ejecutar),
    ("mapa", mapa.ejecutar),
    ("replay", replay.ejecutar),
    ("puntos_control", puntos_control.ejecutar),
    ("llaves", llaves.ejecutar),
    ("historia", historia.ejecutar),
    ("resolubilidad", resolubilidad.ejecutar),
)


def nombres_de_bloques() -> list[str]:
    return [nombre for nombre, _ in BLOQUES]


def ejecutar(nombres: list[str] | None = None, ruta_csv: str | None = None, imprimir=print) -> int:
    """Corre los bloques pedidos (todos si `nombres` es None). Devuelve 0, o 1 si un bloque pedido no existe
    o si el ciclo de eventos supera los 20 ms."""
    pedidos = nombres if nombres else nombres_de_bloques()
    for nombre in pedidos:
        if nombre not in nombres_de_bloques():
            imprimir(f"Bloque desconocido: {nombre!r}. Bloques disponibles: {', '.join(nombres_de_bloques())}")
            return 1
    imprimir(f"CRIPTA --bench · Python {sys.version.split()[0]} · {platform.system()} {platform.machine()} · "
             f"{datetime.now():%Y-%m-%d %H:%M} · semilla {SEMILLA}")
    filas: list = []
    cumple = True
    cumple_recorrido = True
    cumple_mapa = True
    cumple_llaves = True
    cumple_resolubilidad = True
    for nombre, funcion in BLOQUES:
        if nombre not in pedidos:
            continue
        imprimir(f"... midiendo {nombre}")
        resultado = funcion(filas)
        if nombre in ("ciclo", "terreno", "replay", "puntos_control") and resultado is False:
            cumple = False
        if nombre == "recorrido" and resultado is False:
            cumple_recorrido = False
        if nombre == "mapa" and resultado is False:
            cumple_mapa = False
        if nombre == "llaves" and resultado is False:
            cumple_llaves = False
        if nombre == "resolubilidad" and resultado is False:
            cumple_resolubilidad = False
    imprimir_tabla(filas, imprimir)
    if ruta_csv:
        escribir_csv(filas, ruta_csv)
        imprimir(f"\nResultados guardados en {ruta_csv}")
    if "ciclo" in pedidos or "terreno" in pedidos:
        imprimir("\n§5.2: " + ("el ciclo de eventos CUMPLE el límite de 20 ms." if cumple else "el ciclo de eventos NO cumple el límite de 20 ms."))
    if "replay" in pedidos:
        imprimir("\n§3.6 Replay acotado (SC-003, proporcionalidad temporal por conteo de eventos): "
                 + ("CUMPLE." if cumple else "NO CUMPLE."))
    if "puntos_control" in pedidos:
        imprimir("\n§3.6 Puntos de control (FR-426, límite de 20 ms en captura y ciclo): "
                 + ("CUMPLE." if cumple else "NO CUMPLE."))
    if "recorrido" in pedidos:
        imprimir("\nRecorrido por niveles (SC-004, equivalencia y verificaciones previas): "
                 + ("CUMPLE." if cumple_recorrido else "NO CUMPLE; la razón de tiempos solo informa, no decide."))
    if "mapa" in pedidos:
        imprimir("\nMapa conocido (criterios duros por conteo y equivalencia con la referencia): "
                 + ("CUMPLE." if cumple_mapa else "NO CUMPLE; la razón de tiempos solo informa, no decide."))
    if "llaves" in pedidos:
        imprimir("\nLlaves (SC-001, SC-002): "
                 + ("CUMPLE." if cumple_llaves else "NO CUMPLE: 1/0/0 en D, la verificación de B o C, o guardar con "
                    "A y 5 000 salas supera los 50 ms."))
    if "resolubilidad" in pedidos:
        imprimir("\nResolubilidad (FR-345, FR-346): "
                 + ("CUMPLE." if cumple_resolubilidad else "NO CUMPLE: los resultados de A difieren, C supera 200 ms o "
                    "la razón de D del incremental supera 20."))
    return 0 if cumple and cumple_recorrido and cumple_mapa and cumple_llaves and cumple_resolubilidad else 1
