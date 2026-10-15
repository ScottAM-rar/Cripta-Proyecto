import os
import pickle
import sys

from adaptadores.extension import ruta_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS


class PersistenciaPartida:
    FORMATO = "CRIPTA_PARTIDA"
    VERSION = 1
    LIMITE_RECURSION = 20000

    @staticmethod
    def guardar(nombre_archivo: str, estado_juego_logica) -> None:
        nombre_archivo = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS, crear_carpeta=True)

        paquete = {
            "formato": PersistenciaPartida.FORMATO,
            "version": PersistenciaPartida.VERSION,
            "estado": estado_juego_logica,
        }
        temporal = nombre_archivo + ".tmp"
        limite = sys.getrecursionlimit()
        sys.setrecursionlimit(max(limite, PersistenciaPartida.LIMITE_RECURSION))
        try:
            with open(temporal, "wb") as archivo:
                pickle.dump(paquete, archivo, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(temporal, nombre_archivo)
        except (pickle.PicklingError, TypeError, AttributeError) as error:
            PersistenciaPartida._borrar_temporal(temporal)
            raise ValueError(f"No se pudo serializar la partida: {error}") from error
        except OSError as error:
            PersistenciaPartida._borrar_temporal(temporal)
            raise ValueError(f"No se pudo escribir el archivo de partida: {error}") from error
        finally:
            sys.setrecursionlimit(limite)

    @staticmethod
    def cargar(nombre_archivo: str):
        nombre_archivo = ruta_archivo(nombre_archivo, EXTENSION_PARTIDA, CARPETA_PARTIDAS)
        if not os.path.isfile(nombre_archivo):
            raise ValueError(f"No existe el archivo de partida {nombre_archivo!r}")

        limite = sys.getrecursionlimit()
        sys.setrecursionlimit(max(limite, PersistenciaPartida.LIMITE_RECURSION))
        try:
            with open(nombre_archivo, "rb") as archivo:
                paquete = pickle.load(archivo)
        except (pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError, ValueError) as error:
            raise ValueError(f"El archivo de partida está dañado o no es válido: {error}") from error
        except OSError as error:
            raise ValueError(f"No se pudo leer el archivo de partida: {error}") from error
        finally:
            sys.setrecursionlimit(limite)

        if not isinstance(paquete, dict) or paquete.get("formato") != PersistenciaPartida.FORMATO:
            raise ValueError("El archivo no es una partida guardada de Cripta")
        if paquete.get("version") != PersistenciaPartida.VERSION:
            raise ValueError(
                f"Versión de partida no soportada: {paquete.get('version')!r} "
                f"(se esperaba {PersistenciaPartida.VERSION})"
            )
        return paquete["estado"]

    @staticmethod
    def _borrar_temporal(temporal: str) -> None:
        try:
            if os.path.exists(temporal):
                os.remove(temporal)
        except OSError:
            pass
