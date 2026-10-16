import contextlib
import io
import os
import random
import tempfile
import unittest

from DTO.EventoDTO import EventoDTO
from DTO.Objeto import Antorcha, PergaminoRetroceso, Pocion
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from tests_labs.api_falsa import HttpFalso


class ApiPrueba(HttpFalso):
    def __init__(self, con_trampa=False):
        super().__init__()
        self.con_trampa = con_trampa

    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["jugador"]["vida_max"] = 5000
        return datos

    def obtener_contenido(self, cripta_id, salas):
        contenidos = super().obtener_contenido(cripta_id, salas)
        for contenido in contenidos:
            if contenido["sala"] == 1 and self.con_trampa:
                contenido["trampas"] = [{"instancia": "t-1", "tipo": "trp_pinchos"}]
        return contenidos

    def obtener_catalogo(self, ids):
        fichas = super().obtener_catalogo(ids)
        if "trp_pinchos" in ids:
            fichas.append({"id": "trp_pinchos", "clase": "trampa", "nombre": "Pinchos", "daño": 10, "rearme": 300})
        return fichas


MENSAJE_PERGAMINO = "Se han revertido los cambios hasta la última acción registrada."


class PruebaRetroceso(unittest.TestCase):
    def nueva(self, con_trampa=False, semilla=1):
        RetrocesoLogica().reiniciar()
        logica = EstadoJuegoLogica()
        logica.comunicacion = ServicioCripta(ApiPrueba(con_trampa), CacheLRU(25))
        logica.iniciarJuego("cripta-01", semilla)
        logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
        return logica

    def jugar(self, logica, tipo, datos=None):
        jugador = logica.estadoJuego.jugador
        evento = EventoDTO(100, 0, jugador, tipo, [] if datos is None else datos)
        with contextlib.redirect_stdout(io.StringIO()):
            return logica.accionJugador(evento)

    def mover(self, logica, direccion):
        sala = logica.ingresarEnSala(logica.estadoJuego.jugador.id_sala_actual)
        return self.jugar(logica, "MOVER_JUGADOR", [sala, direccion])

    def esperar(self, logica, veces=1):
        for _ in range(veces):
            self.jugar(logica, "ESPERAR")

    def usar_pergamino(self, logica):
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        logica.estadoJuego.jugador.inventario.agregar_objeto(pergamino)
        return self.jugar(logica, "USAR_OBJETO", [pergamino])

    def pendientes(self, logica, tipo, id_actor=None):
        encontrados = []
        for evento in logica.estadoJuego.reloj.heap:
            if evento.tipo_accion != tipo:
                continue
            actor = evento.actor
            identificador = getattr(actor, "id_instancia", None)
            if id_actor is None or identificador == id_actor:
                encontrados.append(evento)
        return encontrados

    def marcadores(self):
        total = 0
        nodo = RetrocesoLogica().cabeza
        while nodo is not None:
            if nodo.es_accion:
                total += 1
            nodo = nodo.siguiente
        return total

    def sin_ultimo_paso(self, foto):
        foto = dict(foto)
        foto["salas"] = [None if sala is None else sala[:1] + sala[2:] for sala in foto["salas"]]
        return foto

    def foto(self, logica):
        estado = logica.estadoJuego
        jugador = estado.jugador
        salas = []
        for sala in estado.salas:
            if sala is None:
                salas.append(None)
                continue
            salas.append((
                sala.id,
                sala.ultimo_paso,
                [(e.id_instancia, e.vida_actual, e.id_sala_actual) for e in sala.enemigos],
                [(t.id_instancia, t.armada) for t in sala.trampas],
                [(s.direccion, s.cerrada) for s in sala.salidas],
                [o.id_catalogo for o in sala.objetos],
            ))
        return {
            "salas": salas,
            "heap": sorted((e.tiempo_ejecucion, e.id_secuencia, e.tipo_accion) for e in estado.reloj.heap),
            "vida": jugador.vida_actual,
            "sala_jugador": jugador.id_sala_actual,
            "puntaje": estado.puntaje,
            "eliminados": jugador.enemigos_eliminados,
            "inventario": jugador.inventario.cantidad_actual,
            "modificador": jugador.modificador_velocidad,
            "antorcha": jugador.antorcha_encendida,
        }


class TestAgrupacionDeAcciones(PruebaRetroceso):
    def test_esperar_cuenta_como_accion_y_se_deshace(self):
        logica = self.nueva()
        sala = logica.estadoJuego.salas[1]
        salida = sala.salidas[0]
        salida.cerrada = True
        self.jugar(logica, "ABRIR_PUERTA", [sala, "norte"])
        self.esperar(logica)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, 2)

        self.usar_pergamino(logica)
        self.assertFalse(salida.cerrada)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, 1)

        self.usar_pergamino(logica)
        self.assertTrue(salida.cerrada)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, 0)

    def test_accion_fallida_del_jugador_cuenta(self):
        logica = self.nueva()
        resultado = self.mover(logica, "sur")
        self.assertFalse(resultado.exito)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, 1)

    def test_solo_las_acciones_del_jugador_abren_grupo(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        self.esperar(logica, 2)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, 3)
        self.assertEqual(self.marcadores(), 3)
        self.assertGreater(RetrocesoLogica().cantidad_actual, 3)

    def test_el_tope_de_cinco_cuenta_acciones_del_jugador(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        self.esperar(logica, 9)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, 5)
        self.assertEqual(self.marcadores(), 5)

    def test_usar_el_pergamino_no_abre_grupo(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        self.esperar(logica)
        antes = RetrocesoLogica().cantidad_acciones
        self.usar_pergamino(logica)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, antes - 1)

    def test_pergamino_sin_historial_no_se_consume(self):
        logica = self.nueva()
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        logica.estadoJuego.jugador.inventario.agregar_objeto(pergamino)
        resultado = self.jugar(logica, "USAR_OBJETO", [pergamino])
        self.assertFalse(resultado.exito)
        self.assertEqual(logica.estadoJuego.jugador.inventario.cantidad_actual, 1)

    def test_hasta_cinco_pergaminos_seguidos(self):
        logica = self.nueva()
        sala = logica.estadoJuego.salas[1]
        sala.salidas[0].cerrada = True
        self.jugar(logica, "ABRIR_PUERTA", [sala, "norte"])
        self.esperar(logica, 4)
        for _ in range(5):
            self.usar_pergamino(logica)
        self.assertEqual(RetrocesoLogica().cantidad_acciones, 0)
        self.assertTrue(sala.salidas[0].cerrada)
        self.assertEqual(logica.estadoJuego.reloj.heap, [])


class TestRestauracionExacta(PruebaRetroceso):
    def test_deshacer_deja_el_estado_anterior_a_la_accion(self):
        logica = self.nueva()
        sala = logica.estadoJuego.salas[1]
        sala.salidas[0].cerrada = True
        sala.salidas[0].cierre_automatico = 300
        antes = self.foto(logica)
        mensajes_antes = [r.mensaje for r in logica.logEventosJuego.obtener_eventos()]

        self.jugar(logica, "ABRIR_PUERTA", [sala, "norte"])
        self.assertNotEqual(self.foto(logica), antes)
        self.usar_pergamino(logica)

        despues = self.foto(logica)
        self.assertEqual(despues, antes)
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, 100)
        mensajes = [r.mensaje for r in logica.logEventosJuego.obtener_eventos()]
        self.assertEqual(mensajes, mensajes_antes + [MENSAJE_PERGAMINO])

    def test_restaura_todo_lo_ocurrido_despues_de_la_accion(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        self.esperar(logica)
        referencia = self.foto(logica)
        tiempo = logica.estadoJuego.reloj.tiempo_actual

        self.usar_pergamino(logica)

        restaurada = self.foto(logica)
        self.assertEqual(self.sin_ultimo_paso(restaurada), self.sin_ultimo_paso(referencia))
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, tiempo)

    def test_puntaje_eliminados_ultimo_paso_y_bitacora(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        sala = logica.estadoJuego.salas[2]
        enemigo = sala.enemigos[0]
        enemigo.vida_actual = 1
        for otro in sala.enemigos[1:]:
            otro.vida_actual = 0
        puntaje = logica.estadoJuego.puntaje

        self.jugar(logica, "ATACAR", [enemigo])
        ultimo_paso_con_ataque = sala.ultimo_paso
        mensajes_con_ataque = [r.mensaje for r in logica.logEventosJuego.obtener_eventos()]
        self.assertEqual(logica.estadoJuego.jugador.enemigos_eliminados, 1)
        self.assertEqual(logica.estadoJuego.puntaje, puntaje + 50)

        self.usar_pergamino(logica)

        self.assertEqual(logica.estadoJuego.jugador.enemigos_eliminados, 0)
        self.assertEqual(logica.estadoJuego.puntaje, puntaje)
        self.assertEqual(enemigo.vida_actual, 1)
        self.assertLess(sala.ultimo_paso, ultimo_paso_con_ataque)
        mensajes = [r.mensaje for r in logica.logEventosJuego.obtener_eventos()]
        self.assertEqual(mensajes, mensajes_con_ataque[:-1] + [MENSAJE_PERGAMINO])

class TestEventosDelEntorno(PruebaRetroceso):
    def test_enemigo_revivido_sigue_activo(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        sala = logica.estadoJuego.salas[2]
        e1, e2 = sala.enemigos
        e2.vida_actual = 0
        e1.vida_actual = 1
        self.jugar(logica, "ATACAR", [e1])
        self.assertEqual(e1.vida_actual, 0)

        self.usar_pergamino(logica)

        self.assertEqual(e1.vida_actual, 1)
        self.assertEqual(len(self.pendientes(logica, "ACCION_ENEMIGO", "e-201")), 1)
        vida = logica.estadoJuego.jugador.vida_actual
        self.esperar(logica, 3)
        self.assertLess(logica.estadoJuego.jugador.vida_actual, vida)

    def test_deshacer_un_ataque_enemigo_conserva_su_cadena(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        self.esperar(logica)
        self.usar_pergamino(logica)
        for id_enemigo in ("e-201", "e-202"):
            self.assertEqual(len(self.pendientes(logica, "ACCION_ENEMIGO", id_enemigo)), 1)

    def test_puerta_con_cierre_automatico_cancela_el_evento(self):
        logica = self.nueva()
        sala = logica.estadoJuego.salas[1]
        salida = sala.salidas[0]
        salida.cerrada = True
        salida.cierre_automatico = 300
        self.jugar(logica, "ABRIR_PUERTA", [sala, "norte"])
        self.assertEqual(len(self.pendientes(logica, "CERRAR_PUERTA")), 1)

        self.usar_pergamino(logica)
        self.assertTrue(salida.cerrada)
        self.assertEqual(self.pendientes(logica, "CERRAR_PUERTA"), [])

        self.jugar(logica, "ABRIR_PUERTA", [sala, "norte"])
        apertura = logica.estadoJuego.reloj.tiempo_actual
        for _ in range(8):
            self.esperar(logica)
            if salida.cerrada:
                break
        self.assertTrue(salida.cerrada)
        self.assertEqual(logica.estadoJuego.reloj.tiempo_actual, apertura + 300)

    def test_deshacer_el_cierre_automatico_vuelve_a_programarlo(self):
        logica = self.nueva()
        sala = logica.estadoJuego.salas[1]
        salida = sala.salidas[0]
        salida.cerrada = True
        salida.cierre_automatico = 300
        self.jugar(logica, "ABRIR_PUERTA", [sala, "norte"])
        self.esperar(logica, 3)
        self.assertTrue(salida.cerrada)

        for _ in range(4):
            if not salida.cerrada:
                break
            self.usar_pergamino(logica)
        self.assertFalse(salida.cerrada)
        self.assertEqual(len(self.pendientes(logica, "CERRAR_PUERTA")), 1)

        for _ in range(4):
            self.esperar(logica)
            if salida.cerrada:
                break
        self.assertTrue(salida.cerrada)

    def test_pocion_deshecha_no_deja_el_evento_de_vencimiento(self):
        logica = self.nueva()
        jugador = logica.estadoJuego.jugador
        pocion = Pocion("itm_pocion_vel", "Pocion velocidad", 1, 1, cura=0, modificador_velocidad=20, duracion=300)
        jugador.inventario.agregar_objeto(pocion)
        self.jugar(logica, "USAR_OBJETO", [pocion])
        self.assertEqual(jugador.modificador_velocidad, 20)

        self.usar_pergamino(logica)
        self.assertEqual(jugador.modificador_velocidad, 0)
        self.assertEqual(self.pendientes(logica, "REVERTIR_MODIFICADOR_VELOCIDAD"), [])
        self.esperar(logica, 5)
        self.assertEqual(jugador.modificador_velocidad, 0)

    def test_deshacer_el_vencimiento_de_la_pocion_lo_vuelve_a_programar(self):
        logica = self.nueva()
        jugador = logica.estadoJuego.jugador
        pocion = Pocion("itm_pocion_vel", "Pocion velocidad", 1, 1, cura=0, modificador_velocidad=20, duracion=300)
        jugador.inventario.agregar_objeto(pocion)
        self.jugar(logica, "USAR_OBJETO", [pocion])
        self.esperar(logica, 4)
        self.assertEqual(jugador.modificador_velocidad, 0)

        for _ in range(5):
            if jugador.modificador_velocidad == 20:
                break
            self.usar_pergamino(logica)
        self.assertEqual(jugador.modificador_velocidad, 20)
        self.assertEqual(len(self.pendientes(logica, "REVERTIR_MODIFICADOR_VELOCIDAD")), 1)

        for _ in range(5):
            self.esperar(logica)
            if jugador.modificador_velocidad == 0:
                break
        self.assertEqual(jugador.modificador_velocidad, 0)

    def test_antorcha_deshecha_y_vencimiento_deshecho(self):
        logica = self.nueva()
        jugador = logica.estadoJuego.jugador
        antorcha = Antorcha("itm_antorcha", "Antorcha", 1, 1, duracion=300)
        jugador.inventario.agregar_objeto(antorcha)
        self.jugar(logica, "USAR_OBJETO", [antorcha])
        self.assertTrue(jugador.antorcha_encendida)
        self.usar_pergamino(logica)
        self.assertFalse(jugador.antorcha_encendida)
        self.assertEqual(self.pendientes(logica, "APAGAR_ANTORCHA"), [])

        logica = self.nueva()
        jugador = logica.estadoJuego.jugador
        antorcha = Antorcha("itm_antorcha", "Antorcha", 1, 1, duracion=300)
        jugador.inventario.agregar_objeto(antorcha)
        self.jugar(logica, "USAR_OBJETO", [antorcha])
        self.esperar(logica, 4)
        self.assertFalse(jugador.antorcha_encendida)
        for _ in range(5):
            if jugador.antorcha_encendida:
                break
            self.usar_pergamino(logica)
        self.assertTrue(jugador.antorcha_encendida)
        self.assertEqual(len(self.pendientes(logica, "APAGAR_ANTORCHA")), 1)
        for _ in range(5):
            self.esperar(logica)
            if not jugador.antorcha_encendida:
                break
        self.assertFalse(jugador.antorcha_encendida)


class TestTrampas(PruebaRetroceso):
    """§2.10: una trampa armada se activa cuando el jugador entra a la sala; no se sondea con el reloj."""

    def entrar_a_la_sala_de_la_trampa(self, logica):
        self.mover(logica, "norte")          # sale de la sala 1 (donde está la trampa)
        return self.mover(logica, "sur")     # y vuelve a entrar

    def test_la_sala_con_trampa_no_programa_eventos_al_cargarse(self):
        logica = self.nueva(con_trampa=True)
        self.assertEqual(self.pendientes(logica, "ACTIVAR_TRAMPA", "t-1"), [])
        self.assertEqual(self.pendientes(logica, "ARMAR_TRAMPA", "t-1"), [])
        self.esperar(logica, 6)
        self.assertTrue(logica.estadoJuego.salas[1].trampas[0].armada)

    def test_entrar_activa_la_trampa_la_desarma_y_programa_su_rearme(self):
        logica = self.nueva(con_trampa=True)
        trampa = logica.estadoJuego.salas[1].trampas[0]
        resultado = self.entrar_a_la_sala_de_la_trampa(logica)
        self.assertFalse(trampa.armada)
        self.assertIn("t-1", resultado.mensaje)
        rearmes = self.pendientes(logica, "ARMAR_TRAMPA", "t-1")
        self.assertEqual(len(rearmes), 1)
        self.assertLessEqual(rearmes[0].tiempo_ejecucion - logica.estadoJuego.reloj.tiempo_actual, trampa.rearme)

    def test_entrar_con_la_trampa_desarmada_no_hace_nada(self):
        logica = self.nueva(con_trampa=True)
        self.entrar_a_la_sala_de_la_trampa(logica)
        jugador = logica.estadoJuego.jugador
        self.mover(logica, "norte")
        resultado = self.mover(logica, "sur")
        self.assertNotIn("t-1", resultado.mensaje)

    def test_deshacer_la_entrada_deja_la_trampa_armada_y_sin_rearme(self):
        logica = self.nueva(con_trampa=True)
        jugador = logica.estadoJuego.jugador
        trampa = logica.estadoJuego.salas[1].trampas[0]
        self.mover(logica, "norte")
        self.mover(logica, "sur")
        self.assertFalse(trampa.armada)
        vida_tras_entrar = jugador.vida_actual
        self.usar_pergamino(logica)
        self.assertTrue(trampa.armada)
        # solo se devuelve lo que hizo la trampa; los golpes de enemigos previos a la acción no pertenecen a ella
        self.assertEqual(jugador.vida_actual, vida_tras_entrar + trampa.daño)
        self.assertEqual(jugador.id_sala_actual, 2)
        self.assertEqual(self.pendientes(logica, "ARMAR_TRAMPA", "t-1"), [])
        self.assertEqual(self.pendientes(logica, "ACTIVAR_TRAMPA", "t-1"), [])

    def test_el_rearme_no_programa_otra_activacion_y_deshacerlo_lo_reprograma(self):
        logica = self.nueva(con_trampa=True)
        trampa = logica.estadoJuego.salas[1].trampas[0]
        self.entrar_a_la_sala_de_la_trampa(logica)
        armada_previa = trampa.armada
        for _ in range(10):
            armada_previa = trampa.armada
            self.esperar(logica)
            if trampa.armada and not armada_previa:
                break
        self.assertTrue(trampa.armada)
        self.assertEqual(self.pendientes(logica, "ACTIVAR_TRAMPA", "t-1"), [])
        self.assertEqual(self.pendientes(logica, "ARMAR_TRAMPA", "t-1"), [])

        for _ in range(4):
            if not trampa.armada:
                break
            self.usar_pergamino(logica)
        self.assertFalse(trampa.armada)
        self.assertEqual(len(self.pendientes(logica, "ARMAR_TRAMPA", "t-1")), 1)


class TestPergaminosYPersistencia(PruebaRetroceso):
    def test_recoger_un_pergamino_y_usarlo_no_falla(self):
        logica = self.nueva()
        sala = logica.estadoJuego.salas[1]
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        sala.objetos.append(pergamino)
        self.jugar(logica, "RECOGER_OBJETO", [pergamino])
        self.assertEqual(logica.estadoJuego.jugador.inventario.cantidad_actual, 1)
        resultado = self.jugar(logica, "USAR_OBJETO", [pergamino])
        self.assertTrue(resultado.exito)
        self.assertEqual(logica.estadoJuego.jugador.inventario.cantidad_actual, 0)
        self.assertEqual(sala.objetos, [])

    def test_el_pergamino_funciona_igual_despues_de_cargar_la_partida(self):
        logica = self.nueva()
        self.mover(logica, "norte")
        self.esperar(logica, 3)
        carpeta = tempfile.mkdtemp()
        archivo = os.path.join(carpeta, "partida.sav")
        logica.guardarPartida(archivo)

        self.usar_pergamino(logica)
        self.esperar(logica, 2)
        self.usar_pergamino(logica)
        referencia = self.foto(logica)

        cargada = EstadoJuegoLogica()
        cargada.comunicacion = ServicioCripta(ApiPrueba(), CacheLRU(25))
        cargada.cargarPartida(archivo)
        self.usar_pergamino(cargada)
        self.esperar(cargada, 2)
        self.usar_pergamino(cargada)
        self.assertEqual(self.foto(cargada), referencia)


class TestSimulacionAleatoria(PruebaRetroceso):
    def revisar(self, logica):
        estado = logica.estadoJuego
        ubicaciones = {}
        for sala in estado.salas:
            if sala is not None:
                for enemigo in sala.enemigos:
                    ubicaciones.setdefault(enemigo.id_instancia, []).append(sala.id)
        for enemigo in estado.catalogo_enemigos:
            self.assertEqual(ubicaciones.get(enemigo.id_instancia), [enemigo.id_sala_actual])
            if enemigo.vida_actual > 0:
                self.assertEqual(len(self.pendientes(logica, "ACCION_ENEMIGO", enemigo.id_instancia)), 1)
        for evento in estado.reloj.heap:
            self.assertGreaterEqual(evento.tiempo_ejecucion, estado.reloj.tiempo_actual)

    def test_invariantes_con_pergaminos_al_azar(self):
        for semilla in range(40):
            azar = random.Random(semilla)
            logica = self.nueva(con_trampa=True, semilla=semilla)
            for _ in range(40):
                if logica.fin:
                    break
                jugador = logica.estadoJuego.jugador
                sala = logica.ingresarEnSala(jugador.id_sala_actual)
                sorteo = azar.random()
                if sorteo < 0.3:
                    self.esperar(logica)
                elif sorteo < 0.55:
                    self.mover(logica, "norte" if jugador.id_sala_actual == 1 else "sur")
                elif sorteo < 0.75:
                    vivos = [e for e in sala.enemigos if e.vida_actual > 0]
                    if vivos:
                        self.jugar(logica, "ATACAR", [vivos[0]])
                elif RetrocesoLogica().hay_algo_para_deshacer():
                    self.usar_pergamino(logica)
                self.revisar(logica)


if __name__ == "__main__":
    unittest.main(verbosity=2)
