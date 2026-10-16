"""Una fila de la tabla de puntajes local (§2.12), como datos simples. Quien la guarda en disco es un adaptador."""
from dataclasses import dataclass


@dataclass
class RegistroPuntajeDTO:
    nombre: str
    id_cripta: str
    version_cripta: str
    acciones_jugador: int
    enemigos_derrotados: int
    tiempo_final: int
    victoria: bool
