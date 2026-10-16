from __future__ import annotations
from collections import deque
from dataclasses import dataclass
 
from DTO.ActorDTO import JugadorDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from adaptadores.resolucion import resolver_sala, resolver_salas
 
 
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
        self._esqueleto: list[dict] = []             # salas crudas de /salas
        self._datos_id: str | None = None            # cripta a la que pertenecen los datos generales
        self._datos: dict | None = None              # respuesta cruda de /criptas/{id}
 
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
 
    def version_cripta(self, cripta_id: str) -> str | None:
        return self.datos_cripta(cripta_id).get("version")

    def version_catalogo(self) -> str | None:
        """Versión del catálogo en uso; None si no se puede conocer (p. ej. offline sin catálogo)."""
        try:
            return self.cliente.obtener_version_catalogo()
        except Exception:
            return None

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
            self._esqueleto = self.cliente.obtener_salas(cripta_id)
            self._esqueleto_id = cripta_id
        return self._esqueleto
 
    def total_salas(self, cripta_id: str) -> int:
        return len(self._cargar_esqueleto(cripta_id))
 
    def construir_sala(self, cripta_id: str, numero_sala: int) -> SalaDTO:
        """Arma una SalaDTO completa: esqueleto (nombre y salidas) + contenido."""
        esqueleto = self._buscar_esqueleto(cripta_id, numero_sala)
        contenido = resolver_sala(self.cliente, self.cache, cripta_id, numero_sala)
        return self._ensamblar(esqueleto, contenido)
 
    def construir_salas(self, cripta_id: str, numeros: list[int]) -> list[SalaDTO]:
        """Arma varias SalaDTO pidiendo todo el contenido en lote."""
        esqueletos = [self._buscar_esqueleto(cripta_id, n) for n in numeros]
        contenidos = resolver_salas(self.cliente, self.cache, cripta_id, numeros)
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
 
    def precargar(self, cripta_id: str, numeros: list[int] | None = None) -> int:
        """Trae de una vez, en lotes, el contenido y las fichas de las salas
        (todas si no se indican). Así luego construir_sala() sale del disco
        sin gastar solicitudes. Devuelve cuántas salas se precargaron."""
        if numeros is None:
            salas = self.construir_todas(cripta_id)
        else:
            salas = self.construir_salas(cripta_id, numeros)
        return len(salas)

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

    def precargar_vecinas(self, cripta_id: str, sala_actual: int, profundidad: int = 1) -> int:
        """Precarga la sala actual y sus vecinas en lotes (precarga por vecindad).
        Lo que ya está en disco no se vuelve a pedir. Devuelve cuántas salas
        se procesaron."""
        numeros = [sala_actual] + self.salas_vecinas(cripta_id, sala_actual, profundidad)
        return self.precargar(cripta_id, numeros)

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
                ))
        return salidas