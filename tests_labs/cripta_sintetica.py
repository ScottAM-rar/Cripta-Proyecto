"""Criptas sintéticas deterministas por semilla, para pruebas y para --bench.

Ningún id ni tamaño está fijo: todo se deriva de los parámetros. El esqueleto sale en el mismo formato que la API
(ids desde 1; cada salida admite "costo" y "cerrada"). Los costos son simétricos salvo que se pida lo contrario.
"""
from __future__ import annotations

import random

LETRAS = ("N", "S", "E", "O")


def ficha_cazador(id_ficha: str = "ent_cazador", rango: int | None = 600, velocidad: int = 100,
                  vida_max: int = 20, ataque: int = 3, defensa: int = 0) -> dict:
    """Ficha de catálogo de un cazador. `rango` None la deja sin el campo (para probar el valor por defecto)."""
    ficha = {"id": id_ficha, "clase": "enemigo", "nombre": "Cazador", "vida_max": vida_max, "ataque": ataque,
             "defensa": defensa, "velocidad": velocidad, "comportamiento": "cazador", "suelta": []}
    if rango is not None:
        ficha["rango"] = rango
    return ficha


def esqueleto_rejilla(ancho: int, alto: int, semilla: int = 0, costo_max: int = 0,
                      fraccion_cerradas: float = 0.0) -> list[dict]:
    """Rejilla ancho x alto, ids 1..ancho*alto en orden de filas.

    costo_max == 0: ninguna salida declara costo (vale 100). costo_max > 0: cada conexión declara un costo entero
    entre 1 y costo_max, el mismo en ambos sentidos. fraccion_cerradas: proporción de conexiones que arrancan
    cerradas (en los dos sentidos).
    """
    azar = random.Random(semilla)
    total = ancho * alto
    salas = []
    for numero in range(1, total + 1):
        salas.append({"id": numero, "nombre": f"Sala {numero}", "salidas": {}})
    for fila in range(alto):
        for columna in range(ancho):
            numero = fila * ancho + columna + 1
            if columna < ancho - 1:
                _conectar(salas, numero, numero + 1, "E", "O", azar, costo_max, fraccion_cerradas)
            if fila < alto - 1:
                _conectar(salas, numero, numero + ancho, "S", "N", azar, costo_max, fraccion_cerradas)
    return salas


def _conectar(salas, a, b, letra_ab, letra_ba, azar, costo_max, fraccion_cerradas) -> None:
    costo = azar.randint(1, costo_max) if costo_max > 0 else None
    cerrada = azar.random() < fraccion_cerradas
    for origen, destino, letra in ((a, b, letra_ab), (b, a, letra_ba)):
        salida = {"sala": destino}
        if costo is not None:
            salida["costo"] = costo
        if cerrada:
            salida["cerrada"] = True
        salas[origen - 1]["salidas"][letra] = salida


def esqueleto_lineal(costos: list[int | None]) -> list[dict]:
    """Cadena 1 - 2 - ... - n+1; costos[i] es el costo de la conexión entre la sala i+1 y la i+2 (None = sin declarar)."""
    salas = [{"id": i, "nombre": f"Sala {i}", "salidas": {}} for i in range(1, len(costos) + 2)]
    for i, costo in enumerate(costos):
        for origen, destino, letra in ((i + 1, i + 2, "E"), (i + 2, i + 1, "O")):
            salida = {"sala": destino}
            if costo is not None:
                salida["costo"] = costo
            salas[origen - 1]["salidas"][letra] = salida
    return salas


def ficha_enemigo(id_ficha: str, comportamiento: str, velocidad: int = 100, vida_max: int = 1000, ataque: int = 1,
                  defensa: int = 0) -> dict:
    """Ficha de catálogo de un enemigo cualquiera (errante, rastreador, guardián...)."""
    return {"id": id_ficha, "clase": "enemigo", "nombre": id_ficha, "vida_max": vida_max, "ataque": ataque,
            "defensa": defensa, "velocidad": velocidad, "comportamiento": comportamiento, "suelta": []}


def esqueleto_de_conexiones(conexiones: list[tuple], total: int | None = None) -> list[dict]:
    """Esqueleto armado a mano. Cada conexión es (a, b, costo, letra_ab, letra_ba) con opciones por nombre al final:
    `cerrada=True` (cerrada en los dos sentidos), `un_sentido=True` (solo existe la salida a -> b). Un costo None no
    se declara. Las salas son 1..total (por defecto, el mayor id usado)."""
    if total is None:
        total = 0
        for c in conexiones:
            total = max(total, c[0], c[1])
    salas = [{"id": i, "nombre": f"Sala {i}", "salidas": {}} for i in range(1, total + 1)]
    for conexion in conexiones:
        a, b, costo, letra_ab, letra_ba = conexion[:5]
        opciones = conexion[5] if len(conexion) > 5 else {}
        lados = [(a, b, letra_ab)] if opciones.get("un_sentido") else [(a, b, letra_ab), (b, a, letra_ba)]
        for origen, destino, letra in lados:
            salida = {"sala": destino}
            if costo is not None:
                salida["costo"] = costo
            if opciones.get("cerrada"):
                salida["cerrada"] = True
            salas[origen - 1]["salidas"][letra] = salida
    return salas
