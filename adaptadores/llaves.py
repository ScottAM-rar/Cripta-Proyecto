"""Lector y validador de la respuesta de GET /criptas/<id>/llaves (capacidad 009, FR-302, FR-311).

El dict de la respuesta JSON solo se lee aquí; lo que sale son listas paralelas (ids, salas, enemigos), sin dict ni
set como índice (principio I). Los repetidos se detectan ordenando posiciones con ordenar_adaptativo y comparando
vecinas. Nada de este módulo hace solicitudes."""
from __future__ import annotations

from Logica.ordenamiento import ordenar_adaptativo


class LlavesInvalidas(ValueError):
    """La respuesta de llaves no cumple FR-311. `motivo` dice qué regla falló. ServicioCripta la traduce siempre a
    LlavesNoDisponibles."""

    def __init__(self, motivo: str):
        super().__init__(motivo)
        self.motivo = motivo


def leer_llaves(respuesta: dict) -> list[dict]:
    """Devuelve respuesta["llaves"] tal cual. Lanza LlavesInvalidas si falta o no es una lista."""
    if not isinstance(respuesta, dict) or "llaves" not in respuesta:
        raise LlavesInvalidas("respuesta sin llaves")
    llaves = respuesta["llaves"]
    if not isinstance(llaves, list):
        raise LlavesInvalidas("el campo llaves no es una lista")
    return llaves


def _es_texto_no_vacio(valor) -> bool:
    return isinstance(valor, str) and valor != ""


def _es_entero(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_llaves(crudas: list[dict], existe: list[bool], contenido_guardado
                   ) -> tuple[list[str], list[int], list[str | None]]:
    """Valida la lista cruda en el orden de research.md §5 y la devuelve como listas paralelas, en el orden de la
    respuesta. `existe[sala]` dice si el esqueleto tiene esa sala. `contenido_guardado(sala) -> dict | None` solo lee
    lo guardado; si devuelve None, el enemigo se acepta sin comprobarlo. Lanza LlavesInvalidas(motivo)."""
    ids: list[str] = []
    salas: list[int] = []
    enemigos: list[str | None] = []

    # 1 y 2. Forma de cada entrada y sala dentro del esqueleto.
    for posicion in range(len(crudas)):
        entrada = crudas[posicion]
        if not isinstance(entrada, dict):
            raise LlavesInvalidas(f"la entrada {posicion} no es un objeto")
        if not _es_texto_no_vacio(entrada.get("id")):
            raise LlavesInvalidas(f"la entrada {posicion} no tiene un id válido")
        if "sala" not in entrada or not _es_entero(entrada["sala"]):
            raise LlavesInvalidas(f"la entrada {posicion} no tiene una sala entera")
        enemigo = entrada.get("enemigo")
        if enemigo is not None and not isinstance(enemigo, str):
            raise LlavesInvalidas(f"la entrada {posicion} tiene un enemigo que no es texto")
        sala = entrada["sala"]
        if sala < 0 or sala >= len(existe) or not existe[sala]:
            raise LlavesInvalidas(f"la sala {sala} de la entrada {posicion} no está en el esqueleto")
        ids.append(entrada["id"])
        salas.append(sala)
        enemigos.append(enemigo)

    # 3. Entradas idénticas: se ordenan las posiciones por (id, sala, enemigo o "") y se comparan vecinas.
    def clave(i):
        return (ids[i], salas[i], enemigos[i] if enemigos[i] is not None else "")

    ordenadas = ordenar_adaptativo(range(len(ids)), key=clave)
    for j in range(1, len(ordenadas)):
        if clave(ordenadas[j - 1]) == clave(ordenadas[j]):
            i = ordenadas[j]
            raise LlavesInvalidas(f"la llave {ids[i]} aparece repetida en la sala {salas[i]}")

    # 4. Enemigo contra el contenido guardado, si lo hay. Nunca se hacen solicitudes.
    for i in range(len(ids)):
        if enemigos[i] is None:
            continue
        contenido = contenido_guardado(salas[i])
        if contenido is None:
            continue
        encontrado = False
        for colocacion in contenido.get("enemigos") or []:
            if colocacion.get("instancia") == enemigos[i]:
                encontrado = True
                break
        if not encontrado:
            raise LlavesInvalidas(f"el enemigo {enemigos[i]} no está en la sala {salas[i]}")

    return ids, salas, enemigos
