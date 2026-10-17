"""§4.10 Guardado binario de la partida contra el mismo estado guardado como JSON.

Para el JSON se convierte el EstadoGuardadoDTO con dataclasses.asdict (así guarda EXACTAMENTE lo mismo). Su "carga"
solo analiza el texto: no reconstruye los DTO, lo que le da ventaja al JSON; si aun así pierde, la conclusión es firme.
"""
from __future__ import annotations

import dataclasses
import json
import os
import tempfile

from DTO.EstadoGuardadoDTO import (
    EnemigoGuardadoDTO, ObjetoGuardadoDTO, SalaGuardadaDTO, SalidaGuardadaDTO, TrampaGuardadaDTO,
)
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida
from bench.datos import azar
from bench.medicion import anotar, medir, nota, verificar
from bench.juego import partida_base

SECCION = "Guardado de la partida (§4.10): binario propio  vs  JSON"
SALAS = (10, 100, 1_000)


def estado_con_salas(base, n: int):
    """Una partida real exportada, con `n` salas sintéticas (3 salidas, 2 enemigos, 2 objetos y 1 trampa por sala)."""
    rng = azar(n)
    estado = dataclasses.replace(base)
    salas, enemigos, trampas = [], [], []
    for numero in range(1, n + 1):
        posiciones_enemigos = []
        for k in range(2):
            posiciones_enemigos.append(len(enemigos))
            enemigos.append(EnemigoGuardadoDTO(f"e-{numero}{k}", "ent_rata_gigante", "Rata gigante", "rastreador",
                                               rng.randrange(1, 20), 20, 5, 1, 150, numero, ["itm_pocion_menor"], True))
        posicion_trampa = len(trampas)
        trampas.append(TrampaGuardadaDTO(f"t-{numero}", "trp_pinchos", numero, 10, 300, True))
        salas.append(SalaGuardadaDTO(
            numero, f"Sala número {numero}", rng.randrange(0, 5000),
            [SalidaGuardadaDTO(d, max(1, numero + delta), False, None, None) for d, delta in (("N", -1), ("S", 1), ("E", 10))],
            posiciones_enemigos,
            [ObjetoGuardadoDTO("Arma", [f"itm_{numero}_{k}", "Daga", 3, 20, numero, 4]) for k in range(2)],
            [posicion_trampa],
        ))
    estado.salas, estado.enemigos, estado.trampas, estado.total_salas = salas, enemigos, trampas, n
    return estado


def _a_json(estado) -> str:
    return json.dumps(dataclasses.asdict(estado), ensure_ascii=False, separators=(",", ":"))


def ejecutar(filas: list) -> None:
    base = partida_base()
    with tempfile.TemporaryDirectory() as carpeta:
        ruta_bin = os.path.join(carpeta, "partida.bin")
        ruta_json = os.path.join(carpeta, "partida.json")
        for n in SALAS:
            estado = estado_con_salas(base, n)
            almacen = AlmacenPartidaBinario(ruta_bin)
            almacen.guardar(estado)
            if n == SALAS[0]:
                verificar(filas, SECCION, "cargar el binario devuelve exactamente el estado guardado", almacen.cargar() == estado)
                with open(ruta_bin, "rb") as f:
                    datos = bytearray(f.read())
                datos[4] ^= 0xFF                     # estropea el número de versión del formato
                ruta_mala = os.path.join(carpeta, "otra_version.bin")
                with open(ruta_mala, "wb") as f:
                    f.write(datos)
                try:
                    AlmacenPartidaBinario(ruta_mala).cargar()
                    rechazada = False
                except ErrorPartida:
                    rechazada = True
                verificar(filas, SECCION, "un archivo de otra versión del formato se rechaza", rechazada)

            with open(ruta_json, "w", encoding="utf-8") as f:
                f.write(_a_json(estado))
            tamano_bin, tamano_json = os.path.getsize(ruta_bin), os.path.getsize(ruta_json)
            filas.append((SECCION, f"{n:>5} salas  tamaño en disco  [binario]", f"{tamano_bin:,}", "bytes"))
            filas.append((SECCION, f"{n:>5} salas  tamaño en disco  [JSON]", f"{tamano_json:,}",
                          f"bytes  ({tamano_json / tamano_bin:.2f}× el binario)"))

            def guardar_json(e):
                with open(ruta_json, "w", encoding="utf-8") as f:
                    f.write(_a_json(e))

            def cargar_json(_):
                with open(ruta_json, "r", encoding="utf-8") as f:
                    return json.loads(f.read())
            anotar(filas, SECCION, f"{n:>5} salas  guardar la partida completa  [binario]", medir(almacen.guardar, lambda: estado, repeticiones=5))
            anotar(filas, SECCION, f"{n:>5} salas  guardar la partida completa  [JSON]", medir(guardar_json, lambda: estado, repeticiones=5))
            anotar(filas, SECCION, f"{n:>5} salas  cargar la partida completa   [binario → DTO]", medir(lambda: almacen.cargar(), repeticiones=5))
            anotar(filas, SECCION, f"{n:>5} salas  cargar la partida completa   [JSON, solo analiza el texto]", medir(lambda: cargar_json(None), repeticiones=5))
            medio = n // 2 + 1
            anotar(filas, SECCION, f"{n:>5} salas  cargar UNA sala (la {medio})    [binario, acceso directo]", medir(lambda: almacen.leer_sala(medio), repeticiones=9))
            anotar(filas, SECCION, f"{n:>5} salas  conseguir UNA sala (la {medio}) [JSON: hay que leer todo]",
                   medir(lambda: cargar_json(None)["salas"][medio - 1], repeticiones=5))
    nota(filas, SECCION, "El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala.")
