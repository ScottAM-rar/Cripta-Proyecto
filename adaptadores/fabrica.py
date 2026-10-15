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
    """
    if cache_size < 1:
        raise ValueError("El tamaño de la caché debe ser al menos 1")

    almacen = AlmacenDisco(carpeta)

    if offline:
        cliente = ClienteOffline(almacen)
    else:
        if cliente_http is None:
            from adaptadores.cliente_http import ClienteCripta   # solo si hay red
            cliente_http = ClienteCripta(url)
        cliente = ClientePersistente(cliente_http, almacen)

    return ServicioCripta(cliente, CacheLRU(cache_size))
