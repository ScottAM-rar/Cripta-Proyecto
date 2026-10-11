from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from DTO.ActorDTO import JugadorDTO
from DTO.EventoDTO import EventoDTO

if __name__ == "__main__":
    servicio = EstadoJuegoServicio()
    criptas = servicio.listarCriptas()
    print(criptas)
    idCripta = servicio.obtenerIdCripta(1)
    print(idCripta)
    servicio.iniciarJuego(idCripta)
    jugador = servicio.getJudador()
    sala_inicial = servicio.obtenerSala(jugador.id_sala_actual)
    print(sala_inicial)
    evento_movimiento = EventoDTO(
        100,
        0,
        jugador,
        "MOVER_JUGADOR",
        [sala_inicial, "norte"]
    )
    servicio.accionJugador(evento_movimiento)
    sala_despues_movimiento = servicio.obtenerSala(jugador.id_sala_actual)
    print(sala_despues_movimiento.salidas)
    evento_movimiento = EventoDTO(
            100,
            0,
            jugador,
            "MOVER_JUGADOR",
            [sala_despues_movimiento, "sur"]
        )
    servicio.accionJugador(evento_movimiento)
