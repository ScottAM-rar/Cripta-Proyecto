"""Historia 3: reutilizar el campo de costos nunca cambia la decisión respecto de calcular desde cero (principio III).

Cada comparación pone lado a lado el campo REUTILIZADO (el que usa el juego) y un campo NUEVO, recién construido, que
calcula desde cero con el mismo estado del mundo en ese instante."""
import random
import types
import unittest

from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from Controlador.ControladorJuego import ControladorJuego
from DTO.CambioDTO import CambioDTO
from DTO.Objeto import PergaminoRetroceso
from Logica.CampoDeCostos import CampoDeCostos
from Logica.CompCazador import ComportamientoCazador
from Logica.PergaminoLogica import PergaminoLogica
from Logica.PuertasLogica import fijar_cerrada
from tests_labs.cripta_sintetica import esqueleto_de_conexiones, esqueleto_rejilla, ficha_cazador
from tests_labs.partida_prueba import jugar, nueva_partida
from test_cazador import Escenario


def acotado(valor, cota):
    return valor if valor is not None and valor <= cota else None


class Mundo:
    """Un esqueleto con sus salas del modelo y el campo reutilizado, más la referencia desde cero."""

    def __init__(self, esqueleto, sala_jugador):
        self.escenario = Escenario(esqueleto, sala_jugador, sala_cazador=1)
        self.campo = self.escenario.campo
        self.jugador = self.escenario.jugador
        self.salas = self.escenario.salas
        self.ids = [s["id"] for s in esqueleto]

    def cambiar_puerta(self, sala, destino, cerrada):
        for salida in self.salas[sala].salidas:
            if salida.sala_destino == destino:
                fijar_cerrada(salida, cerrada, lambda s: self.campo.puerta_cambio(s.sala_destino))

    def desde_cero(self):
        return CampoDeCostos(self.campo.mapa, self.jugador, self.salas)

    def decision(self, campo, sala, rango):
        cazador = types.SimpleNamespace(id_sala_actual=sala, rango=rango)
        salida, d = ComportamientoCazador.decidir(cazador, self.salas, campo)
        return (None if salida is None else salida.sala_destino), d

    def comparar(self, test, cotas=(0, 150, 400, 900)):
        for cota in cotas:
            referencia = self.desde_cero()
            for sala in self.ids:
                a = acotado(self.campo.obtener(cota).costo(sala), cota)
                b = acotado(referencia.obtener(cota).costo(sala), cota)
                test.assertEqual(a, b, f"costo de la sala {sala} con cota {cota}")
                test.assertEqual(self.decision(self.campo, sala, cota), self.decision(referencia, sala, cota),
                                 f"decisión desde la sala {sala} con rango {cota}")


def cuadricula(semilla=3, cerradas=0.25):
    return esqueleto_rejilla(5, 5, semilla=semilla, costo_max=300, fraccion_cerradas=cerradas)


class TestEquivalenciaPorEvento(unittest.TestCase):
    def test_FR116_sin_cambios_el_campo_reutilizado_coincide(self):
        mundo = Mundo(cuadricula(), sala_jugador=13)
        mundo.comparar(self)
        mundo.comparar(self)

    def test_FR116_una_puerta_de_la_ruta_se_cierra_entre_dos_turnos(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (1, 3, 100, "S", "N"), (3, 2, 400, "E", "O")])
        mundo = Mundo(esqueleto, sala_jugador=2)
        mundo.comparar(self)
        mundo.cambiar_puerta(1, 2, True)
        mundo.comparar(self)
        self.assertEqual(mundo.decision(mundo.campo, 1, 1000), (3, 500))

    def test_FR116_una_puerta_cerrada_se_abre_y_aparece_la_ruta_nueva(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O", {"cerrada": True}), (1, 3, 100, "S", "N"),
                                             (3, 2, 400, "E", "O")])
        mundo = Mundo(esqueleto, sala_jugador=2)
        mundo.comparar(self)
        mundo.cambiar_puerta(1, 2, False)
        mundo.comparar(self)
        self.assertEqual(mundo.decision(mundo.campo, 1, 1000), (2, 100))

    def test_FR116_el_jugador_cambia_de_sala(self):
        mundo = Mundo(cuadricula(), sala_jugador=1)
        mundo.comparar(self)
        for sala in (7, 25, 13, 1):
            mundo.jugador.id_sala_actual = sala
            mundo.comparar(self)

    def test_FR116_un_cazador_con_rango_mayor_amplia_la_zona(self):
        mundo = Mundo(cuadricula(), sala_jugador=13)
        mundo.campo.obtener(100)
        mundo.comparar(self, cotas=(100,))
        mundo.comparar(self, cotas=(900,))
        mundo.comparar(self, cotas=(100, 900, 50))

    def test_FR116_deshacer_con_pergamino_pasa_por_el_aviso_de_cambio_de_puertas(self):
        esqueleto = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (1, 3, 100, "S", "N"), (3, 2, 400, "E", "O")])
        mundo = Mundo(esqueleto, sala_jugador=2)
        pergamino = PergaminoLogica(None, mundo.salas, avisar_puerta=lambda s: mundo.campo.puerta_cambio(s.sala_destino))
        salida = next(s for s in mundo.salas[1].salidas if s.sala_destino == 2)
        mundo.comparar(self)
        mundo.cambiar_puerta(1, 2, True)
        mundo.comparar(self)
        pergamino._revertir_cambio(CambioDTO("CAMBIAR_PUERTA", salida, valor_anterior=False))
        self.assertFalse(salida.cerrada)
        mundo.comparar(self)

    def test_FR116_una_puerta_fuera_de_la_zona_no_obliga_a_recalcular_y_una_dentro_si(self):
        lejos = esqueleto_de_conexiones([(1, 2, 100, "E", "O"), (2, 3, 100, "E", "O"), (3, 4, 5000, "E", "O"),
                                         (4, 5, 100, "E", "O")])
        mundo = Mundo(lejos, sala_jugador=1)
        mundo.campo.obtener(250)
        base = mundo.campo.calculos
        mundo.campo.obtener(250)
        self.assertEqual(mundo.campo.calculos, base)                    # nada cambió: se reutiliza
        mundo.cambiar_puerta(4, 5, True)                                # lejos de la zona de costo 250
        mundo.campo.obtener(250)
        self.assertEqual(mundo.campo.calculos, base)
        mundo.cambiar_puerta(2, 1, True)                                # dentro de la zona
        mundo.campo.obtener(250)
        self.assertEqual(mundo.campo.calculos, base + 1)
        mundo.comparar(self, cotas=(250,))

    def test_FR116_secuencias_aleatorias_deterministas_comparan_tras_cada_evento(self):
        for semilla in (1, 2, 3):
            with self.subTest(semilla=semilla):
                azar = random.Random(semilla)
                esqueleto = cuadricula(semilla=semilla)
                mundo = Mundo(esqueleto, sala_jugador=azar.choice(mundo_ids(esqueleto)))
                conexiones = []
                for sala in esqueleto:
                    for salida in sala["salidas"].values():
                        conexiones.append((sala["id"], salida["sala"]))
                for _ in range(400):
                    if azar.random() < 0.6:
                        origen, destino = azar.choice(conexiones)
                        mundo.cambiar_puerta(origen, destino, azar.random() < 0.5)
                    else:
                        mundo.jugador.id_sala_actual = azar.choice(mundo.ids)
                    mundo.comparar(self, cotas=(azar.choice((0, 120, 350, 800)),))


def mundo_ids(esqueleto):
    return [s["id"] for s in esqueleto]


class TestEquivalenciaEnUnaPartida(unittest.TestCase):
    """Partida real: movimientos, aperturas, cierre automático y pergamino; tras cada acción el campo que usa el juego
    coincide con uno calculado desde cero."""

    def test_FR116_el_campo_del_juego_coincide_con_el_calculo_desde_cero_tras_cada_accion(self):
        esqueleto = esqueleto_rejilla(4, 4, semilla=9, costo_max=250, fraccion_cerradas=0.35)
        for sala in esqueleto:
            for salida in sala["salidas"].values():
                if salida.get("cerrada"):
                    salida["cierre_automatico"] = 180
        logica = nueva_partida(esqueleto, [(16, "e-1", "ent_cazador", None)], [ficha_cazador(rango=800)], sala_inicial=1)
        gestor = logica.gestorEventos
        estado = logica.estadoJuego
        azar = random.Random(5)
        controlador = ControladorJuego(None)
        for paso in range(120):
            sala = logica.ingresarEnSala(estado.jugador.id_sala_actual)
            cerradas = [s for s in sala.salidas if s.cerrada and not s.llave]
            abiertas = [s for s in sala.salidas if not s.cerrada]
            tirada = azar.random()
            if tirada < 0.45 and abiertas:
                evento = controlador._mapear_entrada_a_evento(azar.choice(abiertas).direccion, sala, estado.jugador)
                logica.accionJugador(evento)
            elif tirada < 0.7 and cerradas:
                jugar(logica, "ABRIR_PUERTA", [sala, azar.choice(cerradas).direccion])
            elif tirada < 0.85 and estado.jugador.inventario.cantidad_actual == 0:
                pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
                estado.jugador.inventario.agregar_objeto(pergamino)
                jugar(logica, "USAR_OBJETO", [pergamino])
            else:
                jugar(logica, "ESPERAR")
            if logica.fin:
                break
            referencia = CampoDeCostos(gestor.campo_de_costos.mapa, estado.jugador, estado.salas)
            for cota in (150, 700):
                for destino in range(1, 17):
                    a = acotado(gestor.campo_de_costos.obtener(cota).costo(destino), cota)
                    b = acotado(referencia.obtener(cota).costo(destino), cota)
                    self.assertEqual(a, b, f"paso {paso}, sala {destino}, cota {cota}")


if __name__ == "__main__":
    unittest.main()
