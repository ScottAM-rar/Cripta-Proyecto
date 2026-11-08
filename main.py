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
        raise argparse.ArgumentTypeError("el tamaÃ±o de la cachÃ© debe ser al menos 1")
    return valor


def _intervalo_checkpoint(texto: str) -> int:
    try:
        valor = int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{texto!r} no es un número entero")
    if valor < 1:
        raise argparse.ArgumentTypeError("el intervalo entre puntos de control debe ser un entero mayor o igual que 1")
    return valor


def _instante_hasta(texto: str) -> int:
    try:
        valor = int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{texto!r} no es un número entero")
    if valor < 0:
        raise argparse.ArgumentTypeError("el instante virtual debe ser mayor o igual que 0")
    return valor


def leer_argumentos(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="main.py", description="Cripta: juego de mazmorra dirigido por eventos.")
    parser.add_argument("--offline", action="store_true",
                        help="juega solo con los datos guardados en disco, sin conectarse a la red")
    parser.add_argument("--cache-size", type=_tamano_de_cache, default=TAMANO_CACHE, metavar="N",
                        help=f"cantidad de fichas del catÃ¡logo que se mantienen en memoria (por defecto {TAMANO_CACHE})")
    parser.add_argument("--bench", nargs="?", const="todo", metavar="BLOQUES",
                        help="mide el rendimiento con cargas sintÃ©ticas, sin red ni vista (todos los bloques, o una lista "
                             "separada por comas: agenda, cache, inventario, retroceso, ordenamiento, guardado, bitacora, ciclo, terreno, recorrido, replay)")
    parser.add_argument("--bench-csv", metavar="ARCHIVO.csv", help="con --bench, guarda ademÃ¡s los resultados en un CSV")
    parser.add_argument("--replay", metavar="PARTIDA.log",
                        help=f"reproduce una partida grabada, sin pedir nada al usuario (el log debe estar en {CARPETA_LOGS}/)")
    parser.add_argument("--hasta", type=_instante_hasta, metavar="T",
                        help="instante del reloj virtual en el que se detiene la reproducciÃ³n acotada")
    parser.add_argument("--checkpoint-cada", type=_intervalo_checkpoint, metavar="K",
                        help="intervalo de acciones del jugador entre puntos de control (entero >= 1)")
    return parser.parse_args(argv)


def reproducir(servicio: EstadoJuegoServicio, archivo: str, hasta: int | None = None) -> int:
    """--replay: reproduce el log completo o acotado hasta t sin vista ni interacciÃ³n."""
    carpeta, nombre = os.path.split(archivo)
    if carpeta and os.path.abspath(carpeta) != os.path.abspath(CARPETA_LOGS):
        print(f"El log debe estar en la carpeta {CARPETA_LOGS}/ (se indicÃ³ {archivo!r}).", file=sys.stderr)
        return 1

    if hasta is None:
        resultados = servicio.repetirPartida(nombre)
        print(f"\nReproducciÃ³n terminada: {len(resultados)} acciones del jugador.")
        terminado, motivo = servicio.terminado()
        print(f"Estado final: {motivo}" if terminado else "La partida no habÃ­a terminado al acabarse el log.")
        return 0

    dto = servicio.repetirPartida(nombre, hasta=hasta)

    if dto.log_agotado:
        print(f"Aviso: el log terminÃ³ en el instante {dto.instante_alcanzado} antes de alcanzar t={dto.instante_pedido}.\n")

    lista_efectos = ", ".join(dto.efectos_activos) if dto.efectos_activos else "(ninguno)"
    lista_llaves = ", ".join(dto.inventario_llaves) if dto.inventario_llaves else "(ninguna)"
    lista_objetos = ", ".join(dto.inventario_objetos) if dto.inventario_objetos else "(ninguno)"

    if dto.enemigos_sala:
        lineas_enemigos = "\n".join(f"  - {nom} ({i_id}): {vida} PV" for i_id, nom, vida in dto.enemigos_sala)
    else:
        lineas_enemigos = "  (ninguno)"

    print(f"ReproducciÃ³n hasta t={dto.instante_pedido} terminada.")
    print(f"Instante virtual alcanzado: {dto.instante_alcanzado}")
    print(f"Acciones del jugador reproducidas: {dto.acciones_reproducidas}")
    print("Estado del jugador:")
    print(f"  Sala actual: {dto.id_sala_jugador}")
    print(f"  Puntos de vida: {dto.vida_jugador}")
    print(f"  EstadÃ­sticas: ataque {dto.ataque_jugador}, defensa {dto.defensa_jugador}, velocidad {dto.velocidad_jugador}")
    print(f"  Efectos activos: {lista_efectos}")
    print(f"  Llaves: {lista_llaves}")
    print(f"  Objetos: {lista_objetos}")
    print("Enemigos en la sala:")
    print(lineas_enemigos)

    if dto.log_agotado:
        print("Estado de la partida: En curso (el log no contenÃ­a mÃ¡s acciones).")
    elif dto.partida_terminada:
        if dto.instante_alcanzado < dto.instante_pedido:
            print(f"Estado de la partida: Terminada antes de alcanzar t={dto.instante_pedido}.")
        else:
            print(f"Estado de la partida: Terminada en t={dto.instante_pedido}.")
        print(f"  Motivo: {dto.motivo_terminacion}")
    else:
        print("Estado de la partida: En curso (no ha terminado).")

    return 0


def mostrar_reporte(servicio: EstadoJuegoServicio) -> None:
    """Â§5.1: al terminar se informan solicitudes, presupuesto y aciertos/fallos de cachÃ©.
    Solo lee contadores (no hace solicitudes) y nunca debe tapar cÃ³mo terminÃ³ la partida."""
    try:
        reporte = servicio.reporteSolicitudes()
    except Exception as error:
        print(f"No se pudo generar el reporte de solicitudes: {error}", file=sys.stderr)
        return
    if reporte is not None:                      # None = nunca se llegÃ³ a elegir una cripta
        print("\n--- Reporte de solicitudes ---")
        print(reporte.texto())
UMBRAL_GC = (50_000, 20, 100)

def ajustar_recolector_de_basura() -> None:
    gc.set_threshold(*UMBRAL_GC)

def main(argv=None) -> int:
    args = leer_argumentos(argv)
    if args.hasta is not None and not args.replay:
        print("Error: el argumento --hasta requiere especificar una partida con --replay.", file=sys.stderr)
        return 2
    ajustar_recolector_de_basura()           # vale para el juego, --replay y --bench
    if args.bench is not None:               # --bench no usa la red ni crea la vista interactiva
        from bench import ejecutar as ejecutar_bench
        bloques = None if args.bench == "todo" else [b.strip() for b in args.bench.split(",") if b.strip()]
        return ejecutar_bench(bloques, args.bench_csv)
    servicio = None
    try:
        # El servicio de cripta se arma UNA vez aquÃ­ (un solo cliente de red y un solo UUID por ejecuciÃ³n)
        # y se entrega al juego; --offline y --cache-size se aplican en este punto.
        comunicacion = crear_servicio(offline=args.offline, cache_size=args.cache_size)
        servicio = EstadoJuegoServicio(comunicacion=comunicacion, offline=args.offline, k_checkpoint=args.checkpoint_cada)
        if args.replay:
            return reproducir(servicio, args.replay, hasta=args.hasta)     # no se crea la vista
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
        if servicio is not None:                 # tambiÃ©n si la partida terminÃ³ por un error o con Ctrl+C
            mostrar_reporte(servicio)


if __name__ == "__main__":
    sys.exit(main())
