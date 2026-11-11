"""Capacidad 009, T052: UbicacionLlavesDTO (FR-302). Sin red; solo usa DTO/LlavesDTO.py."""
import unittest

from DTO.LlavesDTO import UbicacionLlavesDTO


class UbicacionLlaves(unittest.TestCase):

    def test_fr302_a_listas_de_largo_distinto_lanzan_valueerror_que_nombra_la_cripta(self):
        casos = (
            (["itm_llave_bronce", "itm_llave_negra"], [3], [None]),
            (["itm_llave_bronce"], [3, 9], [None]),
            (["itm_llave_bronce"], [3], [None, "e-401"]),
        )
        for ids, salas, enemigos in casos:
            with self.subTest(ids=ids, salas=salas, enemigos=enemigos):
                with self.assertRaises(ValueError) as error:
                    UbicacionLlavesDTO("cripta-07", "v2", ids, salas, enemigos)
                self.assertIn("cripta-07", str(error.exception))

    def test_fr302_b_listas_vacias_son_validas_y_cantidad_es_0(self):
        llaves = UbicacionLlavesDTO("cripta-07", "v2", [], [], [])
        self.assertEqual(llaves.cantidad(), 0)
        self.assertEqual(llaves.ubicaciones_de("itm_llave_bronce"), [])

    def test_fr302_c_cantidad_es_igual_al_largo_de_las_listas(self):
        llaves = UbicacionLlavesDTO("cripta-07", "v2",
                                    ["itm_llave_bronce", "itm_llave_negra", "itm_llave_bronce"],
                                    [3, 4, 9],
                                    [None, "e-401", None])
        self.assertEqual(llaves.cantidad(), 3)
        self.assertEqual(llaves.cantidad(), len(llaves.ids))

    def test_fr302_d_ubicaciones_de_devuelve_las_posiciones_en_orden_y_vacia_si_no_existe(self):
        llaves = UbicacionLlavesDTO("cripta-07", "v2",
                                    ["itm_llave_bronce", "itm_llave_negra", "itm_llave_bronce"],
                                    [3, 4, 9],
                                    [None, "e-401", None])
        posiciones = llaves.ubicaciones_de("itm_llave_bronce")
        self.assertEqual(posiciones, [0, 2])
        self.assertEqual([llaves.salas[i] for i in posiciones], [3, 9])
        self.assertEqual(llaves.ubicaciones_de("itm_llave_negra"), [1])
        self.assertEqual(llaves.ubicaciones_de("itm_llave_oro"), [])

    def test_fr302_e_ids_salas_y_enemigos_conservan_el_orden_recibido(self):
        ids = ["itm_llave_plata", "itm_llave_bronce", "itm_llave_negra", "itm_llave_bronce"]
        salas = [9, 3, 4, 1]
        enemigos = [None, None, "e-401", None]
        llaves = UbicacionLlavesDTO("cripta-07", "v2", list(ids), list(salas), list(enemigos))
        self.assertEqual(llaves.ids, ids)
        self.assertEqual(llaves.salas, salas)
        self.assertEqual(llaves.enemigos, enemigos)
        self.assertEqual((llaves.cripta_id, llaves.version), ("cripta-07", "v2"))


if __name__ == "__main__":
    unittest.main()
