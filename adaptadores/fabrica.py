"""Punto único para armar el ServicioCripta según cómo se arranca el juego.

El resto del proyecto (EstadoJuegoLogica, main) solo llama a crear_servicio()
y no necesita conocer ClienteCripta, ClientePersistente ni ClienteOffline.

    Con conexión (por defecto):
        ServicioCripta -> ClientePersistente -> ClienteCripta (red)
                                             -> AlmacenDisco  (disco)
    Sin conexión (offline=True):
        ServicioCripta -> ClienteOffline -> AlmacenDisco (solo disco)
"""
from __future__ import annotations

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta

URL_API = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
CARPETA_DATOS = "datos_cripta"
TAMANO_CACHE = 25


# El enunciado pide UN solo UUID por ejecución. Cada ClienteCripta genera el
# suyo, así que aquí se guarda el primero que se crea y se reutiliza: aunque
# alguien llame crear_servicio() varias veces, la API ve siempre el mismo
# cliente y el contador de solicitudes es el de toda la ejecución.
_cliente_compartido = None
_persistente_compartido = None     # (url, carpeta, ClientePersistente)


def _cliente_http_de_ejecucion(url: str):
    global _cliente_compartido
    from adaptadores.cliente_http import ClienteCripta   # solo si hay red
    if _cliente_compartido is None or _cliente_compartido.base_url != url.strip("/"):
        _cliente_compartido = ClienteCripta(url)
    return _cliente_compartido


def _persistente_de_ejecucion(url: str, carpeta: str):
    """Un solo ClientePersistente por ejecución: así listar criptas y luego iniciar
    la partida (que crean servicios distintos) no repiten la lista de criptas, los
    datos generales ni la versión del catálogo. Cada una es una solicitud menos."""
    global _persistente_compartido
    if (_persistente_compartido is None
            or _persistente_compartido[0] != url.strip("/")
            or _persistente_compartido[1] != carpeta):
        cliente = ClientePersistente(_cliente_http_de_ejecucion(url), AlmacenDisco(carpeta))
        _persistente_compartido = (url.strip("/"), carpeta, cliente)
    return _persistente_compartido[2]


def reiniciar_cliente_compartido() -> None:
    """Olvida el cliente de red compartido (nuevo UUID y contador en 0) y la sesión.
    Solo para pruebas; el juego no debería necesitarlo."""
    global _cliente_compartido, _persistente_compartido
    _cliente_compartido = None
    _persistente_compartido = None


def crear_servicio(offline: bool = False,
                   cache_size: int = TAMANO_CACHE,
                   carpeta: str = CARPETA_DATOS,
                   url: str = URL_API,
                   cliente_http=None) -> ServicioCripta:
    """Arma el servicio completo.

    offline      True = jugar solo con lo guardado en disco, sin tocar la red.
    cache_size   capacidad de la caché de fichas en memoria (--cache-size).
    carpeta      dónde se guardan los datos en disco.
    cliente_http solo para pruebas: un cliente de red falso en lugar del real.

    Llamarla varias veces en la misma ejecución reutiliza el mismo cliente de
    red y de persistencia (mismo UUID, mismo contador, misma sesión), pero cada
    llamada arma un servicio y una caché nuevos. Lo ideal es crearla UNA vez en
    main y pasar el servicio.
    """
    if cache_size < 1:
        raise ValueError("El tamaño de la caché debe ser al menos 1")

    if offline:
        cliente = ClienteOffline(AlmacenDisco(carpeta))
    elif cliente_http is None:
        cliente = _persistente_de_ejecucion(url, carpeta)
    else:
        cliente = ClientePersistente(cliente_http, AlmacenDisco(carpeta))

    return ServicioCripta(cliente, CacheLRU(cache_size))
