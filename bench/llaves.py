"""Llaves (capacidad 009, FR-322, FR-323, SC-001, SC-002): cuánto cuesta guardar y validar la ubicación de las llaves
y cuántas solicitudes hace la consulta. Sin red ni vista; todo en carpetas temporales.

Cada sección mide la decisión elegida y la ALTERNATIVA DESCARTADA (principio VII). Las alternativas descartadas existen
SOLO en este archivo (T033):

  A. Presupuesto con cazadores     elegida: precarga por saltos (ServicioCripta.precargar_vecinas, sin cambios)
                                   descartada: precarga por costo de ruta (ServicioPrecargaPorCosto)
  B. Guardar llaves                elegida: clave «llaves» dentro de cripta_<id>.bin (AlmacenDisco)
                                   descartada: archivo aparte llaves_<id>.bin con su propia versión
  C. Entradas repetidas            elegida: ordenar las posiciones (ordenar_adaptativo) y comparar vecinas, O(k log k)
                                   descartada: comparar todas las parejas, O(k²)
  D. Una solicitud por cripta      la primera partida, la segunda con la misma versión y --offline: 1, 0 y 0 consultas

Regla de salida: False si la verificación de B o de C falla, si la opción A de B supera los 50 ms al guardar con
5 000 salas (mediana; research.md §4) o si D no da exactamente 1, 0 y 0. Los demás tiempos solo informan. La sección A
solo informa; devuelve False únicamente si falla su verificación previa (la regla no cambia la partida jugada).
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
from Controlador.ControladorJuego import ControladorJuego
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.MonticuloMinimo import MonticuloMinimo
from Logica.ordenamiento import ordenar_adaptativo
from tests_labs.api_falsa import HttpConfigurable, cripta_v2
from tests_labs.cripta_sintetica import esqueleto_rejilla, ficha_cazador

SECCION_A = "Llaves (A): presupuesto con cazadores, precarga por saltos frente a por costo (FR-322, FR-323)"
SECCION_B = "Llaves (B): guardar y leer, clave en cripta_<id>.bin frente a archivo aparte (research.md §4)"
SECCION_C = "Llaves (C): entradas repetidas, ordenar frente a todas las parejas (research.md §5)"
SECCION_D = "Llaves (D): una solicitud por cripta: primera partida, segunda y --offline (SC-001, SC-002)"

SALAS_B = (50, 500, 5000)
LLAVES_B = 20
LIMITE_GUARDAR_US = 50_000          # 50 ms con 5 000 salas (research.md §4)
TAMANOS_C = (10, 100, 1000)
CRIPTA = "cripta-01"

LADOS_A = (10, 20, 40)
CAZADORES_A = (1, 4, 16)
SEMILLAS_A = 5
MOVIMIENTOS_A = 60
DISTANCIA_MINIMA_A = 4               # salidas entre el jugador y cada cazador al empezar
SALA_JUGADOR_A = 1
SALIDA_INEXISTENTE_A = 10 ** 6       # la partida no termina por llegar a la salida
VIDA_JUGADOR_A = 10 ** 9             # el jugador no puede morir durante el guion
PALABRAS = (("N", "norte"), ("S", "sur"), ("E", "este"), ("O", "oeste"))


# ----------------------------------------------------------------------------------------------------------------
# Alternativas descartadas (solo existen aquí)
# ----------------------------------------------------------------------------------------------------------------
class ServicioPrecargaPorCosto(ServicioCripta):
    """Regla descartada de la sección A: precarga por COSTO de ruta. Sobrescribe solo precargar_vecinas y hace lo mismo
    que la original (validaciones, garantía de la sala actual y sus vecinas, devuelve 0 si ya están, límite max_salas,
    indispensables primero y el mismo conjunto de candidatas dentro de `profundidad` saltos). Lo único que cambia es
    el ORDEN con que se llena el resto del lote: costo de la ruta más barata desde la sala actual (suma de los costos
    del esqueleto, ya normalizados: una salida sin costo declarado vale 100; las puertas cerradas no cuentan, igual que
    en salas_vecinas) y, a igual costo, menor id. Dijkstra con MonticuloMinimo sobre esqueleto(); sin deque."""

    def __init__(self, cliente, cache) -> None:
        super().__init__(cliente, cache)
        self._mapa_costos_id: str | None = None
        self._mapa_costos = None
        self.ultimo_lote: list[int] = []          # para la verificación previa del bench

    def _costos_desde(self, cripta_id: str, origen: int) -> list:
        if self._mapa_costos_id != cripta_id:
            self._mapa_costos = self.esqueleto(cripta_id)
            self._mapa_costos_id = cripta_id
        salas = self._mapa_costos.salas
        costo = [None] * len(salas)
        costo[origen] = 0
        monticulo = MonticuloMinimo()
        monticulo.insertar(0, origen)
        while not monticulo.vacio():
            acumulado, sala = monticulo.extraer_minimo()
            if acumulado > costo[sala]:
                continue                                       # entrada vieja: ya se encontró algo más barato
            for arista in salas[sala].salidas:
                nuevo = acumulado + arista.costo
                if costo[arista.destino] is None or nuevo < costo[arista.destino]:
                    costo[arista.destino] = nuevo
                    monticulo.insertar(nuevo, arista.destino)
        return costo

    def precargar_vecinas(self, cripta_id: str, sala_actual: int, profundidad: int | None = None,
                          max_salas: int = 10) -> int:
        if max_salas < 1:
            raise ValueError("max_salas debe ser al menos 1")
        if profundidad is not None and profundidad < 1:
            raise ValueError("La profundidad debe ser al menos 1")
        self._buscar_esqueleto(cripta_id, sala_actual)
        alcance = profundidad if profundidad is not None else len(self._cargar_esqueleto(cripta_id))

        inmediatas = [sala_actual] + self.salas_vecinas(cripta_id, sala_actual, 1)
        if self._estan_listas(cripta_id, inmediatas):
            self.ultimo_lote = []
            return 0

        indispensables: list[int] = []
        for numero in inmediatas:
            if not self._estan_listas(cripta_id, [numero]):
                indispensables.append(numero)

        costo = self._costos_desde(cripta_id, sala_actual)
        candidatas = ordenar_adaptativo(self.salas_vecinas(cripta_id, sala_actual, alcance),
                                        key=lambda n: (costo[n] if costo[n] is not None else 10 ** 12, n))
        lote = list(indispensables)
        limite = max(max_salas, len(indispensables))
        for numero in candidatas:                              # de la más barata a la más cara
            if len(lote) >= limite:
                break
            if numero not in lote and not self._estan_listas(cripta_id, [numero]):
                lote.append(numero)
        self.ultimo_lote = list(lote)
        return self.precargar(cripta_id, lote)


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
def _distancias_en_saltos(salas: list, origen: int) -> list:
    """Salidas mínimas desde `origen` a cada sala (recorrido por niveles con dos listas, sin deque). -1: no se llega."""
    distancia = [-1] * (len(salas) + 1)
    distancia[origen] = 0
    nivel = [origen]
    while nivel:
        siguiente = []
        for numero in nivel:
            for letra, _ in PALABRAS:
                salida = salas[numero - 1]["salidas"].get(letra)
                if salida is not None and distancia[salida["sala"]] < 0:
                    distancia[salida["sala"]] = distancia[numero] + 1
                    siguiente.append(salida["sala"])
        nivel = siguiente
    return distancia


def _cripta_a(lado: int, cazadores: int, semilla: int, costo_max: int):
    """Esqueleto, enemigos (cazadores a DISTANCIA_MINIMA_A o más salidas del jugador) y guion de MOVIMIENTOS_A
    direcciones por salidas abiertas. Todo sale de la semilla; el guion se decide una vez y lo usan las dos reglas."""
    rng = azar(1000 + semilla)
    salas = esqueleto_rejilla(lado, lado, semilla, costo_max=costo_max)
    distancia = _distancias_en_saltos(salas, SALA_JUGADOR_A)
    lejanas = [n for n in range(1, len(salas) + 1) if distancia[n] >= DISTANCIA_MINIMA_A]
    posiciones = rng.sample(lejanas, cazadores)
    enemigos = [(posiciones[i], f"e-{i + 1}", "ent_cazador", None) for i in range(cazadores)]
    guion = []
    actual = SALA_JUGADOR_A
    for _ in range(MOVIMIENTOS_A):
        abiertas = []
        for letra, palabra in PALABRAS:
            salida = salas[actual - 1]["salidas"].get(letra)
            if salida is not None and not salida.get("cerrada"):
                abiertas.append((palabra, salida["sala"]))
        palabra, destino = abiertas[rng.randrange(len(abiertas))]
        guion.append(palabra)
        actual = destino
    return salas, enemigos, guion


def _jugar_a(salas, enemigos, guion, regla, carpeta) -> tuple[int, int, int, int]:
    """Juega el guion con la regla dada sobre una API falsa y una carpeta nuevas. Devuelve (solicitudes totales,
    solicitudes disparadas por un enemigo, sala final del jugador, movimientos hechos)."""
    http = HttpConfigurable(salas, list(enemigos), [ficha_cazador(rango=600)], sala_inicial=SALA_JUGADOR_A,
                            sala_salida=SALIDA_INEXISTENTE_A, vida_jugador=VIDA_JUGADOR_A, llaves=[])
    clase = ServicioCripta if regla == "saltos" else ServicioPrecargaPorCosto
    servicio = clase(ClientePersistente(http, AlmacenDisco(carpeta)), CacheLRU(25))
    logica = EstadoJuegoLogica(comunicacion=servicio)
    disparadas = [0]

    def ingresar_contando(sala):
        # Una carga que no es la sala del jugador y que todavía no estaba hecha la provocó un enemigo al moverse.
        estado = getattr(logica, "estadoJuego", None)
        por_enemigo = (estado is not None and sala != estado.jugador.id_sala_actual
                       and 0 < sala < len(estado.salas) and estado.salas[sala] is None)
        antes = servicio.solicitudes_realizadas
        try:
            return EstadoJuegoLogica.ingresarEnSala(logica, sala)
        finally:
            if por_enemigo:
                disparadas[0] += servicio.solicitudes_realizadas - antes

    controlador = ControladorJuego(None)
    movimientos = 0
    logica.ingresarEnSala = ingresar_contando          # en la instancia: GestorEventos la toma en iniciarJuego
    try:
        with contextlib.redirect_stdout(salida_muda()):
            logica.iniciarJuego(CRIPTA, 1)
            logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
            for palabra in guion:
                jugador = logica.estadoJuego.jugador
                antes = jugador.id_sala_actual
                sala = logica.estadoJuego.salas[antes]
                evento = controlador._mapear_entrada_a_evento(palabra, sala, jugador)
                if evento and evento != "IGNORAR":
                    logica.accionJugador(evento)
                if logica.estadoJuego.jugador.id_sala_actual != antes:
                    movimientos += 1
    finally:
        del logica.ingresarEnSala                        # vuelve a usarse el método de la clase
    return servicio.solicitudes_realizadas, disparadas[0], logica.estadoJuego.jugador.id_sala_actual, movimientos


def _verificar_precarga_por_costo(filas: list) -> bool:
    """En una cripta pequeña: el lote nunca supera 10 más las indispensables, siempre las incluye, no trae salas fuera
    de la cripta y devuelve 0 cuando la sala y sus vecinas ya están."""
    salas = esqueleto_rejilla(5, 5, 3, costo_max=9)
    servicio = ServicioPrecargaPorCosto(HttpConfigurable(salas, llaves=[]), CacheLRU(25))
    bien = True
    with contextlib.redirect_stdout(salida_muda()):
        for sala_actual in (1, 13, 25, 7):
            inmediatas = [sala_actual] + servicio.salas_vecinas(CRIPTA, sala_actual, 1)
            indispensables = [n for n in inmediatas if not servicio._estan_listas(CRIPTA, [n])]
            traidas = servicio.precargar_vecinas(CRIPTA, sala_actual, 3)
            lote = servicio.ultimo_lote
            if indispensables:
                bien = bien and len(lote) <= max(10, len(indispensables)) and traidas == len(lote)
                bien = bien and all(n in lote for n in indispensables)
                bien = bien and all(1 <= n <= len(salas) for n in lote)
            bien = bien and servicio.precargar_vecinas(CRIPTA, sala_actual, 3) == 0
    return verificar(filas, SECCION_A, "precarga por costo: lote ≤ 10 + indispensables, las incluye, dentro de la "
                     "cripta y 0 si ya están", bien)


def _filas_a(filas: list, raiz: str, lado: int, cazadores: int, costo_max: int, etiqueta: str = "") -> tuple:
    """Promedio de SEMILLAS_A semillas por regla. Devuelve (verificación ok, totales por regla, disparadas por regla)."""
    suma_total = [0, 0]
    suma_disparadas = [0, 0]
    iguales = True
    for semilla in range(SEMILLAS_A):
        salas, enemigos, guion = _cripta_a(lado, cazadores, semilla, costo_max)
        resultados = []
        for i, regla in enumerate(("saltos", "costo")):
            carpeta = os.path.join(raiz, f"a_{costo_max}_{lado}_{cazadores}_{semilla}_{regla}")
            resultados.append(_jugar_a(salas, enemigos, guion, regla, carpeta))
            suma_total[i] += resultados[-1][0]
            suma_disparadas[i] += resultados[-1][1]
        iguales = iguales and resultados[0][2:] == resultados[1][2:]
    ok = verificar(filas, SECCION_A, f"{etiqueta}lado {lado}, {cazadores} cazadores: las dos reglas terminan en la misma "
                   "sala con los mismos movimientos", iguales)
    for i, regla in enumerate(("saltos [elegida]", "costo [descartada]")):
        filas.append((SECCION_A, f"{etiqueta}lado {lado:>2}  {cazadores:>2} cazadores  {regla}",
                      f"{suma_total[i] / SEMILLAS_A:.1f} / {suma_disparadas[i] / SEMILLAS_A:.1f}",
                      "solicitudes totales / disparadas por un enemigo (promedio de 5 semillas)"))
    return ok, suma_total, suma_disparadas


def _seccion_a(filas: list, raiz: str) -> bool:
    cumple = _verificar_precarga_por_costo(filas)
    nota(filas, SECCION_A, f"rejilla con costo_max=9, cazadores de rango 600 a {DISTANCIA_MINIMA_A}+ salidas del "
                           f"jugador, guion de {MOVIMIENTOS_A} movimientos por salidas abiertas; solo informa")
    distinguen = 0
    con_disparadas = 0
    filas_hechas = 0
    for lado in LADOS_A:
        for cazadores in CAZADORES_A:
            ok, totales, disparadas = _filas_a(filas, raiz, lado, cazadores, 9)
            cumple = cumple and ok
            filas_hechas += 1
            if totales[0] != totales[1] or disparadas[0] != disparadas[1]:
                distinguen += 1
            if disparadas[0] + disparadas[1] > 0:
                con_disparadas += 1
    if con_disparadas <= filas_hechas // 3 or distinguen <= filas_hechas // 3:
        nota(filas, SECCION_A, f"comparación poco concluyente: solo {con_disparadas} de {filas_hechas} filas tienen "
                               f"solicitudes disparadas por un enemigo y {distinguen} distinguen las reglas (los "
                               "cazadores se activan solo cuando el jugador entra en su sala, y con costo_max=9 y rango "
                               "600 un cazador activo ve casi toda la rejilla)")
        ok, _, _ = _filas_a(filas, raiz, 20, 4, 300, "variante costo_max=300 (como bench/terreno.py): ")
        cumple = cumple and ok
    return cumple


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
    with tempfile.TemporaryDirectory() as raiz:
        cumple_a = _seccion_a(filas, raiz)
        cumple_b = _seccion_b(filas, raiz)
        cumple_c = _seccion_c(filas)
        cumple_d = _seccion_d(filas, raiz)
    return cumple_a and cumple_b and cumple_c and cumple_d
