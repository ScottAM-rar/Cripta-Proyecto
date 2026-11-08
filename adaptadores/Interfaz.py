from __future__ import annotations
from abc import ABC, abstractmethod

class ClienteInterfaz(ABC):
    """Contrato común entre el cliente online (HTTP) y el offline."""

    @abstractmethod
    def obtener_criptas(self) -> list[dict]:
        ...

    @abstractmethod
    def obtener_datos_generales(self, cripta_id: str) -> dict:
        ...

    @abstractmethod
    def obtener_version_cripta(self, cripta_id: str) -> str:
        ...

    @abstractmethod
    def obtener_salas(self, cripta_id: str) -> list[dict]:
        ...

    @abstractmethod
    def obtener_contenido(self, cripta_id: str, salas: list[int]) -> list[dict]:
        ...

    @abstractmethod
    def obtener_catalogo(self, ids: list[str]) -> list[dict]:
        ...

    @abstractmethod
    def obtener_version_catalogo(self) -> str:
        ...

    @abstractmethod
    def obtener_llaves(self, cripta_id: str, solo_guardadas: bool = False,
                       limite_solicitudes: int | None = None) -> list[dict]:
        """Ubicación de las llaves de la cripta (GET /criptas/<id>/llaves): la lista cruda, cada elemento con `id`,
        `sala` y opcionalmente `enemigo` (capacidad 009).

        `solo_guardadas`: no hacer la solicitud; devolver solo lo guardado o fallar (no queda presupuesto).
        `limite_solicitudes`: máximo de solicitudes (incluidos los reintentos por 429) que puede gastar esta
        consulta; `None` = sin límite propio. El persistente lo pasa tal cual al HTTP; el offline lo ignora."""
        ...

    @property
    @abstractmethod
    def solicitudes_realizadas(self) -> int:
        """Solicitudes HTTP reales hechas hasta ahora (0 si el cliente no usa la red).
        ServicioCripta la usa para el reporte contra el presupuesto de la cripta."""
        ...
