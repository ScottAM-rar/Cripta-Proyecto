from __future__ import annotations
from DTO.CatalogoDTO import EnemigoCatalogoDTO
from DTO.ActorDTO import EnemigoDTO
from DTO.TrampaDTO import Trampa

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

def resolver_ficha_enemigo(ficha: dict) -> EnemigoCatalogoDTO:
    """Convierte la ficha cruda de /catalogo (clase == 'enemigo') en
    EnemigoCatalogoDTO."""
    datos = dict(ficha)
    datos.pop("clase")
    return EnemigoCatalogoDTO(**datos)

def resolver_enemigo(colocacion: dict, ficha: EnemigoCatalogoDTO, id_sala: int) -> EnemigoDTO:
    """Combina la ficha estática del catálogo con la instancia colocada en
    una sala (de /contenido) para armar un EnemigoDTO jugable."""
    vida_actual = colocacion["vida"] if colocacion["vida"] is not None else ficha.vida_max

    return EnemigoDTO(
        vida_actual=vida_actual,
        vida_max=ficha.vida_max,
        ataque=ficha.ataque,
        defensa=ficha.defensa,
        velocidad=ficha.velocidad,
        id_sala_actual=id_sala,
        id_instancia=colocacion["instancia"],
        tipo=colocacion["tipo"],
        nombre=ficha.nombre,
        comportamiento=ficha.comportamiento,
        suelta=list(ficha.suelta),
    )


def resolver_trampa(colocacion: dict, ficha: dict) -> Trampa:
    """Combina la ficha estática del catálogo (clase == 'trampa') con la
    instancia colocada en una sala (de /contenido) para armar una Trampa
    lista para usar."""
    return Trampa(
        id_instancia=colocacion["instancia"],
        id_catalogo=ficha["id"],
        daño=ficha["daño"],
        rearme=ficha["rearme"],
    )