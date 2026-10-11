from DTO.ActorDTO import JugadorDTO
from DTO.DeltaDTO import DeltaDTO
from DTO.Objeto import PergaminoRetroceso
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.RetrocesoLogica import RetrocesoLogica

class PergaminoLogica:
    def __init__(self, jugador: JugadorDTO, retroceso_logica: RetrocesoLogica):
        self.jugador = jugador
        self.retroceso_logica = retroceso_logica

    def hay_algo_para_deshacer(self) -> bool:
        """Verifica si hay acciones registradas en el historial de retroceso."""
        return self.retroceso_logica.hay_acciones_para_deshacer()

    def usar_pergamino(self) -> ResultadoEventoDTO:
        """Aplica los efectos del pergamino al jugador."""
        deltas = self.retroceso_logica.deshacer_accion()
        if deltas is None:
            return ResultadoEventoDTO(False, "No hay acciones para deshacer.")
        for delta in reversed(deltas):  # Revertir en orden inverso para mantener la coherencia
            self._revertir(delta)
        return ResultadoEventoDTO(True, "Se ha usado el pergamino de retroceso y se han revertido las acciones registradas.")

    def _revertir(self, delta: DeltaDTO) -> None:
        """Revertir los efectos de un delta en el jugador."""
        match delta.tipo_accion:
            case "MOVER_JUGADOR":
                self.jugador.id_sala_actual = delta.datos["id_sala_anterior"]
            case "ATACAR":
                delta.datos["objetivo"].vida_actual += delta.datos["danio"]
            case "RECOGER_OBJETO":
                if isinstance(delta.datos["objeto"], PergaminoRetroceso):
                    return 
                try:
                    self.jugador.inventario.eliminar_objeto_utilizado(delta.datos["objeto"])
                except ValueError:
                    pass  # El objeto ya no está en el inventario, no hacer nada
            case _:
                raise ValueError(f"Tipo de accion no reconocido: {delta.tipo_accion}")
    
    