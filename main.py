from collections import deque
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.ActorDTO import JugadorDTO, EnemigoDTO
from DTO.TrampaDTO import Trampa
from Logica.RelojVirtual import RelojVirtual
from Controlador.ControladorJuego import ControladorJuego  

def main():
    # 1. Inicializamos el RelojVirtual 
    reloj = RelojVirtual()
    
    # 2. Configuramos las salidas de la sala de ejemplo
    salidas_iniciales = deque([
        SalidaDTO(direccion="norte", sala_destino=2, cerrada=False, llave=None),
        SalidaDTO(direccion="sur", sala_destino=0, cerrada=True, llave="itm_llave_hierro"),
        SalidaDTO(direccion="este", sala_destino=3, cerrada=False, llave=None),
        SalidaDTO(direccion="oeste", sala_destino=0, cerrada=False, llave=None)
    ], maxlen=4)

    # 3. Creamos un enemigo real usando EnemigoDTO
    enemigo_inicial = EnemigoDTO(
        vida_max=50, 
        vida_actual=50,
        ataque=12, 
        defensa=5, 
        velocidad=10,
        id_instancia="t-01", 
        tipo="trp_goblin", 
        nombre="Goblin Guardián",
        comportamiento="guardian", 
    )

    # 4. Creamos una trampa real usando el DTO de Trampa
    """Esto es mientras se termina la logica de las trampas"""

    trampa_inicial = Trampa(
        id_instancia="trp_01", 
        id_catalogo="pinchos", 
        daño=15, 
        rearme=5, 
        armada=True
    )

    # 5. Armamos la SalaDTO oficial
    sala_inicial = SalaDTO(
        id=1, 
        nombre="Vestíbulo Oscuro", 
        salidas=salidas_iniciales,
        enemigos=[enemigo_inicial], 
        objetos=["itm_antorcha", "itm_pocion"],
        trampas=[trampa_inicial], 
        ultimo_paso=0
    )

    # 6. Creamos el JugadorDTO oficial
    jugador_inicial = JugadorDTO(
        vida_max=100,
        vida_actual=100,
        ataque=15, 
        defensa=10, 
        velocidad=12,
        inventario_max=5, 
        id_sala_actual=1
    )

    # 7. Unificamos todo en el EstadoJuego oficial del equipo
    estado_juego = EstadoJuego(
        salas=[sala_inicial],
        jugador=jugador_inicial,
        reloj=reloj
    )

    # 8. Arrancamos el juego a través de tu Controlador
    controlador = ControladorJuego(estado_juego)
    controlador.iniciar()

if __name__ == "__main__":
    main()