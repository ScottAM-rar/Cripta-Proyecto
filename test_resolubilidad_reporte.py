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


def caso(codigo: str):
    from tests_labs.api_falsa import CASOS_APENDICE_B
    for cod, _descripcion, constructor in CASOS_APENDICE_B:
        if cod == codigo:
            return constructor()
    raise AssertionError(f"CASOS_APENDICE_B no tiene el caso {codigo}")


def servicio_de_caso(codigo: str):
    http, _guion = caso(codigo)
    servicio = ServicioCripta(http, CacheLRU(25))
    servicio.listar_criptas()
    return servicio


class BaseTexto(unittest.TestCase):
    """Texto del reporte (grupo E, T034; contracts/reporte-verificacion.md). Las ramas todavía no implementadas lanzan
    NotImplementedError: se envuelve con self.fail para que la prueba falle por aserción."""

    def verificar_caso(self, codigo: str):
        from Logica.VerificacionResolubilidad import verificar
        return verificar(servicio_de_caso(codigo), CRIPTA)

    def lineas(self, resultado) -> list:
        from Logica.ReporteVerificacion import lineas_reporte
        try:
            return lineas_reporte(resultado)
        except NotImplementedError as error:
            self.fail(f"lineas_reporte todavía no implementa este caso: {error}")

    def aviso(self, resultado) -> str:
        from Logica.ReporteVerificacion import aviso_forzado
        try:
            return aviso_forzado(resultado)
        except NotImplementedError as error:
            self.fail(f"aviso_forzado todavía no está implementado: {error}")


def no_resoluble(bloqueos, causas, alcanzables=(1,), no_alcanzables=1, llave_salida="itm_llave_salida", sala_salida=2):
    from DTO.ResultadoVerificacionDTO import ResultadoVerificacion
    return ResultadoVerificacion(CRIPTA, False, salas_alcanzables=list(alcanzables), salas_no_alcanzables=no_alcanzables,
                                 bloqueos=list(bloqueos), causas=list(causas), llave_salida=llave_salida,
                                 sala_salida=sala_salida)


class Texto(BaseTexto):

    def test_fr336_resoluble_muestra_orden_con_sala_y_enemigo(self):
        self.assertEqual(self.lineas(self.verificar_caso("B-R3")), [
            "Verificación de la cripta cripta-01: RESOLUBLE.",
            "Orden de obtención de llaves:",
            "  1. itm_llave_a en la sala 2",
            "  2. itm_llave_b en la sala 3",
            "  3. itm_llave_salida en la sala 5 (llave de salida)",
        ])
        self.assertEqual(self.lineas(self.verificar_caso("B-R2")), [
            "Verificación de la cripta cripta-01: RESOLUBLE.",
            "Orden de obtención de llaves:",
            "  1. itm_llave_salida en la sala 3, la suelta e-errante (llave de salida)",
        ])

    def test_fr337_lista_salas_alcanzables(self):
        from DTO.ResultadoVerificacionDTO import SALIDA_BLOQUEADA, SIN_LLAVE, BloqueoDTO
        r = no_resoluble([BloqueoDTO(4, "este", 7, None, [], SIN_LLAVE)], [SALIDA_BLOQUEADA],
                         alcanzables=(1, 2, 4), no_alcanzables=3, sala_salida=7)
        lineas = self.lineas(r)
        self.assertEqual(lineas[-2:], ["Salas alcanzables (3): 1, 2, 4", "Salas no alcanzables: 3"])

    def test_fr338_texto_por_tipo_de_bloqueo(self):
        from DTO.ResultadoVerificacionDTO import (CICLO, LLAVE_INEXISTENTE, LLAVE_SIN_CAMINO, SALIDA_BLOQUEADA,
                                                  SIN_LLAVE, BloqueoDTO)
        r = no_resoluble([BloqueoDTO(1, "norte", 2, None, [], SIN_LLAVE),
                          BloqueoDTO(1, "sur", 3, "itm_llave_perdida", [], LLAVE_INEXISTENTE),
                          BloqueoDTO(1, "este", 4, "itm_llave_k", [4, 9], CICLO),
                          BloqueoDTO(1, "oeste", 5, "itm_llave_salida", [8], LLAVE_SIN_CAMINO)],
                         [SALIDA_BLOQUEADA], no_alcanzables=5, sala_salida=4)
        self.assertEqual(self.lineas(r)[2:7], [
            "Puertas bloqueadas:",
            "  - Sala 1, salida norte hacia la sala 2: está cerrada y no tiene llave.",
            "  - Sala 1, salida sur hacia la sala 3: pide itm_llave_perdida, que no existe en la cripta.",
            "  - Sala 1, salida este hacia la sala 4: pide itm_llave_k, que está en las salas 4, 9. Ciclo: la llave "
            "está detrás de esta puerta o de otras puertas bloqueadas.",
            "  - Sala 1, salida oeste hacia la sala 5: pide itm_llave_salida (llave de salida), que está en la sala 8, "
            "sin camino desde la sala inicial.",
        ])

    def test_fr338_texto_por_causa(self):
        from DTO.ResultadoVerificacionDTO import (LLAVE_SALIDA_INALCANZABLE, LLAVE_SALIDA_INEXISTENTE,
                                                  SALIDA_BLOQUEADA, SALIDA_SIN_CAMINO)
        casos = [
            ([LLAVE_SALIDA_INEXISTENTE, SALIDA_BLOQUEADA],
             ["Motivo: la llave de salida itm_llave_salida no existe en la cripta.",
              "Motivo: la sala de salida 2 tiene camino, pero las puertas lo impiden."]),
            ([SALIDA_SIN_CAMINO],
             ["Motivo: la sala de salida 2 no tiene camino desde la sala inicial, aunque se tuvieran todas las llaves."]),
            ([LLAVE_SALIDA_INALCANZABLE],
             ["Motivo: se llega a la sala de salida 2, pero la llave de salida itm_llave_salida no se puede obtener."]),
        ]
        for causas, esperadas in casos:
            lineas = self.lineas(no_resoluble([], causas))
            self.assertEqual(lineas[0], "Verificación de la cripta cripta-01: NO RESOLUBLE.")
            self.assertEqual(lineas[1:1 + len(esperadas)], esperadas, causas)
            self.assertNotIn("Puertas bloqueadas:", lineas)       # sin bloqueos no se escribe el encabezado

    def test_fr338_b_r1_reporte_completo(self):
        self.assertEqual(self.lineas(self.verificar_caso("B-R1")), [
            "Verificación de la cripta cripta-01: NO RESOLUBLE.",
            "Motivo: la sala de salida 2 tiene camino, pero las puertas lo impiden.",
            "Puertas bloqueadas:",
            "  - Sala 1, salida este hacia la sala 2: pide itm_llave_salida (llave de salida), que está en la sala 2. "
            "Ciclo: la llave está detrás de esta puerta o de otras puertas bloqueadas.",
            "Salas alcanzables (1): 1",
            "Salas no alcanzables: 1",
        ])
        b_r4 = self.lineas(self.verificar_caso("B-R4"))
        self.assertIn("  - Sala 1, salida este hacia la sala 2: pide itm_llave_perdida, que no existe en la cripta.", b_r4)

    def test_fr343_reporte_de_error(self):
        from DTO.ResultadoVerificacionDTO import ResultadoVerificacion
        r = ResultadoVerificacion(CRIPTA, None, motivo_error="No se pudieron obtener las llaves de la cripta cripta-01.")
        self.assertEqual(self.lineas(r), ["Verificación de la cripta cripta-01: NO SE PUDO VERIFICAR.",
                                          "No se pudieron obtener las llaves de la cripta cripta-01."])

    def test_fr335_mismo_resultado_mismo_reporte(self):
        primero = self.lineas(self.verificar_caso("B-R1"))
        segundo = self.lineas(self.verificar_caso("B-R1"))
        self.assertEqual("\n".join(primero), "\n".join(segundo))


class CodigosDeSalida(BaseTexto):

    def test_fr331_resoluble_0_no_resoluble_1_error_2(self):
        from Logica.VerificacionResolubilidad import verificar
        from tests_labs.api_falsa import HttpConfigurable
        from tests_labs.cripta_sintetica import esqueleto_lineal
        self.assertEqual(self.verificar_caso("B-R3").codigo_salida(), 0)
        self.assertEqual(self.verificar_caso("B-R1").codigo_salida(), 1)
        sin_llaves = ServicioCripta(HttpConfigurable(esqueleto_lineal([None]), sala_salida=2,
                                                     fallo_llaves="sin_respuesta"), CacheLRU(25))
        sin_llaves.listar_criptas()
        self.assertEqual(verificar(sin_llaves, CRIPTA).codigo_salida(), 2)


class VerificarSinPartida(BaseTexto):

    def test_fr330_verificar_no_inicia_partida_ni_crea_log_ni_vista(self):
        from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
        juego = EstadoJuegoServicio(comunicacion=servicio_de_caso("B-R3"))
        with mock.patch("adaptadores.AlmacenLogTexto.AlmacenLogTexto.abrir") as abrir, \
                mock.patch("Controlador.Vista.VistaConsola.__init__", side_effect=AssertionError("se creó la vista")):
            resultado = juego.verificar(CRIPTA)
        self.assertIs(resultado.resoluble, True)
        self.assertFalse(juego._estadoJuegoLogica.iniciado)
        abrir.assert_not_called()
        self.assertIsNone(juego.nombreLog())


class AvisoForzado(BaseTexto):

    def test_fr340_aviso_forzado_una_linea(self):
        aviso = self.aviso(self.verificar_caso("B-R1"))
        self.assertEqual(aviso, "AVISO: la cripta cripta-01 no es resoluble (la sala de salida 2 tiene camino, pero las "
                                "puertas lo impiden); la partida se inicia porque se usó --forzar.")
        self.assertNotIn("\n", aviso)


if __name__ == "__main__":
    unittest.main()
