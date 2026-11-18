"""Capacidad 011, historia 2: texto exacto de las pantallas (FR-306 a FR-311; SC-304 a SC-307).
Contrato: specs/011-arranque-verificado-pantallas/contracts/pantallas.md. Las funciones de pantalla son puras: se compara
el texto que devuelven, sin capturar la salida estándar. Cada prueba cita el requisito que demuestra."""
import re
import unittest

from Controlador import Pantallas as P
from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.ConocimientoDTO import SalaConocidaDTO, SalidaConocidaDTO
from DTO.Objeto import Objeto
from DTO.SalaDTO import SalaDTO
from DTO.TrampaDTO import Trampa

LINEA = "=" * 50
TITULOS = ["--- SALIDAS ---", "--- ENEMIGOS ---", "--- OBJETOS ---", "--- TRAMPAS ---", "--- ESTADO DEL JUGADOR ---",
           "--- INVENTARIO ---", "--- ÚLTIMOS MENSAJES (máx. 20) ---"]
PALABRAS_EN_OTRO_IDIOMA = ("invalid", "not found", "failed", "unknown")


def jugador(vida=80, maximo=100, antorcha=False, hasta=0):
    return JugadorDTO(vida, maximo, 10, 5, 100, id_sala_actual=1, antorcha_encendida=antorcha, antorcha_hasta=hasta)


def enemigo(nombre, activo, comportamiento="errante", vida=30, maximo=40):
    return EnemigoDTO(vida_actual=vida, vida_max=maximo, ataque=5, defensa=1, velocidad=100, id_instancia="e-" + nombre,
                      tipo="ent_" + nombre.lower(), nombre=nombre, comportamiento=comportamiento, activo=activo)


def sala(enemigos=(), objetos=(), trampas=()):
    return SalaDTO(1, "Entrada", enemigos=list(enemigos), objetos=list(objetos), trampas=list(trampas))


def conocida(*salidas):
    return SalaConocidaDTO(1, "Entrada", list(salidas))


def salida(direccion, costo, puerta, explorado=False, destino="", id_destino=None):
    return SalidaConocidaDTO(direccion, costo, puerta, explorado, id_destino, destino)


_jugador, _sala, _conocida = jugador, sala, conocida          # los parámetros de `pantalla` ocultan estos nombres


def pantalla(jugador=None, tiempo=250, sala=None, sala_conocida=None, llaves=None, objeto_actual=None, mensajes=()):
    return P.texto_sala(jugador or _jugador(), tiempo, sala or _sala(), sala_conocida or _conocida(), llaves,
                        objeto_actual, list(mensajes))


def titulos_en(texto):
    return [linea for linea in texto.splitlines() if linea.startswith("---")]


class TestPantallaDeSala(unittest.TestCase):

    def test_FR306_sala_vacia_conserva_todas_las_secciones_en_el_mismo_orden(self):
        esperado = "\n".join([
            LINEA, "SALA: Entrada (id 1)", LINEA,
            "", "--- SALIDAS ---", "  (ninguna)",
            "", "--- ENEMIGOS ---", "  (ninguno)",
            "", "--- OBJETOS ---", "  (ninguno)",
            "", "--- TRAMPAS ---", "  (ninguna)",
            "", "--- ESTADO DEL JUGADOR ---", "  Vida: 80/100", "  Tiempo: 250", "  Antorcha: apagada",
            "", "--- INVENTARIO ---", "  Objeto actual: (inventario vacío)",
            "", "--- ÚLTIMOS MENSAJES (máx. 20) ---", "  (sin mensajes)",
        ])
        self.assertEqual(pantalla(), esperado)

    def test_FR306_sala_con_salidas_en_los_tres_estados_de_puerta(self):
        texto = pantalla(sala_conocida=conocida(
            salida("norte", 100, "abierta", True, "Pasillo", 2),
            salida("este", 250, "cerrada"),
            salida("sur", 70, "cerrada"),
            salida("oeste", 100, "sin observar")), llaves=[None, "itm_llave_negra", None, None])
        self.assertIn("  norte  -> Pasillo  [abierta]  costo 100", texto)
        self.assertIn("  este   -> sala sin explorar  [cerrada, requiere itm_llave_negra]  costo 250", texto)
        self.assertIn("  sur    -> sala sin explorar  [cerrada]  costo 70", texto)
        self.assertIn("  oeste  -> sala sin explorar  [sin observar]  costo 100", texto)
        self.assertEqual(titulos_en(texto), TITULOS)

    def test_FR306_FR219_una_sala_avistada_no_revela_ni_su_nombre_ni_su_id(self):
        texto = pantalla(sala_conocida=conocida(salida("este", 100, "abierta", False, "Secreta", 9)))
        self.assertIn("sala sin explorar", texto)
        self.assertNotIn("Secreta", texto)
        self.assertNotIn("id 9", texto)

    def test_FR306_enemigos_activos_dormidos_y_cazador(self):
        texto = pantalla(sala=sala(enemigos=[enemigo("Orco", True), enemigo("Esbirro", False),
                                             enemigo("Sombra", True, "cazador", 10, 20)]))
        self.assertIn("  - Orco [activo]  vida 30/40", texto)
        self.assertIn("  - Esbirro [dormido]  vida 30/40", texto)
        self.assertIn("  - [cazador] Sombra [activo]  vida 10/20", texto)
        self.assertEqual(titulos_en(texto), TITULOS)

    def test_FR306_objetos_y_trampas(self):
        texto = pantalla(
            sala=sala(objetos=[Objeto("itm_espada", "espada", 5, 10), "itm_pocion_roja"],
                      trampas=[Trampa("t-1", "trp_dardos", 1, 7, 100, True), Trampa("t-2", "trp_foso", 1, 20, 300, False)]))
        self.assertIn("  - Espada (id itm_espada)", texto)
        self.assertIn("  - Pocion roja (id itm_pocion_roja)", texto)
        self.assertIn("  - Dardos [daño 7] armada", texto)
        self.assertIn("  - Foso [daño 20] desarmada", texto)

    def test_FR306_estado_del_jugador_con_antorcha_encendida_y_sin_mensajes_o_con_mensajes(self):
        texto = pantalla(jugador=jugador(10, 100, True, 900), tiempo=400, mensajes=["Golpeaste al Orco.", "Te hirieron."],
                         objeto_actual=Objeto("itm_pocion", "poción", 1, 5))
        self.assertIn("  Vida: 10/100\n  Tiempo: 400\n  Antorcha: encendida hasta t=900", texto)
        self.assertIn("  Objeto actual: poción (id itm_pocion)", texto)
        self.assertTrue(texto.endswith("  Golpeaste al Orco.\n  Te hirieron."))

    def test_FR311_la_misma_pantalla_dos_veces_es_identica_y_es_texto_plano(self):
        def construir():
            return pantalla(sala=sala(enemigos=[enemigo("Orco", False)], objetos=["itm_llave_a"]),
                            sala_conocida=conocida(salida("este", 100, "abierta", True, "Pasillo", 2)), mensajes=["Hola."])
        primero, segundo = construir(), construir()
        self.assertEqual(primero, segundo)
        self.assertNotIn("\x1b", primero)
        self.assertNotIn("\t", primero)

    def test_SC304_cinco_o_mas_situaciones_tienen_las_mismas_secciones_en_el_mismo_orden(self):
        situaciones = [
            pantalla(),
            pantalla(sala=sala(enemigos=[enemigo("Orco", True)])),
            pantalla(sala=sala(objetos=["itm_a"], trampas=[Trampa("t", "trp_x", 1, 1, 1)])),
            pantalla(sala_conocida=conocida(salida("este", 1, "cerrada"), salida("sur", 1, "sin observar"))),
            pantalla(jugador=jugador(1, 100, True, 5), mensajes=["a"] * 20),
            pantalla(objeto_actual=Objeto("itm_p", "p", 1, 1), tiempo=None),
        ]
        for texto in situaciones:
            self.assertEqual(titulos_en(texto), TITULOS)
            self.assertTrue(texto.startswith(LINEA + "\nSALA: Entrada (id 1)\n" + LINEA))


class TestResumenDeFinDePartida(unittest.TestCase):

    def resumen(self, motivo="El jugador ha llegado a la sala final", salas_exploradas=6, version="v3"):
        return P.texto_fin_partida(motivo, 120, 14, 1850, 77, salas_exploradas, "cripta-01", version, 4)

    def test_FR307_texto_exacto_con_los_seis_rotulos_en_orden(self):
        esperado = "\n".join([
            LINEA, "FIN DE LA PARTIDA", LINEA,
            "Motivo: El jugador ha llegado a la sala final", "Puntaje: 120", "Acciones: 14", "Tiempo: 1850",
            "Vida final: 77", "Salas exploradas: 6", LINEA,
            "Cripta: cripta-01 (versión v3) | Enemigos derrotados: 4",
        ])
        self.assertEqual(self.resumen(), esperado)

    def test_FR307_muerte_motivo_vacio_y_sin_mapa(self):
        self.assertIn("Motivo: El jugador ha muerto", self.resumen(motivo="El jugador ha muerto"))
        for vacio in (None, "", "   "):
            self.assertIn("Motivo: Motivo no informado", self.resumen(motivo=vacio))
        self.assertIn("Salas exploradas: no disponible", self.resumen(salas_exploradas=None))
        self.assertIn("(sin versión)", self.resumen(version=None))

    def test_FR311_el_resumen_es_identico_cada_vez(self):
        self.assertEqual(self.resumen(), self.resumen())


class TestAyuda(unittest.TestCase):
    # Comandos que el controlador reconoce hoy (se comprueban uno por uno en test_pantallas_controlador).
    RECONOCIDOS = ("norte", "sur", "este", "oeste", "atacar", "abrir", "recoger", "usar", "soltar", "siguiente", "sig",
                   "anterior", "ant", "esperar", "inventario", "mapa", "ir", "historia", "ayuda", "salir")

    def test_FR309_la_ayuda_lista_todos_los_comandos_con_su_sintaxis(self):
        texto = P.texto_ayuda()
        self.assertTrue(texto.startswith("COMANDOS DISPONIBLES\n"))
        for fila in P.COMANDOS:
            self.assertIn(fila[1], texto)
        for sintaxis in ("norte | sur | este | oeste", "mapa", "ir a <id de sala>", "historia <t>", "historia #k",
                         "inventario [peso|valor|nombre]", "ayuda", "salir"):
            self.assertIn(sintaxis, texto)

    def test_FR309_cada_comando_reconocido_esta_en_la_tabla_y_cada_fila_es_reconocida(self):
        for comando in self.RECONOCIDOS:
            self.assertIsNotNone(P.buscar_comando(comando), comando)
        for fila in P.COMANDOS:
            for alias in fila[0].split("|"):
                self.assertIn(alias, self.RECONOCIDOS, f"la tabla tiene un comando que el controlador no reconoce: {alias}")

    def test_FR309_cerrar_y_guardar_no_estan_porque_no_son_comandos(self):
        self.assertIsNone(P.buscar_comando("cerrar"))
        self.assertIsNone(P.buscar_comando("guardar"))

    def test_FR309_la_tabla_no_repite_nombres(self):
        vistos = []
        for fila in P.COMANDOS:
            for alias in fila[0].split("|"):
                self.assertNotIn(alias, vistos)
                vistos.append(alias)

    def test_FR309_buscar_comando_no_distingue_mayusculas(self):
        self.assertIs(P.buscar_comando("NoRtE"), P.buscar_comando("norte"))
        self.assertIsNone(P.buscar_comando("xyz"))

    def test_FR309_la_ayuda_posterior_a_la_partida_solo_lista_los_comandos_que_siguen_valiendo(self):
        texto = P.texto_ayuda(post_partida=True)
        for sintaxis in ("historia <t>", "historia #k", "ayuda", "salir"):
            self.assertIn(sintaxis, texto)
        for fuera in ("atacar", "recoger", "mapa", "norte"):
            self.assertNotIn(fuera, texto)

    def test_FR311_la_ayuda_es_identica_cada_vez(self):
        self.assertEqual(P.texto_ayuda(), P.texto_ayuda())


class TestMensajesDeError(unittest.TestCase):

    def mensajes(self):
        return [(nombre, funcion(*args)) for nombre, funcion, args in P.MENSAJES]

    def test_FR310_texto_error_junta_que_paso_y_que_hacer(self):
        self.assertEqual(P.texto_error("Algo falló.", "Prueba de nuevo."), "Algo falló. Prueba de nuevo.")

    def test_FR310_texto_error_sin_una_de_las_dos_partes_es_un_defecto(self):
        for que_paso, que_hacer in (("", "Haz algo."), ("Pasó algo.", ""), ("  ", "x"), ("x", None)):
            with self.assertRaises(ValueError):
                P.texto_error(que_paso, que_hacer)

    def test_FR310_todo_mensaje_del_catalogo_dice_que_paso_y_que_hacer(self):
        for nombre, texto in self.mensajes():
            with self.subTest(mensaje=nombre):
                self.assertTrue(texto.strip())
                self.assertRegex(texto, r"[.!?] \S", "debe tener al menos dos oraciones: qué pasó y qué hacer")
                self.assertTrue(texto.endswith((".", "?", "!")))
                self.assertNotIn("\n", texto)

    def test_FR308_SC307_los_mensajes_estan_en_espanol_y_sin_secuencias_de_color(self):
        for nombre, texto in self.mensajes():
            with self.subTest(mensaje=nombre):
                self.assertNotIn("\x1b", texto)
                for palabra in PALABRAS_EN_OTRO_IDIOMA:
                    self.assertNotIn(palabra, texto.lower())
                self.assertIsNone(re.search("Ã|Â|â€", texto), "caracteres dañados por la codificación")

    def test_FR310_el_catalogo_no_repite_nombres_y_cubre_los_rechazos_de_la_lista(self):
        nombres = [n for n, _, _ in P.MENSAJES]
        for i, nombre in enumerate(nombres):
            self.assertNotIn(nombre, nombres[:i])
        for obligatorio in ("sin_salida", "salida_cerrada_con_llave", "comando_desconocido", "ir_a_destino_invalido",
                            "historia_sin_parametro", "inventario_vacio", "sin_criptas", "numero_cripta_invalido",
                            "cripta_no_resoluble"):
            self.assertIn(obligatorio, nombres)

    def test_FR310_textos_exactos_del_contrato(self):
        self.assertEqual(P.mensaje_sin_salida("norte"),
                         "No existe una salida hacia el 'norte'. Mira la lista de SALIDAS y elige una dirección que aparezca.")
        self.assertEqual(P.mensaje_comando_desconocido("xyz"),
                         "No reconozco el comando 'xyz'. Escribe 'ayuda' para ver los comandos.")
        self.assertEqual(P.mensaje_ir_a_destino_invalido(),
                         "El destino de 'ir a' debe ser el número de una sala. Ejemplo: ir a 12.")
        self.assertEqual(P.mensaje_cripta_no_resoluble("cripta-01"),
                         "La cripta cripta-01 no tiene solución, por eso no se abrió la partida. Elige otra cripta, "
                         "o inicia con --forzar para jugarla de todos modos.")

    def test_FR310_un_error_del_modelo_no_termina_en_dos_puntos(self):
        self.assertNotIn("..", P.mensaje_ir_a_rechazada("Esa sala no está explorada."))


if __name__ == "__main__":
    unittest.main()
