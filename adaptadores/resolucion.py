from __future__ import annotations

from DTO.Objeto import Objeto, Arma, Armadura, Pocion, Antidoto, Llave, Antorcha, PergaminoRetroceso

_CLASES_OBJETO = {
    "arma": Arma,
    "armadura": Armadura,
    "pocion": Pocion,
    "antidoto": Antidoto,
    "llave": Llave,
    "antorcha": Antorcha,
    "pergamino_retroceso": PergaminoRetroceso,
}


def resolver_objeto(ficha: dict) -> Objeto:
    """Convierte una entidad cruda del catálogo (de tipo objeto) en la
    instancia de DTO correspondiente, según su campo 'clase'."""
    clase = ficha["clase"]
    Clase = _CLASES_OBJETO.get(clase)
    if Clase is None:
        raise ValueError(f"'{clase}' no es una clase de objeto conocida")

    datos = dict(ficha)
    datos["id_catalogo"] = datos.pop("id")
    datos.pop("clase")

    return Clase(**datos)