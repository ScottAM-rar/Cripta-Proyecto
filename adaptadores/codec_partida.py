"""Codificación binaria propia de los DTOs de una partida guardada.

Sin pickle, sin json y sin diccionarios. Cada valor lleva una marca de un byte que dice qué es:
  0 None | 1 falso | 2 verdadero | 3 entero | 4 flotante | 5 texto | 6 lista | 7 DTO
Los enteros usan largo variable (7 bits por byte, con signo en zigzag): los números chicos ocupan un byte.
Un DTO se escribe como: índice de su clase en CLASES_DTO, cantidad de campos y los campos en orden.
"""
from __future__ import annotations

import dataclasses
import struct

from DTO.EstadoGuardadoDTO import (
    ObjetoGuardadoDTO, EnemigoGuardadoDTO, TrampaGuardadaDTO, SalidaGuardadaDTO, SalaGuardadaDTO,
    ReferenciaGuardadaDTO, EventoGuardadoDTO, RelojGuardadoDTO, JugadorGuardadoDTO, MensajeGuardadoDTO,
)

# El orden es parte del formato: agregar al final, nunca reordenar (y subir la versión del archivo).
CLASES_DTO = (
    ObjetoGuardadoDTO, EnemigoGuardadoDTO, TrampaGuardadaDTO, SalidaGuardadaDTO, SalaGuardadaDTO,
    ReferenciaGuardadaDTO, EventoGuardadoDTO, RelojGuardadoDTO, JugadorGuardadoDTO, MensajeGuardadoDTO,
)

_NADA, _FALSO, _VERDADERO, _ENTERO, _FLOTANTE, _TEXTO, _LISTA, _DTO = 0, 1, 2, 3, 4, 5, 6, 7
_FLOTANTE_STRUCT = struct.Struct(">d")


class ErrorCodec(ValueError):
    """Los datos no se pueden codificar, o los bytes no son una codificación válida."""


# --------------------------------------------------------------------------- escritura

def escribir_natural(salida: bytearray, numero: int) -> None:
    if numero < 0:
        raise ErrorCodec("Se esperaba un natural")
    while True:
        byte = numero & 0x7F
        numero >>= 7
        if numero:
            salida.append(byte | 0x80)
        else:
            salida.append(byte)
            return


def escribir_entero(salida: bytearray, numero: int) -> None:
    escribir_natural(salida, numero * 2 if numero >= 0 else -numero * 2 - 1)   # zigzag


def escribir_texto(salida: bytearray, texto: str) -> None:
    datos = texto.encode("utf-8")
    escribir_natural(salida, len(datos))
    salida.extend(datos)


def codificar(valor, salida: bytearray) -> None:
    if valor is None:
        salida.append(_NADA)
    elif valor is False:
        salida.append(_FALSO)
    elif valor is True:
        salida.append(_VERDADERO)
    elif isinstance(valor, int):
        salida.append(_ENTERO)
        escribir_entero(salida, valor)
    elif isinstance(valor, float):
        salida.append(_FLOTANTE)
        salida.extend(_FLOTANTE_STRUCT.pack(valor))
    elif isinstance(valor, str):
        salida.append(_TEXTO)
        escribir_texto(salida, valor)
    elif isinstance(valor, (list, tuple)):
        salida.append(_LISTA)
        escribir_natural(salida, len(valor))
        for elemento in valor:
            codificar(elemento, salida)
    elif dataclasses.is_dataclass(valor):
        indice = _indice_de_clase(type(valor))
        campos = dataclasses.fields(valor)
        salida.append(_DTO)
        escribir_natural(salida, indice)
        escribir_natural(salida, len(campos))
        for campo in campos:
            codificar(getattr(valor, campo.name), salida)
    else:
        raise ErrorCodec(f"No se puede guardar un valor de tipo {type(valor).__name__}")


def _indice_de_clase(clase) -> int:
    for i in range(len(CLASES_DTO)):
        if CLASES_DTO[i] is clase:
            return i
    raise ErrorCodec(f"{clase.__name__} no forma parte del formato de partida")


def a_bytes(valor) -> bytes:
    salida = bytearray()
    codificar(valor, salida)
    return bytes(salida)


# --------------------------------------------------------------------------- lectura

class Lector:
    """Recorre unos bytes de izquierda a derecha."""

    def __init__(self, datos: bytes, posicion: int = 0):
        self.datos = datos
        self.posicion = posicion

    def byte(self) -> int:
        if self.posicion >= len(self.datos):
            raise ErrorCodec("Los datos terminan antes de lo esperado")
        valor = self.datos[self.posicion]
        self.posicion += 1
        return valor

    def trozo(self, largo: int) -> bytes:
        if largo < 0 or self.posicion + largo > len(self.datos):
            raise ErrorCodec("Los datos terminan antes de lo esperado")
        trozo = self.datos[self.posicion:self.posicion + largo]
        self.posicion += largo
        return trozo

    def natural(self) -> int:
        resultado = 0
        desplazamiento = 0
        while True:
            byte = self.byte()
            resultado |= (byte & 0x7F) << desplazamiento
            if not byte & 0x80:
                return resultado
            desplazamiento += 7
            if desplazamiento > 70:
                raise ErrorCodec("Entero demasiado largo")

    def entero(self) -> int:
        zigzag = self.natural()
        return zigzag >> 1 if zigzag % 2 == 0 else -((zigzag + 1) >> 1)

    def texto(self) -> str:
        try:
            return self.trozo(self.natural()).decode("utf-8")
        except UnicodeDecodeError as error:
            raise ErrorCodec("Texto inválido en los datos") from error

    def al_final(self) -> bool:
        return self.posicion == len(self.datos)


def decodificar(lector: Lector):
    marca = lector.byte()
    if marca == _NADA:
        return None
    if marca == _FALSO:
        return False
    if marca == _VERDADERO:
        return True
    if marca == _ENTERO:
        return lector.entero()
    if marca == _FLOTANTE:
        return _FLOTANTE_STRUCT.unpack(lector.trozo(_FLOTANTE_STRUCT.size))[0]
    if marca == _TEXTO:
        return lector.texto()
    if marca == _LISTA:
        cantidad = lector.natural()
        if cantidad > len(lector.datos) - lector.posicion:      # cada elemento ocupa al menos un byte
            raise ErrorCodec("Lista más larga que los datos")
        return [decodificar(lector) for _ in range(cantidad)]
    if marca == _DTO:
        indice = lector.natural()
        if indice >= len(CLASES_DTO):
            raise ErrorCodec("Clase desconocida en los datos")
        clase = CLASES_DTO[indice]
        cantidad = lector.natural()
        if cantidad != len(dataclasses.fields(clase)):
            raise ErrorCodec(f"{clase.__name__} tiene otra cantidad de campos que la del archivo")
        return clase(*[decodificar(lector) for _ in range(cantidad)])
    raise ErrorCodec(f"Marca desconocida en los datos: {marca}")


def de_bytes(datos: bytes):
    lector = Lector(datos)
    valor = decodificar(lector)
    if not lector.al_final():
        raise ErrorCodec("Sobran datos al final")
    return valor
