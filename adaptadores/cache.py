from __future__ import annotations
from collections import deque

class CacheLRU:
    """Caché en memoria de capacidad fija. Desaloja la entrada menos usada.

    Una entrada "en uso" (marcar_en_uso) nunca se desaloja. Si la caché está
    llena y todas las entradas están en uso, la nueva NO se guarda (así la
    capacidad jamás se supera); quien la pidió igual puede usarla, y los datos
    siguen en disco por si se vuelven a necesitar.

    Cada entrada es [clave, valor, veces_en_uso]. Las más recientes van al frente.
    """

    def __init__(self, capacidad: int = 25) -> None:
        if capacidad < 1:
            raise ValueError("La capacidad de la caché debe ser al menos 1")
        self._capacidad = capacidad
        self._entradas: deque[list] = deque()

    def __len__(self) -> int:
        return len(self._entradas)

    @property
    def capacidad(self) -> int:
        return self._capacidad

    def claves(self) -> list[str]:
        """Las claves guardadas, de la más reciente a la menos reciente."""
        claves: list[str] = []
        for entrada in self._entradas:
            claves.append(entrada[0])
        return claves

    def _buscar(self, clave: str) -> list | None:
        for entrada in self._entradas:
            if entrada[0] == clave:
                return entrada
        return None

    def obtener(self, clave: str) -> object | None:
        entrada = self._buscar(clave)
        if entrada is None:
            return None
        self._entradas.remove(entrada)
        self._entradas.appendleft(entrada)
        return entrada[1]

    def insertar(self, clave: str, valor: object) -> bool:
        """Guarda el valor. Devuelve False si no hubo lugar (todo en uso)."""
        existente = self._buscar(clave)
        if existente is not None:
            existente[1] = valor
            self._entradas.remove(existente)
            self._entradas.appendleft(existente)
            return True

        if len(self._entradas) >= self._capacidad:
            if self._desalojar() is None:
                return False
        self._entradas.appendleft([clave, valor, 0])
        return True

    def marcar_en_uso(self, clave: str) -> None:
        entrada = self._buscar(clave)
        if entrada is not None:
            entrada[2] += 1

    def marcar_libre(self, clave: str) -> None:
        entrada = self._buscar(clave)
        if entrada is not None and entrada[2] > 0:
            entrada[2] -= 1

    def _desalojar(self) -> str | None:
        for entrada in reversed(self._entradas):
            if entrada[2] == 0:
                self._entradas.remove(entrada)
                return entrada[0]
        return None
