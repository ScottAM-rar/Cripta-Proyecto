"""Niebla de guerra (capacidad 002), historia 6: guardar y cargar una partida con niebla.
Contrato: specs/002-niebla-de-guerra/contracts/estado-guardado-niebla.md. Cada prueba cita el requisito que demuestra."""
import copy
import os
import tempfile
import unittest

from adaptadores import AlmacenPartidaBinario as modulo_partida
from adaptadores.AlmacenPartidaBinario import AlmacenPartidaBinario, ErrorPartida
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta
from DTO import EstadoGuardadoDTO as modulo_estado
from DTO.EstadoGuardadoDTO import ConocimientoGuardadoDTO, PuertaRecordadaDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from tests_labs.api_falsa import HttpConfigurable
from tests_labs.cripta_sintetica import esqueleto_de_conexiones
from tests_labs.partida_prueba import esperar, jugar, nueva_partida


def mover(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "MOVER_JUGADOR", [sala, direccion])


def abrir(logica, direccion):
    sala = logica.estadoJuego.salas[logica.estadoJuego.jugador.id_sala_actual]
    return jugar(logica, "ABRIR_PUERTA", [sala, direccion])


def foto(logica):
    c = logica.mapaConocido
    return (list(c.estado), list(c.puertas), list(c.exploradas))


def cripta():
    """1 -E- 2 -E- 3 -E- 4 ; 2 -N- 5 ; la puerta 1->2 está cerrada y se cierra sola a los 300 una vez abierta."""
    salas = esqueleto_de_conexiones([(1, 2, None, "E", "O", {"cerrada": True}), (2, 3, None, "E", "O"),
                                     (3, 4, None, "E", "O"), (2, 5, None, "N", "S")])
    salas[0]["salidas"]["E"]["cierre_automatico"] = 300
    return salas


def partida_con_niebla():
    """Salas exploradas y avistadas, y una puerta recordada abierta que en realidad está cerrada."""
    logica = nueva_partida(cripta())
    abrir(logica, "este")
    mover(logica, "este")
    mover(logica, "este")
    esperar(logica, 3)                                                       # la puerta 1->2 se cerró lejos
    return logica


def guardar_y_cargar(logica):
    carpeta = tempfile.mkdtemp()
    archivo = os.path.join(carpeta, "partida.bin")
    AlmacenPartidaBinario(archivo).guardar(logica.exportar_estado())
    cargada = EstadoJuegoLogica()
    cargada.comunicacion = ServicioCripta(HttpConfigurable(cripta(), sala_salida=1000), CacheLRU(25))
    cargada.restaurar_estado(AlmacenPartidaBinario(archivo).cargar())
    return cargada, archivo


class TestIdaYVuelta(unittest.TestCase):
    def test_FR220_SC004_el_conocimiento_se_restaura_exactamente(self):
        logica = partida_con_niebla()
        c = logica.mapaConocido
        self.assertEqual(c.puerta_recordada(1, 2), 1)                        # recuerda abierta
        self.assertTrue(logica.estadoJuego.salas[1].salidas[0].cerrada)       # y está cerrada
        cargada, _ = guardar_y_cargar(logica)
        self.assertEqual(foto(cargada), foto(logica))
        self.assertEqual(cargada.mapaConocido.puerta_recordada(1, 2), 1)      # sigue recordando abierta
        self.assertEqual(cargada.instantaneaMapaConocido(), logica.instantaneaMapaConocido())

    def test_FR220_lo_restaurado_empieza_sin_historial_y_no_se_puede_deshacer(self):
        from tests_labs.partida_prueba import jugar as jugar_accion
        from DTO.Objeto import PergaminoRetroceso
        cargada, _ = guardar_y_cargar(partida_con_niebla())
        antes = foto(cargada)
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        cargada.estadoJuego.jugador.inventario.agregar_objeto(pergamino)
        resultado = jugar_accion(cargada, "USAR_OBJETO", [pergamino])
        self.assertFalse(resultado.exito)
        self.assertEqual(foto(cargada), antes)

    def test_FR220_FR222_SC004_continuar_con_las_mismas_acciones_da_el_mismo_conocimiento(self):
        sin_guardar = partida_con_niebla()
        guardada, _ = guardar_y_cargar(partida_con_niebla())
        for logica in (sin_guardar, guardada):
            mover(logica, "oeste")                                           # vuelve a la sala 2: observa la puerta cerrada
            mover(logica, "norte")
            mover(logica, "sur")
        self.assertEqual(foto(guardada), foto(sin_guardar))
        self.assertEqual(guardada.mapaConocido.puerta_recordada(1, 2), 2)

    def test_FR220_el_archivo_guarda_solo_lo_no_desconocido_y_en_orden(self):
        logica = partida_con_niebla()
        guardado = logica.exportar_estado().conocimiento
        self.assertIsInstance(guardado, ConocimientoGuardadoDTO)
        self.assertEqual(guardado.exploradas, list(logica.mapaConocido.exploradas))
        self.assertEqual(guardado.avistadas, sorted_manual(guardado.avistadas))
        for p in guardado.puertas:
            self.assertIsInstance(p, PuertaRecordadaDTO)
            self.assertIn(p.direccion, (0, 1, 2, 3))
        claves = [p.sala * 4 + p.direccion for p in guardado.puertas]
        self.assertEqual(claves, sorted_manual(claves))


def sorted_manual(lista):
    """Comprobación de orden ascendente sin sorted(): devuelve la lista si ya está ordenada y [] si no."""
    for i in range(1, len(lista)):
        if lista[i - 1] > lista[i]:
            return []
    return list(lista)


class TestValidacion(unittest.TestCase):
    """V1 a V5 de contracts/estado-guardado-niebla.md §3: un conocimiento incoherente se rechaza SIN tocar la partida."""

    def intentar(self, modificar):
        logica = partida_con_niebla()
        estado = logica.exportar_estado()
        modificar(estado.conocimiento)
        otra = partida_con_niebla()
        antes = (otra.estadoJuego, foto(otra), otra.mapaConocido)
        with self.assertRaises(ValueError) as contexto:
            otra.restaurar_estado(estado)
        self.assertIn("conocimiento inválido", str(contexto.exception))
        self.assertIs(otra.estadoJuego, antes[0])                              # la partida actual no se tocó
        self.assertIs(otra.mapaConocido, antes[2])
        self.assertEqual(foto(otra), antes[1])

    def test_FR220_V1_un_id_fuera_del_esqueleto_se_rechaza(self):
        self.intentar(lambda k: k.avistadas.append(999))

    def test_FR220_V2_exploradas_repetidas_se_rechazan(self):
        self.intentar(lambda k: k.exploradas.append(k.exploradas[0]))

    def test_FR220_V2_una_sala_en_exploradas_y_avistadas_se_rechaza(self):
        self.intentar(lambda k: k.avistadas.append(k.exploradas[0]))

    def test_FR220_V3_avistadas_incoherentes_con_las_exploradas_se_rechazan(self):
        self.intentar(lambda k: k.avistadas.remove(k.avistadas[0]))

    def test_FR220_V4_la_sala_del_jugador_debe_estar_explorada(self):
        logica = partida_con_niebla()
        estado = logica.exportar_estado()
        estado.jugador.id_sala_actual = 4                                      # avistada, no explorada: lo demás es coherente
        otra = partida_con_niebla()
        actual = otra.estadoJuego
        with self.assertRaises(ValueError) as contexto:
            otra.restaurar_estado(estado)
        self.assertIn("la sala del jugador no está explorada", str(contexto.exception))
        self.assertIs(otra.estadoJuego, actual)

    def test_FR220_V5_una_puerta_de_una_salida_que_no_existe_se_rechaza(self):
        self.intentar(lambda k: k.puertas.append(PuertaRecordadaDTO(4, 0, True)))     # la sala 4 no tiene salida al norte

    def test_FR220_V5_una_puerta_repetida_se_rechaza(self):
        self.intentar(lambda k: k.puertas.append(copy.copy(k.puertas[0])))

    def test_FR220_un_estado_sin_conocimiento_se_rechaza(self):
        logica = partida_con_niebla()
        estado = logica.exportar_estado()
        estado.conocimiento = None
        with self.assertRaises(ValueError) as contexto:
            partida_con_niebla().restaurar_estado(estado)
        self.assertIn("conocimiento", str(contexto.exception))


class TestVersiones(unittest.TestCase):
    def test_FR221_la_numeracion_acordada_por_el_grupo(self):
        self.assertEqual(modulo_partida.VERSION_FORMATO, 7)
        self.assertEqual(modulo_estado.VERSION_ESTADO, 4)

    def test_FR221_un_archivo_de_la_001_se_rechaza_con_la_version_encontrada_y_la_esperada(self):
        logica = nueva_partida(cripta())
        carpeta = tempfile.mkdtemp()
        archivo = os.path.join(carpeta, "partida.bin")
        AlmacenPartidaBinario(archivo).guardar(logica.exportar_estado())
        with open(archivo, "r+b") as f:                                       # lo que habría escrito la 001: formato 6
            f.write(modulo_partida._ENCABEZADO.pack(modulo_partida.MAGIA, 6))
        with self.assertRaises(ErrorPartida) as contexto:
            AlmacenPartidaBinario(archivo).cargar()
        mensaje = str(contexto.exception)
        self.assertIn("6", mensaje)
        self.assertIn("7", mensaje)

    def test_FR221_un_estado_de_la_version_anterior_se_rechaza_con_la_version_encontrada_y_la_esperada(self):
        estado = nueva_partida(cripta()).exportar_estado()
        estado.version_estado = 3
        with self.assertRaises(ValueError) as contexto:
            nueva_partida(cripta()).restaurar_estado(estado)
        mensaje = str(contexto.exception)
        self.assertIn("3", mensaje)
        self.assertIn("4", mensaje)


if __name__ == "__main__":
    unittest.main()
