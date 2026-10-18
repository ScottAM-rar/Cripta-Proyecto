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
    

#test_todo()

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


# =============================================================================
# EXPLORACION COMPLETA DE LA API REAL (todas las criptas)
#
# Recorre TODAS las criptas y muestra, tal como llega de la API: los datos
# generales, el esqueleto de las salas, el contenido de cada sala y la ficha de
# catalogo de todo lo que aparece (enemigos, objetos, trampas y lo que sueltan).
# Al final hace un resumen para responder, por ejemplo, si existen enemigos que
# regeneran vida o trampas con veneno (§2.10).
#
# No usa cache, disco ni el modelo: habla directo con ClienteCripta. Solo hace
# GET, asi que no cambia nada en el servidor.
#
# Como correrlo (desde la raiz del repo):
#     py -m tests_labs.laboratorio --catalogo
#     py -m tests_labs.laboratorio --catalogo --salida api_completa.txt
#     py -m tests_labs.laboratorio --catalogo --resumen --salida api_completa.txt
# Sin --catalogo este archivo hace lo de siempre.
# =============================================================================

# Palabras que delatan veneno o regeneracion en cualquier clave o texto
PALABRAS_VENENO_REGENERACION = ("regen", "venen", "poison", "toxic")

# Campos que el enunciado documenta para cada clase de ficha (§2.7 y §3).
# Lo que aparezca fuera de esta lista se reporta como "campo no documentado".
CAMPOS_DOCUMENTADOS = (
    ("enemigo", ("id", "clase", "nombre", "vida_max", "ataque", "defensa", "velocidad", "comportamiento", "suelta")),
    ("trampa", ("id", "clase", "nombre", "daño", "rearme")),
    ("arma", ("id", "clase", "nombre", "peso", "valor", "ataque_bonus")),
    ("armadura", ("id", "clase", "nombre", "peso", "valor", "defensa_bonus")),
    ("pocion", ("id", "clase", "nombre", "peso", "valor", "cura", "modificador_velocidad", "duracion")),
    ("antidoto", ("id", "clase", "nombre", "peso", "valor")),
    ("llave", ("id", "clase", "nombre", "peso", "valor", "abre")),
    ("antorcha", ("id", "clase", "nombre", "peso", "valor", "duracion")),
    ("pergamino_retroceso", ("id", "clase", "nombre", "peso", "valor")),
)

# Lo mismo para los datos que no son fichas de catalogo
CAMPOS_ESTRUCTURA = (
    ("cripta (lista)", ("id", "nombre", "salas", "dificultad")),
    ("datos generales de la cripta", ("id", "version", "salas_total", "paginas", "salas_por_pagina", "sala_inicial",
                                      "sala_salida", "llave_salida", "presupuesto_solicitudes", "inventario_max", "jugador")),
    ("jugador (datos generales)", ("vida_max", "ataque", "defensa", "velocidad")),
    ("sala (esqueleto)", ("id", "nombre", "salidas")),
    ("salida (esqueleto)", ("sala", "cerrada", "llave", "cierre_automatico")),
    ("contenido de sala", ("sala", "enemigos", "objetos", "trampas")),
    ("enemigo colocado", ("instancia", "tipo", "vida")),
    ("trampa colocada", ("instancia", "tipo")),
)

# Claves de la API cuyo valor es (o contiene) ids de catalogo
CLAVES_CON_IDS = ("tipo", "llave", "llave_salida", "suelta", "objetos", "inventario", "arma", "armadura")


def _texto(dato) -> str:
    import json
    return json.dumps(dato, ensure_ascii=False)


class _Salida:
    """Escribe en pantalla y, si se pidio con --salida, tambien en un archivo."""

    def __init__(self, ruta_archivo, solo_resumen):
        self.solo_resumen = solo_resumen
        self.archivo = open(ruta_archivo, "w", encoding="utf-8") if ruta_archivo else None

    def detalle(self, texto=""):
        """Informacion completa. Con --resumen solo va al archivo."""
        if not self.solo_resumen:
            print(texto)
        if self.archivo:
            self.archivo.write(texto + "\n")

    def resumen(self, texto=""):
        print(texto)
        if self.archivo:
            self.archivo.write(texto + "\n")

    def progreso(self, texto):
        print(texto)

    def cerrar(self):
        if self.archivo:
            self.archivo.close()


# ---------- ids de catalogo ----------

def _agregar_id(ids, valor):
    if isinstance(valor, str) and valor != "" and valor not in ids:
        ids.append(valor)


def _recoger_ids(dato, ids):
    """Busca ids de catalogo en cualquier parte de un dato de la API."""
    if isinstance(dato, dict):
        for clave, valor in dato.items():
            if clave in CLAVES_CON_IDS:
                if isinstance(valor, list):
                    for item in valor:
                        _agregar_id(ids, item)
                else:
                    _agregar_id(ids, valor)
            _recoger_ids(valor, ids)
    elif isinstance(dato, list):
        for item in dato:
            _recoger_ids(item, ids)


def _registrar_uso(usos, id_catalogo, cripta_id):
    """usos es una lista de [id, [criptas donde aparece]]."""
    for par in usos:
        if par[0] == id_catalogo:
            if cripta_id not in par[1]:
                par[1].append(cripta_id)
            return
    usos.append([id_catalogo, [cripta_id]])


def _criptas_de(usos, id_catalogo):
    for par in usos:
        if par[0] == id_catalogo:
            return par[1]
    return []


# ---------- descarga del catalogo ----------

def _pedir_catalogo(cliente, ids):
    """Pide las fichas por lotes de 10. Si un lote falla (por ejemplo por un id
    que no existe), reintenta id por id para saber cual fue."""
    from adaptadores.cliente_http import ErrorSinConexion
    fichas = []
    fallidos = []
    for inicio in range(0, len(ids), 10):
        lote = ids[inicio:inicio + 10]
        try:
            fichas.extend(cliente.obtener_catalogo(lote))
        except ErrorSinConexion:
            raise
        except RuntimeError:
            for uno in lote:
                try:
                    fichas.extend(cliente.obtener_catalogo([uno]))
                except ErrorSinConexion:
                    raise
                except RuntimeError as error:
                    fallidos.append(f"{uno}: {error}")
    return fichas, fallidos


def _fue_reportado(fallidos, ident):
    for texto in fallidos:
        if texto.startswith(ident + ":"):
            return True
    return False


def _descargar_catalogo(cliente, ids_iniciales, usos, salida):
    """Descarga las fichas de los ids iniciales y de todo lo que ellas mencionan
    (por ejemplo, lo que suelta un enemigo). Devuelve (fichas, ids_sin_ficha)."""
    fichas = []
    pedidos = []
    sin_ficha = []
    pendientes = list(ids_iniciales)
    ronda = 0
    while pendientes and ronda < 5:
        ronda += 1
        salida.progreso(f"Catalogo, ronda {ronda}: pidiendo {len(pendientes)} ids")
        pedidos.extend(pendientes)
        nuevas, fallidos = _pedir_catalogo(cliente, pendientes)
        sin_ficha.extend(fallidos)
        recibidos = []
        for ficha in nuevas:
            recibidos.append(ficha.get("id"))
        for ident in pendientes:
            if ident not in recibidos and not _fue_reportado(fallidos, ident):
                sin_ficha.append(f"{ident}: la API no devolvio su ficha")
        fichas.extend(nuevas)
        pendientes = []
        for ficha in nuevas:
            mencionados = []
            _recoger_ids(ficha, mencionados)
            for ident in mencionados:
                for cripta_id in _criptas_de(usos, ficha.get("id")):
                    _registrar_uso(usos, ident, cripta_id)
                if ident not in pedidos and ident not in pendientes:
                    pendientes.append(ident)
    return fichas, sin_ficha


# ---------- campos no documentados y palabras clave ----------

def _campos_documentados(clase):
    for nombre, campos in CAMPOS_DOCUMENTADOS:
        if nombre == clase:
            return campos
    return None


def _anotar_extras(extras, estructura, dato):
    """Anota los campos de `dato` que el enunciado no documenta para esa estructura.
    extras es una lista de [estructura, campo, ejemplo, cuantas_veces]."""
    if not isinstance(dato, dict):
        return
    for nombre, campos in CAMPOS_ESTRUCTURA:
        if nombre != estructura:
            continue
        for clave in dato.keys():
            if clave in campos:
                continue
            for registro in extras:
                if registro[0] == estructura and registro[1] == clave:
                    registro[3] += 1
                    break
            else:
                extras.append([estructura, clave, _texto(dato[clave]), 1])


def _tiene_palabra(texto) -> bool:
    minusculas = str(texto).lower()
    for palabra in PALABRAS_VENENO_REGENERACION:
        if palabra in minusculas:
            return True
    return False


def _buscar_palabras(dato, ruta, hallazgos):
    """Anota (ruta, valor) donde una clave o un texto menciona veneno o regeneracion."""
    if isinstance(dato, dict):
        for clave, valor in dato.items():
            subruta = f"{ruta}.{clave}" if ruta else str(clave)
            if _tiene_palabra(clave):
                hallazgos.append((subruta, valor))
            _buscar_palabras(valor, subruta, hallazgos)
    elif isinstance(dato, list):
        for i, item in enumerate(dato):
            _buscar_palabras(item, f"{ruta}[{i}]", hallazgos)
    elif isinstance(dato, str):
        if _tiene_palabra(dato):
            hallazgos.append((ruta, dato))


def _agrupar_por_clase(fichas):
    """Devuelve una lista de [clase, [fichas]]."""
    grupos = []
    for ficha in fichas:
        clase = ficha.get("clase", "(sin clase)")
        for grupo in grupos:
            if grupo[0] == clase:
                grupo[1].append(ficha)
                break
        else:
            grupos.append([clase, [ficha]])
    return sorted(grupos, key=lambda grupo: grupo[0])


def _contar_campos(fichas):
    """Devuelve una lista de [campo, en_cuantas_fichas_aparece]."""
    conteo = []
    for ficha in fichas:
        for clave in ficha.keys():
            for par in conteo:
                if par[0] == clave:
                    par[1] += 1
                    break
            else:
                conteo.append([clave, 1])
    return conteo


# ---------- recorrido ----------

def _explorar_cripta(cliente, cripta, ids, usos, material, extras, salida):
    cid = cripta["id"]
    salida.progreso(f"Cripta {cid}: pidiendo datos generales, salas y contenido")
    salida.detalle("")
    salida.detalle("#" * 72)
    salida.detalle(f"CRIPTA {cid}")
    salida.detalle("#" * 72)
    salida.detalle("En la lista de criptas: " + _texto(cripta))

    datos = cliente.obtener_datos_generales(cid)
    salida.detalle("Datos generales: " + _texto(datos))
    salida.detalle("Version de la cripta: " + repr(cliente.obtener_version_cripta(cid)))

    salas = cliente.obtener_salas(cid)
    salida.detalle("")
    salida.detalle(f"Esqueleto: {len(salas)} salas")
    for sala in salas:
        salida.detalle("  " + _texto(sala))

    numeros = [numero_de_sala(sala) for sala in salas]
    contenidos = cliente.obtener_contenido(cid, numeros)
    salida.detalle("")
    salida.detalle(f"Contenido: {len(contenidos)} salas")
    for contenido in contenidos:
        salida.detalle("  " + _texto(contenido))

    encontrados = []
    _recoger_ids(datos, encontrados)
    _recoger_ids(salas, encontrados)
    _recoger_ids(contenidos, encontrados)
    for ident in encontrados:
        _agregar_id(ids, ident)
        _registrar_uso(usos, ident, cid)
    salida.detalle("")
    salida.detalle(f"Ids de catalogo que aparecen en {cid} ({len(encontrados)}): " + ", ".join(encontrados))

    _anotar_extras(extras, "cripta (lista)", cripta)
    _anotar_extras(extras, "datos generales de la cripta", datos)
    _anotar_extras(extras, "jugador (datos generales)", datos.get("jugador"))
    for sala in salas:
        _anotar_extras(extras, "sala (esqueleto)", sala)
        salidas = sala.get("salidas") or {}
        for una in (salidas.values() if isinstance(salidas, dict) else salidas):
            _anotar_extras(extras, "salida (esqueleto)", una)
    for contenido in contenidos:
        _anotar_extras(extras, "contenido de sala", contenido)
        for enemigo in contenido.get("enemigos", []):
            _anotar_extras(extras, "enemigo colocado", enemigo)
        for trampa in contenido.get("trampas", []):
            _anotar_extras(extras, "trampa colocada", trampa)

    material.append((f"{cid} datos generales", datos))
    material.append((f"{cid} esqueleto", salas))
    material.append((f"{cid} contenido", contenidos))


def _imprimir_catalogo(salida, fichas, usos):
    salida.detalle("")
    salida.detalle("=" * 72)
    salida.detalle(f"CATALOGO (union de todas las criptas): {len(fichas)} fichas")
    salida.detalle("=" * 72)
    for clase, lista in _agrupar_por_clase(fichas):
        salida.detalle("")
        salida.detalle(f"--- clase {clase} ({len(lista)}) ---")
        for ficha in lista:
            salida.detalle(f"  {ficha.get('id')}   [en: {', '.join(_criptas_de(usos, ficha.get('id')))}]")
            salida.detalle("    " + _texto(ficha))


def _imprimir_resumen(salida, version_catalogo, criptas, fichas, sin_ficha, usos, material, extras, cliente, segundos):
    salida.resumen("")
    salida.resumen("=" * 72)
    salida.resumen("RESUMEN")
    salida.resumen("=" * 72)
    salida.resumen(f"Version del catalogo: {version_catalogo!r}")

    salida.resumen("")
    salida.resumen(f"1) Criptas ({len(criptas)})")
    for cripta in criptas:
        salida.resumen("   " + _texto(cripta))

    grupos = _agrupar_por_clase(fichas)
    salida.resumen("")
    salida.resumen(f"2) Fichas del catalogo por clase (total {len(fichas)})")
    for clase, lista in grupos:
        nombres = ", ".join(str(f.get("id")) for f in lista)
        salida.resumen(f"   {clase} ({len(lista)}): {nombres}")

    salida.resumen("")
    salida.resumen("3) Campos que trae cada clase (entre parentesis, en cuantas fichas aparece)")
    for clase, lista in grupos:
        campos = ", ".join(f"{campo}({n})" for campo, n in _contar_campos(lista))
        salida.resumen(f"   {clase}: {campos}")

    salida.resumen("")
    salida.resumen("4) Campos NO documentados en el enunciado (aqui suelen estar veneno y regeneracion)")
    hubo = False
    for clase, lista in grupos:
        documentados = _campos_documentados(clase)
        if documentados is None:
            salida.resumen(f"   clase '{clase}' no esta descrita en el enunciado: {_texto(lista[0])}")
            hubo = True
            continue
        extras_clase = []
        for ficha in lista:
            for clave in ficha.keys():
                if clave in documentados:
                    continue
                for registro in extras_clase:
                    if registro[0] == clave:
                        registro[2] += 1
                        break
                else:
                    extras_clase.append([clave, f"{ficha.get('id')} = {_texto(ficha[clave])}", 1])
        for clave, ejemplo, veces in extras_clase:
            salida.resumen(f"   ficha de clase {clase}: campo '{clave}' en {veces} ficha(s), p. ej. {ejemplo}")
            hubo = True
    for estructura, clave, ejemplo, veces in extras:
        salida.resumen(f"   {estructura}: campo '{clave}' {veces} vez/veces, p. ej. {ejemplo}")
        hubo = True
    if not hubo:
        salida.resumen("   (ninguno: todo lo que llega esta en el enunciado)")

    salida.resumen("")
    salida.resumen("5) Menciones de veneno / regeneracion (busca: " + ", ".join(PALABRAS_VENENO_REGENERACION) + ")")
    hubo = False
    for ficha in fichas:
        hallazgos = []
        _buscar_palabras(ficha, "", hallazgos)
        for ruta, valor in hallazgos:
            donde = ", ".join(_criptas_de(usos, ficha.get("id")))
            salida.resumen(f"   ficha {ficha.get('id')} [{ficha.get('clase')}] {ruta} = {_texto(valor)}   (en: {donde})")
            hubo = True
    otros = []
    for descripcion, dato in material:
        _buscar_palabras(dato, descripcion, otros)
    for ruta, valor in otros[:15]:
        salida.resumen(f"   {ruta} = {_texto(valor)}")
        hubo = True
    if len(otros) > 15:
        salida.resumen(f"   ... y {len(otros) - 15} menciones mas en datos de cripta / salas / contenido (estan en el detalle)")
    if not hubo:
        salida.resumen("   No hay ninguna clave ni texto con esas palabras. Si la API trae el efecto con otro nombre,")
        salida.resumen("   miralo en los puntos 3 y 4 y en las fichas de enemigo y trampa del punto 6.")

    salida.resumen("")
    salida.resumen("6) Fichas completas de enemigos y trampas")
    for clase, lista in grupos:
        if clase in ("enemigo", "trampa"):
            for ficha in lista:
                salida.resumen(f"   {_texto(ficha)}   (en: {', '.join(_criptas_de(usos, ficha.get('id')))})")

    salida.resumen("")
    salida.resumen(f"7) Ids que la API no devolvio ({len(sin_ficha)})")
    for texto in sin_ficha:
        salida.resumen("   " + texto)
    if not sin_ficha:
        salida.resumen("   (ninguno)")

    salida.resumen("")
    salida.resumen(f"Solicitudes realizadas: {cliente.solicitudes_realizadas} | tiempo: {segundos:.1f} s")


def test_explorar_api(archivo_salida=None, solo_resumen=False):
    import sys
    import time
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")      # que un caracter raro no tumbe el print en la consola de Windows
    salida = _Salida(archivo_salida, solo_resumen)
    inicio = time.perf_counter()
    try:
        cliente = ClienteCripta(BASE_URL)
        version_catalogo = cliente.obtener_version_catalogo()
        criptas = cliente.obtener_criptas()
        salida.progreso(f"La API tiene {len(criptas)} criptas")

        ids = []          # ids de catalogo que aparecen en cualquier cripta
        usos = []         # [id, [criptas donde aparece]]
        material = []     # (descripcion, dato) de todo lo que vino de las criptas
        extras = []       # campos no documentados en datos de cripta, salas y contenido
        for cripta in criptas:
            _explorar_cripta(cliente, cripta, ids, usos, material, extras, salida)

        fichas, sin_ficha = _descargar_catalogo(cliente, ids, usos, salida)
        _imprimir_catalogo(salida, fichas, usos)
        _imprimir_resumen(salida, version_catalogo, criptas, fichas, sin_ficha, usos, material, extras,
                          cliente, time.perf_counter() - inicio)
    finally:
        salida.cerrar()
    if archivo_salida:
        print(f"\nTodo lo anterior tambien se guardo en {archivo_salida}")


def _leer_opciones_de_consola():
    import argparse
    parser = argparse.ArgumentParser(description="Exploracion completa de la API real de Cripta")
    parser.add_argument("--catalogo", action="store_true",
                        help="recorre todas las criptas, sus salas y el catalogo de lo que aparece en ellas")
    parser.add_argument("--salida", metavar="ARCHIVO.txt",
                        help="guarda ademas todo lo que se imprime en este archivo")
    parser.add_argument("--resumen", action="store_true",
                        help="en pantalla solo el resumen (el detalle completo va al archivo de --salida)")
    opciones, _ = parser.parse_known_args()
    return opciones


_opciones = _leer_opciones_de_consola()
if _opciones.catalogo:
    try:
        test_explorar_api(_opciones.salida, _opciones.resumen)
    except RuntimeError as error:                    # incluye ErrorSinConexion y el 429 que no cede
        print(f"\nNo se pudo completar la exploracion: {error}")
        raise SystemExit(1)
    raise SystemExit(0)


etapa1()


























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