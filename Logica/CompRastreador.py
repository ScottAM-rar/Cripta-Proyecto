from Logica.ComportamientoEnemigo import *
from DTO.SalaDTO import *
from Logica.ActorLogica import ActorLogica
class ComportamientoRastreador(ComportamientoEnemigo):
    @staticmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], semilla: int= None) -> str:
        siguienteSala: SalidaDTO = None
        for t in salas[enemigo.id_sala_actual].salidas:
            if (
                t.sala_destino is not None
                and not t.cerrada
                and 0 <= t.sala_destino < len(salas)
            ):
                ultimo_paso_siguiente = (
                    0
                    if salas[t.sala_destino] is None
                    else salas[t.sala_destino].ultimo_paso
                )
                ultimo_paso_seleccionado = (
                    -1
                    if siguienteSala is None or salas[siguienteSala.sala_destino] is None
                    else salas[siguienteSala.sala_destino].ultimo_paso
                )
                if ultimo_paso_seleccionado < ultimo_paso_siguiente:
                    siguienteSala = t
        if siguienteSala is None:
            return "NO SE MOVIÓ"
        salaActual = salas[enemigo.id_sala_actual]
        respuesta = ActorLogica._mover(enemigo, salaActual, siguienteSala.direccion)
        if not respuesta.exito:
            return "NO SE MOVIÓ"
        if enemigo in salaActual.enemigos:
            salaActual.enemigos.remove(enemigo)
        #salas[siguienteSala.sala_destino].enemigos.append(enemigo)
        return f"SE MOVIO A {siguienteSala.direccion}"
        
                