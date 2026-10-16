"""Pruebas de ClienteOffline. Sin internet.
 
    py -m tests_labs.prueba_cliente_offline
 
Primero se "juega con conexión" (API falsa + ClientePersistente) para llenar el
disco, y después se abre el juego en modo offline sobre la misma carpeta.
"""
import os
import tempfile
 
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_offline import ClienteOffline, ErrorOffline
from adaptadores.servicioCripta import ServicioCripta
from tests_labs.api_falsa import cargar_todo, nueva_ejecucion
 
resultados = []
 
 
def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)
 
 
def lanza_error_offline(funcion):
    try:
        funcion()
    except ErrorOffline:
        return True
    return False
 
 
with tempfile.TemporaryDirectory() as raiz:
    carpeta = os.path.join(raiz, "datos_cripta")
 
    print("== 1) Disco vacío: el modo offline avisa claro ==")
    vacio = ClienteOffline(AlmacenDisco(carpeta))
    comprobar("obtener_criptas() -> ErrorOffline", lanza_error_offline(vacio.obtener_criptas))
    comprobar("obtener_datos_generales() -> ErrorOffline",
              lanza_error_offline(lambda: vacio.obtener_datos_generales("cripta-01")))
    comprobar("obtener_catalogo() -> ErrorOffline",
              lanza_error_offline(lambda: vacio.obtener_catalogo(["ent_rata_gigante"])))
 
    print("== 2) Se juega una vez con conexión para llenar el disco ==")
    _, _, servicio_online = nueva_ejecucion(carpeta)
    salas_online = cargar_todo(servicio_online)
    comprobar("se construyeron 3 salas", len(salas_online) == 3)
 
    print("== 3) Modo offline: mismas salas, cero solicitudes ==")
    offline = ClienteOffline(AlmacenDisco(carpeta))
    servicio = ServicioCripta(offline, CacheLRU(25))
    comprobar("lista de criptas", servicio.listar_criptas() == ["Cripta 1: Osario menor"])
    cid = servicio.obtener_id_cripta(1)
    jugador = servicio.crear_jugador(cid)
    salas_offline = servicio.construir_todas(cid)
    comprobar("las salas offline son idénticas a las online", salas_offline == salas_online)
    comprobar("el jugador se crea con las stats guardadas", jugador.vida_actual == 30)
    comprobar("solicitudes realizadas = 0", offline.solicitudes_realizadas == 0)
    comprobar("versiones guardadas disponibles",
              offline.obtener_version_cripta(cid) == "c1" and offline.obtener_version_catalogo() == "k1")
 
    print("== 4) Cripta incompleta: no se ofrece ==")
    almacen = AlmacenDisco(carpeta)
    almacen.validar_cripta("cripta-02", "x")
    almacen.guardar_datos("cripta-02", {"id": "cripta-02"})
    almacen.guardar_criptas([
        {"id": "cripta-01", "nombre": "Osario menor", "salas": 3, "dificultad": 1},
        {"id": "cripta-02", "nombre": "Cripta rota", "salas": 3, "dificultad": 2},
    ])
    offline = ClienteOffline(almacen)
    ids = [c["id"] for c in offline.obtener_criptas()]
    comprobar("solo aparece la cripta completa", ids == ["cripta-01"], f"({ids})")
    comprobar("cripta_disponible distingue ambas",
              offline.cripta_disponible("cripta-01") and not offline.cripta_disponible("cripta-02"))
 
    print("== 5) Falta una pieza concreta ==")
    comprobar("contenido de sala inexistente -> ErrorOffline",
              lanza_error_offline(lambda: offline.obtener_contenido("cripta-01", [1, 99])))
    comprobar("ficha inexistente -> ErrorOffline",
              lanza_error_offline(lambda: offline.obtener_catalogo(["ent_fantasma"])))
 
print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")