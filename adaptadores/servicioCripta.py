from __future__ import annotations
from collections import deque

from DTO.ActorDTO import JugadorDTO
from DTO.SalaDTO import SalaDTO, SalidaDTO
from adaptadores.resolucion import resolver_sala

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
        self._datos_id: str | None = None
        self._datos: dict = {}

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
        """posicion empieza en 1"""
        criptas = self._cargar_criptas()
        if posicion < 1 or posicion > len(criptas):
            raise ValueError(f"No existe la cripta número {posicion}")
        return criptas[posicion - 1]["id"]

    def existe_cripta(self, cripta_id: str) -> bool:
        for cripta in self._cargar_criptas():
            if cripta["id"] == cripta_id:
                return True
        return False

    #------------------- JUGADOR - datos -----------------

    def datos_cripta(self, cripta_id: str) -> dict:
        if not self.existe_cripta(cripta_id):
            raise ValueError(f"La cripta '{cripta_id}' no existe")
        if self._datos_id != cripta_id:
            self._datos = self.cliente.obtener_datos_generales(cripta_id)
            self._datos_id = cripta_id
        return self._datos

    def crear_jugador(self, cripta_id: str) -> JugadorDTO:
        
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

    # ------------------ SALAS ------------------

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
 
        enemigos, objetos, trampas = resolver_sala(
            self.cliente, self.cache, cripta_id, numero_sala
        )
 
        sala = SalaDTO(id=esqueleto["id"], nombre=esqueleto["nombre"])
        sala.salidas = self._armar_salidas(esqueleto.get("salidas", {}))
        sala.enemigos = enemigos
        sala.objetos = objetos      # objetos ya resueltos (Arma, Llave, ...)
        sala.trampas = trampas      # Trampa ya resueltas
        return sala

    def _buscar_esqueleto(self, cripta_id: str, numero_sala: int) -> dict:
        for sala in self._cargar_esqueleto(cripta_id):
            if sala["id"] == numero_sala:
                return sala
        raise ValueError(f"La cripta '{cripta_id}' no tiene la sala {numero_sala}")

    @staticmethod
    def _armar_salidas(salidas_api: dict) -> deque[SalidaDTO]:
        """Convierte el objeto 'salidas' de la API en un deque de SalidaDTO.
 
        Solo se agregan las salidas que existen, en el orden N, S, E, O.
        """
        salidas: deque[SalidaDTO] = deque(maxlen=4)
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