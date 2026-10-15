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

    @property
    @abstractmethod
    def solicitudes_realizadas(self) -> int:
        """Solicitudes HTTP reales hechas hasta ahora (0 si el cliente no usa la red).
        ServicioCripta la usa para el reporte contra el presupuesto de la cripta."""
        ...
