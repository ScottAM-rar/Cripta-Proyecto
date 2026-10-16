"""Pruebas de ClientePersistente con una API FALSA (sin internet).
 
Ejecutar desde la raíz del proyecto:
    py -m tests_labs.prueba_cliente_persistente
 
Cada "ejecución del juego" crea un cliente y un servicio nuevos sobre la MISMA
carpeta de disco, como si se cerrara el programa y se volviera a abrir.
"""
import os
import tempfile
 
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
 
resultados = []
 
 
def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)
 
 
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
 
 
with tempfile.TemporaryDirectory() as raiz:
    carpeta = os.path.join(raiz, "datos_cripta")
 
    print("== 1) Primera ejecución: todo viene de la red y se guarda ==")
    http1, _, servicio1 = nueva_ejecucion(carpeta)
    salas1 = cargar_todo(servicio1)
    comprobar("se construyen las 3 salas", len(salas1) == 3)
    comprobar("la sala 2 tiene 2 enemigos", len(salas1[1].enemigos) == 2)
    comprobar("solicitudes: 1 lista + 1 datos + 1 salas + 1 contenido + 1 versión catálogo + 1 catálogo + 1 catálogo del botín = 7",
              http1.solicitudes_realizadas == 7, f"(fueron {http1.solicitudes_realizadas}: {http1.nombres()})")
    comprobar("se crearon los archivos en disco",
              os.path.exists(os.path.join(carpeta, "criptas.bin"))
              and os.path.exists(os.path.join(carpeta, "catalogo.bin"))
              and os.path.exists(os.path.join(carpeta, "cripta_cripta-01.bin")))
 
    print("== 2) Segunda ejecución, nada cambió: casi todo sale del disco ==")
    http2, _, servicio2 = nueva_ejecucion(carpeta)
    salas2 = cargar_todo(servicio2)
    comprobar("solicitudes: solo lista + datos + versión del catálogo = 3",
              http2.solicitudes_realizadas == 3, f"(fueron {http2.solicitudes_realizadas}: {http2.nombres()})")
    comprobar("no se volvió a pedir salas, contenido ni catálogo",
              http2.veces("salas") == 0 and http2.veces("contenido") == 0 and http2.veces("catalogo") == 0)
    comprobar("las salas son idénticas a las de la primera ejecución", salas2 == salas1)
 
    print("== 3) La cripta cambió de versión: se rehace la cripta, el catálogo sigue ==")
    http3, _, servicio3 = nueva_ejecucion(carpeta, version_cripta="c2")
    cargar_todo(servicio3)
    comprobar("se volvieron a pedir salas y contenido",
              http3.veces("salas") == 1 and http3.veces("contenido") == 1)
    comprobar("el catálogo NO se volvió a pedir (sigue vigente)", http3.veces("catalogo") == 0)
    comprobar("total = lista + datos + versión cat. + salas + contenido = 5",
              http3.solicitudes_realizadas == 5, f"(fueron {http3.solicitudes_realizadas})")
 
    print("== 4) El catálogo cambió de versión: se rehace el catálogo, la cripta sigue ==")
    http4, _, servicio4 = nueva_ejecucion(carpeta, version_cripta="c2", version_catalogo="k2")
    cargar_todo(servicio4)
    comprobar("se volvió a pedir el catálogo (fichas y botín: 2 solicitudes)", http4.veces("catalogo") == 2)
    comprobar("salas y contenido NO se volvieron a pedir",
              http4.veces("salas") == 0 and http4.veces("contenido") == 0)
    comprobar("total = lista + datos + versión cat. + catálogo x2 = 5",
              http4.solicitudes_realizadas == 5, f"(fueron {http4.solicitudes_realizadas})")
 
with tempfile.TemporaryDirectory() as raiz:
    carpeta = os.path.join(raiz, "datos_cripta")
 
    print("== 5) Contenido: solo se piden a la red las salas que faltan ==")
    http, cliente, _ = nueva_ejecucion(carpeta)
    primero = cliente.obtener_contenido("cripta-01", [1, 2])
    segundo = cliente.obtener_contenido("cripta-01", [1, 2, 3])
    pedidos = []
    for llamada in http.llamadas:
        if llamada[0] == "contenido":
            pedidos.append(llamada[1])
    comprobar("primero se pidieron [1, 2] y después solo [3]", pedidos == [[1, 2], [3]], f"({pedidos})")
    comprobar("el resultado sigue el orden pedido", [c["sala"] for c in segundo] == [1, 2, 3])
    comprobar("lo ya conocido no cambia", segundo[:2] == primero)
 
    print("== 6) Catálogo: solo se piden las fichas que faltan, en el orden pedido ==")
    http, cliente, _ = nueva_ejecucion(os.path.join(raiz, "otra"))
    cliente.obtener_catalogo(["ent_rata_gigante"])
    fichas = cliente.obtener_catalogo(["ent_guardian_oseo", "ent_rata_gigante"])
    pedidos = []
    for llamada in http.llamadas:
        if llamada[0] == "catalogo":
            pedidos.append(llamada[1])
    comprobar("la segunda vez solo se pidió el guardián",
              pedidos == [["ent_rata_gigante"], ["ent_guardian_oseo"]], f"({pedidos})")
    comprobar("las fichas salen en el orden pedido",
              [f["id"] for f in fichas] == ["ent_guardian_oseo", "ent_rata_gigante"])
    comprobar("la versión del catálogo se pidió una sola vez", http.veces("version_catalogo") == 1)
 
    print("== 7) Datos generales y versiones ==")
    http, cliente, _ = nueva_ejecucion(os.path.join(raiz, "tercera"))
    cliente.obtener_datos_generales("cripta-01")
    cliente.obtener_datos_generales("cripta-01")
    cliente.obtener_salas("cripta-01")
    comprobar("los datos generales se piden una sola vez por sesión", http.veces("datos") == 1)
    comprobar("obtener_version_* pasan directo a la red",
              cliente.obtener_version_cripta("cripta-01") == "c1" and cliente.obtener_version_catalogo() == "k1")
    comprobar("solicitudes_realizadas cuenta las de la red", cliente.solicitudes_realizadas == len(http.llamadas))
 
    print("== 8) Datos sin campo 'version': se usa el endpoint de versión ==")
    http, cliente, _ = nueva_ejecucion(os.path.join(raiz, "cuarta"), datos_con_version=False)
    cliente.obtener_datos_generales("cripta-01")
    comprobar("se pidió la versión por su endpoint", http.veces("version_cripta") == 1)
 
print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")