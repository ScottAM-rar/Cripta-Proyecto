"""Oráculo de la verificación de resolubilidad (capacidad 003, T028; data-model.md §8).

`verificar_repetida` aplica la regla de la especificación de la forma más directa posible, sin estructuras eficientes:
en cada oleada recorre la cripta DESDE CERO desde la sala inicial con las llaves obtenidas hasta ese momento. Es la
alternativa descartada (O(K · (S + E))) que mide el bench y la referencia de las pruebas de equivalencia (principio III).

La regla sale de spec.md, no del diseño del algoritmo:
- FR-333: una sala es alcanzable si hay un camino desde la sala inicial, respetando el sentido de las salidas, en el que
  cada puerta cerrada que se cruza tiene su llave ya obtenida; una puerta cerrada sin llave no se cruza nunca. Las salidas
  hacia salas que no existen se ignoran (casos límite).
- FR-334: una llave es obtenible cuando alguna de sus ubicaciones (suelo, o sala inicial del enemigo que la suelta) está
  en una sala alcanzable.
- FR-335 (clarificación Q1 del 2026-11-08): el orden se arma por oleadas; una oleada son todas las llaves que se pueden
  obtener antes de tener que abrir otra puerta; dentro de la oleada, por menor sala y luego por id de llave. Si una llave
  es obtenible desde varias salas, cuenta la menor; en esa sala, el suelo antes que un enemigo y, entre enemigos, la
  menor instancia (el reporte no depende del orden de la respuesta).
- FR-332 (clarificación Q1 de la spec): resoluble si se llega a la sala de salida con la llave de salida obtenible.
  Parada igual que el algoritmo (research.md §2): al final de la oleada en que la sala de salida es alcanzable y la llave
  de salida es obtenible (el orden incluye las llaves de esa oleada), o cuando una oleada no agrega ninguna llave nueva.
- FR-337 y FR-338 (clarificación Q3): salas alcanzables crecientes, cantidad de no alcanzables, puertas que separan lo
  alcanzable de lo no alcanzable (por sala de origen creciente y N, S, E, O) con su tipo: SIN_LLAVE, LLAVE_INEXISTENTE,
  CICLO (alguna ubicación de la llave tiene camino desde la sala inicial abriendo todas las puertas) o LLAVE_SIN_CAMINO
  (ninguna lo tiene); y las causas generales en el orden fijo de CAUSAS_EN_ORDEN.

Solo listas (principio I): sin dict, set, sorted() ni .sort(); para ordenar, `ordenar_adaptativo`.
"""
from __future__ import annotations

import random

from DTO.LlavesDTO import UbicacionLlavesDTO
from DTO.MapaDTO import AristaMapaDTO, MapaDTO, SalaMapaDTO
from DTO.ResultadoVerificacionDTO import (CICLO, LLAVE_INEXISTENTE, LLAVE_SALIDA_INALCANZABLE, LLAVE_SALIDA_INEXISTENTE,
                                          LLAVE_SIN_CAMINO, SALIDA_BLOQUEADA, SALIDA_SIN_CAMINO, SIN_LLAVE, BloqueoDTO,
                                          PasoLlaveDTO, ResultadoVerificacion)
from Logica.MapaCripta import MapaCripta
from Logica.ordenamiento import ordenar_adaptativo

LETRAS_EN_ORDEN = ("N", "S", "E", "O")
NOMBRES = ("norte", "sur", "este", "oeste")


# ------------------------------------------------------------------------------------------------ armado de mapas

def mapa_desde_salas(salas: list[dict]) -> MapaCripta:
    """MapaCripta a partir de un esqueleto en el formato de la API (salidas con "sala", "cerrada" y "llave"), sin pasar
    por los adaptadores. Costo 100 en todas las salidas (la verificación no lo mira). Las salidas en orden N, S, E, O."""
    mayor = 0
    for sala in salas:
        if sala["id"] > mayor:
            mayor = sala["id"]
    lista: list = [None] * (mayor + 1)
    for sala in salas:
        aristas = []
        salidas = sala.get("salidas") or {}
        for posicion in range(len(LETRAS_EN_ORDEN)):
            letra = LETRAS_EN_ORDEN[posicion]
            if letra in salidas:
                datos = salidas[letra]
                aristas.append(AristaMapaDTO(NOMBRES[posicion], datos["sala"], 100, datos.get("cerrada", False),
                                             llave=datos.get("llave")))
        lista[sala["id"]] = SalaMapaDTO(sala["id"], aristas)
    return MapaCripta(MapaDTO(lista))


def poner_puerta(salas: list[dict], origen: int, destino: int, llave: str | None, dos_sentidos: bool = True) -> None:
    """Cierra la salida origen -> destino (y la inversa si `dos_sentidos`) y le asigna `llave` (None: sin llave)."""
    pares = [(origen, destino), (destino, origen)] if dos_sentidos else [(origen, destino)]
    for a, b in pares:
        for sala in salas:
            if sala["id"] != a:
                continue
            for salida in sala["salidas"].values():
                if salida["sala"] == b:
                    salida["cerrada"] = True
                    if llave is not None:
                        salida["llave"] = llave


def ubicaciones(cripta_id: str, entradas: list[tuple]) -> UbicacionLlavesDTO:
    """UbicacionLlavesDTO desde una lista de (id, sala, enemigo o None)."""
    return UbicacionLlavesDTO(cripta_id, None, [e[0] for e in entradas], [e[1] for e in entradas],
                              [e[2] for e in entradas])


# ------------------------------------------------------------------------------------------------ oráculo

def _existe(mapa: MapaCripta, sala) -> bool:
    return isinstance(sala, int) and not isinstance(sala, bool) and 0 <= sala < mapa.tamano and mapa.existe[sala]


def _contiene(lista: list, valor) -> bool:
    for elemento in lista:
        if elemento == valor:
            return True
    return False


def _alcanzables(mapa: MapaCripta, sala_inicial: int, obtenidas: list[str] | None) -> list[bool]:
    """Recorrido desde cero. `obtenidas` None: todas las puertas abiertas (camino «ignorando las puertas»)."""
    alcanzable = [False] * mapa.tamano
    alcanzable[sala_inicial] = True
    pendientes = [sala_inicial]
    siguiente = 0
    while siguiente < len(pendientes):
        sala = pendientes[siguiente]
        siguiente += 1
        for arista in mapa.salidas(sala):
            destino = arista.destino
            if not _existe(mapa, destino) or alcanzable[destino]:
                continue
            if arista.cerrada_inicial and obtenidas is not None:
                if arista.llave is None or not _contiene(obtenidas, arista.llave):
                    continue
            alcanzable[destino] = True
            pendientes.append(destino)
    return alcanzable


def _mejor_ubicacion(actual: tuple | None, candidata: tuple) -> tuple:
    """Entre dos ubicaciones (sala, enemigo) de la misma llave: menor sala; en la misma sala, el suelo (None) antes que
    un enemigo; entre enemigos, la menor instancia."""
    if actual is None:
        return candidata
    if candidata[0] != actual[0]:
        return candidata if candidata[0] < actual[0] else actual
    if actual[1] is None:
        return actual
    if candidata[1] is None:
        return candidata
    return candidata if candidata[1] < actual[1] else actual


def _salas_de(llaves: UbicacionLlavesDTO, id_llave: str) -> list[int]:
    salas = []
    for i in range(llaves.cantidad()):
        if llaves.ids[i] == id_llave:
            salas.append(llaves.salas[i])
    ordenadas = ordenar_adaptativo(salas)
    sin_repetir: list[int] = []
    for sala in ordenadas:
        if not sin_repetir or sin_repetir[-1] != sala:
            sin_repetir.append(sala)
    return sin_repetir


def verificar_repetida(mapa: MapaCripta, sala_inicial: int, sala_salida: int, llave_salida: str | None,
                       llaves: UbicacionLlavesDTO, cripta_id: str = "") -> ResultadoVerificacion:
    if not _existe(mapa, sala_inicial):
        return ResultadoVerificacion(cripta_id, None, llave_salida=llave_salida, sala_salida=sala_salida,
                                     motivo_error=f"Datos inválidos en la cripta {cripta_id}: la sala inicial "
                                                  f"{sala_inicial} no existe en el mapa.")
    if not _existe(mapa, sala_salida):
        return ResultadoVerificacion(cripta_id, None, llave_salida=llave_salida, sala_salida=sala_salida,
                                     motivo_error=f"Datos inválidos en la cripta {cripta_id}: la sala de salida "
                                                  f"{sala_salida} no existe en el mapa.")
    obtenidas: list[str] = []
    orden: list[PasoLlaveDTO] = []
    while True:
        alcanzable = _alcanzables(mapa, sala_inicial, obtenidas)
        # Llaves nuevas de la oleada: ids obtenibles todavía no obtenidos, con su mejor ubicación alcanzable.
        ids_nuevos: list[str] = []
        mejores: list = []
        for i in range(llaves.cantidad()):
            id_llave, sala, enemigo = llaves.ids[i], llaves.salas[i], llaves.enemigos[i]
            if not _existe(mapa, sala) or not alcanzable[sala] or _contiene(obtenidas, id_llave):
                continue
            posicion = -1
            for j in range(len(ids_nuevos)):
                if ids_nuevos[j] == id_llave:
                    posicion = j
            if posicion == -1:
                ids_nuevos.append(id_llave)
                mejores.append((sala, enemigo))
            else:
                mejores[posicion] = _mejor_ubicacion(mejores[posicion], (sala, enemigo))
        oleada = ordenar_adaptativo([(mejores[j][0], ids_nuevos[j], mejores[j][1]) for j in range(len(ids_nuevos))],
                                    key=lambda t: (t[0], t[1]))
        salida_obtenible = llave_salida is not None and (_contiene(obtenidas, llave_salida)
                                                         or _contiene(ids_nuevos, llave_salida))
        if alcanzable[sala_salida] and salida_obtenible:
            for sala, id_llave, enemigo in oleada:
                orden.append(PasoLlaveDTO(id_llave, sala, enemigo))
            return ResultadoVerificacion(cripta_id, True, orden=orden,
                                         salas_alcanzables=[s for s in range(mapa.tamano) if mapa.existe[s] and alcanzable[s]],
                                         llave_salida=llave_salida, sala_salida=sala_salida)
        if not oleada:
            return _no_resoluble(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id, alcanzable, obtenidas)
        for sala, id_llave, enemigo in oleada:
            orden.append(PasoLlaveDTO(id_llave, sala, enemigo))
            obtenidas.append(id_llave)


def _no_resoluble(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id, alcanzable, obtenidas):
    sin_puertas = _alcanzables(mapa, sala_inicial, None)
    salas_alcanzables = [s for s in range(mapa.tamano) if mapa.existe[s] and alcanzable[s]]
    no_alcanzables = 0
    for s in range(mapa.tamano):
        if mapa.existe[s] and not alcanzable[s]:
            no_alcanzables += 1
    bloqueos: list[BloqueoDTO] = []
    for sala in salas_alcanzables:
        for arista in mapa.salidas(sala):
            destino = arista.destino
            if not _existe(mapa, destino) or alcanzable[destino]:
                continue
            if arista.llave is None:
                bloqueos.append(BloqueoDTO(sala, arista.direccion, destino, None, [], SIN_LLAVE))
                continue
            salas = _salas_de(llaves, arista.llave)
            if not salas:
                tipo = LLAVE_INEXISTENTE
            else:
                tipo = LLAVE_SIN_CAMINO
                for s in salas:
                    if _existe(mapa, s) and sin_puertas[s]:
                        tipo = CICLO
            bloqueos.append(BloqueoDTO(sala, arista.direccion, destino, arista.llave, salas, tipo))
    llave_salida_existe = llave_salida is not None and len(_salas_de(llaves, llave_salida)) > 0
    causas: list[str] = []
    if not llave_salida_existe:
        causas.append(LLAVE_SALIDA_INEXISTENTE)
    if not sin_puertas[sala_salida]:
        causas.append(SALIDA_SIN_CAMINO)
    elif not alcanzable[sala_salida]:
        causas.append(SALIDA_BLOQUEADA)
    if alcanzable[sala_salida] and llave_salida_existe:
        causas.append(LLAVE_SALIDA_INALCANZABLE)
    return ResultadoVerificacion(cripta_id, False, salas_alcanzables=salas_alcanzables,
                                 salas_no_alcanzables=no_alcanzables, bloqueos=bloqueos, causas=causas,
                                 llave_salida=llave_salida, sala_salida=sala_salida)


# ------------------------------------------------------------------------------------------------ criptas al azar

def cripta_al_azar_con_llaves(semilla: int, salas: int = 60):
    """(mapa, sala_inicial, sala_salida, llave_salida, llaves) deterministas por semilla: grafo dirigido al azar con
    ciclos, salidas de un solo sentido y salidas hacia salas inexistentes; puertas cerradas al azar (algunas sin llave);
    llaves con 0, 1 o 2 ubicaciones (algunas en enemigos) y algunas llaves que no existen."""
    from tests_labs.cripta_sintetica import esqueleto_dirigido_aleatorio
    azar = random.Random(1000 + semilla)
    esqueleto = esqueleto_dirigido_aleatorio(salas, semilla, fraccion_un_sentido=0.2, fraccion_inexistentes=0.05)
    ids_salas = [sala["id"] for sala in esqueleto]
    nombres = ["itm_llave_" + letra for letra in "qwertyuiopasdfgh"]
    azar.shuffle(nombres)                                   # el orden de los ids no sigue el de creación
    for sala in esqueleto:
        for letra in LETRAS_EN_ORDEN:
            salida = sala["salidas"].get(letra)
            if salida is None or azar.random() >= 0.35:
                continue
            salida["cerrada"] = True
            if azar.random() >= 0.1:
                salida["llave"] = nombres[azar.randrange(len(nombres))]
    entradas: list[tuple] = []
    enemigo = 0
    for nombre in nombres:
        cuantas = azar.choice((0, 1, 1, 2))
        for _ in range(cuantas):
            sala = ids_salas[azar.randrange(len(ids_salas))]
            instancia = None
            if azar.random() < 0.3:
                enemigo += 1
                instancia = f"e-{enemigo}"
            if not _contiene(entradas, (nombre, sala, instancia)):
                entradas.append((nombre, sala, instancia))
    llave_salida = nombres[azar.randrange(len(nombres))]
    sala_inicial = ids_salas[azar.randrange(len(ids_salas))]
    sala_salida = ids_salas[azar.randrange(len(ids_salas))]
    return mapa_desde_salas(esqueleto), sala_inicial, sala_salida, llave_salida, ubicaciones("cripta-01", entradas)
