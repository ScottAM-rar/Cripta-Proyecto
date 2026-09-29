from collections import deque

from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.Objeto import Llave
from DTO.EventoDTO import EventoDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Logica.RelojVirtual import RelojVirtual
from Logica.EnemigosLogica import EnemigoLogica
from Logica.CompErrante import ComportamientoErrante
from Logica.CompGuardian import ComportamientoGuardian

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


def prueba_comportamientos_y_combate_enemigos():
    salas = [
        SalaDTO(id=indice, nombre=f"Sala {indice}")
        for indice in range(5)
    ]

    for indice in range(4):
        salas[indice].salidas.append(
            SalidaDTO(direccion="este", sala_destino=indice + 1)
        )
        salas[indice + 1].salidas.append(
            SalidaDTO(direccion="oeste", sala_destino=indice)
        )

    jugador_prueba = JugadorDTO(
        vida_actual=100,
        vida_max=100,
        ataque=20,
        defensa=5,
        velocidad=100,
        inventario_max=2,
        id_sala_actual=0,
    )
    enemigo_errante = EnemigoDTO(
        vida_actual=40,
        vida_max=40,
        ataque=8,
        defensa=4,
        velocidad=100,
        id_instancia="errante-1",
        tipo="esqueleto",
        nombre="Esqueleto errante",
        comportamiento="Errante",
        id_sala_actual=2,
    )
    enemigo_guardian = EnemigoDTO(
        vida_actual=50,
        vida_max=50,
        ataque=10,
        defensa=6,
        velocidad=100,
        id_instancia="guardian-1",
        tipo="guardian",
        nombre="Guardian de la cripta",
        comportamiento="GUARDIAN",
        id_sala_actual=4,
    )

    salas[2].enemigos.append(enemigo_errante)
    salas[4].enemigos.append(enemigo_guardian)

    ubicacion_inicial_errante = enemigo_errante.id_sala_actual
    mensaje_errante = ComportamientoErrante.acción(enemigo_errante, salas)
    assert mensaje_errante.startswith("SE MOVIO A")
    assert enemigo_errante.id_sala_actual != ubicacion_inicial_errante

    assert ComportamientoGuardian.acción(enemigo_guardian, salas) == "NO SE MOVIO"

    jugador_prueba.id_sala_actual = 0
    enemigo_errante.id_sala_actual = 0
    enemigo_guardian.id_sala_actual = 0
    vida_inicial_jugador = jugador_prueba.vida_actual

    resultado_errante = EnemigoLogica(enemigo_errante).decidirAccion(
        jugador_prueba, salas
    )
    resultado_guardian = EnemigoLogica(enemigo_guardian).decidirAccion(
        jugador_prueba, salas
    )
    assert resultado_errante[0] is True
    assert resultado_guardian[0] is True
    assert jugador_prueba.vida_actual < vida_inicial_jugador

    estado_prueba = EstadoJuego(
        reloj=RelojVirtual(),
        jugador=jugador_prueba,
        salas=salas,
        enemigos_vivos=[enemigo_errante, enemigo_guardian],
    )
    servicio_prueba = EstadoJuegoServicio(estado_prueba)
    vida_inicial_errante = enemigo_errante.vida_actual
    vida_inicial_guardian = enemigo_guardian.vida_actual

    servicio_prueba.accionJugador(
        EventoDTO(TIEMPO_ATACAR, 10, jugador_prueba, "ATACAR", [enemigo_errante])
    )
    servicio_prueba.accionJugador(
        EventoDTO(TIEMPO_ATACAR, 11, jugador_prueba, "ATACAR", [enemigo_guardian])
    )

    assert enemigo_errante.vida_actual < vida_inicial_errante
    assert enemigo_guardian.vida_actual < vida_inicial_guardian
    print("Prueba de enemigos completada correctamente")


prueba_comportamientos_y_combate_enemigos()

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