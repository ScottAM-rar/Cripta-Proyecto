from collections import deque

from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.EventoDTO import EventoDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.TrampaDTO import Trampa
from Logica.RelojVirtual import RelojVirtual
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio


TIEMPO_MOVER = 100
TIEMPO_ATACAR = 100
SEMILLA_PRUEBA = 12345


def prueba_partida_completa(semilla: int = SEMILLA_PRUEBA):
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
            id_instancia="Rastreador-1",
            tipo="rastreador",
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

    trampas = [
        Trampa(
            id_instancia="trampa-1",
            id_catalogo="trampa_puas",
            id_sala=1,
            daño=10,
            rearme=25,
        ),
        Trampa(
            id_instancia="trampa-2",
            id_catalogo="trampa_fuego",
            id_sala=3,
            daño=15,
            rearme=25,
        ),
    ]

    for trampa in trampas:
        salas[trampa.id_sala].trampas.append(trampa)

    estado_juego = EstadoJuego(
        reloj=RelojVirtual(),
        jugador=jugador,
        salas=salas,
    )
    servicio = EstadoJuegoServicio(estado_juego, semilla)

    assert len(estado_juego.salas) == 5
    assert sum(len(sala.enemigos) for sala in estado_juego.salas) == 4
    assert sum(len(sala.trampas) for sala in estado_juego.salas) == 2

    def activar_trampa_automatica(trampa: Trampa) -> ResultadoEventoDTO:
        evento = EventoDTO(0, None, trampa, "ACTIVAR_TRAMPA")
        gestor_eventos = servicio._estadoJuegoLogica.gestorEventos
        return gestor_eventos.procesar_evento(evento)

    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    vida_antes_trampa = jugador.vida_actual
    resultado_trampa = activar_trampa_automatica(trampas[0])
    assert resultado_trampa.exito
    assert jugador.vida_actual == vida_antes_trampa - trampas[0].daño
    assert not trampas[0].armada

    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))
    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))

    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    vida_antes_trampa = jugador.vida_actual
    resultado_trampa = activar_trampa_automatica(trampas[1])
    assert resultado_trampa.exito
    assert jugador.vida_actual == vida_antes_trampa - trampas[1].daño
    assert not trampas[1].armada

    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))

    servicio.accionJugador(EventoDTO(TIEMPO_MOVER,None,jugador,"MOVER_JUGADOR",[estado_juego.salas[jugador.id_sala_actual],"este"]))
    if estado_juego.salas[jugador.id_sala_actual].enemigos:
        servicio.accionJugador(EventoDTO(TIEMPO_ATACAR,None,jugador,"ATACAR",[estado_juego.salas[jugador.id_sala_actual].enemigos[0]]))

    estado_final = (
        jugador.vida_actual,
        jugador.id_sala_actual,
        tuple(
            (enemigo.id_instancia, enemigo.vida_actual, enemigo.id_sala_actual)
            for enemigo in enemigos
        ),
    )
    print("Prueba única de partida completada correctamente")
    return estado_final


def prueba_semilla_repetible():
    primera_partida = prueba_partida_completa(SEMILLA_PRUEBA)
    segunda_partida = prueba_partida_completa(SEMILLA_PRUEBA)
    assert primera_partida == segunda_partida
    print("La semilla produce el mismo comportamiento en ambas partidas")


if __name__ == "__main__":
    prueba_semilla_repetible()
