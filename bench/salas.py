"""§4.7 / §7 Salas: acceso por número a una sala ya cargada y recorrido por niveles de la vecindad.

Elegido: arreglo indexado por número de sala (list como almacenamiento contiguo). Alternativa descartada: lista
enlazada de salas cargadas, que existe SOLO aquí. El recorrido por niveles es el de ServicioCripta.salas_vecinas
sobre una cripta en rejilla (cada sala tiene hasta 4 salidas).
"""
from __future__ import annotations

import tempfile

from adaptadores.bench_red_mejorado import _servicio
from bench.datos import azar
from bench.medicion import anotar, medir, nota, verificar

SECCION = "Salas (§4.7): arreglo indexado  vs  lista enlazada, y recorrido por niveles"
TAMANOS = (10, 100, 1_000)
CONSULTAS = 200


class _Nodo:
    def __init__(self, numero: int) -> None:
        self.numero = numero
        self.siguiente = None


class _ListaDeSalas:
    """ALTERNATIVA DESCARTADA: lista enlazada de salas cargadas (sin puestos vacíos)."""

    def __init__(self) -> None:
        self.primero = None

    def agregar(self, numero: int) -> None:
        nodo = _Nodo(numero)
        nodo.siguiente = self.primero
        self.primero = nodo

    def buscar(self, numero: int):
        actual = self.primero
        while actual is not None:
            if actual.numero == numero:
                return actual
            actual = actual.siguiente
        return None


def _rejilla(salas: int) -> tuple[int, int]:
    return {10: (5, 2), 100: (10, 10), 1_000: (50, 20)}[salas]


def ejecutar(filas: list) -> None:
    rng = azar(7)
    preguntas = {n: [rng.randrange(1, n + 1) for _ in range(CONSULTAS)] for n in TAMANOS}

    for n in TAMANOS:
        arreglo: list = [None] * (n + 1)          # el puesto 0 no se usa: las salas empiezan en 1
        lista = _ListaDeSalas()
        for numero in range(1, n + 1):
            arreglo[numero] = numero
            lista.agregar(numero)
        consultas = preguntas[n]
        verificar(filas, SECCION, f"ambas encuentran las mismas {CONSULTAS} salas (N={n})",
                  all(arreglo[c] == lista.buscar(c).numero for c in consultas))

        def con_arreglo():
            for c in consultas:
                arreglo[c]

        def con_lista():
            for c in consultas:
                lista.buscar(c)

        anotar(filas, SECCION, f"{n:>5} salas  {CONSULTAS} accesos por número  [arreglo indexado]", medir(con_arreglo))
        anotar(filas, SECCION, f"{n:>5} salas  {CONSULTAS} accesos por número  [lista enlazada]", medir(con_lista))

    with tempfile.TemporaryDirectory() as raiz:
        for n in TAMANOS:
            ancho, alto = _rejilla(n)
            _, servicio, cripta = _servicio(f"{raiz}/rej{n}", ancho, alto)
            servicio.crear_jugador(cripta)
            centro = n // 2 + 1
            servicio.salas_vecinas(cripta, centro, 1)            # calienta el esqueleto
            for profundidad in (1, 2, 3):
                alcanzadas = len(servicio.salas_vecinas(cripta, centro, profundidad))
                anotar(filas, SECCION,
                       f"{n:>5} salas  recorrido por niveles, profundidad {profundidad} ({alcanzadas} salas)",
                       medir(lambda: servicio.salas_vecinas(cripta, centro, profundidad)))
    nota(filas, SECCION, "El recorrido busca cada sala del esqueleto en forma lineal (_buscar_esqueleto): si crece con N, ese es el punto a mejorar.")
