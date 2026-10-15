from DTO.ActorDTO import *
from DTO.SalaDTO import SalaDTO
from DTO.CambioDTO import CambioDTO
from DTO.Objeto import PergaminoRetroceso

from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.RetrocesoLogica import RetrocesoLogica

class PergaminoLogica:
    def __init__(self, retroceso_logica: RetrocesoLogica, salas: list[SalaDTO], reencolar_evento=None):
        self.retroceso_logica = retroceso_logica
        self.salas = salas
        self.reencolar_evento = reencolar_evento

    def hay_algo_para_deshacer(self) -> bool:
        """Verifica si hay acciones registradas en el historial de retroceso."""
        return self.retroceso_logica.hay_algo_para_deshacer()

    def usar_pergamino(self) -> ResultadoEventoDTO:
        """Aplica los efectos del pergamino al jugador."""
        if not self.hay_algo_para_deshacer():
            return ResultadoEventoDTO(exito=False, mensaje="No hay nada que retroceder.")
        
        self._revertir()
        if self.reencolar_evento is not None:
            for evento in self.retroceso_logica.eventos_retroceso:
                self.reencolar_evento(evento)
        return ResultadoEventoDTO(exito=True, mensaje="Se han revertido los cambios hasta la última acción registrada.")
    
    def _revertir(self) -> list[CambioDTO]:
        """Revertir los efectos de un delta en el jugador."""
        lista_cambios = self.retroceso_logica.obtener_cambios_retroceso() # lista de cambios (cada una con 1 o 2 CambioDTO)
        cambios_revertidos = []
        for cambios in lista_cambios:
            for cambio in reversed(cambios):
                self._revertir_cambio(cambio)
                cambios_revertidos.append(cambio)
        return cambios_revertidos

    def _revertir_cambio(self, cambio: CambioDTO) -> None:
        """Revertir los efectos de un delta en el jugador."""
        match cambio.tipo_accion:
            case "ACTUALIZAR_VIDA":
                cambio.objeto_afectado.vida_actual = cambio.valor_anterior
            case "MOVER":
                sala_anterior = self.salas[cambio.valor_anterior]
                
                cambio.objeto_afectado.id_sala_actual = sala_anterior.id
                if isinstance(cambio.objeto_afectado, EnemigoDTO):
                    sala_nueva = self.salas[cambio.valor_nuevo]
                    sala_anterior.enemigos.append(cambio.objeto_afectado)
                    sala_nueva.enemigos.remove(cambio.objeto_afectado)
            case "RECOGER_OBJETO": # Revertir la acción de recoger un objeto, lo deja en la sala donde se recogio y se suelta desde el inventario
                jugador: JugadorDTO = cambio.objeto_afectado
                objeto: Objeto = cambio.elemento
                jugador.inventario.eliminar_objeto_por_retroceso(objeto)
                sala = self.salas[cambio.valor_anterior]
                sala.objetos.append(objeto)
                
            case "SOLTAR_OBJETO": # Revertir la acción de soltar un objeto, lo quita de la sala y lo devuelve al inventario del jugador
                jugador: JugadorDTO = cambio.objeto_afectado
                objeto: Objeto = cambio.elemento
                sala = self.salas[cambio.valor_anterior]
                if objeto in sala.objetos and jugador is not None:
                    sala.objetos.remove(objeto)
                    jugador.inventario.insertar_en_indice_por_retroceso(
                        cambio.indice,
                        objeto,
                    )
                    
            case "EQUIPAR_OBJETO" : # Revertir la acción de equipar un objeto, lo devuelve al inventario del jugador
                jugador: JugadorDTO = cambio.objeto_afectado
                objeto: Objeto = cambio.elemento
                jugador.arma = cambio.valor_anterior if isinstance(objeto, Arma) else jugador.arma
                jugador.armadura = cambio.valor_anterior if isinstance(objeto, Armadura) else jugador.armadura
                jugador.inventario.mover_objeto_equipado_a_su_indice_anterior(cambio.indice, objeto)
                
            case "DESEQUIPAR_OBJETO" : # Revertir la acción de desequipar un objeto, lo devuelve al inventario del jugador
                jugador: JugadorDTO = cambio.objeto_afectado
                objeto: Objeto = cambio.elemento
                jugador.arma = cambio.valor_anterior if isinstance(objeto, Arma) else jugador.arma
                jugador.armadura = cambio.valor_anterior if isinstance(objeto, Armadura) else jugador.armadura
                jugador.inventario.insertar_en_indice_por_retroceso(cambio.indice, objeto)
                jugador.inventario.equipar_objeto_por_retroceso(cambio.valor_anterior)
                
            case "USAR_OBJETO" : # Revertir la acción de usar un objeto, lo devuelve al inventario del jugador
                jugador: JugadorDTO = cambio.objeto_afectado
                objeto: Objeto = cambio.elemento 
                if isinstance(objeto, PergaminoRetroceso):
                    # No se puede revertir el uso de un pergamino de retroceso, ya que este elimina cambios del historial
                    raise ValueError("No se puede revertir el uso de un pergamino de retroceso.")
                jugador.inventario.insertar_en_indice_por_retroceso(cambio.indice, objeto)
                
            case "REVERTIR_MODIFICADOR_VELOCIDAD":
                jugador: JugadorDTO = cambio.objeto_afectado
                modificador: int = cambio.valor_anterior
                jugador.modificador_velocidad = modificador
            
            case "USAR_ANTORCHA":
                jugador: JugadorDTO = cambio.objeto_afectado
                jugador.antorcha_encendida = cambio.valor_anterior
                
            case "APAGAR_ANTORCHA":
                jugador: JugadorDTO = cambio.objeto_afectado
                jugador.antorcha_encendida = cambio.valor_anterior
                
            case "APLICAR_ANTIDOTO":
                jugador: JugadorDTO = cambio.objeto_afectado
                jugador.veneno = cambio.valor_anterior

            case "CAMBIAR_PUERTA":
                salida = cambio.objeto_afectado
                salida.cerrada = cambio.valor_anterior

            case "CAMBIAR_TRAMPA":
                trampa = cambio.objeto_afectado
                trampa.armada = cambio.valor_anterior

            case _:
                raise ValueError(f"Tipo de acción desconocido: {cambio.tipo_accion}")