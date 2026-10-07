from collections import deque

from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.EventoDTO import EventoDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Logica.RelojVirtual import RelojVirtual
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio


TIEMPO_MOVER = 100
TIEMPO_ATACAR = 100


def prueba_partida_completa():
    salas = [
        SalaDTO(id=indice, nombre=f"Sala {indice}", salidas=deque())
        for indice in range(5)
    ]

    for indice in range(4):
        salas[indice].salidas.append(
            SalidaDTO(direccion="este", sala_destino=indice + 1)
        )
        salas[indice + 1].salidas.append(
            SalidaDTO(direccion="oeste", sala_destino=indice)
        )

    jugador = JugadorDTO(
        vida_actual=100,
        vida_max=100,
        ataque=20,
        defensa=5,
        velocidad=100,
        inventario_max=2,
        id_sala_actual=0,
    )

    enemigos = [
        EnemigoDTO(
            vida_actual=45,
            vida_max=45,
            ataque=8,
            defensa=4,
            velocidad=100,
            id_instancia="errante-1",
            tipo="errante",
            nombre="Errante de la sala 1",
            comportamiento="ERRANTE",
            id_sala_actual=1,
        ),
        EnemigoDTO(
            vida_actual=50,
            vida_max=50,
            ataque=9,
            defensa=5,
            velocidad=100,
            id_instancia="errante-2",
            tipo="errante",
            nombre="Errante de la sala 3",
            comportamiento="RASTREADOR",
            id_sala_actual=2,
        ),
        EnemigoDTO(
            vida_actual=55,
            vida_max=55,
            ataque=10,
            defensa=6,
            velocidad=100,
            id_instancia="guardian-1",
            tipo="guardian",
            nombre="Guardian de la sala 2",
            comportamiento="GUARDIAN",
            id_sala_actual=4,
        ),
        EnemigoDTO(
            vida_actual=60,
            vida_max=60,
            ataque=11,
            defensa=7,
            velocidad=100,
            id_instancia="guardian-2",
            tipo="guardian",
            nombre="Guardian de la sala 4",
            comportamiento="GUARDIAN",
            id_sala_actual=3,
        ),
    ]

    for enemigo in enemigos:
        salas[enemigo.id_sala_actual].enemigos.append(enemigo)

    estado_juego = EstadoJuego(
        reloj=RelojVirtual(),
        jugador=jugador,
        salas=salas,
    )
    servicio = EstadoJuegoServicio(estado_juego)

    assert len(estado_juego.salas) == 5
    assert sum(len(sala.enemigos) for sala in estado_juego.salas) == 4

    respuestas_movimiento = []
    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))
    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))

    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))

    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))

    print("Prueba única de partida completada correctamente")


if __name__ == "__main__":
    prueba_partida_completa()
