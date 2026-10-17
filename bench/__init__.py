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

from bench import agenda, bitacora, ciclo, guardado, inventario, ordenamiento, retroceso, salas
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
    for nombre, funcion in BLOQUES:
        if nombre not in pedidos:
            continue
        imprimir(f"... midiendo {nombre}")
        resultado = funcion(filas)
        if nombre == "ciclo" and resultado is False:
            cumple = False
    imprimir_tabla(filas, imprimir)
    if ruta_csv:
        escribir_csv(filas, ruta_csv)
        imprimir(f"\nResultados guardados en {ruta_csv}")
    if "ciclo" in pedidos:
        imprimir("\n§5.2: " + ("el ciclo de eventos CUMPLE el límite de 20 ms." if cumple else "el ciclo de eventos NO cumple el límite de 20 ms."))
    return 0 if cumple else 1
