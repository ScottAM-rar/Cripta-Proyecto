from Logica.ComportamientoEnemigo import *
from DTO.SalaDTO import *
from Logica.ActorLogica import ActorLogica
class ComportamientoRastreador(ComportamientoEnemigo):
    @staticmethod
    def _ultimo_paso(salas: list[SalaDTO], indice: int) -> int:
        sala = salas[indice]
        if sala is None or sala.ultimo_paso > 400:
            return 0
        return sala.ultimo_paso

    @staticmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], semilla: int= None) -> str:
        siguienteSala: SalidaDTO = None
        pasoSiguiente = 0
        for t in salas[enemigo.id_sala_actual].salidas:
            if (
                t.sala_destino is not None
                and not t.cerrada
                and 0 <= t.sala_destino < len(salas)
            ):
                paso = ComportamientoRastreador._ultimo_paso(salas, t.sala_destino)
                if (
                    siguienteSala is None
                    or paso > pasoSiguiente
                    or (paso == pasoSiguiente and t.sala_destino < siguienteSala.sala_destino)
                ):
                    siguienteSala = t
                    pasoSiguiente = paso
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
