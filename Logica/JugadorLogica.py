from DTO.ActorDTO import JugadorDTO,EnemigoDTO
from DTO.SalaDTO import SalaDTO
from DTO.Objeto import Objeto
import random

class JugadorLogica:
    def __init__(self,jugador : JugadorDTO):
        self.jugador = jugador

    def mover_jugador(self,sala_destino: SalaDTO) -> None:
        if not any(s.sala_destino == sala_destino.id for s in sala_destino.salidas):
            raise ValueError("La sala no es una salida válida.")
        self.jugador.id_sala_actual = sala_destino.id

    def atacarEnemigo(self, enemigo : EnemigoDTO):
        azar = random.Random()
        daño = max(1,self.jugador.ataque+azar.randint(0,4) - enemigo.defensa)
        enemigo.vida_actual-=daño

    def recogerObjeto(self,objeto: Objeto):
        self.jugador.inventario.agregar_objeto(objeto)

    def soltarObjeto(self, objeto: Objeto):
        self.jugador.inventario.soltar_objeto_actual(objeto)
        
    def equiparArmaOArmaduraActual(self, objeto: Objeto):
        if objeto.tipo != "arma" and objeto.tipo != "armadura":
            raise ValueError("El objeto actual no es equipable.")
        self.jugador.inventario.equipar_objeto_actual(objeto)
        
    def tiene_llave(self, id_llave: int) -> bool:
        """Comprueba si el jugador posee en su inventario un objeto llave con el ID dado."""
        nodo = self.jugador.inventario.cabeza
        while nodo is not None:
            if nodo.objeto.id_catalogo == id_llave:
                return True
            nodo = nodo.siguiente
        return False


    
