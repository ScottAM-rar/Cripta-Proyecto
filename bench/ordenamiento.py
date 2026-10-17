"""§4.9 Ordenamiento: inserción y mezcla (los del juego) y el criterio de elección, contra quicksort (descartado).

Se prueban tamaños pequeños, datos casi ordenados y comparaciones costosas, como pide el enunciado. Quicksort existe
SOLO aquí. No se usa list.sort() ni sorted() para ordenar lo que se evalúa.
"""
from __future__ import annotations

from Logica.ordenamiento import insertion_sort, merge_sort, ordenar_adaptativo
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


def _regla_por_tamano(datos, clave):
    """La elección que tenía el juego antes: solo mira el tamaño (≤15 inserción, si no mezcla). Existe SOLO aquí."""
    return insertion_sort(list(datos), clave) if len(datos) <= 15 else merge_sort(list(datos), clave)


def _clave_barata(x):
    return x


def _clave_cara(x):
    """Clave compuesta de cuatro campos, como la de la tabla de puntajes."""
    return (x % 7, -(x % 13), x % 5, x)


def _clave_puntaje(r):
    """La de la tabla de puntajes (§2.12): primero las victorias, luego menos tiempo, menos acciones y más enemigos."""
    return (0 if r[1] else 1, r[2], r[3], -r[4])


def _puntajes(n: int, tipo: str, rng) -> list:
    """Registros (nombre, victoria, tiempo, acciones, enemigos) con muchos empates, como una tabla real."""
    def uno(i):
        return (f"J{i}", rng.random() < 0.4, rng.randrange(200) * 100, rng.randrange(60), rng.randrange(8))
    if tipo == "aleatorio":
        return [uno(i) for i in range(n)]
    # 'casi_ordenado': la tabla ya estaba ordenada y se anexaron partidas nuevas al final (como hace el archivo)
    base = merge_sort([uno(i) for i in range(n - n // 20)], _clave_puntaje)
    return base + [uno(n + i) for i in range(n // 20)]


ALGORITMOS = (
    ("inserción", lambda datos, clave: insertion_sort(list(datos), clave)),
    ("mezcla", lambda datos, clave: merge_sort(list(datos), clave)),
    ("regla por tamaño (anterior)", lambda datos, clave: _regla_por_tamano(datos, clave)),
    ("elección automática", lambda datos, clave: ordenar_adaptativo(datos, clave)),
    ("quicksort", lambda datos, clave: quicksort(datos, clave)),
)


def ejecutar(filas: list) -> None:
    rng = azar(3)
    prueba = numeros(300, "aleatorio", rng)
    referencia = merge_sort(list(prueba), _clave_cara)
    verificar(filas, SECCION, "los cinco algoritmos dan el mismo resultado (clave compuesta, 300 datos)",
              all(f(prueba, _clave_cara) == referencia for _, f in ALGORITMOS))

    for clave_nombre, clave in (("clave barata", _clave_barata), ("clave cara (4 campos)", _clave_cara)):
        for n in TAMANOS:
            for tipo in TIPOS:
                datos = numeros(n, tipo, azar(n))
                for nombre, algoritmo in ALGORITMOS:
                    etiqueta = f"{clave_nombre:<22} N={n:>5} {tipo:<13} [{nombre}]"
                    cuadratico = nombre == "inserción" and n > LIMITE_CUADRATICO
                    if cuadratico and tipo != "casi_ordenado" and nombre == "inserción":
                        filas.append((SECCION, etiqueta, "omitido", f"costo O(n²) con N>{LIMITE_CUADRATICO}"))
                        continue
                    anotar(filas, SECCION, etiqueta,
                           medir(lambda: algoritmo(datos, clave), repeticiones=3 if n >= 5_000 else 7))
    nota(filas, SECCION, "La elección automática del juego mira el tamaño y el orden previo (inserción con presupuesto de 4·n desplazamientos); la «regla por tamaño (anterior)» es la que solo miraba el tamaño.")

    _ejecutar_puntajes(filas)


def _ejecutar_puntajes(filas: list) -> None:
    """Tabla de puntajes con 1 000 y 10 000 registros y clave compuesta (§2.12, §4.9)."""
    seccion = SECCION + " · tabla de puntajes"
    prueba = _puntajes(2_000, "aleatorio", azar(11))
    por_mezcla = merge_sort(list(prueba), _clave_puntaje)
    verificar(filas, seccion, "inserción, mezcla y elección automática dejan los empates en el mismo orden (estables)",
              insertion_sort(list(prueba), _clave_puntaje) == por_mezcla and ordenar_adaptativo(prueba, _clave_puntaje) == por_mezcla)
    distintos = sum(1 for a, b in zip(quicksort(prueba, _clave_puntaje), por_mezcla) if a != b)
    nota(filas, seccion, f"quicksort (no estable) deja {distintos} de {len(prueba)} registros en distinto lugar que la mezcla, por empates en la clave")
    for n in (1_000, 10_000):
        for tipo in ("aleatorio", "casi_ordenado"):
            datos = _puntajes(n, tipo, azar(n))
            for nombre, algoritmo in ALGORITMOS:
                if nombre == "inserción" and not (tipo == "casi_ordenado" and n <= 1_000):
                    filas.append((seccion, f"N={n:>6} {tipo:<13} [{nombre}]", "omitido", "costo O(n²) en esta tabla"))
                    continue
                anotar(filas, seccion, f"N={n:>6} {tipo:<13} [{nombre}]",
                       medir(lambda: algoritmo(datos, _clave_puntaje), repeticiones=3 if n >= 10_000 else 5))

