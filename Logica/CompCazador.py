from Logica.ComportamientoEnemigo import *
from Logica.ActorLogica import ActorLogica
import random


class ComportamientoCazador(ComportamientoEnemigo):
    """Persigue al jugador por la ruta de menor costo (FR-111 a FR-117). Sin azar.

    Si comparte sala con el jugador NO llega aquí: EnemigoLogica ya lo hace atacar (FR-110)."""

    @staticmethod
    def decidir(enemigo, salas: list, campo_de_costos) -> tuple:
        """La decisión del turno SIN ejecutarla: (salida elegida, costo mínimo d) o (None, None) si espera.
        Solo lee: no mueve a nadie ni abre puertas. Es lo que se compara contra el cálculo desde cero (principio III)."""
        origen = enemigo.id_sala_actual
        campo = campo_de_costos.obtener(enemigo.rango)
        d = campo.costo(origen)
        if d is None or d > enemigo.rango:
            return None, None                                          # sin ruta abierta o fuera de rango (FR-112)
        elegida = None
        for salida in salas[origen].salidas:                           # solo salidas abiertas ahora (FR-115)
            if salida.cerrada or salida.sala_destino is None:
                continue
            restante = campo.costo(salida.sala_destino)
            if restante is None or salida.costo + restante != d:
                continue
            if elegida is None or salida.sala_destino < elegida.sala_destino:      # desempate: menor id (FR-114)
                elegida = salida
        if elegida is None:
            return None, None
        return elegida, d

    @staticmethod
    def acción(enemigo: EnemigoDTO, salas: list[SalaDTO], azar: random.Random | None = None, tiempo_actual: int | None = None,
               campo_de_costos=None) -> AccionEnemigoDTO:
        if campo_de_costos is None:
            raise ValueError("El cazador necesita el campo de costos para decidir")
        elegida, _ = ComportamientoCazador.decidir(enemigo, salas, campo_de_costos)
        if elegida is None:
            return AccionEnemigoDTO("ESPERÓ")
        sala_actual = salas[enemigo.id_sala_actual]
        respuesta = ActorLogica._mover(enemigo, sala_actual, elegida.direccion)
        if not respuesta.exito:
            return AccionEnemigoDTO("ESPERÓ")
        if enemigo in sala_actual.enemigos:
            sala_actual.enemigos.remove(enemigo)
        return AccionEnemigoDTO(f"SE MOVIO A {elegida.direccion}", respuesta.costo)       # FR-113
