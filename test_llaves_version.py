"""Capacidad 009, T018: las llaves guardadas valen mientras coincida la versión de la cripta (FR-301, FR-305 a FR-308,
principio III).

Una «ejecución» es: HttpConfigurable nuevo, AlmacenDisco nuevo, ClientePersistente nuevo y ServicioCripta nuevo sobre
la MISMA carpeta, como nueva_ejecucion pero controlando versión y llaves. Sin red; cada prueba en su carpeta temporal."""
import os
import tempfile
import unittest

from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from tests_labs.api_falsa import HttpConfigurable

CRIPTA = "cripta-01"
SALAS = [{"id": i, "nombre": f"Sala {i}",
          "salidas": ({"O": {"sala": i - 1}} if i > 1 else {}) | ({"E": {"sala": i + 1}} if i < 9 else {})}
         for i in range(1, 10)]
ENEMIGOS = [(7, "e-701", "ent_guardian_oseo", None)]
# Llaves distintas en cada versión, para saber de cuál vino la lista.
LLAVES_C1 = [("itm_llave_bronce", 3, None), ("itm_llave_negra", 7, "e-701"), ("itm_llave_bronce", 9, None)]
LLAVES_C2 = [("itm_llave_plata", 4, None), ("itm_llave_negra", 7, "e-701")]


def crudas(llaves):
    """La lista cruda que entrega la API falsa para esas tuplas (la que se guarda en disco)."""
    lista = []
    for id_llave, sala, enemigo in llaves:
        entrada = {"id": id_llave, "sala": sala}
        if enemigo is not None:
            entrada["enemigo"] = enemigo
        lista.append(entrada)
    return lista


def campos(dto):
    return (dto.cripta_id, dto.version, dto.ids, dto.salas, dto.enemigos)


class ConCarpeta(unittest.TestCase):

    def carpeta_nueva(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return os.path.join(tmp.name, "datos_cripta")

    @staticmethod
    def ejecucion(carpeta, version="c1", llaves=None):
        http = HttpConfigurable(SALAS, ENEMIGOS, llaves=LLAVES_C1 if llaves is None else llaves, version_cripta=version)
        almacen = AlmacenDisco(carpeta)
        servicio = ServicioCripta(ClientePersistente(http, almacen), CacheLRU(25))
        return http, almacen, servicio


class MismaVersion(ConCarpeta):

    def test_fr306_a_h2_1_segunda_ejecucion_con_la_misma_version_no_consulta(self):
        carpeta = self.carpeta_nueva()
        http_1, _, servicio_1 = self.ejecucion(carpeta, "c1")
        primera = servicio_1.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_1.veces("llaves"), 1)

        http_2, _, servicio_2 = self.ejecucion(carpeta, "c1")
        segunda = servicio_2.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_2.veces("llaves"), 0)
        self.assertEqual(campos(segunda), campos(primera))


class CriptaSinLlaves(ConCarpeta):
    """T057 (b), caso límite de spec.md: la cripta no tiene ninguna llave."""

    def test_fr301_fr305_t057_b_cripta_sin_llaves_consulta_una_vez_y_la_segunda_partida_ninguna(self):
        carpeta = self.carpeta_nueva()
        http_1, almacen_1, servicio_1 = self.ejecucion(carpeta, "c1", [])
        primera = servicio_1.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_1.veces("llaves"), 1)
        self.assertEqual(primera.cantidad(), 0)
        self.assertEqual(almacen_1.leer_llaves(CRIPTA), [])                  # lista vacía guardada, no None

        http_2, _, servicio_2 = self.ejecucion(carpeta, "c1", [])
        segunda = servicio_2.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_2.veces("llaves"), 0)
        self.assertEqual(segunda.cantidad(), 0)


class OtraVersion(ConCarpeta):

    def test_fr307_b_h2_2_con_otra_version_consulta_una_vez_y_guarda_la_lista_nueva(self):
        carpeta = self.carpeta_nueva()
        _, _, servicio_1 = self.ejecucion(carpeta, "c1", LLAVES_C1)
        servicio_1.ubicacion_llaves(CRIPTA)

        http_2, almacen_2, servicio_2 = self.ejecucion(carpeta, "c2", LLAVES_C2)
        nueva = servicio_2.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_2.veces("llaves"), 1)
        self.assertEqual(almacen_2.version_cripta(CRIPTA), "c2")
        self.assertEqual(almacen_2.leer_llaves(CRIPTA), crudas(LLAVES_C2))
        self.assertEqual((nueva.version, nueva.ids, nueva.salas, nueva.enemigos),
                         ("c2", ["itm_llave_plata", "itm_llave_negra"], [4, 7], [None, "e-701"]))


class ArchivoDeLaParteI(ConCarpeta):

    def test_fr308_c_h2_3_archivo_sin_llaves_se_consulta_una_vez_y_queda_con_llaves(self):
        carpeta = self.carpeta_nueva()
        # Archivo con la forma de la Parte I, armado solo con AlmacenDisco: versión, datos, salas y el contenido de
        # todas las salas, sin la clave llaves. Los datos salen de una API falsa aparte, con la misma versión.
        fabricante = HttpConfigurable(SALAS, ENEMIGOS, llaves=LLAVES_C1, version_cripta="c1")
        almacen = AlmacenDisco(carpeta)
        almacen.guardar_criptas(fabricante.obtener_criptas())
        almacen.validar_cripta(CRIPTA, "c1")
        almacen.guardar_datos(CRIPTA, fabricante.obtener_datos_generales(CRIPTA))
        almacen.guardar_salas(CRIPTA, fabricante.obtener_salas(CRIPTA))
        numeros = [sala["id"] for sala in SALAS]
        almacen.guardar_contenido(CRIPTA, numeros, fabricante.obtener_contenido(CRIPTA, numeros))
        self.assertIsNone(almacen.leer_llaves(CRIPTA))
        self.assertTrue(almacen.cripta_completa(CRIPTA, numeros))
        antes = (almacen.version_cripta(CRIPTA), almacen.leer_datos(CRIPTA), almacen.leer_salas(CRIPTA),
                 [almacen.leer_contenido(CRIPTA, n) for n in numeros])

        http, almacen_2, servicio = self.ejecucion(carpeta, "c1", LLAVES_C1)
        dto = servicio.ubicacion_llaves(CRIPTA)
        self.assertEqual(http.veces("llaves"), 1)
        self.assertEqual(http.veces("salas") + http.veces("contenido"), 0)        # lo demás sale del disco
        self.assertEqual(almacen_2.leer_llaves(CRIPTA), crudas(LLAVES_C1))
        self.assertEqual(dto.cantidad(), len(LLAVES_C1))
        despues = (almacen_2.version_cripta(CRIPTA), almacen_2.leer_datos(CRIPTA), almacen_2.leer_salas(CRIPTA),
                   [almacen_2.leer_contenido(CRIPTA, n) for n in numeros])
        self.assertEqual(despues, antes)


class ReutilizadaIgualQueDesdeCero(ConCarpeta):

    def test_principio_iii_d_reutilizada_de_disco_y_memorizada_igual_a_consulta_desde_cero(self):
        carpeta = self.carpeta_nueva()
        http_1, _, servicio_1 = self.ejecucion(carpeta, "c1")
        servicio_1.ubicacion_llaves(CRIPTA)
        memorizada = servicio_1.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_1.veces("llaves"), 1)

        http_2, _, servicio_2 = self.ejecucion(carpeta, "c1")
        de_disco = servicio_2.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_2.veces("llaves"), 0)

        http_0, _, servicio_0 = self.ejecucion(self.carpeta_nueva(), "c1")
        desde_cero = servicio_0.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_0.veces("llaves"), 1)

        self.assertEqual(campos(memorizada), campos(desde_cero))
        self.assertEqual(campos(de_disco), campos(desde_cero))


class VersionCambiaDuranteLaPartida(ConCarpeta):

    def test_fr301_fr307_e_cambio_de_version_en_la_sesion_no_consulta_y_la_siguiente_invalida(self):
        carpeta = self.carpeta_nueva()
        http, _, servicio = self.ejecucion(carpeta, "c1", LLAVES_C1)
        primera = servicio.ubicacion_llaves(CRIPTA)
        http.version_cripta = "c2"                  # el servicio publica otra versión a mitad de la partida
        http.llaves = LLAVES_C2
        otra_vez = servicio.ubicacion_llaves(CRIPTA)
        self.assertEqual(http.veces("llaves"), 1)   # 0 consultas nuevas en la misma sesión
        self.assertEqual(campos(otra_vez), campos(primera))

        http_2, almacen_2, servicio_2 = self.ejecucion(carpeta, "c2", LLAVES_C2)
        siguiente = servicio_2.ubicacion_llaves(CRIPTA)
        self.assertEqual(http_2.veces("llaves"), 1)
        self.assertEqual(almacen_2.version_cripta(CRIPTA), "c2")
        self.assertEqual((siguiente.version, siguiente.ids), ("c2", ["itm_llave_plata", "itm_llave_negra"]))


if __name__ == "__main__":
    unittest.main()
