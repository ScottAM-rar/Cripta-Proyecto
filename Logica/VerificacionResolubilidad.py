"""Verificación de resolubilidad de una cripta (capacidad 003).

- `verificar_resolubilidad(...)`: función pura que decide con el mapa, la sala inicial, la sala de salida, la llave de
  salida y la ubicación de llaves de la capacidad 009 (research.md §2, §3 y §6; data-model.md §4).
- `verificar(fuente, cripta_id, llaves=None)`: junta esos datos desde la fuente (solo el contrato del modelo,
  FuenteCripta) y llama a la función pura; traduce los fallos de datos a `motivo_error` (research.md §8).
- `CriptaNoResoluble`: la lanza el inicio de partida sin `--forzar` (FR-339).

No importa adaptadores (principio IV). Es la operación única que usan `--verificar` y el inicio de partida (FR-344).

Algoritmo: UN solo recorrido incremental por oleadas desde la sala inicial (research.md §2).
- La frontera es una ColaCircular. Al alcanzar una sala, cada ubicación de llave de esa sala (suelo o enemigo que inicia
  ahí, FR-334) entra a un MonticuloMinimo de pendientes con la clave (sala, número de llave).
- Una salida abierta se cruza; una cerrada sin llave nunca (FR-333); una cerrada cuya llave ya se obtuvo se cruza; si no,
  la arista espera en `esperando[número de llave]`.
- Cuando la cola se vacía termina la oleada: si la sala de salida es alcanzable y la llave de salida es obtenible, las
  llaves de la oleada pasan al orden y la cripta es resoluble (FR-332); si no hay pendientes, no es resoluble; si no,
  todas las llaves de la oleada pasan al orden, se marcan obtenidas y se liberan sus aristas en espera.
Como los números de llave salen de un índice ordenado por id, el montículo entrega el desempate de FR-335: menor sala y,
dentro de la sala, menor id de llave. Cuál ubicación se informa de una llave (suelo antes que enemigo, menor instancia)
se decide aparte, sin depender de cómo desempata el montículo ante claves iguales.

Costo: O(S + E + L log L + (L + E) log K) — cada sala entra una vez a la cola, cada salida se examina una vez y se libera
a lo sumo una vez, cada ubicación entra una vez al montículo, y las llaves se resuelven con búsqueda binaria.
Sin dict, set, heapq, bisect, collections, sorted() ni .sort() (principio I).
"""
from __future__ import annotations

from DTO.LlavesDTO import UbicacionLlavesDTO
from DTO.ResultadoVerificacionDTO import (CICLO, LLAVE_INEXISTENTE, LLAVE_SALIDA_INALCANZABLE, LLAVE_SALIDA_INEXISTENTE,
                                          LLAVE_SIN_CAMINO, SALIDA_BLOQUEADA, SALIDA_SIN_CAMINO, SIN_LLAVE, BloqueoDTO,
                                          PasoLlaveDTO, ResultadoVerificacion)
from Logica.ColaCircular import ColaCircular
from Logica.FuenteCripta import DatoLocalFaltante, LlavesNoDisponibles
from Logica.IndiceLlaves import IndiceLlaves
from Logica.MapaCripta import MapaCripta
from Logica.MonticuloMinimo import MonticuloMinimo
from Logica.ordenamiento import ordenar_adaptativo
from Logica.RecorridoPorNiveles import RecorridoPorNiveles
from Logica.ReporteVerificacion import lineas_reporte


class CriptaNoResoluble(RuntimeError):
    """Se intentó iniciar una partida sin `--forzar` en una cripta no resoluble (FR-339). El mensaje es el reporte."""

    def __init__(self, resultado: ResultadoVerificacion) -> None:
        self.resultado = resultado
        super().__init__("\n".join(lineas_reporte(resultado)))


def _existe(mapa: MapaCripta, sala) -> bool:
    return isinstance(sala, int) and not isinstance(sala, bool) and 0 <= sala < mapa.tamano and mapa.existe[sala]


def _mejor_ubicacion(llaves: UbicacionLlavesDTO, posiciones: list[int], sala: int) -> str | None:
    """Enemigo que se informa para una llave obtenida en `sala`: entre sus ubicaciones en esa sala, el suelo (None)
    antes que un enemigo y, entre enemigos, la menor instancia (FR-335: no depende del orden de la respuesta)."""
    mejor = None
    hay = False
    for posicion in posiciones:
        if llaves.salas[posicion] != sala:
            continue
        enemigo = llaves.enemigos[posicion]
        if enemigo is None:
            return None
        if not hay or enemigo < mejor:
            mejor = enemigo
            hay = True
    return mejor


def _sin_repetir(valores: list[int]) -> list[int]:
    ordenados = ordenar_adaptativo(valores)
    resultado: list[int] = []
    for valor in ordenados:
        if not resultado or resultado[-1] != valor:
            resultado.append(valor)
    return resultado


def verificar_resolubilidad(mapa: MapaCripta, sala_inicial: int, sala_salida: int, llave_salida: str | None,
                            llaves: UbicacionLlavesDTO, cripta_id: str = "") -> ResultadoVerificacion:
    """Decide si la cripta es resoluble (FR-332 a FR-338). Pura: sin E/S ni solicitudes; mismo resultado para los
    mismos datos (FR-335)."""
    if not _existe(mapa, sala_inicial):
        return ResultadoVerificacion(cripta_id, None, llave_salida=llave_salida, sala_salida=sala_salida,
                                     motivo_error=f"Datos inválidos en la cripta {cripta_id}: la sala inicial "
                                                  f"{sala_inicial} no existe en el mapa.")
    if not _existe(mapa, sala_salida):
        return ResultadoVerificacion(cripta_id, None, llave_salida=llave_salida, sala_salida=sala_salida,
                                     motivo_error=f"Datos inválidos en la cripta {cripta_id}: la sala de salida "
                                                  f"{sala_salida} no existe en el mapa.")
    tamano = mapa.tamano

    # Índice de llaves: las de las ubicaciones, las de las puertas y la llave de salida (research.md §4).
    todos: list[str] = list(llaves.ids)
    for sala in range(tamano):
        for arista in mapa.salidas(sala):
            if arista.llave is not None:
                todos.append(arista.llave)
    if llave_salida is not None:
        todos.append(llave_salida)
    indice = IndiceLlaves(todos)
    k = indice.cantidad()

    numero_de: list[int] = [indice.numero(id_llave) for id_llave in llaves.ids]
    ubicaciones_por_llave: list[list[int]] = [[] for _ in range(k)]
    ubicaciones_por_sala: list[list[int]] = [[] for _ in range(tamano)]
    for posicion in range(llaves.cantidad()):
        ubicaciones_por_llave[numero_de[posicion]].append(posicion)
        if _existe(mapa, llaves.salas[posicion]):
            ubicaciones_por_sala[llaves.salas[posicion]].append(posicion)

    alcanzable = [False] * tamano
    obtenible = [False] * k
    obtenida = [False] * k
    esperando: list[list] = [[] for _ in range(k)]
    cola = ColaCircular()
    pendientes = MonticuloMinimo()         # clave (sala, número de llave); sus parámetros se llaman (costo, sala)
    numero_salida = indice.numero(llave_salida) if llave_salida is not None else -1

    def alcanzar(sala: int) -> None:
        alcanzable[sala] = True
        cola.agregar(sala)
        for posicion in ubicaciones_por_sala[sala]:
            numero = numero_de[posicion]
            if not obtenida[numero]:
                obtenible[numero] = True
                pendientes.insertar(sala, numero)

    def oleada_en_orden() -> list[tuple[int, int]]:
        """Saca TODOS los pendientes de la oleada, en orden, antes de liberar nada: lo que se libere después es de la
        oleada siguiente. Una llave obtenible desde varias salas queda con la menor (la primera que sale); las demás
        entradas de esa llave se descartan con la marca `obtenida`, en O(1)."""
        sacadas: list[tuple[int, int]] = []
        while not pendientes.vacio():
            sala, numero = pendientes.extraer_minimo()
            if not obtenida[numero]:
                obtenida[numero] = True
                sacadas.append((sala, numero))
        return sacadas

    def pasar_al_orden(oleada: list[tuple[int, int]]) -> None:
        for sala, numero in oleada:
            orden.append(PasoLlaveDTO(indice.id_de(numero), sala,
                                      _mejor_ubicacion(llaves, ubicaciones_por_llave[numero], sala)))

    orden: list[PasoLlaveDTO] = []
    alcanzar(sala_inicial)
    while True:
        while not cola.vacia():
            sala = cola.sacar()
            for arista in mapa.salidas(sala):
                destino = arista.destino
                if not _existe(mapa, destino) or alcanzable[destino]:
                    continue
                if not arista.cerrada_inicial:
                    alcanzar(destino)
                elif arista.llave is None:
                    continue                                    # cerrada sin llave: nunca se cruza (FR-333)
                else:
                    numero = indice.numero(arista.llave)
                    if obtenida[numero]:
                        alcanzar(destino)
                    else:
                        esperando[numero].append(arista)
        salida_obtenible = numero_salida != -1 and (obtenida[numero_salida] or obtenible[numero_salida])
        if alcanzable[sala_salida] and salida_obtenible:
            pasar_al_orden(oleada_en_orden())
            return ResultadoVerificacion(cripta_id, True, orden=orden,
                                         salas_alcanzables=[s for s in range(tamano) if mapa.existe[s] and alcanzable[s]],
                                         llave_salida=llave_salida, sala_salida=sala_salida)
        if pendientes.vacio():
            return _no_resoluble(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id, alcanzable, indice,
                                 ubicaciones_por_llave, numero_salida)
        oleada = oleada_en_orden()
        pasar_al_orden(oleada)
        for _, numero in oleada:                                 # liberar las puertas que esperaban estas llaves
            for arista in esperando[numero]:
                if not alcanzable[arista.destino]:
                    alcanzar(arista.destino)
            esperando[numero] = []


def _no_resoluble(mapa: MapaCripta, sala_inicial: int, sala_salida: int, llave_salida: str | None,
                  llaves: UbicacionLlavesDTO, cripta_id: str, alcanzable: list[bool], indice: IndiceLlaves,
                  ubicaciones_por_llave: list[list[int]], numero_salida: int) -> ResultadoVerificacion:
    """Salas alcanzables, bloqueos y causas (FR-337, FR-338; research.md §6)."""
    tamano = mapa.tamano
    sin_puertas = [False] * tamano                               # camino ignorando las puertas: un solo recorrido
    for sala in RecorridoPorNiveles(mapa).recorrer(sala_inicial).salas:
        sin_puertas[sala] = True
    salas_alcanzables: list[int] = []
    no_alcanzables = 0
    for sala in range(tamano):
        if mapa.existe[sala]:
            if alcanzable[sala]:
                salas_alcanzables.append(sala)
            else:
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
            posiciones = ubicaciones_por_llave[indice.numero(arista.llave)]
            salas = _sin_repetir([llaves.salas[p] for p in posiciones])
            if not salas:
                tipo = LLAVE_INEXISTENTE
            else:
                tipo = LLAVE_SIN_CAMINO
                for s in salas:
                    if _existe(mapa, s) and sin_puertas[s]:
                        tipo = CICLO
                        break
            bloqueos.append(BloqueoDTO(sala, arista.direccion, destino, arista.llave, salas, tipo))
    llave_salida_existe = numero_salida != -1 and len(ubicaciones_por_llave[numero_salida]) > 0
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


class DatoGeneralFaltante(Exception):
    """Los datos generales de la cripta no traen un campo que la verificación necesita (T065, FR-343)."""


def _dato_general(obtener, cripta_id: str, campo: str):
    """Lee un campo de los datos generales con la operación de la fuente. Si la fuente lo lee con [] y el campo no
    está, el KeyError se traduce a un error de datos que nombra la cripta y el campo (FR-343); no se cambia el
    adaptador. Solo se traduce el KeyError de este campo: uno de otra clave no se oculta."""
    try:
        return obtener(cripta_id)
    except KeyError as error:
        if error.args != (campo,):
            raise
        raise DatoGeneralFaltante(f"Datos inválidos en la cripta {cripta_id}: faltan los datos generales «{campo}».")


def verificar(fuente, cripta_id: str, llaves: UbicacionLlavesDTO | None = None) -> ResultadoVerificacion:
    """Verifica la cripta con los datos de `fuente` (FuenteCripta). `llaves`: las que ya pidió la partida, para no
    volver a pedirlas (FR-341). Nunca lanza por falta de datos ni inventa un resultado: devuelve resoluble=None con
    motivo_error (FR-343, research.md §8)."""
    try:
        if not fuente.existe_cripta(cripta_id):
            return ResultadoVerificacion(cripta_id, None, motivo_error=f"La cripta {cripta_id} no existe.")
        mapa = MapaCripta(fuente.obtener_mapa(cripta_id))
        sala_inicial = _dato_general(fuente.obtener_sala_inicial, cripta_id, "sala_inicial")
        sala_salida = _dato_general(fuente.obtener_sala_salida, cripta_id, "sala_salida")
        llave_salida = fuente.obtener_llave_salida(cripta_id)
        if llaves is None:
            llaves = fuente.ubicacion_llaves(cripta_id)
    except (LlavesNoDisponibles, DatoLocalFaltante, DatoGeneralFaltante) as error:
        return ResultadoVerificacion(cripta_id, None, motivo_error=str(error))
    except (RuntimeError, OSError) as error:
        return ResultadoVerificacion(cripta_id, None, motivo_error=f"No se pudieron obtener los datos de la cripta "
                                                                   f"{cripta_id}: {str(error).rstrip('.')}.")
    return verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id)
