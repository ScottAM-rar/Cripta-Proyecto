"""Texto del reporte de la verificación de resolubilidad (capacidad 003; contracts/reporte-verificacion.md).

Es el único lugar donde se arma el texto: `--verificar`, el error de `CriptaNoResoluble` y el aviso de `--forzar` salen
de aquí. Se arma solo a partir del ResultadoVerificacion, sin hora, rutas ni contadores, así que dos resultados iguales
dan el mismo texto carácter por carácter (FR-335). Es una función pura sin E/S: no es la vista (principio IV).
"""
from __future__ import annotations

from DTO.ResultadoVerificacionDTO import (CICLO, LLAVE_INEXISTENTE, LLAVE_SALIDA_INALCANZABLE, LLAVE_SALIDA_INEXISTENTE,
                                          LLAVE_SIN_CAMINO, SALIDA_BLOQUEADA, SALIDA_SIN_CAMINO, SIN_LLAVE,
                                          ResultadoVerificacion)

MARCA_SALIDA = " (llave de salida)"


def _con_marca(id_llave: str, resultado: ResultadoVerificacion) -> str:
    """El id de la llave, marcado si es la llave de salida."""
    return id_llave + MARCA_SALIDA if id_llave == resultado.llave_salida else id_llave


def _lista(numeros: list[int]) -> str:
    texto = ""
    for posicion in range(len(numeros)):
        if posicion > 0:
            texto += ", "
        texto += str(numeros[posicion])
    return texto


def _en_salas(salas: list[int]) -> str:
    """«la sala 2» con una sola sala, «las salas 4, 9» con varias."""
    return f"la sala {salas[0]}" if len(salas) == 1 else f"las salas {_lista(salas)}"


def _texto_causa(causa: str, resultado: ResultadoVerificacion) -> str:
    salida, llave = resultado.sala_salida, resultado.llave_salida
    if causa == LLAVE_SALIDA_INEXISTENTE:
        return f"la llave de salida {llave} no existe en la cripta."
    if causa == SALIDA_SIN_CAMINO:
        return f"la sala de salida {salida} no tiene camino desde la sala inicial, aunque se tuvieran todas las llaves."
    if causa == SALIDA_BLOQUEADA:
        return f"la sala de salida {salida} tiene camino, pero las puertas lo impiden."
    if causa == LLAVE_SALIDA_INALCANZABLE:
        return f"se llega a la sala de salida {salida}, pero la llave de salida {llave} no se puede obtener."
    raise ValueError(f"Causa desconocida: {causa!r}")


def _texto_bloqueo(bloqueo, resultado: ResultadoVerificacion) -> str:
    inicio = f"  - Sala {bloqueo.sala_origen}, salida {bloqueo.direccion} hacia la sala {bloqueo.sala_destino}: "
    if bloqueo.tipo == SIN_LLAVE:
        return inicio + "está cerrada y no tiene llave."
    llave = _con_marca(bloqueo.llave, resultado)
    if bloqueo.tipo == LLAVE_INEXISTENTE:
        return inicio + f"pide {llave}, que no existe en la cripta."
    if bloqueo.tipo == CICLO:
        return (inicio + f"pide {llave}, que está en {_en_salas(bloqueo.salas_de_la_llave)}. Ciclo: la llave está detrás "
                         f"de esta puerta o de otras puertas bloqueadas.")
    if bloqueo.tipo == LLAVE_SIN_CAMINO:
        return inicio + f"pide {llave}, que está en {_en_salas(bloqueo.salas_de_la_llave)}, sin camino desde la sala inicial."
    raise ValueError(f"Tipo de bloqueo desconocido: {bloqueo.tipo!r}")


def lineas_reporte(resultado: ResultadoVerificacion) -> list[str]:
    """Líneas del reporte de `--verificar` (FR-336 a FR-338, FR-343)."""
    encabezado = f"Verificación de la cripta {resultado.cripta_id}: "
    if resultado.resoluble is None:
        return [encabezado + "NO SE PUDO VERIFICAR.", str(resultado.motivo_error)]
    if resultado.resoluble:
        lineas = [encabezado + "RESOLUBLE.", "Orden de obtención de llaves:"]
        for posicion in range(len(resultado.orden)):
            paso = resultado.orden[posicion]
            linea = f"  {posicion + 1}. {paso.llave} en la sala {paso.sala}"
            if paso.enemigo is not None:
                linea += f", la suelta {paso.enemigo}"
            if paso.llave == resultado.llave_salida:
                linea += MARCA_SALIDA
            lineas.append(linea)
        return lineas
    lineas = [encabezado + "NO RESOLUBLE."]
    for causa in resultado.causas:
        lineas.append("Motivo: " + _texto_causa(causa, resultado))
    if resultado.bloqueos:                                  # sin bloqueos no se escribe el encabezado
        lineas.append("Puertas bloqueadas:")
        for bloqueo in resultado.bloqueos:
            lineas.append(_texto_bloqueo(bloqueo, resultado))
    lineas.append(f"Salas alcanzables ({len(resultado.salas_alcanzables)}): {_lista(resultado.salas_alcanzables)}")
    lineas.append(f"Salas no alcanzables: {resultado.salas_no_alcanzables}")
    return lineas


def aviso_forzado(resultado: ResultadoVerificacion) -> str:
    """Aviso de una sola línea que se muestra al iniciar con `--forzar` una cripta no resoluble (FR-340). La primera
    causa va sin su punto final, entre paréntesis."""
    if resultado.resoluble is not False or not resultado.causas:
        raise ValueError("aviso_forzado solo se usa con una cripta no resoluble")
    causa = _texto_causa(resultado.causas[0], resultado)
    if causa.endswith("."):
        causa = causa[:-1]
    return (f"AVISO: la cripta {resultado.cripta_id} no es resoluble ({causa}); la partida se inicia porque se usó "
            f"--forzar.")
