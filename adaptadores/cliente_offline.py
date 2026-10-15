from __future__ import annotations
 
from adaptadores.Interfaz import ClienteInterfaz
 
 
class ErrorOffline(Exception):
    """Falta en disco algo que el modo sin conexión necesita."""
 
 
class ClienteOffline(ClienteInterfaz):
 
    def __init__(self, almacen) -> None:
        self.almacen = almacen
 
    @property
    def solicitudes_realizadas(self) -> int:
        return 0                          # el modo offline nunca usa la red
 
    # ------------------------------------------------------------------
    # Criptas
    # ------------------------------------------------------------------
    def obtener_criptas(self) -> list[dict]:
        """Solo las criptas que se pueden jugar completas sin conexión."""
        guardadas = self.almacen.leer_criptas()
        if guardadas is None:
            raise ErrorOffline(
                "No hay datos guardados. Juega una vez con conexión para poder usar el modo offline."
            )
        jugables: list[dict] = []
        for cripta in guardadas:
            if self.cripta_disponible(cripta["id"]):
                jugables.append(cripta)
        if not jugables:
            raise ErrorOffline(
                "Ninguna cripta está guardada por completo. Juega una vez con conexión."
            )
        return jugables
 
    def cripta_disponible(self, cripta_id: str) -> bool:
        """True si datos, salas y contenido de todas las salas están en disco."""
        salas = self.almacen.leer_salas(cripta_id)
        if salas is None:
            return False
        numeros: list[int] = []
        for sala in salas:
            numeros.append(sala["id"])
        return self.almacen.cripta_completa(cripta_id, numeros)
 
    def obtener_datos_generales(self, cripta_id: str) -> dict:
        datos = self.almacen.leer_datos(cripta_id)
        if datos is None:
            raise ErrorOffline(f"La cripta {cripta_id} no está guardada para jugar sin conexión.")
        return datos
 
    def obtener_version_cripta(self, cripta_id: str) -> str:
        version = self.almacen.version_cripta(cripta_id)
        if version is None:
            raise ErrorOffline(f"No hay versión guardada de la cripta {cripta_id}.")
        return version
 
    def obtener_salas(self, cripta_id: str) -> list[dict]:
        salas = self.almacen.leer_salas(cripta_id)
        if salas is None:
            raise ErrorOffline(f"Las salas de {cripta_id} no están guardadas.")
        return salas
 
    def obtener_contenido(self, cripta_id: str, salas: list[int]) -> list[dict]:
        resultado: list[dict] = []
        for numero in salas:
            contenido = self.almacen.leer_contenido(cripta_id, numero)
            if contenido is None:
                raise ErrorOffline(f"Falta el contenido de la sala {numero} de {cripta_id}.")
            resultado.append(contenido)
        return resultado
 
    # ------------------------------------------------------------------
    # Catálogo
    # ------------------------------------------------------------------
    def obtener_version_catalogo(self) -> str:
        version = self.almacen.version_catalogo()
        if version is None:
            raise ErrorOffline("No hay catálogo guardado.")
        return version
 
    def obtener_catalogo(self, ids: list[str]) -> list[dict]:
        resultado: list[dict] = []
        for id_catalogo in ids:
            ficha = self.almacen.leer_ficha(id_catalogo)
            if ficha is None:
                raise ErrorOffline(f"Falta la ficha {id_catalogo} del catálogo guardado.")
            resultado.append(ficha)
        return resultado