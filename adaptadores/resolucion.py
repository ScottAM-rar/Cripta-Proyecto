from __future__ import annotations
from DTO.CatalogoDTO import EnemigoCatalogoDTO
from DTO.ActorDTO import EnemigoDTO
from DTO.TrampaDTO import Trampa
 
from DTO.Objeto import Objeto, Arma, Armadura, Pocion, Antidoto, Llave, Antorcha, PergaminoRetroceso
 
def _clase_de_objeto(clase: str):
    """Devuelve la clase de DTO que corresponde al campo 'clase' de la ficha."""
    match clase:
        case "arma":
            return Arma
        case "armadura":
            return Armadura
        case "pocion":
            return Pocion
        case "antidoto":
            return Antidoto
        case "llave":
            return Llave
        case "antorcha":
            return Antorcha
        case "pergamino_retroceso":
            return PergaminoRetroceso
        case _:
            return None
 
 
def resolver_objeto(ficha: dict, id_sala: int | None = None) -> Objeto:
    """Convierte una entidad cruda del catálogo (de tipo objeto) en la
    instancia de DTO correspondiente, según su campo 'clase'.
 
    `id_sala` es la sala donde está el objeto en el suelo. Es opcional: un
    objeto que lleva el jugador en el inventario no está en ninguna sala."""
    clase = ficha["clase"]
    Clase = _clase_de_objeto(clase)
    if Clase is None:
        raise ValueError(f"'{clase}' no es una clase de objeto conocida")
 
    datos = dict(ficha)
    datos["id_catalogo"] = datos.pop("id")
    datos.pop("clase")
    if id_sala is not None:
        datos["id_sala"] = id_sala
 
    return Clase(**datos)
 
def _rango_de(ficha: dict, advertencias: list[str] | None) -> int:
    """Rango de un cazador (FR-108): entero >= 0. Ausente o inválido (negativo, no entero) vale 0 y deja una
    advertencia; 0 declarado es válido. Solo importa si el comportamiento es 'cazador'; para los demás vale 0."""
    if ficha.get("comportamiento") != "cazador":
        return 0
    valor = ficha.get("rango")
    if isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0:
        return valor
    if advertencias is not None:
        motivo = "sin rango" if "rango" not in ficha else f"rango inválido {valor!r}"
        texto = f"Ficha {ficha.get('id')}: cazador {motivo}; se usa 0 (solo ataca en su sala)"
        if texto not in advertencias:
            advertencias.append(texto)
    return 0


def resolver_ficha_enemigo(ficha: dict, advertencias: list[str] | None = None) -> EnemigoCatalogoDTO:
    """Convierte la ficha cruda de /catalogo (clase == 'enemigo') en
    EnemigoCatalogoDTO."""
    datos = dict(ficha)
    datos.pop("clase")
    datos["rango"] = _rango_de(ficha, advertencias)
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
        rango=ficha.rango,
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
 
 
def _ids_de_botin(contenidos: list[dict], fichas: list[dict], ya_pedidos: list[str]) -> list[str]:
    """Ids de lo que sueltan los enemigos de estas salas (campo `suelta` de su ficha) y que todavía no se
    pidieron. Se traen junto con la sala para que, al morir el enemigo, el botín salga de la caché o del disco
    sin gastar solicitudes en pleno combate (y para que también funcione con --offline)."""
    ids: list[str] = []
    for contenido in contenidos:
        for colocacion in contenido["enemigos"]:
            ficha = _buscar_ficha(fichas, colocacion["tipo"])
            for id_objeto in ficha.get("suelta") or []:
                if id_objeto not in ya_pedidos and id_objeto not in ids:
                    ids.append(id_objeto)
    return ids


def resolver_botin(cliente, cache, ids_suelta: list[str], id_sala: int) -> list[Objeto]:
    """Instancias NUEVAS de lo que suelta un enemigo (una por cada id de `suelta`, aunque se repita), con
    `id_sala` como sala donde quedan en el suelo. Las fichas que no estén en la caché ni en el disco se piden
    juntas, en una sola solicitud en lote."""
    if not ids_suelta:
        return []
    unicos: list[str] = []
    for id_objeto in ids_suelta:
        if id_objeto not in unicos:
            unicos.append(id_objeto)
    fichas = _obtener_fichas(unicos, cliente, cache)
    botin: list[Objeto] = []
    for id_objeto in ids_suelta:
        botin.append(resolver_objeto(_buscar_ficha(fichas, id_objeto), id_sala))
    return botin


def _armar_sala(contenido: dict, fichas: list[dict], numero_sala: int, advertencias: list[str] | None = None):
    """Resuelve enemigos, objetos y trampas de UNA sala a partir de su
    colocación (/contenido) y de las fichas ya disponibles."""
    enemigos = []
    for colocacion in contenido["enemigos"]:
        ficha = resolver_ficha_enemigo(_buscar_ficha(fichas, colocacion["tipo"]), advertencias)
        enemigos.append(resolver_enemigo(colocacion, ficha, numero_sala))
 
    objetos = []
    for id_objeto in contenido["objetos"]:
        objetos.append(resolver_objeto(_buscar_ficha(fichas, id_objeto), numero_sala))
 
    trampas = []
    for colocacion in contenido["trampas"]:
        trampas.append(resolver_trampa(colocacion, _buscar_ficha(fichas, colocacion["tipo"]), numero_sala))
 
    return enemigos, objetos, trampas
 
 
def resolver_sala(cliente, cache, cripta_id: str, numero_sala: int, advertencias: list[str] | None = None):
    resultado = cliente.obtener_contenido(cripta_id, [numero_sala])
    if not resultado:
        raise ValueError(f"La API no devolvió contenido para la sala {numero_sala}")
    contenido = resultado[0]
 
    ids = _ids_necesarios(contenido)
    fichas = _obtener_fichas(ids, cliente, cache)
    fichas = fichas + _obtener_fichas(_ids_de_botin([contenido], fichas, ids), cliente, cache)
    return _armar_sala(contenido, fichas, numero_sala, advertencias)
 
 
def resolver_salas(cliente, cache, cripta_id: str, numeros: list[int], advertencias: list[str] | None = None):
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
    fichas = fichas + _obtener_fichas(_ids_de_botin(contenidos, fichas, ids), cliente, cache)
 
    resultado = []
    posicion = 0
    for numero in numeros:
        resultado.append(_armar_sala(contenidos[posicion], fichas, numero, advertencias))
        posicion += 1
    return resultado