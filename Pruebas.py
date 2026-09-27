from collections import deque

from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.Objeto import Llave
from DTO.EventoDTO import EventoDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Logica.RelojVirtual import RelojVirtual

TIEMPO_MOVER = 100
TIEMPO_ATACAR = 100
TIEMPO_RECOGER_OBJETO = 25
TIEMPO_USAR_OBJETO = 50
TIEMPO_ABRIR_PUERTA = 25

jugador = JugadorDTO(
    vida_actual=100,
    vida_max=100,
    ataque=15,
    defensa=10,
    velocidad=100,
    inventario_max=2,
    armadura=None,
    arma=None,
)

sala = SalaDTO(
    id=1,
    nombre="Entrada",
    salidas=deque(
        [
            SalidaDTO(
                direccion="norte",
                sala_destino=2,
                cerrada=True,
                llave="llave-bronce",
                cierre_automatico=400,
            )
        ]
    ),
)

estado_juego = EstadoJuego(
    reloj=RelojVirtual(),
    jugador=jugador,
    salas=[sala],
)
estado_juego_servicio = EstadoJuegoServicio(estado_juego)

enemigo = EnemigoDTO(
    vida_actual=40,
    vida_max=40,
    ataque=8,
    defensa=5,
    velocidad=150,
    id_instancia="enemigo-1",
    tipo="esqueleto",
    nombre="Esqueleto",
    comportamiento="agresivo",
)

print(
    "Vida del enemigo antes del ataque:",
    enemigo.vida_actual,
)
estado_juego_servicio.accionJugador(
    EventoDTO(TIEMPO_ATACAR, 1, jugador, "ATACAR", [enemigo])
)

print(
    "Vida del enemigo después del ataque:",
    enemigo.vida_actual,
)



print(
    "Apertura sin llave:",
    estado_juego_servicio.accionJugador(
        EventoDTO(TIEMPO_ABRIR_PUERTA, 1, jugador, "ABRIR_PUERTA", [sala, "norte"])
    ),
)


llave = Llave(
    id_catalogo="llave-bronce",
    nombre="Llave de bronce",
    peso=1,
    valor=0,
)

estado_juego_servicio.accionJugador(
    EventoDTO(TIEMPO_RECOGER_OBJETO, 2, jugador, "RECOGER_OBJETO", [llave])
)


estado_juego_servicio.accionJugador(
    EventoDTO(TIEMPO_USAR_OBJETO, 3, jugador, "USAR_OBJETO", [llave])
)


print(
    "Tiene llave después de recogerla:",
    estado_juego_servicio.tieneLlave("llave-bronce")
    
)


print(
    "Apertura con llave:",
    estado_juego_servicio.accionJugador(
        EventoDTO(TIEMPO_ABRIR_PUERTA, 4, jugador, "ABRIR_PUERTA", [sala, "norte"])
    ),
)
estado_juego_servicio.accionJugador(
    EventoDTO(TIEMPO_ATACAR, 1, jugador, "ATACAR", [enemigo])
)


print(
    "Sala del jugador antes de moverse:",
    jugador.id_sala_actual,
)
estado_juego_servicio.accionJugador(
    EventoDTO(TIEMPO_MOVER, 5, jugador, "MOVER_JUGADOR", [sala, "norte"])
)


print(
    "Sala del jugador después de moverse:",
    jugador.id_sala_actual,
)

estado_juego_servicio.accionJugador(
    EventoDTO(TIEMPO_ATACAR, 1, jugador, "ATACAR", [enemigo])
)
estado_juego_servicio.accionJugador(
    EventoDTO(TIEMPO_ATACAR, 1, jugador, "ATACAR", [enemigo])
)