"""§4.9 Ordenamiento: inserción y mezcla (los del juego) y el criterio de elección, contra quicksort (descartado).

Se prueban tamaños pequeños, datos casi ordenados y comparaciones costosas, como pide el enunciado. Quicksort existe
SOLO aquí. No se usa list.sort() ni sorted() para ordenar lo que se evalúa.
"""
from __future__ import annotations

from Controlador.ordenamiento import insertion_sort, merge_sort, ordenar_adaptativo
from bench.datos import azar, numeros
from bench.medicion import anotar, medir, nota, verificar

SECCION = "Ordenamiento (§4.9): inserción · mezcla · elección automática  vs  quicksort"
TAMANOS = (5, 15, 50, 500, 5_000)
TIPOS = ("aleatorio", "casi_ordenado", "inverso")
LIMITE_CUADRATICO = 2_000      # la inserción en datos desordenados mayores a esto se omite (O(n²))


def quicksort(lista: list, key=lambda x: x) -> list:
    """ALTERNATIVA DESCARTADA: quicksort iterativo con pivote mediana de tres (no estable)."""
    datos = list(lista)
    pila = [(0, len(datos) - 1)]
    while pila:
        bajo, alto = pila.pop()
        while bajo < alto:
            medio = (bajo + alto) // 2
            a, b, c = key(datos[bajo]), key(datos[medio]), key(datos[alto])
            if (a <= b <= c) or (c <= b <= a):
                indice_pivote = medio
            elif (b <= a <= c) or (c <= a <= b):
                indice_pivote = bajo
            else:
                indice_pivote = alto
            pivote = key(datos[indice_pivote])
            datos[indice_pivote], datos[alto] = datos[alto], datos[indice_pivote]
            frontera = bajo
            for i in range(bajo, alto):
                if key(datos[i]) < pivote:
                    datos[i], datos[frontera] = datos[frontera], datos[i]
                    frontera += 1
            datos[frontera], datos[alto] = datos[alto], datos[frontera]
            if frontera - bajo < alto - frontera:           # se apila la parte grande y se sigue con la chica
                pila.append((frontera + 1, alto))
                alto = frontera - 1
            else:
                pila.append((bajo, frontera - 1))
                bajo = frontera + 1
    return datos


def _clave_barata(x):
    return x


def _clave_cara(x):
    """Clave compuesta de cuatro campos, como la de la tabla de puntajes."""
    return (x % 7, -(x % 13), x % 5, x)


ALGORITMOS = (
    ("inserción", lambda datos, clave: insertion_sort(list(datos), clave)),
    ("mezcla", lambda datos, clave: merge_sort(list(datos), clave)),
    ("elección automática", lambda datos, clave: ordenar_adaptativo(datos, clave)),
    ("quicksort", lambda datos, clave: quicksort(datos, clave)),
)


def ejecutar(filas: list) -> None:
    rng = azar(3)
    prueba = numeros(300, "aleatorio", rng)
    referencia = merge_sort(list(prueba), _clave_cara)
    verificar(filas, SECCION, "los cuatro algoritmos dan el mismo resultado (clave compuesta, 300 datos)",
              all(f(prueba, _clave_cara) == referencia for _, f in ALGORITMOS))

    for clave_nombre, clave in (("clave barata", _clave_barata), ("clave cara (4 campos)", _clave_cara)):
        for n in TAMANOS:
            for tipo in TIPOS:
                datos = numeros(n, tipo, azar(n))
                for nombre, algoritmo in ALGORITMOS:
                    etiqueta = f"{clave_nombre:<22} N={n:>5} {tipo:<13} [{nombre}]"
                    cuadratico = nombre in ("inserción", "elección automática") and n > LIMITE_CUADRATICO
                    if cuadratico and tipo != "casi_ordenado" and nombre == "inserción":
                        filas.append((SECCION, etiqueta, "omitido", f"costo O(n²) con N>{LIMITE_CUADRATICO}"))
                        continue
                    anotar(filas, SECCION, etiqueta,
                           medir(lambda: algoritmo(datos, clave), repeticiones=3 if n >= 5_000 else 7))
    nota(filas, SECCION, "La elección automática del juego (≤15 inserción, si no mezcla) hoy solo mira el tamaño; estas filas permiten ver si el umbral 15 es el correcto.")
