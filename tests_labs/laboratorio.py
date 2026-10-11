from adaptadores.resolucion import resolver_objeto, resolver_enemigo, resolver_ficha_enemigo, resolver_sala
from adaptadores.cache import CacheLRU
from adaptadores.cliente_http import ClienteCripta


def test_resolver_objeto():
    ficha = {"id": "itm_daga", "nombre": "Daga", "clase": "arma", 
            "peso": 2, "valor": 5, "ataque_bonus": 3 
    }
    objeto = resolver_objeto(ficha)

    print(objeto)
    print(type(objeto))
    print(objeto.id_catalogo)
    print(ficha)

# test_resolver_objeto()

def test_resolver_enemigo():
    ficha_rata = {"id": "ent_rata_gigante", "nombre": "Rata gigante", "clase": "enemigo",
              "vida_max": 8, "ataque": 2, "defensa": 1, "velocidad": 5,
              "comportamiento": "errante", "suelta": ["itm_antorcha"]
    }

    ficha = resolver_ficha_enemigo(ficha_rata)

    sana = {"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": None}
    herida = {"instancia": "e-202", "tipo": "ent_rata_gigante", "vida": 3}
    sin_clave = {"instancia": "e-203", "tipo": "ent_rata_gigante"}

    e1 = resolver_enemigo(sana, ficha, 2)
    e2 = resolver_enemigo(herida, ficha, 2)
    e3 = resolver_enemigo(sin_clave, ficha, 2)

    print(e1.vida_actual, e2.vida_actual, e3.vida_actual)
    print(e1.vida_max, e2.vida_max, e3.vida_max)

    e1.suelta.clear()
    print(e2.suelta)
    print(ficha.suelta)

# test_resolver_enemigo()

def test_cache():
    c = CacheLRU(3)
    c.insertar("a", 1)
    c.insertar("b", 2)
    c.insertar("c", 3)

    c.obtener("a")

    c.insertar("d", 4)

    print(c.obtener("a"), c.obtener("b"), c.obtener("c"), c.obtener("d"))

    c2 = CacheLRU(3)
    c2.insertar("a", 1)
    c2.insertar("b", 2)
    c2.insertar("c", 3)

    c2.marcar_en_uso("a") #es la mas vieja pero esta en uso, no se puede desalojar
    c2.insertar("d", 4)

    print(c2.obtener("a"), c2.obtener("b"), c2.obtener("c"), c2.obtener("d"))

# test_cache()

def test_api():
    BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"

    cliente = ClienteCripta(BASE_URL)
    cache = CacheLRU(25)

    cripta_id = cliente.obtener_criptas()[0]["id"]
    print("A) tras listar criptas:", cliente.solicitudes_realizadas)

    resolver_sala(cliente, cache, cripta_id, 2)
    print("B) tras resolver la sala 2:", cliente.solicitudes_realizadas)

    resolver_sala(cliente, cache, cripta_id, 2)
    print("C) tras repetir la sala 2:", cliente.solicitudes_realizadas)

    resolver_sala(cliente, cache, cripta_id, 3)
    print("D) tras resolver la sala 3:", cliente.solicitudes_realizadas)

# test_api()

def numero_de_sala(sala: dict) -> int:
    return sala["id"] if "id" in sala else sala["sala"]

def test_todo(limite_salas=5):
    BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
    cliente = ClienteCripta(BASE_URL)
    cache = CacheLRU(25)

    cripta_id = cliente.obtener_criptas()[0]["id"] #esta es la cripta total
    salas = cliente.obtener_salas(cripta_id)
    print(f"La cripta {cripta_id} tiene {len(salas)} salas.")

    # Resolver todas las salas de la cripta
    for sala in salas[:limite_salas]:
        numero = numero_de_sala(sala)
        enemigos, objetos, trampas = resolver_sala(cliente, cache, cripta_id, numero)

        print(f"\n--- Sala {numero} ---")
        for e in enemigos:
            print(f"Enemigo: {e.id_instancia} ({e.tipo}) "
                  f"en sala {e.id_sala_actual}: "
                  f"vida {e.vida_actual}/{e.vida_max}")

        for o in objetos:
            print(f"Objeto: {o.id_catalogo}: {o.nombre}")

        for t in trampas:
            print(f"Trampa {t.id_catalogo} en sala {numero}: daño {t.daño}")

    print("\nSolicitudes realizadas:", cliente.solicitudes_realizadas)
    

test_todo()

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"

def etapa1():
    cliente = ClienteCripta(BASE_URL)
    cripta_id = cliente.obtener_criptas()[0]["id"]

    contenido = cliente.obtener_contenido(cripta_id, [2])[0]
    colocaciones = contenido["enemigos"]

    print("Contenido de la sala 2:", contenido)
    print("Colocaciones de enemigos:", colocaciones)
    print("Cantidad de enemigos:", len(colocaciones))

    tipos = []
    for col in colocaciones:
        if col["tipo"] not in tipos:
            tipos.append(col["tipo"])

    fichas_crudas = cliente.obtener_catalogo(tipos)

    print("Cantidad de fichas:", len(fichas_crudas))
    for ficha in fichas_crudas:
        print(ficha)

    fichas = []
    for ficha_cruda in fichas_crudas:
        fichas.append(resolver_ficha_enemigo(ficha_cruda))

    enemigos = []
    for col in colocaciones:
        for ficha in fichas:
            if ficha.id == col["tipo"]:
                enemigos.append(resolver_enemigo(col, ficha, 2))
                break

    for e in enemigos:
        print(e.id_instancia, e.nombre, "vida", e.vida_actual, "de", e.vida_max)


    


# etapa1()


























# BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
# #test_catalogo()

# cliente = ClienteCripta(BASE_URL)
# cripta_id = cliente.obtener_criptas()[0]["id"]

# # info = cliente.obtener_datos_generales(cripta_id)
# salas = cliente.obtener_salas(cripta_id)

# contenido = cliente.obtener_contenido(cripta_id, [2])[0]
# print("Contenido de la sala 2:", contenido)

# colocaciones = contenido["enemigos"]
# print("Colocaciones:", colocaciones)

# tipos = []
# for col in colocaciones:
#     if col["tipo"] not in tipos:
#         tipos.append(col["tipo"])
# print("Tipos distintos:", tipos)

# fichas_crudas = cliente.obtener_catalogo(tipos)
# fichas = []
# for ficha_cruda in fichas_crudas:
#     fichas.append(resolver_ficha_enemigo(ficha_cruda))

# enemigos = []
# for col in colocaciones:
#     for ficha in fichas:
#         if ficha.id == col["tipo"]:
#             enemigos.append(resolver_enemigo(col, ficha, 2))
#             break

# for e in enemigos:
#     print(f"{e.id_instancia} {e.nombre}: vida {e.vida_actual}/{e.vida_max}")
# print("Solicitudes:", cliente.solicitudes_realizadas)


# ids = []
# for e in contenido["enemigos"]:
#     if e["tipo"] not in ids:
#         ids.append(e["tipo"])
# for o in contenido["objetos"]:
#     if o not in ids:
#         ids.append(o)
# for t in contenido["trampas"]:
#     if t["tipo"] not in ids:
#         ids.append(t["tipo"])
# print("Ids que necesito:", ids)

# fichas = cliente.obtener_catalogo(ids)
# for ficha in fichas:
#     print(ficha["id"], "->", ficha["clase"])

# v_cripta = cliente.obtener_version_cripta(cripta_id)
# v_catalogo = cliente.obtener_version_catalogo()
# print("Versión de la cripta:", repr(v_cripta))
# print("Versión del catálogo:", repr(v_catalogo))

# # ¿La versión cambia si la vuelvo a pedir?
# print("¿Igual al repetir?", cliente.obtener_version_cripta(cripta_id) == v_cripta)