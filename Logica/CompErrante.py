from Logica.ComportamientoEnemigo import *
from Logica.ActorLogica import ActorLogica
import random
class ComportamientoErrante(ComportamientoEnemigo):
    @staticmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO]) -> str:
        salaActual = salas[enemigo.id_sala_actual]
        azar = random.Random()
        intentos = 0
        salidasDisponibles = [s for s in salaActual.salidas if s is not None]
        if not salidasDisponibles:
            return "NO SE MOVIÓ"
        siguienteSala = azar.choice(salidasDisponibles)
        ActorLogica._mover(enemigo, salaActual, siguienteSala.direccion)
        return f"SE MOVIO A {siguienteSala.direccion}"


        