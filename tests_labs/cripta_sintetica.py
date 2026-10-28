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


# ---------------------------------------------------------------- recorrido por niveles (capacidad 005)

_OPUESTA = {"N": "S", "S": "N", "E": "O", "O": "E"}


def esqueleto_arbol(ramificacion: int, niveles: int) -> list[dict]:
    """Árbol completo: la raíz (sala 1) tiene `ramificacion` hijos y cada hijo también; ids desde 1 en orden de niveles.
    Cada sala usa una letra para su padre y las demás para sus hijos, así que la ramificación máxima es 3.
    `esqueleto_arbol(3, 9)` tiene 29 524 salas (el último nivel, 19 683): la forma de cripta de frontera más ancha."""
    if not 1 <= ramificacion <= 3:
        raise ValueError("La ramificación debe estar entre 1 y 3 (cada sala tiene a lo sumo 4 salidas)")
    total = 0
    ancho = 1
    for _ in range(niveles + 1):
        total += ancho
        ancho *= ramificacion
    salas = [{"id": i, "nombre": f"Sala {i}", "salidas": {}} for i in range(1, total + 1)]
    letra_al_padre = [None] * (total + 1)
    for padre in range(1, total + 1):
        libres = [l for l in LETRAS if l != letra_al_padre[padre]]
        for j in range(ramificacion):
            hijo = (padre - 1) * ramificacion + 2 + j
            if hijo > total:
                break
            letra = libres[j]
            salas[padre - 1]["salidas"][letra] = {"sala": hijo}
            letra_al_padre[hijo] = _OPUESTA[letra]
            salas[hijo - 1]["salidas"][_OPUESTA[letra]] = {"sala": padre}
    return salas


def esqueleto_dirigido_aleatorio(total: int, semilla: int, fraccion_un_sentido: float = 0.2,
                                 fraccion_inexistentes: float = 0.0) -> list[dict]:
    """Cripta al azar, determinista por semilla, pensada para estresar el recorrido: ciclos, caminos paralelos, dos
    salidas distintas hacia la misma sala, salidas de una sala a sí misma, conexiones de un solo sentido y, según
    `fraccion_inexistentes`, salidas hacia ids que no existen (fuera de rango o en un hueco). A lo sumo 4 salidas por
    sala. Ids desde 1; con `fraccion_inexistentes` > 0 faltan algunas salas del medio."""
    azar = random.Random(semilla)
    hueco = [False] * (total + 1)
    if fraccion_inexistentes > 0 and total > 3:
        for i in range(2, total):
            hueco[i] = azar.random() < fraccion_inexistentes / 2
    ids = [i for i in range(1, total + 1) if not hueco[i]]
    salas = {}
    for i in ids:
        salas[i] = {"id": i, "nombre": f"Sala {i}", "salidas": {}}

    def destino_al_azar():
        if fraccion_inexistentes > 0 and azar.random() < fraccion_inexistentes:
            huecos = [i for i in range(1, total + 1) if hueco[i]]
            if huecos and azar.random() < 0.5:
                return huecos[azar.randrange(len(huecos))]
            return total + azar.randint(1, 5)
        return ids[azar.randrange(len(ids))]

    for i in ids:
        cuantas = azar.choice((0, 1, 2, 2, 3, 3, 4))
        letras = list(LETRAS)
        azar.shuffle(letras)
        for letra in letras[:cuantas]:
            if letra in salas[i]["salidas"]:
                continue
            destino = destino_al_azar()
            salas[i]["salidas"][letra] = {"sala": destino}
            if destino in salas and destino != i and azar.random() >= fraccion_un_sentido:
                for vuelta in LETRAS:                                   # su inversa, si la sala destino tiene una letra libre
                    if vuelta not in salas[destino]["salidas"]:
                        salas[destino]["salidas"][vuelta] = {"sala": i}
                        break
    return [salas[i] for i in ids]


def mapa_desde_esqueleto(esqueleto: list[dict]):
    """MapaCripta armado por el mismo camino que usa el juego: ServicioCripta.obtener_mapa sobre una API falsa."""
    from adaptadores.cache import CacheLRU
    from adaptadores.servicioCripta import ServicioCripta
    from Logica.MapaCripta import MapaCripta
    from tests_labs.api_falsa import HttpConfigurable
    servicio = ServicioCripta(HttpConfigurable(esqueleto), CacheLRU(5))
    servicio.listar_criptas()
    return MapaCripta(servicio.obtener_mapa(servicio.obtener_id_cripta(1)))
