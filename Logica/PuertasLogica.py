"""Único lugar donde cambia el estado de una puerta (FR-116).

El campo de costos que usan los cazadores se reutiliza entre turnos; para que eso sea equivalente a calcular desde cero
tiene que enterarse de TODO cambio de una puerta. Por eso abrir, cerrar (también el cierre automático), deshacer con el
pergamino y cualquier otro cambio pasan por `fijar_cerrada`; test_puertas_punto_unico.py falla si alguien escribe
`.cerrada` en otro sitio.

También es el único punto que sube `MapaCripta.version_puertas`: así quien guarde un cálculo puede comparar la versión
para saber si sigue vigente.
"""
from __future__ import annotations

from typing import Callable


def fijar_cerrada(salida, cerrada: bool, avisar: Callable | None = None, mapa=None) -> bool:
    """Deja la salida abierta o cerrada. Si cambió, sube la versión de puertas de `mapa` (si se da), llama a
    `avisar(salida)` y devuelve True; si ya estaba así, no hace nada más."""
    if salida.cerrada == cerrada:
        return False
    salida.cerrada = cerrada
    if mapa is not None:
        mapa.registrar_cambio_de_puerta()
    if avisar is not None:
        avisar(salida)
    return True
