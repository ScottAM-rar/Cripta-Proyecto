from DTO.ActorDTO import JugadorDTO
from DTO.Objeto import *
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica import RelojVirtual

class ObjetoLogica:
    def __init__(self, jugador: JugadorDTO):
        self.jugador = jugador 

    def usar_objeto(self, objeto: Objeto, reloj: RelojVirtual) -> ResultadoEventoDTO:
        """Logica para usar el objeto. Varia segun el tipo de objeto."""
        match objeto:
            case Pocion():
                self._consumir(objeto)
                self._aplicar_pocion(objeto)
                return ResultadoEventoDTO(True, f"Se ha usado la pocion {objeto.nombre}.")
            case Antidoto():
                self._consumir(objeto)
                self._aplicar_antidoto(objeto)
                return ResultadoEventoDTO(True, f"Se ha usado el antidoto {objeto.nombre}.")
            case Antorcha():
                self._consumir(objeto)
                self._usar_antorcha(objeto, reloj)
                return ResultadoEventoDTO(True, f"Se ha encendido una antorcha de {objeto.duracion} segundos.")
            case Arma() | Armadura():
                self._equipar(objeto)
                return ResultadoEventoDTO(True, f"Se ha equipado {objeto.nombre}.")
            case PergaminoRetroceso():
                raise NotImplementedError("Es mas largo de lo que parece esta weba")
            case Llave():
                raise ResultadoEventoDTO(False, "No tiene sentido usar esta llave si no es en una puerta... Bruto.")
                
                
    def _consumir(self, objeto: Objeto):
        """Consume el objeto del inventario del jugador y lo manda a eliminar."""
        self.jugador.inventario.eliminar_objeto_utilizado(objeto)
    
    def _aplicar_pocion(self, pocion: Pocion, reloj: RelojVirtual):
        """Aplica los efectos de la pocion al jugador."""
        if pocion.cura > 0:
            self.jugador.vida_actual = min(self.jugador.vida_max, self.jugador.vida_actual + pocion.cura)
        if pocion.modificador_velocidad != 0: #Un modificador podria ser negativo? una pocion vencida *(CCSS)* maincra si lo tiene, ya lo puse pero ahi me avisan
            self.jugador.modificador_velocidad += pocion.modificador_velocidad
            reloj.encolar(pocion.duracion, self.jugador, "REVERTIR_MODIFICADOR_VELOCIDAD", datos_extra=[pocion.modificador_velocidad])  # Se encola un evento futuro para revertir el modificador de velocidad
    
    def _aplicar_antidoto(self, antidoto: Antidoto):
        """Aplica los efectos del antidoto al jugador."""
        #Primero tiene que estar envenenado y yo no veo que tenga nada de eso el jugador fajsfhasjfdsdajf, codigo "muerto":
        self.jugador.envenenado = False
        
    def _usar_antorcha(self, antorcha: Antorcha, reloj: RelojVirtual):
        """Enciende la antorcha del jugador."""
        #Este no se como implementarlo jjajajajdajdjasdjasjdasjdad, codigo "muerto":
        self.jugador.antorcha_encendida = True
        reloj.encolar(antorcha.duracion, self.jugador, "APAGAR_ANTORCHA")  # Se encola un evento futuro para apagar la antorcha
        
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
            
    #TODO: Ver si ObjetoLogica recibe el reloj al construirse o se pasa por parametro
    #TODO: falta implementar .antorcha_encendida y envenenado en el jugador, y que se revierta el efecto de la pocion de velocidad.
    #TODO: ver si se queda la antorcha encendida como booleano, bonus velocidad como un int en JugadorDTO en (ActorDTO) o otra implementacion 
    #TODO: Ver si encolar esta realmente bien implementao porque esa vaina esta en blanco.