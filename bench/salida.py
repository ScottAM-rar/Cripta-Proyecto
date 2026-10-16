"""Presentación de los resultados del bench: tabla en pantalla y, si se pide, un CSV para el documento."""
from __future__ import annotations

import csv


def imprimir_tabla(filas: list, imprimir=print) -> None:
    seccion = None
    for fila in filas:
        if fila[0] != seccion:
            seccion = fila[0]
            imprimir(f"\n{seccion}")
        valor = f"{fila[2]}" + (f"  {fila[3]}" if fila[3] else "")
        imprimir(f"  {fila[1]:<66} {valor}")


def escribir_csv(filas: list, ruta: str) -> None:
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["seccion", "medicion", "resultado", "unidad"])
        for fila in filas:
            escritor.writerow(fila)
