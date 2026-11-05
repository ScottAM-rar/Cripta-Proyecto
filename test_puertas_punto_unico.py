"""Toda escritura de una puerta pasa por Logica/PuertasLogica.fijar_cerrada: si no, el campo de costos reutilizado
podría quedar viejo sin enterarse (principio III, FR-116)."""
import os
import re
import unittest

ESCRITURA = re.compile(r"\.cerrada\s*=(?!=)|setattr\([^)]*['\"]cerrada['\"]")
PERMITIDO = os.path.join("Logica", "PuertasLogica.py")


def archivos_de_produccion():
    for carpeta in ("Logica", "adaptadores", "Servicio", "Controlador", "DTO"):
        for raiz, _, nombres in os.walk(carpeta):
            for nombre in nombres:
                if nombre.endswith(".py"):
                    yield os.path.join(raiz, nombre)


class TestPuntoUnicoDeCambioDePuertas(unittest.TestCase):
    def test_FR116_ninguna_otra_parte_escribe_el_estado_de_una_puerta(self):
        infractores = []
        for ruta in archivos_de_produccion():
            if ruta == PERMITIDO:
                continue
            with open(ruta, encoding="utf-8") as f:
                for numero, linea in enumerate(f, 1):
                    if ESCRITURA.search(linea.split("#")[0]):
                        infractores.append(f"{ruta}:{numero}: {linea.strip()}")
        self.assertEqual(infractores, [], "Escrituras de .cerrada fuera de PuertasLogica.fijar_cerrada")

    def test_FR116_la_funcion_unica_existe_y_avisa_solo_si_hubo_cambio(self):
        from DTO.SalaDTO import SalidaDTO
        from Logica.PuertasLogica import fijar_cerrada
        avisos = []
        salida = SalidaDTO("este", 2, False)
        self.assertTrue(fijar_cerrada(salida, True, avisos.append))
        self.assertTrue(salida.cerrada)
        self.assertFalse(fijar_cerrada(salida, True, avisos.append))     # ya estaba cerrada: nada que avisar
        self.assertEqual(avisos, [salida])


if __name__ == "__main__":
    unittest.main()
