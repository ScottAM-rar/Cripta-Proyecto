"""§4.5 Inventario: lista doblemente enlazada con cursor (la del juego) contra un arreglo con índice de cursor."""
from __future__ import annotations

from DTO.Objeto import Pocion
from Logica.InventarioLogica import InventarioLogica
from bench.datos import azar
from bench.medicion import anotar, medir, nota, verificar

SECCION = "Inventario (§4.5): lista doble con cursor  vs  arreglo con índice"
CAPACIDADES = (10, 100, 1_000)
GOLPES = 200            # quitar-y-reinsertar el objeto del medio por medición


class InventarioArreglo:
    """ALTERNATIVA DESCARTADA: solo para medirla."""

    def __init__(self, capacidad: int) -> None:
        self.capacidad = capacidad
        self.objetos: list = []
        self.cursor = 0

    def agregar_objeto(self, objeto) -> None:
        if len(self.objetos) >= self.capacidad:
            raise ValueError("inventario lleno")
        self.objetos.append(objeto)

    def siguiente_objeto(self) -> bool:
        if self.cursor + 1 >= len(self.objetos):
            return False
        self.cursor += 1
        return True

    def indice_de_objeto(self, objeto) -> int:
        for i in range(len(self.objetos)):
            if self.objetos[i] is objeto:
                return i
        raise ValueError("no está")

    def eliminar_objeto_utilizado(self, objeto) -> None:
        del self.objetos[self.indice_de_objeto(objeto)]
        self.cursor = 0

    def insertar_en_indice_por_retroceso(self, indice: int, objeto) -> None:
        self.objetos.insert(indice, objeto)


def _objetos(n: int) -> list[Pocion]:
    rng = azar(n)
    return [Pocion(f"itm_{i}", f"Objeto {i}", rng.randrange(1, 20), rng.randrange(1, 100)) for i in range(n)]


def _llenar(inventario, objetos) -> None:
    for objeto in objetos:
        inventario.agregar_objeto(objeto)


def ejecutar(filas: list) -> None:
    # Ambos deben quedar iguales tras quitar y reinsertar un objeto del medio.
    objetos = _objetos(50)
    elegido, alterno = InventarioLogica(50), InventarioArreglo(50)
    _llenar(elegido, objetos)
    _llenar(alterno, objetos)
    medio = objetos[25]
    for inv in (elegido, alterno):
        indice = inv.indice_de_objeto(medio)
        inv.eliminar_objeto_utilizado(medio)
        inv.insertar_en_indice_por_retroceso(indice, medio)

    def contenido(inv):
        if isinstance(inv, InventarioArreglo):
            return [o.id_catalogo for o in inv.objetos]
        resultado, nodo = [], inv.cabeza
        while nodo is not None:
            resultado.append(nodo.objeto.id_catalogo)
            nodo = nodo.siguiente
        return resultado
    verificar(filas, SECCION, "quitar y reinsertar en su índice deja el mismo orden en ambos", contenido(elegido) == contenido(alterno))

    for n in CAPACIDADES:
        objetos = _objetos(n)
        medio = objetos[n // 2]
        for nombre, fabrica in (("lista doble", InventarioLogica), ("arreglo", InventarioArreglo)):
            anotar(filas, SECCION, f"cap={n:>5}  agregar N objetos                    [{nombre}]",
                   medir(lambda: _llenar(fabrica(n), objetos)))

            def preparar(f=fabrica):
                inv = f(n)
                _llenar(inv, objetos)
                return inv

            def recorrer(inv):
                while inv.siguiente_objeto():
                    pass
            anotar(filas, SECCION, f"cap={n:>5}  mover el cursor de punta a punta    [{nombre}]",
                   medir(recorrer, preparar))

            def quitar_y_reinsertar(inv):
                for _ in range(GOLPES):
                    indice = inv.indice_de_objeto(medio)
                    inv.eliminar_objeto_utilizado(medio)
                    inv.insertar_en_indice_por_retroceso(indice, medio)
            anotar(filas, SECCION, f"cap={n:>5}  {GOLPES}× quitar+reinsertar el del medio [{nombre}]",
                   medir(quitar_y_reinsertar, preparar))
    nota(filas, SECCION, "Quitar y reinsertar usa la búsqueda por identidad que hace el juego al usar, equipar o deshacer.")
