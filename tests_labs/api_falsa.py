"""API falsa y ayudas compartidas por las pruebas de persistencia y offline."""
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
 
 
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
        ]
        devueltas = []
        for ficha in fichas:
            if ficha["id"] in ids:
                devueltas.append(ficha)
        return devueltas
 
 
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