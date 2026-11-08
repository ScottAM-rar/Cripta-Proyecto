"""Corre las 9 pruebas nuevas de la capacidad 009 con la red bloqueada (T051, SC-006, FR-318).

    py -m tests_labs.sin_red

`sin_red()` sustituye requests.get por una función que lanza AssertionError("intento de red") y lo restaura al salir,
aunque algo falle adentro. Las pruebas que usan mock.patch de requests.get siguen funcionando: lo sustituyen dentro de
su propio alcance y, al terminar, vuelve a quedar el bloqueo (no la red). Termina con código distinto de cero si alguna
prueba falla o da error.
"""
from __future__ import annotations

import contextlib
import sys
import unittest

import requests

PRUEBAS = (
    "test_llaves_validacion",
    "test_llaves_dto",
    "test_llaves_clientes",
    "test_llaves_presupuesto",
    "test_llaves_version",
    "test_llaves_fallos",
    "test_llaves_partida_cargada",
    "test_fuente_solo_local",
    "test_api_falsa_v2",
)


def _intento_de_red(*args, **kwargs):
    raise AssertionError("intento de red")


@contextlib.contextmanager
def sin_red():
    """Mientras dura, cualquier requests.get lanza AssertionError("intento de red")."""
    original = requests.get
    requests.get = _intento_de_red
    try:
        yield
    finally:
        requests.get = original


def main() -> int:
    pruebas = unittest.TestLoader().loadTestsFromNames(PRUEBAS)
    with sin_red():
        resultado = unittest.TextTestRunner(verbosity=2).run(pruebas)
    print(f"\nPruebas ejecutadas con requests.get bloqueado: {resultado.testsRun} "
          f"(fallos: {len(resultado.failures)}, errores: {len(resultado.errors)})")
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
