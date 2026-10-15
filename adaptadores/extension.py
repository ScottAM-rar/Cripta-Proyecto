import os

EXTENSION_PARTIDA = ".bin"
EXTENSION_LOG = ".log"
CARPETA_PARTIDAS = "Partidas Guardadas"
CARPETA_LOGS = "logs"


def con_extension(nombre_archivo: str, extension: str = EXTENSION_PARTIDA) -> str:
    if not isinstance(nombre_archivo, str) or not nombre_archivo.strip():
        raise ValueError("El nombre del archivo no es válido")
    nombre = nombre_archivo.strip()
    if nombre.lower().endswith(extension):
        return nombre[: -len(extension)] + extension
    return nombre + extension


def ruta_archivo(nombre_archivo: str, extension: str, carpeta: str, crear_carpeta: bool = False) -> str:
    nombre = con_extension(nombre_archivo, extension)
    separadores = {os.sep, "/", "\\"}
    if os.altsep:
        separadores.add(os.altsep)
    if any(s in nombre for s in separadores) or nombre in (extension, ".", ".."):
        raise ValueError("El nombre del archivo no debe incluir carpetas")
    if crear_carpeta:
        os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, nombre)
