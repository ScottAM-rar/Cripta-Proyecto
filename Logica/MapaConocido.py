"""Conocimiento del jugador sobre la cripta (capacidad 002, niebla de guerra).

Cada sala está para el jugador explorada, avistada o desconocida, y cada salida recuerda el estado de su puerta tal como
se vio por última vez. Es estado del modelo: se deshace con el pergamino y no depende de qué contenido se haya descargado.

Estructuras (principio I): `estado` es una lista indexada por id de sala (consultar es acceso directo); `puertas` es una
lista plana de cuatro posiciones por sala (`sala*4 + d`, con d = 0 norte, 1 sur, 2 este, 3 oeste); `exploradas` guarda los
ids en orden de descubrimiento para deshacer quitando del final. Se dimensionan con el mayor id del esqueleto más uno (los
ids van desde 1; la posición 0 no se usa). Sin `dict`/`set`; el orden del mapa sale de `ordenar_adaptativo`.

Solo lee el esqueleto (`MapaCripta`, sin modificarlo) y `MapaCripta.esta_abierta`: explorar nunca pasa por
`ingresarEnSala` ni descarga contenido, así que la antorcha no activa enemigos ni trampas (FR-211). Nunca escribe el estado
de una puerta: el único punto de cambio sigue siendo `PuertasLogica.fijar_cerrada` (FR-207).
"""
from __future__ import annotations

from DTO.CambioDTO import CambioDTO
from DTO.ConocimientoDTO import (MapaConocidoDTO, SalaConocidaDTO, SalidaConocidaDTO,
                                 PUERTA_ABIERTA, PUERTA_CERRADA, PUERTA_SIN_OBSERVAR)
from DTO.EstadoGuardadoDTO import ConocimientoGuardadoDTO, PuertaRecordadaDTO
from Logica.ordenamiento import ordenar_adaptativo

DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2
SIN_OBSERVAR, ABIERTA, CERRADA = 0, 1, 2
DIRECCIONES = ("norte", "sur", "este", "oeste")           # el orden N, S, E, O del esqueleto
_TEXTO_PUERTA = (PUERTA_SIN_OBSERVAR, PUERTA_ABIERTA, PUERTA_CERRADA)


class MapaConocido:
    def __init__(self, mapa, nombres: list, salas: list, jugador, registrar=None) -> None:
        """`mapa`: MapaCripta. `nombres`: nombre de cada sala del esqueleto, por id. `salas`: lista de salas del modelo (solo
        se lee para saber el estado real de una puerta). `registrar`: función que recibe una lista de CambioDTO."""
        self.mapa = mapa
        self.nombres = nombres
        self.salas = salas
        self.jugador = jugador
        self.registrar = registrar
        tamano = mapa.tamano
        self.estado: list[int] = [DESCONOCIDA] * tamano
        self.puertas: list[int] = [SIN_OBSERVAR] * (4 * tamano)
        self.exploradas: list[int] = []
        self.version_conocimiento = 0          # sube con todo cambio, también al deshacer
        self.salas_reveladas = 0               # del último `entrar`: salas cuyo estado cambió (para pruebas y --bench)
        self.salidas_examinadas = 0            # del último `entrar`: salidas del esqueleto que se miraron

    # --- consultas (acceso directo, FR-223) ---

    def estado_de(self, sala: int) -> int:
        return self.estado[sala]

    def puerta_recordada(self, sala: int, direccion: int) -> int:
        return self.puertas[sala * 4 + direccion]

    @staticmethod
    def indice_direccion(direccion) -> int:
        for i in range(4):
            if DIRECCIONES[i] == direccion:
                return i
        raise ValueError(f"Dirección desconocida: {direccion!r}")

    # --- instante 0 y entrada del jugador ---

    def iniciar(self, sala: int) -> None:
        """Conocimiento del instante 0 (FR-202): como si el jugador acabara de entrar. No se registra: no se puede deshacer."""
        self._entrada(sala, False)

    def entrar(self, sala: int, antorcha: bool = False) -> None:
        """El jugador entra a `sala` (FR-204). Con la antorcha encendida en este instante explora además sus vecinas
        (FR-210); la antorcha solo actúa aquí (FR-212). Todo cambio va en un solo nodo del historial del pergamino."""
        cambios = self._entrada(sala, antorcha)
        if cambios and self.registrar is not None:
            self.registrar(cambios)

    def _entrada(self, sala: int, antorcha: bool) -> list:
        mapa = self.mapa
        if isinstance(sala, bool) or not isinstance(sala, int) or not 0 <= sala < mapa.tamano or not mapa.existe[sala]:
            raise ValueError(f"La sala {sala!r} no existe en el esqueleto")
        self.salas_reveladas = 0
        self.salidas_examinadas = 0
        cambios: list = []
        self._explorar(sala, cambios)
        for arista in mapa.salidas(sala):                 # puertas de las salidas propias
            self._observar(arista, cambios)
        for arista in mapa.entrantes(sala):               # y de las salidas que llegan aquí (la otra mitad de la conexión)
            self._observar(arista, cambios)
        if antorcha:
            for arista in mapa.salidas(sala):             # bucle directo: un solo nivel (research §4)
                destino = arista.destino
                if 0 <= destino < mapa.tamano and mapa.existe[destino] and self.estado[destino] != EXPLORADA:
                    self._explorar(destino, cambios)      # no observa sus puertas (FR-209)
        return cambios

    def _explorar(self, sala: int, cambios: list) -> None:
        estado = self.estado
        if estado[sala] == EXPLORADA:
            return
        cambios.append(CambioDTO(tipo_accion="EXPLORAR_SALA", objeto_afectado=self, indice=sala,
                                 valor_anterior=estado[sala], valor_nuevo=EXPLORADA))
        estado[sala] = EXPLORADA
        self.exploradas.append(sala)
        self.version_conocimiento += 1
        self.salas_reveladas += 1
        mapa = self.mapa
        for arista in mapa.salidas(sala):
            self.salidas_examinadas += 1
            destino = arista.destino
            if 0 <= destino < mapa.tamano and mapa.existe[destino] and estado[destino] == DESCONOCIDA:
                cambios.append(CambioDTO(tipo_accion="AVISTAR_SALA", objeto_afectado=self, indice=destino,
                                         valor_anterior=DESCONOCIDA, valor_nuevo=AVISTADA))
                estado[destino] = AVISTADA
                self.version_conocimiento += 1
                self.salas_reveladas += 1

    def _observar(self, arista, cambios: list) -> None:
        self.salidas_examinadas += 1
        nuevo = ABIERTA if self.mapa.esta_abierta(arista, self.salas) else CERRADA
        posicion = arista.origen * 4 + self.indice_direccion(arista.direccion)
        anterior = self.puertas[posicion]
        if anterior != nuevo:
            cambios.append(CambioDTO(tipo_accion="OBSERVAR_PUERTA", objeto_afectado=self, indice=posicion,
                                     valor_anterior=anterior, valor_nuevo=nuevo))
            self.puertas[posicion] = nuevo
            self.version_conocimiento += 1

    # --- una puerta cambia mientras el jugador está junto a ella (FR-207, FR-208) ---

    def puerta_cambio(self, salida) -> None:
        """Aviso de `fijar_cerrada` en una acción hacia adelante. Si `salida` es una salida de la sala del jugador o una que
        llega a ella, se observa; si cambió lejos, no pasa nada (el mapa conserva lo que recuerda)."""
        posicion = self._posicion_adyacente(salida)
        if posicion < 0:
            return
        nuevo = CERRADA if salida.cerrada else ABIERTA
        anterior = self.puertas[posicion]
        if anterior == nuevo:
            return
        cambio = CambioDTO(tipo_accion="OBSERVAR_PUERTA", objeto_afectado=self, indice=posicion,
                           valor_anterior=anterior, valor_nuevo=nuevo)
        self.puertas[posicion] = nuevo
        self.version_conocimiento += 1
        if self.registrar is not None:
            self.registrar([cambio])

    def _posicion_adyacente(self, salida) -> int:
        """Posición de `salida` en `puertas` si está en la sala del jugador o llega a ella; -1 si no. Busca por identidad."""
        actual = self.jugador.id_sala_actual
        salas = self.salas
        sala = salas[actual] if 0 <= actual < len(salas) else None
        if sala is not None:
            for candidata in sala.salidas:
                if candidata is salida:
                    return actual * 4 + self.indice_direccion(candidata.direccion)
        for arista in self.mapa.entrantes(actual):
            origen = salas[arista.origen] if 0 <= arista.origen < len(salas) else None
            if origen is None:
                continue
            for candidata in origen.salidas:
                if candidata is salida and candidata.sala_destino == actual:      # solo las que llegan a la sala del jugador (FR-207)
                    return arista.origen * 4 + self.indice_direccion(candidata.direccion)
        return -1

    # --- pergamino de retroceso (FR-214, FR-225) ---

    def deshacer(self, cambio) -> None:
        """Revierte un cambio de conocimiento. No registra nada. Se llama en orden inverso al de registro."""
        tipo = cambio.tipo_accion
        if tipo == "EXPLORAR_SALA":
            if not self.exploradas or self.exploradas[-1] != cambio.indice:
                raise ValueError("Se deshace la exploración de una sala que no es la última explorada")
            self.exploradas.pop()
            self.estado[cambio.indice] = cambio.valor_anterior
        elif tipo == "AVISTAR_SALA":
            self.estado[cambio.indice] = cambio.valor_anterior
        elif tipo == "OBSERVAR_PUERTA":
            self.puertas[cambio.indice] = cambio.valor_anterior
        else:
            raise ValueError(f"Cambio de conocimiento desconocido: {tipo!r}")
        self.version_conocimiento += 1

    # --- partida guardada (FR-220, FR-221) ---

    def exportar(self) -> ConocimientoGuardadoDTO:
        """Lo que se guarda: las exploradas en orden de descubrimiento, las avistadas ascendentes y las puertas observadas
        ascendentes por (sala, dirección). Lo desconocido y lo sin observar no se guarda; tampoco la versión ni los contadores."""
        avistadas = []
        for sala in range(self.mapa.tamano):
            if self.estado[sala] == AVISTADA:
                avistadas.append(sala)
        puertas = []
        for posicion in range(4 * self.mapa.tamano):
            if self.puertas[posicion] != SIN_OBSERVAR:
                puertas.append(PuertaRecordadaDTO(posicion // 4, posicion % 4, self.puertas[posicion] == CERRADA))
        return ConocimientoGuardadoDTO(list(self.exploradas), avistadas, puertas)

    @staticmethod
    def validar(dto, mapa, sala_jugador: int) -> None:
        """Comprueba V1 a V5 de contracts/estado-guardado-niebla.md §3 sin modificar nada. `ValueError` si es incoherente."""
        def invalido(motivo):
            return ValueError(f"conocimiento inválido: {motivo}")

        if not isinstance(dto, ConocimientoGuardadoDTO):
            raise invalido("falta en el estado guardado")
        tamano = mapa.tamano

        def sala_valida(sala):
            return isinstance(sala, int) and not isinstance(sala, bool) and 0 < sala < tamano and mapa.existe[sala]

        marca = [0] * tamano                                     # 1 explorada, 2 avistada
        for sala in dto.exploradas:                              # V1 y V2
            if not sala_valida(sala):
                raise invalido(f"la sala explorada {sala!r} no existe en el esqueleto")
            if marca[sala] != 0:
                raise invalido(f"la sala {sala} está repetida entre las exploradas")
            marca[sala] = 1
        for sala in dto.avistadas:
            if not sala_valida(sala):
                raise invalido(f"la sala avistada {sala!r} no existe en el esqueleto")
            if marca[sala] == 1:
                raise invalido(f"la sala {sala} figura explorada y avistada")
            if marca[sala] == 2:
                raise invalido(f"la sala {sala} está repetida entre las avistadas")
            marca[sala] = 2
        derivada = [False] * tamano                              # V3: avistada si y solo si no explorada y destino de una explorada
        for sala in dto.exploradas:
            for arista in mapa.salidas(sala):
                destino = arista.destino
                if 0 <= destino < tamano and mapa.existe[destino] and marca[destino] != 1:
                    derivada[destino] = True
        for sala in range(tamano):
            if (marca[sala] == 2) != derivada[sala]:
                raise invalido(f"las avistadas no coinciden con las salidas de las exploradas (sala {sala})")
        if not sala_valida(sala_jugador) or marca[sala_jugador] != 1:      # V4
            raise invalido("la sala del jugador no está explorada")
        vistas = [False] * (4 * tamano)                          # V5
        for puerta in dto.puertas:
            bien_formada = (isinstance(puerta, PuertaRecordadaDTO) and sala_valida(puerta.sala)
                            and isinstance(puerta.direccion, int) and not isinstance(puerta.direccion, bool)
                            and 0 <= puerta.direccion <= 3 and isinstance(puerta.cerrada, bool))
            if not bien_formada:
                raise invalido(f"puerta mal formada: {puerta!r}")
            existe = False
            for arista in mapa.salidas(puerta.sala):
                if MapaConocido.indice_direccion(arista.direccion) == puerta.direccion:
                    existe = True
            if not existe:
                raise invalido(f"la sala {puerta.sala} no tiene una salida en la dirección {puerta.direccion}")
            posicion = puerta.sala * 4 + puerta.direccion
            if vistas[posicion]:
                raise invalido(f"la puerta ({puerta.sala}, {puerta.direccion}) está repetida")
            vistas[posicion] = True

    def restaurar(self, dto) -> None:
        """Carga el conocimiento guardado, tras validarlo; si es incoherente no cambia nada. El historial del pergamino
        empieza vacío, así que lo restaurado no se puede deshacer (FR-215)."""
        self.validar(dto, self.mapa, self.jugador.id_sala_actual)
        self.estado = [DESCONOCIDA] * self.mapa.tamano
        self.puertas = [SIN_OBSERVAR] * (4 * self.mapa.tamano)
        self.exploradas = list(dto.exploradas)
        for sala in dto.exploradas:
            self.estado[sala] = EXPLORADA
        for sala in dto.avistadas:
            self.estado[sala] = AVISTADA
        for puerta in dto.puertas:
            self.puertas[puerta.sala * 4 + puerta.direccion] = CERRADA if puerta.cerrada else ABIERTA
        self.version_conocimiento = 0
        self.salas_reveladas = 0
        self.salidas_examinadas = 0

    # --- lo que ve la vista (FR-216, FR-217, FR-219) ---

    def exploradas_en_orden(self) -> list:
        """Ids de las exploradas en orden ascendente, con el ordenamiento propio del repositorio (sobre una copia)."""
        return ordenar_adaptativo(self.exploradas)

    def instantanea(self) -> MapaConocidoDTO:
        salas = [self._sala_conocida(i) for i in self.exploradas_en_orden()]
        return MapaConocidoDTO(self.jugador.id_sala_actual, salas)

    def sala_conocida(self, sala: int) -> SalaConocidaDTO:
        """La sala `sala` (debe estar explorada) en el formato de la vista."""
        if self.estado[sala] != EXPLORADA:
            raise ValueError(f"La sala {sala!r} no está explorada")
        return self._sala_conocida(sala)

    def _sala_conocida(self, sala: int) -> SalaConocidaDTO:
        salidas = []
        for arista in self.mapa.salidas(sala):
            destino = arista.destino
            valido = 0 <= destino < self.mapa.tamano and self.mapa.existe[destino]
            explorado = valido and self.estado[destino] == EXPLORADA
            puerta = _TEXTO_PUERTA[self.puertas[sala * 4 + self.indice_direccion(arista.direccion)]]
            if explorado:
                salidas.append(SalidaConocidaDTO(arista.direccion, arista.costo, puerta, True, destino, self.nombres[destino]))
            else:
                salidas.append(SalidaConocidaDTO(arista.direccion, arista.costo, puerta, False, None, ""))
        return SalaConocidaDTO(sala, self.nombres[sala], salidas)


class VistaMapaConocido:
    """Vista del conocimiento para `BuscadorRutas` (contrato de la futura 006, contracts/vista-buscador.md): solo salas
    exploradas y salidas recordadas como abiertas. Consulta los arreglos sin copiar nada; siempre está vigente."""

    def __init__(self, conocimiento: MapaConocido) -> None:
        self.conocimiento = conocimiento

    @property
    def tamano(self) -> int:
        return self.conocimiento.mapa.tamano

    @property
    def version_conocimiento(self) -> int:
        return self.conocimiento.version_conocimiento

    def salidas(self, sala: int) -> list:
        c = self.conocimiento
        if 0 <= sala < c.mapa.tamano and c.estado[sala] == EXPLORADA:
            return c.mapa.salidas(sala)
        return c.mapa.salidas(-1)                        # lista vacía

    def entrantes(self, sala: int) -> list:
        c = self.conocimiento
        if 0 <= sala < c.mapa.tamano and c.estado[sala] == EXPLORADA:
            return c.mapa.entrantes(sala)
        return c.mapa.entrantes(-1)

    def transitable(self, arista) -> bool:
        c = self.conocimiento
        destino = arista.destino
        if not 0 <= destino < c.mapa.tamano:
            return False
        if c.estado[arista.origen] != EXPLORADA or c.estado[destino] != EXPLORADA:
            return False
        return c.puertas[arista.origen * 4 + c.indice_direccion(arista.direccion)] == ABIERTA
