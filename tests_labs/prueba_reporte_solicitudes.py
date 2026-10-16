"""Pruebas del reporte de solicitudes (§5.1): se imprime al terminar la partida y al terminar --replay,
cuenta las solicitudes reales, no cuesta ninguna y baja con la caché en disco. Sin internet.

    py -m tests_labs.prueba_reporte_solicitudes
"""
import builtins
import contextlib
import io
import os
import tempfile

import main as programa
from adaptadores import fabrica
from DTO.EventoDTO import EventoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from tests_labs.api_falsa import HttpFalso

resultados = []


def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)


def ejecutar(argv, teclas, carpeta, http):
    """Corre main() como si fuera una ejecución nueva: cliente falso nuevo y servicio nuevo.
    Devuelve (código de salida, lo que se imprimió)."""
    fabrica.reiniciar_cliente_compartido()
    original_servicio, original_input = programa.crear_servicio, builtins.input
    pendientes = list(teclas)

    def servicio_de_prueba(offline=False, cache_size=fabrica.TAMANO_CACHE):
        return fabrica.crear_servicio(offline=offline, cache_size=cache_size, carpeta=carpeta, cliente_http=http)

    programa.crear_servicio = servicio_de_prueba
    builtins.input = lambda *_: pendientes.pop(0)
    salida = io.StringIO()
    try:
        with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(salida):
            codigo = programa.main(argv)
    finally:
        programa.crear_servicio, builtins.input = original_servicio, original_input
        fabrica.reiniciar_cliente_compartido()
    return codigo, salida.getvalue()


def servicio_para(carpeta, http):
    fabrica.reiniciar_cliente_compartido()
    comunicacion = fabrica.crear_servicio(carpeta=carpeta, cliente_http=http)
    return EstadoJuegoServicio(comunicacion=comunicacion)


with tempfile.TemporaryDirectory() as raiz:
    datos = os.path.join(raiz, "datos")
    anterior = os.getcwd()
    os.chdir(raiz)                 # los logs se guardan en ./logs y las partidas en ./Partidas Guardadas
    try:
        print("== 1) Partida completa por main: el reporte sale al final ==")
        http1 = HttpFalso()
        # no cargar partida, cripta 1, semilla 7, ir al norte, salir sin guardar
        codigo, texto = ejecutar([], ["n", "1", "7", "norte", "salir", "n"], datos, http1)
        comprobar("termina bien", codigo == 0)
        comprobar("imprime el encabezado del reporte", "--- Reporte de solicitudes ---" in texto)
        comprobar("el reporte va DESPUÉS de despedirse",
                  texto.rfind("Saliendo del juego") < texto.rfind("--- Reporte de solicitudes ---"))
        esperado = f"Solicitudes a la API: {http1.solicitudes_realizadas} de 9"
        comprobar("las solicitudes del reporte son las que hizo el cliente de red", esperado in texto, f"-> {esperado!r}")
        comprobar("informa aciertos y fallos de la caché", "aciertos" in texto and "fallos" in texto)
        primera_vez = http1.solicitudes_realizadas

        print("== 2) Consultar el reporte no cuesta solicitudes ==")
        http2 = HttpFalso()
        servicio = servicio_para(os.path.join(raiz, "datos2"), http2)
        comprobar("antes de elegir cripta no hay reporte", servicio.reporteSolicitudes() is None)
        servicio.iniciarJuego(servicio.obtenerIdCripta(1), 7)
        antes = http2.solicitudes_realizadas
        for _ in range(3):
            informe = servicio.reporteSolicitudes()
        comprobar("pedirlo 3 veces no suma solicitudes", http2.solicitudes_realizadas == antes, f"({antes})")
        comprobar("trae el presupuesto de la cripta (9)", informe.presupuesto == 9)
        servicio.accionJugador(EventoDTO(100, 0, servicio.getJudador(), "MOVER_JUGADOR",
                                         [servicio.obtenerSala(1), "norte"]))
        comprobar("tras jugar sigue coincidiendo con el cliente",
                  servicio.reporteSolicitudes().solicitudes == http2.solicitudes_realizadas)

        print("== 3) --replay también muestra el reporte (y no pide nada al usuario) ==")
        nombre_log = servicio.nombreLog()       # el log se va grabando solo, no hay que guardarlo
        http3 = HttpFalso()
        codigo, texto = ejecutar(["--replay", nombre_log], [], os.path.join(raiz, "datos2"), http3)
        comprobar("la reproducción termina bien", codigo == 0, f"(código {codigo})")
        comprobar("el reporte sale al final de la reproducción",
                  texto.rfind("Reproducción terminada") < texto.rfind("--- Reporte de solicitudes ---"))
        comprobar("con la caché en disco ya caliente hace menos solicitudes que la primera vez",
                  http3.solicitudes_realizadas < http2.solicitudes_realizadas,
                  f"({http3.solicitudes_realizadas} contra {http2.solicitudes_realizadas})")

        print("== 4) --offline: lecturas del disco no cuentan ==")
        http4 = HttpFalso()
        codigo, texto = ejecutar(["--offline", "--replay", nombre_log], [], os.path.join(raiz, "datos2"), http4)
        comprobar("la reproducción offline termina bien", codigo == 0, f"(código {codigo})")
        comprobar("el reporte dice 0 solicitudes de 9", "Solicitudes a la API: 0 de 9" in texto)
        comprobar("y de verdad no tocó la red", http4.solicitudes_realizadas == 0)

        print("== 5) Si nunca se llegó a elegir cripta, no se inventa un reporte ==")
        codigo, texto = ejecutar(["--replay", "noexiste.log"], [], datos, HttpFalso())
        comprobar("falla con código 1", codigo == 1)
        comprobar("no imprime reporte", "Reporte de solicitudes" not in texto)
    finally:
        os.chdir(anterior)

print()
print(f"{sum(resultados)} de {len(resultados)} comprobaciones correctas")
raise SystemExit(0 if all(resultados) else 1)
