from collections import deque

from DTO.ActorDTO import JugadorDTO
from DTO.Objeto import Llave
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Logica.SalasLogica import SalaLogica


jugador = JugadorDTO(
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

sala_logica = SalaLogica(sala)

print(
    "Sin llave:",
    sala_logica.intentarAbrirPuerta(jugador, "norte"),
)

jugador.inventario.append(
    Llave(
        id_catalogo="llave-bronce",
        nombre="Llave de bronce",
        peso=1,
        valor=0,
    )
)

print(
    "Con llave:",
    sala_logica.intentarAbrirPuerta(jugador, "norte"),
)