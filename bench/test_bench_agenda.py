"""Prueba del bloque de agenda con decenas de actores y reajuste de velocidad (T072, FR-121, §5.6)."""
from __future__ import annotations

import unittest

from bench import agenda
from bench.agenda import AgendaConEventosPorActor, _armar, _vaciar
from Logica.RelojVirtual import RelojVirtual


class TestReajusteDeVelocidadConDecenasDeActores(unittest.TestCase):
    """FR-121: la agenda debe seguir siendo adecuada con decenas de actores; la alternativa por actor es solo de medición."""

    def test_el_bloque_corre_y_todas_las_verificaciones_dan_ok(self):
        filas = []
        agenda._reajuste_velocidad(filas, tamanos=(10, 30), todos_hasta=30, repeticiones=1)
        verificaciones = [f for f in filas if f[1].startswith("verificación")]
        self.assertGreaterEqual(len(verificaciones), 4)
        self.assertTrue(all(f[2] == "OK" for f in verificaciones), verificaciones)

    def test_ambas_agendas_reajustan_igual(self):
        intervalos = [100 + 13 * i % 400 for i in range(45)]
        a, actores_a = _armar(RelojVirtual, 30, intervalos)
        b, actores_b = _armar(AgendaConEventosPorActor, 30, intervalos)
        for i in (0, 7, 7, 29):                      # incluye un actor reajustado dos veces
            a.reajustar_velocidad(actores_a[i], 100, 150)
            b.reajustar_velocidad(actores_b[i], 100, 150)
        a.reajustar_velocidad(actores_a[7], 150, 100)
        b.reajustar_velocidad(actores_b[7], 150, 100)
        self.assertEqual(_vaciar(a), _vaciar(b))

    def test_el_indice_por_actor_queda_consistente_tras_sacar_y_reprogramar(self):
        intervalos = [100 + 7 * i for i in range(15)]
        b, actores = _armar(AgendaConEventosPorActor, 10, intervalos)
        for _ in range(5):
            evento = b.desencolar()
            b.programar(250, evento.actor, "MOVER")
        b.reajustar_velocidad(actores[3], 100, 200)
        cuenta = sum(len(lista) for lista in b.por_actor)
        con_actor = sum(1 for e in b.heap if e.actor is not None)
        self.assertEqual(cuenta, con_actor)
        for numero, lista in enumerate(b.por_actor):
            for evento in lista:
                self.assertIs(evento.actor, actores[numero])
                self.assertGreaterEqual(evento.posicion, 0)


if __name__ == "__main__":
    unittest.main()
