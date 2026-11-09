"""Resultado de la verificación de resolubilidad de una cripta (capacidad 003, FR-344; data-model.md §3).

Lo devuelve la operación de verificación y lo leen el inicio de partida, `--verificar` y la vista. Son dataclasses con
listas comunes: sin dict ni set (principio I). No importa nada de Logica ni de los adaptadores.

Invariantes:
- `resoluble is None` ⇔ `motivo_error is not None`; en ese caso `orden`, `salas_alcanzables`, `bloqueos` y `causas`
  están vacías (error de datos, FR-343: no se inventa un resultado).
- `resoluble is True` ⇒ la llave de salida figura exactamente una vez en `orden`; `bloqueos` y `causas` vacías.
- `resoluble is False` ⇒ `orden` vacía y `causas` no vacía.
- Cada id de llave aparece como máximo una vez en `orden`.
- Dos verificaciones de los mismos datos dan resultados iguales campo por campo (FR-335).
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Tipos de bloqueo (FR-338, research.md §6).
SIN_LLAVE = "SIN_LLAVE"                      # la puerta está cerrada y no tiene llave asignada
LLAVE_INEXISTENTE = "LLAVE_INEXISTENTE"      # ninguna ubicación tiene esa llave
CICLO = "CICLO"                              # alguna ubicación está en una sala a la que se llegaría abriendo todas las puertas
LLAVE_SIN_CAMINO = "LLAVE_SIN_CAMINO"        # ninguna ubicación tiene camino desde la sala inicial, ni abriendo todas las puertas

# Causas generales de una cripta no resoluble, en el orden fijo en que se informan.
LLAVE_SALIDA_INEXISTENTE = "LLAVE_SALIDA_INEXISTENTE"
SALIDA_SIN_CAMINO = "SALIDA_SIN_CAMINO"
SALIDA_BLOQUEADA = "SALIDA_BLOQUEADA"
LLAVE_SALIDA_INALCANZABLE = "LLAVE_SALIDA_INALCANZABLE"
CAUSAS_EN_ORDEN = (LLAVE_SALIDA_INEXISTENTE, SALIDA_SIN_CAMINO, SALIDA_BLOQUEADA, LLAVE_SALIDA_INALCANZABLE)


@dataclass
class PasoLlaveDTO:
    """Un paso del orden de obtención de llaves (FR-336)."""
    llave: str                    # id de la llave
    sala: int                     # sala del suelo o sala inicial del enemigo que la suelta (FR-334)
    enemigo: str | None = None    # instancia del enemigo que la suelta, o None si está en el suelo


@dataclass
class BloqueoDTO:
    """Una puerta que separa lo alcanzable de lo no alcanzable (FR-338)."""
    sala_origen: int              # sala alcanzable desde la que sale la puerta
    direccion: str                # "norte", "sur", "este" u "oeste"
    sala_destino: int             # sala no alcanzable
    llave: str | None             # llave que pide la puerta; None si no tiene
    salas_de_la_llave: list[int]  # salas de las ubicaciones de esa llave, crecientes y sin repetir; vacía si no existe
    tipo: str                     # SIN_LLAVE, LLAVE_INEXISTENTE, CICLO o LLAVE_SIN_CAMINO


@dataclass
class ResultadoVerificacion:
    cripta_id: str
    resoluble: bool | None                                       # None: error de datos (FR-343)
    orden: list[PasoLlaveDTO] = field(default_factory=list)      # solo si resoluble (FR-336)
    salas_alcanzables: list[int] = field(default_factory=list)   # ids crecientes (FR-337)
    salas_no_alcanzables: int = 0                                # solo si no resoluble (FR-337)
    bloqueos: list[BloqueoDTO] = field(default_factory=list)     # solo si no resoluble (FR-338)
    causas: list[str] = field(default_factory=list)              # solo si no resoluble, en el orden de CAUSAS_EN_ORDEN
    llave_salida: str | None = None
    sala_salida: int | None = None
    motivo_error: str | None = None                              # solo si resoluble is None

    def codigo_salida(self) -> int:
        """Código de salida de `--verificar` (FR-331): 0 si resoluble is True, 1 si resoluble is False, 2 si resoluble
        is None (error de datos)."""
        if self.resoluble is True:
            return 0
        if self.resoluble is False:
            return 1
        return 2
