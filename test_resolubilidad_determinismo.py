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


if __name__ == "__main__":
    unittest.main()
