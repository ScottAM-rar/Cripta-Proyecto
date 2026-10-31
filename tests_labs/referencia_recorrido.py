"""Recorrido por niveles de REFERENCIA, hecho de la forma más ingenua posible, para comparar con el real en las pruebas.

Solo listas, `pop(0)`, búsqueda con `in` y un ordenamiento simple escrito aquí. No importa el recorrido real ni
`Logica.ordenamiento`: así un error del real no se puede repetir en la referencia. Nunca se usa en el juego.

El criterio de transitabilidad es una función del par (origen, destino) de ids de sala.
"""
from __future__ import annotations

LETRAS = ("N", "S", "E", "O")


def _ordenar(lista: list) -> list:
    """Selección: la forma más simple de ordenar de menor a mayor."""
    resultado = list(lista)
    for i in range(len(resultado)):
        menor = i
        for j in range(i + 1, len(resultado)):
            if resultado[j] < resultado[menor]:
                menor = j
        resultado[i], resultado[menor] = resultado[menor], resultado[i]
    return resultado


def recorrer_referencia(esqueleto: list, origen: int, limite: int | None = None, transitable=None) -> tuple:
    """Devuelve (salas, niveles). `esqueleto` es la lista cruda de salas ({"id", "salidas": {letra: {"sala": id}}})."""
    mayor = 0
    for sala in esqueleto:
        if sala["id"] > mayor:
            mayor = sala["id"]
    por_id = [None] * (mayor + 1)
    for sala in esqueleto:
        por_id[sala["id"]] = sala
    if not 0 <= origen <= mayor or por_id[origen] is None:
        raise ValueError("El origen no existe")

    salas = [origen]
    niveles = [0]
    frontera = [origen]
    nivel = 0
    while frontera:
        siguiente = []
        while frontera:
            actual = frontera.pop(0)
            if limite is not None and nivel >= limite:
                continue
            salidas = por_id[actual].get("salidas") or {}
            for letra in LETRAS:
                if letra not in salidas:
                    continue
                destino = salidas[letra]["sala"]
                if not 0 <= destino <= mayor or por_id[destino] is None:
                    continue                                    # sala que no existe: se ignora (FR-513)
                if transitable is not None and not transitable(actual, destino):
                    continue
                if destino in salas or destino in siguiente:
                    continue
                siguiente.append(destino)
        siguiente = _ordenar(siguiente)
        nivel += 1
        for destino in siguiente:
            salas.append(destino)
            niveles.append(nivel)
        frontera = siguiente
    return salas, niveles
