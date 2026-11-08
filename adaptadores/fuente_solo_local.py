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

    def __init__(self, fuente, almacen, version_vigente: str | None) -> None:
        self.fuente = fuente                    # ServicioCripta sobre ClienteOffline
        self.almacen = almacen                  # AlmacenDisco: solo se lee
        self.version_vigente = version_vigente  # None: sirve la versión guardada de cada cripta

    # ------------------------------------------------------------------
    # Comprobaciones
    # ------------------------------------------------------------------
    def _exigir_version(self, cripta_id: str) -> None:
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
