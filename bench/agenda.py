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
    _reajuste_velocidad(filas)


# --- §5.6 (T072, FR-121): la agenda con decenas de actores y el reajuste de velocidad ---------------------------------

SECCION_REAJUSTE = "Agenda con decenas de actores (§5.6): reajustar_velocidad, barrido del heap  vs  eventos por actor"
ACTORES = (10, 30, 100, 1_000)      # actores con una acción pendiente cada uno (cazadores, errantes, jugador)
TODOS_HASTA = 100                   # el reajuste de TODOS los actores a la vez solo se mide con decenas
LIMITE_CICLO_US = 20_000            # FR-121: 20 ms


class _Actor:
    """Un actor mínimo: lo único que la agenda le pide es un número para la alternativa con índice."""

    def __init__(self, numero: int) -> None:
        self.numero = numero


class AgendaConEventosPorActor(RelojVirtual):
    """Alternativa descartada: cada actor lleva la lista de SUS eventos pendientes (lista de listas indexada por el
    número del actor), así reajustar la velocidad no recorre el heap. A cambio, programar, sacar y reprogramar deben
    mantener el índice. Existe SOLO aquí, para medir."""

    def __init__(self, actores: int) -> None:
        super().__init__()
        self.por_actor: list[list[EventoDTO]] = [[] for _ in range(actores)]

    def insertar_evento(self, evento: EventoDTO) -> None:
        super().insertar_evento(evento)
        if evento.actor is not None:
            self.por_actor[evento.actor.numero].append(evento)

    def _olvidar(self, evento: EventoDTO) -> None:
        if evento.actor is None:
            return
        lista = self.por_actor[evento.actor.numero]
        for i in range(len(lista)):
            if lista[i] is evento:
                del lista[i]
                return

    def quitar_evento(self, evento: EventoDTO) -> bool:
        quitado = super().quitar_evento(evento)
        if quitado:
            self._olvidar(evento)
        return quitado

    def desencolar(self) -> EventoDTO | None:
        evento = super().desencolar()
        if evento is not None:
            self._olvidar(evento)
        return evento

    def reajustar_velocidad(self, actor, velocidad_anterior: int, velocidad_nueva: int) -> None:
        for evento in list(self.por_actor[actor.numero]):
            restante = max(0, evento.tiempo_ejecucion - self.tiempo_actual)
            nuevo_restante = self.restante_por_cambio_de_velocidad(restante, velocidad_anterior, velocidad_nueva)
            self.reprogramar(evento, self.tiempo_actual + nuevo_restante)


def _armar(fabrica, actores: int, intervalos: list[int]):
    """Agenda con una acción por actor y, además, puertas con cierre automático (eventos sin actor)."""
    agenda = fabrica(actores) if fabrica is AgendaConEventosPorActor else fabrica()
    lista = [_Actor(i) for i in range(actores)]
    for i, intervalo in enumerate(intervalos[:actores]):
        agenda.programar(intervalo, lista[i], "MOVER")
    for intervalo in intervalos[actores:]:
        agenda.programar(intervalo, None, "CERRAR_PUERTA")
    return agenda, lista


def _reajuste_velocidad(filas: list, tamanos: tuple = ACTORES, todos_hasta: int = TODOS_HASTA, repeticiones: int = 7) -> None:
    """Mide reajustar_velocidad con la carga de la Parte II (T072). Cambiar la velocidad de un actor ocurre al empezar
    o terminar un efecto; con cazadores, un efecto que afecte a muchos actores a la vez es el peor caso."""
    fabricas = (("barrido del heap (elegida)", RelojVirtual), ("eventos por actor (descartada)", AgendaConEventosPorActor))
    for n in tamanos:
        rng = azar(n + 31)
        intervalos = [rng.randrange(100, 1000) for _ in range(n + n // 2)]

        # Las dos agendas deben terminar con los mismos eventos, en el mismo orden, después de reajustar.
        a, actores_a = _armar(RelojVirtual, n, intervalos)
        b, actores_b = _armar(AgendaConEventosPorActor, n, intervalos)
        for k in range(0, n, 3):
            a.reajustar_velocidad(actores_a[k], 100, 150)
            b.reajustar_velocidad(actores_b[k], 100, 150)
        verificar(filas, SECCION_REAJUSTE, f"{n} actores: ambas agendas sacan los mismos eventos tras reajustar", _vaciar(a) == _vaciar(b))

        for nombre, fabrica in fabricas:
            def preparar(f=fabrica):
                return _armar(f, n, intervalos)
            anotar(filas, SECCION_REAJUSTE, f"{n:>5} actores  reajustar la velocidad de UN actor      [{nombre}]",
                   medir(lambda estado: estado[0].reajustar_velocidad(estado[1][n // 2], 100, 150), preparar, repeticiones=repeticiones))

        if n <= todos_hasta:
            peor = {}
            for nombre, fabrica in fabricas:
                def preparar(f=fabrica):
                    return _armar(f, n, intervalos)

                def todos(estado):
                    agenda, lista = estado
                    for actor in lista:
                        agenda.reajustar_velocidad(actor, 100, 150)
                peor[nombre] = anotar(filas, SECCION_REAJUSTE, f"{n:>5} actores  reajustar a TODOS los actores a la vez [{nombre}]",
                                      medir(todos, preparar, repeticiones=repeticiones))
            verificar(filas, SECCION_REAJUSTE, f"{n} actores: reajustar a todos cabe en el límite de 20 ms (FR-121)",
                      peor["barrido del heap (elegida)"] < LIMITE_CICLO_US)

        for nombre, fabrica in fabricas:
            def preparar_ciclo(f=fabrica):
                return _armar(f, n, intervalos)

            def ciclo(estado, r=azar(n + 77)):
                agenda = estado[0]
                for _ in range(CICLOS):
                    evento = agenda.desencolar()
                    agenda.programar(r.randrange(100, 1000), evento.actor, evento.tipo_accion)
            anotar(filas, SECCION_REAJUSTE, f"{n:>5} actores  {CICLOS} ciclos sacar+programar              [{nombre}]",
                   medir(ciclo, preparar_ciclo, repeticiones=repeticiones))
    nota(filas, SECCION_REAJUSTE, "Cada actor tiene una acción pendiente y hay además n/2 puertas con cierre automático (sin actor). "
                                  "La alternativa mantiene un índice por actor; su costo se ve en los ciclos sacar+programar.")
