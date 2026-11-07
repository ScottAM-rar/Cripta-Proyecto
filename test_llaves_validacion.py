"""Capacidad 009: lector y validador de la respuesta de llaves (FR-302, FR-311).

Una prueba por fila de la tabla «Casos de validación» de specs/009-contrato-datos-v2/contracts/consulta-llaves.md,
más las pruebas de `leer_llaves`, la del contenido no guardado con un espía y la del orden. Sin red."""
import unittest

from adaptadores.llaves import LlavesInvalidas, leer_llaves, validar_llaves

# Esqueleto de prueba: salas 0..9, sin la sala 5 (un hueco en los ids).
EXISTE = [True, True, True, True, True, False, True, True, True, True]


def sin_contenido(_sala):
    """Ninguna sala tiene el contenido guardado."""
    return None


class EspiaContenido:
    """`contenido_guardado` que anota qué salas se consultaron. `guardado` es una lista de pares (sala, contenido)."""

    def __init__(self, guardado=None):
        self.guardado = guardado or []
        self.consultadas: list[int] = []

    def __call__(self, sala):
        self.consultadas.append(sala)
        for numero, contenido in self.guardado:
            if numero == sala:
                return contenido
        return None


def validar(crudas, contenido_guardado=sin_contenido):
    return validar_llaves(crudas, EXISTE, contenido_guardado)


class CasosDeValidacion(unittest.TestCase):
    """Las 9 filas de la tabla, en el mismo orden."""

    def test_fr311_fila1_lista_vacia_es_valida_con_0_llaves(self):
        ids, salas, enemigos = validar(leer_llaves({"llaves": []}))
        self.assertEqual((ids, salas, enemigos), ([], [], []))

    def test_fr311_fila2_falta_llaves_o_no_es_lista_es_invalida(self):
        for respuesta in ({}, {"llaves": None}, {"llaves": "itm_llave_bronce"}, {"llaves": {"id": "x", "sala": 1}}):
            with self.subTest(respuesta=respuesta):
                with self.assertRaises(LlavesInvalidas):
                    leer_llaves(respuesta)

    def test_fr311_fila3_entrada_sin_id_sin_sala_sala_no_entera_o_id_vacio_es_invalida(self):
        casos = (
            {"sala": 1},                              # sin id
            {"id": "itm_llave_bronce"},               # sin sala
            {"id": "itm_llave_bronce", "sala": "1"},  # sala no entera
            {"id": "itm_llave_bronce", "sala": 1.0},  # sala no entera
            {"id": "itm_llave_bronce", "sala": True}, # bool no cuenta como entero (T006)
            {"id": "", "sala": 1},                    # id vacío
            {"id": 7, "sala": 1},                     # id que no es texto
            {"id": "itm_llave_bronce", "sala": 1, "enemigo": 401},  # enemigo que no es texto
            "itm_llave_bronce",                       # la entrada no es un objeto
        )
        for entrada in casos:
            with self.subTest(entrada=entrada):
                with self.assertRaises(LlavesInvalidas):
                    validar([entrada])

    def test_fr311_fila4_sala_fuera_del_esqueleto_es_invalida(self):
        for sala in (-1, 10, 99, 5):              # 5 está dentro del rango pero no existe en el esqueleto
            with self.subTest(sala=sala):
                with self.assertRaises(LlavesInvalidas):
                    validar([{"id": "itm_llave_bronce", "sala": sala}])

    def test_fr302_fila5_misma_llave_en_salas_3_y_9_es_valida_con_2_ubicaciones(self):
        ids, salas, enemigos = validar([{"id": "itm_llave_bronce", "sala": 3},
                                        {"id": "itm_llave_bronce", "sala": 9}])
        self.assertEqual(ids, ["itm_llave_bronce", "itm_llave_bronce"])
        self.assertEqual(salas, [3, 9])
        self.assertEqual(enemigos, [None, None])

    def test_fr302_fila6_misma_llave_misma_sala_enemigos_distintos_es_valida(self):
        ids, salas, enemigos = validar([{"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"},
                                        {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-402"}])
        self.assertEqual(ids, ["itm_llave_negra", "itm_llave_negra"])
        self.assertEqual(salas, [4, 4])
        self.assertEqual(enemigos, ["e-401", "e-402"])

    def test_fr311_fila7_dos_entradas_identicas_es_invalida(self):
        casos = (
            [{"id": "itm_llave_bronce", "sala": 3}, {"id": "itm_llave_bronce", "sala": 3}],
            [{"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"},
             {"id": "itm_llave_bronce", "sala": 1},
             {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}],          # repetidas no contiguas
            [{"id": "itm_llave_bronce", "sala": 3}, {"id": "itm_llave_bronce", "sala": 3, "enemigo": None}],
        )
        for crudas in casos:
            with self.subTest(crudas=crudas):
                with self.assertRaises(LlavesInvalidas):
                    validar(crudas)

    def test_fr311_fila8_enemigo_presente_contenido_guardado_sin_ese_enemigo_es_invalida(self):
        espia = EspiaContenido([(4, {"enemigos": [{"instancia": "e-402", "tipo": "ent_rata_gigante"}]})])
        with self.assertRaises(LlavesInvalidas):
            validar([{"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}], espia)

    def test_fr311_fila9_enemigo_presente_contenido_no_guardado_es_valida_sin_solicitudes(self):
        espia = EspiaContenido()
        ids, salas, enemigos = validar([{"id": "itm_llave_bronce", "sala": 1},
                                        {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}], espia)
        self.assertEqual(enemigos, [None, "e-401"])
        # Solo se consultó la sala de la entrada con enemigo, una vez; la entrada en el suelo no consulta nada.
        # El validador no recibe ningún cliente: lo único que puede leer es el espía, y este no hace solicitudes.
        self.assertEqual(espia.consultadas, [4])


class LeerLlaves(unittest.TestCase):

    def test_fr311_respuesta_sin_llaves_es_invalida(self):
        with self.assertRaises(LlavesInvalidas) as error:
            leer_llaves({"otra": []})
        self.assertTrue(error.exception.motivo)

    def test_fr311_llaves_que_no_es_lista_es_invalida(self):
        with self.assertRaises(LlavesInvalidas):
            leer_llaves({"llaves": {"id": "itm_llave_bronce", "sala": 3}})

    def test_fr302_llaves_vacia_devuelve_lista_vacia(self):
        self.assertEqual(leer_llaves({"llaves": []}), [])

    def test_fr302_devuelve_la_lista_tal_cual(self):
        crudas = [{"id": "itm_llave_bronce", "sala": 3}, {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}]
        self.assertIs(leer_llaves({"llaves": crudas}), crudas)


class EnemigoConContenidoGuardado(unittest.TestCase):

    def test_fr302_enemigo_que_esta_en_el_contenido_guardado_es_valido(self):
        espia = EspiaContenido([(4, {"enemigos": [{"instancia": "e-402"}, {"instancia": "e-401"}]})])
        _, _, enemigos = validar([{"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}], espia)
        self.assertEqual(enemigos, ["e-401"])
        self.assertEqual(espia.consultadas, [4])


class OrdenDeLaRespuesta(unittest.TestCase):

    def test_fr302_se_conserva_el_orden_de_la_respuesta(self):
        crudas = [{"id": "itm_llave_plata", "sala": 9},
                  {"id": "itm_llave_bronce", "sala": 3},
                  {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"},
                  {"id": "itm_llave_bronce", "sala": 1},
                  {"id": "itm_llave_oro", "sala": 0}]
        ids, salas, enemigos = validar(crudas)
        self.assertEqual(ids, ["itm_llave_plata", "itm_llave_bronce", "itm_llave_negra", "itm_llave_bronce",
                               "itm_llave_oro"])
        self.assertEqual(salas, [9, 3, 4, 1, 0])
        self.assertEqual(enemigos, [None, None, "e-401", None, None])

    def test_fr302_mismo_resultado_en_dos_ejecuciones(self):
        crudas = [{"id": "itm_llave_bronce", "sala": 3}, {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}]
        self.assertEqual(validar(crudas), validar(crudas))


if __name__ == "__main__":
    unittest.main()
