"""«Ir a» (capacidad 006, FR-250, FR-251): lo que cuesta un paso del viaje, con la ALTERNATIVA DESCARTADA de cada decisión
(principio VII). Contrato: specs/006-ir-a/contracts/bench-ir-a.md; decisiones: specs/006-ir-a/research.md.

  A. Ruta               elegida: campo de costos + siguiente paso   | descartada: enumerar todas las rutas y comparar lista a lista
  B. Paso               elegida: movimiento normal (accionJugador)  | descartada: camino propio que solo mueve (cota inferior)
  C. Recálculo          elegida: si cambia la versión, con cota     | descartadas: cada paso; la versión sin cota
  D. Detención          elegida: mirar los enemigos de la sala      | descartada: mirar el contenido de las salas de la ruta
  E. Pergamino          elegida: un nodo del historial por paso     | descartada: todo el viaje como una sola acción
  F. Registro           elegida: dos marcas + pasos normales        | descartada: repetir el log sin marcas (diferencia)
  G. Paso, peor caso    FR-250: mediana y máximo por paso <= 5 ms
  H. Equivalencia       reutilizar el campo decide igual que recalcularlo desde cero (principio III)
  I. Mapa completo      FR-250/FR-251: el paso con TODAS las salas exploradas (enunciado §6.1), mediana y máximo <= 5 ms

El límite de 5 ms (G) es duro por tiempo porque lo exige la especificación, en las criptas de 400 y 2 000 salas con el 10 %
explorado; con el mapa conocido COMPLETO (I, el criterio del enunciado §6.1) es duro en 400 salas (la mayor cripta publicada
tiene 300) y se informa en 2 000 y 20 000, donde el recálculo tras una puerta cerrada supera 5 ms. Los demás
criterios son por CONTEO (lección de la 005). En 20 000 salas (2 000 exploradas) el paso sin captura cumple, pero dos casos
superan 5 ms y se informan sin ocultarlos: el paso en que se captura un punto de control (capacidad 007, cada K acciones;
copia el estado completo y crece con el tamaño de la cripta) y el recálculo desde cero tras una puerta cerrada, que no admite
cota. Ver la sección G y specs/006-ir-a/research.md D3.
Los pasos se miden con el recolector de basura apagado (como `timeit`): en 20 000 salas una pausa del recolector, de unos
10 ms, cae en un paso cualquiera de cualquier acción y no es costo del viaje; el bloque `ciclo` mide el ciclo completo.
Criptas sintéticas deterministas por semilla; sin red ni vista. Sin dict/set/sorted().
"""
from __future__ import annotations

import contextlib
import gc
import time

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from bench.datos import SEMILLA, salida_muda
from bench.medicion import anotar, medir, nota, texto, verificar
from DTO.ResultadoViajeDTO import EN_CURSO
from Logica.BuscadorRutas import BuscadorRutas, VistaMapaReal
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.MapaCripta import MapaCripta
from Logica.MapaConocido import VistaMapaConocido
from Logica.ordenamiento import insertion_sort
from Logica.RetrocesoLogica import RetrocesoLogica
from Logica.ViajeLogica import LIMITE_SIN_COTA, ViajeLogica
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_lineal, esqueleto_rejilla, mapa_dto_desde_esqueleto
from tests_labs.escenarios_ir_a import dar_pergamino, usar_pergamino
from tests_labs.partida_prueba import esperar, nueva_partida
from tests_labs.referencia_viaje import resumen_estado, ruta_minima_lexicografica

SECCION_A = "Ir a (A): ruta, campo de costos frente a enumerar rutas (FR-234)"
SECCION_B = "Ir a (B): un paso por el flujo normal frente a un camino propio"
SECCION_C = "Ir a (C): recálculo, cada paso / solo si cambia la versión, sin y con cota"
SECCION_D = "Ir a (D): condiciones de detención, enemigos de la sala frente a revisar la ruta"
SECCION_E = "Ir a (E): pergamino, un nodo por paso frente a una acción por viaje"
SECCION_F = "Ir a (F): registro del viaje, marcas y repetición"
SECCION_G = "Ir a (G): un paso en el peor caso (FR-250, límite 5 ms)"
SECCION_H = "Ir a (H): equivalencia con recalcular desde cero (principio III)"
SECCION_I = "Ir a (I): un paso con el mapa conocido completo (FR-250, enunciado §6.1, límite 5 ms)"

TAMANOS = ((20, 20), (20, 100), (100, 200))          # 400, 2 000 y 20 000 salas: el mayor, 50 veces el menor
LIMITE_MS = 5.0
REPETICIONES = (5, 5, 3)                             # viajes completos por tamaño (cada uno con una partida nueva)


# ---------------------------------------------------------------- partidas y viajes

def _partida(ancho: int, alto: int, semilla: int = 0, antorcha: bool = False, explorado: int | None = None):
    """Partida real sobre una rejilla con el 10 % de las salas (las primeras por id) ya exploradas y algunas puertas
    cerradas. Devuelve (modelo, destino): la última sala explorada, lejos del jugador."""
    total = ancho * alto
    k = explorado if explorado is not None else total // 10
    for intento in range(1, 40):
        esqueleto = esqueleto_rejilla(ancho, alto, semilla=SEMILLA + semilla + intento, costo_max=300, fraccion_cerradas=0.05)
        logica = nueva_partida(esqueleto)
        for sala in range(1, k + 1):
            logica.mapaConocido._entrada(sala, False)           # conocimiento previo, sin pasar por el jugador
        esperar(logica, 1)                                       # la primera acción toma el punto de control inicial (una vez)
        logica.estadoJuego.jugador.antorcha_encendida = antorcha
        if logica.iniciarViaje(k).estado == EN_CURSO:
            logica.cancelarViaje()
            logica.viaje_activo = None
            return logica, k
    raise RuntimeError("no se halló una cripta de prueba con ruta")


def _recorrer(logica, viaje) -> tuple:
    """Da todos los pasos de `viaje` midiendo cada uno. Devuelve (milisegundos por paso, ¿capturó un punto de control?)."""
    logica.viaje_activo = viaje
    tiempos = []
    capturas = []
    recolector = gc.isenabled()
    gc.disable()           # como timeit: una pausa del recolector no es costo del paso (la mide el bloque `ciclo`)
    try:
        while viaje.estado == EN_CURSO:
            puntos = len(logica.puntos_control)
            inicio = time.perf_counter()
            viaje.avanzar()
            tiempos.append((time.perf_counter() - inicio) * 1000.0)
            capturas.append(len(logica.puntos_control) != puntos)
    finally:
        if recolector:
            gc.enable()
    logica.viaje_activo = None
    return tiempos, capturas


def _viaje(logica, destino, clase=ViajeLogica):
    viaje = clase(logica)
    viaje.iniciar(destino)
    return viaje


def _mediana(valores: list) -> float:
    copia = list(valores)
    insertion_sort(copia)
    return copia[len(copia) // 2]


def _maximo(valores: list) -> float:
    mayor = valores[0]
    for v in valores:
        if v > mayor:
            mayor = v
    return mayor


class _ViajeCadaPaso(ViajeLogica):
    """Alternativa descartada de C: recalcula el campo antes de cada paso aunque el conocimiento no haya cambiado."""

    def _hay_ruta(self, sala: int) -> bool:
        self._calcular()
        return self.buscador.costo(sala) is not None


class _ViajeSoloVersion(ViajeLogica):
    """Política B de la decisión 3 (descartada tras medir): recalcula solo si cambió la versión, pero SIEMPRE sin cota."""

    def _calcular(self) -> None:
        self.buscador.distancias_hacia(self.destino, self.vista, LIMITE_SIN_COTA)
        self.version_vista = self.vista.version_conocimiento


# ---------------------------------------------------------------- A. ruta

def _enumerar(esqueleto: list, origen: int, destino: int) -> tuple:
    """Alternativa descartada de A: enumera todas las rutas simples de costo mínimo hasta ahora y se queda con la menor
    lista de ids. Devuelve (ruta, rutas completas halladas)."""
    mejor = [None, None, 0]

    def visitar(sala, ruta, costo):
        if mejor[0] is not None and costo > mejor[0]:
            return
        if sala == destino:
            mejor[2] += 1
            if mejor[0] is None or costo < mejor[0] or (costo == mejor[0] and ruta < mejor[1]):
                mejor[0], mejor[1] = costo, list(ruta)
            return
        for entrada in esqueleto:
            if entrada["id"] != sala:
                continue
            for letra in ("N", "S", "E", "O"):
                if letra in entrada["salidas"] and not entrada["salidas"][letra].get("cerrada"):
                    siguiente = entrada["salidas"][letra]["sala"]
                    if siguiente not in ruta:
                        ruta.append(siguiente)
                        visitar(siguiente, ruta, costo + entrada["salidas"][letra].get("costo", 100))
                        ruta.pop()

    visitar(origen, [origen], 0)
    return mejor[1], mejor[2]


def _ruta_con_campo(esqueleto: list, origen: int, destino: int) -> list:
    mapa = MapaCripta(mapa_dto_desde_esqueleto(esqueleto))
    vista = VistaMapaReal(mapa, [None] * mapa.tamano)
    buscador = BuscadorRutas()
    buscador.distancias_hacia(destino, vista, LIMITE_SIN_COTA)
    ruta = [origen]
    while ruta[-1] != destino:
        arista = buscador.siguiente_paso(ruta[-1])
        ruta.append(arista.destino)
    return ruta


def seccion_a(filas: list) -> bool:
    cumple = True
    for lado in (3, 4, 5):
        esqueletos = [esqueleto_rejilla(lado, lado, semilla=semilla, costo_max=2) for semilla in range(1, 7)]
        destino = lado * lado
        iguales = True
        rutas_enumeradas = 0
        for esqueleto in esqueletos:
            esperada, completas = _enumerar(esqueleto, 1, destino)
            rutas_enumeradas += completas
            iguales = iguales and _ruta_con_campo(esqueleto, 1, destino) == esperada == ruta_minima_lexicografica(esqueleto, 1, destino)
        cumple = verificar(filas, SECCION_A, f"rejilla {lado}x{lado}: el campo y la enumeración dan la misma ruta (6 criptas)", iguales) and cumple
        anotar(filas, SECCION_A, f"elegida: campo + siguiente paso, {lado}x{lado}, 6 criptas",
               medir(lambda: [_ruta_con_campo(e, 1, destino) for e in esqueletos]))
        anotar(filas, SECCION_A, f"descartada: enumerar rutas, {lado}x{lado}, 6 criptas",
               medir(lambda: [_enumerar(e, 1, destino) for e in esqueletos]))
        nota(filas, SECCION_A, f"{lado}x{lado}: la alternativa llegó al destino {rutas_enumeradas} veces en 6 criptas")
    nota(filas, SECCION_A, "El desempate de Dijkstra por predecesor (criterio del cazador) elige la ÚLTIMA sala y no cumple FR-234")
    return cumple


# ---------------------------------------------------------------- B. paso por el flujo normal

def seccion_b(filas: list) -> bool:
    ancho, alto = TAMANOS[1]
    a, destino = _partida(ancho, alto)
    b, _ = _partida(ancho, alto)
    viaje = _viaje(a, destino)
    tiempos, _ = _recorrer(a, viaje)
    from tests_labs.referencia_viaje import caminar_a_mano
    caminar_a_mano(b, [1] + viaje.recorrido)
    cumple = verificar(filas, SECCION_B, "viajar y caminar a mano dejan el mismo estado (sala, reloj, vida, conocimiento, salas cargadas)",
                       resumen_estado(a)[:7] == resumen_estado(b)[:7])
    nota(filas, SECCION_B, f"viaje de {viaje.pasos} pasos en {ancho * alto} salas")
    nota(filas, SECCION_B, f"elegida: mediana por paso {texto(_mediana(tiempos) * 1000)} (máximo {texto(_maximo(tiempos) * 1000)})")

    c, destino_c = _partida(ancho, alto)
    jugador = c.estadoJuego.jugador
    conocimiento = c.mapaConocido
    ruta = viaje.recorrido
    inicio = time.perf_counter()
    for sala in ruta:                                            # lo mínimo que duplicaría un camino propio: mover + conocer
        jugador.id_sala_actual = sala
        conocimiento.entrar(sala, False)
    propio = (time.perf_counter() - inicio) * 1000.0 / len(ruta)
    nota(filas, SECCION_B, f"descartada: camino propio, {texto(propio * 1000)} por paso (cota inferior: sin reloj, agenda, trampas ni efectos)")
    return cumple


# ---------------------------------------------------------------- C. recálculo

def seccion_c(filas: list) -> bool:
    ancho, alto = TAMANOS[1]
    cumple = True
    for antorcha in (False, True):
        etiqueta = "con antorcha" if antorcha else "sin antorcha"
        resultados = []
        for nombre, clase in (("cada paso", _ViajeCadaPaso), ("solo si cambia la versión, sin cota", _ViajeSoloVersion),
                              ("solo si cambia la versión, con cota (elegida)", ViajeLogica)):
            logica, destino = _partida(ancho, alto, antorcha=antorcha)
            viaje = _viaje(logica, destino, clase)
            fijadas = viaje.buscador.salas_fijadas
            inicio = time.perf_counter()
            tiempos, _ = _recorrer(logica, viaje)
            total = (time.perf_counter() - inicio) * 1000.0
            resultados.append((nombre, list(viaje.recorrido), viaje.buscador.salas_fijadas - fijadas, total))
            nota(filas, SECCION_C, f"{etiqueta}, {nombre}: {viaje.pasos} pasos, salas fijadas {viaje.buscador.salas_fijadas - fijadas}, "
                                   f"{texto(total * 1000)} el viaje")
        cumple = verificar(filas, SECCION_C, f"{etiqueta}: las tres políticas recorren las mismas salas",
                           resultados[0][1] == resultados[1][1] == resultados[2][1]) and cumple
        if not antorcha:
            cumple = verificar(filas, SECCION_C, "sin cambios de conocimiento la política elegida no recalcula (0 salas fijadas)",
                               resultados[2][2] == 0) and cumple
        cumple = verificar(filas, SECCION_C, f"{etiqueta}: la cota no fija más salas que la política sin cota",
                           resultados[2][2] <= resultados[1][2]) and cumple
    return cumple


# ---------------------------------------------------------------- D. detención

class _Enemigo:
    activo = False
    vida_actual = 1


class _EnemigosContados(list):
    examinados = 0

    def __iter__(self):
        for elemento in list.__iter__(self):
            _EnemigosContados.examinados += 1
            yield elemento


class _SalaFalsa:
    def __init__(self, identificador: int, enemigos: int) -> None:
        self.id = identificador
        self.enemigos = _EnemigosContados([_Enemigo() for _ in range(enemigos)])


def seccion_d(filas: list) -> bool:
    cumple = True
    for enemigos in (0, 10, 100):
        cuentas = []
        for ancho, alto in TAMANOS:
            logica, destino = _partida(ancho, alto)
            viaje = _viaje(logica, destino)
            sala = _SalaFalsa(destino + 1, enemigos)
            _EnemigosContados.examinados = 0
            viaje._parada(sala, logica.estadoJuego.jugador.vida_actual, logica.activaciones_enemigos)
            cuentas.append(_EnemigosContados.examinados)
        cumple = verificar(filas, SECCION_D, f"{enemigos} enemigos: se examinan {enemigos} en los tres tamaños de cripta",
                           cuentas == [enemigos] * 3) and cumple
        pasos = 120
        nota(filas, SECCION_D, f"descartada (revisar el contenido de las salas de una ruta de {pasos} pasos): {pasos * enemigos} "
                               f"enemigos examinados y descargas posibles (viola FR-248)")
    return cumple


# ---------------------------------------------------------------- E. pergamino

def seccion_e(filas: list) -> bool:
    cumple = True
    ancho, alto = TAMANOS[0]
    for antorcha in (False, True):
        etiqueta = "con antorcha" if antorcha else "sin antorcha"

        def preparar(antorcha=antorcha):
            logica, destino = _partida(ancho, alto, antorcha=antorcha)
            objeto = dar_pergamino(logica)
            logica.iniciarViaje(destino)
            logica.avanzarViaje()
            logica.avanzarViaje()
            antes = resumen_estado(logica)
            logica.avanzarViaje()                                # el último paso
            return logica, objeto, antes

        logica, objeto, antes = preparar()
        acciones = logica.jugadorLogica.retroceso.cantidad_acciones
        usar_pergamino(logica, objeto)
        despues = resumen_estado(logica)
        igual = despues[:1] + despues[2:6] == antes[:1] + antes[2:6]      # sala, vida, conocimiento (las salas cargadas no se revierten)
        cumple = verificar(filas, SECCION_E, f"{etiqueta}: revertir el último paso deja la partida como antes de darlo", igual) and cumple
        cumple = verificar(filas, SECCION_E, f"{etiqueta}: el historial pierde exactamente una acción",
                           logica.jugadorLogica.retroceso.cantidad_acciones == acciones - 1) and cumple

        def revertir(estado):
            usar_pergamino(estado[0], estado[1])
        anotar(filas, SECCION_E, f"elegida: revertir un paso, {etiqueta}", medir(revertir, preparar=preparar))
    nota(filas, SECCION_E, "descartada (todo el viaje como una sola acción): contradice «revierte solo el último paso» y el máximo de 5 acciones")
    return cumple


# ---------------------------------------------------------------- F. registro

def _corredor(pasos: int):
    esqueleto = esqueleto_lineal([None] * pasos)
    RetrocesoLogica().reiniciar()
    logica = EstadoJuegoLogica()
    logica.comunicacion = ServicioCripta(HttpConfigurable(esqueleto, sala_salida=len(esqueleto) + 1000), CacheLRU(25))
    logica.iniciarJuego("cripta-01", 1)
    logica.ingresarEnSala(1)
    return logica, esqueleto


def _caminar_ida(logica, pasos: int) -> None:
    from tests_labs.escenarios_ir_a import mover
    for _ in range(pasos):
        mover(logica, "este")


def _linea_es_marca(linea: str) -> bool:
    return '"IR_A"' in linea or '"FIN_IR_A"' in linea


def seccion_f(filas: list) -> bool:
    cumple = True
    for pasos in (10, 100, 1000):
        logica, esqueleto = _corredor(pasos)
        _caminar_ida(logica, pasos)                              # explora todo el corredor
        antes = logica.logEventos.cantidad
        resultado = logica.iniciarViaje(1)
        logica.ejecutarViaje()
        lineas = logica.exportar_log().acciones
        escritas = logica.logEventos.cantidad - antes
        sin_marcas = []
        for linea in lineas:
            if not _linea_es_marca(linea):
                sin_marcas.append(linea)
        cumple = verificar(filas, SECCION_F, f"viaje de {pasos} pasos: el registro crece en {pasos} movimientos + 2 marcas",
                           resultado.estado == EN_CURSO and escritas == pasos + 2 and len(lineas) - len(sin_marcas) == 2) and cumple

        def repetir(dto, esqueleto=esqueleto):
            RetrocesoLogica().reiniciar()
            otra = EstadoJuegoLogica()
            otra.comunicacion = ServicioCripta(HttpConfigurable(esqueleto, sala_salida=len(esqueleto) + 1000), CacheLRU(25))
            otra.repetirPartida(dto)
            return otra

        dto_con = logica.exportar_log()
        dto_sin = type(dto_con)(dto_con.id_cripta, dto_con.semilla, dto_con.version_cripta, dto_con.version_catalogo, sin_marcas)
        con = repetir(dto_con)
        sin = repetir(dto_sin)
        cumple = verificar(filas, SECCION_F, f"viaje de {pasos} pasos: repetir con y sin marcas deja la misma partida",
                           resumen_estado(con)[:3] == resumen_estado(sin)[:3] == resumen_estado(logica)[:3]) and cumple
        if pasos <= 100:
            anotar(filas, SECCION_F, f"repetir el log con marcas, {pasos} pasos de ida y {pasos} de vuelta",
                   medir(lambda: repetir(dto_con), repeticiones=3))
            anotar(filas, SECCION_F, f"descartada: repetir el log sin marcas, {pasos} pasos de ida y {pasos} de vuelta",
                   medir(lambda: repetir(dto_sin), repeticiones=3))
    return cumple


# ---------------------------------------------------------------- G. un paso, peor caso

def seccion_g(filas: list) -> bool:
    cumple = True
    for (ancho, alto), repeticiones in zip(TAMANOS, REPETICIONES):
        total = ancho * alto
        por_paso = []                                            # por paso (sin captura): lista de tiempos de las repeticiones
        capturas_ms = []
        for repeticion in range(repeticiones):
            logica, destino = _partida(ancho, alto, semilla=repeticion, antorcha=True)    # la versión sube al entrar a salas nuevas
            viaje = _viaje(logica, destino)
            tiempos, capturas = _recorrer(logica, viaje)
            for indice in range(len(tiempos)):
                if capturas[indice]:
                    capturas_ms.append(tiempos[indice])
                else:
                    while len(por_paso) <= indice:
                        por_paso.append([])
                    por_paso[indice].append(tiempos[indice])
        medianas = [_mediana(v) for v in por_paso if v]
        todos = [x for v in por_paso for x in v]
        mediana, maximo_por_paso, maximo = _mediana(todos), _maximo(medianas), _maximo(todos)
        nota(filas, SECCION_G, f"{total} salas, paso sin captura (antorcha): mediana {texto(mediana * 1000)}; "
                               f"máximo de las medianas por paso {texto(maximo_por_paso * 1000)}; máximo absoluto {texto(maximo * 1000)}")
        cumple = verificar(filas, SECCION_G, f"{total} salas: el paso (sin captura) cumple <= {LIMITE_MS:g} ms", maximo_por_paso <= LIMITE_MS) and cumple
        if capturas_ms:
            capturados = _mediana(capturas_ms)
            ok = capturados <= LIMITE_MS
            nota(filas, SECCION_G, f"{total} salas, paso que captura un punto de control (007, cada K acciones): mediana "
                                   f"{texto(capturados * 1000)} {'<=' if ok else '>'} {LIMITE_MS:g} ms")
            if total <= TAMANOS[1][0] * TAMANOS[1][1]:
                cumple = verificar(filas, SECCION_G, f"{total} salas: el paso con captura cumple <= {LIMITE_MS:g} ms", ok) and cumple

        # una puerta recordada abierta resulta cerrada: el recálculo sin límite cae en un solo paso
        logica, destino = _partida(ancho, alto)
        viaje = _viaje(logica, destino)
        ruta = _ruta_del_viaje(logica, destino)
        if len(ruta) > 3:
            _cerrar_lejos(logica, ruta[2], ruta[3])
        tiempos, capturas = _recorrer(logica, viaje)
        sin_captura = [tiempos[i] for i in range(len(tiempos)) if not capturas[i]]
        nota(filas, SECCION_G, f"{total} salas, puerta cerrada en la ruta (recálculo sin límite): máximo de un paso "
                               f"{texto(_maximo(sin_captura) * 1000)}")
        recalculo_ok = _maximo(sin_captura) <= LIMITE_MS
        if total <= TAMANOS[1][0] * TAMANOS[1][1]:
            cumple = verificar(filas, SECCION_G, f"{total} salas: el paso que recalcula tras una puerta cerrada cumple <= {LIMITE_MS:g} ms",
                               recalculo_ok) and cumple
        elif not recalculo_ok:
            nota(filas, SECCION_G, f"{total} salas: SUPERA {LIMITE_MS:g} ms (informativo): recalcular desde cero el campo de {total // 10} "
                                   f"salas exploradas tras una puerta cerrada no admite cota; haría falta un recálculo incremental")
    return cumple


def _ruta_del_viaje(logica, destino) -> list:
    """Salas de la ruta que seguiría hoy el viaje (sin dar pasos), preguntando el siguiente paso al campo."""
    buscador = BuscadorRutas()
    vista = VistaMapaConocido(logica.mapaConocido)
    buscador.distancias_hacia(destino, vista, LIMITE_SIN_COTA)
    sala = logica.estadoJuego.jugador.id_sala_actual
    ruta = [sala]
    while sala != destino:
        arista = buscador.siguiente_paso(sala)
        sala = arista.destino
        ruta.append(sala)
    return ruta


def _cerrar_lejos(logica, origen: int, destino: int) -> None:
    """Cierra la puerta origen → destino por el camino del cierre automático; el mapa la sigue recordando abierta."""
    sala = logica.ingresarEnSala(origen)
    gestor = logica.gestorEventos
    gestor.salas_logica.sala = sala
    for salida in sala.salidas:
        if salida.sala_destino == destino:
            gestor.salas_logica.cerrarPuerta(salida.direccion)
            return


# ---------------------------------------------------------------- H. equivalencia

def seccion_h(filas: list) -> bool:
    cumple = True
    ancho, alto = TAMANOS[1]
    casos = (("sin antorcha", False, False), ("con antorcha", True, False), ("con una puerta que resulta cerrada", False, True))
    for etiqueta, antorcha, cerrar in casos:
        resultados = []
        for clase in (_ViajeCadaPaso, _ViajeSoloVersion, ViajeLogica):
            logica, destino = _partida(ancho, alto, antorcha=antorcha)
            viaje = _viaje(logica, destino, clase)
            if cerrar:
                ruta = _ruta_del_viaje(logica, destino)
                _cerrar_lejos(logica, ruta[3], ruta[4])
            _recorrer(logica, viaje)
            resultados.append((viaje.estado, viaje.motivo, list(viaje.recorrido), resumen_estado(logica)[:7]))
        cumple = verificar(filas, SECCION_H, f"{etiqueta}: reutilizar el campo (con y sin límite) decide como recalcular cada paso",
                           resultados[0] == resultados[1] == resultados[2]) and cumple
    return cumple


# ---------------------------------------------------------------- I. mapa conocido completo

def seccion_i(filas: list) -> bool:
    """El criterio del enunciado §6.1 es sobre el mapa conocido COMPLETO: aquí todas las salas están exploradas. Duro en 400
    salas (más que la mayor cripta publicada, de 300); en 2 000 y 20 000 se informa sin ocultar lo que supera 5 ms."""
    cumple = True
    for (ancho, alto), repeticiones in zip(TAMANOS, (5, 3, 1)):
        total = ancho * alto
        for cerrada in (False, True):
            etiqueta = "con una puerta cerrada en la ruta (recálculo sin cota)" if cerrada else "sin puertas cerradas"
            por_paso = []
            for repeticion in range(repeticiones):
                logica, destino = _partida(ancho, alto, semilla=repeticion, antorcha=True, explorado=total)
                viaje = _viaje(logica, destino)
                if cerrada:
                    ruta = _ruta_del_viaje(logica, destino)
                    if len(ruta) > 3:
                        _cerrar_lejos(logica, ruta[2], ruta[3])
                tiempos, capturas = _recorrer(logica, viaje)
                for indice in range(len(tiempos)):
                    if not capturas[indice]:
                        while len(por_paso) <= indice:
                            por_paso.append([])
                        por_paso[indice].append(tiempos[indice])
            medianas = [_mediana(v) for v in por_paso if v]
            todos = [x for v in por_paso for x in v]
            mediana, maximo_por_paso, maximo = _mediana(todos), _maximo(medianas), _maximo(todos)
            nota(filas, SECCION_I, f"{total} salas exploradas (100 %), {etiqueta}: mediana {texto(mediana * 1000)}; "
                                   f"máximo de las medianas por paso {texto(maximo_por_paso * 1000)}; máximo absoluto {texto(maximo * 1000)}")
            ok = maximo_por_paso <= LIMITE_MS
            if total <= TAMANOS[0][0] * TAMANOS[0][1]:
                cumple = verificar(filas, SECCION_I, f"{total} salas, mapa completo, {etiqueta}: el paso cumple <= {LIMITE_MS:g} ms", ok) and cumple
            elif not ok:
                nota(filas, SECCION_I, f"{total} salas, mapa completo, {etiqueta}: SUPERA {LIMITE_MS:g} ms (informativo, fuera del criterio duro de "
                                       f"FR-251): recalcular el campo de las {total} salas conocidas cuesta más que el límite")
    return cumple


def ejecutar(filas: list) -> bool:
    with contextlib.redirect_stdout(salida_muda()):
        cumple = seccion_a(filas)
        cumple = seccion_b(filas) and cumple
        cumple = seccion_c(filas) and cumple
        cumple = seccion_d(filas) and cumple
        cumple = seccion_e(filas) and cumple
        cumple = seccion_f(filas) and cumple
        cumple = seccion_g(filas) and cumple
        cumple = seccion_h(filas) and cumple
        cumple = seccion_i(filas) and cumple
    return cumple
