"""Pruebas de la precarga perezosa (presupuesto de red), de la sesión compartida
y de las ayudas del servicio (versiones, fichas en uso). Sin internet.

    py -m tests_labs.prueba_precarga_presupuesto
"""
import os
import tempfile

from adaptadores import fabrica
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from tests_labs.api_falsa import HttpFalso

resultados = []
TOTAL = 30


def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)


def lanza(excepcion, funcion):
    try:
        funcion()
    except excepcion:
        return True
    return False


class HttpPasillo(HttpFalso):
    """Una cripta lineal de TOTAL salas: 1 - 2 - 3 - ... - TOTAL."""

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["salas_total"] = TOTAL
        datos["sala_salida"] = TOTAL
        return datos

    def obtener_salas(self, cripta_id):
        self.llamadas.append(("salas", cripta_id))
        salas = []
        for n in range(1, TOTAL + 1):
            salidas = {}
            if n > 1:
                salidas["O"] = {"sala": n - 1}
            if n < TOTAL:
                salidas["E"] = {"sala": n + 1}
            salas.append({"id": n, "nombre": f"Sala {n}", "salidas": salidas})
        return salas

    def obtener_contenido(self, cripta_id, salas):
        self.llamadas.append(("contenido", list(salas)))
        resultado = []
        for n in salas:
            resultado.append({"sala": n, "enemigos": [], "objetos": [], "trampas": []})
        return resultado


def servicio_pasillo(carpeta):
    http = HttpPasillo()
    servicio = ServicioCripta(ClientePersistente(http, AlmacenDisco(carpeta)), CacheLRU(25))
    servicio.listar_criptas()
    return http, servicio, servicio.obtener_id_cripta(1)


def recorrer(servicio, cid, profundidad, perezosa=True):
    """Camina de la sala 1 a la última precargando en cada paso, como el juego."""
    for sala in range(1, TOTAL + 1):
        if perezosa:
            servicio.precargar_vecinas(cid, sala, profundidad)
        else:   # lo que hacía antes: pedir actual + alcance en CADA paso
            servicio.precargar(cid, [sala] + servicio.salas_vecinas(cid, sala, profundidad))


with tempfile.TemporaryDirectory() as raiz:
    print("== 1) Garantía: lo inmediato siempre está listo ==")
    http, s, cid = servicio_pasillo(os.path.join(raiz, "a"))
    s.crear_jugador(cid)
    garantia = True
    for sala in range(1, TOTAL + 1):
        s.precargar_vecinas(cid, sala, 2)
        antes = http.solicitudes_realizadas
        for vecina in [sala] + s.salas_vecinas(cid, sala, 1):
            s.construir_sala(cid, vecina)
        if http.solicitudes_realizadas != antes:
            garantia = False
    comprobar("en las 30 salas, entrar a la actual o a una vecina NO espera a la red", garantia)

    print("== 2) Es perezosa: sin necesidad, no hace nada ==")
    http2, s2, c2 = servicio_pasillo(os.path.join(raiz, "b"))
    primera = s2.precargar_vecinas(c2, 1, 2)
    antes = http2.solicitudes_realizadas
    segunda = s2.precargar_vecinas(c2, 1, 2)
    comprobar("la primera llamada trae salas", primera > 0, f"({primera})")
    comprobar("repetirla devuelve 0 y no gasta solicitudes", segunda == 0 and http2.solicitudes_realizadas == antes)
    s2.precargar_vecinas(c2, 2, 2)
    comprobar("avanzar a una sala cuyas vecinas ya están: 0 solicitudes", http2.solicitudes_realizadas == antes)

    print("== 3) Ahorra solicitudes frente a pedir en cada paso ==")
    h_a, s_a, c_a = servicio_pasillo(os.path.join(raiz, "c1"))
    recorrer(s_a, c_a, 2, perezosa=False)
    h_p, s_p, c_p = servicio_pasillo(os.path.join(raiz, "c2"))
    recorrer(s_p, c_p, 2, perezosa=True)
    comprobar("perezosa gasta menos que 'en cada paso'",
              h_p.solicitudes_realizadas < h_a.solicitudes_realizadas,
              f"(perezosa {h_p.solicitudes_realizadas} vs en cada paso {h_a.solicitudes_realizadas})")
    h_g, s_g, c_g = servicio_pasillo(os.path.join(raiz, "c3"))
    recorrer(s_g, c_g, 9, perezosa=True)
    comprobar("con profundidad 9 el lote se llena (menos solicitudes aún)",
              h_g.solicitudes_realizadas < h_p.solicitudes_realizadas,
              f"({h_g.solicitudes_realizadas} solicitudes en las {TOTAL} salas)")
    h_n, s_n, c_n = servicio_pasillo(os.path.join(raiz, "c4"))
    recorrer(s_n, c_n, None, perezosa=True)
    comprobar("sin indicar profundidad (lo normal) se llena el lote solo",
              h_n.solicitudes_realizadas <= h_g.solicitudes_realizadas,
              f"({h_n.solicitudes_realizadas} solicitudes: {h_n.nombres()} / contenido x{h_n.veces('contenido')})")
    comprobar("cada solicitud de contenido trae 10 salas como máximo",
              all(len(l[1]) <= 10 for l in h_n.llamadas if l[0] == "contenido"))

    print("== 4) Nunca toda la cripta de una vez ==")
    h4, s4, c4 = servicio_pasillo(os.path.join(raiz, "d"))
    traidas = s4.precargar_vecinas(c4, 1, 99)
    pedidos = [llamada[1] for llamada in h4.llamadas if llamada[0] == "contenido"]
    comprobar("un lote nunca pasa de 10 salas", traidas <= 10 and len(pedidos[0]) <= 10, f"(trajo {traidas})")
    comprobar("no se trajo la cripta completa", traidas < TOTAL)
    pequeno = ServicioCripta(ClientePersistente(HttpPasillo(), AlmacenDisco(os.path.join(raiz, "e"))), CacheLRU(25))
    pequeno.listar_criptas()
    comprobar("max_salas se respeta", pequeno.precargar_vecinas(pequeno.obtener_id_cripta(1), 1, 99, max_salas=4) == 4)
    comprobar("profundidad < 1 -> ValueError", lanza(ValueError, lambda: s4.precargar_vecinas(c4, 1, 0)))
    comprobar("max_salas < 1 -> ValueError", lanza(ValueError, lambda: s4.precargar_vecinas(c4, 1, 2, 0)))
    comprobar("sala inexistente -> ValueError", lanza(ValueError, lambda: s4.precargar_vecinas(c4, 999, 2)))

    print("== 5) Sesión compartida: criptas, datos y versión se piden una vez ==")
    http5 = HttpFalso()
    fabrica.reiniciar_cliente_compartido()
    original = fabrica._cliente_http_de_ejecucion
    fabrica._cliente_http_de_ejecucion = lambda url: http5
    try:
        carpeta5 = os.path.join(raiz, "f")
        a = fabrica.crear_servicio(carpeta=carpeta5)
        a.listar_criptas()                                   # lo que hace el menú
        b = fabrica.crear_servicio(carpeta=carpeta5)         # lo que hace iniciarJuego
        cid5 = b.obtener_id_cripta(1)
        b.crear_jugador(cid5)
        b.construir_sala(cid5, 1)
        comprobar("los dos servicios comparten el cliente persistente", a.cliente is b.cliente)
        comprobar("/criptas se pidió UNA sola vez", http5.veces("criptas") == 1, f"(fueron {http5.veces('criptas')})")
        comprobar("cada servicio tiene su propia caché", a.cache is not b.cache)
        distinto = fabrica.crear_servicio(carpeta=os.path.join(raiz, "g"))
        comprobar("otra carpeta no reutiliza la sesión", distinto.cliente is not a.cliente)
    finally:
        fabrica._cliente_http_de_ejecucion = original
        fabrica.reiniciar_cliente_compartido()

    print("== 6) Versiones para el log y los puntajes, sin gastar de más ==")
    http6 = HttpFalso()
    s6 = ServicioCripta(ClientePersistente(http6, AlmacenDisco(os.path.join(raiz, "h"))), CacheLRU(25))
    s6.listar_criptas()
    c6 = s6.obtener_id_cripta(1)
    comprobar("version_cripta sale de los datos generales", s6.version_cripta(c6) == "c1")
    antes = http6.solicitudes_realizadas
    s6.version_cripta(c6)
    comprobar("pedirla otra vez no cuesta nada", http6.solicitudes_realizadas == antes)
    comprobar("version_catalogo devuelve la versión", s6.version_catalogo() == "k1")
    antes = http6.solicitudes_realizadas
    s6.version_catalogo()
    s6.construir_sala(c6, 2)    # esto valida el catálogo: no debe repetir la consulta de versión
    comprobar("la versión del catálogo se consulta una sola vez",
              http6.veces("version_catalogo") == 1, f"(fueron {http6.veces('version_catalogo')})")

    print("== 7) Fichas en uso ==")
    mini = ServicioCripta(ClientePersistente(HttpFalso(), AlmacenDisco(os.path.join(raiz, "i"))), CacheLRU(1))
    mini.cache.insertar("ent_a", {"id": "ent_a"})
    mini.retener_fichas(["ent_a"])
    comprobar("una ficha retenida no se desaloja", mini.cache.insertar("ent_b", {}) is False and mini.cache.claves() == ["ent_a"])
    mini.liberar_fichas(["ent_a"])
    comprobar("al liberarla ya puede salir", mini.cache.insertar("ent_b", {}) is True and mini.cache.claves() == ["ent_b"])

print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")
