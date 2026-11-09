"""Capacidad 003: interfaz de la verificación, texto del reporte y códigos de salida.

Clase `Contrato` (T010, grupo B): fija las firmas, los campos del resultado y la entrega provisional que recibe Fernanda
(contracts/interfaz-verificacion.md, data-model.md §3 y §5). Los módulos nuevos se importan dentro de cada prueba con
`try/except ImportError: self.fail(...)`, para que mientras no existan la prueba falle por aserción y no por un error de
importación. Las clases `Texto`, `CodigosDeSalida`, `VerificarSinPartida` y `AvisoForzado` se agregan en el grupo E (T034).

Todo corre con requests.get bloqueado: si algo intentara usar la red, la prueba fallaría."""
import dataclasses
import importlib
import inspect
import shutil
import tempfile
import unittest
from unittest import mock

import requests

from adaptadores import fabrica
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from tests_labs.api_falsa import HttpFalso, cargar_todo, nueva_ejecucion

CRIPTA = "cripta-01"


def _sin_red(*args, **kwargs):
    raise AssertionError("intento de red")


_parche_red = mock.patch.object(requests, "get", side_effect=_sin_red)


def setUpModule():
    _parche_red.start()


def tearDownModule():
    _parche_red.stop()


def parametros(funcion) -> list:
    """[(nombre, valor por defecto o '<sin defecto>')] de la firma, en orden."""
    resultado = []
    for nombre, parametro in inspect.signature(funcion).parameters.items():
        defecto = "<sin defecto>" if parametro.default is inspect.Parameter.empty else parametro.default
        resultado.append((nombre, defecto))
    return resultado


class Contrato(unittest.TestCase):
    """Firmas y entrega provisional del grupo B (FR-331, FR-339, FR-343, FR-344)."""

    def importar(self, modulo: str):
        try:
            return importlib.import_module(modulo)
        except ImportError as error:
            self.fail(f"{modulo} todavía no existe: {error}")

    def servicio_falso(self):
        servicio = ServicioCripta(HttpFalso(), CacheLRU(25))
        servicio.listar_criptas()
        return servicio

    def test_fr344_firmas_de_la_interfaz(self):
        verificacion = self.importar("Logica.VerificacionResolubilidad")
        reporte = self.importar("Logica.ReporteVerificacion")
        from Logica.EstadoJuegoLogica import EstadoJuegoLogica
        from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
        sin = "<sin defecto>"
        self.assertEqual(parametros(verificacion.verificar_resolubilidad),
                         [("mapa", sin), ("sala_inicial", sin), ("sala_salida", sin), ("llave_salida", sin),
                          ("llaves", sin), ("cripta_id", "")])
        self.assertEqual(parametros(verificacion.verificar), [("fuente", sin), ("cripta_id", sin), ("llaves", None)])
        self.assertEqual(parametros(EstadoJuegoServicio.verificar),
                         [("self", sin), ("cripta_id", sin), ("offline", None)])
        self.assertEqual(parametros(EstadoJuegoServicio.iniciarJuego),
                         [("self", sin), ("cripta", sin), ("semilla", None), ("offline", None), ("nombre_log", None),
                          ("forzar", False)])
        self.assertEqual(parametros(EstadoJuegoLogica.iniciarJuego),
                         [("self", sin), ("cripta", sin), ("semilla", None), ("pedir_llaves", True), ("forzar", False)])
        self.assertEqual(parametros(EstadoJuegoServicio.avisoResolubilidad), [("self", sin)])
        self.assertEqual(parametros(reporte.lineas_reporte), [("resultado", sin)])
        self.assertEqual(parametros(reporte.aviso_forzado), [("resultado", sin)])

    def test_fr331_codigo_salida(self):
        dto = self.importar("DTO.ResultadoVerificacionDTO")
        self.assertEqual(dto.ResultadoVerificacion(CRIPTA, resoluble=True).codigo_salida(), 0)
        self.assertEqual(dto.ResultadoVerificacion(CRIPTA, resoluble=False).codigo_salida(), 1)
        self.assertEqual(dto.ResultadoVerificacion(CRIPTA, resoluble=None, motivo_error="x").codigo_salida(), 2)

    def test_fr344_campos_del_resultado(self):
        dto = self.importar("DTO.ResultadoVerificacionDTO")
        nombres = [campo.name for campo in dataclasses.fields(dto.ResultadoVerificacion)]
        self.assertEqual(nombres, ["cripta_id", "resoluble", "orden", "salas_alcanzables", "salas_no_alcanzables",
                                   "bloqueos", "causas", "llave_salida", "sala_salida", "motivo_error"])
        self.assertEqual([campo.name for campo in dataclasses.fields(dto.PasoLlaveDTO)], ["llave", "sala", "enemigo"])
        self.assertEqual([campo.name for campo in dataclasses.fields(dto.BloqueoDTO)],
                         ["sala_origen", "direccion", "sala_destino", "llave", "salas_de_la_llave", "tipo"])
        uno = dto.ResultadoVerificacion(CRIPTA, resoluble=None, motivo_error="x")
        otro = dto.ResultadoVerificacion(CRIPTA, resoluble=None, motivo_error="x")
        for nombre in ("orden", "salas_alcanzables", "bloqueos", "causas"):
            self.assertEqual(getattr(uno, nombre), [], nombre)
            self.assertIsNot(getattr(uno, nombre), getattr(otro, nombre), f"{nombre} se comparte entre instancias")
        self.assertEqual(uno.salas_no_alcanzables, 0)
        self.assertEqual((uno.llave_salida, uno.sala_salida), (None, None))
        self.assertEqual(dto.CAUSAS_EN_ORDEN, ("LLAVE_SALIDA_INEXISTENTE", "SALIDA_SIN_CAMINO", "SALIDA_BLOQUEADA",
                                               "LLAVE_SALIDA_INALCANZABLE"))
        self.assertEqual((dto.SIN_LLAVE, dto.LLAVE_INEXISTENTE, dto.CICLO, dto.LLAVE_SIN_CAMINO),
                         ("SIN_LLAVE", "LLAVE_INEXISTENTE", "CICLO", "LLAVE_SIN_CAMINO"))

    def test_fr339_cripta_no_resoluble_es_runtime_error(self):
        verificacion = self.importar("Logica.VerificacionResolubilidad")
        dto = self.importar("DTO.ResultadoVerificacionDTO")
        self.assertTrue(issubclass(verificacion.CriptaNoResoluble, RuntimeError))
        resultado = dto.ResultadoVerificacion(CRIPTA, resoluble=None, motivo_error="motivo de prueba")
        error = verificacion.CriptaNoResoluble(resultado)
        self.assertIs(error.resultado, resultado)
        self.assertIn("motivo de prueba", str(error))

    def test_fr344_fuente_entrega_sala_inicial_y_llave_salida(self):
        from Logica.FuenteCripta import FuenteCripta
        for nombre in ("obtener_sala_inicial", "obtener_llave_salida"):
            self.assertTrue(hasattr(FuenteCripta, nombre), f"FuenteCripta no declara {nombre}")
        servicio = self.servicio_falso()
        for nombre in ("obtener_sala_inicial", "obtener_llave_salida"):
            if not hasattr(servicio, nombre):
                self.fail(f"ServicioCripta no tiene {nombre}")
        self.assertEqual(servicio.obtener_sala_inicial(CRIPTA), 1)
        self.assertEqual(servicio.obtener_llave_salida(CRIPTA), "itm_llave_negra")

        carpeta = tempfile.mkdtemp(prefix="cripta_003_contrato_")
        try:
            _http, _cliente, guardado = nueva_ejecucion(carpeta)
            cargar_todo(guardado)
            guardado.ubicacion_llaves(CRIPTA)
            fuente = fabrica.crear_fuente_solo_local(carpeta=carpeta)
            for nombre in ("obtener_sala_inicial", "obtener_llave_salida"):
                if not hasattr(fuente, nombre):
                    self.fail(f"FuenteSoloLocal no tiene {nombre}")
            self.assertEqual(fuente.obtener_sala_inicial(CRIPTA), 1)
            self.assertEqual(fuente.obtener_llave_salida(CRIPTA), "itm_llave_negra")
            self.assertEqual(fuente.fuente.solicitudes_realizadas, 0)
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)

    def test_fr343_sin_datos_devuelve_codigo_2(self):
        """Reemplaza a test_fr343_cuerpo_provisional_devuelve_codigo_2 (T032, grupo D): desde que el cuerpo dejó de ser
        provisional, el código 2 solo aparece cuando faltan datos. Aquí el servicio no responde a la consulta de llaves
        (fallo real de la API falsa v2): no se inventa un resultado (FR-343)."""
        verificacion = self.importar("Logica.VerificacionResolubilidad")
        reporte = self.importar("Logica.ReporteVerificacion")
        from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
        from tests_labs.api_falsa import HttpConfigurable
        from tests_labs.cripta_sintetica import esqueleto_lineal

        servicio = ServicioCripta(HttpConfigurable(esqueleto_lineal([None, None]), sala_salida=3,
                                                   fallo_llaves="sin_respuesta"), CacheLRU(25))
        servicio.listar_criptas()
        resultado = verificacion.verificar(servicio, CRIPTA)
        self.assertIsNone(resultado.resoluble)
        self.assertEqual(resultado.codigo_salida(), 2)
        self.assertIn(CRIPTA, resultado.motivo_error)
        self.assertEqual((resultado.orden, resultado.salas_alcanzables, resultado.bloqueos, resultado.causas),
                         ([], [], [], []))
        self.assertEqual(reporte.lineas_reporte(resultado),
                         [f"Verificación de la cripta {CRIPTA}: NO SE PUDO VERIFICAR.", resultado.motivo_error])

        juego = EstadoJuegoServicio(comunicacion=servicio)
        desde_servicio = juego.verificar(CRIPTA)
        self.assertIsNone(desde_servicio.resoluble)
        self.assertEqual(desde_servicio.codigo_salida(), 2)
        self.assertFalse(juego._estadoJuegoLogica.iniciado)          # verificar no inicia la partida
        self.assertIsNone(juego.avisoResolubilidad())                # sin partida no hay aviso


if __name__ == "__main__":
    unittest.main()
