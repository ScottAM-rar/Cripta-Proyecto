"""Niebla de guerra (capacidad 002), rendimiento por CONTEO y no por tiempo (FR-223, FR-224, FR-225, SC-006).
Lección de la 005: a decenas de microsegundos una razón de tiempos es frágil; lo que se prueba es cuánto se lee y se examina."""
import unittest

from DTO.CambioDTO import CambioDTO
from Logica.MapaConocido import MapaConocido, EXPLORADA
from tests_labs.cripta_sintetica import esqueleto_rejilla, mapa_dto_desde_esqueleto
from Logica.MapaCripta import MapaCripta

TAMANOS = ((20, 20), (20, 100), (100, 200))          # 400, 2 000 y 20 000 salas: el mayor, 50 veces el menor


class JugadorFalso:
    def __init__(self, sala):
        self.id_sala_actual = sala


class ListaContada(list):
    """list que cuenta cuántas posiciones se leen."""
    lecturas = 0

    def __getitem__(self, i):
        ListaContada.lecturas += 1
        return list.__getitem__(self, i)


def conocimiento(ancho, alto, previamente_explorado):
    esqueleto = esqueleto_rejilla(ancho, alto, semilla=1, costo_max=300, fraccion_cerradas=0.1)
    mapa_dto = mapa_dto_desde_esqueleto(esqueleto)
    mapa = MapaCripta(mapa_dto)
    nombres = [("" if s is None else s.nombre) for s in mapa_dto.salas]
    salas = [None] * mapa.tamano
    registrados = []
    c = MapaConocido(mapa, nombres, salas, JugadorFalso(1), registrados.append)
    for sala in range(1, previamente_explorado + 1):         # un mapa conocido grande, lejos de la sala de prueba
        c.entrar(sala)
    registrados.clear()
    return c, registrados, ancho * alto


class TestConsultas(unittest.TestCase):
    def test_FR223_SC006_cada_consulta_lee_una_sola_posicion_en_los_tres_tamanos(self):
        for ancho, alto in TAMANOS:
            for explorado in (1, (ancho * alto) // 10):
                with self.subTest(salas=ancho * alto, explorado=explorado):
                    c, _, total = conocimiento(ancho, alto, explorado)
                    c.estado = ListaContada(c.estado)
                    c.puertas = ListaContada(c.puertas)
                    ListaContada.lecturas = 0
                    c.estado_de(total // 2)
                    self.assertEqual(ListaContada.lecturas, 1)
                    ListaContada.lecturas = 0
                    c.puerta_recordada(total // 2, 2)
                    self.assertEqual(ListaContada.lecturas, 1)


class TestEntrar(unittest.TestCase):
    def reveladas(self, ancho, alto, explorado, antorcha):
        c, registrados, total = conocimiento(ancho, alto, explorado)
        centro = (alto // 2) * ancho + ancho // 2 + 1
        self.assertNotEqual(c.estado_de(centro), EXPLORADA)
        c.entrar(centro, antorcha)
        return c.salas_reveladas, c.salidas_examinadas, len(registrados[0]) if registrados else 0

    def test_FR224_entrar_cuesta_lo_revelado_y_no_el_tamano_del_mapa_ni_de_la_cripta(self):
        for antorcha in (False, True):
            medidas = []
            for ancho, alto in TAMANOS:
                for explorado in (1, (ancho * alto) // 10):
                    medidas.append(self.reveladas(ancho, alto, explorado, antorcha))
            with self.subTest(antorcha=antorcha):
                self.assertTrue(all(m == medidas[0] for m in medidas), f"las medidas cambian con el tamaño: {medidas}")

    def test_FR224_la_antorcha_cuesta_una_cantidad_acotada(self):
        sin = self.reveladas(20, 20, 1, False)
        con = self.reveladas(20, 20, 1, True)
        self.assertGreater(con[0], sin[0])
        self.assertLessEqual(con[1], 4 + 8 + 4 * 4)           # salidas propias + entrantes + salidas de las 4 vecinas


class TestDeshacer(unittest.TestCase):
    def test_FR225_deshacer_una_accion_revierte_exactamente_sus_cambios_en_los_tres_tamanos(self):
        for ancho, alto in TAMANOS:
            c, registrados, total = conocimiento(ancho, alto, total_previo(ancho, alto))
            centro = (alto // 2) * ancho + ancho // 2 + 1
            antes = (list(c.estado), list(c.puertas), list(c.exploradas))
            c.entrar(centro, True)
            cambios = registrados[0]
            version = c.version_conocimiento
            for cambio in reversed(cambios):
                c.deshacer(cambio)
            self.assertEqual(c.version_conocimiento, version + len(cambios))
            self.assertEqual((list(c.estado), list(c.puertas), list(c.exploradas)), antes)
            with self.subTest(salas=total):
                self.assertEqual(len(cambios), len(registrados[0]))


def total_previo(ancho, alto):
    return (ancho * alto) // 10


class TestSinCopias(unittest.TestCase):
    def test_FR225_ningun_cambio_guarda_los_arreglos_completos(self):
        c, registrados, total = conocimiento(20, 100, 200)
        c.entrar(1500, True)
        for cambio in registrados[0]:
            self.assertIsInstance(cambio, CambioDTO)
            for campo in (cambio.valor_anterior, cambio.valor_nuevo, cambio.indice):
                self.assertIsInstance(campo, int)


if __name__ == "__main__":
    unittest.main()
