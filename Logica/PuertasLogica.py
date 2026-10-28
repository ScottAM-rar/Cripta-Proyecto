"""Único lugar donde cambia el estado de una puerta (FR-116).

El campo de costos que usan los cazadores se reutiliza entre turnos; para que eso sea equivalente a calcular desde cero
tiene que enterarse de TODO cambio de una puerta. Por eso abrir, cerrar (también el cierre automático), deshacer con el
pergamino y cualquier otro cambio pasan por `fijar_cerrada`; test_puertas_punto_unico.py falla si alguien escribe
`.cerrada` en otro sitio.
"""
from __future__ import annotations

from typing import Callable


def fijar_cerrada(salida, cerrada: bool, avisar: Callable | None = None) -> bool:
    """Deja la salida abierta o cerrada. Si cambió, llama a `avisar(salida)` y devuelve True; si ya estaba así, no avisa."""
    if salida.cerrada == cerrada:
        return False
    salida.cerrada = cerrada
    if avisar is not None:
        avisar(salida)
    return True
