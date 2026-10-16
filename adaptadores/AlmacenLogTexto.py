"""Log de reproducción en texto, de solo añadir (append-only).

El archivo se crea al empezar la partida con la cabecera (cripta, semilla y versiones) y cada acción del jugador se
añade como una línea al momento de ocurrir, así que el log queda en disco aunque el juego se cierre a la mitad.
El modelo no conoce este archivo: solo entrega datos (LogPartidaDTO) y avisa cada acción por `agregar`.
"""
from __future__ import annotations
import os
import re
from datetime import datetime

from DTO.LogPartidaDTO import LogPartidaDTO
from adaptadores.extension import ruta_archivo, EXTENSION_LOG, CARPETA_LOGS


class AlmacenLogTexto:
    def __init__(self, nombre: str | None = None, carpeta: str = CARPETA_LOGS):
        """nombre=None: el nombre se genera solo al abrir (cripta, semilla y fecha-hora)."""
        self._nombre_pedido = nombre
        self._carpeta = carpeta
        self.ruta: str | None = None

    @property
    def nombre(self) -> str | None:
        """Nombre del archivo creado (con extensión), o None si todavía no se abrió."""
        return None if self.ruta is None else os.path.basename(self.ruta)

    # ---------------------------------------------------------------- escritura
    def comprobar_nombre(self) -> None:
        """Falla (ValueError) si el nombre elegido no es válido o ya lo usa otro log. Con nombre automático no hace nada."""
        if self._nombre_pedido is None:
            return
        ruta = ruta_archivo(self._nombre_pedido, EXTENSION_LOG, self._carpeta)
        if os.path.exists(ruta):
            raise ValueError(f"Ya existe un log con el nombre {os.path.basename(ruta)!r}")

    def abrir(self, log: LogPartidaDTO) -> str:
        """Crea el archivo con la cabecera y las acciones que ya tenga `log`. Nunca pisa un log existente."""
        cabecera = (
            f"cripta: {log.id_cripta or 'ninguna'}\n"
            f"semilla: {log.semilla}\n"
            f"version_cripta: {log.version_cripta or 'desconocida'}\n"
            f"version_catalogo: {log.version_catalogo or 'desconocida'}\n"
        )
        cuerpo = "".join(accion + "\n" for accion in log.acciones)
        if self._nombre_pedido is not None:
            ruta = ruta_archivo(self._nombre_pedido, EXTENSION_LOG, self._carpeta, crear_carpeta=True)
            try:
                self._crear(ruta, cabecera + cuerpo)
            except FileExistsError:
                raise ValueError(f"Ya existe un log con el nombre {os.path.basename(ruta)!r}") from None
        else:
            base = f"{_limpio(log.id_cripta)}_semilla{log.semilla}_{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            repeticion = 1
            while True:
                nombre = base if repeticion == 1 else f"{base}-{repeticion}"
                ruta = ruta_archivo(nombre, EXTENSION_LOG, self._carpeta, crear_carpeta=True)
                try:
                    self._crear(ruta, cabecera + cuerpo)
                    break
                except FileExistsError:
                    repeticion += 1
        self.ruta = ruta
        return ruta

    @staticmethod
    def _crear(ruta: str, texto: str) -> None:
        with open(ruta, "x", encoding="utf-8") as archivo:      # "x": falla si ya existe
            archivo.write(texto)

    def agregar(self, accion: str) -> None:
        """Añade una acción al final del log, ya escrita en disco al volver."""
        if self.ruta is None:
            raise ValueError("El log no se ha abierto")
        with open(self.ruta, "a", encoding="utf-8") as archivo:
            archivo.write(accion + "\n")

    # ---------------------------------------------------------------- lectura
    @staticmethod
    def leer(nombre: str, carpeta: str = CARPETA_LOGS) -> LogPartidaDTO:
        ruta = ruta_archivo(nombre, EXTENSION_LOG, carpeta)
        with open(ruta, "r", encoding="utf-8") as archivo:
            lineas = [linea.rstrip("\n") for linea in archivo]

        if len(lineas) < 2 or not lineas[0].startswith("cripta: "):
            raise ValueError("El archivo .log no contiene una cripta válida")
        id_cripta = lineas[0][len("cripta: "):]
        if id_cripta == "ninguna":
            id_cripta = None
        elif not id_cripta.strip():
            raise ValueError("El ID de la cripta del archivo .log no es válido")
        if not lineas[1].startswith("semilla: "):
            raise ValueError("El archivo .log no contiene una semilla válida")
        try:
            semilla = int(lineas[1][len("semilla: "):])
        except ValueError as error:
            raise ValueError("La semilla del archivo .log debe ser un entero") from error

        # Las versiones son opcionales: los logs antiguos no las traen.
        posicion = 2
        versiones = [None, None]
        for indice, clave in enumerate(("version_cripta: ", "version_catalogo: ")):
            if posicion < len(lineas) and lineas[posicion].startswith(clave):
                valor = lineas[posicion][len(clave):].strip()
                versiones[indice] = None if valor in ("", "desconocida") else valor
                posicion += 1

        acciones = [linea for linea in lineas[posicion:] if linea.strip()]
        return LogPartidaDTO(id_cripta, semilla, versiones[0], versiones[1], acciones)


def _limpio(texto: str | None) -> str:
    """Deja solo letras, números, guion y guion bajo, para que sirva de nombre de archivo."""
    resultado = re.sub(r"[^A-Za-z0-9_-]", "_", texto or "sin-cripta")
    return resultado or "sin-cripta"
