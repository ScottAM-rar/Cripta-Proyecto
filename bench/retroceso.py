"""§4.6 Historial de retroceso: diferencias en lista doble (el del juego) contra instantáneas del estado en un buffer de 5.

Las instantáneas existen SOLO aquí. Para ser justas copian únicamente los campos que el juego puede cambiar (no un
deepcopy), así que son la versión razonable de la alternativa, no una caricatura.
"""
from __future__ import annotations

from DTO.CambioDTO import CambioDTO
from Logica.PergaminoLogica import PergaminoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from bench.medicion import anotar, medir, nota, verificar

SECCION = "Historial de retroceso (§4.6): diferencias en lista doble  vs  instantáneas del estado"
MUNDOS = (10, 100, 1_000)       # salas cargadas (3 entidades por sala)
ACCIONES = 200                   # acciones del jugador registradas por medición (el historial guarda 5)
TAMANOS_DE_ACCION = (1, 10, 100)


class Entidad:
    """Un enemigo o trampa del mundo sintético: lo único que cambia es su vida."""
    __slots__ = ("vida_actual", "id_sala_actual", "armada")

    def __init__(self, vida: int, sala: int) -> None:
        self.vida_actual, self.id_sala_actual, self.armada = vida, sala, True


class MundoConInstantaneas:
    """ALTERNATIVA DESCARTADA: antes de cada acción copia los campos de todas las entidades; deshacer los restaura."""
    MAX = 5

    def __init__(self, entidades: list) -> None:
        self.entidades = entidades
        self.buffer: list = []

    def antes_de_la_accion(self) -> None:
        foto = [(e.vida_actual, e.id_sala_actual, e.armada) for e in self.entidades]
        self.buffer.append(foto)
        if len(self.buffer) > self.MAX:
            del self.buffer[0]

    def deshacer(self) -> None:
        foto = self.buffer.pop()
        for entidad, (vida, sala, armada) in zip(self.entidades, foto):
            entidad.vida_actual, entidad.id_sala_actual, entidad.armada = vida, sala, armada


def _mundo(salas: int) -> list[Entidad]:
    return [Entidad(100, i // 3) for i in range(salas * 3)]


def _con_diferencias(entidades: list, acciones: int, por_accion: int) -> None:
    retroceso = RetrocesoLogica()
    for a in range(acciones):
        retroceso.iniciar_accion(a)
        for k in range(por_accion):
            entidad = entidades[(a + k) % len(entidades)]
            anterior = entidad.vida_actual
            entidad.vida_actual = anterior - 1
            retroceso.registrar_cambio([CambioDTO(tipo_accion="ACTUALIZAR_VIDA", objeto_afectado=entidad,
                                                  valor_anterior=anterior, valor_nuevo=anterior - 1)])


def _con_instantaneas(mundo: MundoConInstantaneas, acciones: int, por_accion: int) -> None:
    entidades = mundo.entidades
    for a in range(acciones):
        mundo.antes_de_la_accion()
        for k in range(por_accion):
            entidad = entidades[(a + k) % len(entidades)]
            entidad.vida_actual -= 1


def ejecutar(filas: list) -> None:
    retroceso = RetrocesoLogica()
    # Equivalencia: deshacer una acción deja el mundo igual en ambos mecanismos.
    retroceso.reiniciar()
    a, b = _mundo(20), _mundo(20)
    antes = [e.vida_actual for e in a]
    _con_diferencias(a, 1, 5)
    PergaminoLogica(retroceso, []).usar_pergamino()
    otro = MundoConInstantaneas(b)
    _con_instantaneas(otro, 1, 5)
    otro.deshacer()
    verificar(filas, SECCION, "deshacer una acción devuelve el mundo a su estado anterior en ambos",
              [e.vida_actual for e in a] == antes == [e.vida_actual for e in b])

    for salas in MUNDOS:
        for por_accion in (1, 10):
            def registrar_diferencias(entidades):
                retroceso.reiniciar()
                _con_diferencias(entidades, ACCIONES, por_accion)
            anotar(filas, SECCION, f"mundo={salas * 3:>5} entidades  {ACCIONES} acciones de {por_accion:>2} cambio(s)  [diferencias]",
                   medir(registrar_diferencias, lambda: _mundo(salas)))
            anotar(filas, SECCION, f"mundo={salas * 3:>5} entidades  {ACCIONES} acciones de {por_accion:>2} cambio(s)  [instantáneas]",
                   medir(lambda m: _con_instantaneas(m, ACCIONES, por_accion), lambda: MundoConInstantaneas(_mundo(salas))))

    for por_accion in TAMANOS_DE_ACCION:
        def preparar_diferencias():
            retroceso.reiniciar()
            entidades = _mundo(100)
            _con_diferencias(entidades, 1, por_accion)
            return PergaminoLogica(retroceso, [])
        anotar(filas, SECCION, f"deshacer una acción de {por_accion:>3} cambio(s)  (mundo de 300)       [diferencias]",
               medir(lambda p: p.usar_pergamino(), preparar_diferencias))

        def preparar_instantaneas():
            mundo = MundoConInstantaneas(_mundo(100))
            _con_instantaneas(mundo, 1, por_accion)
            return mundo
        anotar(filas, SECCION, f"deshacer una acción de {por_accion:>3} cambio(s)  (mundo de 300)       [instantáneas]",
               medir(lambda m: m.deshacer(), preparar_instantaneas))
    retroceso.reiniciar()
    nota(filas, SECCION, "El historial del juego conserva solo 5 acciones: su memoria no depende de cuánto dure la partida.")
