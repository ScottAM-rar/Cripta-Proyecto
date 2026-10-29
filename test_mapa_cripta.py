"""Lectura del esqueleto y versión de las puertas (Logica/MapaCripta.py, contrato compartido de rutas).
Cada prueba cita el requisito que demuestra."""
import unittest

from DTO.SalaDTO import SalaDTO, SalidaDTO
from Logica.CampoDeCostos import CampoDeCostos
from Logica.GestorEventos import GestorEventos
from Logica.PergaminoLogica import PergaminoLogica
from Logica.PuertasLogica import fijar_cerrada
from Logica.SalasLogica import SalaLogica
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_lineal, mapa_desde_esqueleto


class JugadorFalso:
    def __init__(self, id_sala_actual):
        self.id_sala_actual = id_sala_actual


class TestLecturaDelEsqueleto(unittest.TestCase):
    def test_FR116_total_salas_cuenta_las_salas_que_existen(self):
        self.assertEqual(mapa_desde_esqueleto(esqueleto_lineal([100, 100, 100])).total_salas(), 4)

    def test_FR116_total_salas_no_cuenta_los_ids_sin_sala(self):
        esqueleto = [s for s in esqueleto_lineal([100, 100, 100, 100]) if s["id"] != 3]    # falta la sala 3
        for s in esqueleto:
            s["salidas"] = {l: d for l, d in s["salidas"].items() if d["sala"] != 3}
        self.assertEqual(mapa_desde_esqueleto(esqueleto).total_salas(), 4)

    def test_FR116_salidas_devuelve_las_aristas_que_salen_de_la_sala(self):
        mapa = mapa_desde_esqueleto(esqueleto_lineal([100, 250]))
        self.assertEqual([(a.destino, a.costo) for a in mapa.salidas(2)], [(3, 250), (1, 100)])
        self.assertEqual([(a.destino, a.costo) for a in mapa.salidas(1)], [(2, 100)])

    def test_FR116_entrantes_devuelve_las_aristas_que_llegan_a_la_sala(self):
        mapa = mapa_desde_esqueleto(esqueleto_lineal([100, 250]))
        self.assertEqual(sorted((a.origen, a.costo) for a in mapa.entrantes(3)), [(2, 250)])
        self.assertEqual(sorted((a.origen, a.costo) for a in mapa.entrantes(2)), [(1, 100), (3, 250)])

    def test_FR116_ids_fuera_del_esqueleto_no_tienen_salidas_ni_entrantes(self):
        mapa = mapa_desde_esqueleto(esqueleto_lineal([100]))
        for sala in (0, 3, 999, -1):
            self.assertEqual(list(mapa.salidas(sala)), [])
            self.assertEqual(list(mapa.entrantes(sala)), [])

    def test_FR116_id_sin_sala_dentro_del_rango_no_tiene_salidas_ni_entrantes(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O")], total=3)
        esqueleto = [s for s in esqueleto if s["id"] != 3]
        mapa = mapa_desde_esqueleto(esqueleto)
        self.assertEqual(list(mapa.salidas(3)), [])
        self.assertEqual(list(mapa.entrantes(3)), [])

    def test_FR124_en_una_conexion_de_un_solo_sentido_solo_existe_la_arista_declarada(self):
        mapa = mapa_desde_esqueleto(esqueleto_de_conexiones([(1, 2, 100, "E", "O", {"un_sentido": True})]))
        self.assertEqual([a.destino for a in mapa.salidas(1)], [2])
        self.assertEqual(list(mapa.salidas(2)), [])
        self.assertEqual([a.origen for a in mapa.entrantes(2)], [1])
        self.assertEqual(list(mapa.entrantes(1)), [])

    def test_FR116_los_campos_que_ya_usa_el_cazador_siguen_disponibles(self):
        mapa = mapa_desde_esqueleto(esqueleto_lineal([100, 100]))
        self.assertEqual(mapa.tamano, 4)
        self.assertEqual(len(mapa.salientes[2]), 2)
        self.assertEqual(len(mapa.entrantes_por_sala[2]), 2)
        self.assertTrue(mapa.existe[2])


class TestVersionDePuertas(unittest.TestCase):
    """`version_puertas` la sube solo `fijar_cerrada`, el único punto de cambio de puertas."""

    def setUp(self):
        self.mapa = mapa_desde_esqueleto(esqueleto_lineal([100, 100]))
        self.salida = SalidaDTO("este", 2, False)

    def test_FR116_la_version_empieza_en_cero(self):
        self.assertEqual(self.mapa.version_puertas, 0)

    def test_FR116_sube_con_cada_cambio_de_puerta(self):
        fijar_cerrada(self.salida, True, None, self.mapa)
        self.assertEqual(self.mapa.version_puertas, 1)
        fijar_cerrada(self.salida, False, None, self.mapa)
        self.assertEqual(self.mapa.version_puertas, 2)

    def test_FR116_no_sube_si_la_puerta_ya_estaba_asi(self):
        fijar_cerrada(self.salida, False, None, self.mapa)
        self.assertEqual(self.mapa.version_puertas, 0)

    def test_FR116_no_sube_al_consultar_ni_al_avisar_al_campo(self):
        campo = CampoDeCostos(self.mapa, JugadorFalso(1), [])
        campo.obtener(300)
        campo.costo(2)
        campo.puerta_cambio(2)
        self.assertEqual(self.mapa.version_puertas, 0)

    def test_FR116_sube_aunque_nadie_haya_calculado_nada(self):
        fijar_cerrada(self.salida, True, lambda s: None, self.mapa)
        self.assertEqual(self.mapa.version_puertas, 1)

    def test_FR116_abrir_y_cerrar_en_el_juego_suben_la_version_por_el_gestor(self):
        salas = [None, SalaDTO(1, "Sala 1", salidas=[SalidaDTO("este", 2, True)])]
        gestor = GestorEventos.__new__(GestorEventos)
        gestor.salas_logica = SalaLogica(salas[1], avisar_puerta=lambda s: None)
        gestor.pergamino_logica = PergaminoLogica(None, salas)
        GestorEventos.campo_de_costos.fset(gestor, CampoDeCostos(self.mapa, JugadorFalso(1), salas))
        gestor.salas_logica.intentarAbrirPuerta(JugadorFalso(1), "este")
        self.assertEqual(self.mapa.version_puertas, 1)
        gestor.salas_logica.cerrarPuerta("este")
        self.assertEqual(self.mapa.version_puertas, 2)


if __name__ == "__main__":
    unittest.main()
