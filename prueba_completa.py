"""
Prueba completa de la capa de comunicación con la API (Scott).

Uso:
    py prueba_completa.py            -> solo pruebas OFFLINE (sin internet, 0 solicitudes)
    py prueba_completa.py --live     -> offline + pruebas contra la API real

Cada prueba es una función 'prueba_*'. Si un 'assert' falla, se muestra FALLO
con el motivo; si todo va bien se muestra OK.
"""
import sys
import traceback
from unittest import mock

import adaptadores.cliente_http as modulo_http
from adaptadores.cliente_http import ClienteCripta
from adaptadores.resolucion import (
    resolver_objeto, resolver_ficha_enemigo, resolver_enemigo,
    resolver_trampa, resolver_sala,
)
from DTO.Objeto import Arma, Armadura, Pocion, Antidoto, Llave, Antorcha, PergaminoRetroceso

from adaptadores.Cache import CacheLRU

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


# ======================================================================
# Datos y herramientas de apoyo
# ======================================================================
FICHAS = {
    "ent_rata_gigante": {"id": "ent_rata_gigante", "nombre": "Rata gigante", "clase": "enemigo",
        "vida_max": 8, "ataque": 2, "defensa": 1, "velocidad": 5,
        "comportamiento": "errante", "suelta": ["itm_antorcha"]},
    "itm_antorcha": {"id": "itm_antorcha", "nombre": "Antorcha", "clase": "antorcha",
        "peso": 1, "valor": 2, "duracion": 30},
    "itm_daga": {"id": "itm_daga", "nombre": "Daga", "clase": "arma",
        "peso": 2, "valor": 5, "ataque_bonus": 3},
    "itm_coraza": {"id": "itm_coraza", "nombre": "Coraza", "clase": "armadura",
        "peso": 8, "valor": 20, "defensa_bonus": 4},
    "itm_pocion": {"id": "itm_pocion", "nombre": "Poción", "clase": "pocion",
        "peso": 1, "valor": 4, "cura": 10, "modificador_velocidad": 0, "duracion": 0},
    "itm_antidoto": {"id": "itm_antidoto", "nombre": "Antídoto", "clase": "antidoto",
        "peso": 1, "valor": 3},
    "itm_llave": {"id": "itm_llave", "nombre": "Llave", "clase": "llave",
        "peso": 1, "valor": 1, "abre": "itm_llave"},
    "itm_pergamino": {"id": "itm_pergamino", "nombre": "Pergamino", "clase": "pergamino_retroceso",
        "peso": 1, "valor": 9},
    "trp_dardos": {"id": "trp_dardos", "nombre": "Dardos", "clase": "trampa",
        "daño": 4, "rearme": 10},
}


class ClienteFalso:
    """Imita a ClienteCripta sin internet y registra qué se le pidió."""
    def __init__(self, contenido_por_sala):
        self.contenido_por_sala = contenido_por_sala
        self.pedidos_catalogo = []       # una entrada por llamada a obtener_catalogo

    def obtener_contenido(self, cripta_id, salas):
        return [self.contenido_por_sala[n] for n in salas if n in self.contenido_por_sala]

    def obtener_catalogo(self, ids):
        self.pedidos_catalogo.append(list(ids))
        return [FICHAS[i] for i in ids]


SALA_2 = {"sala": 2,
          "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": None},
                       {"instancia": "e-202", "tipo": "ent_rata_gigante", "vida": 3}],
          "objetos": ["itm_antorcha"],
          "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]}
SALA_VACIA = {"sala": 5, "enemigos": [], "objetos": [], "trampas": []}


class RespuestaFalsa:
    def __init__(self, codigo, datos):
        self.status_code = codigo
        self._datos = datos
    def json(self):
        return self._datos


# ======================================================================
# 1) resolver_objeto / resolver_ficha_enemigo / resolver_enemigo / resolver_trampa
# ======================================================================
def prueba_resolver_objeto_las_7_clases():
    esperado = {"itm_antorcha": Antorcha, "itm_daga": Arma, "itm_coraza": Armadura,
                "itm_pocion": Pocion, "itm_antidoto": Antidoto, "itm_llave": Llave,
                "itm_pergamino": PergaminoRetroceso}
    for id_cat, clase in esperado.items():
        obj = resolver_objeto(FICHAS[id_cat])
        assert type(obj) is clase, f"{id_cat}: esperaba {clase.__name__}, salió {type(obj).__name__}"
        assert obj.id_catalogo == id_cat, f"{id_cat}: id_catalogo incorrecto ({obj.id_catalogo})"

def prueba_resolver_objeto_campos_especificos():
    assert resolver_objeto(FICHAS["itm_daga"]).ataque_bonus == 3
    assert resolver_objeto(FICHAS["itm_coraza"]).defensa_bonus == 4
    assert resolver_objeto(FICHAS["itm_llave"]).abre == "itm_llave"
    assert resolver_objeto(FICHAS["itm_antorcha"]).duracion == 30

def prueba_resolver_objeto_no_modifica_la_ficha():
    ficha = dict(FICHAS["itm_daga"])
    copia = dict(ficha)
    resolver_objeto(ficha)
    assert ficha == copia, "resolver_objeto modificó el diccionario original (¡rompería la caché!)"

def prueba_resolver_objeto_clase_desconocida():
    for ficha in (FICHAS["trp_dardos"], FICHAS["ent_rata_gigante"], {"id": "x", "clase": "dragon"}):
        try:
            resolver_objeto(ficha)
        except ValueError:
            continue
        raise AssertionError(f"debía lanzar ValueError con clase {ficha['clase']!r}")

def prueba_resolver_enemigo_vida():
    ficha = resolver_ficha_enemigo(FICHAS["ent_rata_gigante"])
    sano = resolver_enemigo(SALA_2["enemigos"][0], ficha, 2)
    herido = resolver_enemigo(SALA_2["enemigos"][1], ficha, 2)
    assert sano.vida_actual == 8, f"vida None debía dar vida_max (8), dio {sano.vida_actual}"
    assert herido.vida_actual == 3, f"vida 3 debía respetarse, dio {herido.vida_actual}"
    assert sano.vida_max == herido.vida_max == 8

def prueba_resolver_enemigo_campos():
    ficha = resolver_ficha_enemigo(FICHAS["ent_rata_gigante"])
    e = resolver_enemigo(SALA_2["enemigos"][0], ficha, 2)
    assert (e.id_instancia, e.tipo, e.nombre) == ("e-201", "ent_rata_gigante", "Rata gigante")
    assert (e.ataque, e.defensa, e.velocidad) == (2, 1, 5)
    assert e.id_sala_actual == 2
    assert e.comportamiento == "errante"

def prueba_resolver_enemigo_suelta_es_copia():
    ficha = resolver_ficha_enemigo(FICHAS["ent_rata_gigante"])
    a = resolver_enemigo(SALA_2["enemigos"][0], ficha, 2)
    b = resolver_enemigo(SALA_2["enemigos"][1], ficha, 2)
    a.suelta.clear()
    assert b.suelta == ["itm_antorcha"], "a y b comparten la misma lista 'suelta'"
    assert ficha.suelta == ["itm_antorcha"], "la ficha fue modificada desde un enemigo"

def prueba_resolver_trampa():
    t = resolver_trampa(SALA_2["trampas"][0], FICHAS["trp_dardos"])
    assert (t.id_instancia, t.id_catalogo, t.daño, t.rearme) == ("t-17", "trp_dardos", 4, 10)
    assert t.armada is True


# ======================================================================
# 2) CacheLRU
# ======================================================================
def prueba_cache_obtener_y_insertar():
    c = CacheLRU(3)
    assert c.obtener("a") is None
    c.insertar("a", 1)
    assert c.obtener("a") == 1

def prueba_cache_actualiza_clave_existente():
    c = CacheLRU(3)
    c.insertar("a", 1)
    c.insertar("a", 99)
    assert c.obtener("a") == 99
    assert len(c._entradas) == 1, "insertar la misma clave duplicó la entrada"

def prueba_cache_desaloja_el_menos_reciente():
    c = CacheLRU(3)
    for k in ("a", "b", "c"):
        c.insertar(k, k)
    c.obtener("a")               # a pasa a ser la más reciente → la víctima será b
    c.insertar("d", "d")
    assert c.obtener("b") is None, "b debía haber sido desalojada"
    assert c.obtener("a") == "a" and c.obtener("c") == "c" and c.obtener("d") == "d"

def prueba_cache_no_pasa_de_capacidad():
    c = CacheLRU(3)
    for i in range(10):
        c.insertar(f"k{i}", i)
    assert len(c._entradas) == 3, f"tiene {len(c._entradas)} entradas, capacidad 3"

def prueba_cache_en_uso_no_se_desaloja():
    c = CacheLRU(2)
    c.insertar("a", 1)           # la más vieja...
    c.insertar("b", 2)
    c.marcar_en_uso("a")         # ...pero está en uso
    c.insertar("c", 3)
    assert c.obtener("a") == 1, "a estaba en uso y fue desalojada"
    assert c.obtener("b") is None, "debía desalojarse b (la más vieja libre)"

def prueba_cache_marcar_libre_permite_desalojar():
    c = CacheLRU(2)
    c.insertar("a", 1); c.insertar("b", 2)
    c.marcar_en_uso("a"); c.marcar_libre("a")
    c.insertar("c", 3)
    assert c.obtener("a") is None, "a ya estaba libre y era la más vieja"

def prueba_cache_contador_en_uso_acumula():
    c = CacheLRU(2)
    c.insertar("a", 1); c.insertar("b", 2)
    c.marcar_en_uso("a"); c.marcar_en_uso("a")    # dos usos
    c.marcar_libre("a")                            # queda uno
    c.insertar("c", 3)
    assert c.obtener("a") == 1, "a aún tenía 1 uso y fue desalojada"

def prueba_cache_marcar_clave_inexistente_no_falla():
    c = CacheLRU(2)
    c.marcar_en_uso("nada")
    c.marcar_libre("nada")


# ======================================================================
# 3) resolver_sala (con cliente falso)
# ======================================================================
def prueba_sala_contenido_correcto():
    cliente = ClienteFalso({2: SALA_2})
    enemigos, objetos, trampas = resolver_sala(cliente, CacheLRU(25), "c1", 2)
    assert [(e.id_instancia, e.vida_actual) for e in enemigos] == [("e-201", 8), ("e-202", 3)]
    assert len(objetos) == 1 and type(objetos[0]) is Antorcha
    assert len(trampas) == 1 and trampas[0].id_instancia == "t-17"

def prueba_sala_una_sola_tanda_sin_repetidos():
    cliente = ClienteFalso({2: SALA_2})
    resolver_sala(cliente, CacheLRU(25), "c1", 2)
    assert len(cliente.pedidos_catalogo) == 1, f"hizo {len(cliente.pedidos_catalogo)} llamadas a catálogo"
    assert sorted(cliente.pedidos_catalogo[0]) == ["ent_rata_gigante", "itm_antorcha", "trp_dardos"]

def prueba_sala_segunda_vez_sale_de_cache():
    cliente = ClienteFalso({2: SALA_2})
    cache = CacheLRU(25)
    resolver_sala(cliente, cache, "c1", 2)
    resolver_sala(cliente, cache, "c1", 2)
    assert len(cliente.pedidos_catalogo) == 1, "la segunda vez volvió a pedir al catálogo"

def prueba_sala_pide_solo_lo_que_falta():
    cliente = ClienteFalso({2: SALA_2})
    cache = CacheLRU(25)
    cache.insertar("itm_antorcha", FICHAS["itm_antorcha"])    # ya la tenemos
    resolver_sala(cliente, cache, "c1", 2)
    assert "itm_antorcha" not in cliente.pedidos_catalogo[0], "volvió a pedir una ficha que estaba en caché"
    assert len(cliente.pedidos_catalogo[0]) == 2

def prueba_sala_vacia_no_pide_nada():
    cliente = ClienteFalso({5: SALA_VACIA})
    resultado = resolver_sala(cliente, CacheLRU(25), "c1", 5)
    assert resultado == ([], [], [])
    assert cliente.pedidos_catalogo == [], "pidió catálogo para una sala vacía"

def prueba_sala_inexistente_falla_claro():
    try:
        resolver_sala(ClienteFalso({}), CacheLRU(25), "c1", 99)
    except ValueError:
        return
    raise AssertionError("debía lanzar ValueError para una sala sin contenido")

def prueba_sala_funciona_con_cache_diminuta():
    """Con capacidad 1 las fichas se desalojan entre sí, pero la sala debe resolverse bien."""
    cliente = ClienteFalso({2: SALA_2})
    enemigos, objetos, trampas = resolver_sala(cliente, CacheLRU(1), "c1", 2)
    assert len(enemigos) == 2 and len(objetos) == 1 and len(trampas) == 1


# ======================================================================
# 4) ClienteCripta real, pero con 'requests.get' y 'time.sleep' simulados
# ======================================================================
def _cliente_con_respuestas(respuestas):
    """Crea un ClienteCripta cuyo requests.get devuelve 'respuestas' en orden."""
    cliente = ClienteCripta("https://api.falsa/v1/")
    parche_get = mock.patch.object(modulo_http.requests, "get", side_effect=respuestas)
    parche_sleep = mock.patch.object(modulo_http.time, "sleep")
    return cliente, parche_get, parche_sleep

def prueba_cliente_url_sin_barra_final_y_header():
    cliente, pg, ps = _cliente_con_respuestas([RespuestaFalsa(200, {"criptas": []})])
    with pg as get, ps:
        cliente.obtener_criptas()
    url = get.call_args.args[0]
    assert url == "https://api.falsa/v1/criptas", f"URL armada mal: {url}"
    assert "X-Cripta-Client-Id" in get.call_args.kwargs["headers"]

def prueba_cliente_contenido_en_lotes_de_10():
    # 25 salas → 3 solicitudes (10 + 10 + 5)
    respuestas = [RespuestaFalsa(200, {"contenido": [{"sala": i} for i in range(n)]}) for n in (10, 10, 5)]
    cliente, pg, ps = _cliente_con_respuestas(respuestas)
    with pg as get, ps:
        resultado = cliente.obtener_contenido("c1", list(range(1, 26)))
    assert get.call_count == 3, f"hizo {get.call_count} solicitudes"
    assert len(resultado) == 25
    assert cliente.solicitudes_realizadas == 3
    ultima_url = get.call_args.args[0]
    assert ultima_url.endswith("salas=21,22,23,24,25"), ultima_url

def prueba_cliente_catalogo_en_lotes_de_10():
    ids = [f"id{i}" for i in range(12)]
    respuestas = [RespuestaFalsa(200, {"entidades": [{"id": "x"}] * n}) for n in (10, 2)]
    cliente, pg, ps = _cliente_con_respuestas(respuestas)
    with pg as get, ps:
        assert len(cliente.obtener_catalogo(ids)) == 12
    assert get.call_count == 2

def prueba_cliente_salas_pagina_todo():
    respuestas = [RespuestaFalsa(200, {"salas": [{"id": 1}, {"id": 2}], "total_paginas": 3}),
                  RespuestaFalsa(200, {"salas": [{"id": 3}, {"id": 4}], "total_paginas": 3}),
                  RespuestaFalsa(200, {"salas": [{"id": 5}], "total_paginas": 3})]
    cliente, pg, ps = _cliente_con_respuestas(respuestas)
    with pg as get, ps:
        salas = cliente.obtener_salas("c1")
    assert [s["id"] for s in salas] == [1, 2, 3, 4, 5]
    assert get.call_count == 3

def prueba_cliente_reintenta_en_429():
    respuestas = [RespuestaFalsa(429, {"reintentar_en": 2}),
                  RespuestaFalsa(200, {"criptas": [{"id": "c1"}]})]
    cliente, pg, ps = _cliente_con_respuestas(respuestas)
    with pg as get, ps as sleep:
        resultado = cliente.obtener_criptas()
    assert resultado == [{"id": "c1"}]
    sleep.assert_called_once_with(2)
    assert cliente.solicitudes_realizadas == 2, "el reintento también cuenta como solicitud"

def prueba_cliente_error_lanza_runtimeerror():
    for codigo in (400, 404, 500):
        cliente, pg, ps = _cliente_con_respuestas([RespuestaFalsa(codigo, {})])
        with pg, ps:
            try:
                cliente.obtener_criptas()
            except RuntimeError as e:
                assert str(codigo) in str(e)
                continue
        raise AssertionError(f"el código {codigo} debía lanzar RuntimeError")

def prueba_cliente_versiones():
    cliente, pg, ps = _cliente_con_respuestas([RespuestaFalsa(200, {"id": "c1", "version": "v7"}),
                                               RespuestaFalsa(200, {"version": "cat-3"})])
    with pg, ps:
        assert cliente.obtener_version_cripta("c1") == "v7"
        assert cliente.obtener_version_catalogo() == "cat-3"


# ======================================================================
# 5) Pruebas contra la API REAL (solo con --live)
# ======================================================================
def prueba_live_flujo_completo():
    cliente = ClienteCripta(BASE_URL)
    cache = CacheLRU(25)

    criptas = cliente.obtener_criptas()
    assert len(criptas) > 0, "la API no devolvió criptas"
    cripta_id = criptas[0]["id"]

    assert isinstance(cliente.obtener_version_cripta(cripta_id), str)
    assert isinstance(cliente.obtener_version_catalogo(), str)

    salas = cliente.obtener_salas(cripta_id)
    assert len(salas) == criptas[0]["salas"], f"salas: {len(salas)} vs anunciadas {criptas[0]['salas']}"

    # Recorre todas las salas con resolver_sala: nada debe fallar
    comportamientos = []
    total_enemigos = total_objetos = total_trampas = 0
    for sala in salas:
        numero = sala["id"] if "id" in sala else sala["sala"]
        enemigos, objetos, trampas = resolver_sala(cliente, cache, cripta_id, numero)
        total_enemigos += len(enemigos); total_objetos += len(objetos); total_trampas += len(trampas)
        for e in enemigos:
            assert 0 < e.vida_actual <= e.vida_max, f"vida rara en {e.id_instancia}: {e.vida_actual}/{e.vida_max}"
            if e.comportamiento not in comportamientos:
                comportamientos.append(e.comportamiento)

    print(f"      salas={len(salas)} enemigos={total_enemigos} objetos={total_objetos} trampas={total_trampas}")
    print(f"      comportamientos vistos: {comportamientos}")
    print(f"      solicitudes HTTP realizadas: {cliente.solicitudes_realizadas}")
    for c in comportamientos:
        assert c in ("guardián", "errante", "rastreador"), f"comportamiento inesperado: {c!r}"

    # Segunda pasada sobre una sala: cuánto cuesta ahora (informativo)
    antes = cliente.solicitudes_realizadas
    resolver_sala(cliente, cache, cripta_id, salas[0].get("id", salas[0].get("sala")))
    print(f"      repetir 1 sala costó {cliente.solicitudes_realizadas - antes} solicitudes (contenido siempre se pide; fichas, solo si no están en caché)")


# ======================================================================
# Ejecutor
# ======================================================================
def ejecutar(pruebas):
    ok = fallos = 0
    for prueba in pruebas:
        nombre = prueba.__name__
        try:
            prueba()
            print(f"  OK     {nombre}")
            ok += 1
        except Exception as error:
            print(f"  FALLO  {nombre}: {error!r}")
            if "-v" in sys.argv:
                traceback.print_exc()
            fallos += 1
    return ok, fallos


if __name__ == "__main__":
    offline = [f for n, f in sorted(globals().items(), key=lambda kv: kv[1].__code__.co_firstlineno if callable(kv[1]) and hasattr(kv[1], "__code__") else 0)
               if n.startswith("prueba_") and not n.startswith("prueba_live")]
    print(f"\n== Pruebas OFFLINE ({len(offline)}) ==")
    ok, fallos = ejecutar(offline)

    if "--live" in sys.argv:
        print("\n== Pruebas LIVE (API real) ==")
        o2, f2 = ejecutar([prueba_live_flujo_completo])
        ok += o2; fallos += f2

    print(f"\nResultado: {ok} OK, {fallos} con fallo")
    sys.exit(1 if fallos else 0)