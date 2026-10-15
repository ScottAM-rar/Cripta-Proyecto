import unittest
from io import StringIO
from contextlib import redirect_stdout

from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.BitacoraLogica import BitacoraLogica


class TestBitacoraLogica(unittest.TestCase):
    def test_guarda_resultados_en_orden_fifo(self):
        bitacora = BitacoraLogica()
        resultados = [ResultadoEventoDTO(True, f"Mensaje {i}") for i in range(3)]

        for resultado in resultados:
            bitacora.agregar_evento(resultado)

        self.assertEqual(bitacora.obtener_eventos(), resultados)

    def test_conserva_los_20_resultados_mas_recientes(self):
        bitacora = BitacoraLogica()
        resultados = [ResultadoEventoDTO(True, f"Mensaje {i}") for i in range(21)]

        for resultado in resultados:
            bitacora.agregar_evento(resultado)

        self.assertEqual(bitacora.contador, 20)
        self.assertEqual(bitacora.obtener_eventos(), resultados[1:])

    def test_imprimir_mensajes_va_de_mas_antiguo_a_mas_nuevo(self):
        bitacora = BitacoraLogica()
        bitacora.agregar_evento(ResultadoEventoDTO(True, "Primero"))
        bitacora.agregar_evento(ResultadoEventoDTO(False, "Segundo"))

        salida = StringIO()
        with redirect_stdout(salida):
            bitacora.imprimir_mensajes()

        self.assertEqual(salida.getvalue(), "Primero\nSegundo\n")

    def test_rechaza_valores_que_no_sean_resultados(self):
        with self.assertRaises(TypeError):
            BitacoraLogica().agregar_evento("resultado")


if __name__ == "__main__":
    unittest.main(verbosity=2)