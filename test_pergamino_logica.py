import unittest

from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.CambioDTO import CambioDTO
from DTO.Objeto import Arma, Armadura, Objeto, PergaminoRetroceso
from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.TrampaDTO import Trampa
from Logica.PergaminoLogica import PergaminoLogica
from Logica.RetrocesoLogica import RetrocesoLogica


class TestPergaminoLogica(unittest.TestCase):
    def setUp(self):
        self.retroceso = RetrocesoLogica()
        self.retroceso.reiniciar()
        self.jugador = JugadorDTO(100, 100, 10, 5, 3, inventario_max=10)
        self.sala_anterior = SalaDTO(id=1, nombre="Anterior")
        self.sala_nueva = SalaDTO(id=2, nombre="Nueva")
        self.salas = [None, self.sala_anterior, self.sala_nueva]
        self.logica = PergaminoLogica(self.retroceso, self.salas)

    def registrar(self, cambios):
        self.retroceso.nueva_accion()
        self.retroceso.registrar_cambio(cambios)

    def objeto(self, nombre):
        return Objeto(nombre, nombre, 1, 1)

    def test_hay_algo_y_usar_sin_historial(self):
        self.assertFalse(self.logica.hay_algo_para_deshacer())
        resultado = self.logica.usar_pergamino()

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.mensaje, "No hay nada que retroceder.")

    def test_usar_pergamino_revierte_accion_compuesta_y_consumo_historial(self):
        objeto = self.objeto("Pocion")
        self.jugador.inventario.agregar_objeto(objeto)
        self.jugador.inventario.eliminar_objeto_utilizado(objeto)
        self.jugador.vida_actual = 70
        self.registrar([
            CambioDTO("USAR_OBJETO", self.jugador, elemento=objeto, indice=0),
            CambioDTO("ACTUALIZAR_VIDA", self.jugador, valor_anterior=100),
        ])

        resultado = self.logica.usar_pergamino()

        self.assertTrue(resultado.exito)
        self.assertEqual(self.jugador.vida_actual, 100)
        self.assertIs(self.jugador.inventario.cabeza.objeto, objeto)
        self.assertFalse(self.logica.hay_algo_para_deshacer())

    def test_revertir_cambio_actualiza_vida_y_mueve_jugador(self):
        self.jugador.vida_actual = 30
        self.jugador.id_sala_actual = 2
        self.logica._revertir_cambio(
            CambioDTO("ACTUALIZAR_VIDA", self.jugador, valor_anterior=90)
        )
        self.logica._revertir_cambio(
            CambioDTO("MOVER", self.jugador, valor_anterior=1, valor_nuevo=2)
        )

        self.assertEqual(self.jugador.vida_actual, 90)
        self.assertEqual(self.jugador.id_sala_actual, 1)

    def test_revertir_movimiento_de_enemigo(self):
        enemigo = EnemigoDTO(30, 30, 5, 2, 3, "e1", "esqueleto", "Esqueleto", "errante")
        enemigo.id_sala_actual = 2
        self.sala_nueva.enemigos.append(enemigo)

        self.logica._revertir_cambio(
            CambioDTO("MOVER", enemigo, valor_anterior=1, valor_nuevo=2)
        )

        self.assertEqual(enemigo.id_sala_actual, 1)
        self.assertEqual(self.sala_anterior.enemigos, [enemigo])
        self.assertEqual(self.sala_nueva.enemigos, [])

    def test_revertir_recoger_y_soltar_objeto(self):
        objeto = self.objeto("Llave")
        self.jugador.inventario.agregar_objeto(objeto)
        self.logica._revertir_cambio(
            CambioDTO("RECOGER_OBJETO", self.jugador, valor_anterior=1, elemento=objeto)
        )
        self.assertEqual(self.sala_anterior.objetos, [objeto])
        self.assertIsNone(self.jugador.inventario.buscar_objeto(objeto))

        self.jugador.inventario.agregar_objeto(objeto)
        self.sala_anterior.objetos.remove(objeto)
        self.logica._revertir_cambio(
            CambioDTO("SOLTAR_OBJETO", self.jugador, valor_anterior=1, elemento=objeto, indice=0)
        )
        self.assertIs(self.jugador.inventario.cabeza.objeto, objeto)
        self.assertEqual(self.sala_anterior.objetos, [])

    def test_revertir_equipar_y_desequipar(self):
        arma_anterior = Arma("vieja", "Vieja", 1, 1, 2)
        arma_nueva = Arma("nueva", "Nueva", 1, 1, 3)
        self.jugador.inventario.agregar_objeto(arma_anterior)
        self.jugador.inventario.agregar_objeto(arma_nueva)
        self.jugador.arma = arma_nueva
        self.jugador.inventario.equipar_objeto_actual()
        self.logica._revertir_cambio(
            CambioDTO("EQUIPAR_OBJETO", self.jugador, valor_anterior=arma_anterior,
                      elemento=arma_nueva, indice=1)
        )
        self.assertIs(self.jugador.arma, arma_anterior)
        self.assertIs(self.jugador.inventario.cabeza.objeto, arma_anterior)
        self.assertIs(self.jugador.inventario.cabeza.siguiente.objeto, arma_nueva)

        self.logica._revertir_cambio(
            CambioDTO("DESEQUIPAR_OBJETO", self.jugador, valor_anterior=arma_nueva,
                      elemento=arma_anterior, indice=0)
        )
        self.assertIs(self.jugador.arma, arma_nueva)
        self.assertIs(self.jugador.inventario.cabeza.objeto, arma_nueva)

    def test_revertir_objeto_usado_y_estados(self):
        objeto = self.objeto("Pocion")
        self.logica._revertir_cambio(
            CambioDTO("USAR_OBJETO", self.jugador, elemento=objeto, indice=0)
        )
        self.assertIs(self.jugador.inventario.cabeza.objeto, objeto)

        self.jugador.modificador_velocidad = 4
        self.jugador.antorcha_encendida = True
        self.jugador.veneno = False
        self.logica._revertir_cambio(CambioDTO("REVERTIR_MODIFICADOR_VELOCIDAD", self.jugador, valor_anterior=1))
        self.logica._revertir_cambio(CambioDTO("USAR_ANTORCHA", self.jugador, valor_anterior=False))
        self.logica._revertir_cambio(CambioDTO("APAGAR_ANTORCHA", self.jugador, valor_anterior=True))
        self.logica._revertir_cambio(CambioDTO("APLICAR_ANTIDOTO", self.jugador, valor_anterior=True))
        self.assertEqual(self.jugador.modificador_velocidad, 1)
        self.assertTrue(self.jugador.antorcha_encendida)
        self.assertTrue(self.jugador.veneno)

    def test_revertir_puerta_y_trampa(self):
        salida = SalidaDTO("N", 2, cerrada=False)
        trampa = Trampa("t1", "trampa", 1, 10, 5, armada=False)
        self.logica._revertir_cambio(CambioDTO("CAMBIAR_PUERTA", salida, valor_anterior=True))
        self.logica._revertir_cambio(CambioDTO("CAMBIAR_TRAMPA", trampa, valor_anterior=True))
        self.assertTrue(salida.cerrada)
        self.assertTrue(trampa.armada)

    def test_revertir_tipo_desconocido_y_pergamino(self):
        with self.assertRaises(ValueError):
            self.logica._revertir_cambio(CambioDTO("NO_EXISTE"))
        pergamino = PergaminoRetroceso("p", "Pergamino", 1, 1)
        with self.assertRaises(ValueError):
            self.logica._revertir_cambio(
                CambioDTO("USAR_OBJETO", self.jugador, elemento=pergamino, indice=0)
            )


if __name__ == "__main__":
    unittest.main()