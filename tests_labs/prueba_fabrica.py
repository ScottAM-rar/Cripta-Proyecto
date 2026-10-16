"""Pruebas de crear_servicio y de la precarga. Sin internet.

    py -m tests_labs.prueba_fabrica
"""
import os
import tempfile

from adaptadores.cliente_offline import ErrorOffline
from adaptadores.fabrica import crear_servicio
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


def arrancar(carpeta, http):
    """Lo que hará el juego al arrancar."""
    servicio = crear_servicio(carpeta=carpeta, cliente_http=http)
    servicio.listar_criptas()
    cid = servicio.obtener_id_cripta(1)
    servicio.crear_jugador(cid)
    return servicio, cid


with tempfile.TemporaryDirectory() as raiz:
    carpeta = os.path.join(raiz, "datos_cripta")

    print("== 1) Primera vez, con conexión: precarga en lotes ==")
    http1 = HttpFalso()
    servicio, cid = arrancar(carpeta, http1)
    cargadas = servicio.precargar(cid)
    comprobar("se precargan las 3 salas", cargadas == 3)
    comprobar("7 solicitudes en total (la 7ª trae lo que sueltan los enemigos)", http1.solicitudes_realizadas == 7, f"(fueron {http1.solicitudes_realizadas})")
    comprobar("el servicio las cuenta igual", servicio.solicitudes_realizadas == 7)
    antes = http1.solicitudes_realizadas
    salas = [servicio.construir_sala(cid, n) for n in (1, 2, 3)]
    comprobar("construir_sala después de precargar NO gasta solicitudes",
              http1.solicitudes_realizadas == antes)
    comprobar("dentro del presupuesto", servicio.solicitudes_realizadas <= servicio.presupuesto_solicitudes(cid),
              f"({servicio.solicitudes_realizadas} de {servicio.presupuesto_solicitudes(cid)})")
    comprobar("sala de salida", servicio.obtener_sala_salida(cid) == 3)

    print("== 2) Segunda vez, con conexión: casi todo del disco ==")
    http2 = HttpFalso()
    servicio2, cid2 = arrancar(carpeta, http2)
    servicio2.precargar(cid2)
    comprobar("solo 3 solicitudes", http2.solicitudes_realizadas == 3, f"(fueron {http2.solicitudes_realizadas})")
    comprobar("las mismas salas", [servicio2.construir_sala(cid2, n) for n in (1, 2, 3)] == salas)

    print("== 3) Sin conexión: mismo juego, cero solicitudes ==")
    servicio3 = crear_servicio(offline=True, carpeta=carpeta)
    servicio3.listar_criptas()
    cid3 = servicio3.obtener_id_cripta(1)
    servicio3.crear_jugador(cid3)
    servicio3.precargar(cid3)
    comprobar("0 solicitudes", servicio3.solicitudes_realizadas == 0)
    comprobar("las mismas salas", [servicio3.construir_sala(cid3, n) for n in (1, 2, 3)] == salas)

    print("== 4) Sin conexión y sin nada guardado ==")
    vacio = crear_servicio(offline=True, carpeta=os.path.join(raiz, "vacia"))
    comprobar("avisa con ErrorOffline", lanza(ErrorOffline, vacio.listar_criptas))

    print("== 5) Precarga parcial y parámetros ==")
    http5 = HttpFalso()
    s5, c5 = arrancar(os.path.join(raiz, "otra"), http5)
    comprobar("precargar([1, 2]) trae 2 salas", s5.precargar(c5, [1, 2]) == 2)
    comprobar("tamaño de caché inválido -> ValueError", lanza(ValueError, lambda: crear_servicio(cache_size=0)))

print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")
