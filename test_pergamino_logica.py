import unittest

from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.CambioDTO import CambioDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.EventoDTO import EventoDTO
from DTO.Objeto import Arma, Objeto, PergaminoRetroceso
from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.TrampaDTO import Trampa
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.BitacoraLogica import BitacoraLogica
from Logica.GestorEventos import GestorEventos
from Logica.PergaminoLogica import PergaminoLogica
from Logica.RelojVirtual import RelojVirtual
from Logica.RetrocesoLogica import RetrocesoLogica


class TestPergaminoLogica(unittest.TestCase):
    def setUp(self):
        self.retroceso = RetrocesoLogica()
        self.retroceso.reiniciar()
        self.jugador = JugadorDTO(100, 100, 10, 5, 3, inventario_max=10)
        self.jugador.id_sala_actual = 1
        self.sala_anterior = SalaDTO(id=1, nombre="Anterior")
        self.sala_nueva = SalaDTO(id=2, nombre="Nueva")
        self.salas = [None, self.sala_anterior, self.sala_nueva]
        self.logica = PergaminoLogica(self.retroceso, self.salas)
        self.gestor = GestorEventos(self.salas, self.jugador, lambda sala_id: self.salas[sala_id], semilla=1)

    def registrar(self, cambios):
        self.retroceso.iniciar_accion()
        self.retroceso.registrar_cambio(cambios)

    def accion_del_jugador(self, tiempo=100, tipo="ESPERAR"):
        return self.gestor.procesar_evento(EventoDTO(tiempo, 1, self.jugador, tipo, []))

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

    def test_usar_equipa_un_arma_que_no_es_el_cursor_actual(self):
        objeto_inicial = self.objeto("Antorcha")
        arma = Arma("daga", "Daga", 1, 1, 3)
        self.jugador.id_sala_actual = 1
        self.jugador.inventario.agregar_objeto(objeto_inicial)
        self.jugador.inventario.agregar_objeto(arma)

        resultado = self.gestor.procesar_evento(
            EventoDTO(50, 1, self.jugador, "USAR_OBJETO", [arma])
        )

        self.assertTrue(resultado.exito)
        self.assertIs(self.jugador.arma, arma)
        self.assertIs(self.jugador.inventario.cabeza.objeto, arma)

    def test_soltar_objeto_elegido_que_no_es_el_cursor_actual(self):
        objeto_inicial = self.objeto("Antorcha")
        objeto_elegido = self.objeto("Llave")
        self.jugador.id_sala_actual = 1
        self.jugador.inventario.agregar_objeto(objeto_inicial)
        self.jugador.inventario.agregar_objeto(objeto_elegido)

        resultado = self.gestor.procesar_evento(
            EventoDTO(25, 1, self.jugador, "SOLTAR_OBJETO", [objeto_elegido])
        )

        self.assertTrue(resultado.exito)
        self.assertIsNone(self.jugador.inventario.buscar_objeto(objeto_elegido))
        self.assertIn(objeto_elegido, self.sala_anterior.objetos)
        self.assertIs(self.jugador.inventario.cabeza.objeto, objeto_inicial)

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

    def test_pergamino_revierte_ataque_de_enemigo_y_el_enemigo_sigue_programado(self):
        enemigo = EnemigoDTO(30, 30, 5, 2, 3, "e1", "guardian", "Guardian", "guardián")
        self.jugador.id_sala_actual = 1
        enemigo.id_sala_actual = 1
        self.sala_anterior.enemigos.append(enemigo)
        evento = EventoDTO(100, 1, enemigo, "ACCION_ENEMIGO", [self.jugador])

        self.accion_del_jugador()
        resultado_enemigo = self.gestor.procesar_evento(evento)
        resultado_pergamino = self.gestor.pergamino_logica.usar_pergamino()

        self.assertTrue(resultado_enemigo.exito)
        self.assertTrue(resultado_pergamino.exito)
        self.assertEqual(self.jugador.vida_actual, 100)
        self.assertIsNotNone(resultado_enemigo.eventoResultado)
        self.assertEqual(resultado_enemigo.eventoResultado.tipo_accion, "ACCION_ENEMIGO")

    def test_pergamino_revierte_trampa_y_conserva_su_rearme_programado(self):
        trampa = Trampa("t1", "trampa", 1, 10, 5, armada=True)
        self.sala_anterior.trampas.append(trampa)
        evento = EventoDTO(77, 1, trampa, "ACTIVAR_TRAMPA", [self.sala_anterior])

        self.accion_del_jugador()
        resultado_trampa = self.gestor.procesar_evento(evento)
        resultado_pergamino = self.gestor.pergamino_logica.usar_pergamino()

        self.assertTrue(resultado_trampa.exito)
        self.assertTrue(resultado_pergamino.exito)
        self.assertEqual(self.jugador.vida_actual, 100)
        self.assertTrue(trampa.armada)
        self.assertIsNotNone(resultado_trampa.eventoResultado)
        self.assertEqual(resultado_trampa.eventoResultado.tipo_accion, "ARMAR_TRAMPA")

        cambios = self.retroceso.cola
        self.assertIsNone(cambios)

    def test_cambios_de_un_evento_conservan_su_tiempo_de_ejecucion(self):
        trampa = Trampa("t1", "trampa", 1, 10, 5, armada=True)
        self.jugador.id_sala_actual = 1
        self.sala_anterior.trampas.append(trampa)
        evento = EventoDTO(77, 1, trampa, "ACTIVAR_TRAMPA", [self.sala_anterior])

        self.accion_del_jugador(tiempo=50)
        self.gestor.procesar_evento(evento)

        marcador = self.retroceso.cabeza
        self.assertEqual([cambio.tiempo_ejecucion for cambio in marcador.objeto], [50])
        nodo = marcador.siguiente
        while nodo.objeto[0].tipo_accion != "ACTUALIZAR_VIDA":
            nodo = nodo.siguiente
        self.assertEqual([cambio.tiempo_ejecucion for cambio in nodo.objeto], [77, 77])

    def test_los_cambios_sin_accion_abierta_se_ignoran(self):
        self.retroceso.registrar_cambio([CambioDTO("ACTUALIZAR_VIDA", self.jugador, valor_anterior=90)])

        self.assertIsNone(self.retroceso.cabeza)
        self.assertFalse(self.retroceso.hay_algo_para_deshacer())

    def test_solo_los_eventos_del_jugador_abren_una_accion(self):
        enemigo = EnemigoDTO(30, 30, 5, 2, 3, "e1", "guardian", "Guardian", "guardián")
        enemigo.id_sala_actual = 1
        self.jugador.id_sala_actual = 1
        self.sala_anterior.enemigos.append(enemigo)

        self.gestor.procesar_evento(EventoDTO(100, 1, enemigo, "ACCION_ENEMIGO", [self.jugador]))
        self.assertEqual(self.retroceso.cantidad_acciones, 0)

        self.accion_del_jugador()
        self.gestor.procesar_evento(EventoDTO(200, 2, enemigo, "ACCION_ENEMIGO", [self.jugador]))
        self.gestor.procesar_evento(EventoDTO(300, 3, enemigo, "ACCION_ENEMIGO", [self.jugador]))
        self.assertEqual(self.retroceso.cantidad_acciones, 1)

        self.accion_del_jugador(tiempo=400)
        self.assertEqual(self.retroceso.cantidad_acciones, 2)

    def test_una_accion_rechazada_no_cuenta(self):
        self.jugador.id_sala_actual = 1
        self.accion_del_jugador()
        resultado = self.gestor.procesar_evento(
            EventoDTO(100, 2, self.jugador, "MOVER_JUGADOR", [self.sala_anterior, "norte"])
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(self.retroceso.cantidad_acciones, 1)

    def test_el_uso_del_pergamino_no_abre_una_accion(self):
        pergamino = PergaminoRetroceso("p", "Pergamino", 1, 1)
        self.jugador.inventario.agregar_objeto(pergamino)
        self.accion_del_jugador()
        self.accion_del_jugador(tiempo=200)
        self.assertEqual(self.retroceso.cantidad_acciones, 2)

        self.gestor.procesar_evento(EventoDTO(300, 3, self.jugador, "USAR_OBJETO", [pergamino]))

        self.assertEqual(self.retroceso.cantidad_acciones, 1)

    def test_un_evento_que_falla_no_deja_una_accion_vacia_ni_cambios_a_medias(self):
        with self.assertRaises(ValueError):
            self.gestor.procesar_evento(EventoDTO(100, 1, self.jugador, "NO_EXISTE", []))

        self.assertEqual(self.retroceso.cantidad_acciones, 0)
        self.assertIsNone(self.retroceso.cabeza)
        self.assertEqual(self.sala_anterior.ultimo_paso, 0)

    def test_el_tope_elimina_la_accion_mas_antigua_con_todo_lo_posterior(self):
        for numero in range(1, 8):
            self.registrar([CambioDTO("ACTUALIZAR_VIDA", self.jugador, valor_anterior=numero)])
            self.retroceso.registrar_cambio([CambioDTO("ACTUALIZAR_VIDA", self.jugador, valor_anterior=numero * 10)])

        self.assertEqual(self.retroceso.cantidad_acciones, RetrocesoLogica.MAX_HISTORIAL)
        self.assertEqual(self.retroceso.cantidad_actual, RetrocesoLogica.MAX_HISTORIAL * 3)
        nodo = self.retroceso.cabeza
        self.assertTrue(nodo.es_accion)
        self.assertEqual(nodo.siguiente.objeto[0].valor_anterior, 3)

    def test_el_pergamino_restaura_reloj_y_agenda(self):
        reloj = RelojVirtual()
        reloj.retroceso = self.retroceso
        self.retroceso.reloj = reloj
        reloj.encolar(100, self.jugador, "ESPERAR")
        reloj.encolar(150, None, "APAGAR_ANTORCHA")
        reloj.desencolar()
        tiempo = reloj.tiempo_actual
        secuencia = reloj.secuencia_actual

        self.retroceso.iniciar_accion()
        consumido = reloj.desencolar()
        creado_antes = reloj.encolar(50, None, "CERRAR_PUERTA")
        creado = reloj.heap[0] if reloj.heap[0].tipo_accion == "CERRAR_PUERTA" else reloj.heap[1]

        self.logica.usar_pergamino()

        self.assertEqual(reloj.tiempo_actual, tiempo)
        self.assertEqual(reloj.secuencia_actual, secuencia)
        self.assertIn(consumido, reloj.heap)
        self.assertNotIn(creado, reloj.heap)
        self.assertEqual(len(reloj.heap), 1)

    def test_los_eventos_creados_y_consumidos_en_la_misma_accion_se_cancelan(self):
        reloj = RelojVirtual()
        reloj.retroceso = self.retroceso
        self.retroceso.reloj = reloj

        self.retroceso.iniciar_accion()
        reloj.encolar(10, None, "APAGAR_ANTORCHA")
        reloj.desencolar()
        self.logica.usar_pergamino()

        self.assertEqual(reloj.heap, [])
        self.assertEqual(reloj.tiempo_actual, 0)

    def test_los_eventos_de_carga_de_sala_no_se_registran(self):
        reloj = RelojVirtual()
        reloj.retroceso = self.retroceso
        self.retroceso.reloj = reloj
        self.retroceso.iniciar_accion()

        with self.retroceso.sin_registro():
            reloj.encolar(100, None, "ACCION_ENEMIGO")
        self.logica.usar_pergamino()

        self.assertEqual(len(reloj.heap), 1)

    def test_quitar_un_evento_del_medio_del_heap_mantiene_el_orden(self):
        reloj = RelojVirtual()
        for intervalo in (50, 10, 40, 20, 30, 60, 5):
            reloj.encolar(intervalo, None, f"E{intervalo}")
        medio = reloj.heap[2]

        self.assertTrue(reloj.quitar_evento(medio))
        self.assertFalse(reloj.quitar_evento(medio))

        tiempos = []
        while reloj.heap:
            tiempos.append(reloj.desencolar().tiempo_ejecucion)
        self.assertEqual(tiempos, sorted(tiempos))
        self.assertEqual(len(tiempos), 6)

    def test_revertir_puntaje_eliminados_y_ultimo_paso(self):
        estado = EstadoJuego()
        estado.puntaje = 90
        self.jugador.enemigos_eliminados = 3
        self.sala_anterior.ultimo_paso = 500

        self.logica._revertir_cambio(CambioDTO("ACTUALIZAR_PUNTAJE", estado, valor_anterior=40))
        self.logica._revertir_cambio(CambioDTO("ENEMIGOS_ELIMINADOS", self.jugador, valor_anterior=2))
        self.logica._revertir_cambio(CambioDTO("ULTIMO_PASO", self.sala_anterior, valor_anterior=300))

        self.assertEqual(estado.puntaje, 40)
        self.assertEqual(self.jugador.enemigos_eliminados, 2)
        self.assertEqual(self.sala_anterior.ultimo_paso, 300)

    def test_revertir_bitacora_quita_el_mensaje_y_recupera_el_descartado(self):
        bitacora = BitacoraLogica()
        resultados = [ResultadoEventoDTO(True, f"Mensaje {i}") for i in range(20)]
        for resultado in resultados:
            bitacora.agregar_evento(resultado)
        nuevo = ResultadoEventoDTO(True, "Nuevo")
        descartado = bitacora.agregar_evento(nuevo)

        self.assertIs(descartado, resultados[0])
        self.logica._revertir_cambio(
            CambioDTO("BITACORA_AGREGADA", bitacora, valor_anterior=descartado, elemento=nuevo)
        )

        self.assertEqual(bitacora.obtener_eventos(), resultados)
        self.assertEqual(bitacora.contador, 20)

    def test_revertir_recoger_y_soltar_un_pergamino_no_hace_nada(self):
        pergamino = PergaminoRetroceso("p", "Pergamino", 1, 1)
        self.jugador.inventario.agregar_objeto(pergamino)

        self.logica._revertir_cambio(
            CambioDTO("RECOGER_OBJETO", self.jugador, valor_anterior=1, elemento=pergamino)
        )
        self.assertIs(self.jugador.inventario.cabeza.objeto, pergamino)
        self.assertEqual(self.sala_anterior.objetos, [])

        self.logica._revertir_cambio(
            CambioDTO("SOLTAR_OBJETO", self.jugador, valor_anterior=1, elemento=pergamino, indice=0)
        )
        self.assertIs(self.jugador.inventario.cabeza.objeto, pergamino)

    def test_revertir_tipo_desconocido_y_pergamino(self):
        with self.assertRaises(ValueError):
            self.logica._revertir_cambio(CambioDTO("NO_EXISTE"))
        pergamino = PergaminoRetroceso("p", "Pergamino", 1, 1)
        with self.assertRaises(ValueError):
            self.logica._revertir_cambio(
                CambioDTO("USAR_OBJETO", self.jugador, elemento=pergamino, indice=0)
            )


def pruebas_visuales():
    print("\n=== PRUEBAS VISUALES DEL RETROCESO AUTOMATICO ===")
    prueba = TestPergaminoLogica()
    prueba.setUp()

    enemigo = EnemigoDTO(30, 30, 5, 2, 3, "e-visual", "guardian", "Guardian", "guardián")
    enemigo.id_sala_actual = 1
    prueba.jugador.id_sala_actual = 1
    prueba.sala_anterior.enemigos.append(enemigo)
    prueba.accion_del_jugador()
    resultado_enemigo = prueba.gestor.procesar_evento(
        EventoDTO(100, 1, enemigo, "ACCION_ENEMIGO", [prueba.jugador])
    )

    print(f"Enemigo: vida del jugador despues de la accion = {prueba.jugador.vida_actual}")
    print(f"Enemigo: evento siguiente = {resultado_enemigo.eventoResultado.tipo_accion}")
    print(f"Enemigo: acciones en el historial = {prueba.retroceso.cantidad_acciones}")

    resultado_pergamino = prueba.gestor.pergamino_logica.usar_pergamino()
    print(f"Enemigo: vida restaurada = {prueba.jugador.vida_actual}")
    print(f"Enemigo: resultado del pergamino = {resultado_pergamino.exito}")

    prueba.retroceso.reiniciar()
    trampa = Trampa("t-visual", "trampa", 1, 10, 5, armada=True)
    prueba.sala_anterior.trampas.append(trampa)
    prueba.accion_del_jugador()
    resultado_trampa = prueba.gestor.procesar_evento(
        EventoDTO(77, 2, trampa, "ACTIVAR_TRAMPA", [prueba.sala_anterior])
    )
    print(f"Trampa: estado despues de activar = {trampa.armada}")
    print(f"Trampa: evento siguiente = {resultado_trampa.eventoResultado.tipo_accion}")

    prueba.gestor.pergamino_logica.usar_pergamino()
    print(f"Trampa: estado restaurado = {trampa.armada}")
    print("=== FIN DE PRUEBAS VISUALES ===\n")


if __name__ == "__main__":
    pruebas_visuales()
    unittest.main(verbosity=2)