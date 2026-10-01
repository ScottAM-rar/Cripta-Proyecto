from DTO.ActorDTO import JugadorDTO
from DTO.Objeto import *

class ObjetoLogica:
    def __init__(self, jugador: JugadorDTO):
        self.jugador = jugador 

    def usar_objeto(self, objeto: Objeto, tiempo_actual: int) -> None:
        """Logica para usar el objeto. Varia segun el tipo de objeto."""
        match objeto:
            case Pocion():
                self._consumir(objeto)
                self._aplicar_pocion(objeto)
            case Antidoto():
                self._consumir(objeto)
                self._aplicar_antidoto(objeto)
            case Antorcha():
                self._consumir(objeto)
                self._usar_antorcha(objeto, tiempo_actual)
            case Arma() | Armadura():
                self._equipar(objeto)
            case PergaminoRetroceso():
                raise NotImplementedError("Es mas largo de lo que parece esta weba")
            case Llave():
                raise ValueError("No tiene sentido usar esta llave si no es en una puerta... Bruto.")
                
                
    def _consumir(self, objeto: Objeto):
        """Consume el objeto del inventario del jugador y lo manda a eliminar."""
        self.jugador.inventario.eliminar_objeto_utilizado(objeto)
    
    def _aplicar_pocion(self, pocion: Pocion):
        """Aplica los efectos de la pocion al jugador."""
        if pocion.cura > 0:
            self.jugador.vida_actual = min(self.jugador.vida_max, self.jugador.vida_actual + pocion.cura)
        if pocion.modificador_velocidad != 0: #Un modificador podria ser negativo? una pocion vencida *(CCSS)* maincra si lo tiene, ya lo puse pero ahi me avisan
            self.jugador.velocidad += pocion.modificador_velocidad
            # TODO: implementar evento futuro que revierta el efecto de la pocion 
    
    def _aplicar_antidoto(self, antidoto: Antidoto):
        """Aplica los efectos del antidoto al jugador."""
        #Primero tiene que estar envenenado y yo no veo que tenga nada de eso el jugador fajsfhasjfdsdajf
        
    def _usar_antorcha(self, antorcha: Antorcha, tiempo_actual: int):
        """Enciende la antorcha del jugador."""
        #Este no se como implementarlo jjajajajdajdjasdjasjdasjdad
        
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