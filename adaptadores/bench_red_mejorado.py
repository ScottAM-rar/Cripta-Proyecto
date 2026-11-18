"""Copia de bench_red.py con una medición más (la sección 6). bench_red.py queda intacto.

Mediciones de la capa de red, caché y persistencia (para --bench y el Documento
de Decisiones). Todo es sintético: no usa internet ni la API real.

    py -m adaptadores.bench_red_mejorado

Cada sección responde una pregunta concreta de una decisión de diseño:
  1. ¿Cuántas solicitudes cuesta recorrer una cripta según la estrategia de precarga?
  2. ¿Cuánto cuesta buscar en la caché? (y la alternativa descartada: tabla hash propia). Desde la 012 la caché
     es una lista propia con la más reciente al final, y sus filas se llaman «lista propia lineal» (antes «deque
     lineal»), en la misma posición y con el mismo escenario.
  3. ¿Cuánto cuesta recuperar de disco una ficha liberada de memoria?
  4. ¿Cuánto cuesta guardar un lote de fichas?
  5. ¿Cuánto cuesta planear la vecindad en una cripta grande?
  6. (nueva) ¿Qué tasa de aciertos tiene la caché en una partida completa, según su capacidad?

Capacidad 012 (§5.6): las mediciones se repiten con la carga de la Parte II en las mismas filas.
  - Costos de salida (1 a 9, simétricos, de la semilla del bench) en las secciones 1, 5 y 6.
  - La consulta de llaves (+1 solicitud) y cazadores que se mueven hacia el jugador en las secciones 1 y 6.
  - En la sección 3, la ficha que se recupera es la de un cazador.
  - Al final, filas 31 a 34: la lista doblemente enlazada propia, alternativa descartada de la caché (D2).
La carga solo se activa aquí (`carga=True`); los demás bloques que usan ClienteSintetico no cambian.
Solo listas (principio I): sin dict ni set como índice, sin sorted, heapq, bisect, collections ni networkx.
"""
from __future__ import annotations

import os
import random
import tempfile
import time

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from bench.datos import SEMILLA
from tests_labs.cripta_sintetica import ficha_cazador

LATENCIA_API_MS = 400          # §3.4: lo que tarda cada solicitud real
ID_CAZADOR = "ent_cazador"     # tipo propio de los cazadores del contenido sintético (012)


class ClienteSintetico:
    """Imita a ClienteCripta con una cripta en forma de rejilla ancho x alto.

    Con `carga=True` (012), cada salida declara un "costo" entre 1 y 9 sacado de la semilla del bench, el mismo en
    las dos direcciones de cada conexión."""

    def __init__(self, ancho: int, alto: int, carga: bool = False) -> None:
        self.ancho = ancho
        self.alto = alto
        self.carga = carga
        self.llamadas = 0

    @property
    def solicitudes_realizadas(self) -> int:
        return self.llamadas

    def obtener_criptas(self):
        self.llamadas += 1
        return [{"id": "sintetica", "nombre": "Sintética", "salas": self.ancho * self.alto}]

    def obtener_datos_generales(self, cripta_id):
        self.llamadas += 1
        return {"id": cripta_id, "version": "v1", "salas_total": self.ancho * self.alto,
                "sala_inicial": 1, "sala_salida": self.ancho * self.alto,
                "llave_salida": "itm_llave", "presupuesto_solicitudes": 9, "inventario_max": 10,
                "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}

    def obtener_version_cripta(self, cripta_id):
        self.llamadas += 1
        return "v1"

    def _costos(self) -> tuple:
        """(costo_este, costo_sur): listas de posición = número de sala con el costo de la conexión hacia el este y
        hacia el sur de esa sala. La conexión inversa (O y N) lee el mismo valor, así el costo es simétrico."""
        total = self.ancho * self.alto
        costo_este, costo_sur = [0] * (total + 1), [0] * (total + 1)
        rng = random.Random(SEMILLA)
        for numero in range(1, total + 1):
            costo_este[numero] = rng.randint(1, 9)
            costo_sur[numero] = rng.randint(1, 9)
        return costo_este, costo_sur

    def obtener_salas(self, cripta_id):
        self.llamadas += 1
        costo_este, costo_sur = self._costos() if self.carga else (None, None)

        def salida(destino, costo):
            return {"sala": destino} if costo is None else {"sala": destino, "costo": costo}

        salas = []
        for fila in range(self.alto):
            for columna in range(self.ancho):
                numero = fila * self.ancho + columna + 1
                salidas = {}
                if fila > 0:
                    salidas["N"] = salida(numero - self.ancho, costo_sur[numero - self.ancho] if self.carga else None)
                if fila < self.alto - 1:
                    salidas["S"] = salida(numero + self.ancho, costo_sur[numero] if self.carga else None)
                if columna < self.ancho - 1:
                    salidas["E"] = salida(numero + 1, costo_este[numero] if self.carga else None)
                if columna > 0:
                    salidas["O"] = salida(numero - 1, costo_este[numero - 1] if self.carga else None)
                salas.append({"id": numero, "nombre": f"Sala {numero}", "salidas": salidas})
        return salas

    def obtener_llaves(self, cripta_id, solo_guardadas=False, limite_solicitudes=None):
        """GET /criptas/<id>/llaves (capacidad 009): una solicitud; una llave en la sala de salida, con la forma de
        tests_labs/api_falsa.py."""
        self.llamadas += 1
        return [{"id": "itm_llave", "sala": self.ancho * self.alto}]

    def obtener_contenido(self, cripta_id, salas):
        self.llamadas += 1
        return [{"sala": n, "enemigos": [], "objetos": [], "trampas": []} for n in salas]

    def obtener_version_catalogo(self):
        self.llamadas += 1
        return "k1"

    def obtener_catalogo(self, ids):
        self.llamadas += 1
        return []


class _TablaHashPropia:
    """ALTERNATIVA DESCARTADA para la caché: tabla hash con encadenamiento hecha con
    listas. Solo se usa aquí, para medir qué se gana y qué se pierde."""

    def __init__(self, cubos: int) -> None:
        self._cubos: list[list] = []
        for _ in range(cubos):
            self._cubos.append([])

    def poner(self, clave: str, valor) -> None:
        self._cubos[hash(clave) % len(self._cubos)].append((clave, valor))

    def obtener(self, clave: str):
        for par in self._cubos[hash(clave) % len(self._cubos)]:
            if par[0] == clave:
                return par[1]
        return None


class _NodoLRU:
    """Nodo de la lista doblemente enlazada del prototipo descartado."""

    __slots__ = ("clave", "valor", "veces", "anterior", "siguiente")

    def __init__(self, clave: str, valor) -> None:
        self.clave = clave
        self.valor = valor
        self.veces = 0
        self.anterior = None
        self.siguiente = None


class _ListaEnlazadaLRU:
    """ALTERNATIVA DESCARTADA para la caché (012, research D2 (c)): lista doblemente enlazada propia con la más
    reciente en la cabeza. Sin un índice por clave la búsqueda sigue siendo lineal; lo único que gana es el reenlace
    O(1) al mover la entrada a la cabeza. Solo se usa aquí, para medirla."""

    def __init__(self) -> None:
        self.cabeza = None
        self.cola = None

    def _desenlazar(self, nodo: _NodoLRU) -> None:
        if nodo.anterior is None:
            self.cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente
        if nodo.siguiente is None:
            self.cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior
        nodo.anterior = nodo.siguiente = None

    def _a_la_cabeza(self, nodo: _NodoLRU) -> None:
        nodo.siguiente = self.cabeza
        if self.cabeza is not None:
            self.cabeza.anterior = nodo
        self.cabeza = nodo
        if self.cola is None:
            self.cola = nodo

    def insertar(self, clave: str, valor) -> None:
        self._a_la_cabeza(_NodoLRU(clave, valor))

    def obtener(self, clave: str):
        nodo = self.cabeza
        while nodo is not None and nodo.clave != clave:
            nodo = nodo.siguiente
        if nodo is None:
            return None
        if nodo is not self.cabeza:
            self._desenlazar(nodo)
            self._a_la_cabeza(nodo)
        return nodo.valor


def _servicio(carpeta: str, ancho: int, alto: int, carga: bool = False):
    cliente = ClienteSintetico(ancho, alto, carga)
    servicio = ServicioCripta(ClientePersistente(cliente, AlmacenDisco(carpeta)), CacheLRU(25))
    servicio.listar_criptas()
    return cliente, servicio, servicio.obtener_id_cripta(1)


def _salas_con_cazador(total: int) -> list:
    """Una sala con cazador cada 10 salas, en una posición sacada de la semilla del bench (ascendentes)."""
    rng = random.Random(SEMILLA)
    salas = []
    for bloque in range(total // 10):
        salas.append(bloque * 10 + rng.randrange(10) + 1)
    return salas


def _mover_cazadores(servicio, cid: str, cazadores: list, sala_jugador: int) -> int:
    """Cada cazador avanza una salida hacia la sala del jugador, por la menor cantidad de salidas (012, research D3).

    Recorrido por niveles desde la sala del jugador sobre listas: cola por índice y distancias en una lista de
    posición = número de sala (almacenamiento contiguo, no un índice por clave). Las criptas sintéticas son
    simétricas, así que la distancia desde el jugador es la distancia hasta él. Desempate: la primera salida en el
    orden N, S, E, O que acerca. Si el cazador entra en una sala cuyo contenido no está traído, se construye la sala
    (la misma carga que provoca un enemigo al entrar). Mueve `cazadores` en su lugar y devuelve las solicitudes
    disparadas. El esqueleto ya está descargado: armar el mapa no hace solicitudes."""
    if not cazadores:
        return 0
    mapa = servicio.esqueleto(cid).salas
    distancia = [-1] * len(mapa)
    distancia[sala_jugador] = 0
    cola = [sala_jugador]
    lectura = 0
    while lectura < len(cola):
        actual = cola[lectura]
        lectura += 1
        for arista in mapa[actual].salidas:                 # ya vienen en el orden N, S, E, O
            if distancia[arista.destino] < 0:
                distancia[arista.destino] = distancia[actual] + 1
                cola.append(arista.destino)
    disparadas = 0
    for i in range(len(cazadores)):
        sala = cazadores[i]
        if sala == sala_jugador or distancia[sala] < 0:
            continue
        for arista in mapa[sala].salidas:
            if distancia[arista.destino] == distancia[sala] - 1:
                cazadores[i] = arista.destino
                if servicio.cliente.contenido_en_disco(cid, arista.destino) is None:
                    antes = servicio.solicitudes_realizadas
                    servicio.construir_sala(cid, arista.destino)
                    disparadas += servicio.solicitudes_realizadas - antes
                break
    return disparadas


def _cronometrar(funcion, repeticiones: int) -> float:
    """Microsegundos por operación."""
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        funcion()
    return (time.perf_counter() - inicio) / repeticiones * 1_000_000


# ----------------------------------------------------------------------
def solicitudes_por_estrategia(filas: list, raiz: str, total: int = 60) -> None:
    """Recorre un pasillo de `total` salas, de la primera a la última."""
    estrategias = [
        ("sala por sala (sin precarga)", lambda s, c, n: None),
        ("actual + vecinas en cada paso (prof. 2)",
         lambda s, c, n: s.precargar(c, [n] + s.salas_vecinas(c, n, 2))),
        ("perezosa, prof. 2", lambda s, c, n: s.precargar_vecinas(c, n, 2)),
        ("perezosa, por defecto (lote de 10)", lambda s, c, n: s.precargar_vecinas(c, n)),
    ]
    indice = 0
    for nombre, paso in estrategias:
        indice += 1
        cliente, servicio, cid = _servicio(os.path.join(raiz, f"est{indice}"), total, 1, carga=True)
        servicio.crear_jugador(cid)
        servicio.ubicacion_llaves(cid)                # 012: la consulta de llaves, contada en el presupuesto
        cazadores = _salas_con_cazador(total)         # 012: activos desde el inicio (peor caso)
        disparadas = 0
        for sala in range(1, total + 1):
            paso(servicio, cid, sala)
            servicio.construir_sala(cid, sala)        # el jugador entra a la sala
            disparadas += _mover_cazadores(servicio, cid, cazadores, sala)
        espera = cliente.solicitudes_realizadas * LATENCIA_API_MS / 1000
        filas.append(("1. Solicitudes al recorrer un pasillo de %d salas" % total, nombre,
                      cliente.solicitudes_realizadas,
                      f"solicitudes (~{espera:.1f} s de espera); de ellas, {disparadas} disparadas por un cazador"))


def busqueda_en_cache(filas: list) -> None:
    for tamano in (25, 100, 1000, 5000):
        cache = CacheLRU(tamano)
        tabla = _TablaHashPropia(tamano * 2 + 1)
        claves = []
        for n in range(tamano):
            clave = f"ent_{n:05d}"
            cache.insertar(clave, {"id": clave})
            tabla.poner(clave, {"id": clave})
            claves.append(clave)
        repeticiones = 2000
        contador = [0]

        def acierto_lru():
            # siempre la menos reciente: el peor caso de la búsqueda lineal
            clave = claves[contador[0] % tamano]
            contador[0] += 1
            cache.obtener(clave)

        def fallo_lru():
            cache.obtener("no_existe")

        def acierto_hash():
            clave = claves[contador[0] % tamano]
            contador[0] += 1
            tabla.obtener(clave)

        filas.append(("2. Búsqueda en la caché (µs por operación)", f"lista propia lineal, {tamano} fichas, acierto",
                      round(_cronometrar(acierto_lru, repeticiones), 2), "µs"))
        filas.append(("2. Búsqueda en la caché (µs por operación)", f"lista propia lineal, {tamano} fichas, fallo",
                      round(_cronometrar(fallo_lru, repeticiones), 2), "µs"))
        filas.append(("2. Búsqueda en la caché (µs por operación)", f"tabla hash propia, {tamano} fichas, acierto (descartada)",
                      round(_cronometrar(acierto_hash, repeticiones), 2), "µs"))


def lista_enlazada_descartada(filas: list) -> None:
    """Filas 31 a 34 (012): la lista doblemente enlazada propia, alternativa descartada de la caché (research D2,
    principio VII). Mismo escenario que la fila «acierto» de la sección 2: siempre la menos reciente, el peor caso
    de la búsqueda lineal. Van al final del bloque para no mover el número de las filas que ya existían."""
    for tamano in (25, 100, 1000, 5000):
        lista = _ListaEnlazadaLRU()
        claves = []
        for n in range(tamano):
            clave = f"ent_{n:05d}"
            lista.insertar(clave, {"id": clave})
            claves.append(clave)
        contador = [0]

        def acierto_enlazada():
            clave = claves[contador[0] % tamano]
            contador[0] += 1
            lista.obtener(clave)

        filas.append(("2. Búsqueda en la caché (µs por operación)", f"lista enlazada propia, {tamano} fichas, acierto (descartada)",
                      round(_cronometrar(acierto_enlazada, 2000), 2), "µs"))


def ficha_liberada(filas: list, raiz: str) -> None:
    for cantidad in (25, 200, 1000):
        almacen = AlmacenDisco(os.path.join(raiz, f"cat{cantidad}"))
        almacen.validar_catalogo("k1")
        fichas = [{"id": f"ent_{n:05d}", "clase": "enemigo", "nombre": f"E{n}", "vida_max": 10,
                   "ataque": 3, "defensa": 1, "velocidad": 100, "comportamiento": "guardián", "suelta": []}
                  for n in range(cantidad)]
        fichas[cantidad // 2] = ficha_cazador(f"ent_{cantidad // 2:05d}", rango=600)   # 012: la que se lee es de cazador
        almacen.guardar_fichas(fichas)
        medio = fichas[cantidad // 2]["id"]
        filas.append(("3. Recuperar una ficha liberada desde disco", f"catálogo con {cantidad} fichas",
                      round(_cronometrar(lambda: almacen.leer_ficha(medio), 200) / 1000, 3),
                      f"ms por lectura (una solicitud real: ~{LATENCIA_API_MS} ms)"))


def guardado_en_lote(filas: list, raiz: str) -> None:
    for existentes in (25, 200, 1000):
        almacen = AlmacenDisco(os.path.join(raiz, f"lote{existentes}"))
        almacen.validar_catalogo("k1")
        base = [{"id": f"ent_{n:05d}", "clase": "enemigo", "nombre": f"E{n}"} for n in range(existentes)]
        almacen.guardar_fichas(base)
        nuevas = [{"id": f"nueva_{n:03d}", "clase": "enemigo", "nombre": f"N{n}"} for n in range(10)]
        filas.append(("4. Guardar 10 fichas nuevas (reescribe el archivo completo)", f"catálogo con {existentes} fichas",
                      round(_cronometrar(lambda: almacen.guardar_fichas(nuevas), 20) / 1000, 3), "ms"))


def planear_vecindad(filas: list, raiz: str) -> None:
    cliente, servicio, cid = _servicio(os.path.join(raiz, "grande"), 50, 20, carga=True)   # 1000 salas, con costos
    servicio.crear_jugador(cid)
    servicio.salas_vecinas(cid, 1, 1)                                               # calienta el esqueleto
    sala = 500
    filas.append(("5. Planear la vecindad en una cripta de 1000 salas", "salas_vecinas, 1 paso",
                  round(_cronometrar(lambda: servicio.salas_vecinas(cid, sala, 1), 500), 1), "µs"))
    filas.append(("5. Planear la vecindad en una cripta de 1000 salas", "salas_vecinas, 2 pasos",
                  round(_cronometrar(lambda: servicio.salas_vecinas(cid, sala, 2), 500), 1), "µs"))
    servicio.precargar_vecinas(cid, sala)
    filas.append(("5. Planear la vecindad en una cripta de 1000 salas", "precargar_vecinas cuando no hace falta nada",
                  round(_cronometrar(lambda: servicio.precargar_vecinas(cid, sala), 500), 1), "µs"))


class ClienteConCatalogo(ClienteSintetico):
    """Rejilla ancho x alto con contenido y catálogo reales: cada sala tiene 2 enemigos (de `tipos_enemigo`
    tipos, cada uno suelta un objeto) y 1 objeto en el suelo (de `tipos_objeto` tipos). Así la caché se
    llena con fichas distintas, como en una cripta de verdad.

    012: con costos de salida y un cazador más cada 10 salas (posiciones de la semilla del bench), con su propio
    tipo y una ficha con comportamiento cazador y rango 600."""

    def __init__(self, ancho: int, alto: int, tipos_enemigo: int = 40, tipos_objeto: int = 30) -> None:
        super().__init__(ancho, alto, carga=True)
        self.tipos_enemigo = tipos_enemigo
        self.tipos_objeto = tipos_objeto
        self.cazadores = _salas_con_cazador(ancho * alto)

    def _id_enemigo(self, n: int) -> str:
        return f"ent_{n % self.tipos_enemigo:03d}"

    def _id_objeto(self, n: int) -> str:
        return f"obj_{n % self.tipos_objeto:03d}"

    def obtener_contenido(self, cripta_id, salas):
        self.llamadas += 1
        contenidos = []
        for n in salas:
            enemigos = [{"instancia": f"e-{n}-{k}", "tipo": self._id_enemigo(n * 3 + k * 7)} for k in range(2)]
            if n in self.cazadores:                         # lista de a lo sumo total/10 salas: búsqueda lineal
                enemigos.append({"instancia": f"c-{n}", "tipo": ID_CAZADOR})
            contenidos.append({"sala": n, "enemigos": enemigos, "objetos": [self._id_objeto(n)], "trampas": []})
        return contenidos

    def obtener_catalogo(self, ids):
        self.llamadas += 1
        fichas = []
        for id_catalogo in ids:
            if id_catalogo == ID_CAZADOR:
                fichas.append(ficha_cazador(ID_CAZADOR, rango=600))
                continue
            numero = int(id_catalogo[4:])
            if id_catalogo.startswith("ent_"):
                fichas.append({"id": id_catalogo, "clase": "enemigo", "nombre": f"Enemigo {numero}", "vida_max": 10,
                               "ataque": 3, "defensa": 1, "velocidad": 100, "comportamiento": "guardián",
                               "suelta": [self._id_objeto(numero * 5 + 1)]})
            else:
                fichas.append({"id": id_catalogo, "clase": "arma", "nombre": f"Objeto {numero}", "peso": 2,
                               "valor": 10, "ataque_bonus": 1})
        return fichas


def _recorrido(ancho: int, alto: int) -> list:
    """Serpiente por toda la rejilla y vuelta atrás por la primera mitad (150 pasos con 10x10)."""
    ida = []
    for fila in range(alto):
        columnas = range(ancho) if fila % 2 == 0 else range(ancho - 1, -1, -1)
        for columna in columnas:
            ida.append(fila * ancho + columna + 1)
    vuelta = []
    for i in range(len(ida) // 2 - 1, -1, -1):
        vuelta.append(ida[i])
    return ida + vuelta


def cache_en_partida(filas: list, raiz: str, ancho: int = 10, alto: int = 10) -> None:
    """Juega un recorrido completo (como el bucle del juego: precarga las vecinas, entra a la sala, retiene las
    fichas de sus enemigos y las libera al salir) con distintas capacidades de caché. El disco absorbe los
    fallos de la caché, así que se registra también cuántas solicitudes de red costó cada capacidad."""
    seccion = "6. Caché en una partida completa (%d pasos por una rejilla de %dx%d)" % (len(_recorrido(ancho, alto)), ancho, alto)
    for capacidad in (5, 10, 25, 100, 1000):
        cliente = ClienteConCatalogo(ancho, alto)
        cache = CacheLRU(capacidad)
        servicio = ServicioCripta(ClientePersistente(cliente, AlmacenDisco(os.path.join(raiz, f"part{capacidad}"))), cache)
        servicio.listar_criptas()
        cid = servicio.obtener_id_cripta(1)
        servicio.crear_jugador(cid)
        servicio.ubicacion_llaves(cid)                # 012: la consulta de llaves, contada en el presupuesto
        cazadores = list(cliente.cazadores)           # 012: activos desde el inicio (peor caso)
        disparadas = 0
        retenidas: list = []
        for sala in _recorrido(ancho, alto):
            servicio.liberar_fichas(retenidas)
            servicio.precargar_vecinas(cid, sala)
            construida = servicio.construir_sala(cid, sala)
            retenidas = [enemigo.tipo for enemigo in construida.enemigos]
            servicio.retener_fichas(retenidas)
            disparadas += _mover_cazadores(servicio, cid, cazadores, sala)
        total = cache.aciertos + cache.fallos
        porcentaje = 100 * cache.aciertos / total if total else 0.0
        filas.append((seccion, f"capacidad {capacidad:>4}",
                      f"{cache.aciertos} aciertos / {cache.fallos} fallos ({porcentaje:.1f} %)",
                      f"{cliente.solicitudes_realizadas} solicitudes de red; de ellas, {disparadas} disparadas por un cazador"))
    # 012: bench/__init__.py llama a esta sección en último lugar; así las filas de la alternativa descartada
    # quedan al final del bloque (31 a 34) sin mover el número de ninguna fila existente.
    lista_enlazada_descartada(filas)


def ejecutar(imprimir=print) -> list:
    """Corre todas las mediciones. Devuelve las filas (sección, nombre, valor, unidad)."""
    filas: list = []
    with tempfile.TemporaryDirectory() as raiz:
        solicitudes_por_estrategia(filas, raiz)
        busqueda_en_cache(filas)
        ficha_liberada(filas, raiz)
        guardado_en_lote(filas, raiz)
        planear_vecindad(filas, raiz)
        cache_en_partida(filas, raiz)
    seccion = None
    for fila in filas:
        if fila[0] != seccion:
            seccion = fila[0]
            imprimir(f"\n{seccion}")
        imprimir(f"  {fila[1]:<58} {fila[2]:>10}  {fila[3]}")
    return filas


if __name__ == "__main__":
    ejecutar()
