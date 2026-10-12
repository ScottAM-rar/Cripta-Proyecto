from __future__ import annotations
import json
import os
import struct

MAGIA = b"CRPT"
VERSION_FORMATO = 1
 
_ENCABEZADO = struct.Struct(">4sH")   # magia + versión del formato
_PIE = struct.Struct(">QI")           # posición del índice + cantidad de entradas
_LARGO_CLAVE = struct.Struct(">H")
_POSICION_Y_LARGO = struct.Struct(">QI")

class ErrorArchivo(Exception):
    """El archivo no existe en el formato esperado o está dañado."""


class ArchivoIndexado:
    def __init__(self, ruta: str) -> None:
        self.ruta = ruta


    # --------- CONSULTAS ---------------
    def existe(self) -> bool:
        return os.path.exists(self.ruta)

    def claves(self) -> list[str]:
        """Las claves guardadas, en el orden en que se escribieron."""

        if not self.existe():
            return []
        with open(self.ruta, "rb") as f:
            indice = self._leer_indice(f)

        claves: list[str] = []
        for clave, _, _ in indice:
            claves.append(clave)
        return claves

    def contiene(self, clave: str) -> bool:
        return clave in self.claves()

    def leer(self, clave: str):
        """Devuelve el valor guardado para la clave, o None si no existe."""
        if not self.existe():
            return None
        with open(self.ruta, "rb") as f:
            indice = self._leer_indice(f)
            for clave_i, posicion, largo in indice:
                if clave_i == clave:
                    f.seek(posicion)
                    return self._decodificar(f.read(largo))
        return None


    #----------- ESCRITURA ---------------------
    def escribir(self, clave: str, valor) -> None:
        self.escribir_varios([(clave, valor)])

    def escribir_varios(self, pares: list[tuple[str, object]]) -> None:
        """Guarda varios pares de una vez. Si la clave ya existe, se reemplaza.
 
        El archivo se reescribe completo en un archivo temporal y después se
        cambia por el real, así que un corte a la mitad no deja un archivo
        a medio escribir."""
        entradas = self._cargar_todo()          # lista de [clave, bytes]
        for clave, valor in pares:
            datos = json.dumps(valor, ensure_ascii=False).encode("utf-8")
            reemplazada = False
            for entrada in entradas:
                if entrada[0] == clave:
                    entrada[1] = datos
                    reemplazada = True
            if not reemplazada:
                entradas.append([clave, datos])
        self._escribir_todo(entradas)

    def vaciar(self) -> None:
        """Borra el archivo (por ejemplo, cuando la versión guardada ya no sirve)."""
        if self.existe():
            os.remove(self.ruta)

    #----------- PRIVADOS ---------------
    @staticmethod
    def _decodificar(datos: bytes):
        try:
            return json.loads(datos.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as error:
            raise ErrorArchivo(f"Registro dañado: {error}") from error

    def _leer_indice(self, f) -> list[tuple[str, int, int]]:
        """Lee y valida encabezado, pie e índice. Devuelve [(clave, posición, largo)]."""
        try:
            cabecera = f.read(_ENCABEZADO.size)
            if len(cabecera) < _ENCABEZADO.size:
                raise ErrorArchivo(f"{self.ruta}: archivo demasiado corto")
            magia, version = _ENCABEZADO.unpack(cabecera)
            if magia != MAGIA:
                raise ErrorArchivo(f"{self.ruta}: no es un archivo de Cripta")
            if version != VERSION_FORMATO:
                raise ErrorArchivo(f"{self.ruta}: versión de formato {version} no soportada")
 
            f.seek(0, os.SEEK_END)
            tamano = f.tell()
            if tamano < _ENCABEZADO.size + _PIE.size:
                raise ErrorArchivo(f"{self.ruta}: archivo demasiado corto")
            f.seek(tamano - _PIE.size)
            pos_indice, cantidad = _PIE.unpack(f.read(_PIE.size))
            if pos_indice < _ENCABEZADO.size or pos_indice > tamano - _PIE.size:
                raise ErrorArchivo(f"{self.ruta}: pie dañado")
 
            f.seek(pos_indice)
            indice: list[tuple[str, int, int]] = []
            for _ in range(cantidad):
                (largo_clave,) = _LARGO_CLAVE.unpack(f.read(_LARGO_CLAVE.size))
                clave = f.read(largo_clave).decode("utf-8")
                posicion, largo = _POSICION_Y_LARGO.unpack(f.read(_POSICION_Y_LARGO.size))
                if posicion < _ENCABEZADO.size or posicion + largo > pos_indice:
                    raise ErrorArchivo(f"{self.ruta}: índice dañado")
                indice.append((clave, posicion, largo))
            return indice
        except (struct.error, UnicodeDecodeError) as error:
            raise ErrorArchivo(f"{self.ruta}: archivo dañado ({error})") from error

    def _cargar_todo(self) -> list[list]:
        """Devuelve [[clave, bytes], ...] con todo lo guardado (o [] si no hay archivo)."""
        if not self.existe():
            return []
        entradas: list[list] = []
        with open(self.ruta, "rb") as f:
            for clave, posicion, largo in self._leer_indice(f):
                f.seek(posicion)
                entradas.append([clave, f.read(largo)])
        return entradas

    def _escribir_todo(self, entradas: list[list]) -> None:
        contenido = bytearray(_ENCABEZADO.pack(MAGIA, VERSION_FORMATO))
 
        indice: list[tuple[bytes, int, int]] = []
        for clave, datos in entradas:
            indice.append((clave.encode("utf-8"), len(contenido), len(datos)))
            contenido += datos
 
        pos_indice = len(contenido)
        for clave_bytes, posicion, largo in indice:
            contenido += _LARGO_CLAVE.pack(len(clave_bytes))
            contenido += clave_bytes
            contenido += _POSICION_Y_LARGO.pack(posicion, largo)
        contenido += _PIE.pack(pos_indice, len(indice))
 
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        temporal = self.ruta + ".tmp"
        with open(temporal, "wb") as f:
            f.write(contenido)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, self.ruta)