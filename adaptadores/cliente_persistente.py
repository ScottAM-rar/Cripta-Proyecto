from __future__ import annotations
 
from adaptadores.Interfaz import ClienteInterfaz
 
 
class ClientePersistente(ClienteInterfaz):
 
    def __init__(self, cliente, almacen) -> None:
        self.cliente = cliente          # el cliente de red (ClienteCripta)
        self.almacen = almacen          # AlmacenDisco
        self._catalogo_validado = False
        self._version_catalogo: str | None = None   # se pide una sola vez por sesión
        self._datos_de_la_sesion: list[tuple[str, dict]] = []   # (cripta_id, datos)
 
    @property
    def solicitudes_realizadas(self) -> int:
        """Solicitudes HTTP reales (las que cuentan para el presupuesto)."""
        return self.cliente.solicitudes_realizadas
 
    # ------------------------------------------------------------------
    # Criptas
    # ------------------------------------------------------------------
    def obtener_criptas(self) -> list[dict]:
        criptas = self.cliente.obtener_criptas()
        self.almacen.guardar_criptas(criptas)
        return criptas
 
    def obtener_datos_generales(self, cripta_id: str) -> dict:
        """Siempre va a la red (una vez por sesión): trae la versión actual."""
        for id_guardado, datos in self._datos_de_la_sesion:
            if id_guardado == cripta_id:
                return datos
 
        datos = self.cliente.obtener_datos_generales(cripta_id)
        version = datos.get("version")
        if version is None:
            version = self.cliente.obtener_version_cripta(cripta_id)
 
        vigente = self.almacen.validar_cripta(cripta_id, version)
        if not vigente or self.almacen.leer_datos(cripta_id) is None:
            self.almacen.guardar_datos(cripta_id, datos)
 
        self._datos_de_la_sesion.append((cripta_id, datos))
        return datos
 
    def obtener_version_cripta(self, cripta_id: str) -> str:
        return self.cliente.obtener_version_cripta(cripta_id)
 
    def _asegurar_cripta(self, cripta_id: str) -> None:
        """Comprueba (una vez por sesión) que lo guardado de esta cripta sirve."""
        self.obtener_datos_generales(cripta_id)
 
    def obtener_salas(self, cripta_id: str) -> list[dict]:
        self._asegurar_cripta(cripta_id)
        salas = self.almacen.leer_salas(cripta_id)
        if salas is None:
            salas = self.cliente.obtener_salas(cripta_id)
            self.almacen.guardar_salas(cripta_id, salas)
        return salas
 
    def obtener_contenido(self, cripta_id: str, salas: list[int]) -> list[dict]:
        """Devuelve el contenido en el mismo orden que `salas`.
        Solo se piden a la red las salas que no están en disco."""
        self._asegurar_cripta(cripta_id)
 
        guardados: list[dict | None] = []
        faltantes: list[int] = []
        for numero in salas:
            contenido = self.almacen.leer_contenido(cripta_id, numero)
            guardados.append(contenido)
            if contenido is None:
                faltantes.append(numero)
 
        if not faltantes:
            return guardados
 
        nuevos = self.cliente.obtener_contenido(cripta_id, faltantes)
        if len(nuevos) != len(faltantes):
            raise ValueError(
                f"Se pidieron {len(faltantes)} salas y la API devolvió {len(nuevos)}"
            )
        self.almacen.guardar_contenido(cripta_id, faltantes, nuevos)
 
        resultado: list[dict] = []
        siguiente = 0
        for contenido in guardados:
            if contenido is None:
                resultado.append(nuevos[siguiente])
                siguiente += 1
            else:
                resultado.append(contenido)
        return resultado
 
    # ------------------------------------------------------------------
    # Catálogo
    # ------------------------------------------------------------------
    def obtener_version_catalogo(self) -> str:
        if self._version_catalogo is None:
            self._version_catalogo = self.cliente.obtener_version_catalogo()
        return self._version_catalogo
 
    def _asegurar_catalogo(self) -> None:
        if not self._catalogo_validado:
            version = self.obtener_version_catalogo()
            self.almacen.validar_catalogo(version)
            self._catalogo_validado = True
 
    def obtener_catalogo(self, ids: list[str]) -> list[dict]:
        """Devuelve las fichas en el mismo orden que `ids`.
        Solo se piden a la red las que no están en disco."""
        self._asegurar_catalogo()
 
        guardadas: list[dict | None] = []
        faltantes: list[str] = []
        for id_catalogo in ids:
            ficha = self.almacen.leer_ficha(id_catalogo)
            guardadas.append(ficha)
            if ficha is None:
                faltantes.append(id_catalogo)
 
        nuevas: list[dict] = []
        if faltantes:
            nuevas = self.cliente.obtener_catalogo(faltantes)
            self.almacen.guardar_fichas(nuevas)
 
        resultado: list[dict] = []
        posicion = 0
        for id_catalogo in ids:
            ficha = guardadas[posicion]
            posicion += 1
            if ficha is None:
                for candidata in nuevas:
                    if candidata["id"] == id_catalogo:
                        ficha = candidata
            if ficha is not None:
                resultado.append(ficha)
        return resultado