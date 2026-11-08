"""Verificación de resolubilidad de una cripta (capacidad 003).

- `verificar_resolubilidad(...)`: función pura que decide con el mapa, la sala inicial, la sala de salida, la llave de
  salida y la ubicación de llaves de la capacidad 009 (research.md §2 a §6).
- `verificar(fuente, cripta_id, llaves=None)`: junta esos datos desde la fuente (solo el contrato del modelo,
  FuenteCripta) y llama a la función pura; traduce los fallos de datos a `motivo_error` (research.md §8).
- `CriptaNoResoluble`: la lanza el inicio de partida sin `--forzar` (FR-339).

No importa adaptadores (principio IV). Es la operación única que usan `--verificar` y el inicio de partida (FR-344).

ENTREGA PROVISIONAL (grupo B, T016): las firmas son las definitivas (contracts/interfaz-verificacion.md), pero las dos
funciones devuelven un resultado de error de datos (código de salida 2) y nunca inventan un resultado. El algoritmo se
implementa en el grupo D (T030 a T032)."""
from __future__ import annotations

from DTO.LlavesDTO import UbicacionLlavesDTO
from DTO.ResultadoVerificacionDTO import ResultadoVerificacion
from Logica.MapaCripta import MapaCripta
from Logica.ReporteVerificacion import lineas_reporte

MOTIVO_PROVISIONAL = "La verificación de resolubilidad todavía no está implementada."


class CriptaNoResoluble(RuntimeError):
    """Se intentó iniciar una partida sin `--forzar` en una cripta no resoluble (FR-339). El mensaje es el reporte."""

    def __init__(self, resultado: ResultadoVerificacion) -> None:
        self.resultado = resultado
        super().__init__("\n".join(lineas_reporte(resultado)))


def verificar_resolubilidad(mapa: MapaCripta, sala_inicial: int, sala_salida: int, llave_salida: str | None,
                            llaves: UbicacionLlavesDTO, cripta_id: str = "") -> ResultadoVerificacion:
    """Decide si la cripta es resoluble (FR-332 a FR-338). Provisional: devuelve error de datos (código 2)."""
    return ResultadoVerificacion(cripta_id, resoluble=None, motivo_error=MOTIVO_PROVISIONAL)


def verificar(fuente, cripta_id: str, llaves: UbicacionLlavesDTO | None = None) -> ResultadoVerificacion:
    """Verifica la cripta con los datos de `fuente` (FuenteCripta). `llaves`: las que ya pidió la partida, para no
    volver a pedirlas (FR-341). Provisional: devuelve error de datos (código 2)."""
    return ResultadoVerificacion(cripta_id, resoluble=None, motivo_error=MOTIVO_PROVISIONAL)
