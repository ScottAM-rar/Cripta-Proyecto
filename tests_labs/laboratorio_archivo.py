"""Laboratorio: mirar POR DENTRO un ArchivoIndexado.
 
Ejecutar desde la raíz del proyecto:
    py -m tests_labs.laboratorio_archivo
"""
import os
import struct
import tempfile
 
from adaptadores.Archivo_indexado import ArchivoIndexado
 
with tempfile.TemporaryDirectory() as carpeta:
    ruta = os.path.join(carpeta, "demo.bin")
    archivo = ArchivoIndexado(ruta)
 
    # 1) Guardamos tres cosas
    archivo.escribir("version", "fd58f7743b9e")
    archivo.escribir("ent_rata", {"vida_max": 12, "comportamiento": "rastreador"})
    archivo.escribir("itm_daga", {"ataque_bonus": 3})
 
    print("1) Lo que guardamos, visto desde fuera:")
    print("   claves:", archivo.claves())
    print("   leer('ent_rata') ->", archivo.leer("ent_rata"))
 
    # 2) Abrimos el archivo "a mano", sin usar la clase, para ver los bytes
    with open(ruta, "rb") as f:
        todo = f.read()
    print()
    print(f"2) El archivo mide {len(todo)} bytes.")
    print("   Primeros 6 bytes (encabezado):", todo[:6])
 
    # 3) El pie: los últimos 12 bytes dicen dónde está el índice
    pos_indice, cantidad = struct.unpack(">QI", todo[-12:])
    print()
    print("3) Pie (últimos 12 bytes): el índice empieza en el byte",
          pos_indice, "y tiene", cantidad, "entradas")
 
    # 4) Leemos el índice a mano
    print()
    print("4) El índice, entrada por entrada:")
    cursor = pos_indice
    for _ in range(cantidad):
        (largo_clave,) = struct.unpack(">H", todo[cursor:cursor + 2])
        cursor += 2
        clave = todo[cursor:cursor + largo_clave].decode("utf-8")
        cursor += largo_clave
        posicion, largo = struct.unpack(">QI", todo[cursor:cursor + 12])
        cursor += 12
        registro = todo[posicion:posicion + largo]
        print(f"   clave {clave!r:12} -> empieza en el byte {posicion:3}, mide {largo:2} bytes: {registro}")