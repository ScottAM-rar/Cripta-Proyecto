"""Archivo binario de formato propio para guardar una partida (§4.10).

Disposición del archivo:
    [encabezado: marca "CRPP" + versión del formato]
    [bloques: cada sección del estado y cada sala se codifican por separado]
    [secciones: nombre, posición, largo y CRC de cada sección]
    [tabla de salas: una entrada de tamaño fijo (número, posición, largo, CRC) por sala, en orden de número]
    [pie: dónde están las secciones y la tabla, cuántas salas hay y una marca de cierre]

Se lee de atrás hacia adelante. Como las entradas de la tabla de salas miden lo mismo y están ordenadas, leer_sala(n)
hace una búsqueda binaria dando saltos dentro del archivo: lee O(log n) entradas de 20 bytes y el bloque de esa sala,
sin leer el resto. No hay diccionarios.
"""
from __future__ import annotations

import dataclasses
import os
import struct
import zlib

from DTO.EstadoGuardadoDTO import EstadoGuardadoDTO, SalaGuardadaDTO
from adaptadores.codec_partida import (
    ErrorCodec, Lector, a_bytes, de_bytes, escribir_natural, escribir_texto,
)

MAGIA = b"CRPP"
VERSION_FORMATO = 6     # 6: costo por salida y rango por enemigo; 5: anterior; 4: se guarda el contador de acciones del jugador; 3: los enemigos guardan si están activos
MARCA_FIN = b"FIN!"

_ENCABEZADO = struct.Struct(">4sH")
_PIE = struct.Struct(">QIQI4s")        # pos. secciones, largo secciones, pos. tabla de salas, cantidad de salas, marca
_ENTRADA_SALA = struct.Struct(">IQII")  # número de sala, posición del bloque, largo del bloque, CRC del bloque
_CAMPO_SALAS = "salas"                  # el único campo de EstadoGuardadoDTO que se guarda sala por sala


class ErrorPartida(ValueError):
    """El archivo de partida no existe, está dañado o es de otra versión del formato."""


class AlmacenPartidaBinario:
    def __init__(self, ruta: str) -> None:
        self.ruta = ruta

    # ------------------------------------------------------------------ guardar

    def guardar(self, estado: EstadoGuardadoDTO) -> None:
        secciones: list = []     # (nombre, posicion, largo, crc)
        salas: list = []         # (numero, posicion, largo, crc)
        temporal = self.ruta + ".tmp"
        try:
            with open(temporal, "wb") as archivo:
                archivo.write(_ENCABEZADO.pack(MAGIA, VERSION_FORMATO))
                for campo in dataclasses.fields(EstadoGuardadoDTO):
                    if campo.name == _CAMPO_SALAS:
                        continue
                    secciones.append(self._escribir_bloque(archivo, campo.name, getattr(estado, campo.name)))
                anterior = -1
                for sala in estado.salas:
                    if sala.id <= anterior:
                        raise ErrorPartida("Las salas deben guardarse en orden creciente de número")
                    anterior = sala.id
                    _, posicion, largo, crc = self._escribir_bloque(archivo, "", sala)
                    salas.append((sala.id, posicion, largo, crc))

                indice = bytearray()
                escribir_natural(indice, len(secciones))
                for nombre, posicion, largo, crc in secciones:
                    escribir_texto(indice, nombre)
                    escribir_natural(indice, posicion)
                    escribir_natural(indice, largo)
                    escribir_natural(indice, crc)
                posicion_secciones = archivo.tell()
                archivo.write(indice)
                posicion_tabla = archivo.tell()
                for entrada in salas:
                    archivo.write(_ENTRADA_SALA.pack(*entrada))
                archivo.write(_PIE.pack(posicion_secciones, len(indice), posicion_tabla, len(salas), MARCA_FIN))
            os.replace(temporal, self.ruta)
        except ErrorPartida:
            self._borrar(temporal)
            raise
        except (OSError, ErrorCodec, struct.error) as error:
            self._borrar(temporal)
            raise ErrorPartida(f"No se pudo escribir la partida en {self.ruta!r}: {error}") from error

    @staticmethod
    def _escribir_bloque(archivo, nombre: str, valor) -> tuple:
        datos = a_bytes(valor)
        posicion = archivo.tell()
        archivo.write(datos)
        return nombre, posicion, len(datos), zlib.crc32(datos)

    # ------------------------------------------------------------------ cargar

    def existe(self) -> bool:
        return os.path.isfile(self.ruta)

    def cargar(self) -> EstadoGuardadoDTO:
        """Lee la partida completa."""
        try:
            with self._abrir() as archivo:
                pie = self._leer_pie(archivo)
                secciones = self._leer_secciones(archivo, pie)
                valores = []
                for campo in dataclasses.fields(EstadoGuardadoDTO):
                    if campo.name == _CAMPO_SALAS:
                        salas = []
                        for i in range(pie[3]):
                            salas.append(self._leer_sala_en(archivo, self._entrada(archivo, pie, i)))
                        valores.append(salas)
                    else:
                        valores.append(self._leer_seccion(archivo, secciones, campo.name))
            return EstadoGuardadoDTO(*valores)
        except (ErrorCodec, TypeError, IndexError, struct.error) as error:
            raise ErrorPartida(f"El archivo de partida está dañado: {error}") from error
        except OSError as error:
            raise ErrorPartida(f"No se pudo leer el archivo de partida: {error}") from error

    def leer_sala(self, numero: int) -> SalaGuardadaDTO | None:
        """Trae una sola sala sin leer el resto del archivo. None si esa sala no se guardó."""
        try:
            with self._abrir() as archivo:
                pie = self._leer_pie(archivo)
                bajo, alto = 0, pie[3] - 1
                while bajo <= alto:                              # búsqueda binaria dando saltos en la tabla
                    medio = (bajo + alto) // 2
                    entrada = self._entrada(archivo, pie, medio)
                    if entrada[0] == numero:
                        return self._leer_sala_en(archivo, entrada)
                    if entrada[0] < numero:
                        bajo = medio + 1
                    else:
                        alto = medio - 1
                return None
        except (ErrorCodec, TypeError, IndexError, struct.error) as error:
            raise ErrorPartida(f"El archivo de partida está dañado: {error}") from error
        except OSError as error:
            raise ErrorPartida(f"No se pudo leer el archivo de partida: {error}") from error

    def numeros_de_salas(self) -> list[int]:
        """Números de las salas guardadas, sin leer ninguna sala."""
        try:
            with self._abrir() as archivo:
                pie = self._leer_pie(archivo)
                return [self._entrada(archivo, pie, i)[0] for i in range(pie[3])]
        except (ErrorCodec, IndexError, struct.error) as error:
            raise ErrorPartida(f"El archivo de partida está dañado: {error}") from error
        except OSError as error:
            raise ErrorPartida(f"No se pudo leer el archivo de partida: {error}") from error

    # ------------------------------------------------------------------ interno

    def _abrir(self):
        if not os.path.isfile(self.ruta):
            raise ErrorPartida(f"No existe el archivo de partida {self.ruta!r}")
        return open(self.ruta, "rb")

    @staticmethod
    def _leer_pie(archivo) -> tuple:
        """Valida encabezado y pie. Devuelve (pos_secciones, largo_secciones, pos_tabla, cantidad_salas)."""
        archivo.seek(0, os.SEEK_END)
        tamano = archivo.tell()
        if tamano < _ENCABEZADO.size + _PIE.size:
            raise ErrorPartida("El archivo es demasiado corto para ser una partida de Cripta")
        archivo.seek(0)
        magia, version = _ENCABEZADO.unpack(archivo.read(_ENCABEZADO.size))
        if magia != MAGIA:
            raise ErrorPartida("El archivo no es una partida guardada de Cripta")
        if version != VERSION_FORMATO:
            raise ErrorPartida(
                f"Versión del formato de partida no soportada: {version} (este programa usa la {VERSION_FORMATO})"
            )
        archivo.seek(tamano - _PIE.size)
        pos_secciones, largo_secciones, pos_tabla, cantidad, marca = _PIE.unpack(archivo.read(_PIE.size))
        fin_tabla = pos_tabla + cantidad * _ENTRADA_SALA.size
        if (
            marca != MARCA_FIN
            or pos_secciones < _ENCABEZADO.size
            or pos_secciones + largo_secciones != pos_tabla
            or fin_tabla != tamano - _PIE.size
        ):
            raise ErrorPartida("El archivo de partida está incompleto o dañado")
        return pos_secciones, largo_secciones, pos_tabla, cantidad

    @staticmethod
    def _leer_secciones(archivo, pie: tuple) -> list:
        archivo.seek(pie[0])
        lector = Lector(archivo.read(pie[1]))
        secciones = []
        for _ in range(lector.natural()):
            secciones.append((lector.texto(), lector.natural(), lector.natural(), lector.natural()))
        if not lector.al_final():
            raise ErrorPartida("El índice del archivo de partida está dañado")
        return secciones

    @staticmethod
    def _entrada(archivo, pie: tuple, i: int) -> tuple:
        archivo.seek(pie[2] + i * _ENTRADA_SALA.size)
        return _ENTRADA_SALA.unpack(archivo.read(_ENTRADA_SALA.size))

    def _leer_seccion(self, archivo, secciones: list, nombre: str):
        for entrada in secciones:                                # son pocas: búsqueda en orden
            if entrada[0] == nombre:
                return self._leer_bloque(archivo, entrada[1], entrada[2], entrada[3])
        raise ErrorPartida(f"Al archivo de partida le falta la sección {nombre!r}")

    def _leer_sala_en(self, archivo, entrada: tuple) -> SalaGuardadaDTO:
        sala = self._leer_bloque(archivo, entrada[1], entrada[2], entrada[3])
        if not isinstance(sala, SalaGuardadaDTO) or sala.id != entrada[0]:
            raise ErrorPartida(f"El bloque de la sala {entrada[0]} no es una sala válida")
        return sala

    @staticmethod
    def _leer_bloque(archivo, posicion: int, largo: int, crc: int):
        archivo.seek(posicion)
        datos = archivo.read(largo)
        if len(datos) != largo or zlib.crc32(datos) != crc:
            raise ErrorPartida("Un bloque del archivo de partida está dañado (no coincide su CRC)")
        return de_bytes(datos)

    @staticmethod
    def _borrar(ruta: str) -> None:
        try:
            if os.path.exists(ruta):
                os.remove(ruta)
        except OSError:
            pass
