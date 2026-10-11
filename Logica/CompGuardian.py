from Logica.ComportamientoEnemigo import *

class ComportamientoGuardian(ComportamientoEnemigo):
    @staticmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], semilla: int = None) -> str:
        return "NO SE MOVIO"
    #por DEFINICION guardian nunca hace nada, se crea el comportamiento 
    # PENSANDO a futuro si tiene que hacer una acción