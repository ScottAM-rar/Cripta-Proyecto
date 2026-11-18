"""§4.10 Guardado binario de la partida contra el mismo estado guardado como JSON.

Para el JSON se convierte el EstadoGuardadoDTO con dataclasses.asdict (así guarda EXACTAMENTE lo mismo). Su "carga"
solo analiza el texto: no reconstruye los DTO, lo que le da ventaja al JSON; si aun así pierde, la conclusión es firme.

Capacidad 012 (§5.6): la partida lleva la carga de la Parte II (un cazador con rango por sala, costo en cada salida y
el conocimiento del jugador de la mitad de las salas). Al final del bloque (G28 en adelante) van las filas nuevas de
FR-381 y FR-382: bytes leídos y entradas de la tabla al cargar UNA sala (la primera, la del medio y la última) y el
tiempo de la primera y la última. Los bytes se cuentan con una subclase de medición; la clase de producción no cambia.
"""
from __future__ import annotations

import dataclasses
import json
import os
import tempfile

from DTO.EstadoGuardadoDTO import (
    ConocimientoGuardadoDTO, EnemigoGuardadoDTO, ObjetoGuardadoDTO, SalaGuardadaDTO, SalidaGuardadaDTO,
    TrampaGuardadaDTO,
)
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida
from bench.datos import azar
from bench.medicion import anotar, medir, nota, verificar
from bench.juego import partida_base

SECCION = "Guardado de la partida (§4.10): binario propio  vs  JSON"
SALAS = (10, 100, 1_000)


def estado_con_salas(base, n: int):
    """Una partida real exportada, con `n` salas sintéticas (3 salidas, 2 enemigos, 2 objetos y 1 trampa por sala).

    012: el segundo enemigo de cada sala es un cazador con rango 600, cada salida lleva un costo entre 1 y 9 del
    mismo generador, y el jugador conoce la mitad de las salas (exploradas las impares, avistadas las pares)."""
    rng = azar(n)
    estado = dataclasses.replace(base)
    salas, enemigos, trampas = [], [], []
    for numero in range(1, n + 1):
        posiciones_enemigos = []
        for k in range(2):
            posiciones_enemigos.append(len(enemigos))
            if k == 0:
                enemigos.append(EnemigoGuardadoDTO(f"e-{numero}{k}", "ent_rata_gigante", "Rata gigante", "rastreador",
                                                   rng.randrange(1, 20), 20, 5, 1, 150, numero, ["itm_pocion_menor"], True))
            else:
                enemigos.append(EnemigoGuardadoDTO(f"e-{numero}{k}", "ent_cazador", "Cazador", "cazador",
                                                   rng.randrange(1, 20), 20, 5, 1, 150, numero, ["itm_pocion_menor"], True,
                                                   rango=600))
        posicion_trampa = len(trampas)
        trampas.append(TrampaGuardadaDTO(f"t-{numero}", "trp_pinchos", numero, 10, 300, True))
        salas.append(SalaGuardadaDTO(
            numero, f"Sala número {numero}", rng.randrange(0, 5000),
            [SalidaGuardadaDTO(d, max(1, numero + delta), False, None, None, rng.randint(1, 9))
             for d, delta in (("N", -1), ("S", 1), ("E", 10))],
            posiciones_enemigos,
            [ObjetoGuardadoDTO("Arma", [f"itm_{numero}_{k}", "Daga", 3, 20, numero, 4]) for k in range(2)],
            [posicion_trampa],
        ))
    estado.salas, estado.enemigos, estado.trampas, estado.total_salas = salas, enemigos, trampas, n
    estado.conocimiento = ConocimientoGuardadoDTO(exploradas=list(range(1, n + 1, 2)),
                                                  avistadas=list(range(2, n + 1, 2)))
    return estado


class _ArchivoContador:
    """Envoltorio de medición sobre el archivo abierto: suma los bytes que devuelve cada `read`."""

    def __init__(self, archivo, almacen) -> None:
        self._archivo = archivo
        self._almacen = almacen

    def read(self, cuantos: int = -1) -> bytes:
        datos = self._archivo.read(cuantos)
        self._almacen.bytes_leidos += len(datos)
        return datos

    def seek(self, *args):
        return self._archivo.seek(*args)

    def tell(self) -> int:
        return self._archivo.tell()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._archivo.close()
        return False


class _AlmacenContador(AlmacenPartidaBinario):
    """Subclase de MEDICIÓN (012): cuenta los bytes leídos y las entradas de la tabla que se leen. No cambia nada
    del formato ni de la lógica de la clase de producción."""

    def __init__(self, ruta: str) -> None:
        super().__init__(ruta)
        self.bytes_leidos = 0
        self.entradas_leidas = 0

    def _abrir(self):
        return _ArchivoContador(super()._abrir(), self)

    def _entrada(self, archivo, pie, i):
        self.entradas_leidas += 1
        return AlmacenPartidaBinario._entrada(archivo, pie, i)


def _filas_de_una_sala(filas_nuevas: list, almacen, ruta_bin: str, n: int, tamano_bin: int) -> None:
    """Filas nuevas de FR-381 y FR-382 para una partida de `n` salas (van al final del bloque)."""
    contador = _AlmacenContador(ruta_bin)
    medio = n // 2 + 1
    bytes_ok, entradas_max = True, 0
    for cual, numero in (("la primera", 1), ("la del medio", medio), ("la última", n)):
        contador.bytes_leidos = contador.entradas_leidas = 0
        sala = contador.leer_sala(numero)
        bytes_ok = bytes_ok and sala is not None and sala.id == numero and contador.bytes_leidos < tamano_bin
        if contador.entradas_leidas > entradas_max:
            entradas_max = contador.entradas_leidas
        filas_nuevas.append((SECCION, f"{n:>5} salas  bytes leídos al cargar UNA sala ({cual}, la {numero})",
                             f"{contador.bytes_leidos:,}",
                             f"bytes de {tamano_bin:,} del archivo; {contador.entradas_leidas} entradas de la tabla"))
    anotar(filas_nuevas, SECCION, f"{n:>5} salas  cargar UNA sala (la primera, la 1)    [binario, acceso directo]",
           medir(lambda: almacen.leer_sala(1), repeticiones=9))
    anotar(filas_nuevas, SECCION, f"{n:>5} salas  cargar UNA sala (la última, la {n})    [binario, acceso directo]",
           medir(lambda: almacen.leer_sala(n), repeticiones=9))
    verificar(filas_nuevas, SECCION, f"{n} salas: leer UNA sala lee menos bytes que el archivo", bytes_ok)
    verificar(filas_nuevas, SECCION, f"{n} salas: entradas leídas ({entradas_max}) ≤ ⌊log₂ n⌋ + 1 = {n.bit_length()}",
              entradas_max <= n.bit_length())


def _a_json(estado) -> str:
    return json.dumps(dataclasses.asdict(estado), ensure_ascii=False, separators=(",", ":"))


def ejecutar(filas: list) -> None:
    base = partida_base()
    filas_nuevas: list = []                       # 012: G28 en adelante, después de la nota final
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
            _filas_de_una_sala(filas_nuevas, almacen, ruta_bin, n, tamano_bin)
    nota(filas, SECCION, "El binario ordena las salas en una tabla de entradas fijas y busca con búsqueda binaria; el JSON no puede saltar a una sala.")
    filas.extend(filas_nuevas)
