"""Referencias ingenuas para probar «ir a» (capacidad 006): caminar a mano, la ruta mínima lexicográfica por
enumeración y un resumen del estado para comparar partidas. Solo para pruebas y --bench; sin dict/set/sorted().

Contrato: specs/006-ir-a/research.md (D1) y contracts/viaje-logica.md."""
from __future__ import annotations

import contextlib
import io

from DTO.EventoDTO import EventoDTO

COSTO_POR_DEFECTO = 100


def caminar_a_mano(logica, salas: list) -> None:
    """Recorre `salas` (ids consecutivos; el primero es la sala actual) con movimientos individuales, como lo haría el
    controlador: un MOVER_JUGADOR por salida y `ingresarEnSala` al empezar cada turno (activa a los enemigos dormidos)."""
    for destino in salas[1:]:
        actual = logica.estadoJuego.jugador.id_sala_actual
        sala = logica.ingresarEnSala(actual)
        salida = None
        for candidata in sala.salidas:
            if candidata.sala_destino == destino and not candidata.cerrada:
                salida = candidata
                break
        if salida is None:
            raise ValueError(f"No hay una salida abierta de {actual} a {destino}")
        evento = EventoDTO(salida.costo, 0, logica.estadoJuego.jugador, "MOVER_JUGADOR", [sala, salida.direccion])
        with contextlib.redirect_stdout(io.StringIO()):
            logica.accionJugador(evento)
        logica.ingresarEnSala(destino)


def ruta_minima_lexicografica(esqueleto: list, origen: int, destino: int) -> list | None:
    """Ruta de menor costo total y, entre las de igual costo, la de menor lista de ids de sala (FR-234), hallada por
    enumeración de TODAS las rutas simples. Solo para criptas pequeñas. Las salidas cerradas del esqueleto no se
    cruzan. Devuelve la lista de ids de sala (con origen y destino) o None si no hay ruta."""
    mejor = [None, None]                      # [costo, ruta]

    def visitar(sala: int, ruta: list, costo: int) -> None:
        if mejor[0] is not None and costo > mejor[0]:
            return
        if sala == destino:
            if mejor[0] is None or costo < mejor[0] or (costo == mejor[0] and ruta < mejor[1]):
                mejor[0], mejor[1] = costo, list(ruta)
            return
        for entrada in esqueleto:
            if entrada["id"] != sala:
                continue
            for letra in ("N", "S", "E", "O"):
                if letra not in entrada["salidas"]:
                    continue
                salida = entrada["salidas"][letra]
                if salida.get("cerrada"):
                    continue
                siguiente = salida["sala"]
                if siguiente in ruta:
                    continue
                ruta.append(siguiente)
                visitar(siguiente, ruta, costo + salida.get("costo", COSTO_POR_DEFECTO))
                ruta.pop()

    visitar(origen, [origen], 0)
    return mejor[1]


def resumen_estado(logica) -> tuple:
    """Todo lo observable de la partida que un viaje y el camino a mano deben dejar igual."""
    jugador = logica.estadoJuego.jugador
    c = logica.mapaConocido
    cargadas = []
    for i in range(len(logica.estadoJuego.salas)):
        if logica.estadoJuego.salas[i] is not None:
            cargadas.append(i)
    return (jugador.id_sala_actual, logica.estadoJuego.reloj.tiempo_actual, jugador.vida_actual,
            list(c.estado), list(c.puertas), list(c.exploradas), cargadas,
            logica.accionesJugador, logica.acciones_linea_tiempo)
