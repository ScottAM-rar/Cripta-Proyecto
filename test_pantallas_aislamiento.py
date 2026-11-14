"""Capacidad 011, pantallas claras: la vista solo presenta (FR-312) y los archivos nuevos cumplen la constitución I y IV.
Cada prueba cita el requisito que demuestra."""
import contextlib
import io
import os
import re
import unittest
from unittest import mock

from Controlador import Pantallas
from Controlador.Vista import VistaConsola

RAIZ = os.path.dirname(os.path.abspath(__file__))
# Archivos nuevos o tocados por la 011 (se amplía cuando existen: bench/pantallas.py).
ARCHIVOS_011 = ("main.py", os.path.join("Controlador", "Pantallas.py"), os.path.join("Controlador", "Vista.py"),
                os.path.join("Controlador", "ControladorJuego.py"), os.path.join("bench", "pantallas.py"))
PROHIBIDO = re.compile(r"\b(dict|set)\(|sorted\(|\.sort\(|\bheapq\b|\bbisect\b|\bcollections\b|\bnetworkx\b|"
                       r"\bOrderedDict\b|\bdefaultdict\b|\bCounter\b|\{\s*\}")


def leer(ruta):
    with open(os.path.join(RAIZ, ruta), encoding="utf-8") as archivo:
        return archivo.read()


class TestPantallasNoConoceElModelo(unittest.TestCase):
    def test_FR312_pantallas_no_importa_servicio_logica_ni_adaptadores(self):
        """Principio IV: las funciones de pantalla solo reciben datos; no pueden leer el modelo."""
        fuente = leer(os.path.join("Controlador", "Pantallas.py"))
        for linea in fuente.splitlines():
            if linea.lstrip().startswith(("import ", "from ")):
                self.assertNotRegex(linea, r"\b(Servicio|Logica|adaptadores)\b", linea)

    def test_FR312_pantallas_no_imprime(self):
        """Las funciones de pantalla devuelven texto: no llaman a print ni a input."""
        fuente = leer(os.path.join("Controlador", "Pantallas.py"))
        self.assertNotRegex(fuente, r"\bprint\(")
        self.assertNotRegex(fuente, r"\binput\(")


class TestVistaSoloImprime(unittest.TestCase):
    def test_FR312_la_vista_imprime_exactamente_lo_que_devuelve_la_funcion_de_pantalla(self):
        salida = io.StringIO()
        with mock.patch("Controlador.Vista.texto_sala", return_value="PANTALLA FIJA"), \
                contextlib.redirect_stdout(salida):
            VistaConsola().mostrar_juego(object(), object(), object())
        self.assertEqual(salida.getvalue(), "PANTALLA FIJA\n")

    def test_FR312_el_resumen_de_fin_de_partida_se_imprime_tal_como_viene(self):
        salida = io.StringIO()
        with mock.patch("Controlador.Vista.texto_fin_partida", return_value="RESUMEN FIJO"), \
                contextlib.redirect_stdout(salida):
            VistaConsola().mostrar_fin_partida("m", 1, 2, 3, 4, 5, "c", "v", 6)
        self.assertEqual(salida.getvalue(), "RESUMEN FIJO\n")

    def test_FR312_la_ayuda_y_los_errores_se_imprimen_tal_como_vienen(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            VistaConsola().mostrar_ayuda("AYUDA FIJA")
            VistaConsola().mostrar_error("ERROR FIJO")
        self.assertEqual(salida.getvalue(), "AYUDA FIJA\nERROR FIJO\n")


class TestSinEstructurasProhibidas(unittest.TestCase):
    def test_FR316_los_archivos_de_la_011_no_usan_estructuras_prohibidas(self):
        """Constitución I: sin dict/set como índice, sin sorted()/list.sort() y sin heapq, bisect, collections ni networkx."""
        for ruta in ARCHIVOS_011:
            if not os.path.exists(os.path.join(RAIZ, ruta)):
                continue
            for numero, linea in enumerate(leer(ruta).splitlines(), start=1):
                codigo = linea.split("#", 1)[0]
                self.assertIsNone(PROHIBIDO.search(codigo), f"{ruta}:{numero}: {linea.strip()}")


if __name__ == "__main__":
    unittest.main()
