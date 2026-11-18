from __future__ import annotations


class CacheLRU:
    """Caché en memoria de capacidad fija. Desaloja la entrada menos usada.

    Una entrada "en uso" (marcar_en_uso) nunca se desaloja. Si la caché está
    llena y todas las entradas están en uso, la nueva NO se guarda (así la
    capacidad jamás se supera); quien la pidió igual puede usarla, y los datos
    siguen en disco por si se vuelven a necesitar.

    Cada entrada es [clave, valor, veces_en_uso]. Se guardan en una lista propia
    ordenada de menos a más reciente: la más reciente va al final (012, D2).
    Un acierto o una reinserción mueven la entrada al final; se desaloja la
    primera libre desde el inicio. Sin estructuras de biblioteca (principio I).
    """

    def __init__(self, capacidad: int = 25) -> None:
        if capacidad < 1:
            raise ValueError("La capacidad de la caché debe ser al menos 1")
        self._capacidad = capacidad
        self._entradas: list[list] = []           # de la menos reciente (inicio) a la más reciente (final)
        self._aciertos = 0
        self._fallos = 0

    def __len__(self) -> int:
        return len(self._entradas)

    @property
    def capacidad(self) -> int:
        return self._capacidad

    @property
    def aciertos(self) -> int:
        """Veces que obtener() encontró la clave en la caché."""
        return self._aciertos

    @property
    def fallos(self) -> int:
        """Veces que obtener() NO encontró la clave (hubo que ir al cliente)."""
        return self._fallos

    def claves(self) -> list[str]:
        """Las claves guardadas, de la más reciente a la menos reciente."""
        claves: list[str] = []
        for i in range(len(self._entradas) - 1, -1, -1):
            claves.append(self._entradas[i][0])
        return claves

    def _posicion(self, clave: str) -> int:
        """Posición de la entrada con esa clave, o -1. Busca del final (más recientes) al inicio."""
        for i in range(len(self._entradas) - 1, -1, -1):
            if self._entradas[i][0] == clave:
                return i
        return -1

    def _buscar(self, clave: str) -> list | None:
        i = self._posicion(clave)
        return None if i < 0 else self._entradas[i]

    def _al_final(self, i: int) -> list:
        """Mueve la entrada de la posición i al final (pasa a ser la más reciente) y la devuelve."""
        entrada = self._entradas[i]
        del self._entradas[i]
        self._entradas.append(entrada)
        return entrada

    def obtener(self, clave: str) -> object | None:
        i = self._posicion(clave)
        if i < 0:
            self._fallos += 1
            return None
        self._aciertos += 1
        return self._al_final(i)[1]

    def insertar(self, clave: str, valor: object) -> bool:
        """Guarda el valor. Devuelve False si no hubo lugar (todo en uso)."""
        i = self._posicion(clave)
        if i >= 0:
            self._al_final(i)[1] = valor
            return True

        if len(self._entradas) >= self._capacidad:
            if self._desalojar() is None:
                return False
        self._entradas.append([clave, valor, 0])
        return True

    def marcar_en_uso(self, clave: str) -> None:
        entrada = self._buscar(clave)
        if entrada is not None:
            entrada[2] += 1

    def marcar_libre(self, clave: str) -> None:
        entrada = self._buscar(clave)
        if entrada is not None and entrada[2] > 0:
            entrada[2] -= 1

    def establecer_en_uso(self, claves: list[str]) -> None:
        """Deja como "en uso" exactamente las claves dadas, cada entrada queda con tantas
        referencias como veces aparece su clave. Se recalcula desde cero, así nunca se desfasa."""
        for entrada in self._entradas:
            veces = 0
            for clave in claves:
                if clave == entrada[0]:
                    veces += 1
            entrada[2] = veces

    def en_uso(self, clave: str) -> bool:
        entrada = self._buscar(clave)
        return entrada is not None and entrada[2] > 0

    def _desalojar(self) -> str | None:
        """Quita la entrada menos reciente que no está en uso (la primera libre desde el inicio)."""
        for i in range(len(self._entradas)):
            if self._entradas[i][2] == 0:
                clave = self._entradas[i][0]
                del self._entradas[i]
                return clave
        return None
