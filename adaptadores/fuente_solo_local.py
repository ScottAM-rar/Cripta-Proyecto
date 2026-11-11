"""Fuente de datos solo local (capacidad 009, FR-314 a FR-317): la usa la consulta histórica de la capacidad 004.

Envuelve un ServicioCripta armado sobre ClienteOffline (fabrica.crear_fuente_solo_local). Lee únicamente de disco, no
gasta solicitudes y no modifica nada de lo guardado:
- antes de cada operación compara la versión guardada de la cripta con la versión vigente (FR-317);
- ErrorOffline y LlavesNoDisponibles se entregan como DatoLocalFaltante, que nombra el dato y la cripta (FR-315);
- nunca llama a validar_cripta (vaciaría el archivo si la versión no coincide) ni a ningún guardar_*.
"""
from __future__ import annotations

from adaptadores.cliente_offline import ErrorOffline
from Logica.FuenteCripta import DatoLocalFaltante, LlavesNoDisponibles


class FuenteSoloLocal:

    def __init__(self, fuente, almacen, version_vigente: str | None,
                 version_catalogo_vigente: str | None = None) -> None:
        self.fuente = fuente                    # ServicioCripta sobre ClienteOffline
        self.almacen = almacen                  # AlmacenDisco: solo se lee
        self.version_vigente = version_vigente  # None: sirve la versión guardada de cada cripta
        self.version_catalogo_vigente = version_catalogo_vigente   # None: sirve la versión guardada del catálogo
        self._ultima_cripta: str | None = None  # cripta de la última operación que la recibió (objetos_que_suelta)

    # ------------------------------------------------------------------
    # Comprobaciones
    # ------------------------------------------------------------------
    def _exigir_version(self, cripta_id: str) -> None:
        self._ultima_cripta = cripta_id
        guardada = self.almacen.version_cripta(cripta_id)
        if guardada is None:
            necesaria = self.version_vigente if self.version_vigente is not None else "una versión guardada"
            raise DatoLocalFaltante(
                f"La cripta {cripta_id} no tiene versión guardada en disco (guardada: ninguna); se necesita {necesaria}"
            )
        if self.version_vigente is not None and guardada != self.version_vigente:
            raise DatoLocalFaltante(
                f"La cripta {cripta_id} está guardada con la versión {guardada}; se necesita {self.version_vigente}"
            )

    def _leer(self, cripta_id: str, dato: str, operacion):
        """Comprueba la versión y hace la operación; un dato que falta en disco sale como DatoLocalFaltante."""
        self._exigir_version(cripta_id)
        try:
            return operacion()
        except (ErrorOffline, LlavesNoDisponibles) as error:
            raise DatoLocalFaltante(f"Falta en disco {dato} de la cripta {cripta_id}: {error}") from error
        except ValueError as error:
            # Solo el de cripta desconocida del servicio (no está en la lista de criptas guardada); los demás siguen.
            if str(error) != f"La cripta '{cripta_id}' no existe":
                raise
            raise DatoLocalFaltante(f"La cripta {cripta_id} no está en la lista de criptas guardada en disco") from error

    # ------------------------------------------------------------------
    # Operaciones de FuenteCripta que lee la consulta histórica (data-model.md)
    # ------------------------------------------------------------------
    def esqueleto(self, cripta_id: str):
        return self._leer(cripta_id, "el esqueleto", lambda: self.fuente.esqueleto(cripta_id))

    def construir_sala(self, cripta_id: str, numero_sala: int):
        self._exigir_version(cripta_id)
        if self.almacen.leer_contenido(cripta_id, numero_sala) is None:
            raise DatoLocalFaltante(f"Falta en disco sala {numero_sala} de la cripta {cripta_id}")
        return self._leer(cripta_id, f"sala {numero_sala}", lambda: self.fuente.construir_sala(cripta_id, numero_sala))

    def ubicacion_llaves(self, cripta_id: str):
        return self._leer(cripta_id, "las llaves", lambda: self.fuente.ubicacion_llaves(cripta_id))

    def datos_cripta(self, cripta_id: str) -> dict:
        return self._leer(cripta_id, "los datos generales", lambda: self.fuente.datos_cripta(cripta_id))

    def crear_jugador(self, cripta_id: str):
        return self._leer(cripta_id, "los datos del jugador", lambda: self.fuente.crear_jugador(cripta_id))

    def version_cripta(self, cripta_id: str) -> str | None:
        return self._leer(cripta_id, "la versión", lambda: self.fuente.version_cripta(cripta_id))

    def total_salas(self, cripta_id: str) -> int:
        return self._leer(cripta_id, "el esqueleto", lambda: self.fuente.total_salas(cripta_id))

    def precargar_vecinas(self, cripta_id: str, sala_actual: int, profundidad: int | None = None, *args, **kwargs) -> int:
        """La consulta histórica no precarga: no hace nada y devuelve 0."""
        self._exigir_version(cripta_id)
        return 0

    def reporte(self, cripta_id: str):
        """Reporte del servicio interior: 0 solicitudes, porque ClienteOffline nunca usa la red."""
        return self._leer(cripta_id, "los datos generales", lambda: self.fuente.reporte(cripta_id))

    # ------------------------------------------------------------------
    # Operaciones que pide la capacidad 004 (T053)
    # ------------------------------------------------------------------
    def obtener_mapa(self, cripta_id: str):
        """Lo mismo que esqueleto() (el modelo lo pide con este nombre para el campo de costos)."""
        return self.esqueleto(cripta_id)

    def obtener_sala_salida(self, cripta_id: str) -> int:
        return self._leer(cripta_id, "los datos generales", lambda: self.fuente.obtener_sala_salida(cripta_id))

    def obtener_sala_inicial(self, cripta_id: str) -> int:
        """Capacidad 003: sala inicial de los datos generales guardados, sin solicitudes."""
        return self._leer(cripta_id, "los datos generales", lambda: self.fuente.obtener_sala_inicial(cripta_id))

    def obtener_llave_salida(self, cripta_id: str) -> str | None:
        """Capacidad 003: llave de salida de los datos generales guardados, sin solicitudes."""
        return self._leer(cripta_id, "los datos generales", lambda: self.fuente.obtener_llave_salida(cripta_id))

    def existe_cripta(self, cripta_id: str) -> bool:
        """Solo existencia, sin comparar versión: si la cripta está en la lista de criptas guardada. Se lee la lista
        del almacén y no la del servicio, porque el modo sin red descarta las criptas que no están completas."""
        self._ultima_cripta = cripta_id
        criptas = self.almacen.leer_criptas()
        if criptas is None:
            raise DatoLocalFaltante(f"Falta en disco la lista de criptas (se buscaba la cripta {cripta_id})")
        for cripta in criptas:
            if cripta.get("id") == cripta_id:
                return True
        return False

    def version_catalogo(self) -> str:
        guardada = self.almacen.version_catalogo()
        if guardada is None:
            necesaria = (self.version_catalogo_vigente if self.version_catalogo_vigente is not None
                         else "una versión guardada")
            raise DatoLocalFaltante(
                f"El catálogo no tiene versión guardada en disco (guardada: ninguna); se necesita {necesaria}"
            )
        if self.version_catalogo_vigente is not None and guardada != self.version_catalogo_vigente:
            raise DatoLocalFaltante(
                f"El catálogo está guardado con la versión {guardada}; se necesita {self.version_catalogo_vigente}"
            )
        return guardada

    def objetos_que_suelta(self, enemigo) -> list:
        """Recibe el enemigo, no la cripta: comprueba la versión de la última cripta consultada por esta fuente. Una
        ficha que falta en el catálogo guardado sale como DatoLocalFaltante con su id y la cripta."""
        if self._ultima_cripta is None:
            raise DatoLocalFaltante("Todavía no se consultó ninguna cripta: no se sabe contra qué versión comprobar "
                                    "lo que suelta el enemigo")
        cripta_id = self._ultima_cripta
        ids = ", ".join(enemigo.suelta) if enemigo.suelta else "ninguna"
        return self._leer(cripta_id, f"las fichas de lo que suelta {enemigo.id_instancia} ({ids})",
                          lambda: self.fuente.objetos_que_suelta(enemigo))

    def fijar_fichas_en_uso(self, ids_catalogo: list[str]) -> None:
        """Delega en el servicio: solo marca fichas en la caché en memoria; no escribe en disco ni pide nada."""
        self.fuente.fijar_fichas_en_uso(ids_catalogo)
