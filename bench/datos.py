"""Generadores de datos sintéticos con semilla fija: dos corridas de --bench miden exactamente lo mismo."""
from __future__ import annotations

import io
import random

SEMILLA = 2026


def azar(desplazamiento: int = 0) -> random.Random:
    return random.Random(SEMILLA + desplazamiento)


def numeros(n: int, tipo: str, rng: random.Random) -> list[int]:
    """tipo: 'aleatorio', 'casi_ordenado' (1 de cada 20 fuera de lugar) o 'inverso'."""
    if tipo == "aleatorio":
        lista = list(range(n))
        rng.shuffle(lista)
        return lista
    if tipo == "inverso":
        return list(range(n, 0, -1))
    if tipo == "casi_ordenado":
        lista = list(range(n))
        for _ in range(max(1, n // 20)):
            i, j = rng.randrange(n), rng.randrange(n)
            lista[i], lista[j] = lista[j], lista[i]
        return lista
    raise ValueError(f"Tipo de datos desconocido: {tipo}")


class Mudo(io.TextIOBase):
    """Sustituto de la salida estándar: el modelo imprime mensajes, y eso es renderizado, no procesamiento (§5.2)."""

    def write(self, texto):
        return len(texto)


def salida_muda():
    return Mudo()
