"""Capacidad 009, T023: lectura solo local, sin red y sin modificar lo guardado (FR-314 a FR-317, SC-003).

Las carpetas se arman con la API falsa v2 (cripta_v2) por el flujo normal: ServicioCripta sobre ClientePersistente.
Durante las operaciones solo locales, requests.get queda bloqueado y el cliente HTTP que pudiera armar la fábrica es un
HttpFalso espía, que no debe recibir ninguna llamada."""
from adaptadores.fuente_solo_local import FuenteSoloLocal

import os
import tempfile
import unittest
from unittest import mock

import requests

from adaptadores import fabrica
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from Logica.FuenteCripta import DatoLocalFaltante
from tests_labs.api_falsa import HttpFalso, cripta_v2

CRIPTA = "cripta-01"
SALA_QUE_FALTA = 5


def _sin_red(*args, **kwargs):
    raise AssertionError("intento de red")


def servicio_normal(carpeta, http=None):
    return ServicioCripta(ClientePersistente(http or cripta_v2(semilla=0), AlmacenDisco(carpeta)), CacheLRU(25))


def guardar_cripta_completa(carpeta):
    servicio = servicio_normal(carpeta)
    servicio.listar_criptas()
    servicio.crear_jugador(CRIPTA)
    servicio.construir_todas(CRIPTA)
    servicio.ubicacion_llaves(CRIPTA)


def guardar_cripta_sin_sala_5(carpeta):
    """Lo mismo, pero el contenido se trae sala por sala y la 5 nunca se pide: el archivo no tiene contenido:5."""
    servicio = servicio_normal(carpeta)
    servicio.listar_criptas()
    servicio.crear_jugador(CRIPTA)
    numeros = [sala["id"] for sala in servicio._cargar_esqueleto(CRIPTA) if sala["id"] != SALA_QUE_FALTA]
    servicio.construir_salas(CRIPTA, numeros)
    servicio.ubicacion_llaves(CRIPTA)


def bytes_de_la_carpeta(carpeta):
    """(nombre, bytes) de cada archivo de la carpeta, en orden de nombre."""
    resultado = []
    for nombre in sorted(os.listdir(carpeta)):
        with open(os.path.join(carpeta, nombre), "rb") as archivo:
            resultado.append((nombre, archivo.read()))
    return resultado


def campos_llaves(dto):
    return (dto.cripta_id, dto.version, dto.ids, dto.salas, dto.enemigos)


def campos_jugador(jugador):
    """JugadorDTO trae un InventarioLogica, que no se compara por valor: se comparan los campos que vienen de disco."""
    return (jugador.vida_actual, jugador.vida_max, jugador.ataque, jugador.defensa, jugador.velocidad,
            jugador.id_sala_actual, jugador.inventario.capacidad_maxima)


class SoloLocal(unittest.TestCase):
    """Cada prueba arma su carpeta y comprueba (d): el espía sin llamadas y los archivos byte a byte iguales."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)          # se registra primero: corre al final, después de comprobar (d)
        self.carpeta = os.path.join(self._tmp.name, "datos_cripta")
        self.espia = HttpFalso()

    def solo_local(self, version_vigente=None):
        """Abre la fuente solo local con la red bloqueada y el espía como único cliente HTTP posible, y comprueba (d)
        al terminar la prueba."""
        antes = bytes_de_la_carpeta(self.carpeta)
        parches = [mock.patch.object(requests, "get", side_effect=_sin_red),
                   mock.patch.object(fabrica, "_cliente_http_de_ejecucion", side_effect=lambda url: self.espia)]
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)
        self.addCleanup(self.comprobar_sin_cambios, antes)
        return fabrica.crear_fuente_solo_local(carpeta=self.carpeta, version_vigente=version_vigente)

    def comprobar_sin_cambios(self, antes):
        # (d) SC-003 / FR-315: ninguna solicitud y lo guardado queda igual, byte a byte.
        self.assertEqual(self.espia.llamadas, [])
        self.assertEqual(bytes_de_la_carpeta(self.carpeta), antes)

    def version_guardada(self):
        return AlmacenDisco(self.carpeta).version_cripta(CRIPTA)


class DatoFaltante(SoloLocal):

    def test_fr315_a_h4_1_sin_contenido_de_la_sala_5_falla_nombrando_sala_y_cripta(self):
        guardar_cripta_sin_sala_5(self.carpeta)
        self.assertIsNone(AlmacenDisco(self.carpeta).leer_contenido(CRIPTA, SALA_QUE_FALTA))
        fuente = self.solo_local()
        self.assertIsInstance(fuente, FuenteSoloLocal)
        with self.assertRaises(DatoLocalFaltante) as error:
            fuente.construir_sala(CRIPTA, SALA_QUE_FALTA)
        self.assertIn("sala 5", str(error.exception))
        self.assertIn(CRIPTA, str(error.exception))


class IgualQueLaViaNormal(SoloLocal):

    def test_fr314_fr316_b_h4_2_con_la_cache_completa_da_lo_mismo_que_la_via_normal(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        local = (fuente.esqueleto(CRIPTA), [fuente.construir_sala(CRIPTA, n) for n in (1, SALA_QUE_FALTA, 25)],
                 campos_llaves(fuente.ubicacion_llaves(CRIPTA)), campos_jugador(fuente.crear_jugador(CRIPTA)), fuente.total_salas(CRIPTA))
        self.comprobar_sin_cambios(bytes_de_la_carpeta(self.carpeta))   # antes de abrir la vía normal

        # La vía normal, con la misma carpeta: un HttpFalso que no trae nada nuevo (todo sale del disco).
        http = cripta_v2(semilla=0)
        normal = servicio_normal(self.carpeta, http)
        esperado = (normal.esqueleto(CRIPTA), [normal.construir_sala(CRIPTA, n) for n in (1, SALA_QUE_FALTA, 25)],
                    campos_llaves(normal.ubicacion_llaves(CRIPTA)), campos_jugador(normal.crear_jugador(CRIPTA)),
                    normal.total_salas(CRIPTA))
        self.assertEqual(http.veces("salas") + http.veces("contenido") + http.veces("llaves"), 0)
        self.assertEqual(local, esperado)


class VersionDistinta(SoloLocal):

    def test_fr317_c_h4_3_con_otra_version_vigente_toda_operacion_falla_nombrando_las_dos(self):
        guardar_cripta_completa(self.carpeta)
        guardada = self.version_guardada()
        fuente = self.solo_local(version_vigente="v-nueva")
        operaciones = [("esqueleto", lambda: fuente.esqueleto(CRIPTA)),
                       ("construir_sala", lambda: fuente.construir_sala(CRIPTA, 1)),
                       ("ubicacion_llaves", lambda: fuente.ubicacion_llaves(CRIPTA)),
                       ("datos_cripta", lambda: fuente.datos_cripta(CRIPTA)),
                       ("crear_jugador", lambda: fuente.crear_jugador(CRIPTA)),
                       ("version_cripta", lambda: fuente.version_cripta(CRIPTA)),
                       ("total_salas", lambda: fuente.total_salas(CRIPTA)),
                       ("precargar_vecinas", lambda: fuente.precargar_vecinas(CRIPTA, 1)),
                       ("reporte", lambda: fuente.reporte(CRIPTA))]
        for nombre, operacion in operaciones:
            with self.subTest(operacion=nombre):
                with self.assertRaises(DatoLocalFaltante) as error:
                    operacion()
                self.assertIn(guardada, str(error.exception))
                self.assertIn("v-nueva", str(error.exception))
                self.assertIn(CRIPTA, str(error.exception))

    def test_fr317_c_sin_version_guardada_falla_aunque_no_se_pida_una(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        with self.assertRaises(DatoLocalFaltante) as error:
            fuente.esqueleto("cripta-sin-guardar")
        self.assertIn("cripta-sin-guardar", str(error.exception))


class SinPrecarga(SoloLocal):

    def test_fr316_e_precargar_vecinas_devuelve_0_y_reporte_0_solicitudes(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        self.assertEqual(fuente.precargar_vecinas(CRIPTA, 1), 0)
        self.assertEqual(fuente.precargar_vecinas(CRIPTA, 1, 3), 0)
        self.assertEqual(fuente.reporte(CRIPTA).solicitudes, 0)


if __name__ == "__main__":
    unittest.main()
