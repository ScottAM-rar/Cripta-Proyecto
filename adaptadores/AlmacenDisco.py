from __future__ import annotations
import os

from adaptadores.Archivo_indexado import ArchivoIndexado, ErrorArchivo

_VERSION =  "version"
_CARACTERES_PROHIBIDOS = '/\\:*?"<>|'

class AlmacenDisco:

    def __init__(self, carpeta: str = "datos_cripta") -> None:
        self.carpeta = carpeta

    #---- PRIVADOS ---------------
    def _archivo(self, nombre: str) -> ArchivoIndexado:
        return ArchivoIndexado(os.path.join(self.carpeta, nombre + ".bin"))

    @staticmethod
    def _cripta_segura(cripta_id: str) -> str:
        """El id va a formar parte del nombre de un archivo: no puede traer rutas."""
        if not cripta_id or ".." in cripta_id:
            raise ValueError(f"Id de cripta no válido: {cripta_id!r}")
        for caracter in cripta_id:
            if caracter in _CARACTERES_PROHIBIDOS:
                raise ValueError(f"Id de cripta no válido: {cripta_id!r}")
        return cripta_id

    def _archivo_cripta(self, cripta_id: str) -> ArchivoIndexado:
        return self._archivo("cripta_" + self._cripta_segura(cripta_id))

    @staticmethod
    def _validar(archivo: ArchivoIndexado, version_actual: str) -> bool:
        try:
            guardada = archivo.leer(_VERSION)
        except ErrorArchivo:
            guardada = None            # archivo dañado: se trata como si no sirviera
        if guardada is not None and guardada == version_actual:
            return True
        archivo.vaciar()
        archivo.escribir(_VERSION, version_actual)
        return False

    #------ LISTA DE CRIPTAS -------------
    def guardar_criptas(self, criptas: list[dict]) -> None:
        self._archivo("criptas").escribir("lista", criptas)
 
    def leer_criptas(self) -> list[dict] | None:
        return self._archivo("criptas").leer("lista")

    #------- CATALOGO ----------------
    def validar_catalogo(self, version_actual: str) -> bool:
        """True si lo guardado corresponde a esta versión. Si no, lo vacía."""
        return self._validar(self._archivo("catalogo"), version_actual)
 
    def version_catalogo(self) -> str | None:
        return self._archivo("catalogo").leer(_VERSION)
 
    def guardar_fichas(self, fichas: list[dict]) -> None:
        pares = []
        for ficha in fichas:
            pares.append(("ficha:" + ficha["id"], ficha))
        self._archivo("catalogo").escribir_varios(pares)
 
    def leer_ficha(self, id_catalogo: str) -> dict | None:
        return self._archivo("catalogo").leer("ficha:" + id_catalogo)

    #-------- CRIPTAS ---------------
    def validar_cripta(self, cripta_id: str, version_actual: str) -> bool:
        return self._validar(self._archivo_cripta(cripta_id), version_actual)
 
    def version_cripta(self, cripta_id: str) -> str | None:
        return self._archivo_cripta(cripta_id).leer(_VERSION)
 
    def guardar_datos(self, cripta_id: str, datos: dict) -> None:
        self._archivo_cripta(cripta_id).escribir("datos", datos)
 
    def leer_datos(self, cripta_id: str) -> dict | None:
        return self._archivo_cripta(cripta_id).leer("datos")
 
    def guardar_salas(self, cripta_id: str, salas: list[dict]) -> None:
        self._archivo_cripta(cripta_id).escribir("salas", salas)
 
    def leer_salas(self, cripta_id: str) -> list[dict] | None:
        return self._archivo_cripta(cripta_id).leer("salas")
 
    def guardar_contenido(self, cripta_id: str, numeros: list[int], contenidos: list[dict]) -> None:
        """Guarda el contenido de varias salas. contenidos[i] es el de numeros[i]."""
        if len(numeros) != len(contenidos):
            raise ValueError("Hay que dar un contenido por cada número de sala")
        pares = []
        posicion = 0
        for numero in numeros:
            pares.append((f"contenido:{numero}", contenidos[posicion]))
            posicion += 1
        self._archivo_cripta(cripta_id).escribir_varios(pares)
 
    def leer_contenido(self, cripta_id: str, numero_sala: int) -> dict | None:
        return self._archivo_cripta(cripta_id).leer(f"contenido:{numero_sala}")
 
    def cripta_completa(self, cripta_id: str, numeros_salas: list[int]) -> bool:
        """True si hay en disco todo lo necesario para jugar esa cripta sin red."""
        archivo = self._archivo_cripta(cripta_id)
        claves = archivo.claves()
        if "datos" not in claves or "salas" not in claves:
            return False
        for numero in numeros_salas:
            if f"contenido:{numero}" not in claves:
                return False
        return True