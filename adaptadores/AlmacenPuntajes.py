"""Tabla de puntajes local en un archivo binario de formato propio, de solo añadir registros.

Encabezado: marca "PUNT", versión del formato y cantidad de registros. Cada registro mide lo mismo (RegistroPuntajeDTO
con textos de largo fijo), así que agregar uno es escribirlo al final y actualizar la cantidad, sin reescribir el archivo.
Este adaptador solo guarda y lee; ordenar la tabla no es asunto suyo.
"""
from __future__ import annotations
import os
import struct

from DTO.RegistroPuntajeDTO import RegistroPuntajeDTO
from adaptadores.extension import ruta_archivo, CARPETA_PARTIDAS

MAGIA = b"PUNT"
VERSION_FORMATO = 1
MAX_NOMBRE = 15                      # caracteres; en disco ocupan hasta 4 bytes cada uno (UTF-8)
_ENCABEZADO = struct.Struct(">4sHI")
_REGISTRO = struct.Struct(f">{MAX_NOMBRE * 4}s32s16sIIIB")
EXTENSION_PUNTAJES = ".pts"
NOMBRE_TABLA = "puntajes"


class ErrorPuntajes(ValueError):
    """El archivo de puntajes está dañado, es de otra versión o el registro no es válido."""


def _texto(valor: str, largo: int) -> bytes:
    datos = valor.encode("utf-8")[:largo]
    return datos.decode("utf-8", errors="ignore").encode("utf-8")    # no deja un carácter cortado a la mitad


class AlmacenPuntajes:
    def __init__(self, ruta: str | None = None) -> None:
        self.ruta = ruta if ruta is not None else ruta_archivo(NOMBRE_TABLA, EXTENSION_PUNTAJES, CARPETA_PARTIDAS)

    @staticmethod
    def validar_nombre(nombre: str) -> str:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorPuntajes("El nombre del jugador no puede estar vacío")
        limpio = nombre.strip()
        if len(limpio) > MAX_NOMBRE:
            raise ErrorPuntajes(f"El nombre no puede pasar de {MAX_NOMBRE} caracteres (tiene {len(limpio)})")
        return limpio

    def agregar(self, registro: RegistroPuntajeDTO) -> None:
        nombre = self.validar_nombre(registro.nombre)
        datos = _REGISTRO.pack(
            _texto(nombre, MAX_NOMBRE * 4), _texto(registro.id_cripta or "", 32), _texto(registro.version_cripta or "", 16),
            registro.acciones_jugador, registro.enemigos_derrotados, registro.tiempo_final, 1 if registro.victoria else 0,
        )
        os.makedirs(os.path.dirname(self.ruta) or ".", exist_ok=True)
        if not os.path.exists(self.ruta):
            with open(self.ruta, "wb") as archivo:
                archivo.write(_ENCABEZADO.pack(MAGIA, VERSION_FORMATO, 1))
                archivo.write(datos)
            return
        with open(self.ruta, "r+b") as archivo:
            cantidad = self._leer_encabezado(archivo, os.path.getsize(self.ruta))
            archivo.seek(_ENCABEZADO.size + cantidad * _REGISTRO.size)
            archivo.write(datos)                          # primero el registro, después la cantidad: si se corta, no queda a medias
            archivo.seek(0)
            archivo.write(_ENCABEZADO.pack(MAGIA, VERSION_FORMATO, cantidad + 1))

    def leer_todos(self) -> list[RegistroPuntajeDTO]:
        if not os.path.exists(self.ruta):
            return []
        with open(self.ruta, "rb") as archivo:
            cantidad = self._leer_encabezado(archivo, os.path.getsize(self.ruta))
            registros = []
            for _ in range(cantidad):
                nombre, cripta, version, acciones, enemigos, tiempo, victoria = _REGISTRO.unpack(archivo.read(_REGISTRO.size))
                registros.append(RegistroPuntajeDTO(
                    nombre.rstrip(b"\0").decode("utf-8"), cripta.rstrip(b"\0").decode("utf-8"),
                    version.rstrip(b"\0").decode("utf-8"), acciones, enemigos, tiempo, bool(victoria),
                ))
        return registros

    @staticmethod
    def _leer_encabezado(archivo, tamano: int) -> int:
        crudo = archivo.read(_ENCABEZADO.size)
        if len(crudo) < _ENCABEZADO.size:
            raise ErrorPuntajes("El archivo de puntajes está dañado")
        magia, version, cantidad = _ENCABEZADO.unpack(crudo)
        if magia != MAGIA:
            raise ErrorPuntajes("El archivo no es una tabla de puntajes")
        if version != VERSION_FORMATO:
            raise ErrorPuntajes(f"Versión del formato de puntajes no soportada: {version} (este programa usa la {VERSION_FORMATO})")
        if tamano != _ENCABEZADO.size + cantidad * _REGISTRO.size:
            raise ErrorPuntajes("El archivo de puntajes está dañado (su tamaño no coincide con la cantidad de registros)")
        return cantidad
