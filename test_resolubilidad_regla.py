"""Capacidad 003, T025: regla de resolubilidad, orden y bloqueos sobre mapas hechos a mano (FR-332 a FR-334, FR-336 a
FR-338; escenarios H1-1, H1-3 a H1-7, H2-2 y H2-3).

Los mapas se arman con `esqueleto_de_conexiones` y `poner_puerta`/`mapa_desde_salas` (tests_labs), sin adaptadores; las
llaves, con `UbicacionLlavesDTO` directo. Se llama a la función pura `verificar_resolubilidad`, que se importa dentro de
cada prueba con `try/except ImportError: self.fail(...)`."""
import importlib
import unittest

from DTO.ResultadoVerificacionDTO import (CICLO, LLAVE_INEXISTENTE, LLAVE_SALIDA_INALCANZABLE, LLAVE_SALIDA_INEXISTENTE,
                                          LLAVE_SIN_CAMINO, SALIDA_BLOQUEADA, SALIDA_SIN_CAMINO, SIN_LLAVE, BloqueoDTO,
                                          PasoLlaveDTO)
from tests_labs.cripta_sintetica import esqueleto_de_conexiones
from tests_labs.referencia_resolubilidad import mapa_desde_salas, poner_puerta, ubicaciones

CRIPTA = "cripta-01"
S = "itm_llave_salida"


def conexion(a, b, letra_ab, letra_ba, **opciones):
    return (a, b, 100, letra_ab, letra_ba, opciones)


class Base(unittest.TestCase):

    def verificar(self, salas, sala_inicial, sala_salida, llave_salida, entradas):
        try:
            modulo = importlib.import_module("Logica.VerificacionResolubilidad")
        except ImportError as error:
            self.fail(f"Logica.VerificacionResolubilidad todavía no existe: {error}")
        return modulo.verificar_resolubilidad(mapa_desde_salas(salas), sala_inicial, sala_salida, llave_salida,
                                              ubicaciones(CRIPTA, entradas), CRIPTA)


class Regla(Base):

    def test_fr332_h1_1_salida_alcanzable_y_llave_obtenible_es_resoluble(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O"), conexion(2, 3, "E", "O")])
        r = self.verificar(salas, 1, 3, S, [(S, 2, None)])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO(S, 2, None)])
        self.assertEqual((r.bloqueos, r.causas), ([], []))
        self.assertEqual(r.codigo_salida(), 0)

    def test_fr332_sala_inicial_es_salida(self):
        salas = esqueleto_de_conexiones([], total=1)
        r = self.verificar(salas, 1, 1, S, [(S, 1, None)])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO(S, 1, None)])
        self.assertEqual(r.salas_alcanzables, [1])

    def test_fr332_no_exige_puerta_hacia_la_salida(self):
        # La llave de salida abre una puerta que no lleva a la salida; la salida se alcanza por salidas abiertas.
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O"), conexion(2, 3, "E", "O")])
        poner_puerta(salas, 2, 3, S)
        r = self.verificar(salas, 1, 2, S, [(S, 1, None)])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO(S, 1, None)])

    def test_fr333_h1_3_cadena_de_puertas(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O"), conexion(2, 3, "E", "O"), conexion(3, 4, "E", "O")])
        poner_puerta(salas, 1, 2, "itm_k1")
        poner_puerta(salas, 2, 3, "itm_k2")
        poner_puerta(salas, 3, 4, "itm_k3")
        r = self.verificar(salas, 1, 4, S, [("itm_k3", 3, None), ("itm_k1", 1, None), (S, 4, None), ("itm_k2", 2, None)])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO("itm_k1", 1), PasoLlaveDTO("itm_k2", 2), PasoLlaveDTO("itm_k3", 3),
                                   PasoLlaveDTO(S, 4)])

    def test_fr333_h1_6_respeta_salidas_de_un_solo_sentido(self):
        # Solo existe la salida 2 -> 1: desde la sala 1 no se llega a la 2, donde está la llave de salida.
        salas = esqueleto_de_conexiones([conexion(2, 1, "O", "E", un_sentido=True)])
        r = self.verificar(salas, 1, 1, S, [(S, 2, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.salas_alcanzables, [1])
        self.assertEqual(r.causas, [LLAVE_SALIDA_INALCANZABLE])
        self.assertEqual(r.bloqueos, [])
        # Al revés, empezando en la 2 se cruza la salida 2 -> 1 y la llave está en la sala inicial.
        r = self.verificar(salas, 2, 1, S, [(S, 2, None)])
        self.assertIs(r.resoluble, True)

    def test_fr333_puerta_sin_llave_nunca_se_cruza(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O")])
        poner_puerta(salas, 1, 2, None)
        r = self.verificar(salas, 1, 2, S, [(S, 1, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.salas_alcanzables, [1])

    def test_fr333_una_llave_abre_varias_puertas(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O"), conexion(2, 3, "E", "O")])
        poner_puerta(salas, 1, 2, "itm_k")
        poner_puerta(salas, 2, 3, "itm_k")
        r = self.verificar(salas, 1, 3, S, [("itm_k", 1, None), (S, 3, None)])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO("itm_k", 1), PasoLlaveDTO(S, 3)])

    def test_fr334_h2_2_enemigo_tras_puerta(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O")])
        poner_puerta(salas, 1, 2, "itm_k")
        # La puerta se abre: la llave que suelta e-1, que inicia en la sala 2, es obtenible.
        r = self.verificar(salas, 1, 2, S, [("itm_k", 1, None), (S, 2, "e-1")])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO("itm_k", 1), PasoLlaveDTO(S, 2, "e-1")])
        # La puerta no se abre (su llave no existe): la llave de e-1 no es obtenible.
        r = self.verificar(salas, 1, 2, S, [(S, 2, "e-1")])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.bloqueos, [BloqueoDTO(1, "este", 2, "itm_k", [], LLAVE_INEXISTENTE)])

    def test_fr334_h2_3_basta_una_ubicacion_alcanzable(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O"), conexion(1, 3, "S", "N")])
        poner_puerta(salas, 1, 3, None)
        r = self.verificar(salas, 1, 2, S, [(S, 3, None), (S, 2, None)])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO(S, 2)])

    def test_fr336_llave_salida_en_el_orden_una_vez(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O")])
        r = self.verificar(salas, 1, 2, S, [(S, 2, None), (S, 1, None), (S, 1, "e-1")])
        self.assertIs(r.resoluble, True)
        self.assertEqual(r.orden, [PasoLlaveDTO(S, 1, None)])


class Bloqueos(Base):

    def test_fr332_fr338_h1_4_salida_sin_camino(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O")], total=3)       # la sala 3 no tiene salidas
        r = self.verificar(salas, 1, 3, S, [(S, 1, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.causas, [SALIDA_SIN_CAMINO])
        self.assertEqual(r.bloqueos, [])
        self.assertEqual(r.orden, [])

    def test_fr332_fr338_h1_5_llave_salida_inexistente(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O")])
        r = self.verificar(salas, 1, 2, S, [("itm_otra", 1, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.causas, [LLAVE_SALIDA_INEXISTENTE])

    def test_fr337_salas_alcanzables_crecientes_y_cantidad_no_alcanzables(self):
        # Desde la 5 se llega a 4 y a 2 (se descubren en ese orden); la puerta 2-3 no tiene llave y 3-1 sigue detrás.
        salas = esqueleto_de_conexiones([conexion(5, 4, "N", "S"), conexion(4, 2, "N", "S"), conexion(2, 3, "E", "O"),
                                         conexion(3, 1, "E", "O")])
        poner_puerta(salas, 2, 3, None)
        r = self.verificar(salas, 5, 1, S, [(S, 5, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.salas_alcanzables, [2, 4, 5])
        self.assertEqual(r.salas_no_alcanzables, 2)

    def test_fr338_varios_bloqueos_en_orden(self):
        salas = esqueleto_de_conexiones([conexion(1, 3, "E", "O"), conexion(1, 4, "S", "N"), conexion(1, 5, "O", "E"),
                                         conexion(3, 6, "N", "S")])
        poner_puerta(salas, 1, 4, "itm_ka")                # no existe
        poner_puerta(salas, 1, 5, None)                    # sin llave
        poner_puerta(salas, 3, 6, "itm_kb")                # está en la 6, detrás de esta misma puerta
        r = self.verificar(salas, 3, 6, S, [("itm_kb", 6, None), (S, 1, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.bloqueos, [BloqueoDTO(1, "sur", 4, "itm_ka", [], LLAVE_INEXISTENTE),
                                      BloqueoDTO(1, "oeste", 5, None, [], SIN_LLAVE),
                                      BloqueoDTO(3, "norte", 6, "itm_kb", [6], CICLO)])
        self.assertEqual(r.causas, [SALIDA_BLOQUEADA])

    def test_fr338_puerta_sin_llave_es_bloqueo_sin_llave(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O")])
        poner_puerta(salas, 1, 2, None)
        r = self.verificar(salas, 1, 2, S, [(S, 1, None)])
        self.assertEqual(r.bloqueos, [BloqueoDTO(1, "este", 2, None, [], SIN_LLAVE)])
        self.assertEqual(r.causas, [SALIDA_BLOQUEADA])

    def test_fr338_h1_7_llave_en_sala_sin_camino_es_bloqueo_no_ciclo(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O")], total=3)       # la 3 no tiene ningún camino
        poner_puerta(salas, 1, 2, "itm_k")
        r = self.verificar(salas, 1, 2, S, [("itm_k", 3, None), (S, 1, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.bloqueos, [BloqueoDTO(1, "este", 2, "itm_k", [3], LLAVE_SIN_CAMINO)])
        self.assertEqual(r.causas, [SALIDA_BLOQUEADA])

    def test_fr338_ciclo_a_traves_de_otras_puertas(self):
        salas = esqueleto_de_conexiones([conexion(1, 2, "E", "O"), conexion(2, 3, "E", "O")])
        poner_puerta(salas, 1, 2, "itm_ka")                # itm_ka está en la 3, detrás de esta puerta y de la 2-3
        poner_puerta(salas, 2, 3, "itm_kb")
        r = self.verificar(salas, 1, 3, S, [("itm_ka", 3, None), ("itm_kb", 2, None), (S, 1, None)])
        self.assertIs(r.resoluble, False)
        self.assertEqual(r.bloqueos, [BloqueoDTO(1, "este", 2, "itm_ka", [3], CICLO)])
        self.assertEqual(r.salas_alcanzables, [1])


if __name__ == "__main__":
    unittest.main()
