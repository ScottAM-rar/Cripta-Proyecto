import argparse
import os
import sys
import gc

from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Controlador.ControladorJuego import ControladorJuego
from adaptadores.extension import CARPETA_LOGS
from adaptadores.fabrica import crear_servicio, TAMANO_CACHE


def _tamano_de_cache(texto: str) -> int:
    try:
        valor = int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{texto!r} no es un número entero")
    if valor < 1:
        raise argparse.ArgumentTypeError("el tamaño de la caché debe ser al menos 1")
    return valor


def leer_argumentos(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="main.py", description="Cripta: juego de mazmorra dirigido por eventos.")
    parser.add_argument("--offline", action="store_true",
                        help="juega solo con los datos guardados en disco, sin conectarse a la red")
    parser.add_argument("--cache-size", type=_tamano_de_cache, default=TAMANO_CACHE, metavar="N",
                        help=f"cantidad de fichas del catálogo que se mantienen en memoria (por defecto {TAMANO_CACHE})")
    parser.add_argument("--bench", nargs="?", const="todo", metavar="BLOQUES",
                        help="mide el rendimiento con cargas sintéticas, sin red ni vista (todos los bloques, o una lista "
                             "separada por comas: agenda, cache, inventario, retroceso, ordenamiento, guardado, bitacora, ciclo)")
    parser.add_argument("--bench-csv", metavar="ARCHIVO.csv", help="con --bench, guarda además los resultados en un CSV")
    parser.add_argument("--replay", metavar="PARTIDA.log",
                        help=f"reproduce una partida grabada, sin pedir nada al usuario (el log debe estar en {CARPETA_LOGS}/)")
    return parser.parse_args(argv)


def reproducir(servicio: EstadoJuegoServicio, archivo: str) -> int:
    """--replay: reproduce el log completo sin vista ni interacción."""
    carpeta, nombre = os.path.split(archivo)
    if carpeta and os.path.abspath(carpeta) != os.path.abspath(CARPETA_LOGS):
        print(f"El log debe estar en la carpeta {CARPETA_LOGS}/ (se indicó {archivo!r}).", file=sys.stderr)
        return 1
    resultados = servicio.repetirPartida(nombre)
    print(f"\nReproducción terminada: {len(resultados)} acciones del jugador.")
    terminado, motivo = servicio.terminado()
    print(f"Estado final: {motivo}" if terminado else "La partida no había terminado al acabarse el log.")
    return 0


def mostrar_reporte(servicio: EstadoJuegoServicio) -> None:
    """§5.1: al terminar se informan solicitudes, presupuesto y aciertos/fallos de caché.
    Solo lee contadores (no hace solicitudes) y nunca debe tapar cómo terminó la partida."""
    try:
        reporte = servicio.reporteSolicitudes()
    except Exception as error:
        print(f"No se pudo generar el reporte de solicitudes: {error}", file=sys.stderr)
        return
    if reporte is not None:                      # None = nunca se llegó a elegir una cripta
        print("\n--- Reporte de solicitudes ---")
        print(reporte.texto())
UMBRAL_GC = (50_000, 20, 100)

def ajustar_recolector_de_basura() -> None:
    gc.set_threshold(*UMBRAL_GC)

def main(argv=None) -> int:
    args = leer_argumentos(argv)

    ajustar_recolector_de_basura()           # vale para el juego, --replay y --bench
    if args.bench is not None:               # --bench no usa la red ni crea la vista interactiva
        from bench import ejecutar as ejecutar_bench
        bloques = None if args.bench == "todo" else [b.strip() for b in args.bench.split(",") if b.strip()]
        return ejecutar_bench(bloques, args.bench_csv)
  

    servicio = None
    try:
        # El servicio de cripta se arma UNA vez aquí (un solo cliente de red y un solo UUID por ejecución)
        # y se entrega al juego; --offline y --cache-size se aplican en este punto.
        comunicacion = crear_servicio(offline=args.offline, cache_size=args.cache_size)
        servicio = EstadoJuegoServicio(comunicacion=comunicacion, offline=args.offline)
        if args.replay:
            return reproducir(servicio, args.replay)     # no se crea la vista
        print("Inicializando Cripta...")
        ControladorJuego(servicio).iniciar()
        return 0
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        return 130
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if servicio is not None:                 # también si la partida terminó por un error o con Ctrl+C
            mostrar_reporte(servicio)


if __name__ == "__main__":
    sys.exit(main())
