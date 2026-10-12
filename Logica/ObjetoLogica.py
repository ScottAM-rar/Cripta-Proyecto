from DTO.ActorDTO import JugadorDTO
from DTO.EventoDTO import EventoDTO
from DTO.Objeto import *
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.RelojVirtual import RelojVirtual
from Logica.PergaminoLogica import PergaminoLogica

class ObjetoLogica:
    def __init__(self, jugador: JugadorDTO, pergamino_logica: PergaminoLogica | None = None):
        self.jugador = jugador 
        self.pergamino_logica = pergamino_logica

    def usar_objeto(self, objeto: Objeto) -> ResultadoEventoDTO:
        """Logica para usar el objeto. Varia segun el tipo de objeto."""
        resultado = ResultadoEventoDTO()
        match objeto:
            case Pocion():
                self._consumir(objeto)
                evento = self._aplicar_pocion(objeto)
                resultado.exito, resultado.mensaje, resultado.eventoResultado = True, f"Se ha usado la pocion {objeto.nombre}.", evento
            case Antidoto():
                self._consumir(objeto)
                self._aplicar_antidoto(objeto)
                resultado.exito, resultado.mensaje = True, f"Se ha usado el antidoto {objeto.nombre}."
            case Antorcha():
                self._consumir(objeto)
                evento = self._usar_antorcha(objeto)
                resultado.exito, resultado.mensaje, resultado.eventoResultado = True, f"Se ha usado la antorcha {objeto.nombre}.", evento
            case Arma() | Armadura():
                self._equipar(objeto)
                resultado.exito, resultado.mensaje = True, f"Se ha equipado {objeto.nombre}."
            case PergaminoRetroceso():
                if not self.pergamino_logica.hay_algo_para_deshacer():
                    resultado.exito, resultado.mensaje = False, "No hay acciones para deshacer."
                    return resultado
                self._consumir(objeto)
                return self.pergamino_logica.usar_pergamino()
            case Llave():
                resultado.exito, resultado.mensaje = False, "No tiene sentido usar esta llave si no es en una puerta... Bruto."
            case _:
                resultado.exito, resultado.mensaje = False, "El objeto no tiene un uso definido."
        return resultado 
                
                
    def _consumir(self, objeto: Objeto):
        """Consume el objeto del inventario del jugador y lo manda a eliminar."""
        objeto_buscado = self.jugador.inventario.buscar_objeto(objeto)
        if objeto_buscado is None:
            raise ValueError("El objeto no se encuentra en el inventario del jugador.")
        self.jugador.inventario.eliminar_objeto_utilizado(objeto_buscado.objeto)
        
    
    def _aplicar_pocion(self, pocion: Pocion) -> EventoDTO:
        """Aplica los efectos de la pocion al jugador."""
        if pocion.cura > 0:
            self.jugador.vida_actual = min(self.jugador.vida_max, self.jugador.vida_actual + pocion.cura)
        if pocion.modificador_velocidad != 0: #Un modificador podria ser negativo? una pocion vencida *(CCSS)* maincra si lo tiene, ya lo puse pero ahi me avisan
            self.jugador.modificador_velocidad += pocion.modificador_velocidad
            return EventoDTO(pocion.duracion, None, None, "REVERTIR_MODIFICADOR_VELOCIDAD", datos_extra=[pocion.modificador_velocidad])  # Se encola un evento futuro para revertir el modificador de velocidad
    
    def revertir_modificador_velocidad(self, modificador: int):
        """Revierte el modificador de velocidad del jugador."""
        self.jugador.modificador_velocidad -= modificador
    
    def _aplicar_antidoto(self, antidoto: Antidoto):
        """Aplica los efectos del antidoto al jugador."""
        #Primero tiene que estar envenenado y yo no veo que tenga nada de eso el jugador fajsfhasjfdsdajf, codigo "muerto":
        self.jugador.veneno = False
        
    def _usar_antorcha(self, antorcha: Antorcha) -> EventoDTO:
        """Enciende la antorcha del jugador por el tiempo de duracion de la antorcha."""
        self.jugador.antorcha_encendida = True
        return EventoDTO(antorcha.duracion, None, None, "APAGAR_ANTORCHA")  # Se encola un evento futuro para apagar la antorcha
        
    def apagar_antorcha(self):
        """Apaga la antorcha del jugador."""
        self.jugador.antorcha_encendida = False
    
    def _equipar(self, objeto: Arma | Armadura):
        """Equipa el objeto al jugador."""
        inv = self.jugador.inventario
        if inv.actual is None or inv.actual.objeto != objeto:
            raise ValueError("El objeto actual no coincide con el objeto a equipar.")
        inv.equipar_objeto_actual()
        if isinstance(objeto, Arma):
            self.jugador.arma = objeto
        elif isinstance(objeto, Armadura): #Lo hice con elif por la posibilidad de meter por ejemplo, un baston magico.
            self.jugador.armadura = objeto
            