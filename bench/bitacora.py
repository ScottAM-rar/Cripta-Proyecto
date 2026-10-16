"""§4.8 y §4.11 Bitácoras: la de mensajes en pantalla (cola enlazada de 20) y el log de acciones (lista enlazada + texto).

Alternativas descartadas, que existen SOLO aquí: buffer circular para los mensajes y arreglo dinámico para el log.
"""
from __future__ import annotations

import os
import tempfile

from DTO.LogPartidaDTO import LogPartidaDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.BitacoraLogica import BitacoraLogica
from Logica.LogEventos import LogEventos
from adaptadores.AlmacenLogTexto import AlmacenLogTexto
from bench.medicion import anotar, medir, nota, verificar

SECCION = "Bitácoras (§4.8, §4.11): cola enlazada y lista enlazada  vs  buffer circular y arreglo"
MENSAJES = 20_000
ACCIONES = (1_000, 10_000)
LINEAS_EN_DISCO = 300


class BufferCircular:
    """ALTERNATIVA DESCARTADA para la bitácora de 20 mensajes."""

    def __init__(self, capacidad: int = 20) -> None:
        self.capacidad = capacidad
        self.datos: list = [None] * capacidad
        self.inicio = 0
        self.cantidad = 0

    def agregar_evento(self, resultado) -> None:
        if self.cantidad < self.capacidad:
            self.datos[(self.inicio + self.cantidad) % self.capacidad] = resultado
            self.cantidad += 1
        else:
            self.datos[self.inicio] = resultado
            self.inicio = (self.inicio + 1) % self.capacidad

    def obtener_eventos(self) -> list:
        return [self.datos[(self.inicio + i) % self.capacidad] for i in range(self.cantidad)]


def _mensajes(estructura, resultados: list) -> None:
    for resultado in resultados:
        estructura.agregar_evento(resultado)


def ejecutar(filas: list) -> None:
    resultados = [ResultadoEventoDTO(True, f"mensaje {i}") for i in range(MENSAJES)]
    a, b = BitacoraLogica(), BufferCircular(20)
    _mensajes(a, resultados)
    _mensajes(b, resultados)
    verificar(filas, SECCION, "ambas dejan los mismos 20 últimos mensajes, en el mismo orden",
              [r.mensaje for r in a.obtener_eventos()] == [r.mensaje for r in b.obtener_eventos()])
    anotar(filas, SECCION, f"{MENSAJES} mensajes con la bitácora ya llena        [cola enlazada]",
           medir(lambda e: _mensajes(e, resultados), BitacoraLogica))
    anotar(filas, SECCION, f"{MENSAJES} mensajes con la bitácora ya llena        [buffer circular]",
           medir(lambda e: _mensajes(e, resultados), lambda: BufferCircular(20)))

    for n in ACCIONES:
        lineas = [f'{{"tipo_accion": "ESPERAR", "tiempo_ejecucion": {i}, "actor": {{"tipo": "jugador"}}, "datos_extra": []}}'
                  for i in range(n)]

        def registrar_lista(log):
            for linea in lineas:
                log.agregar(linea)

        def registrar_arreglo(arreglo):
            for linea in lineas:
                arreglo.append(linea.strip())
        anotar(filas, SECCION, f"{n:>6} acciones registradas en memoria           [lista enlazada]",
               medir(registrar_lista, lambda: LogEventos(1, "bench")))
        anotar(filas, SECCION, f"{n:>6} acciones registradas en memoria           [arreglo]",
               medir(registrar_arreglo, list))

    with tempfile.TemporaryDirectory() as carpeta:
        cabecera = LogPartidaDTO("bench", 1, "v1", "k1", [])

        def preparar_disco():
            almacen = AlmacenLogTexto(None, carpeta)
            almacen.abrir(cabecera)
            return almacen

        def anexar(almacen):
            for i in range(LINEAS_EN_DISCO):
                almacen.agregar(f'{{"tipo_accion": "ESPERAR", "tiempo_ejecucion": {i}}}')
        anotar(filas, SECCION, f"{LINEAS_EN_DISCO} líneas anexadas al .log (abre y cierra el archivo en cada acción)  [juego]",
               medir(anexar, preparar_disco, repeticiones=3))
        total = anotar(filas, SECCION, "  (lo mismo con el archivo abierto una sola vez, sin cerrarlo)           [alternativa]",
                       medir(lambda a: [a.write("x\n") for _ in range(LINEAS_EN_DISCO)],
                             lambda: open(os.path.join(carpeta, "alt.log"), "a", encoding="utf-8"), repeticiones=3))
    nota(filas, SECCION, "El .log es de solo anexado y se escribe en el momento de cada acción para que sobreviva a un cierre inesperado: esa durabilidad es lo que cuesta abrir y cerrar el archivo.")
