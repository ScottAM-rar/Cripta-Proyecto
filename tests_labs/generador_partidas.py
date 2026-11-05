"""Generador determinista de partidas sintéticas y archivos de log para pruebas y benchmarks.

Permite construir objetos LogPartidaDTO o archivos físicos de registro con longitudes
parametrizables (por defecto 250, 1 000 y 4 000 acciones), cabeceras de versión
y acciones deterministas reproducibles por semilla.
"""
from __future__ import annotations

import json
import os
import random
from DTO.LogPartidaDTO import LogPartidaDTO

SEMILLA_DEFECTO = 2026
ESCALAS = (250, 1_000, 4_000)


def generar_acciones(num_acciones: int, semilla: int = SEMILLA_DEFECTO, incluir_cursor: bool = False) -> list[str]:
    """Genera una lista de acciones JSON deterministas por semilla.
    
    Por defecto genera acciones de juego con costo (ESPERAR). Opcionalmente
    intercala movimientos de cursor de inventario para pruebas específicas.
    """
    rng = random.Random(semilla)
    acciones: list[str] = []
    
    for i in range(num_acciones):
        if incluir_cursor and i > 0 and (i % 20 == 0):
            tipo = "SIGUIENTE_OBJETO" if rng.random() < 0.5 else "ANTERIOR_OBJETO"
            registro = {
                "tipo_accion": tipo,
                "tiempo_ejecucion": 0,
                "actor": {"tipo": "jugador"},
                "datos_extra": []
            }
        else:
            registro = {
                "tipo_accion": "ESPERAR",
                "tiempo_ejecucion": 100,
                "actor": {"tipo": "jugador"},
                "datos_extra": []
            }
        acciones.append(json.dumps(registro))
        
    return acciones


def generar_log_dto(
    num_acciones: int,
    semilla: int = SEMILLA_DEFECTO,
    id_cripta: str = "cripta-01",
    version_cripta: str = "fd58f7743b9e",
    version_catalogo: str = "be68d322d2f5",
    incluir_cursor: bool = False,
) -> LogPartidaDTO:
    """Construye un LogPartidaDTO determinista con la cantidad solicitada de acciones."""
    acciones = generar_acciones(num_acciones, semilla, incluir_cursor=incluir_cursor)
    return LogPartidaDTO(
        id_cripta=id_cripta,
        semilla=semilla,
        version_cripta=version_cripta,
        version_catalogo=version_catalogo,
        acciones=acciones,
    )


def generar_archivo_log(
    ruta: str,
    num_acciones: int,
    semilla: int = SEMILLA_DEFECTO,
    id_cripta: str = "cripta-01",
    version_cripta: str = "fd58f7743b9e",
    version_catalogo: str = "be68d322d2f5",
) -> str:
    """Escribe un archivo de registro .log en la ruta indicada y devuelve dicha ruta."""
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    dto = generar_log_dto(num_acciones, semilla, id_cripta, version_cripta, version_catalogo)
    
    cabecera = (
        f"cripta: {dto.id_cripta}\n"
        f"semilla: {dto.semilla}\n"
        f"version_cripta: {dto.version_cripta}\n"
        f"version_catalogo: {dto.version_catalogo}\n"
    )
    cuerpo = "\n".join(dto.acciones) + ("\n" if dto.acciones else "")
    
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(cabecera + cuerpo)
        
    return ruta
