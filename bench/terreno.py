"""Terreno y cazador (FR-121, FR-122, FR-123): cuánto cuesta decidir a los cazadores y qué ganan las decisiones tomadas.

Cada sección mide la decisión elegida y la ALTERNATIVA DESCARTADA (principio VII), sobre criptas sintéticas en rejilla
con costos y puertas cerradas deterministas por semilla. Se mide la DECISIÓN del cazador (`ComportamientoCazador.decidir`)
y no su movimiento, para que el estado no cambie entre repeticiones. Sin red ni vista.

  A. Un cazador frente a muchos   elegida: campo compartido y reutilizado | descartada: calcular desde cero por cazador
  B. Rango pequeño frente a grande elegida: búsqueda acotada por el rango  | descartada: búsqueda sin cota (toda la cripta)
  C. Puertas estables frente a cambiantes
                                   elegida: invalidar por evento           | descartada: invalidar con cualquier cambio
  D. Equivalencia                  la decisión reutilizada coincide con la calculada desde cero
  E. Búsqueda con vista            elegida: BuscadorRutas sobre una vista del mapa | descartada: campo sin vista (la búsqueda
                                   dentro del campo, directa sobre el mapa, como estaba antes del contrato compartido)
"""
from __future__ import annotations

import types

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from bench.datos import azar
from bench.medicion import anotar, medir, nota, texto, verificar
from DTO.SalaDTO import SalaDTO
from DTO.ActorDTO import JugadorDTO
from Logica.CampoDeCostos import CampoDeCostos
from Logica.CompCazador import ComportamientoCazador
from Logica.MapaCripta import MapaCripta
from Logica.MonticuloMinimo import MonticuloMinimo
from Logica.PuertasLogica import fijar_cerrada
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_rejilla

SECCION_A = "Terreno y cazador (A): un cazador frente a muchos, ciclo de decisiones — límite 20 ms (FR-121)"
SECCION_B = "Terreno y cazador (B): rango pequeño frente a grande al crecer la cripta (FR-122)"
SECCION_C = "Terreno y cazador (C): puertas estables frente a cambiantes (FR-123)"
SECCION_D = "Terreno y cazador (D): la decisión reutilizada es la de calcular desde cero (principio III)"

SECCION_E = "Terreno y cazador (E): búsqueda con vista del mapa frente al campo sin vista (T071)"

LIMITE_US = 20_000
COSTO_MAX = 300
RANGO_PEQUENO = 600           # unos 4 a 6 pasos
RANGO_SIN_COTA = 10 ** 9      # alternativa descartada: ninguna cota
CAZADORES = (1, 10, 50, 200)
LADOS = (20, 70, 200)         # 400, 4 900 y 40 000 salas


class Cripta:
    """Rejilla lado x lado con las salas del modelo SOLO donde hay cazadores (las demás quedan sin descargar)."""

    def __init__(self, lado: int, semilla: int = 0, cerradas: float = 0.15):
        self.lado = lado
        self.esqueleto = esqueleto_rejilla(lado, lado, semilla=semilla, costo_max=COSTO_MAX, fraccion_cerradas=cerradas)
        servicio = ServicioCripta(HttpConfigurable(self.esqueleto), CacheLRU(5))
        servicio.listar_criptas()
        self.mapa = MapaCripta(servicio.obtener_mapa(servicio.obtener_id_cripta(1)))
        self.total = lado * lado
        self.salas: list = [None] * (self.total + 1)
        self.jugador = JugadorDTO(1, 1, 1, 1, 100, id_sala_actual=self.total // 2 + lado // 2)

    def distancia_al_jugador(self, sala: int) -> int:
        """Distancia en filas/columnas de la rejilla entre `sala` y el jugador (solo para ARMAR la carga del bench)."""
        jf, jc = divmod(self.jugador.id_sala_actual - 1, self.lado)
        sf, sc = divmod(sala - 1, self.lado)
        return max(abs(jf - sf), abs(jc - sc))

    def poner_cazadores(self, cantidad: int, rango: int, semilla: int = 1, radio: int | None = None) -> list:
        """Cazadores en salas al azar; con `radio`, todos dentro de ese cuadrado alrededor del jugador (carga realista:
        así varios están dentro de su rango y la decisión hace trabajo de verdad)."""
        rng = azar(semilla)
        cazadores = []
        for _ in range(cantidad):
            sala = rng.randint(1, self.total)
            while radio is not None and self.distancia_al_jugador(sala) > radio:
                sala = rng.randint(1, self.total)
            if self.salas[sala] is None:
                self.salas[sala] = self._sala(sala)
            cazadores.append(types.SimpleNamespace(id_sala_actual=sala, rango=rango))
        return cazadores

    def _sala(self, numero: int) -> SalaDTO:
        sala = SalaDTO(id=numero, nombre=f"Sala {numero}")
        sala.salidas = ServicioCripta._armar_salidas(self.esqueleto[numero - 1]["salidas"])
        return sala

    def campo(self) -> CampoDeCostos:
        return CampoDeCostos(self.mapa, self.jugador, self.salas)

    def puertas(self, cerca: bool | None = None, radio: int = 4) -> list:
        """(origen, destino) de las conexiones, en orden fijo. cerca=True: solo las de la zona del jugador; False: solo
        las lejanas (a más de 3 veces el radio); None: todas."""
        conexiones = []
        for sala in self.esqueleto:
            distancia = self.distancia_al_jugador(sala["id"])
            if cerca is True and distancia > radio:
                continue
            if cerca is False and distancia <= 3 * radio:
                continue
            for salida in sala["salidas"].values():
                conexiones.append((sala["id"], salida["sala"]))
        return conexiones


def decidir_a_todos(cazadores: list, salas: list, campo: CampoDeCostos) -> list:
    return [ComportamientoCazador.decidir(c, salas, campo) for c in cazadores]


def _mover_puerta(cripta: Cripta, campo: CampoDeCostos, origen: int, destino: int, cerrada: bool) -> None:
    if cripta.salas[origen] is None:
        cripta.salas[origen] = cripta._sala(origen)        # una puerta solo cambia en una sala cargada
    for salida in cripta.salas[origen].salidas:
        if salida.sala_destino == destino:
            fijar_cerrada(salida, cerrada, lambda s: campo.puerta_cambio(s.sala_destino))


def seccion_a(filas: list) -> bool:
    cumple = True
    cripta = Cripta(50)
    centro = cripta.jugador.id_sala_actual
    recorrido = [centro, centro + 1, centro + 51, centro + 50, centro - 1, centro - 51, centro - 50]    # nunca repite la sala de un ciclo al siguiente
    for cantidad in CAZADORES:
        cazadores = cripta.poner_cazadores(cantidad, RANGO_PEQUENO, radio=4)
        elegida = cripta.campo()
        descartada = cripta.campo()
        descartada.reutilizar = False
        enrango = sum(1 for _, d in decidir_a_todos(cazadores, cripta.salas, elegida) if d is not None)
        iguales = verificar(filas, SECCION_A, f"{cantidad} cazadores ({enrango} dentro de su rango): ambas decisiones coinciden",
                            decidir_a_todos(cazadores, cripta.salas, elegida) == decidir_a_todos(cazadores, cripta.salas, descartada))
        if not iguales:
            cumple = False
            continue
        turno = [0]

        def ciclo(campo, se_mueve):
            if se_mueve:                                   # el jugador cambia de sala: hay que recalcular una vez por ciclo
                turno[0] += 1
                cripta.jugador.id_sala_actual = recorrido[turno[0] % len(recorrido)]
            decidir_a_todos(cazadores, cripta.salas, campo)

        for se_mueve, etiqueta in ((False, "jugador quieto"), (True, "jugador se mueve cada ciclo")):
            resultado = medir(lambda: ciclo(elegida, se_mueve), repeticiones=25)
            anotar(filas, SECCION_A, f"{cantidad:>4} cazadores, {etiqueta:<27} campo compartido (elegida)", resultado)
            anotar(filas, SECCION_A, f"{cantidad:>4} cazadores, {etiqueta:<27} desde cero por cazador (descartada)",
                   medir(lambda: ciclo(descartada, se_mueve), repeticiones=25))
            if cantidad <= 50:                             # "decenas de cazadores" (FR-121)
                ok = resultado[2] < LIMITE_US
                cumple = cumple and ok
                filas.append((SECCION_A, f"    ¿el peor de 25 ciclos con {cantidad} cazadores ({etiqueta}) < 20 ms?",
                              "CUMPLE" if ok else "NO CUMPLE", f"(máx {texto(resultado[2])})"))
        cripta.jugador.id_sala_actual = centro
    nota(filas, SECCION_A, "Un ciclo = cada cazador decide una vez. El campo compartido explora la zona una vez (y solo si algo cambió); la alternativa la repite por cazador.")
    nota(filas, SECCION_A, "Los cazadores están dentro de un cuadrado de 9 x 9 salas alrededor del jugador: parte está dentro de su rango y parte no.")
    return cumple


def seccion_b(filas: list) -> None:
    for lado in LADOS:
        cripta = Cripta(lado)
        cazadores = cripta.poner_cazadores(1, RANGO_PEQUENO, radio=4)
        grande = [types.SimpleNamespace(id_sala_actual=c.id_sala_actual, rango=RANGO_SIN_COTA) for c in cazadores]
        campo = cripta.campo()
        campo.reutilizar = False                           # se mide la búsqueda fría: lo que cuesta calcularla
        antes = campo.salas_fijadas
        decidir_a_todos(cazadores, cripta.salas, campo)
        pequena_salas = campo.salas_fijadas - antes
        antes = campo.salas_fijadas
        decidir_a_todos(grande, cripta.salas, campo)
        grande_salas = campo.salas_fijadas - antes
        anotar(filas, SECCION_B, f"{cripta.total:>6} salas  rango pequeño {RANGO_PEQUENO} — acotada (elegida)",
               medir(lambda: decidir_a_todos(cazadores, cripta.salas, campo), repeticiones=9))
        anotar(filas, SECCION_B, f"{cripta.total:>6} salas  sin cota (descartada)",
               medir(lambda: decidir_a_todos(grande, cripta.salas, campo), repeticiones=5))
        filas.append((SECCION_B, f"{cripta.total:>6} salas  salas exploradas: acotada / sin cota", f"{pequena_salas:,} / {grande_salas:,}", ""))
    nota(filas, SECCION_B, "Con rango pequeño el trabajo depende de la zona dentro del rango, no de cuántas salas tiene la cripta.")


def seccion_c(filas: list) -> None:
    pasos = 40
    variantes = (("estables (sin cambios)", None), ("cambian lejos de la zona", False), ("cambian dentro de la zona", True))
    for etiqueta, cerca in variantes:
        for nombre, siempre in (("invalidar por evento (elegida)", False), ("invalidar con cualquier cambio (descartada)", True)):
            cripta = Cripta(50)
            cazadores = cripta.poner_cazadores(50, RANGO_PEQUENO, radio=4)
            campo = cripta.campo()
            campo.invalidar_siempre = siempre
            conexiones = cripta.puertas(cerca) if cerca is not None else []
            rng = azar(7)
            decidir_a_todos(cazadores, cripta.salas, campo)

            def ciclo():
                if conexiones:
                    origen, destino = conexiones[rng.randrange(len(conexiones))]
                    _mover_puerta(cripta, campo, origen, destino, rng.random() < 0.5)
                decidir_a_todos(cazadores, cripta.salas, campo)

            calculos = campo.calculos
            resultado = medir(lambda: [ciclo() for _ in range(pasos)], repeticiones=7)
            anotar(filas, SECCION_C, f"puertas {etiqueta:<26} {nombre}", resultado)
            filas.append((SECCION_C, f"    búsquedas por cada {pasos} ciclos", f"{(campo.calculos - calculos) // 8:,}", ""))
    nota(filas, SECCION_C, f"{pasos} ciclos seguidos con 50 cazadores de rango pequeño en 2 500 salas; una puerta cambia por ciclo. "
                           "Cambiar una puerta fuera de la zona calculada no obliga a recalcular.")


def seccion_d(filas: list) -> None:
    cripta = Cripta(20)
    cazadores = cripta.poner_cazadores(40, 900)
    elegida = cripta.campo()
    conexiones = cripta.puertas()
    rng = azar(11)
    diferencias = 0
    comparaciones = 0
    for _ in range(300):
        tirada = rng.random()
        if tirada < 0.6:
            origen, destino = conexiones[rng.randrange(len(conexiones))]
            _mover_puerta(cripta, elegida, origen, destino, rng.random() < 0.5)
        elif tirada < 0.9:
            cripta.jugador.id_sala_actual = rng.randint(1, cripta.total)
        else:
            cazadores = cripta.poner_cazadores(40, rng.choice((200, 500, 900)), semilla=rng.randint(0, 99))
        referencia = cripta.campo()
        for resultado_a, resultado_b in zip(decidir_a_todos(cazadores, cripta.salas, elegida), decidir_a_todos(cazadores, cripta.salas, referencia)):
            comparaciones += 1
            if (None if resultado_a[0] is None else resultado_a[0].sala_destino, resultado_a[1]) != \
               (None if resultado_b[0] is None else resultado_b[0].sala_destino, resultado_b[1]):
                diferencias += 1
    verificar(filas, SECCION_D, f"{comparaciones:,} decisiones reutilizadas vs desde cero, {diferencias} diferencias", diferencias == 0)
    filas.append((SECCION_D, "decisiones idénticas", f"{100 * (comparaciones - diferencias) // comparaciones} %", "debe ser 100 %"))


class CampoSinVista(CampoDeCostos):
    """ALTERNATIVA DESCARTADA (T071): el campo con la búsqueda escrita dentro, directa sobre las listas del mapa, sin la
    capa de la vista (`entrantes`, `salidas` y `transitable` son aquí accesos directos). Es el código de `CampoDeCostos`
    antes de `BuscadorRutas`; la invalidación y la reutilización son las mismas, solo cambia cómo se busca."""

    def __init__(self, mapa, jugador, salas) -> None:
        super().__init__(mapa, jugador, salas)
        self._costo_d: list[int] = [0] * mapa.tamano
        self._marca_d: list[int] = [0] * mapa.tamano
        self._epoca_d = 0
        self._monticulo_d = MonticuloMinimo()
        self._fijadas = 0

    @property
    def salas_fijadas(self) -> int:
        return self._fijadas

    def puerta_cambio(self, destino: int) -> None:
        if not self._valido:
            return
        if self.invalidar_siempre or (0 <= destino < self.mapa.tamano and self._marca_d[destino] == self._epoca_d):
            self._valido = False
            self.invalidaciones += 1

    def costo(self, sala: int):
        if 0 <= sala < self.mapa.tamano and self._marca_d[sala] == self._epoca_d:
            return self._costo_d[sala]
        return None

    def siguiente_paso(self, origen: int):
        d = self.costo(origen)
        if d is None or d == 0:
            return None
        elegida = None
        for arista in self.mapa.salientes[origen]:
            if not self.mapa.esta_abierta(arista, self.salas):
                continue
            restante = self.costo(arista.destino)
            if restante is None or arista.costo + restante != d:
                continue
            if elegida is None or arista.destino < elegida.destino:
                elegida = arista
        return elegida

    def _calcular(self, cota: int) -> None:
        self.calculos += 1
        self._epoca_d += 1
        epoca = self._epoca_d
        origen = self.jugador.id_sala_actual
        monticulo = self._monticulo_d
        monticulo.vaciar()
        if not 0 <= origen < self.mapa.tamano or cota < 0:
            return
        costos, marcas = self._costo_d, self._marca_d
        costos[origen] = 0
        marcas[origen] = epoca
        monticulo.insertar(0, origen)
        while not monticulo.vacio():
            costo, sala = monticulo.extraer_minimo()
            if costo > costos[sala]:
                continue
            self._fijadas += 1
            for arista in self.mapa.entrantes_por_sala[sala]:
                if not self.mapa.esta_abierta(arista, self.salas):
                    continue
                nuevo = costo + arista.costo
                if nuevo > cota:
                    continue
                x = arista.origen
                if marcas[x] != epoca or nuevo < costos[x]:
                    costos[x] = nuevo
                    marcas[x] = epoca
                    monticulo.insertar(nuevo, x)


def seccion_e(filas: list) -> bool:
    """Misma carga que la sección A (50 y 200 cazadores en el cuadrado de 9 x 9) y que la B (búsqueda fría, rango pequeño
    y sin cota): lo único que cambia es si la búsqueda pasa por la vista o va directa al mapa."""
    cumple = True
    cripta = Cripta(50)
    centro = cripta.jugador.id_sala_actual
    recorrido = [centro, centro + 1, centro + 51, centro + 50, centro - 1, centro - 51, centro - 50]
    for cantidad in (50, 200):
        cazadores = cripta.poner_cazadores(cantidad, RANGO_PEQUENO, radio=4)
        elegida = cripta.campo()
        descartada = CampoSinVista(cripta.mapa, cripta.jugador, cripta.salas)
        cumple = verificar(filas, SECCION_E, f"{cantidad} cazadores: ambas decisiones coinciden",
                           decidir_a_todos(cazadores, cripta.salas, elegida) == decidir_a_todos(cazadores, cripta.salas, descartada)) and cumple
        turno = [0]

        def ciclo(campo, se_mueve):
            if se_mueve:
                turno[0] += 1
                cripta.jugador.id_sala_actual = recorrido[turno[0] % len(recorrido)]
            decidir_a_todos(cazadores, cripta.salas, campo)

        for se_mueve, etiqueta in ((False, "jugador quieto"), (True, "jugador se mueve cada ciclo")):
            anotar(filas, SECCION_E, f"{cantidad:>4} cazadores, {etiqueta:<27} con vista (elegida)",
                   medir(lambda: ciclo(elegida, se_mueve), repeticiones=25))
            anotar(filas, SECCION_E, f"{cantidad:>4} cazadores, {etiqueta:<27} sin vista (descartada)",
                   medir(lambda: ciclo(descartada, se_mueve), repeticiones=25))
        cripta.jugador.id_sala_actual = centro
    for lado in LADOS:
        cripta = Cripta(lado)
        cazadores = cripta.poner_cazadores(1, RANGO_PEQUENO, radio=4)
        elegida = cripta.campo()
        elegida.reutilizar = False
        descartada = CampoSinVista(cripta.mapa, cripta.jugador, cripta.salas)
        descartada.reutilizar = False
        anotar(filas, SECCION_E, f"{cripta.total:>6} salas, búsqueda fría de rango pequeño con vista (elegida)",
               medir(lambda: decidir_a_todos(cazadores, cripta.salas, elegida), repeticiones=9))
        anotar(filas, SECCION_E, f"{cripta.total:>6} salas, búsqueda fría de rango pequeño sin vista (descartada)",
               medir(lambda: decidir_a_todos(cazadores, cripta.salas, descartada), repeticiones=9))
    nota(filas, SECCION_E, "La vista agrega una llamada por arista (entrantes, transitable y salidas); lo que se mide es ese costo frente a lo que se gana al poder buscar sobre el mapa conocido.")
    return cumple


def ejecutar(filas: list) -> bool:
    cumple = seccion_a(filas)
    seccion_b(filas)
    seccion_c(filas)
    seccion_d(filas)
    cumple = seccion_e(filas) and cumple
    return cumple
