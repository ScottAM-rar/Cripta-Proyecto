import random
from Logica.ComportamientoEnemigo import *
from DTO.SalaDTO import *
from Logica.ActorLogica import ActorLogica
class ComportamientoRastreador(ComportamientoEnemigo):
    VIGENCIA_RASTRO = 400   # un rastro más viejo que esto (en tiempo virtual) ya no cuenta

    @staticmethod
    def _ultimo_paso(salas: list[SalaDTO], indice: int, tiempo_actual: int | None) -> int:
        """Rastro de la sala: el tiempo de la última visita del jugador, o -1 si nunca la pisó o el rastro ya se enfrió
        (hace VIGENCIA_RASTRO o más que pasó). Sin reloj conocido no se descarta ningún rastro."""
        sala = salas[indice]
        if sala is None or sala.ultimo_paso < 0:
            return -1
        if tiempo_actual is not None and tiempo_actual - sala.ultimo_paso >= ComportamientoRastreador.VIGENCIA_RASTRO:
            return -1
        return sala.ultimo_paso

    @staticmethod
    def acción(enemigo:EnemigoDTO, salas: list[SalaDTO], azar: random.Random | None = None, tiempo_actual: int | None = None) -> str:
        siguienteSala: SalidaDTO = None
        pasoSiguiente = 0
        for t in salas[enemigo.id_sala_actual].salidas:
            if (
                t.sala_destino is not None
                and not t.cerrada
                and 0 <= t.sala_destino < len(salas)
            ):
                paso = ComportamientoRastreador._ultimo_paso(salas, t.sala_destino, tiempo_actual)
                if (
                    siguienteSala is None
                    or paso > pasoSiguiente
                    or (paso == pasoSiguiente and t.sala_destino < siguienteSala.sala_destino)
                ):
                    siguienteSala = t
                    pasoSiguiente = paso
        if siguienteSala is None or pasoSiguiente < 0:
            return "NO SE MOVIÓ"
        salaActual = salas[enemigo.id_sala_actual]
        respuesta = ActorLogica._mover(enemigo, salaActual, siguienteSala.direccion)
        if not respuesta.exito:
            return "NO SE MOVIÓ"
        if enemigo in salaActual.enemigos:
            salaActual.enemigos.remove(enemigo)
        #salas[siguienteSala.sala_destino].enemigos.append(enemigo)
        return f"SE MOVIO A {siguienteSala.direccion}"
