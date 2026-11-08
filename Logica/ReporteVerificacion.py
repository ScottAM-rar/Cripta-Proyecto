"""Texto del reporte de la verificación de resolubilidad (capacidad 003; contracts/reporte-verificacion.md).

Es el único lugar donde se arma el texto: `--verificar`, el error de `CriptaNoResoluble` y el aviso de `--forzar` salen
de aquí. Se arma solo a partir del ResultadoVerificacion, sin hora, rutas ni contadores, así que dos resultados iguales
dan el mismo texto (FR-335). Es una función pura sin E/S: no es la vista.

Entrega provisional (grupo B, T017): solo el caso de error de datos. Los casos resoluble y no resoluble se completan en
el grupo E (T036)."""
from __future__ import annotations

from DTO.ResultadoVerificacionDTO import ResultadoVerificacion


def lineas_reporte(resultado: ResultadoVerificacion) -> list[str]:
    """Líneas del reporte de `--verificar`."""
    if resultado.resoluble is None:
        return [f"Verificación de la cripta {resultado.cripta_id}: NO SE PUDO VERIFICAR.", str(resultado.motivo_error)]
    raise NotImplementedError("se completa en el grupo E (T036)")


def aviso_forzado(resultado: ResultadoVerificacion) -> str:
    """Aviso de una sola línea que se muestra al iniciar con `--forzar` una cripta no resoluble (FR-340)."""
    raise NotImplementedError("se completa en el grupo E (T036)")
