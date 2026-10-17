"""Partidas sintéticas para medir el modelo real (guardado y ciclo de eventos) sin red ni la cripta real."""
from __future__ import annotations

import tempfile

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.bench_red_mejorado import ClienteSintetico
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica

FICHA_ENEMIGO = {"id": "ent_bench", "clase": "enemigo", "nombre": "Esbirro", "vida_max": 1_000_000, "ataque": 1,
                 "defensa": 0, "velocidad": 100, "comportamiento": "guardián", "suelta": []}


class ClienteDeBatalla(ClienteSintetico):
    """Cripta en rejilla con `enemigos` esbirros en la sala inicial y un jugador que no muere por el bench."""

    def __init__(self, ancho: int, alto: int, enemigos: int) -> None:
        super().__init__(ancho, alto)
        self.enemigos = enemigos

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["jugador"] = {"vida_max": 10 ** 9, "ataque": 6, "defensa": 2, "velocidad": 100}
        return datos

    def obtener_contenido(self, cripta_id, salas):
        self.llamadas += 1
        contenidos = []
        for numero in salas:
            enemigos = []
            if numero == 1:
                enemigos = [{"instancia": f"e-{i}", "tipo": "ent_bench"} for i in range(self.enemigos)]
            contenidos.append({"sala": numero, "enemigos": enemigos, "objetos": [], "trampas": []})
        return contenidos

    def obtener_catalogo(self, ids):
        self.llamadas += 1
        return [dict(FICHA_ENEMIGO)] if "ent_bench" in ids else []


def servicio_sintetico(carpeta: str, enemigos: int = 0, ancho: int = 5, alto: int = 5):
    cliente = ClienteDeBatalla(ancho, alto, enemigos)
    servicio = ServicioCripta(ClientePersistente(cliente, AlmacenDisco(carpeta)), CacheLRU(25))
    servicio.listar_criptas()
    return servicio, servicio.obtener_id_cripta(1)


def juego_sin_iniciar(carpeta: str, enemigos: int = 0) -> EstadoJuegoLogica:
    """Modelo real con el servicio listo pero sin partida en curso (para reproducir un log)."""
    RetrocesoLogica().reiniciar()
    servicio, _ = servicio_sintetico(tempfile.mkdtemp(dir=carpeta), enemigos)     # carpeta propia: la caché en disco no se reutiliza
    return EstadoJuegoLogica(None, None, servicio)


def nuevo_juego(carpeta: str, enemigos: int = 0) -> EstadoJuegoLogica:
    """Juego del modelo real sobre la cripta sintética (sin log en disco, sin vista)."""
    RetrocesoLogica().reiniciar()
    servicio, cripta = servicio_sintetico(tempfile.mkdtemp(dir=carpeta), enemigos)
    juego = EstadoJuegoLogica(1, cripta, servicio)
    juego.ingresarEnSala(juego.estadoJuego.jugador.id_sala_actual)     # como hace el controlador al empezar: carga la sala y activa a sus enemigos
    return juego


def partida_base():
    """Una partida real exportada a datos simples (jugador, reloj, bitácora...) para armar guardados de distinto tamaño."""
    with tempfile.TemporaryDirectory() as carpeta:
        return nuevo_juego(carpeta, 2).exportar_estado()
