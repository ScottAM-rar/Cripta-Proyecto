from __future__ import annotations
from collections import deque
from dataclasses import dataclass
 
from DTO.ActorDTO import JugadorDTO
from DTO.MapaDTO import AristaMapaDTO, MapaDTO, SalaMapaDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from adaptadores.cliente_offline import ErrorOffline
from adaptadores.resolucion import resolver_botin, resolver_sala, resolver_salas
 
 
def _nombre_direccion(letra: str) -> str:
    """Traduce la letra que usa la API al nombre que usa el motor (Direccion)."""
    match letra:
        case "N":
            return "norte"
        case "S":
            return "sur"
        case "E":
            return "este"
        case "O":
            return "oeste"
        case _:
            raise ValueError(f"Dirección desconocida en la API: {letra!r}")
 
 
# Orden fijo en el que se agregan las salidas a la sala
_LETRAS_EN_ORDEN = ("N", "S", "E", "O")

COSTO_POR_DEFECTO = 100


def _costo_valido(valor) -> bool:
    """FR-101: entero >= 1 (un booleano no cuenta como entero)."""
    return isinstance(valor, int) and not isinstance(valor, bool) and valor >= 1


def _agregar_advertencia(advertencias: list[str], texto: str) -> None:
    if texto not in advertencias:
        advertencias.append(texto)


def _costo_declarado(salida: dict, advertencias: list[str] | None, sala: int, letra: str) -> int | None:
    """Costo declarado por una salida, o None si no declara ninguno. Un costo inválido (cero, negativo, no entero)
    cuenta como no declarado y, si `advertencias` no es None, deja una advertencia (FR-101)."""
    if "costo" not in salida:
        return None
    valor = salida["costo"]
    if _costo_valido(valor):
        return valor
    if advertencias is not None:
        _agregar_advertencia(advertencias, f"Sala {sala}, salida {letra}: costo inválido {valor!r}; se usa {COSTO_POR_DEFECTO}")
    return None


def _salida_de_vuelta(por_id: list, origen: int, destino: int) -> tuple | None:
    """(letra, salida) de la sala `destino` que lleva de vuelta a `origen`, o None si la conexión es de un solo sentido
    (FR-124). Si hubiera varias, la primera en el orden N, S, E, O."""
    if destino < 0 or destino >= len(por_id) or por_id[destino] is None:
        return None
    salidas = por_id[destino].get("salidas") or {}
    for letra in _LETRAS_EN_ORDEN:
        if letra in salidas and salidas[letra]["sala"] == origen:
            return letra, salidas[letra]
    return None


def normalizar_esqueleto(salas: list[dict], advertencias: list[str]) -> list[dict]:
    """Copia del esqueleto con el campo "costo" resuelto en TODAS las salidas (FR-101, FR-102, FR-124).

    - Sin costo declarado: 100. Costo inválido: cuenta como no declarado y deja una advertencia.
    - Si una sola de las dos salidas de la conexión declara costo, ese vale para ambos sentidos.
    - Si las dos declaran costos distintos, vale el de la sala de menor id y se advierte (una vez por conexión).
    - Una conexión de un solo sentido usa el costo de su única salida.
    No usa ningún índice por diccionario: el acceso por id va en una lista de posición = id."""
    mayor = 0
    for sala in salas:
        if sala["id"] > mayor:
            mayor = sala["id"]
    por_id: list = [None] * (mayor + 1)
    for sala in salas:
        por_id[sala["id"]] = sala

    resultado: list[dict] = []
    for sala in salas:
        origen = sala["id"]
        nueva = dict(sala)
        salidas_api = sala.get("salidas")
        if salidas_api is not None:
            salidas_nuevas = {}
            for letra in _LETRAS_EN_ORDEN:
                if letra not in salidas_api:
                    continue
                salida = salidas_api[letra]
                destino = salida["sala"]
                propio = _costo_declarado(salida, advertencias, origen, letra)
                vuelta = _salida_de_vuelta(por_id, origen, destino)
                ajeno = None if vuelta is None else _costo_declarado(vuelta[1], None, destino, vuelta[0])
                if propio is None and ajeno is None:
                    costo = COSTO_POR_DEFECTO
                elif ajeno is None:
                    costo = propio
                elif propio is None:
                    costo = ajeno
                elif propio == ajeno:
                    costo = propio
                else:
                    costo = propio if origen < destino else ajeno       # gana la declaración de la sala de menor id
                    if origen < destino:
                        _agregar_advertencia(advertencias, f"Conexión entre las salas {origen} y {destino}: costos distintos "
                                                           f"({propio} y {ajeno}); vale el de la sala {origen}")
                copia = dict(salida)
                copia["costo"] = costo
                salidas_nuevas[letra] = copia
            nueva["salidas"] = salidas_nuevas
        resultado.append(nueva)
    return resultado
 
 
@dataclass
class ReporteSolicitudes:
    """Resumen para mostrar al terminar la partida."""
    solicitudes: int
    presupuesto: int
    aciertos_cache: int
    fallos_cache: int

    @property
    def restante(self) -> int:
        return self.presupuesto - self.solicitudes

    @property
    def dentro_del_presupuesto(self) -> bool:
        return self.solicitudes <= self.presupuesto

    def texto(self) -> str:
        estado = "dentro del presupuesto" if self.dentro_del_presupuesto else "EXCEDIDO"
        return (f"Solicitudes a la API: {self.solicitudes} de {self.presupuesto} ({estado})\n"
                f"Caché de fichas: {self.aciertos_cache} aciertos, {self.fallos_cache} fallos")


class ServicioCripta:
    """Punto único por el que el resto del juego obtiene criptas y salas.
 
    Recibe el cliente (online u offline) y la caché por el constructor, así
    quien la use no sabe de dónde salen los datos.
    """
 
    def __init__(self, cliente, cache) -> None:
        self.cliente = cliente
        self.cache = cache
        self._criptas: list[dict] | None = None      # lista de /criptas ya pedida
        self._esqueleto_id: str | None = None        # cripta a la que pertenece el esqueleto
        self._esqueleto: list[dict] = []             # salas de /salas con el costo de cada salida ya resuelto
        self.advertencias: list[str] = []            # datos inválidos que se corrigieron al leer (costos, rangos)
        self._datos_id: str | None = None            # cripta a la que pertenecen los datos generales
        self._datos: dict | None = None              # respuesta cruda de /criptas/{id}
        self._listas_id: str | None = None           # cripta a la que pertenecen las salas ya precargadas
        self._listas: list[int] = []                 # salas ya traídas (y guardadas) en esta sesión
 
    # ------------------------------------------------------------------
    # Criptas
    # ------------------------------------------------------------------
    def _cargar_criptas(self) -> list[dict]:
        if self._criptas is None:
            self._criptas = self.cliente.obtener_criptas()
        return self._criptas
 
    def listar_criptas(self) -> list[str]:
        """Ej: ['Cripta 1: Osario menor']."""
        textos: list[str] = []
        posicion = 1
        for cripta in self._cargar_criptas():
            textos.append(f"Cripta {posicion}: {cripta.get('nombre', cripta['id'])}")
            posicion += 1
        return textos
 
    def obtener_id_cripta(self, posicion: int) -> str:
        """posicion empieza en 1, como se muestra en listar_criptas()."""
        criptas = self._cargar_criptas()
        if posicion < 1 or posicion > len(criptas):
            raise ValueError(f"No existe la cripta número {posicion}")
        return criptas[posicion - 1]["id"]
 
    def existe_cripta(self, cripta_id: str) -> bool:
        for cripta in self._cargar_criptas():
            if cripta["id"] == cripta_id:
                return True
        return False
 
    def datos_cripta(self, cripta_id: str) -> dict:
        """Datos generales de la cripta (sala_inicial, sala_salida, llave_salida,
        inventario_max, jugador, ...). Se piden una sola vez por cripta."""
        if not self.existe_cripta(cripta_id):
            raise ValueError(f"La cripta '{cripta_id}' no existe")
        if self._datos_id != cripta_id:
            self._datos = self.cliente.obtener_datos_generales(cripta_id)
            self._datos_id = cripta_id
        return self._datos
 
    def crear_jugador(self, cripta_id: str) -> JugadorDTO:
        """Arma el jugador con las estadísticas que define la cripta."""
        datos = self.datos_cripta(cripta_id)
        stats = datos["jugador"]
        return JugadorDTO(
            vida_actual=stats["vida_max"],      # empieza con la vida completa
            vida_max=stats["vida_max"],
            ataque=stats["ataque"],
            defensa=stats["defensa"],
            velocidad=stats["velocidad"],
            inventario_max=datos["inventario_max"],
            id_sala_actual=datos["sala_inicial"],
        )
 
    def obtener_sala_salida(self, cripta_id: str) -> int:
        """Id de la sala donde se gana la partida (la que tiene la salida).
        Sale de los datos generales, que ya se piden una sola vez por cripta."""
        return self.datos_cripta(cripta_id)["sala_salida"]

    def presupuesto_solicitudes(self, cripta_id: str) -> int:
        """Cuántas solicitudes permite la API para jugar esta cripta."""
        return self.datos_cripta(cripta_id)["presupuesto_solicitudes"]

    @property
    def solicitudes_realizadas(self) -> int:
        """Solicitudes de red hechas hasta ahora (0 en modo offline)."""
        return self.cliente.solicitudes_realizadas

    # ------------------------------------------------------------------
    # Salas
    # ------------------------------------------------------------------
    def _cargar_esqueleto(self, cripta_id: str) -> list[dict]:
        if not self.existe_cripta(cripta_id):
            raise ValueError(f"La cripta '{cripta_id}' no existe")
        if self._esqueleto_id != cripta_id:
            self._esqueleto = normalizar_esqueleto(self.cliente.obtener_salas(cripta_id), self.advertencias)
            self._esqueleto_id = cripta_id
        return self._esqueleto
 
    def total_salas(self, cripta_id: str) -> int:
        return len(self._cargar_esqueleto(cripta_id))

    def obtener_mapa(self, cripta_id: str) -> MapaDTO:
        """Esqueleto completo con el costo de cada salida y el estado inicial de las puertas. Sale del esqueleto que
        ya se descarga al iniciar: no gasta solicitudes ni depende de qué salas tengan contenido traído."""
        esqueleto = self._cargar_esqueleto(cripta_id)
        mayor = 0
        for sala in esqueleto:
            if sala["id"] > mayor:
                mayor = sala["id"]
        salas: list = [None] * (mayor + 1)
        for sala in esqueleto:
            aristas: list[AristaMapaDTO] = []
            salidas_api = sala.get("salidas") or {}
            for letra in _LETRAS_EN_ORDEN:
                if letra in salidas_api:
                    datos = salidas_api[letra]
                    aristas.append(AristaMapaDTO(_nombre_direccion(letra), datos["sala"], datos["costo"],
                                                 datos.get("cerrada", False)))
            salas[sala["id"]] = SalaMapaDTO(sala["id"], aristas)
        return MapaDTO(salas, list(self.advertencias))
 
    def construir_sala(self, cripta_id: str, numero_sala: int) -> SalaDTO:
        """Arma una SalaDTO completa: esqueleto (nombre y salidas) + contenido."""
        esqueleto = self._buscar_esqueleto(cripta_id, numero_sala)
        contenido = resolver_sala(self.cliente, self.cache, cripta_id, numero_sala, self.advertencias)
        return self._ensamblar(esqueleto, contenido)
 
    def construir_salas(self, cripta_id: str, numeros: list[int]) -> list[SalaDTO]:
        """Arma varias SalaDTO pidiendo todo el contenido en lote."""
        esqueletos = [self._buscar_esqueleto(cripta_id, n) for n in numeros]
        contenidos = resolver_salas(self.cliente, self.cache, cripta_id, numeros, self.advertencias)
        salas: list[SalaDTO] = []
        posicion = 0
        for esqueleto in esqueletos:
            salas.append(self._ensamblar(esqueleto, contenidos[posicion]))
            posicion += 1
        return salas
 
    def construir_todas(self, cripta_id: str) -> list[SalaDTO]:
        """Todas las salas de la cripta, en el mínimo de solicitudes."""
        numeros = [sala["id"] for sala in self._cargar_esqueleto(cripta_id)]
        return self.construir_salas(cripta_id, numeros)
 
    def objetos_que_suelta(self, enemigo) -> list:
        """Lo que suelta `enemigo` al morir (§2.6): una instancia NUEVA de cada objeto de su campo `suelta`,
        con la sala del enemigo, lista para ponerla en el suelo. Un id repetido da instancias separadas y sin
        `suelta` devuelve []. Las fichas ya se trajeron junto con la sala del enemigo, así que normalmente sale
        de la caché o del disco sin gastar solicitudes; si alguna faltara se piden juntas, en un solo lote."""
        return resolver_botin(self.cliente, self.cache, enemigo.suelta, enemigo.id_sala_actual)

    def precargar(self, cripta_id: str, numeros: list[int] | None = None) -> int:
        """Trae de una vez, en lotes, el contenido y las fichas de las salas
        (todas si no se indican). Así luego construir_sala() sale del disco
        sin gastar solicitudes. Devuelve cuántas salas se precargaron.

        Sin `numeros` trae TODA la cripta: solo para pruebas y laboratorios; en el
        juego se usa precargar_vecinas()."""
        if numeros is None:
            salas = self.construir_todas(cripta_id)
        else:
            salas = self.construir_salas(cripta_id, numeros)
        self._marcar_listas(cripta_id, [sala.id for sala in salas])
        return len(salas)

    def _marcar_listas(self, cripta_id: str, numeros: list[int]) -> None:
        if self._listas_id != cripta_id:
            self._listas_id = cripta_id
            self._listas = []
        for numero in numeros:
            if numero not in self._listas:
                self._listas.append(numero)

    def _estan_listas(self, cripta_id: str, numeros: list[int]) -> bool:
        if self._listas_id != cripta_id:
            return False
        for numero in numeros:
            if numero not in self._listas:
                return False
        return True

    def salas_vecinas(self, cripta_id: str, numero_sala: int, profundidad: int = 1) -> list[int]:
        """Ids de las salas a las que se llega desde numero_sala por sus salidas
        (aunque la puerta esté cerrada), sin repetir y sin incluir la propia.
        profundidad=1: las contiguas; 2: también las contiguas de esas; etc."""
        if profundidad < 0:
            raise ValueError("La profundidad no puede ser negativa")
        self._buscar_esqueleto(cripta_id, numero_sala)       # valida que exista
        alcanzadas: list[int] = [numero_sala]
        pendientes: deque = deque([(numero_sala, 0)])         # (sala, nivel)
        while pendientes:
            actual, nivel = pendientes.popleft()
            if nivel >= profundidad:
                continue
            salidas = self._buscar_esqueleto(cripta_id, actual).get("salidas") or {}
            for letra in _LETRAS_EN_ORDEN:
                if letra in salidas:
                    destino = salidas[letra]["sala"]
                    if destino not in alcanzadas:
                        alcanzadas.append(destino)
                        pendientes.append((destino, nivel + 1))
        return alcanzadas[1:]

    def precargar_vecinas(self, cripta_id: str, sala_actual: int, profundidad: int | None = None,
                          max_salas: int = 10) -> int:
        """Precarga por vecindad, pensada para gastar pocas solicitudes.

        Garantía (§4.2): al terminar, la sala actual y todas las que se alcanzan en
        UN movimiento ya están traídas, así que entrar a cualquiera no espera a la red.

        Ahorro: si esa garantía ya se cumple devuelve 0 sin hacer nada. Solo cuando
        falta alguna, trae un lote que se llena con las salas faltantes más cercanas
        (hasta `max_salas`; 10 es lo que cabe en una solicitud de contenido). Así una
        tanda de solicitudes cubre varios pasos del jugador en vez de una por sala.
        Nunca trae toda la cripta de una vez. `profundidad` limita hasta cuántos pasos
        se mira al llenar el lote; con None (lo normal) no hay otro límite que max_salas.

        Devuelve cuántas salas se trajeron en esta llamada."""
        if max_salas < 1:
            raise ValueError("max_salas debe ser al menos 1")
        if profundidad is not None and profundidad < 1:
            raise ValueError("La profundidad debe ser al menos 1")
        self._buscar_esqueleto(cripta_id, sala_actual)            # valida que exista
        alcance = profundidad if profundidad is not None else len(self._cargar_esqueleto(cripta_id))

        inmediatas = [sala_actual] + self.salas_vecinas(cripta_id, sala_actual, 1)
        if self._estan_listas(cripta_id, inmediatas):
            return 0

        indispensables: list[int] = []
        for numero in inmediatas:
            if not self._estan_listas(cripta_id, [numero]):
                indispensables.append(numero)

        lote = list(indispensables)
        limite = max(max_salas, len(indispensables))
        for numero in self.salas_vecinas(cripta_id, sala_actual, alcance):       # de la más cercana a la más lejana
            if len(lote) >= limite:
                break
            if numero not in lote and not self._estan_listas(cripta_id, [numero]):
                lote.append(numero)
        return self.precargar(cripta_id, lote)

    def version_cripta(self, cripta_id: str) -> str | None:
        """Versión de la cripta (para el encabezado del log, el guardado y la tabla de puntajes).
        Sale de los datos generales ya pedidos: no cuesta solicitudes extra. Devuelve None
        si la fuente no la conoce (p. ej. offline sin versión guardada)."""
        version = self.datos_cripta(cripta_id).get("version")
        if version is None:
            try:
                version = self.cliente.obtener_version_cripta(cripta_id)
            except ErrorOffline:
                version = None
        return version

    def version_catalogo(self) -> str | None:
        """Versión del catálogo (para el encabezado del log y el guardado). Si ya se validó
        en esta sesión no cuesta solicitudes extra. Devuelve None si la fuente no la conoce
        (p. ej. offline sin catálogo guardado)."""
        try:
            return self.cliente.obtener_version_catalogo()
        except ErrorOffline:
            return None

    def retener_fichas(self, ids_catalogo: list[str]) -> None:
        """Marca fichas como EN USO (§4.4): la caché no las libera mientras alguien
        las use. Llamar una vez por cada instancia activa que las referencia."""
        for id_catalogo in ids_catalogo:
            self.cache.marcar_en_uso(id_catalogo)

    def liberar_fichas(self, ids_catalogo: list[str]) -> None:
        """Quita una referencia de uso (el enemigo murió, se recogió, se salió de la sala...)."""
        for id_catalogo in ids_catalogo:
            self.cache.marcar_libre(id_catalogo)

    def fijar_fichas_en_uso(self, ids_catalogo: list[str]) -> None:
        """El modelo informa qué fichas referencian sus instancias activas (un id por instancia).
        La caché no desaloja ninguna mientras siga en esta lista."""
        self.cache.establecer_en_uso(ids_catalogo)

    def reporte(self, cripta_id: str) -> ReporteSolicitudes:
        """Solicitudes hechas contra el presupuesto de la cripta, y aciertos y
        fallos de la caché. Para mostrar al final de la partida."""
        return ReporteSolicitudes(
            solicitudes=self.solicitudes_realizadas,
            presupuesto=self.presupuesto_solicitudes(cripta_id),
            aciertos_cache=self.cache.aciertos,
            fallos_cache=self.cache.fallos,
        )

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _buscar_esqueleto(self, cripta_id: str, numero_sala: int) -> dict:
        for sala in self._cargar_esqueleto(cripta_id):
            if sala["id"] == numero_sala:
                return sala
        raise ValueError(f"La cripta '{cripta_id}' no tiene la sala {numero_sala}")
 
    def _ensamblar(self, esqueleto: dict, contenido) -> SalaDTO:
        enemigos, objetos, trampas = contenido
        sala = SalaDTO(id=esqueleto["id"], nombre=esqueleto["nombre"])
        sala.salidas = self._armar_salidas(esqueleto.get("salidas"))
        sala.enemigos = enemigos
        sala.objetos = objetos      # objetos ya resueltos (Arma, Llave, ...)
        sala.trampas = trampas      # Trampa ya resueltas
        return sala
 
    @staticmethod
    def _armar_salidas(salidas_api: dict | None) -> deque[SalidaDTO]:
        """Convierte el objeto 'salidas' de la API en un deque de SalidaDTO.
 
        Solo se agregan las salidas que existen, en el orden N, S, E, O.
        """
        salidas: deque[SalidaDTO] = deque(maxlen=4)
        if salidas_api is None:          # sala sin salidas
            return salidas
        for letra in _LETRAS_EN_ORDEN:
            if letra in salidas_api:
                datos = salidas_api[letra]
                salidas.append(SalidaDTO(
                    direccion=_nombre_direccion(letra),
                    sala_destino=datos["sala"],
                    cerrada=datos.get("cerrada", False),
                    llave=datos.get("llave"),
                    cierre_automatico=datos.get("cierre_automatico"),
                    costo=datos.get("costo", COSTO_POR_DEFECTO),
                ))
        return salidas