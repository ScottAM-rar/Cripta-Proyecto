"""Llaves (capacidad 009, FR-322, FR-323, SC-001, SC-002): cuánto cuesta guardar y validar la ubicación de las llaves
y cuántas solicitudes hace la consulta. Sin red ni vista; todo en carpetas temporales.

Cada sección mide la decisión elegida y la ALTERNATIVA DESCARTADA (principio VII). Las alternativas descartadas existen
SOLO en este archivo (T033):

  A. Presupuesto con cazadores     (pendiente: grupo I2, ServicioPrecargaPorCosto)
  B. Guardar llaves                elegida: clave «llaves» dentro de cripta_<id>.bin (AlmacenDisco)
                                   descartada: archivo aparte llaves_<id>.bin con su propia versión
  C. Entradas repetidas            elegida: ordenar las posiciones (ordenar_adaptativo) y comparar vecinas, O(k log k)
                                   descartada: comparar todas las parejas, O(k²)
  D. Una solicitud por cripta      la primera partida, la segunda con la misma versión y --offline: 1, 0 y 0 consultas

Regla de salida: False si la verificación de B o de C falla, si la opción A de B supera los 50 ms al guardar con
5 000 salas (mediana; research.md §4) o si D no da exactamente 1, 0 y 0. Los demás tiempos solo informan.
"""
from __future__ import annotations

import contextlib
import os
import tempfile

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.Archivo_indexado import ArchivoIndexado
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.fabrica import crear_servicio
from adaptadores.llaves import LlavesInvalidas, validar_llaves
from adaptadores.servicioCripta import ServicioCripta
from bench.datos import azar, salida_muda
from bench.medicion import anotar, medir, nota, texto, verificar
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from tests_labs.api_falsa import cripta_v2

SECCION_B = "Llaves (B): guardar y leer, clave en cripta_<id>.bin frente a archivo aparte (research.md §4)"
SECCION_C = "Llaves (C): entradas repetidas, ordenar frente a todas las parejas (research.md §5)"
SECCION_D = "Llaves (D): una solicitud por cripta: primera partida, segunda y --offline (SC-001, SC-002)"

SALAS_B = (50, 500, 5000)
LLAVES_B = 20
LIMITE_GUARDAR_US = 50_000          # 50 ms con 5 000 salas (research.md §4)
TAMANOS_C = (10, 100, 1000)
CRIPTA = "cripta-01"


# ----------------------------------------------------------------------------------------------------------------
# Alternativas descartadas (solo existen aquí)
# ----------------------------------------------------------------------------------------------------------------
class GuardadoLlavesAparte:
    """Opción B de research.md §4: llaves_<id>.bin con su propia clave version, sobre ArchivoIndexado."""

    def __init__(self, carpeta: str) -> None:
        self.carpeta = carpeta

    def _archivo(self, cripta_id: str) -> ArchivoIndexado:
        return ArchivoIndexado(os.path.join(self.carpeta, f"llaves_{cripta_id}.bin"))

    def guardar(self, cripta_id: str, version: str, llaves: list) -> None:
        self._archivo(cripta_id).escribir_varios([("version", version), ("llaves", llaves)])

    def leer(self, cripta_id: str, version: str) -> list | None:
        """None si no hay nada guardado o si está guardado con otra versión (la opción B valida su propio archivo)."""
        archivo = self._archivo(cripta_id)
        if archivo.leer("version") != version:
            return None
        return archivo.leer("llaves")


def repetidas_por_parejas(crudas: list) -> None:
    """Detección de entradas idénticas comparando todas las parejas, O(k²). Mismo resultado que el paso 3 de
    validar_llaves: lanza LlavesInvalidas con el mismo mensaje si hay una repetida; si no, no devuelve nada."""
    for i in range(len(crudas)):
        clave_i = (crudas[i]["id"], crudas[i]["sala"], crudas[i].get("enemigo") or "")
        for j in range(i + 1, len(crudas)):
            if clave_i == (crudas[j]["id"], crudas[j]["sala"], crudas[j].get("enemigo") or ""):
                raise LlavesInvalidas(f"la llave {crudas[j]['id']} aparece repetida en la sala {crudas[j]['sala']}")


# ----------------------------------------------------------------------------------------------------------------
# Datos sintéticos
# ----------------------------------------------------------------------------------------------------------------
def _llaves_sinteticas(k: int, salas: int, rng) -> list:
    """k entradas válidas y sin repetir (cada una con su id), en salas 1..salas elegidas con la semilla."""
    llaves = []
    for i in range(k):
        llaves.append({"id": f"itm_llave_{i}", "sala": rng.randint(1, salas)})
    return llaves


def _guardar_cripta_con_contenido(almacen: AlmacenDisco, cripta_id: str, salas: int) -> None:
    """Archivo cripta_<id>.bin como lo deja el juego: versión, datos, esqueleto y el contenido de todas las salas."""
    almacen.validar_cripta(cripta_id, "c1")
    almacen.guardar_datos(cripta_id, {"id": cripta_id, "salas_total": salas, "version": "c1"})
    esqueleto = []
    contenidos = []
    numeros = []
    for n in range(1, salas + 1):
        salidas = {}
        if n > 1:
            salidas["O"] = {"sala": n - 1, "costo": 1 + n % 9}
        if n < salas:
            salidas["E"] = {"sala": n + 1, "costo": 1 + (n + 1) % 9}
        esqueleto.append({"id": n, "nombre": f"Sala {n}", "salidas": salidas})
        contenidos.append({"sala": n, "enemigos": [{"instancia": f"e-{n}", "tipo": "ent_rata_gigante", "vida": None}],
                           "objetos": ["itm_pocion_menor"], "trampas": []})
        numeros.append(n)
    almacen.guardar_salas(cripta_id, esqueleto)
    almacen.guardar_contenido(cripta_id, numeros, contenidos)


# ----------------------------------------------------------------------------------------------------------------
# Secciones
# ----------------------------------------------------------------------------------------------------------------
def _seccion_b(filas: list, raiz: str) -> bool:
    cumple = True
    rng = azar(9)
    llaves = _llaves_sinteticas(LLAVES_B, SALAS_B[0], rng)
    nota(filas, SECCION_B, f"{LLAVES_B} llaves; el archivo de la cripta ya tiene esqueleto y contenido de todas las salas")
    for salas in SALAS_B:
        carpeta = os.path.join(raiz, f"b_{salas}")
        cripta_id = f"cripta-{salas}"
        almacen = AlmacenDisco(carpeta)
        aparte = GuardadoLlavesAparte(carpeta)
        _guardar_cripta_con_contenido(almacen, cripta_id, salas)          # fuera del cronómetro

        almacen.guardar_llaves(cripta_id, llaves)
        aparte.guardar(cripta_id, "c1", llaves)
        if not verificar(filas, SECCION_B, f"{salas} salas: A y B guardan y leen la misma lista",
                         almacen.leer_llaves(cripta_id) == llaves == aparte.leer(cripta_id, "c1")):
            cumple = False
            continue

        guardar_a = anotar(filas, SECCION_B, f"{salas:>5} salas  guardar  [A: clave en cripta_<id>.bin, elegida]",
                           medir(lambda: almacen.guardar_llaves(cripta_id, llaves)))
        anotar(filas, SECCION_B, f"{salas:>5} salas  guardar  [B: llaves_<id>.bin, descartada]",
               medir(lambda: aparte.guardar(cripta_id, "c1", llaves)))
        anotar(filas, SECCION_B, f"{salas:>5} salas  leer     [A: clave en cripta_<id>.bin, elegida]",
               medir(lambda: almacen.leer_llaves(cripta_id)))
        anotar(filas, SECCION_B, f"{salas:>5} salas  leer     [B: llaves_<id>.bin, descartada]",
               medir(lambda: aparte.leer(cripta_id, "c1")))
        if salas == SALAS_B[-1]:
            dentro = guardar_a <= LIMITE_GUARDAR_US
            filas.append((SECCION_B, f"guardar con A y {salas} salas ≤ 50 ms (research.md §4)",
                          "CUMPLE" if dentro else "NO CUMPLE", texto(guardar_a)))
            cumple = cumple and dentro
    return cumple


def _seccion_c(filas: list) -> bool:
    cumple = True
    rng = azar(10)
    for k in TAMANOS_C:
        salas = max(10, k)
        existe = [False] + [True] * salas
        crudas = _llaves_sinteticas(k, salas, rng)
        con_repetida = crudas + [dict(crudas[k // 2])]

        def real(lista):
            validar_llaves(lista, existe, lambda _sala: None)

        def detecta(funcion, lista):
            try:
                funcion(lista)
            except LlavesInvalidas as error:
                return "repetida" in error.motivo
            return False

        iguales = (detecta(real, crudas) is False and detecta(repetidas_por_parejas, crudas) is False
                   and detecta(real, con_repetida) is True and detecta(repetidas_por_parejas, con_repetida) is True)
        if not verificar(filas, SECCION_C, f"k = {k}: las dos detectan la repetida y no inventan otra", iguales):
            cumple = False
            continue
        anotar(filas, SECCION_C, f"k = {k:>4}  validar_llaves real  [ordenar y comparar vecinas, elegida]",
               medir(lambda: real(crudas)))
        anotar(filas, SECCION_C, f"k = {k:>4}  solo repetidas       [todas las parejas, descartada]",
               medir(lambda: repetidas_por_parejas(crudas)))
    nota(filas, SECCION_C, "la elegida incluye además las demás reglas de FR-311; los tiempos solo informan")
    return cumple


def _partida(servicio) -> EstadoJuegoLogica:
    logica = EstadoJuegoLogica(comunicacion=servicio)
    with contextlib.redirect_stdout(salida_muda()):
        logica.iniciarJuego(CRIPTA, 1)
    return logica


def _seccion_d(filas: list, raiz: str) -> bool:
    carpeta = os.path.join(raiz, "d")

    http_1 = cripta_v2(semilla=0)
    servicio_1 = ServicioCripta(ClientePersistente(http_1, AlmacenDisco(carpeta)), CacheLRU(25))
    logica_1 = _partida(servicio_1)
    with contextlib.redirect_stdout(salida_muda()):
        servicio_1.construir_todas(CRIPTA)          # la partida recorrió la cripta: queda completa para --offline
    primera = http_1.veces("llaves")

    http_2 = cripta_v2(semilla=0)
    logica_2 = _partida(ServicioCripta(ClientePersistente(http_2, AlmacenDisco(carpeta)), CacheLRU(25)))
    segunda = http_2.veces("llaves")

    servicio_3 = crear_servicio(offline=True, carpeta=carpeta)
    logica_3 = _partida(servicio_3)
    offline = servicio_3.solicitudes_realizadas

    filas.append((SECCION_D, "primera partida (carpeta vacía)", primera, "consultas («llaves», …)"))
    filas.append((SECCION_D, "segunda partida, misma versión", segunda, "consultas («llaves», …)"))
    filas.append((SECCION_D, "--offline", offline, "solicitudes de red"))
    entregadas = (logica_1.llaves is not None and logica_2.llaves is not None and logica_3.llaves is not None
                  and logica_3.llaves.ids == logica_1.llaves.ids)
    verificar(filas, SECCION_D, "las tres partidas reciben la misma lista de llaves", entregadas)
    cumple = primera == 1 and segunda == 0 and offline == 0 and entregadas
    filas.append((SECCION_D, "1 / 0 / 0", "CUMPLE" if cumple else "NO CUMPLE", f"{primera} / {segunda} / {offline}"))
    return cumple


def ejecutar(filas: list) -> bool:
    nota(filas, SECCION_B, "sección A (presupuesto con cazadores): pendiente, grupo I2")
    with tempfile.TemporaryDirectory() as raiz:
        cumple_b = _seccion_b(filas, raiz)
        cumple_c = _seccion_c(filas)
        cumple_d = _seccion_d(filas, raiz)
    return cumple_b and cumple_c and cumple_d
