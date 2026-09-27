from collections import deque

from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.Objeto import Llave
from DTO.EventoDTO import EventoDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Logica.GestorEventos import GestorEventos
from Logica.JugadorLogica import JugadorLogica
from Logica.SalasLogica import SalaLogica


jugador = JugadorDTO(
    vida_actual=100,
    vida_max=100,
    ataque=15,
    defensa=10,
    velocidad=5,
    inventario_max=2,
    armadura=None,
    arma=None,
)

print("Capacidad del inventario:", jugador.inventario.maxlen)
print(
    "Tiene capacidad_inventario:",
    hasattr(jugador, "capacidad_inventario"),
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
                cierre_automatico=10,
            )
        ]
    ),
)

estado_juego = EstadoJuego(jugador=jugador, salas=[sala])
jugador_logica = JugadorLogica(jugador)
sala_logica = SalaLogica(sala)
gestor_eventos = GestorEventos([sala], jugador_logica, sala_logica)

enemigo = EnemigoDTO(
    vida_actual=40,
    vida_max=40,
    ataque=8,
    defensa=5,
    velocidad=3,
    id_instancia="enemigo-1",
    tipo="esqueleto",
    nombre="Esqueleto",
    comportamiento="agresivo",
)

print(
    "Vida del enemigo antes del ataque:",
    enemigo.vida_actual,
)
gestor_eventos.procesar_evento(
    EventoDTO(0, 1, jugador, "ATACAR", [enemigo]),
    estado_juego,
)
print(
    "Vida del enemigo después del ataque:",
    enemigo.vida_actual,
)

print(
    "Vida del jugador antes del contraataque:",
    jugador.vida_actual,
)
gestor_eventos.procesar_evento(
    EventoDTO(0, 2, enemigo, "ATACAR", [jugador]),
    estado_juego,
)
print(
    "Vida del jugador después del contraataque:",
    jugador.vida_actual,
)

print(
    "Apertura sin llave:",
    gestor_eventos.procesar_evento(
        EventoDTO(0, 1, sala, "ABRIR_PUERTA", [jugador, "norte"]),
        estado_juego,
    ),
)

llave = Llave(
    id_catalogo="llave-bronce",
    nombre="Llave de bronce",
    peso=1,
    valor=0,
)

gestor_eventos.procesar_evento(
    EventoDTO(0, 2, jugador, "RECOGER_OBJETO", [llave]),
    estado_juego,
)

print(
    "Tiene llave después de recogerla:",
    gestor_eventos.procesar_evento(
        EventoDTO(0, 3, jugador, "TIENE_LLAVE", ["llave-bronce"]),
        estado_juego,
    ),
)

print(
    "Apertura con llave:",
    gestor_eventos.procesar_evento(
        EventoDTO(0, 4, sala, "ABRIR_PUERTA", [jugador, "norte"]),
        estado_juego,
    ),
)

print(
    "Sala del jugador antes de moverse:",
    jugador.id_sala_actual,
)
gestor_eventos.procesar_evento(
    EventoDTO(0, 5, jugador, "MOVER_JUGADOR", [sala, "norte"]),
    estado_juego,
)
print(
    "Sala del jugador después de moverse:",
    jugador.id_sala_actual,
)