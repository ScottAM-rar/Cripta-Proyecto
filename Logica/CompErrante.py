from Logica.ComportamientoEnemigo import *
from Logica.ActorLogica import ActorLogica
import random
class ComportamientoErrante(ComportamientoEnemigo):
    @staticmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], azar: random.Random | None = None, tiempo_actual: int | None = None,
               campo_de_costos=None) -> AccionEnemigoDTO:
        salaActual = salas[enemigo.id_sala_actual]
        if azar is None:
            azar = random.Random()   # solo si alguien la llama suelta; el juego siempre pasa el azar del modelo
        salidasDisponibles = [
            salida for salida in salaActual.salidas
            if salida is not None
            and not salida.cerrada
            and salida.sala_destino is not None
            and 0 <= salida.sala_destino < len(salas)
        ]
        if not salidasDisponibles:
            return AccionEnemigoDTO("NO SE MOVIÓ")
        siguienteSala = azar.choice(salidasDisponibles)
        respuesta = ActorLogica._mover(enemigo, salaActual, siguienteSala.direccion)
        if not respuesta.exito:
            return AccionEnemigoDTO("NO SE MOVIÓ")
        if enemigo in salaActual.enemigos:
            salaActual.enemigos.remove(enemigo)
        #salas[siguienteSala.sala_destino].enemigos.append(enemigo)
        return AccionEnemigoDTO(f"SE MOVIO A {siguienteSala.direccion}", respuesta.costo)

    

        