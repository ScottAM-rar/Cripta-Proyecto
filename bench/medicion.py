"""Medidor común del modo --bench: todos los bloques cronometran igual.

Cada medición descarta una pasada de calentamiento, repite varias veces y reporta la MEDIANA (más el mínimo y el
máximo): un pico del sistema no la ensucia como lo haría un promedio. Los datos se preparan fuera del cronómetro.
"""
from __future__ import annotations

import time

from Logica.ordenamiento import insertion_sort

UNIDAD = "µs"


def medir(operacion, preparar=None, repeticiones: int = 7, calentar: int = 1) -> tuple[float, float, float]:
    """Microsegundos que tarda `operacion`: (mediana, mínimo, máximo).

    Con `preparar`, antes de cada repetición se arma un estado nuevo (sin cronometrar) y se le pasa a la operación."""
    tiempos: list[float] = []
    for i in range(calentar + repeticiones):
        entrada = preparar() if preparar is not None else None
        inicio = time.perf_counter()
        if preparar is not None:
            operacion(entrada)
        else:
            operacion()
        fin = time.perf_counter()
        if i >= calentar:
            tiempos.append((fin - inicio) * 1_000_000)
    insertion_sort(tiempos)                      # pocas muestras: se usa el ordenamiento propio del proyecto
    return tiempos[len(tiempos) // 2], tiempos[0], tiempos[-1]


def texto(microsegundos: float) -> str:
    if microsegundos >= 1000:
        return f"{microsegundos / 1000:,.2f} ms"
    return f"{microsegundos:,.1f} µs"


def anotar(filas: list, seccion: str, nombre: str, resultado: tuple[float, float, float]) -> float:
    """Agrega una fila 'mediana (mín – máx)' y devuelve la mediana en µs."""
    mediana, minimo, maximo = resultado
    filas.append((seccion, nombre, f"{texto(mediana)}  ({texto(minimo)} – {texto(maximo)})", "mediana (mín – máx)"))
    return mediana


def verificar(filas: list, seccion: str, nombre: str, condicion: bool) -> bool:
    """Una comprobación previa a medir: si las dos estructuras no hacen lo mismo, el tiempo no vale nada."""
    filas.append((seccion, f"verificación: {nombre}", "OK" if condicion else "FALLA", ""))
    return bool(condicion)


def nota(filas: list, seccion: str, texto_nota: str) -> None:
    filas.append((seccion, texto_nota, "", ""))
