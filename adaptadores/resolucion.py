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
    vida = colocacion.get("vida")   
    vida_actual = vida if vida is not None else ficha.vida_max
 
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
 
 
def resolver_trampa(colocacion: dict, ficha: dict, id_sala: int) -> Trampa:
    """Combina la ficha estática del catálogo (clase == 'trampa') con la
    instancia colocada en una sala (de /contenido) para armar una Trampa
    lista para usar. `id_sala` es la sala donde está colocada."""
    return Trampa(
        id_sala=id_sala,
        id_instancia=colocacion["instancia"],
        id_catalogo=ficha["id"],
        daño=ficha["daño"],
        rearme=ficha["rearme"],
    )
 
 
 
 
# ----------------------------------------------------------------------
# Resolución de una sala completa
# ----------------------------------------------------------------------
 
def _ids_necesarios(contenido: dict) -> list[str]:
    ids: list[str] = []
    for colocacion in contenido["enemigos"]:
        if colocacion["tipo"] not in ids:
            ids.append(colocacion["tipo"])
    for id_objeto in contenido["objetos"]:
        if id_objeto not in ids:
            ids.append(id_objeto)
    for colocacion in contenido["trampas"]:
        if colocacion["tipo"] not in ids:
            ids.append(colocacion["tipo"])
    return ids
 
 
def _obtener_fichas(ids: list[str], cliente, cache) -> list[dict]:
    fichas: list[dict] = []
    faltantes: list[str] = []
 
    for id_catalogo in ids:
        ficha = cache.obtener(id_catalogo)
        if ficha is None:
            faltantes.append(id_catalogo)
        else:
            fichas.append(ficha)
 
    if faltantes:
        for ficha in cliente.obtener_catalogo(faltantes):
            cache.insertar(ficha["id"], ficha)
            fichas.append(ficha)
 
    return fichas
 
 
def _buscar_ficha(fichas: list[dict], id_catalogo: str) -> dict:
    for ficha in fichas:
        if ficha["id"] == id_catalogo:
            return ficha
    raise KeyError(f"La API no devolvió la ficha de catálogo '{id_catalogo}'")
 
 
def _armar_sala(contenido: dict, fichas: list[dict], numero_sala: int):
    """Resuelve enemigos, objetos y trampas de UNA sala a partir de su
    colocación (/contenido) y de las fichas ya disponibles."""
    enemigos = []
    for colocacion in contenido["enemigos"]:
        ficha = resolver_ficha_enemigo(_buscar_ficha(fichas, colocacion["tipo"]))
        enemigos.append(resolver_enemigo(colocacion, ficha, numero_sala))
 
    objetos = []
    for id_objeto in contenido["objetos"]:
        objetos.append(resolver_objeto(_buscar_ficha(fichas, id_objeto)))
 
    trampas = []
    for colocacion in contenido["trampas"]:
        trampas.append(resolver_trampa(colocacion, _buscar_ficha(fichas, colocacion["tipo"]), numero_sala))
 
    return enemigos, objetos, trampas
 
 
def resolver_sala(cliente, cache, cripta_id: str, numero_sala: int):
    resultado = cliente.obtener_contenido(cripta_id, [numero_sala])
    if not resultado:
        raise ValueError(f"La API no devolvió contenido para la sala {numero_sala}")
    contenido = resultado[0]
 
    fichas = _obtener_fichas(_ids_necesarios(contenido), cliente, cache)
    return _armar_sala(contenido, fichas, numero_sala)
 
 
def resolver_salas(cliente, cache, cripta_id: str, numeros: list[int]):
    """Igual que resolver_sala pero para varias salas a la vez.
 
    Pide el contenido de todas en lotes de 10 y las fichas que falten en
    lotes de 10 (una sola vez por ficha, aunque se repita entre salas).
    Devuelve una lista de (enemigos, objetos, trampas) en el mismo orden
    que `numeros`."""
    contenidos = cliente.obtener_contenido(cripta_id, numeros)
    if len(contenidos) != len(numeros):
        raise ValueError(
            f"Se pidieron {len(numeros)} salas y la API devolvió {len(contenidos)}"
        )
 
    ids: list[str] = []
    for contenido in contenidos:
        for id_catalogo in _ids_necesarios(contenido):
            if id_catalogo not in ids:
                ids.append(id_catalogo)
 
    fichas = _obtener_fichas(ids, cliente, cache)
 
    resultado = []
    posicion = 0
    for numero in numeros:
        resultado.append(_armar_sala(contenidos[posicion], fichas, numero))
        posicion += 1
    return resultado