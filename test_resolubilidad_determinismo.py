"""Capacidad 003, T027: determinismo del orden por oleadas y equivalencia con el oráculo (FR-335, FR-346; II, III).

- `Determinismo`: el ejemplo de dos oleadas de H3-2 (sala inicial 5), el orden de la respuesta de llaves no importa,
  suelo antes que enemigo y menor instancia, dos ejecuciones iguales.
- `Equivalencia`: en 20 criptas al azar por semilla, la verificación incremental da lo mismo que el oráculo
  `verificar_repetida` (tests_labs/referencia_resolubilidad.py), campo por campo.

La función se importa dentro de cada prueba con `try/except ImportError: self.fail(...)`. Las clases `Fuentes` y la
prueba con y sin contenido guardado se agregan en el grupo F (T039); `CadenaSintetica`, en el grupo H (T050)."""
import importlib
import unittest

from DTO.ResultadoVerificacionDTO import PasoLlaveDTO
from tests_labs.cripta_sintetica import esqueleto_de_conexiones
from tests_labs.referencia_resolubilidad import (cripta_al_azar_con_llaves, mapa_desde_salas, poner_puerta, ubicaciones,
                                                 verificar_repetida)

CRIPTA = "cripta-01"
A, B, C, X = "itm_llave_a", "itm_llave_b", "itm_llave_c", "itm_llave_x"


def conexion(a, b, letra_ab, letra_ba):
    return (a, b, 100, letra_ab, letra_ba)


def cripta_h3_2():
    """Escenario H3-2: sala inicial 5; desde ella se llega sin llaves a la 2 (A y B) y a la 4 (X); la sala 3 tiene la
    llave C y está detrás de una puerta que se abre con A. La salida es la 3 y su llave, C."""
    salas = esqueleto_de_conexiones([conexion(5, 2, "O", "E"), conexion(5, 4, "N", "S"), conexion(5, 3, "S", "N")])
    poner_puerta(salas, 5, 3, A)
    entradas = [(X, 4, None), (B, 2, None), (A, 2, None), (C, 3, None)]
    return salas, 5, 3, C, entradas


class Base(unittest.TestCase):

    def funcion(self):
        try:
            return importlib.import_module("Logica.VerificacionResolubilidad").verificar_resolubilidad
        except ImportError as error:
            self.fail(f"Logica.VerificacionResolubilidad todavía no existe: {error}")

    def verificar(self, salas, inicial, salida, llave_salida, entradas):
        return self.funcion()(mapa_desde_salas(salas), inicial, salida, llave_salida, ubicaciones(CRIPTA, entradas),
                              CRIPTA)


class Determinismo(Base):

    def test_fr335_h3_2_dos_oleadas(self):
        r = self.verificar(*cripta_h3_2())
        self.assertIs(r.resoluble, True)
        # Primera oleada: A y B (sala 2) y X (sala 4). C es de la oleada siguiente: va última aunque su sala (3) tenga
        # menor id que la de X (4).
        self.assertEqual(r.orden, [PasoLlaveDTO(A, 2), PasoLlaveDTO(B, 2), PasoLlaveDTO(X, 4), PasoLlaveDTO(C, 3)])

    def test_fr335_orden_de_la_respuesta_no_importa(self):
        salas, inicial, salida, llave_salida, entradas = cripta_h3_2()
        al_derecho = self.verificar(salas, inicial, salida, llave_salida, entradas)
        invertidas = [entradas[i] for i in range(len(entradas) - 1, -1, -1)]
        al_reves = self.verificar(salas, inicial, salida, llave_salida, invertidas)
        self.assertIs(al_derecho.resoluble, True)
        self.assertEqual(al_derecho, al_reves)

    def test_fr335_suelo_antes_que_enemigo_y_menor_instancia(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O"), conexion(1, 3, "S", "N")])
        s = "itm_llave_salida"
        k = "itm_llave_k"
        entradas = [(s, 2, "e-1"), (s, 2, None), (k, 3, "e-9"), (k, 3, "e-2")]
        r = self.verificar(salas, 1, 3, s, entradas)
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO(s, 2, None), PasoLlaveDTO(k, 3, "e-2")])

    def test_fr335_dos_ejecuciones_iguales(self):
        primero = self.verificar(*cripta_h3_2())
        segundo = self.verificar(*cripta_h3_2())
        self.assertIs(primero.resoluble, True)                # sin esto, dos resultados provisionales iguales pasarían
        self.assertEqual(primero, segundo)


class Equivalencia(Base):

    def test_fr335_fr346_incremental_igual_a_repetida_en_criptas_al_azar(self):
        verificar = self.funcion()
        for semilla in range(20):
            mapa, inicial, salida, llave_salida, llaves = cripta_al_azar_con_llaves(semilla)
            esperado = verificar_repetida(mapa, inicial, salida, llave_salida, llaves, CRIPTA)
            obtenido = verificar(mapa, inicial, salida, llave_salida, llaves, CRIPTA)
            self.assertIsNotNone(obtenido.resoluble, f"semilla {semilla}: no se verificó")
            self.assertEqual(obtenido, esperado, f"semilla {semilla}")


def caso_http(codigo: str):
    from tests_labs.api_falsa import CASOS_APENDICE_B
    for cod, _descripcion, constructor in CASOS_APENDICE_B:
        if cod == codigo:
            return constructor()[0]
    raise AssertionError(f"CASOS_APENDICE_B no tiene el caso {codigo}")


class ConServicio(unittest.TestCase):
    """Grupo F (T039): las mismas verificaciones a través de las fuentes reales, con requests.get bloqueado."""

    def setUp(self):
        import shutil
        import tempfile
        from unittest import mock

        import requests
        self.carpeta = tempfile.mkdtemp(prefix="cripta_003_fuentes_")
        self.addCleanup(shutil.rmtree, self.carpeta, True)
        parche = mock.patch.object(requests, "get", side_effect=AssertionError("intento de red"))
        parche.start()
        self.addCleanup(parche.stop)

    def directo(self, codigo: str):
        from adaptadores.cache import CacheLRU
        from adaptadores.servicioCripta import ServicioCripta
        servicio = ServicioCripta(caso_http(codigo), CacheLRU(25))
        servicio.listar_criptas()
        return servicio

    def verificar(self, fuente):
        try:
            return importlib.import_module("Logica.VerificacionResolubilidad").verificar(fuente, CRIPTA)
        except ImportError as error:
            self.fail(f"Logica.VerificacionResolubilidad todavía no existe: {error}")


class Fuentes(ConServicio):

    def test_fr342_h3_4_http_offline_y_solo_local_dan_lo_mismo(self):
        from adaptadores import fabrica
        from adaptadores.AlmacenDisco import AlmacenDisco
        from adaptadores.cache import CacheLRU
        from adaptadores.cliente_offline import ClienteOffline
        from adaptadores.cliente_persistente import ClientePersistente
        from adaptadores.servicioCripta import ServicioCripta
        for codigo in ("B-R1", "B-R2", "B-R3", "B-R4"):
            carpeta = f"{self.carpeta}/{codigo}"
            # Con red (cliente HTTP falso directo).
            con_red = self.verificar(self.directo(codigo))
            self.assertIsNotNone(con_red.resoluble, codigo)
            # Guardar la cripta completa por el flujo normal y leerla por --offline y por la lectura solo local.
            guardado = ServicioCripta(ClientePersistente(caso_http(codigo), AlmacenDisco(carpeta)), CacheLRU(25))
            guardado.listar_criptas()
            guardado.crear_jugador(CRIPTA)
            guardado.construir_todas(CRIPTA)
            guardado.ubicacion_llaves(CRIPTA)
            offline = ServicioCripta(ClienteOffline(AlmacenDisco(carpeta)), CacheLRU(25))
            offline.listar_criptas()
            solo_local = fabrica.crear_fuente_solo_local(carpeta=carpeta)
            self.assertEqual(self.verificar(offline), con_red, f"{codigo}: --offline")
            self.assertEqual(self.verificar(solo_local), con_red, f"{codigo}: lectura solo local")
            self.assertEqual(offline.solicitudes_realizadas, 0)
            self.assertEqual(solo_local.fuente.solicitudes_realizadas, 0)


class DeterminismoConContenido(ConServicio):

    def test_fr335_h3_3_con_y_sin_contenido_guardado(self):
        for codigo in ("B-R1", "B-R2", "B-R3", "B-R4"):
            servicio = self.directo(codigo)
            sin_contenido = self.verificar(servicio)
            servicio.crear_jugador(CRIPTA)
            servicio.construir_todas(CRIPTA)                     # ahora el contenido de todas las salas está traído
            con_contenido = self.verificar(servicio)
            otra_sesion = self.verificar(self.directo(codigo))   # sesión nueva, sin contenido
            self.assertIsNotNone(sin_contenido.resoluble, codigo)
            self.assertEqual(con_contenido, sin_contenido, codigo)
            self.assertEqual(otra_sesion, sin_contenido, codigo)


class CadenaSintetica(unittest.TestCase):
    """Grupo H (T050): la cripta sintética de llaves encadenadas del bench (data-model.md §7; FR-346, principio V).
    `esqueleto_llaves_encadenadas` se importa dentro de cada prueba con try/except ImportError: self.fail."""

    def generador(self):
        try:
            return importlib.import_module("tests_labs.cripta_sintetica").esqueleto_llaves_encadenadas
        except (ImportError, AttributeError) as error:
            self.fail(f"esqueleto_llaves_encadenadas todavía no existe: {error}")

    def verificar_cadena(self, n: int, semilla: int):
        esqueleto, llaves, llave_salida, sala_salida = self.generador()(n, semilla)
        resultado = importlib.import_module("Logica.VerificacionResolubilidad").verificar_resolubilidad(
            mapa_desde_salas(esqueleto), 1, sala_salida, llave_salida, ubicaciones(CRIPTA, llaves), CRIPTA)
        return esqueleto, llave_salida, sala_salida, resultado

    def test_fr346_cadena_determinista_por_semilla(self):
        generar = self.generador()
        self.assertEqual(generar(30, 7), generar(30, 7))
        _, llaves_7, _, _ = generar(30, 7)
        _, llaves_8, _, _ = generar(30, 8)
        self.assertNotEqual([e[0] for e in llaves_7], [e[0] for e in llaves_8])

    def test_fr346_cadena_es_resoluble_con_n_llaves(self):
        n = 50
        esqueleto, llave_salida, sala_salida, r = self.verificar_cadena(n, 3)
        self.assertEqual(sala_salida, n)
        self.assertIs(r.resoluble, True)
        self.assertEqual(len(r.orden), n)                      # n - 1 puertas + la llave de salida
        self.assertEqual(r.orden[-1].llave, llave_salida)
        # El orden sigue la cadena: el paso i es la llave de la puerta i+1 -> i+2 del pasillo.
        for i in range(n - 1):
            puerta = esqueleto[i]["salidas"]["E"]
            self.assertEqual(puerta["sala"], i + 2)
            self.assertTrue(puerta.get("cerrada"))
            self.assertEqual(puerta.get("llave"), r.orden[i].llave, f"paso {i}")

    def test_fr346_ids_no_siguen_la_cadena(self):
        _esqueleto, _llave_salida, _sala_salida, r = self.verificar_cadena(50, 3)
        ids = [paso.llave for paso in r.orden[:-1]]
        bajadas = 0
        for i in range(1, len(ids)):
            if ids[i] < ids[i - 1]:
                bajadas += 1
        self.assertGreater(bajadas, 0, "los ids de llave quedaron en el mismo orden que la cadena")


if __name__ == "__main__":
    unittest.main()
