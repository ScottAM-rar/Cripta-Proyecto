from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Trampa:
    id_instancia: str
    id_catalogo: str
    daño: int
    rearme: int #Unidades virtuales para volver a armarse tras activarse
    armada: bool = True

    #Aplica el daño y queda desarmada. Devuelve el daño a infligir;
    #quien llame es responsable de aplicarlo al jugador y de programar el evento de rearme
    def activar(self) -> int:
        if not self.armada:
            raise RuntimeError(f"La trampa {self.id_instancia!r} ya esta darmada")
        self.armada = False
        return self.daño

    def rearmar(self) -> None:
        """Vuelve a dejar la trampa armada (se llama desde el evento de
        rearme programado por el motor (el wapo Cesarin), `rearme` unidades después)."""
        self.armada = True
