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