"""Capacidad 009, T026: API falsa v2 de pruebas (FR-318, FR-319, FR-321).

(e) Todo el archivo corre con requests.get sustituido por una función que lanza AssertionError: si algo intentara
usar la red, la prueba fallaría. La parte (c) (CASOS_APENDICE_B) es del grupo E2."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

import requests

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_http import ErrorSinConexion
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.llaves import LlavesInvalidas
from adaptadores.servicioCripta import ServicioCripta
from tests_labs.api_falsa import HttpConfigurable as HttpConfigurableBase
from tests_labs.api_falsa import cripta_v2


def _sin_red(*args, **kwargs):
    raise AssertionError("intento de red")


_parche_red = mock.patch.object(requests, "get", side_effect=_sin_red)


def setUpModule():
    _parche_red.start()


def tearDownModule():
    _parche_red.stop()


def respuestas(http):
    """Todo lo que la API falsa entrega de la cripta: salas, contenido de todas las salas, catálogo y llaves."""
    salas = http.obtener_salas("cripta-01")
    numeros = [sala["id"] for sala in salas]
    contenido = http.obtener_contenido("cripta-01", numeros)
    ids = []
    for sala in contenido:
        for colocacion in sala["enemigos"]:
            if colocacion["tipo"] not in ids:
                ids.append(colocacion["tipo"])
        for id_objeto in sala["objetos"]:
            if id_objeto not in ids:
                ids.append(id_objeto)
    catalogo = http.obtener_catalogo(ids)
    for ficha in catalogo:
        for id_objeto in ficha.get("suelta") or []:
            if id_objeto not in ids:
                ids.append(id_objeto)
    catalogo = http.obtener_catalogo(ids)
    llaves = http.obtener_llaves("cripta-01")
    return salas, contenido, catalogo, llaves


def buscar_ficha(catalogo, id_ficha):
    for ficha in catalogo:
        if ficha["id"] == id_ficha:
            return ficha
    return None


class Determinismo(unittest.TestCase):

    def test_fr318_a_h5_1_misma_semilla_mismas_respuestas_y_otra_semilla_cambia(self):
        primera = respuestas(cripta_v2(semilla=0))
        segunda = respuestas(cripta_v2(semilla=0))
        self.assertEqual(primera, segunda)
        otra = respuestas(cripta_v2(semilla=1))
        self.assertNotEqual(primera, otra)


class ContenidoDeCriptaV2(unittest.TestCase):

    def setUp(self):
        self.http = cripta_v2(semilla=0)
        self.salas, self.contenido, self.catalogo, self.llaves = respuestas(self.http)

    def test_fr319_b_h5_2_hay_una_salida_con_costo_distinto_de_100(self):
        costos = []
        for sala in self.salas:
            for salida in sala["salidas"].values():
                costos.append(salida.get("costo", 100))
        self.assertTrue(any(costo != 100 for costo in costos))

    def test_fr319_b_h5_2_hay_un_cazador_con_rango(self):
        cazadores = [f for f in self.catalogo if f.get("comportamiento") == "cazador" and "rango" in f]
        self.assertEqual(len(cazadores), 1)

    def test_fr319_b_h5_2_llave_sin_enemigo_con_enemigo_y_la_misma_en_dos_salas(self):
        sin_enemigo = [llave for llave in self.llaves if llave.get("enemigo") is None]
        con_enemigo = [llave for llave in self.llaves if llave.get("enemigo") is not None]
        self.assertGreaterEqual(len(sin_enemigo), 1)
        self.assertGreaterEqual(len(con_enemigo), 1)
        repetida = False
        for i in range(len(self.llaves)):
            for j in range(i + 1, len(self.llaves)):
                if self.llaves[i]["id"] == self.llaves[j]["id"] and self.llaves[i]["sala"] != self.llaves[j]["sala"]:
                    repetida = True
        self.assertTrue(repetida)

    def test_fr319_b_h5_2_la_llave_de_salida_la_suelta_el_cazador(self):
        llave_salida = self.http.obtener_datos_generales("cripta-01")["llave_salida"]
        entradas = [llave for llave in self.llaves if llave["id"] == llave_salida]
        self.assertEqual(len(entradas), 1)
        entrada = entradas[0]
        self.assertIsNotNone(entrada.get("enemigo"))
        # El enemigo está en el contenido de la sala indicada (su sala inicial) y es el cazador.
        sala = [c for c in self.contenido if c["sala"] == entrada["sala"]][0]
        colocaciones = [c for c in sala["enemigos"] if c["instancia"] == entrada["enemigo"]]
        self.assertEqual(len(colocaciones), 1)
        ficha = buscar_ficha(self.catalogo, colocaciones[0]["tipo"])
        self.assertEqual(ficha["comportamiento"], "cazador")
        self.assertIn(llave_salida, ficha["suelta"])

    def test_fr319_b_las_llaves_en_el_suelo_estan_en_el_contenido_y_tienen_ficha(self):
        for llave in self.llaves:
            self.assertIsNotNone(buscar_ficha(self.catalogo, llave["id"]), llave["id"])
            if llave.get("enemigo") is None:
                sala = [c for c in self.contenido if c["sala"] == llave["sala"]][0]
                self.assertIn(llave["id"], sala["objetos"])

    def test_fr319_b_la_cripta_se_carga_y_valida_por_el_servicio_sin_red(self):
        with tempfile.TemporaryDirectory() as raiz:
            http = cripta_v2(semilla=0)
            servicio = ServicioCripta(ClientePersistente(http, AlmacenDisco(os.path.join(raiz, "d"))), CacheLRU(25))
            servicio.construir_todas("cripta-01")
            dto = servicio.ubicacion_llaves("cripta-01")
        self.assertEqual(dto.cantidad(), len(self.llaves))
        self.assertEqual(http.veces("llaves"), 1)


class FallosRepetibles(unittest.TestCase):

    def test_fr321_d_h5_4_sin_respuesta_falla_igual_dos_veces(self):
        http = cripta_v2(semilla=0)
        http.fallo_llaves = "sin_respuesta"
        mensajes = []
        for _ in range(2):
            with self.assertRaises(ErrorSinConexion) as error:
                http.obtener_llaves("cripta-01")
            mensajes.append(str(error.exception))
        self.assertEqual(mensajes[0], mensajes[1])
        self.assertEqual(http.veces("llaves"), 2)

    def test_fr321_d_h5_4_invalida_falla_igual_dos_veces(self):
        http = cripta_v2(semilla=0)
        http.fallo_llaves = "invalida"
        motivos = []
        for _ in range(2):
            with self.assertRaises(LlavesInvalidas) as error:
                http.obtener_llaves("cripta-01")
            motivos.append(error.exception.motivo)
        self.assertEqual(motivos, ["respuesta sin llaves", "respuesta sin llaves"])
        self.assertEqual(http.veces("llaves"), 2)


CODIGOS_APENDICE_B = (["B-T%d" % i for i in range(1, 8)] + ["B-N%d" % i for i in range(1, 7)]
                      + ["B-R%d" % i for i in range(1, 5)] + ["B-L%d" % i for i in range(1, 7)])
RUTA_CONTRATO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs", "009-contrato-datos-v2", "contracts",
                             "api-falsa-v2.md")


def descripciones_del_contrato():
    """Pares (código, descripción) de las tablas del Apéndice B en contracts/api-falsa-v2.md, tal cual."""
    pares = []
    with open(RUTA_CONTRATO, encoding="utf-8") as archivo:
        for linea in archivo:
            if linea.startswith("| B-"):
                celdas = linea.strip().strip("|").split("|", 1)
                pares.append((celdas[0].strip(), celdas[1].strip()))
    return pares


def guion_comparable(guion):
    """El guion con cada ("cargar_partida", ruta) cambiado por el contenido del archivo (las rutas temporales cambian)."""
    resultado = []
    for paso in guion:
        if paso[0] == "cargar_partida":
            with open(paso[1], "rb") as archivo:
                resultado.append(("cargar_partida", archivo.read()))
        else:
            resultado.append(paso)
    return resultado


class CasosApendiceB(unittest.TestCase):
    """(c) H5-3: CASOS_APENDICE_B (grupo E2)."""

    @classmethod
    def setUpClass(cls):
        from tests_labs.api_falsa import CASOS_APENDICE_B, PASOS_GUION
        cls.casos = CASOS_APENDICE_B
        cls.pasos = PASOS_GUION

    def construir(self, constructor):
        """Llama al constructor y borra al terminar la prueba los archivos temporales que dejó (B-L6)."""
        http, guion = constructor()
        for paso in guion:
            if paso[0] == "cargar_partida":
                self.addCleanup(shutil.rmtree, os.path.dirname(paso[1]), True)
        return http, guion

    def test_fr320_c_h5_3_tiene_exactamente_los_23_codigos_sin_repetidos(self):
        codigos = [codigo for codigo, _, _ in self.casos]
        self.assertEqual(len(codigos), 23)
        self.assertEqual(codigos, CODIGOS_APENDICE_B)

    def test_fr320_c_cada_descripcion_es_la_de_la_tabla_del_contrato(self):
        self.assertEqual([(codigo, descripcion) for codigo, descripcion, _ in self.casos], descripciones_del_contrato())

    def test_fr320_c_cada_constructor_da_una_cripta_jugable_sin_red_y_un_guion_con_pasos_conocidos(self):
        from adaptadores.fabrica import crear_servicio
        for codigo, _, construir in self.casos:
            with self.subTest(codigo=codigo):
                http, guion = self.construir(construir)
                self.assertIsInstance(http, HttpConfigurableBase)
                self.assertIsInstance(guion, list)
                for paso in guion:
                    self.assertIn(paso[0], self.pasos, paso)
                with tempfile.TemporaryDirectory() as raiz:
                    servicio = crear_servicio(carpeta=os.path.join(raiz, "datos"), cliente_http=http)
                    servicio.listar_criptas()
                    cid = servicio.obtener_id_cripta(1)
                    servicio.crear_jugador(cid)
                    servicio.construir_todas(cid)
                    servicio.esqueleto(cid)
                    llaves = servicio.ubicacion_llaves(cid)
                self.assertEqual(llaves.cantidad(), len(http.obtener_llaves(cid)))

    def test_fr320_c_llaves_coherentes_con_el_contenido_y_el_catalogo(self):
        for codigo, _, construir in self.casos:
            with self.subTest(codigo=codigo):
                http, _ = self.construir(construir)
                salas, contenido, catalogo, llaves = respuestas(http)
                for llave in llaves:
                    self.assertEqual(buscar_ficha(catalogo, llave["id"])["clase"], "llave")
                    sala = [c for c in contenido if c["sala"] == llave["sala"]][0]
                    if llave.get("enemigo") is None:
                        self.assertIn(llave["id"], sala["objetos"])
                    else:
                        colocacion = [c for c in sala["enemigos"] if c["instancia"] == llave["enemigo"]][0]
                        self.assertIn(llave["id"], buscar_ficha(catalogo, colocacion["tipo"])["suelta"])

    def test_fr318_c_dos_construcciones_del_mismo_caso_dan_respuestas_identicas(self):
        for codigo, _, construir in self.casos:
            with self.subTest(codigo=codigo):
                http_1, guion_1 = self.construir(construir)
                http_2, guion_2 = self.construir(construir)
                self.assertEqual(respuestas(http_1), respuestas(http_2))
                self.assertEqual(guion_comparable(guion_1), guion_comparable(guion_2))

    def test_fr320_c_b_l6_la_partida_de_la_parte_i_se_rechaza_por_su_version(self):
        from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida
        construir = [c for c in self.casos if c[0] == "B-L6"][0][2]
        _, guion = self.construir(construir)
        rutas = [paso[1] for paso in guion if paso[0] == "cargar_partida"]
        self.assertEqual(len(rutas), 1)
        with self.assertRaises(ErrorPartida) as error:
            AlmacenPartidaBinario(rutas[0]).cargar()
        self.assertIn("Versión del formato de partida no soportada: 5", str(error.exception))


class SinRed(unittest.TestCase):

    def test_fr318_e_requests_get_esta_bloqueado_en_todo_el_archivo(self):
        with self.assertRaises(AssertionError):
            requests.get("http://ejemplo.invalido/")


if __name__ == "__main__":
    unittest.main()
