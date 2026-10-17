"""§4.1 Agenda de eventos: heap con posición (el del juego) contra una lista ordenada con búsqueda binaria.

La lista ordenada existe SOLO aquí, para medir la alternativa descartada. Se guarda de mayor a menor para que sacar el
siguiente sea quitar el último elemento; insertar y cancelar buscan su sitio con búsqueda binaria y desplazan elementos.
"""
from __future__ import annotations

from DTO.EventoDTO import EventoDTO
from Logica.RelojVirtual import RelojVirtual
from bench.datos import azar
from bench.medicion import anotar, medir, nota, verificar

SECCION = "Agenda de eventos (§4.1): heap con posición  vs  lista ordenada"
TAMANOS = (100, 1_000, 10_000)
CICLOS = 1_000          # pares sacar + programar por medición del "régimen estable"


class AgendaListaOrdenada:
    """Misma interfaz que RelojVirtual para lo que se mide."""

    def __init__(self) -> None:
        self.tiempo_actual = 0
        self.secuencia_actual = 0
        self.lista: list[EventoDTO] = []          # de mayor a menor: el siguiente evento es el último

    @staticmethod
    def _antes(a: EventoDTO, b: EventoDTO) -> bool:
        if a.tiempo_ejecucion != b.tiempo_ejecucion:
            return a.tiempo_ejecucion < b.tiempo_ejecucion
        return a.id_secuencia < b.id_secuencia

    def _posicion(self, evento: EventoDTO) -> int:
        """Primer índice cuyo elemento es MENOR que `evento` (la lista va de mayor a menor)."""
        bajo, alto = 0, len(self.lista)
        while bajo < alto:
            medio = (bajo + alto) // 2
            if self._antes(self.lista[medio], evento):
                alto = medio
            else:
                bajo = medio + 1
        return bajo

    def programar(self, intervalo, actor, tipo_accion, datos_extra=None) -> EventoDTO:
        self.secuencia_actual += 1
        evento = EventoDTO(self.tiempo_actual + intervalo, self.secuencia_actual, actor, tipo_accion, datos_extra or [])
        self.lista.insert(self._posicion(evento), evento)
        return evento

    def desencolar(self) -> EventoDTO | None:
        if not self.lista:
            return None
        evento = self.lista.pop()
        self.tiempo_actual = evento.tiempo_ejecucion
        return evento

    def quitar_evento(self, evento: EventoDTO) -> bool:
        posicion = self._posicion(evento) - 1
        if 0 <= posicion < len(self.lista) and self.lista[posicion] is evento:
            del self.lista[posicion]
            return True
        return False


def _llenar(agenda, intervalos: list[int]) -> list[EventoDTO]:
    return [agenda.programar(intervalo, None, "BENCH") for intervalo in intervalos]


def _vaciar(agenda) -> list[tuple[int, int]]:
    salida = []
    while True:
        evento = agenda.desencolar()
        if evento is None:
            return salida
        salida.append((evento.tiempo_ejecucion, evento.id_secuencia))


def ejecutar(filas: list) -> None:
    rng = azar(1)
    # Las dos agendas deben ejecutar los eventos en el mismo orden (con empates incluidos).
    intervalos = [rng.randrange(1, 200) for _ in range(2_000)]
    a, b = RelojVirtual(), AgendaListaOrdenada()
    _llenar(a, intervalos)
    _llenar(b, intervalos)
    verificar(filas, SECCION, "ambas sacan los eventos en el mismo orden (2 000 eventos con empates)", _vaciar(a) == _vaciar(b))

    for n in TAMANOS:
        rng = azar(n)
        intervalos = [rng.randrange(1, 1000) for _ in range(n)]
        orden_de_baja = list(range(n))
        rng.shuffle(orden_de_baja)
        mitad = orden_de_baja[: n // 2]
        repeticiones = 5 if n >= 10_000 else 7

        for nombre, fabrica in (("heap con posición", RelojVirtual), ("lista ordenada", AgendaListaOrdenada)):
            anotar(filas, SECCION, f"N={n:>6}  programar N eventos          [{nombre}]",
                   medir(lambda: _llenar(fabrica(), intervalos), repeticiones=repeticiones))

            def preparar_llena(f=fabrica):
                agenda = f()
                _llenar(agenda, intervalos)
                return agenda
            anotar(filas, SECCION, f"N={n:>6}  sacar los N eventos          [{nombre}]",
                   medir(_vaciar, preparar_llena, repeticiones=repeticiones))

            def preparar_con_eventos(f=fabrica):
                agenda = f()
                return agenda, _llenar(agenda, intervalos)
            anotar(filas, SECCION, f"N={n:>6}  cancelar N/2 eventos         [{nombre}]",
                   medir(lambda estado: [estado[0].quitar_evento(estado[1][i]) for i in mitad],
                         preparar_con_eventos, repeticiones=repeticiones))

            def ciclo(agenda, r=azar(n + 7)):
                for _ in range(CICLOS):
                    evento = agenda.desencolar()
                    agenda.programar(r.randrange(1, 1000), evento.actor, "BENCH")
            anotar(filas, SECCION, f"N={n:>6}  {CICLOS} ciclos sacar+programar   [{nombre}]",
                   medir(ciclo, preparar_llena, repeticiones=repeticiones))
    nota(filas, SECCION, "Los ciclos sacar+programar son lo que hace el juego en cada evento; con N grande se ve cómo escala cada estructura.")
