import random
from Logica.ComportamientoEnemigo import *

class ComportamientoGuardian(ComportamientoEnemigo):
    @staticmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], azar: random.Random | None = None, tiempo_actual: int | None = None) -> str:
        return "NO SE MOVIO"
    #por DEFINICION guardian nunca hace nada, se crea el comportamiento 
    # PENSANDO a futuro si tiene que hacer una acción