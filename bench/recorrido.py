"""Recorrido por niveles (FR-510, FR-511, SC-004): lo que cuesta, con la alternativa descartada de cada decisión.

  A. Acotado frente a sin límite al crecer la cripta. CRITERIO DURO (SC-004): un recorrido de 2 niveles visita las mismas
     salas y examina las mismas salidas en criptas de 400, 4 900 y 40 000 salas. La razón de tiempos solo se informa.
  B. Cola circular (elegida) frente a `list` con pop(0), `list` con índice de cabeza y dos listas por nivel (sin cola),
     en rejilla (frontera angosta).
  C. Lo mismo en un árbol de ramificación 3 de 29 524 salas (frontera ancha), donde pop(0) debería degradarse.
  D. Orden dentro del nivel: ordenar_adaptativo por nivel (elegida) frente a un montículo con clave (nivel, id).
  E. Referencia de lo que hay hoy, ServicioCripta.salas_vecinas (deque y búsqueda lineal). SOLO INFORMATIVA.
  F. Equivalencia: el recorrido coincide con la referencia ingenua en criptas aleatorias.

Las alternativas descartadas existen SOLO aquí. Criptas sintéticas deterministas por semilla; sin red ni vista.
"""
from __future__ import annotations

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from bench.datos import azar
from bench.medicion import anotar, medir, nota, texto, verificar
from DTO.RecorridoDTO import RecorridoDTO
from Logica.MapaCripta import MapaCripta
from Logica.MonticuloMinimo import MonticuloMinimo
from Logica.ordenamiento import ordenar_adaptativo
from Logica.RecorridoPorNiveles import RecorridoPorNiveles
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import (esqueleto_arbol, esqueleto_dirigido_aleatorio, esqueleto_rejilla,
                                         mapa_desde_esqueleto)
from tests_labs.referencia_recorrido import recorrer_referencia

SECCION_A = "Recorrido por niveles (A): acotado frente a sin límite al crecer la cripta (SC-004)"
SECCION_B = "Recorrido por niveles (B): cola circular frente a la alternativa descartada, rejilla"
SECCION_C = "Recorrido por niveles (C): cola circular frente a la alternativa descartada, árbol de frontera ancha"
SECCION_D = "Recorrido por niveles (D): orden dentro del nivel, ordenar_adaptativo frente a montículo (nivel, id)"
SECCION_E = "Recorrido por niveles (E): referencia de lo que hay hoy, ServicioCripta.salas_vecinas (solo informativa)"
SECCION_F = "Recorrido por niveles (F): equivalencia con la referencia ingenua"

LADOS = (20, 70, 200)                           # 400, 4 900 y 40 000 salas
LIMITES = (2, 5, None)


# --------------------------------------------------------------------------- alternativas descartadas

class _Base:
    """Lo común de las alternativas: mismo mapa, mismas marcas de época, mismo resultado."""

    def __init__(self, mapa: MapaCripta) -> None:
        self.mapa = mapa
        self._marca = [0] * mapa.tamano
        self._epoca = 0

    def _vecinas(self, sala: int, nivel_de_sala: int, limite):
        """Salas nuevas que se descubren desde `sala` (las marca como visitadas)."""
        nuevas = []
        if limite is not None and nivel_de_sala >= limite:
            return nuevas
        mapa, marca, epoca = self.mapa, self._marca, self._epoca
        for arista in mapa.salientes[sala]:
            destino = arista.destino
            if 0 <= destino < mapa.tamano and mapa.existe[destino] and marca[destino] != epoca:
                marca[destino] = epoca
                nuevas.append(destino)
        return nuevas


class ColaConPop0(_Base):
    """DESCARTADA: cola con list y pop(0). Sacar cuesta O(largo de la cola): desplaza todo lo que queda."""

    def recorrer(self, origen: int, limite=None) -> RecorridoDTO:
        self._epoca += 1
        self._marca[origen] = self._epoca
        cola = [origen]
        salas, niveles, nivel = [], [], 0
        while cola:
            siguiente = []
            for _ in range(len(cola)):
                sala = cola.pop(0)
                salas.append(sala)
                niveles.append(nivel)
                siguiente.extend(self._vecinas(sala, nivel, limite))
            cola.extend(ordenar_adaptativo(siguiente))
            nivel += 1
        return RecorridoDTO(salas, niveles)


class ColaConIndiceDeCabeza(_Base):
    """DESCARTADA: list con un índice de cabeza que solo avanza. O(1), pero nunca libera lo ya sacado."""

    def recorrer(self, origen: int, limite=None) -> RecorridoDTO:
        self._epoca += 1
        self._marca[origen] = self._epoca
        cola = [origen]
        cabeza = 0
        niveles = [0]
        nivel = 0
        while cabeza < len(cola):
            fin = len(cola)
            siguiente = []
            while cabeza < fin:
                siguiente.extend(self._vecinas(cola[cabeza], nivel, limite))
                cabeza += 1
            for destino in ordenar_adaptativo(siguiente):
                cola.append(destino)
                niveles.append(nivel + 1)
            nivel += 1
        return RecorridoDTO(cola, niveles)


class DosListasPorNivel(_Base):
    """DESCARTADA (o por confirmar): sin cola; el nivel actual y el siguiente son dos listas que se intercambian."""

    def recorrer(self, origen: int, limite=None) -> RecorridoDTO:
        self._epoca += 1
        self._marca[origen] = self._epoca
        actual = [origen]
        salas, niveles, nivel = [], [], 0
        while actual:
            siguiente = []
            for sala in actual:
                salas.append(sala)
                niveles.append(nivel)
                siguiente.extend(self._vecinas(sala, nivel, limite))
            actual = ordenar_adaptativo(siguiente)
            nivel += 1
        return RecorridoDTO(salas, niveles)


class ConMonticuloNivelId(_Base):
    """DESCARTADA (o por confirmar): un MonticuloMinimo con clave (nivel, id) entrega las salas ya en el orden pedido,
    sin cola ni ordenar por nivel. Cuesta O(log V) por sala en vez de O(log ancho)."""

    def __init__(self, mapa: MapaCripta) -> None:
        super().__init__(mapa)
        self._monticulo = MonticuloMinimo()

    def recorrer(self, origen: int, limite=None) -> RecorridoDTO:
        self._epoca += 1
        self._marca[origen] = self._epoca
        monticulo = self._monticulo
        monticulo.vaciar()
        monticulo.insertar(0, origen)
        salas, niveles = [], []
        while not monticulo.vacio():
            nivel, sala = monticulo.extraer_minimo()
            salas.append(sala)
            niveles.append(nivel)
            for destino in self._vecinas(sala, nivel, limite):
                monticulo.insertar(nivel + 1, destino)
        return RecorridoDTO(salas, niveles)


# --------------------------------------------------------------------------- criptas de la medición

class Cripta:
    def __init__(self, nombre: str, esqueleto: list, origen: int) -> None:
        self.nombre = nombre
        self.esqueleto = esqueleto
        self.total = len(esqueleto)
        self.origen = origen
        self.mapa = mapa_desde_esqueleto(esqueleto)


def rejilla(lado: int) -> Cripta:
    return Cripta(f"rejilla {lado * lado:>6} salas", esqueleto_rejilla(lado, lado), (lado // 2) * lado + lado // 2 + 1)


def arbol() -> Cripta:
    return Cripta("árbol 3-ario 29 524 salas", esqueleto_arbol(3, 9), 1)


def _forma(resultado: RecorridoDTO) -> tuple:
    return tuple(resultado.salas), tuple(resultado.niveles)


def _ancho_maximo(resultado: RecorridoDTO) -> int:
    cuentas = [0] * (resultado.niveles[-1] + 1)
    for nivel in resultado.niveles:
        cuentas[nivel] += 1
    mayor = 0
    for c in cuentas:
        if c > mayor:
            mayor = c
    return mayor


# --------------------------------------------------------------------------- secciones

def seccion_a(filas: list) -> bool:
    cumple = True
    criptas = [rejilla(lado) for lado in LADOS]
    recorridores = [RecorridoPorNiveles(c.mapa) for c in criptas]
    tiempos_limite_2 = []
    for limite in LIMITES:
        conteos = []
        for cripta, recorridor in zip(criptas, recorridores):
            repeticiones = 5 if limite is None else 25
            resultado = medir(lambda: recorridor.recorrer(cripta.origen, limite=limite), repeticiones=repeticiones)
            conteos.append((recorridor.salas_visitadas, recorridor.salidas_examinadas))
            etiqueta = "sin límite" if limite is None else f"límite {limite} niveles"
            anotar(filas, SECCION_A, f"{cripta.nombre}  {etiqueta:<16} ({recorridor.salas_visitadas:>6,} salas visitadas, "
                                     f"{recorridor.salidas_examinadas:>6,} salidas examinadas)", resultado)
            if limite == 2:
                tiempos_limite_2.append(resultado[0])
        if limite is not None:                        # CRITERIO DURO de SC-004: el conteo no crece con la cripta
            iguales = conteos[0] == conteos[1] == conteos[2]
            cumple = cumple and verificar(filas, SECCION_A, f"límite {limite}: mismas salas visitadas y mismas salidas examinadas "
                                                           f"en 400, 4 900 y 40 000 salas {conteos[0]}", iguales)
    razon = tiempos_limite_2[-1] / tiempos_limite_2[0] if tiempos_limite_2[0] else 0.0
    filas.append((SECCION_A, "razón de tiempos con límite 2: 40 000 salas / 400 salas (INFORMATIVA, sin umbral)",
                  f"{razon:.2f}×", "se espera cercana a 1; depende de la máquina"))
    nota(filas, SECCION_A, "Sin límite el trabajo sí crece con la cripta porque todo es alcanzable; con límite depende solo de la zona alrededor del origen.")
    return cumple


def _comparar_colas(filas: list, seccion: str, cripta: Cripta, repeticiones: int) -> bool:
    elegida = RecorridoPorNiveles(cripta.mapa)
    alternativas = (("lista con pop(0) (descartada)", ColaConPop0(cripta.mapa)),
                    ("lista con índice de cabeza (descartada)", ColaConIndiceDeCabeza(cripta.mapa)),
                    ("dos listas por nivel, sin cola (descartada)", DosListasPorNivel(cripta.mapa)))
    esperado = _forma(elegida.recorrer(cripta.origen))
    ancho = _ancho_maximo(elegida.recorrer(cripta.origen))
    ok = True
    for nombre, alternativa in alternativas:
        ok = verificar(filas, seccion, f"{cripta.nombre}: {nombre.split(' (')[0]} da el mismo recorrido",
                       _forma(alternativa.recorrer(cripta.origen)) == esperado) and ok
    if not ok:
        return False
    anotar(filas, seccion, f"{cripta.nombre}  cola circular (elegida)",
           medir(lambda: elegida.recorrer(cripta.origen), repeticiones=repeticiones))
    for nombre, alternativa in alternativas:
        anotar(filas, seccion, f"{cripta.nombre}  {nombre}",
               medir(lambda: alternativa.recorrer(cripta.origen), repeticiones=repeticiones))
    filas.append((seccion, f"{cripta.nombre}  nivel más ancho", f"{ancho:,} salas", "tamaño máximo que llega a tener la cola"))
    return True


def seccion_b(filas: list) -> bool:
    ok = True
    for lado in LADOS[1:]:
        ok = _comparar_colas(filas, SECCION_B, rejilla(lado), repeticiones=5) and ok
    nota(filas, SECCION_B, "Sin límite, desde el centro. La frontera de una rejilla es angosta: pop(0) desplaza pocos elementos.")
    return ok


def seccion_c(filas: list) -> bool:
    ok = _comparar_colas(filas, SECCION_C, arbol(), repeticiones=3)
    nota(filas, SECCION_C, "En el árbol el último nivel tiene 19 683 salas: cada pop(0) desplaza una cola de ese largo.")
    return ok


def seccion_d(filas: list) -> bool:
    ok = True
    for cripta in (rejilla(200), arbol()):
        elegida = RecorridoPorNiveles(cripta.mapa)
        montículo = ConMonticuloNivelId(cripta.mapa)
        ok = verificar(filas, SECCION_D, f"{cripta.nombre}: el montículo da el mismo recorrido",
                       _forma(montículo.recorrer(cripta.origen)) == _forma(elegida.recorrer(cripta.origen))) and ok
        anotar(filas, SECCION_D, f"{cripta.nombre}  ordenar_adaptativo por nivel (elegida)",
               medir(lambda: elegida.recorrer(cripta.origen), repeticiones=5))
        anotar(filas, SECCION_D, f"{cripta.nombre}  montículo (nivel, id) (descartada)",
               medir(lambda: montículo.recorrer(cripta.origen), repeticiones=5))
    nota(filas, SECCION_D, "El montículo no necesita cola ni ordenar por nivel, pero paga log V por sala en vez de log del ancho del nivel.")
    return ok


def seccion_e(filas: list) -> None:
    for lado in LADOS:
        cripta = rejilla(lado)
        servicio = ServicioCripta(HttpConfigurable(cripta.esqueleto), CacheLRU(5))
        servicio.listar_criptas()
        id_cripta = servicio.obtener_id_cripta(1)
        servicio.salas_vecinas(id_cripta, cripta.origen, 1)                  # calienta el esqueleto
        nuevo = RecorridoPorNiveles(cripta.mapa)
        for limite in (2, 5):
            hoy = medir(lambda: servicio.salas_vecinas(id_cripta, cripta.origen, limite), repeticiones=5)
            anotar(filas, SECCION_E, f"{cripta.nombre}  límite {limite}  salas_vecinas (hoy, {len(servicio.salas_vecinas(id_cripta, cripta.origen, limite))} salas)", hoy)
            anotar(filas, SECCION_E, f"{cripta.nombre}  límite {limite}  recorrido nuevo ({len(nuevo.recorrer(cripta.origen, limite=limite).salas) - 1} salas)",
                   medir(lambda: nuevo.recorrer(cripta.origen, limite=limite), repeticiones=25))
    nota(filas, SECCION_E, "No se compara la secuencia: salas_vecinas ordena por letra de dirección y no incluye el origen. No interviene en el veredicto.")
    nota(filas, SECCION_E, "salas_vecinas busca cada sala en el esqueleto con un recorrido lineal: su costo depende del tamaño de la cripta.")


def seccion_f(filas: list) -> bool:
    diferencias = 0
    comparaciones = 0
    for semilla in range(60):
        total = 1 + (semilla * 53) % 400
        esqueleto = esqueleto_dirigido_aleatorio(total, 5000 + semilla, 0.25, 0.3 if semilla % 2 else 0.0)
        ids = [s["id"] for s in esqueleto]
        recorridor = RecorridoPorNiveles(mapa_desde_esqueleto(esqueleto))
        rng = azar(semilla)
        for _ in range(5):
            origen = ids[rng.randrange(len(ids))]
            limite = None if rng.random() < 0.3 else rng.randint(0, 8)
            esperado = recorrer_referencia(esqueleto, origen, limite=limite)
            obtenido = recorridor.recorrer(origen, limite=limite)
            comparaciones += 1
            if (obtenido.salas, obtenido.niveles) != esperado:
                diferencias += 1
    return verificar(filas, SECCION_F, f"{comparaciones} recorridos frente a la referencia, {diferencias} diferencias", diferencias == 0)


def ejecutar(filas: list) -> bool:
    cumple = seccion_a(filas)
    cumple = seccion_b(filas) and cumple
    cumple = seccion_c(filas) and cumple
    cumple = seccion_d(filas) and cumple
    seccion_e(filas)
    cumple = seccion_f(filas) and cumple
    return cumple
