"""Pruebas de la precarga por vecindad, el reporte de solicitudes, los
contadores de la caché y el cliente de red compartido. Sin internet.

    py -m tests_labs.prueba_vecinas_reporte
"""
import os
import tempfile

from adaptadores import fabrica
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ReporteSolicitudes, ServicioCripta
from tests_labs.api_falsa import HttpFalso

resultados = []


def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)


def lanza(excepcion, funcion):
    try:
        funcion()
    except excepcion:
        return True
    return False


class HttpConCiclo(HttpFalso):
    """Cripta de 5 salas con un ciclo (4 vuelve a 1) y una sala aislada (5)."""

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["salas_total"] = 5
        return datos

    def obtener_salas(self, cripta_id):
        self.llamadas.append(("salas", cripta_id))
        return [
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}}},
            {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "C", "salidas": {"O": {"sala": 2}, "N": {"sala": 4}}},
            {"id": 4, "nombre": "D", "salidas": {"S": {"sala": 3}, "E": {"sala": 1}}},
            {"id": 5, "nombre": "E", "salidas": {}},
        ]

    def obtener_contenido(self, cripta_id, salas):
        self.llamadas.append(("contenido", list(salas)))
        resultado = []
        for numero in salas:
            resultado.append({"sala": numero, "enemigos": [], "objetos": [], "trampas": []})
        return resultado


def servicio_nuevo(carpeta, http):
    servicio = ServicioCripta(ClientePersistente(http, AlmacenDisco(carpeta)), CacheLRU(25))
    servicio.listar_criptas()
    return servicio, servicio.obtener_id_cripta(1)


with tempfile.TemporaryDirectory() as raiz:
    print("== 1) salas_vecinas en la cripta de 3 salas ==")
    s, cid = servicio_nuevo(os.path.join(raiz, "a"), HttpFalso())
    comprobar("vecinas de la 1 = [2]", s.salas_vecinas(cid, 1) == [2])
    comprobar("vecinas de la 2 = [3, 1] (orden N, S, E, O)", s.salas_vecinas(cid, 2) == [3, 1])
    comprobar("profundidad 2 desde la 1 = [2, 3]", s.salas_vecinas(cid, 1, 2) == [2, 3])
    comprobar("profundidad 0 = []", s.salas_vecinas(cid, 1, 0) == [])
    comprobar("profundidad negativa -> ValueError", lanza(ValueError, lambda: s.salas_vecinas(cid, 1, -1)))
    comprobar("sala inexistente -> ValueError", lanza(ValueError, lambda: s.salas_vecinas(cid, 99)))

    print("== 2) salas_vecinas con ciclo y sala aislada ==")
    s2, c2 = servicio_nuevo(os.path.join(raiz, "b"), HttpConCiclo())
    comprobar("desde la 1 (prof. 1) = [2]", s2.salas_vecinas(c2, 1) == [2])
    comprobar("desde la 1 (prof. 3) = [2, 3, 4] sin repetir ni incluir la 1",
              s2.salas_vecinas(c2, 1, 3) == [2, 3, 4], f"(fue {s2.salas_vecinas(c2, 1, 3)})")
    comprobar("desde la 4 (prof. 1) = [3, 1]", s2.salas_vecinas(c2, 4) == [3, 1])
    comprobar("la sala aislada no tiene vecinas", s2.salas_vecinas(c2, 5, 5) == [])

    print("== 3) precargar_vecinas: lo precargado ya no cuesta ==")
    http3 = HttpFalso()
    s3, c3 = servicio_nuevo(os.path.join(raiz, "c"), http3)
    s3.crear_jugador(c3)
    comprobar("procesa la actual y su vecina (2 salas)", s3.precargar_vecinas(c3, 1, 1) == 2)
    antes = http3.solicitudes_realizadas
    s3.construir_sala(c3, 1)
    s3.construir_sala(c3, 2)
    comprobar("construir las salas 1 y 2 NO gasta solicitudes", http3.solicitudes_realizadas == antes)
    comprobar("la sala 3 todavía no estaba precargada", http3.veces("contenido") == 1)
    s3.precargar_vecinas(c3, 2, 1)
    comprobar("al avanzar a la 2 solo se pide lo que faltaba (sala 3 y su ficha)",
              http3.llamadas[antes:] == [("contenido", [3]), ("catalogo", ["ent_guardian_oseo"])],
              f"(llamadas: {http3.llamadas[antes:]})")
    comprobar("contenido pedido en lotes, nunca sala por sala",
              http3.veces("contenido") == 2)

    print("== 4) Contadores de la caché ==")
    cache = CacheLRU(2)
    comprobar("empieza en 0 y 0", cache.aciertos == 0 and cache.fallos == 0)
    cache.obtener("x")
    comprobar("obtener algo que no está cuenta un fallo", cache.fallos == 1 and cache.aciertos == 0)
    cache.insertar("x", 1)
    comprobar("insertar no cuenta como acierto ni fallo", cache.fallos == 1 and cache.aciertos == 0)
    cache.obtener("x")
    cache.obtener("x")
    comprobar("obtener algo que sí está cuenta aciertos", cache.aciertos == 2 and cache.fallos == 1)

    print("== 5) Reporte de solicitudes ==")
    http5 = HttpFalso()
    s5, c5 = servicio_nuevo(os.path.join(raiz, "d"), http5)
    s5.crear_jugador(c5)
    s5.precargar(c5)
    informe = s5.reporte(c5)
    comprobar("solicitudes = las del cliente", informe.solicitudes == http5.solicitudes_realizadas == 7)
    comprobar("presupuesto = 9", informe.presupuesto == 9)
    comprobar("dentro del presupuesto y restante 2", informe.dentro_del_presupuesto and informe.restante == 2)
    comprobar("la caché registró fallos al buscar fichas", informe.fallos_cache > 0)
    comprobar("el texto resume solicitudes y caché",
              "7 de 9" in informe.texto() and "aciertos" in informe.texto(), f"\n{informe.texto()}")
    excedido = ReporteSolicitudes(solicitudes=10, presupuesto=9, aciertos_cache=0, fallos_cache=0)
    comprobar("10 de 9 se marca como EXCEDIDO",
              not excedido.dentro_del_presupuesto and excedido.restante == -1 and "EXCEDIDO" in excedido.texto())

    print("== 6) Un solo cliente de red (UUID y contador) por ejecución ==")
    fabrica.reiniciar_cliente_compartido()
    a = fabrica.crear_servicio(carpeta=os.path.join(raiz, "e"), url="http://prueba.invalido/v1")
    b = fabrica.crear_servicio(carpeta=os.path.join(raiz, "e"), url="http://prueba.invalido/v1")
    comprobar("dos llamadas comparten el mismo cliente de red", a.cliente.cliente is b.cliente.cliente)
    comprobar("mismo UUID", a.cliente.cliente.client_id == b.cliente.cliente.client_id)
    comprobar("pero cada una tiene su propia caché", a.cache is not b.cache)
    fabrica.reiniciar_cliente_compartido()
    c = fabrica.crear_servicio(carpeta=os.path.join(raiz, "e"), url="http://prueba.invalido/v1")
    comprobar("tras reiniciar hay otro UUID", c.cliente.cliente.client_id != a.cliente.cliente.client_id)
    d = fabrica.crear_servicio(carpeta=os.path.join(raiz, "e"), url="http://otra.invalida/v1")
    comprobar("otra URL no reutiliza el cliente", d.cliente.cliente is not c.cliente.cliente)
    fabrica.reiniciar_cliente_compartido()

print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")
