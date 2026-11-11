"""Verificación de resolubilidad (capacidad 003; FR-345, FR-346; contracts/bench-resolubilidad.md).

  A. Estrategias en la cadena de llaves encadenadas, n = 300 y n = 3 000: recorrido incremental por oleadas (elegido)
     frente a `verificar_repetida` del oráculo (alternativa descartada: recorre desde cero en cada oleada). FALLA si
     los dos resultados difieren (principio III).
  B. Índice de llaves: búsqueda binaria de IndiceLlaves (elegida) frente a búsqueda lineal, K = 100, 1 000 y 10 000.
     INFORMATIVA.
  C. Límite: el incremental en una cadena de n = 5 000 y en una rejilla de 70 × 70 con puertas y llaves al azar.
     FALLA si alguna supera 200 ms (FR-345).
  D. Crecimiento: razón t(3 000) / t(300) de cada estrategia. FALLA si la del incremental supera 20, el doble del
     factor de tamaño (FR-346, SC-007); la de la repetida solo se informa.

Se mide la función pura `verificar_resolubilidad` con `time.perf_counter_ns`, con el MapaCripta y la UbicacionLlavesDTO
ya construidos (los datos «ya descargados»). Criptas sintéticas deterministas por semilla; sin red, vista ni caché del
usuario. Sin dict, set, heapq, bisect, collections, sorted() ni .sort(): la mediana usa el ordenamiento propio.
"""
from __future__ import annotations

import random
import time

from bench.datos import SEMILLA
from bench.medicion import nota, texto, verificar
from Logica.IndiceLlaves import IndiceLlaves
from Logica.ordenamiento import insertion_sort
from Logica.VerificacionResolubilidad import verificar_resolubilidad
from tests_labs.cripta_sintetica import esqueleto_llaves_encadenadas, esqueleto_rejilla
from tests_labs.referencia_resolubilidad import mapa_desde_salas, ubicaciones, verificar_repetida

SECCION_A = "Resolubilidad (A): incremental frente a recorrido repetido, cadena de llaves encadenadas"
SECCION_B = "Resolubilidad (B): índice de llaves, búsqueda binaria frente a búsqueda lineal (INFORMATIVA)"
SECCION_C = "Resolubilidad (C): límite de 200 ms del incremental (FR-345)"
SECCION_D = "Resolubilidad (D): crecimiento t(3 000) / t(300) (FR-346, SC-007)"

TAMANO_CHICO = 300
TAMANO_GRANDE = 3000                 # factor 10 respecto del chico
TAMANO_LIMITE = 5000                 # mucho mayor que cualquier cripta publicada (principio V: es un parámetro)
LADO_REJILLA = 70
FRACCION_CERRADAS = 0.15
CANTIDADES_INDICE = (100, 1000, 10000)
REPETICIONES = 5
UMBRAL_UNA_REPETICION_NS = 10 * 1_000_000_000      # la repetida, con n grande: 1 sola repetición si supera 10 s
LIMITE_NS = 200 * 1_000_000
RAZON_MAXIMA = 20.0
CRIPTA = "bench"


# ------------------------------------------------------------------------------------------------ cronómetro

def _mediana_ns(operacion, repeticiones: int = REPETICIONES, calentar: int = 1) -> int:
    tiempos: list[int] = []
    for i in range(calentar + repeticiones):
        inicio = time.perf_counter_ns()
        operacion()
        fin = time.perf_counter_ns()
        if i >= calentar:
            tiempos.append(fin - inicio)
    insertion_sort(tiempos)
    return tiempos[len(tiempos) // 2]


def _texto_ns(ns: int) -> str:
    return texto(ns / 1000)                         # bench.medicion trabaja en µs


# ------------------------------------------------------------------------------------------------ datos

def _cadena(n: int) -> tuple:
    esqueleto, llaves, llave_salida, sala_salida = esqueleto_llaves_encadenadas(n, SEMILLA)
    return mapa_desde_salas(esqueleto), 1, sala_salida, llave_salida, ubicaciones(CRIPTA, llaves)


def _rejilla() -> tuple:
    """Rejilla de LADO_REJILLA × LADO_REJILLA con FRACCION_CERRADAS de puertas cerradas; cada puerta (los dos sentidos)
    recibe su propia llave, ubicada en una sala al azar; la llave de salida, también en una sala al azar."""
    esqueleto = esqueleto_rejilla(LADO_REJILLA, LADO_REJILLA, semilla=SEMILLA, fraccion_cerradas=FRACCION_CERRADAS)
    azar = random.Random(SEMILLA + 3)
    total = len(esqueleto)
    entradas: list[tuple] = []
    numero = 0
    for sala in esqueleto:
        for letra in ("N", "S", "E", "O"):
            salida = sala["salidas"].get(letra)
            if salida is None or not salida.get("cerrada") or salida["sala"] < sala["id"]:
                continue                                      # cada conexión se trata una vez, desde la sala de menor id
            numero += 1
            llave = f"r_{numero}"
            salida["llave"] = llave
            for vuelta in esqueleto[salida["sala"] - 1]["salidas"].values():
                if vuelta["sala"] == sala["id"]:
                    vuelta["llave"] = llave
            entradas.append((llave, azar.randint(1, total), None))
    entradas.append(("r_salida", azar.randint(1, total), None))
    return mapa_desde_salas(esqueleto), 1, total, "r_salida", ubicaciones(CRIPTA, entradas)


# ------------------------------------------------------------------------------------------------ secciones

def seccion_a(filas: list) -> tuple[bool, list[int], list[int]]:
    """Devuelve (resultados iguales, [t_incremental chico, grande], [t_repetida chico, grande]) en ns."""
    iguales = True
    incremental: list[int] = []
    repetida: list[int] = []
    for n in (TAMANO_CHICO, TAMANO_GRANDE):
        datos = _cadena(n)
        mapa, inicial, salida, llave_salida, llaves = datos
        a = verificar_resolubilidad(mapa, inicial, salida, llave_salida, llaves, CRIPTA)
        inicio = time.perf_counter_ns()
        b = verificar_repetida(mapa, inicial, salida, llave_salida, llaves, CRIPTA)
        primera = time.perf_counter_ns() - inicio
        iguales = verificar(filas, SECCION_A, f"n = {n:,}: el incremental y la repetida dan el mismo resultado "
                                              f"({len(a.orden):,} llaves en el orden)", a == b) and iguales
        t_inc = _mediana_ns(lambda: verificar_resolubilidad(mapa, inicial, salida, llave_salida, llaves, CRIPTA))
        if primera > UMBRAL_UNA_REPETICION_NS:
            t_rep, detalle = primera, "1 repetición (la primera superó 10 s)"
        else:
            t_rep = _mediana_ns(lambda: verificar_repetida(mapa, inicial, salida, llave_salida, llaves, CRIPTA),
                                calentar=0)
            detalle = f"mediana de {REPETICIONES}"
        incremental.append(t_inc)
        repetida.append(t_rep)
        salas = mapa.total_salas()
        filas.append((SECCION_A, f"n = {n:,} ({salas:,} salas): incremental (elegido)", _texto_ns(t_inc),
                      f"mediana de {REPETICIONES}"))
        filas.append((SECCION_A, f"n = {n:,} ({salas:,} salas): repetida (oráculo, descartada)", _texto_ns(t_rep),
                      detalle))
    return iguales, incremental, repetida


def _lineal(ids: list[str], buscado: str) -> int:
    for posicion in range(len(ids)):
        if ids[posicion] == buscado:
            return posicion
    return -1


def seccion_b(filas: list) -> None:
    azar = random.Random(SEMILLA + 7)
    for k in CANTIDADES_INDICE:
        ids = [f"itm_llave_{azar.randrange(10 ** 9)}" for _ in range(k)]
        indice = IndiceLlaves(ids)
        ordenados = [indice.id_de(i) for i in range(indice.cantidad())]
        iguales = True
        for buscado in ids:
            if indice.numero(buscado) != _lineal(ordenados, buscado):
                iguales = False
                break
        verificar(filas, SECCION_B, f"K = {k:,}: binaria y lineal dan la misma posición", iguales)

        def binaria():
            for buscado in ids:
                indice.numero(buscado)

        def lineal():
            for buscado in ids:
                _lineal(ordenados, buscado)
        t_bin = _mediana_ns(binaria)
        reps_lineal = REPETICIONES if k <= 1000 else 1
        t_lin = _mediana_ns(lineal, repeticiones=reps_lineal, calentar=1 if k <= 1000 else 0)
        filas.append((SECCION_B, f"K = {k:,}, {k:,} consultas: búsqueda binaria (elegida)", _texto_ns(t_bin),
                      f"mediana de {REPETICIONES}"))
        filas.append((SECCION_B, f"K = {k:,}, {k:,} consultas: búsqueda lineal (descartada)", _texto_ns(t_lin),
                      f"mediana de {reps_lineal}" if reps_lineal > 1 else "1 repetición"))


def seccion_c(filas: list) -> bool:
    cumple = True
    for nombre, datos in ((f"cadena n = {TAMANO_LIMITE:,}", _cadena(TAMANO_LIMITE)),
                          (f"rejilla {LADO_REJILLA} × {LADO_REJILLA} con puertas y llaves al azar", _rejilla())):
        mapa, inicial, salida, llave_salida, llaves = datos
        resultado = verificar_resolubilidad(mapa, inicial, salida, llave_salida, llaves, CRIPTA)
        t = _mediana_ns(lambda: verificar_resolubilidad(mapa, inicial, salida, llave_salida, llaves, CRIPTA))
        ok = t <= LIMITE_NS
        cumple = ok and cumple
        estado = "resoluble" if resultado.resoluble else "no resoluble"
        filas.append((SECCION_C, f"{nombre} ({mapa.total_salas():,} salas, {llaves.cantidad():,} llaves, {estado})",
                      _texto_ns(t), f"mediana de {REPETICIONES}; límite 200 ms: {'CUMPLE' if ok else 'NO CUMPLE'}"))
    return cumple


def seccion_d(filas: list, incremental: list[int], repetida: list[int]) -> bool:
    razon_inc = incremental[1] / incremental[0]
    razon_rep = repetida[1] / repetida[0]
    ok = razon_inc <= RAZON_MAXIMA
    filas.append((SECCION_D, "incremental (elegido)", f"{razon_inc:,.1f}",
                  f"tamaño ×10; límite {RAZON_MAXIMA:.0f}: {'CUMPLE' if ok else 'NO CUMPLE'}"))
    filas.append((SECCION_D, "repetida (oráculo, descartada)", f"{razon_rep:,.1f}", "INFORMATIVA"))
    nota(filas, SECCION_D, "Una razón cercana a 10 es crecimiento lineal; cerca de 100, cuadrático.")
    return ok


def ejecutar(filas: list) -> bool:
    iguales, incremental, repetida = seccion_a(filas)
    seccion_b(filas)
    cumple_c = seccion_c(filas)
    cumple_d = seccion_d(filas, incremental, repetida)
    return iguales and cumple_c and cumple_d
