"""Referencia ingenua del conocimiento del jugador (capacidad 002) y verificador de invariantes.

La referencia reconstruye DESDE CERO, con bucles simples, lo que el jugador sabe tras una historia de observaciones; se compara
con el conocimiento incremental (principio III, SC-003). No usa `dict`/`set`.

Una historia es una lista de eventos:
    ("entrar", sala, antorcha, reales)   `reales`: lista de (origen, d, cerrada) con el estado real de las salidas propias
                                          y entrantes de `sala` en ese instante (ver `capturar_reales`)
    ("cambio", origen, d, cerrada)        una puerta cambió junto al jugador
"""
from __future__ import annotations

DIRECCIONES = ("norte", "sur", "este", "oeste")


def indice(direccion) -> int:
    for i in range(4):
        if DIRECCIONES[i] == direccion:
            return i
    raise ValueError(direccion)


def capturar_reales(mapa, salas, sala: int) -> list:
    """Estado real (origen, d, cerrada) de las salidas que salen de `sala` y de las que llegan a ella, ahora."""
    reales = []
    for arista in list(mapa.salidas(sala)) + list(mapa.entrantes(sala)):
        reales.append((arista.origen, indice(arista.direccion), not mapa.esta_abierta(arista, salas)))
    return reales


def reconstruir(mapa, historia: list):
    """Devuelve (estado, puertas, exploradas) tras repetir `historia` sobre un conocimiento vacío."""
    estado = [0] * mapa.tamano
    puertas = [0] * (4 * mapa.tamano)
    exploradas: list[int] = []

    def explorar(sala):
        if estado[sala] != 2:
            estado[sala] = 2
            exploradas.append(sala)

    for evento in historia:
        if evento[0] == "entrar":
            _, sala, antorcha, reales = evento
            explorar(sala)
            for origen, d, cerrada in reales:
                puertas[origen * 4 + d] = 2 if cerrada else 1
            if antorcha:
                for arista in mapa.salidas(sala):
                    if 0 <= arista.destino < mapa.tamano and mapa.existe[arista.destino]:
                        explorar(arista.destino)
        else:
            _, origen, d, cerrada = evento
            puertas[origen * 4 + d] = 2 if cerrada else 1
    # avistada por definición (FR-203): no explorada y destino de una salida de una explorada
    for sala in range(mapa.tamano):
        if estado[sala] == 2:
            for arista in mapa.salidas(sala):
                if 0 <= arista.destino < mapa.tamano and mapa.existe[arista.destino] and estado[arista.destino] == 0:
                    estado[arista.destino] = 1
    return estado, puertas, exploradas


def diferencias(conocimiento, referencia) -> list:
    """Textos que describen en qué difiere el conocimiento de la referencia (vacío si son idénticos)."""
    estado, puertas, exploradas = referencia
    fallos = []
    if list(conocimiento.estado) != estado:
        fallos.append("estados de sala distintos")
    if list(conocimiento.puertas) != puertas:
        fallos.append("puertas recordadas distintas")
    if list(conocimiento.exploradas) != exploradas:
        fallos.append("orden de exploradas distinto")
    return fallos


def comprobar_invariantes(conocimiento, mapa, salas, jugador, con_puertas: bool = True) -> list:
    """Violaciones de I1 a I6 de data-model.md (lista vacía si todo vale). Con `con_puertas` falso solo I2 a I5."""
    fallos = []
    estado, puertas, exploradas = conocimiento.estado, conocimiento.puertas, conocimiento.exploradas
    # I2
    for sala in range(mapa.tamano):
        esta = False
        cuantas = 0
        for e in exploradas:
            if e == sala:
                esta = True
                cuantas += 1
        if (estado[sala] == 2) != esta or cuantas > 1:
            fallos.append(f"I2: sala {sala}")
    # I3
    for sala in range(mapa.tamano):
        esperada = False
        if mapa.existe[sala] and estado[sala] != 2:
            for origen in range(mapa.tamano):
                if estado[origen] == 2:
                    for arista in mapa.salidas(origen):
                        if arista.destino == sala:
                            esperada = True
        if (estado[sala] == 1) != esperada:
            fallos.append(f"I3: sala {sala}")
    # I4
    if estado[jugador.id_sala_actual] != 2:
        fallos.append("I4: la sala del jugador no está explorada")
    # I5
    for sala in range(mapa.tamano):
        for d in range(4):
            if puertas[sala * 4 + d] != 0:
                existe = False
                for arista in mapa.salidas(sala):
                    if indice(arista.direccion) == d:
                        existe = True
                if not existe:
                    fallos.append(f"I5: puerta ({sala}, {d}) sin salida")
    if con_puertas:
        actual = jugador.id_sala_actual
        # I1
        for arista in list(mapa.salidas(actual)) + list(mapa.entrantes(actual)):
            real = 1 if mapa.esta_abierta(arista, salas) else 2
            recordada = puertas[arista.origen * 4 + indice(arista.direccion)]
            if recordada != real:
                fallos.append(f"I1: puerta ({arista.origen}, {arista.direccion}) recordada {recordada}, real {real}")
        # I6
        for valor in puertas:
            if valor not in (0, 1, 2):
                fallos.append("I6: valor de puerta inválido")
                break
    return fallos
