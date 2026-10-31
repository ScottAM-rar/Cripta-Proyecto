"""Contrato de la vista del conocimiento para BuscadorRutas (contracts/vista-buscador.md, futura especificación 006)."""
import unittest

from DTO.Objeto import PergaminoRetroceso
from Logica.BuscadorRutas import BuscadorRutas
from Logica.MapaConocido import VistaMapaConocido, EXPLORADA, ABIERTA
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_rejilla
from tests_labs.partida_prueba import jugar, nueva_partida

LIMITE = 10 ** 9


def mover(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "MOVER_JUGADOR", [sala, direccion])


def costos_naivos(c, destino):
    """Referencia ingenua (Bellman-Ford) sobre el mapa materializado: solo salas exploradas y salidas recordadas abiertas."""
    infinito = 10 ** 12
    costo = [infinito] * c.mapa.tamano
    costo[destino] = 0
    cambio = True
    while cambio:
        cambio = False
        for origen in range(c.mapa.tamano):
            if c.estado[origen] != EXPLORADA:
                continue
            for arista in c.mapa.salidas(origen):
                d = arista.destino
                if not 0 <= d < c.mapa.tamano or c.estado[d] != EXPLORADA:
                    continue
                if c.puertas[origen * 4 + c.indice_direccion(arista.direccion)] != ABIERTA:
                    continue
                if costo[d] + arista.costo < costo[origen]:
                    costo[origen] = costo[d] + arista.costo
                    cambio = True
    return [None if x == infinito else x for x in costo]


class TestVistaDelConocimiento(unittest.TestCase):
    def cripta(self):
        # 1 -E- 2 -E- 3 -E- 4 -E- 5 con costos distintos y la puerta 3-4 cerrada
        return esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (2, 3, 250, "E", "O"),
                                        (3, 4, 100, "E", "O", {"cerrada": True}), (4, 5, 100, "E", "O")])

    def partida(self):
        logica = nueva_partida(self.cripta())
        mover(logica, "este")
        mover(logica, "este")                                               # exploradas 1, 2, 3; avistada 4
        return logica

    def test_contrato_no_atraviesa_salas_no_exploradas_ni_puertas_cerradas_o_sin_observar(self):
        logica = self.partida()
        c = logica.mapaConocido
        buscador = BuscadorRutas()
        buscador.distancias_hacia(3, VistaMapaConocido(c), LIMITE)
        self.assertEqual(buscador.costo(3), 0)
        self.assertEqual(buscador.costo(2), 250)
        self.assertEqual(buscador.costo(1), 350)
        self.assertIsNone(buscador.costo(4))                                # avistada: sin salidas conocidas
        self.assertIsNone(buscador.costo(5))                                # desconocida

    def test_contrato_el_costo_coincide_con_el_de_un_mapa_materializado_de_referencia(self):
        logica = nueva_partida(esqueleto_rejilla(5, 5, semilla=3, costo_max=300, fraccion_cerradas=0.2))
        for direccion in ("este", "sur", "este", "sur", "oeste"):
            sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
            if any(s.direccion == direccion and not s.cerrada for s in sala.salidas):
                mover(logica, direccion)
        c = logica.mapaConocido
        destino = logica.estadoJuego.jugador.id_sala_actual
        buscador = BuscadorRutas()
        buscador.distancias_hacia(destino, VistaMapaConocido(c), LIMITE)
        esperado = costos_naivos(c, destino)
        for sala in range(c.mapa.tamano):
            if c.mapa.existe[sala]:
                self.assertEqual(buscador.costo(sala), esperado[sala], f"sala {sala}")

    def test_contrato_las_salas_no_exploradas_no_tienen_salidas_ni_entrantes_en_la_vista(self):
        c = self.partida().mapaConocido
        vista = VistaMapaConocido(c)
        self.assertEqual(len(vista.salidas(4)), 0)
        self.assertEqual(len(vista.entrantes(4)), 0)
        self.assertEqual(len(vista.salidas(5)), 0)
        self.assertGreater(len(vista.salidas(3)), 0)
        self.assertEqual(vista.tamano, c.mapa.tamano)

    def test_contrato_una_puerta_sin_observar_o_cerrada_no_es_transitable(self):
        c = self.partida().mapaConocido
        vista = VistaMapaConocido(c)
        cerrada = [a for a in c.mapa.salidas(3) if a.destino == 4][0]
        self.assertFalse(vista.transitable(cerrada))                        # destino sin explorar y puerta cerrada
        abierta = [a for a in c.mapa.salidas(1) if a.destino == 2][0]
        self.assertTrue(vista.transitable(abierta))

    def test_contrato_version_conocimiento_sube_al_explorar_y_al_deshacer_y_no_al_consultar(self):
        logica = nueva_partida(self.cripta())
        c = logica.mapaConocido
        vista = VistaMapaConocido(c)
        v0 = vista.version_conocimiento
        BuscadorRutas().distancias_hacia(1, vista, LIMITE)
        vista.salidas(1)
        vista.transitable(c.mapa.salidas(1)[0])
        self.assertEqual(vista.version_conocimiento, v0)
        mover(logica, "este")
        v1 = vista.version_conocimiento
        self.assertGreater(v1, v0)
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        logica.estadoJuego.jugador.inventario.agregar_objeto(pergamino)
        jugar(logica, "USAR_OBJETO", [pergamino])
        self.assertGreater(vista.version_conocimiento, v1)


if __name__ == "__main__":
    unittest.main()
