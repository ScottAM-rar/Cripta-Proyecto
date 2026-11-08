"""Capacidad 003, T021: índice de ids de llave a número (research.md §4, data-model.md §4).

`IndiceLlaves` ordena los ids con `ordenar_adaptativo`, quita los repetidos y busca con una búsqueda binaria propia.
El orden de los números es el de los ids, y eso sostiene el desempate de FR-335 (dentro de una sala, por id de llave).

El módulo se importa dentro de cada prueba con `try/except ImportError: self.fail(...)`, para que mientras no exista la
prueba falle por aserción y no por un error de importación. Sin dict, set, sorted() ni .sort() (principio I)."""
import importlib
import random
import unittest


def busqueda_lineal(ids: list, buscado: str) -> int:
    """Referencia: posición de `buscado` recorriendo la lista de punta a punta, o -1."""
    for posicion in range(len(ids)):
        if ids[posicion] == buscado:
            return posicion
    return -1


def id_al_azar(azar: random.Random) -> str:
    letras = "abcdefghijklmnopqrstuvwxyz_"
    largo = azar.randint(1, 8)
    texto = ""
    for _ in range(largo):
        texto += letras[azar.randint(0, len(letras) - 1)]
    return "itm_llave_" + texto


class IndiceLlavesPrueba(unittest.TestCase):

    def indice(self, ids: list):
        try:
            modulo = importlib.import_module("Logica.IndiceLlaves")
        except ImportError as error:
            self.fail(f"Logica.IndiceLlaves todavía no existe: {error}")
        return modulo.IndiceLlaves(ids)

    def ids_del_indice(self, indice) -> list:
        return [indice.id_de(numero) for numero in range(indice.cantidad())]

    def test_fr335_ids_quedan_en_orden_creciente(self):
        indice = self.indice(["itm_llave_c", "itm_llave_a", "itm_llave_d", "itm_llave_b"])
        ids = self.ids_del_indice(indice)
        self.assertEqual(ids, ["itm_llave_a", "itm_llave_b", "itm_llave_c", "itm_llave_d"])
        for numero in range(1, len(ids)):
            self.assertLess(ids[numero - 1], ids[numero])

    def test_fr335_repetidos_cuentan_una_vez(self):
        indice = self.indice(["itm_llave_b", "itm_llave_a", "itm_llave_b", "itm_llave_a", "itm_llave_b"])
        self.assertEqual(indice.cantidad(), 2)
        self.assertEqual(self.ids_del_indice(indice), ["itm_llave_a", "itm_llave_b"])

    def test_fr335_numero_de_un_id_presente(self):
        indice = self.indice(["itm_llave_negra", "itm_llave_bronce", "itm_llave_plata", "itm_llave_salida"])
        for numero in range(indice.cantidad()):
            self.assertEqual(indice.numero(indice.id_de(numero)), numero)

    def test_fr335_numero_de_un_id_ausente_es_menos_uno(self):
        indice = self.indice(["itm_llave_b", "itm_llave_d", "itm_llave_f"])
        self.assertEqual(indice.numero("itm_llave_a"), -1)     # menor que todos
        self.assertEqual(indice.numero("itm_llave_z"), -1)     # mayor que todos
        self.assertEqual(indice.numero("itm_llave_c"), -1)     # entre dos
        self.assertEqual(indice.numero(""), -1)

    def test_lista_vacia(self):
        indice = self.indice([])
        self.assertEqual(indice.cantidad(), 0)
        self.assertEqual(indice.numero("x"), -1)

    def test_un_solo_elemento(self):
        indice = self.indice(["itm_llave_salida"])
        self.assertEqual(indice.cantidad(), 1)
        self.assertEqual(indice.numero("itm_llave_salida"), 0)
        self.assertEqual(indice.id_de(0), "itm_llave_salida")
        self.assertEqual(indice.numero("itm_llave_otra"), -1)

    def test_prefijos_compartidos(self):
        indice = self.indice(["itm_llave_ab", "itm_llave_a", "itm_llave_abc"])
        self.assertEqual(self.ids_del_indice(indice), ["itm_llave_a", "itm_llave_ab", "itm_llave_abc"])
        self.assertEqual(indice.numero("itm_llave_a"), 0)
        self.assertEqual(indice.numero("itm_llave_ab"), 1)
        self.assertEqual(indice.numero("itm_llave_abc"), 2)
        self.assertEqual(indice.numero("itm_llave_abcd"), -1)

    def test_fr335_igual_que_busqueda_lineal(self):
        for semilla in range(5):
            azar = random.Random(semilla)
            ids = [id_al_azar(azar) for _ in range(1000)]
            indice = self.indice(ids)
            ordenados = self.ids_del_indice(indice)
            for numero in range(1, len(ordenados)):
                self.assertLess(ordenados[numero - 1], ordenados[numero], f"semilla {semilla}")
            for original in ids:                                # todo id de la entrada está, una vez
                self.assertEqual(indice.numero(original), busqueda_lineal(ordenados, original), f"semilla {semilla}")
                self.assertNotEqual(indice.numero(original), -1)
            ausentes = 0
            while ausentes < 200:
                candidato = id_al_azar(azar) + "#"              # '#' no aparece en los ids generados
                self.assertEqual(indice.numero(candidato), -1, f"semilla {semilla}")
                self.assertEqual(busqueda_lineal(ordenados, candidato), -1)
                ausentes += 1


if __name__ == "__main__":
    unittest.main()
