"""API falsa y ayudas compartidas por las pruebas de persistencia y offline."""
import random

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.llaves import LlavesInvalidas
from adaptadores.servicioCripta import ServicioCripta
from Logica.FuenteCripta import LlavesNoDisponibles
from tests_labs.cripta_sintetica import esqueleto_rejilla, ficha_cazador
 
# Llaves de la cripta de 3 salas de HttpFalso (capacidad 009): una en el suelo de la sala 1 y la llave de salida,
# que la suelta e-301 en la sala 3. Es la lista ya extraída, como la entrega el HTTP real después de leer_llaves.
LLAVES_FALSAS = [{"id": "itm_llave_bronce", "sala": 1}, {"id": "itm_llave_negra", "sala": 3, "enemigo": "e-301"}]
 
 
class HttpFalso:
    """Imita a ClienteCripta y apunta cada solicitud que se le hace."""
 
    def __init__(self, version_cripta="c1", version_catalogo="k1", datos_con_version=True):
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.datos_con_version = datos_con_version
        self.llamadas = []                       # [(nombre, argumento), ...]
 
    @property
    def solicitudes_realizadas(self):
        return len(self.llamadas)
 
    def veces(self, nombre):
        total = 0
        for llamada in self.llamadas:
            if llamada[0] == nombre:
                total += 1
        return total
 
    def nombres(self):
        lista = []
        for llamada in self.llamadas:
            if llamada[0] not in lista:
                lista.append(llamada[0])
        return lista
 
    def obtener_criptas(self):
        self.llamadas.append(("criptas", None))
        return [{"id": "cripta-01", "nombre": "Osario menor", "salas": 3, "dificultad": 1}]
 
    def obtener_datos_generales(self, cripta_id):
        self.llamadas.append(("datos", cripta_id))
        datos = {"id": cripta_id, "salas_total": 3, "sala_inicial": 1, "sala_salida": 3,
                 "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 9,
                 "inventario_max": 10,
                 "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}
        if self.datos_con_version:
            datos["version"] = self.version_cripta
        return datos
 
    def obtener_version_cripta(self, cripta_id):
        self.llamadas.append(("version_cripta", cripta_id))
        return self.version_cripta
 
    def obtener_salas(self, cripta_id):
        self.llamadas.append(("salas", cripta_id))
        return [
            {"id": 1, "nombre": "Entrada derruida", "salidas": {"N": {"sala": 2}}},
            {"id": 2, "nombre": "Pasillo de las urnas",
             "salidas": {"S": {"sala": 1}, "N": {"sala": 3}}},
            {"id": 3, "nombre": "Salida", "salidas": {"S": {"sala": 2}}},
        ]
 
    def obtener_contenido(self, cripta_id, salas):
        self.llamadas.append(("contenido", list(salas)))
        contenidos = []
        for numero in salas:
            if numero == 2:
                enemigos = [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": None},
                            {"instancia": "e-202", "tipo": "ent_rata_gigante"}]
            elif numero == 3:
                enemigos = [{"instancia": "e-301", "tipo": "ent_guardian_oseo", "vida": 15}]
            else:
                enemigos = []
            contenidos.append({"sala": numero, "enemigos": enemigos, "objetos": [], "trampas": []})
        return contenidos
 
    def obtener_version_catalogo(self):
        self.llamadas.append(("version_catalogo", None))
        return self.version_catalogo
 
    def obtener_catalogo(self, ids):
        self.llamadas.append(("catalogo", list(ids)))
        fichas = [
            {"id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante", "vida_max": 12,
             "ataque": 5, "defensa": 1, "velocidad": 150, "comportamiento": "rastreador",
             "suelta": ["itm_pocion_menor"]},
            {"id": "ent_guardian_oseo", "clase": "enemigo", "nombre": "Guardián óseo", "vida_max": 20,
             "ataque": 7, "defensa": 3, "velocidad": 80, "comportamiento": "guardián", "suelta": []},
            {"id": "itm_pocion_menor", "clase": "pocion", "nombre": "Poción menor", "peso": 1, "valor": 10,
             "cura": 8, "modificador_velocidad": 0, "duracion": 0},
        ]
        devueltas = []
        for ficha in fichas:
            if ficha["id"] in ids:
                devueltas.append(ficha)
        return devueltas
 
    def obtener_llaves(self, cripta_id, solo_guardadas=False, limite_solicitudes=None):
        """GET /criptas/<id>/llaves (capacidad 009). Cuenta como una solicitud. Con solo_guardadas imita al
        ClienteCripta real, que no tiene disco: falla sin hacer (ni registrar) la solicitud."""
        if solo_guardadas:
            raise LlavesNoDisponibles(f"no queda presupuesto y no hay llaves guardadas de la cripta {cripta_id}")
        self.llamadas.append(("llaves", cripta_id))
        return [dict(llave) for llave in LLAVES_FALSAS]
 
 
class HttpConfigurable(HttpFalso):
    """HttpFalso con la cripta definida por la prueba: esqueleto, enemigos por sala y fichas extra.

    `salas`: lista de salas del esqueleto, como las entrega la API (cada salida admite "costo").
    `enemigos`: lista de tuplas (sala, instancia, tipo, vida o None).
    `fichas`: fichas de catálogo adicionales (p. ej. un cazador con "rango").
    `llaves`: lista de tuplas (id, sala, enemigo o None); con None se usan las de HttpFalso (capacidad 009).
    `fallo_llaves`: None, "sin_respuesta" (ErrorSinConexion) o "invalida" (LlavesInvalidas). La llamada se
    registra igual en los dos fallos.
    `llave_salida`: id de la llave de salida de los datos generales; con None se usa la de HttpFalso.
    `objetos`: lista de tuplas (sala, id de catálogo) de objetos en el suelo; con None no hay objetos.
    """

    def __init__(self, salas, enemigos=None, fichas=None, sala_inicial=1, sala_salida=None, vida_jugador=5000,
                 llaves=None, fallo_llaves=None, llave_salida=None, objetos=None, **versiones):
        super().__init__(**versiones)
        self.llave_salida = llave_salida
        self.objetos = [] if objetos is None else objetos
        if fallo_llaves not in (None, "sin_respuesta", "invalida"):
            raise ValueError(f"fallo_llaves desconocido: {fallo_llaves!r}")
        self.llaves = llaves
        self.fallo_llaves = fallo_llaves
        self.salas = salas
        self.enemigos = [] if enemigos is None else enemigos
        self.fichas = [] if fichas is None else fichas
        self.sala_inicial = sala_inicial
        self.sala_salida = sala_salida if sala_salida is not None else salas[-1]["id"]
        self.vida_jugador = vida_jugador

    def obtener_criptas(self):
        self.llamadas.append(("criptas", None))
        return [{"id": "cripta-01", "nombre": "Cripta de prueba", "salas": len(self.salas), "dificultad": 1}]

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["salas_total"] = len(self.salas)
        datos["sala_inicial"] = self.sala_inicial
        datos["sala_salida"] = self.sala_salida
        datos["jugador"]["vida_max"] = self.vida_jugador
        if self.llave_salida is not None:
            datos["llave_salida"] = self.llave_salida
        return datos

    def obtener_salas(self, cripta_id):
        self.llamadas.append(("salas", cripta_id))
        return self.salas

    def obtener_contenido(self, cripta_id, salas):
        self.llamadas.append(("contenido", list(salas)))
        contenidos = []
        for numero in salas:
            colocados = []
            for sala, instancia, tipo, vida in self.enemigos:
                if sala == numero:
                    colocados.append({"instancia": instancia, "tipo": tipo, "vida": vida})
            en_el_suelo = []
            for sala, id_objeto in self.objetos:
                if sala == numero:
                    en_el_suelo.append(id_objeto)
            contenidos.append({"sala": numero, "enemigos": colocados, "objetos": en_el_suelo, "trampas": []})
        return contenidos

    def obtener_catalogo(self, ids):
        devueltas = super().obtener_catalogo(ids)
        for ficha in self.fichas:
            if ficha["id"] in ids:
                devueltas.append(ficha)
        return devueltas

    def obtener_llaves(self, cripta_id, solo_guardadas=False, limite_solicitudes=None):
        if solo_guardadas:
            raise LlavesNoDisponibles(f"no queda presupuesto y no hay llaves guardadas de la cripta {cripta_id}")
        self.llamadas.append(("llaves", cripta_id))
        if self.fallo_llaves == "sin_respuesta":
            # Import diferido, como en fabrica: cliente_http importa requests y la API falsa no debe exigirlo.
            from adaptadores.cliente_http import ErrorSinConexion
            raise ErrorSinConexion(f"No se pudo conectar para pedir las llaves de la cripta {cripta_id}")
        if self.fallo_llaves == "invalida":
            raise LlavesInvalidas("respuesta sin llaves")
        if self.llaves is None:
            return [dict(llave) for llave in LLAVES_FALSAS]
        lista = []
        for id_llave, sala, enemigo in self.llaves:
            entrada = {"id": id_llave, "sala": sala}
            if enemigo is not None:
                entrada["enemigo"] = enemigo
            lista.append(entrada)
        return lista


def nueva_ejecucion(carpeta, **versiones):
    """Simula abrir el juego: cliente falso nuevo, almacén nuevo, servicio nuevo."""
    http = HttpFalso(**versiones)
    cliente = ClientePersistente(http, AlmacenDisco(carpeta))
    servicio = ServicioCripta(cliente, CacheLRU(25))
    return http, cliente, servicio
 
 
def cargar_todo(servicio):
    """Lo que hace el juego al arrancar."""
    servicio.listar_criptas()
    cid = servicio.obtener_id_cripta(1)
    servicio.crear_jugador(cid)
    return servicio.construir_todas(cid)


def _ficha_llave(id_llave):
    return {"id": id_llave, "clase": "llave", "nombre": id_llave, "peso": 1, "valor": 0, "abre": ""}


def _sala_mas_lejana(salas, origen=1):
    """Sala a más salidas de distancia de `origen` (la de menor id si empatan). Recorrido por niveles con dos
    listas (sin deque ni dict): `distancia[id]` es -1 mientras la sala no se alcanzó."""
    mayor = 0
    for sala in salas:
        if sala["id"] > mayor:
            mayor = sala["id"]
    por_id = [None] * (mayor + 1)
    for sala in salas:
        por_id[sala["id"]] = sala
    distancia = [-1] * (mayor + 1)
    distancia[origen] = 0
    nivel = [origen]
    lejana = origen
    while nivel:
        siguiente = []
        for numero in nivel:
            for letra in ("N", "S", "E", "O"):
                salida = por_id[numero]["salidas"].get(letra)
                if salida is not None and distancia[salida["sala"]] < 0:
                    distancia[salida["sala"]] = distancia[numero] + 1
                    siguiente.append(salida["sala"])
        if siguiente:
            lejana = siguiente[0]
            for numero in siguiente:
                if numero < lejana:
                    lejana = numero
        nivel = siguiente
    return lejana


def cripta_v2(semilla: int = 0) -> HttpConfigurable:
    """Cripta de prueba v2 (capacidad 009, FR-319): rejilla 5x5 con costos (costo_max=9), un cazador de rango 600 en
    la sala más lejana de la 1, la llave de salida soltada por el cazador, una llave en el suelo y otra llave con el
    mismo id en dos salas distintas. Todo sale de random.Random(semilla): la misma semilla da las mismas respuestas."""
    azar = random.Random(semilla)
    salas = esqueleto_rejilla(5, 5, semilla, costo_max=9)
    lejana = _sala_mas_lejana(salas, 1)
    llave_salida = "itm_llave_salida"
    cazador = ficha_cazador(rango=600)
    cazador["suelta"] = [llave_salida]

    candidatas = []
    for sala in salas:
        if sala["id"] != 1 and sala["id"] != lejana:
            candidatas.append(sala["id"])
    elegidas = azar.sample(candidatas, 3)
    sala_bronce = elegidas[0]
    salas_plata = [elegidas[1], elegidas[2]]

    llaves = [(llave_salida, lejana, "e-cazador"),
              ("itm_llave_bronce", sala_bronce, None),
              ("itm_llave_plata", salas_plata[0], None),
              ("itm_llave_plata", salas_plata[1], None)]
    objetos = [(sala_bronce, "itm_llave_bronce"), (salas_plata[0], "itm_llave_plata"),
               (salas_plata[1], "itm_llave_plata")]
    fichas = [cazador, _ficha_llave(llave_salida), _ficha_llave("itm_llave_bronce"), _ficha_llave("itm_llave_plata")]
    return HttpConfigurable(salas, [(lejana, "e-cazador", "ent_cazador", None)], fichas, sala_inicial=1,
                            sala_salida=lejana, llaves=llaves, llave_salida=llave_salida, objetos=objetos)


# ======================================================================================================================
# Casos del Apéndice B (capacidad 009, FR-320; contracts/api-falsa-v2.md)
#
# CASOS_APENDICE_B es una lista de tuplas (código, descripción literal de la tabla, constructor). Cada constructor no
# recibe argumentos y devuelve (HttpConfigurable, guion): la cripta que arma la situación y la lista de pasos que la
# provocan. Es determinista (no hay azar: dos construcciones dan las mismas respuestas) y no usa red. Esta capacidad
# solo ofrece la situación reproducible; quien escribe el escenario (dueño de 001 a 004 y 010) ejecuta el guion.
#
# Vocabulario de pasos del guion (PASOS_GUION). Solo "mover" y "esperar" se ejecutan hoy (como en
# tests_labs/escenarios_terreno.py); los demás nombran algo que implementa otra capacidad o un cambio durante la
# partida, y esta capacidad NO los ejecuta:
#   ("mover", dirección)              el jugador sale por "norte", "sur", "este" u "oeste".
#   ("esperar", veces)                el jugador espera `veces` turnos.
#   ("recoger", id_catálogo)          el jugador recoge ese objeto del suelo de su sala (acción de la Parte I).
#   ("ir_a", sala)                    orden «ir a <sala>» (capacidad 002).
#   ("antorcha",)                     el jugador enciende la antorcha que lleva (capacidad 002).
#   ("pergamino",)                    el jugador usa el pergamino de retroceso que lleva.
#   ("pergamino_en_viaje", pasos)     usa el pergamino cuando el último «ir a» lleva `pasos` pasos (capacidad 002).
#   ("cerrar_puerta", sala, dirección) la salida de `sala` en esa dirección se cierra durante la partida (en los dos
#                                     sentidos); lo provoca la prueba, no el jugador.
#   ("cambiar_velocidad", instancia, velocidad)  cambia la velocidad del actor ("jugador" o la instancia de un
#                                     enemigo) en ese momento; lo provoca la prueba.
#   ("historia", t)                   comando «historia <t>»; t None = «historia» sin argumento (capacidad 004).
#   ("replay_hasta", t)               «--replay partida.log --hasta t» con el log de la partida jugada (capacidad 004).
#   ("verificar",)                    verificación de resolubilidad de la cripta (capacidad 003).
#   ("iniciar_sin_forzar",)           iniciar la partida sin «--forzar» (capacidad 003).
#   ("cargar_partida", ruta)          cargar el archivo de partida de esa ruta (capacidades 004 y 010).
# ======================================================================================================================
from tests_labs.cripta_sintetica import ficha_enemigo  # noqa: E402  (solo la usan los casos)

PASOS_GUION = ("mover", "esperar", "recoger", "ir_a", "antorcha", "pergamino", "pergamino_en_viaje", "cerrar_puerta",
               "cambiar_velocidad", "historia", "replay_hasta", "verificar", "iniciar_sin_forzar", "cargar_partida")

LLAVE_SALIDA_CASOS = "itm_llave_salida"
ANTORCHA = "itm_antorcha"
PERGAMINO = "itm_pergamino"
SALIDA_INEXISTENTE_CASOS = 1000      # como en escenarios_terreno: la partida no termina por llegar a una sala final


class HttpCaso(HttpConfigurable):
    """HttpConfigurable que además pone trampas en el contenido. `trampas`: lista de tuplas (sala, instancia, tipo)."""

    def __init__(self, *args, trampas=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trampas = [] if trampas is None else trampas

    def obtener_contenido(self, cripta_id, salas):
        contenidos = super().obtener_contenido(cripta_id, salas)
        for contenido in contenidos:
            for sala, instancia, tipo in self.trampas:
                if sala == contenido["sala"]:
                    contenido["trampas"].append({"instancia": instancia, "tipo": tipo})
        return contenidos


def _ficha_objeto(id_objeto, clase, **campos):
    ficha = {"id": id_objeto, "clase": clase, "nombre": id_objeto, "peso": 1, "valor": 0}
    for nombre, valor in campos.items():
        ficha[nombre] = valor
    return ficha


def _fichas_de_objetos(ids):
    """Fichas de catálogo de los objetos sueltos que usan los casos (llaves, antorcha, pergamino)."""
    fichas = []
    for id_objeto in ids:
        if id_objeto == ANTORCHA:
            fichas.append(_ficha_objeto(ANTORCHA, "antorcha", duracion=300))
        elif id_objeto == PERGAMINO:
            fichas.append(_ficha_objeto(PERGAMINO, "pergamino_retroceso"))
        else:
            fichas.append(_ficha_llave(id_objeto))
    return fichas


def _caso(salas, enemigos=(), fichas=(), suelo=(), soltadas=(), trampas=(), sala_inicial=1, sala_salida=None,
          llave_salida=LLAVE_SALIDA_CASOS):
    """Arma la cripta del caso con /llaves coherente con el contenido:
    `suelo`: (id, sala) de objetos en el suelo; si el id es una llave, aparece en /llaves sin enemigo.
    `soltadas`: (id_llave, instancia): la llave va al `suelta` de la ficha del enemigo y a /llaves con su instancia y
    su sala inicial. `trampas`: (sala, instancia, tipo)."""
    fichas = [dict(ficha, suelta=list(ficha.get("suelta") or [])) for ficha in fichas]
    llaves = []
    objetos = []
    ids_objetos = []
    for id_objeto, sala in suelo:
        objetos.append((sala, id_objeto))
        if id_objeto != ANTORCHA and id_objeto != PERGAMINO:
            llaves.append((id_objeto, sala, None))
        if id_objeto not in ids_objetos:
            ids_objetos.append(id_objeto)
    for id_llave, instancia in soltadas:
        colocacion = [e for e in enemigos if e[1] == instancia][0]
        ficha = [f for f in fichas if f["id"] == colocacion[2]][0]
        ficha["suelta"].append(id_llave)
        llaves.append((id_llave, colocacion[0], instancia))
        if id_llave not in ids_objetos:
            ids_objetos.append(id_llave)
    if trampas:
        fichas.append({"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos", "daño": 3, "rearme": 500})
    fichas = fichas + _fichas_de_objetos(ids_objetos)
    return HttpCaso(salas, list(enemigos), fichas, sala_inicial=sala_inicial, sala_salida=sala_salida,
                    llaves=llaves, llave_salida=llave_salida, objetos=objetos, trampas=list(trampas))


def _puerta_con_llave(salas, a, b, llave):
    """Cierra en los dos sentidos la salida entre las salas a y b y la deja abrible con `llave`."""
    for origen, destino in ((a, b), (b, a)):
        for salida in salas[origen - 1]["salidas"].values():
            if salida["sala"] == destino:
                salida["cerrada"] = True
                salida["llave"] = llave


def _escenario_001(nombre):
    """Esqueleto, enemigos, fichas, sala del jugador y guion de un escenario de tests_labs/escenarios_terreno.py
    (copias: los casos no modifican los originales). Import diferido: escenarios_terreno importa este módulo."""
    import copy
    from tests_labs.escenarios_terreno import ESCENARIOS
    escenario = [e for e in ESCENARIOS if e.nombre == nombre][0]
    return (copy.deepcopy(escenario.esqueleto), list(escenario.enemigos), copy.deepcopy(escenario.fichas),
            escenario.sala_jugador, list(escenario.guion))


def _cazador_en(esqueleto, sala_cazador, sala_jugador, guion, rango=1000, velocidad=100):
    http = _caso(esqueleto, [(sala_cazador, "e-1", "ent_cazador", None)], [ficha_cazador(rango=rango, velocidad=velocidad)],
                 suelo=[(LLAVE_SALIDA_CASOS, sala_jugador)], sala_inicial=sala_jugador,
                 sala_salida=SALIDA_INEXISTENTE_CASOS)
    return http, guion


def _desde_escenario_001(nombre):
    esqueleto, enemigos, fichas, sala_jugador, guion = _escenario_001(nombre)
    http = _caso(esqueleto, enemigos, fichas, suelo=[(LLAVE_SALIDA_CASOS, sala_jugador)], sala_inicial=sala_jugador,
                 sala_salida=SALIDA_INEXISTENTE_CASOS)
    return http, guion


# ---------------------------------------------------------------- Terreno y cazador (B-T, capacidad 001)
def _b_t1():
    # 1 - 2 con la única puerta cerrada: el cazador (sala 2) no tiene ruta abierta hacia el jugador (sala 1).
    from tests_labs.cripta_sintetica import esqueleto_de_conexiones
    esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O", {"cerrada": True})])
    return _cazador_en(esqueleto, 2, 1, [("esperar", 3)])


def _b_t2():
    # Escenario FR112 de la 001: ruta de costo 300 y rango 299.
    return _desde_escenario_001("FR112_fuera_de_rango_espera")


def _b_t3():
    # Del cazador (sala 1) al jugador (sala 2): directo cuesta 500 (1 salida); por 3 y 4 cuesta 150 (3 salidas).
    from tests_labs.cripta_sintetica import esqueleto_de_conexiones
    esqueleto = esqueleto_de_conexiones([(1, 2, 500, "E", "O"), (1, 3, 50, "S", "N"), (3, 4, 50, "E", "O"),
                                         (4, 2, 50, "N", "S")])
    return _cazador_en(esqueleto, 1, 2, [("esperar", 5)])


def _b_t4():
    # Escenario FR114 de la 001: el diamante 1 -> 2 -> 4 y 1 -> 3 -> 4, con rutas de igual costo.
    return _desde_escenario_001("FR114_desempate_por_menor_id")


def _b_t5():
    # 1 - 2 - 3: el cazador (sala 3, lento) va hacia el jugador (sala 1); la puerta 2-1 se cierra entre dos turnos.
    from tests_labs.cripta_sintetica import esqueleto_lineal
    return _cazador_en(esqueleto_lineal([100, 100]), 3, 1,
                       [("esperar", 1), ("cerrar_puerta", 2, "oeste"), ("esperar", 3)], velocidad=50)


def _b_t6():
    # Salida de costo 1 y un cazador muy rápido (velocidad 10000).
    from tests_labs.cripta_sintetica import esqueleto_lineal
    return _cazador_en(esqueleto_lineal([1]), 2, 1, [("esperar", 2)], velocidad=10000)


def _b_t7():
    # Salida de costo 900: el cazador la está cruzando cuando cambia su velocidad.
    from tests_labs.cripta_sintetica import esqueleto_lineal
    return _cazador_en(esqueleto_lineal([900]), 2, 1,
                       [("esperar", 1), ("cambiar_velocidad", "e-1", 50), ("esperar", 5)])


# ---------------------------------------------------------------- Niebla e «ir a» (B-N, capacidad 002)
def _pasillo(salas):
    from tests_labs.cripta_sintetica import esqueleto_lineal
    return esqueleto_lineal([None] * (salas - 1))       # 1 - 2 - ... - salas, de este a oeste, costo 100


def _b_n1():
    http = _caso(_pasillo(3), suelo=[(LLAVE_SALIDA_CASOS, 1)])
    return http, [("ir_a", 3)]


def _b_n2():
    http = _caso(_pasillo(3), suelo=[(LLAVE_SALIDA_CASOS, 1)])
    return http, [("mover", "este"), ("mover", "este"), ("mover", "oeste"), ("mover", "oeste"),
                  ("cerrar_puerta", 2, "este"), ("ir_a", 3)]


def _b_n3():
    # Con la antorcha, al entrar a 2 se explora 3 sin despertar a su enemigo; luego «ir a 3» entra donde duerme.
    http = _caso(_pasillo(3), [(3, "e-dormido", "ent_errante", None)], [ficha_enemigo("ent_errante", "errante")],
                 suelo=[(LLAVE_SALIDA_CASOS, 1), (ANTORCHA, 1)])
    return http, [("recoger", ANTORCHA), ("antorcha",), ("mover", "este"), ("ir_a", 3)]


def _b_n4():
    http = _caso(_pasillo(3), [(3, "e-dormido", "ent_errante", None)], [ficha_enemigo("ent_errante", "errante")],
                 suelo=[(LLAVE_SALIDA_CASOS, 1), (ANTORCHA, 1)], trampas=[(3, "t-1", "trp_dardos")])
    return http, [("recoger", ANTORCHA), ("antorcha",), ("mover", "este")]


def _b_n5():
    http = _caso(_pasillo(3), [(3, "e-dormido", "ent_errante", None)], [ficha_enemigo("ent_errante", "errante")],
                 suelo=[(LLAVE_SALIDA_CASOS, 1), (ANTORCHA, 1), (PERGAMINO, 1)], trampas=[(3, "t-1", "trp_dardos")])
    return http, [("recoger", ANTORCHA), ("recoger", PERGAMINO), ("antorcha",), ("mover", "este"), ("pergamino",)]


def _b_n6():
    http = _caso(_pasillo(4), suelo=[(LLAVE_SALIDA_CASOS, 1), (PERGAMINO, 1)])
    return http, [("recoger", PERGAMINO), ("mover", "este"), ("mover", "este"), ("mover", "este"),
                  ("mover", "oeste"), ("mover", "oeste"), ("mover", "oeste"), ("ir_a", 4), ("pergamino_en_viaje", 1)]


# ---------------------------------------------------------------- Resolubilidad (B-R, capacidad 003)
def _b_r1():
    # 1 - 2: la única puerta se abre con la llave de salida, y esa llave está en el suelo de la sala 2.
    salas = _pasillo(2)
    _puerta_con_llave(salas, 1, 2, LLAVE_SALIDA_CASOS)
    http = _caso(salas, suelo=[(LLAVE_SALIDA_CASOS, 2)], sala_salida=2)
    return http, [("verificar",)]


def _b_r2():
    # 1 - 2 - 3: la llave de salida la suelta un errante que inicia en la sala 3.
    http = _caso(_pasillo(3), [(3, "e-errante", "ent_errante", None)], [ficha_enemigo("ent_errante", "errante")],
                 soltadas=[(LLAVE_SALIDA_CASOS, "e-errante")], sala_salida=3)
    return http, [("verificar",)]


def _b_r3():
    # Desde 1 se llega sin llaves a 2 (llave A) y a 3 (llave B). 1-4 se abre con A y 4-5 con B; la llave de salida
    # está en 5. A y B se pueden obtener en cualquier orden.
    from tests_labs.cripta_sintetica import esqueleto_de_conexiones
    salas = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (1, 3, 100, "O", "E"), (1, 4, 100, "S", "N"),
                                     (4, 5, 100, "S", "N")])
    _puerta_con_llave(salas, 1, 4, "itm_llave_a")
    _puerta_con_llave(salas, 4, 5, "itm_llave_b")
    http = _caso(salas, suelo=[("itm_llave_a", 2), ("itm_llave_b", 3), (LLAVE_SALIDA_CASOS, 5)], sala_salida=5)
    return http, [("verificar",), ("verificar",)]


def _b_r4():
    # 1 - 2: la puerta se abre con una llave que no está en ninguna parte; la llave de salida está detrás.
    salas = _pasillo(2)
    _puerta_con_llave(salas, 1, 2, "itm_llave_perdida")
    http = _caso(salas, suelo=[(LLAVE_SALIDA_CASOS, 2)], sala_salida=2)
    return http, [("iniciar_sin_forzar",)]


# ---------------------------------------------------------------- Línea de tiempo (B-L, capacidad 004)
def _b_l1():
    http = _caso(_pasillo(2), suelo=[(LLAVE_SALIDA_CASOS, 1)])
    return http, [("esperar", 2), ("historia", 1000000)]


def _b_l2():
    http = _caso(_pasillo(2), suelo=[(LLAVE_SALIDA_CASOS, 1), (PERGAMINO, 1)])
    return http, [("recoger", PERGAMINO), ("mover", "este"), ("pergamino",), ("historia", None)]


def _b_l3():
    # Jugador y dos errantes de velocidad 100 en la sala 1: los tres actúan en t = 100.
    http = _caso(_pasillo(2), [(1, "e-a", "ent_errante", None), (1, "e-b", "ent_errante", None)],
                 [ficha_enemigo("ent_errante", "errante")], suelo=[(LLAVE_SALIDA_CASOS, 2)])
    return http, [("esperar", 1), ("historia", 100)]


def _b_l4():
    http = _caso(_pasillo(2), suelo=[(LLAVE_SALIDA_CASOS, 1)])
    return http, [("esperar", 1), ("historia", 0), ("esperar", 1)]


def _b_l5():
    # Partida corta: recoger la llave de salida y salir a la sala 2, que es la salida.
    http = _caso(_pasillo(2), suelo=[(LLAVE_SALIDA_CASOS, 1)], sala_salida=2)
    return http, [("recoger", LLAVE_SALIDA_CASOS), ("mover", "este"), ("replay_hasta", 1000000)]


def _b_l6():
    """Archivo de partida de la Parte I armado a mano en una carpeta temporal: la MAGIA y el encabezado de
    AlmacenPartidaBinario con la versión de formato 5, más un cuerpo mínimo (un pie vacío con la marca de fin). No usa
    el codec ni AlmacenPartidaBinario para escribir: los dos solo escriben la versión 6. La carpeta la borra quien usa
    el caso."""
    import os
    import tempfile
    from adaptadores.AlmacenPartidaBinario import MAGIA, MARCA_FIN, _ENCABEZADO, _PIE
    carpeta = tempfile.mkdtemp(prefix="cripta_b_l6_")
    ruta = os.path.join(carpeta, "partida_parte1.bin")
    with open(ruta, "wb") as archivo:
        archivo.write(_ENCABEZADO.pack(MAGIA, 5))
        archivo.write(_PIE.pack(_ENCABEZADO.size, 0, _ENCABEZADO.size, 0, MARCA_FIN))
    http = _caso(_pasillo(2), suelo=[(LLAVE_SALIDA_CASOS, 1)])
    return http, [("cargar_partida", ruta)]


CASOS_APENDICE_B = [
    ("B-T1", "Un cazador no tiene ruta abierta hacia el jugador: espera con costo 100.", _b_t1),
    ("B-T2", "La ruta más barata del cazador cuesta más que su `rango`: espera con costo 100.", _b_t2),
    ("B-T3", "Existe una ruta de menos salas pero mayor costo y otra de más salas y menor costo: el cazador sigue la "
             "de menor costo.", _b_t3),
    ("B-T4", "Dos vecinas inician rutas de costo mínimo: el cazador va a la de menor id.", _b_t4),
    ("B-T5", "Una puerta de la ruta del cazador se cierra entre dos de sus turnos: en el turno siguiente decide como si "
             "calculara desde cero.", _b_t5),
    ("B-T6", "Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1.", _b_t6),
    ("B-T7", "Cambia la velocidad de un actor que atraviesa una salida costosa: el tiempo restante se escala según P1 "
             "§2.3.", _b_t7),
    ("B-N1", "`ir a` hacia una sala no explorada: se rechaza y no consume tiempo.", _b_n1),
    ("B-N2", "El mapa recuerda abierta una puerta que en realidad está cerrada: al observarla, el mapa se actualiza y "
             "la ruta se recalcula; si no queda ruta, el viaje se detiene sin consumir tiempo adicional.", _b_n2),
    ("B-N3", "`ir a` entra a una sala con enemigos dormidos: los enemigos se activan según P1 §2.4 y el viaje se "
             "detiene.", _b_n3),
    ("B-N4", "Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni sus "
             "trampas.", _b_n4),
    ("B-N5", "Un pergamino revierte una entrada con antorcha encendida: las salas exploradas por la antorcha vuelven a "
             "su estado anterior.", _b_n5),
    ("B-N6", "Un pergamino durante un viaje: revierte solo el último paso y el viaje no continúa.", _b_n6),
    ("B-R1", "`llave_salida` está detrás de la única puerta que ella misma abre: no resoluble; el reporte señala el "
             "ciclo.", _b_r1),
    ("B-R2", "Una llave está en el campo `suelta` de un enemigo errante: la verificación la ubica en la sala inicial "
             "del enemigo.", _b_r2),
    ("B-R3", "Existen varios órdenes válidos de obtención de llaves: dos ejecuciones producen el mismo orden.", _b_r3),
    ("B-R4", "Cripta no resoluble sin `--forzar`: la partida no inicia y se muestra el reporte.", _b_r4),
    ("B-L1", "`historia <t>` con `t` mayor que el reloj actual: se rechaza.", _b_l1),
    ("B-L2", "`historia` después de usar un pergamino: no muestra las acciones revertidas.", _b_l2),
    ("B-L3", "Varios eventos ocurren en el mismo instante `t`: `historia <t>` muestra el estado después de todos "
             "ellos.", _b_l3),
    ("B-L4", "`historia` no consume tiempo virtual, no se registra en `partida.log` y no modifica el historial de "
             "retroceso.", _b_l4),
    ("B-L5", "`--replay partida.log --hasta t` con `t` posterior al final de la partida: muestra el estado final e "
             "indica que la partida terminó antes.", _b_l5),
    ("B-L6", "Se carga un archivo de partida de la primera parte: se reporta la incompatibilidad de formato o se migra "
             "explícitamente; nunca se carga en silencio (caso compartido con Scott, capacidad 010).", _b_l6),
]