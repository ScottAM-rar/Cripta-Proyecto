"""Pruebas de los errores de ClienteCripta. Sin internet: se reemplaza requests.get.

    py -m tests_labs.prueba_cliente_http_errores
"""
import requests

import adaptadores.cliente_http as modulo
from adaptadores.Interfaz import ClienteInterfaz
from adaptadores.cliente_http import ClienteCripta, ErrorSinConexion, MAX_REINTENTOS_429

resultados = []


def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)


class Respuesta:
    def __init__(self, codigo, cuerpo=None):
        self.status_code = codigo
        self._cuerpo = cuerpo

    def json(self):
        return self._cuerpo


def con_respuestas(respuestas):
    """Cada requests.get() devuelve (o lanza) lo siguiente de la lista."""
    pendientes = list(respuestas)

    def falso(url, headers=None, timeout=None):
        siguiente = pendientes.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente
    return falso


def lanza(excepcion, funcion):
    try:
        funcion()
    except excepcion as error:
        return error
    return None


original_get, original_sleep = requests.get, modulo.time.sleep
esperas = []
modulo.requests.get = None
modulo.time.sleep = lambda s: esperas.append(s)
try:
    cliente = ClienteCripta("https://falso/v1")

    print("== 1) Contrato ==")
    comprobar("ClienteCripta cumple ClienteInterfaz", isinstance(cliente, ClienteInterfaz))

    print("== 2) Respuesta normal ==")
    modulo.requests.get = con_respuestas([Respuesta(200, {"criptas": [{"id": "c1"}]})])
    comprobar("devuelve las criptas", cliente.obtener_criptas() == [{"id": "c1"}])
    comprobar("cuenta 1 solicitud", cliente.solicitudes_realizadas == 1)

    print("== 3) Un 429 y luego éxito ==")
    cliente = ClienteCripta("https://falso/v1")
    modulo.requests.get = con_respuestas([Respuesta(429, {"reintentar_en": 2}), Respuesta(200, {"criptas": []})])
    comprobar("se recupera", cliente.obtener_criptas() == [])
    comprobar("esperó lo que pidió el servidor", esperas == [2])
    comprobar("el 429 también cuenta como solicitud", cliente.solicitudes_realizadas == 2)

    print("== 4) 429 sin fin: ahora tiene tope ==")
    cliente = ClienteCripta("https://falso/v1")
    modulo.requests.get = con_respuestas([Respuesta(429, {"reintentar_en": 1})] * (MAX_REINTENTOS_429 + 1))
    error = lanza(RuntimeError, cliente.obtener_criptas)
    comprobar("se rinde con RuntimeError", error is not None and not isinstance(error, ErrorSinConexion))
    comprobar("hizo el intento inicial + los reintentos", cliente.solicitudes_realizadas == MAX_REINTENTOS_429 + 1,
              f"({cliente.solicitudes_realizadas})")

    print("== 5) Otros códigos ==")
    cliente = ClienteCripta("https://falso/v1")
    modulo.requests.get = con_respuestas([Respuesta(404, {})])
    comprobar("404 -> RuntimeError", lanza(RuntimeError, cliente.obtener_criptas) is not None)

    print("== 6) Sin conexión ==")
    cliente = ClienteCripta("https://falso/v1")
    modulo.requests.get = con_respuestas([requests.exceptions.ConnectionError("sin red")])
    error = lanza(ErrorSinConexion, cliente.obtener_criptas)
    comprobar("ConnectionError -> ErrorSinConexion", error is not None)
    comprobar("el mensaje sugiere --offline", error is not None and "--offline" in str(error))
    comprobar("no cuenta como solicitud (nunca llegó al servidor)", cliente.solicitudes_realizadas == 0)
    modulo.requests.get = con_respuestas([requests.exceptions.Timeout("tardó")])
    comprobar("Timeout -> ErrorSinConexion", lanza(ErrorSinConexion, cliente.obtener_criptas) is not None)
finally:
    modulo.requests.get = original_get
    modulo.time.sleep = original_sleep

print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")
