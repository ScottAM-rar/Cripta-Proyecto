"""Capacidad 009, T023: lectura solo local, sin red y sin modificar lo guardado (FR-314 a FR-317, SC-003).

Las carpetas se arman con la API falsa v2 (cripta_v2) por el flujo normal: ServicioCripta sobre ClientePersistente.
Durante las operaciones solo locales, requests.get queda bloqueado y el cliente HTTP que pudiera armar la fábrica es un
HttpFalso espía, que no debe recibir ninguna llamada."""
from adaptadores.fuente_solo_local import FuenteSoloLocal

import os
import tempfile
import unittest
from unittest import mock

import requests

from adaptadores import fabrica
from adaptadores.AlmacenDisco import AlmacenDisco
from adaptadores.cache import CacheLRU
from adaptadores.cliente_persistente import ClientePersistente
from adaptadores.servicioCripta import ServicioCripta
from Logica.FuenteCripta import DatoLocalFaltante
from tests_labs.api_falsa import HttpFalso, cripta_v2

CRIPTA = "cripta-01"
SALA_QUE_FALTA = 5


def _sin_red(*args, **kwargs):
    raise AssertionError("intento de red")


def servicio_normal(carpeta, http=None):
    return ServicioCripta(ClientePersistente(http or cripta_v2(semilla=0), AlmacenDisco(carpeta)), CacheLRU(25))


def guardar_cripta_completa(carpeta):
    servicio = servicio_normal(carpeta)
    servicio.listar_criptas()
    servicio.crear_jugador(CRIPTA)
    servicio.construir_todas(CRIPTA)
    servicio.ubicacion_llaves(CRIPTA)


def guardar_cripta_sin_sala_5(carpeta):
    """Lo mismo, pero el contenido se trae sala por sala y la 5 nunca se pide: el archivo no tiene contenido:5."""
    servicio = servicio_normal(carpeta)
    servicio.listar_criptas()
    servicio.crear_jugador(CRIPTA)
    numeros = [sala["id"] for sala in servicio._cargar_esqueleto(CRIPTA) if sala["id"] != SALA_QUE_FALTA]
    servicio.construir_salas(CRIPTA, numeros)
    servicio.ubicacion_llaves(CRIPTA)


def bytes_de_la_carpeta(carpeta):
    """(nombre, bytes) de cada archivo de la carpeta, en orden de nombre."""
    resultado = []
    for nombre in sorted(os.listdir(carpeta)):
        with open(os.path.join(carpeta, nombre), "rb") as archivo:
            resultado.append((nombre, archivo.read()))
    return resultado


def campos_llaves(dto):
    return (dto.cripta_id, dto.version, dto.ids, dto.salas, dto.enemigos)


def campos_jugador(jugador):
    """JugadorDTO trae un InventarioLogica, que no se compara por valor: se comparan los campos que vienen de disco."""
    return (jugador.vida_actual, jugador.vida_max, jugador.ataque, jugador.defensa, jugador.velocidad,
            jugador.id_sala_actual, jugador.inventario.capacidad_maxima)


class SoloLocal(unittest.TestCase):
    """Cada prueba arma su carpeta y comprueba (d): el espía sin llamadas y los archivos byte a byte iguales."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)          # se registra primero: corre al final, después de comprobar (d)
        self.carpeta = os.path.join(self._tmp.name, "datos_cripta")
        self.espia = HttpFalso()

    def solo_local(self, version_vigente=None, **opciones):
        """Abre la fuente solo local con la red bloqueada y el espía como único cliente HTTP posible, y comprueba (d)
        al terminar la prueba. `opciones`: version_catalogo_vigente (T053)."""
        antes = bytes_de_la_carpeta(self.carpeta)
        parches = [mock.patch.object(requests, "get", side_effect=_sin_red),
                   mock.patch.object(fabrica, "_cliente_http_de_ejecucion", side_effect=lambda url: self.espia)]
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)
        self.addCleanup(self.comprobar_sin_cambios, antes)
        return fabrica.crear_fuente_solo_local(carpeta=self.carpeta, version_vigente=version_vigente, **opciones)

    def comprobar_sin_cambios(self, antes):
        # (d) SC-003 / FR-315: ninguna solicitud y lo guardado queda igual, byte a byte.
        self.assertEqual(self.espia.llamadas, [])
        self.assertEqual(bytes_de_la_carpeta(self.carpeta), antes)

    def version_guardada(self):
        return AlmacenDisco(self.carpeta).version_cripta(CRIPTA)


class DatoFaltante(SoloLocal):

    def test_fr315_a_h4_1_sin_contenido_de_la_sala_5_falla_nombrando_sala_y_cripta(self):
        guardar_cripta_sin_sala_5(self.carpeta)
        self.assertIsNone(AlmacenDisco(self.carpeta).leer_contenido(CRIPTA, SALA_QUE_FALTA))
        fuente = self.solo_local()
        self.assertIsInstance(fuente, FuenteSoloLocal)
        with self.assertRaises(DatoLocalFaltante) as error:
            fuente.construir_sala(CRIPTA, SALA_QUE_FALTA)
        self.assertIn("sala 5", str(error.exception))
        self.assertIn(CRIPTA, str(error.exception))


class IgualQueLaViaNormal(SoloLocal):

    def test_fr314_fr316_b_h4_2_con_la_cache_completa_da_lo_mismo_que_la_via_normal(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        local = (fuente.esqueleto(CRIPTA), [fuente.construir_sala(CRIPTA, n) for n in (1, SALA_QUE_FALTA, 25)],
                 campos_llaves(fuente.ubicacion_llaves(CRIPTA)), campos_jugador(fuente.crear_jugador(CRIPTA)), fuente.total_salas(CRIPTA))
        self.comprobar_sin_cambios(bytes_de_la_carpeta(self.carpeta))   # antes de abrir la vía normal

        # La vía normal, con la misma carpeta: un HttpFalso que no trae nada nuevo (todo sale del disco).
        http = cripta_v2(semilla=0)
        normal = servicio_normal(self.carpeta, http)
        esperado = (normal.esqueleto(CRIPTA), [normal.construir_sala(CRIPTA, n) for n in (1, SALA_QUE_FALTA, 25)],
                    campos_llaves(normal.ubicacion_llaves(CRIPTA)), campos_jugador(normal.crear_jugador(CRIPTA)),
                    normal.total_salas(CRIPTA))
        self.assertEqual(http.veces("salas") + http.veces("contenido") + http.veces("llaves"), 0)
        self.assertEqual(local, esperado)


class VersionDistinta(SoloLocal):

    def test_fr317_c_h4_3_con_otra_version_vigente_toda_operacion_falla_nombrando_las_dos(self):
        guardar_cripta_completa(self.carpeta)
        guardada = self.version_guardada()
        fuente = self.solo_local(version_vigente="v-nueva")
        operaciones = [("esqueleto", lambda: fuente.esqueleto(CRIPTA)),
                       ("construir_sala", lambda: fuente.construir_sala(CRIPTA, 1)),
                       ("ubicacion_llaves", lambda: fuente.ubicacion_llaves(CRIPTA)),
                       ("datos_cripta", lambda: fuente.datos_cripta(CRIPTA)),
                       ("crear_jugador", lambda: fuente.crear_jugador(CRIPTA)),
                       ("version_cripta", lambda: fuente.version_cripta(CRIPTA)),
                       ("total_salas", lambda: fuente.total_salas(CRIPTA)),
                       ("precargar_vecinas", lambda: fuente.precargar_vecinas(CRIPTA, 1)),
                       ("reporte", lambda: fuente.reporte(CRIPTA))]
        for nombre, operacion in operaciones:
            with self.subTest(operacion=nombre):
                with self.assertRaises(DatoLocalFaltante) as error:
                    operacion()
                self.assertIn(guardada, str(error.exception))
                self.assertIn("v-nueva", str(error.exception))
                self.assertIn(CRIPTA, str(error.exception))

    def test_fr317_c_sin_version_guardada_falla_aunque_no_se_pida_una(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        with self.assertRaises(DatoLocalFaltante) as error:
            fuente.esqueleto("cripta-sin-guardar")
        self.assertIn("cripta-sin-guardar", str(error.exception))


class SinPrecarga(SoloLocal):

    def test_fr316_e_precargar_vecinas_devuelve_0_y_reporte_0_solicitudes(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        self.assertEqual(fuente.precargar_vecinas(CRIPTA, 1), 0)
        self.assertEqual(fuente.precargar_vecinas(CRIPTA, 1, 3), 0)
        self.assertEqual(fuente.reporte(CRIPTA).solicitudes, 0)


# ----------------------------------------------------------------------------------------------------------------
# T053: lo que pide la capacidad 004 (consulta histórica). (f) vale en todas: solo_local() comprueba al terminar que
# el espía no recibió llamadas y que los bytes de la carpeta no cambiaron.
# ----------------------------------------------------------------------------------------------------------------
SALA_DEL_CAZADOR = 25          # cripta_v2: el cazador está en la sala más lejana de la 1


class ExisteCripta(SoloLocal):

    def test_fr314_t053_a_existe_cripta_con_lista_guardada_true_o_false_sin_comparar_version(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local(version_vigente="v-nueva")      # otra versión: existe_cripta no la mira
        self.assertIs(fuente.existe_cripta(CRIPTA), True)
        self.assertIs(fuente.existe_cripta("cripta-que-no-esta"), False)

    def test_fr315_t053_a_existe_cripta_sin_lista_en_disco_lanza(self):
        os.makedirs(self.carpeta)
        fuente = self.solo_local()
        with self.assertRaises(DatoLocalFaltante):
            fuente.existe_cripta(CRIPTA)


class CriptaDesconocida(SoloLocal):
    """T056: una cripta con archivo y versión en disco que no está en la lista de criptas guardada. El servicio interior
    lanza ValueError («La cripta 'X' no existe»); la fuente solo local debe entregarlo como DatoLocalFaltante."""

    def test_fr315_sc004_t056_cripta_que_no_esta_en_la_lista_lanza_dato_local_faltante(self):
        guardar_cripta_completa(self.carpeta)
        AlmacenDisco(self.carpeta).validar_cripta("cripta-fantasma", "c1")     # archivo con versión, fuera de la lista
        fuente = self.solo_local()
        self.assertIs(fuente.existe_cripta("cripta-fantasma"), False)
        with self.assertRaises(DatoLocalFaltante) as error:
            fuente.esqueleto("cripta-fantasma")
        self.assertIn("cripta-fantasma", str(error.exception))


class VersionCatalogo(SoloLocal):

    def test_fr317_t053_b_version_catalogo_igual_o_none_devuelve_la_guardada(self):
        guardar_cripta_completa(self.carpeta)
        guardada = AlmacenDisco(self.carpeta).version_catalogo()
        self.assertIsNotNone(guardada)
        self.assertEqual(self.solo_local(version_catalogo_vigente=guardada).version_catalogo(), guardada)
        self.assertEqual(self.solo_local().version_catalogo(), guardada)

    def test_fr317_t053_b_version_catalogo_distinta_lanza_nombrando_las_dos(self):
        guardar_cripta_completa(self.carpeta)
        guardada = AlmacenDisco(self.carpeta).version_catalogo()
        with self.assertRaises(DatoLocalFaltante) as error:
            self.solo_local(version_catalogo_vigente="k-nueva").version_catalogo()
        self.assertIn(guardada, str(error.exception))
        self.assertIn("k-nueva", str(error.exception))

    def test_fr315_t053_b_sin_version_de_catalogo_guardada_lanza(self):
        os.makedirs(self.carpeta)
        with self.assertRaises(DatoLocalFaltante) as error:
            self.solo_local(version_catalogo_vigente="k1").version_catalogo()
        self.assertIn("k1", str(error.exception))


class ObjetosQueSuelta(SoloLocal):

    def cazador(self, fuente):
        return fuente.construir_sala(CRIPTA, SALA_DEL_CAZADOR).enemigos[0]

    def test_fr314_t053_c_tras_consultar_la_cripta_da_lo_mismo_que_la_via_normal(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        local = fuente.objetos_que_suelta(self.cazador(fuente))
        self.comprobar_sin_cambios(bytes_de_la_carpeta(self.carpeta))       # antes de abrir la vía normal
        normal = servicio_normal(self.carpeta)
        esperado = normal.objetos_que_suelta(normal.construir_sala(CRIPTA, SALA_DEL_CAZADOR).enemigos[0])
        self.assertTrue(local)
        self.assertEqual(local, esperado)

    def test_fr317_t053_c_ultima_cripta_con_otra_version_lanza(self):
        guardar_cripta_completa(self.carpeta)
        cazador = self.cazador(self.solo_local())
        fuente = self.solo_local(version_vigente="v-nueva")
        with self.assertRaises(DatoLocalFaltante):
            fuente.esqueleto(CRIPTA)                               # la última cripta consultada es esta
        with self.assertRaises(DatoLocalFaltante) as error:
            fuente.objetos_que_suelta(cazador)
        self.assertIn("v-nueva", str(error.exception))

    def test_fr315_t053_c_ficha_ausente_lanza_con_el_id_de_la_ficha(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        cazador = self.cazador(fuente)
        cazador.suelta = ["itm_que_no_esta"]
        with self.assertRaises(DatoLocalFaltante) as error:
            fuente.objetos_que_suelta(cazador)
        self.assertIn("itm_que_no_esta", str(error.exception))
        self.assertIn(CRIPTA, str(error.exception))

    def test_fr315_t053_c_sin_ninguna_cripta_consultada_lanza(self):
        guardar_cripta_completa(self.carpeta)
        cazador = self.cazador(self.solo_local())
        with self.assertRaises(DatoLocalFaltante):
            self.solo_local().objetos_que_suelta(cazador)


class SalidaYMapa(SoloLocal):

    def test_fr314_t053_d_sala_de_salida_y_mapa_iguales_a_la_via_normal(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        local = (fuente.obtener_sala_salida(CRIPTA), fuente.obtener_mapa(CRIPTA))
        self.comprobar_sin_cambios(bytes_de_la_carpeta(self.carpeta))
        normal = servicio_normal(self.carpeta)
        self.assertEqual(local, (normal.obtener_sala_salida(CRIPTA), normal.obtener_mapa(CRIPTA)))

    def test_fr317_t053_d_con_otra_version_lanzan(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local(version_vigente="v-nueva")
        for nombre, operacion in (("obtener_sala_salida", lambda: fuente.obtener_sala_salida(CRIPTA)),
                                  ("obtener_mapa", lambda: fuente.obtener_mapa(CRIPTA))):
            with self.subTest(operacion=nombre):
                with self.assertRaises(DatoLocalFaltante):
                    operacion()


class FichasEnUso(SoloLocal):

    def test_sc003_t053_e_fijar_fichas_en_uso_no_escribe_ni_pide(self):
        guardar_cripta_completa(self.carpeta)
        fuente = self.solo_local()
        fuente.construir_sala(CRIPTA, SALA_DEL_CAZADOR)
        fuente.fijar_fichas_en_uso(["ent_cazador"])
        fuente.fijar_fichas_en_uso([])
        # (f) lo comprueba solo_local() al terminar: llamadas == [] y la carpeta igual byte a byte


if __name__ == "__main__":
    unittest.main()
