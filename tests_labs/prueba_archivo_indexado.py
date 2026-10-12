"""Pruebas de ArchivoIndexado. Corren sin internet y sin gastar solicitudes.
 
Ejecutar desde la raíz del proyecto:
    py -m tests_labs.prueba_archivo_indexado
"""
import os
import tempfile
 
from adaptadores.Archivo_indexado import ArchivoIndexado, ErrorArchivo, MAGIA
 
resultados = []
 
 
def comprobar(nombre, condicion):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre}")
    resultados.append(condicion)
 
 
def lanza_error_archivo(funcion):
    try:
        funcion()
    except ErrorArchivo:
        return True
    return False
 
 
with tempfile.TemporaryDirectory() as carpeta:
    ruta = os.path.join(carpeta, "prueba.bin")
    a = ArchivoIndexado(ruta)
 
    print("== Archivo que todavía no existe ==")
    comprobar("existe() es False", not a.existe())
    comprobar("claves() devuelve lista vacía", a.claves() == [])
    comprobar("leer() devuelve None", a.leer("x") is None)
 
    print("== Escribir y leer ==")
    ficha = {"id": "ent_guardian_oseo", "comportamiento": "guardián", "vida_max": 20,
             "suelta": ["itm_llave_negra"]}
    a.escribir("ent_guardian_oseo", ficha)
    comprobar("el archivo se crea", a.existe())
    comprobar("lee lo mismo que guardó", a.leer("ent_guardian_oseo") == ficha)
    comprobar("conserva la tilde de 'guardián'",
              a.leer("ent_guardian_oseo")["comportamiento"] == "guardián")
    comprobar("clave inexistente devuelve None", a.leer("no_existe") is None)
    comprobar("contiene() sí / no", a.contiene("ent_guardian_oseo") and not a.contiene("zzz"))
 
    print("== Varias claves y reemplazos ==")
    a.escribir("version", "abc123")
    a.escribir("itm_daga", {"id": "itm_daga", "peso": 2})
    comprobar("claves en el orden en que se escribieron",
              a.claves() == ["ent_guardian_oseo", "version", "itm_daga"])
    a.escribir("version", "def456")
    comprobar("reemplazar no duplica la clave", a.claves().count("version") == 1)
    comprobar("reemplazar cambia el valor", a.leer("version") == "def456")
    comprobar("reemplazar no daña las demás",
              a.leer("itm_daga") == {"id": "itm_daga", "peso": 2} and a.leer("ent_guardian_oseo") == ficha)
    a.escribir_varios([("a", 1), ("b", [1, 2, 3]), ("version", "z")])
    comprobar("escribir_varios guarda todo",
              a.leer("a") == 1 and a.leer("b") == [1, 2, 3] and a.leer("version") == "z")
 
    print("== Persistencia ==")
    otro = ArchivoIndexado(ruta)
    comprobar("una instancia nueva lee lo que escribió la anterior",
              otro.leer("itm_daga") == {"id": "itm_daga", "peso": 2})
 
    print("== Formato binario ==")
    with open(ruta, "rb") as f:
        comprobar("empieza con la marca CRPT", f.read(4) == MAGIA)
    comprobar("no queda archivo temporal", not os.path.exists(ruta + ".tmp"))
 
    print("== Muchos registros ==")
    grande = ArchivoIndexado(os.path.join(carpeta, "grande.bin"))
    grande.escribir_varios([(f"clave-{i}", {"n": i, "texto": "ñandú " * 5}) for i in range(300)])
    comprobar("300 registros: primero, medio y último",
              grande.leer("clave-0")["n"] == 0 and grande.leer("clave-150")["n"] == 150
              and grande.leer("clave-299")["n"] == 299)
    comprobar("300 claves", len(grande.claves()) == 300)
 
    print("== Archivos dañados ==")
    basura = os.path.join(carpeta, "basura.bin")
    with open(basura, "wb") as f:
        f.write(b"esto no es un archivo de Cripta, solo texto cualquiera")
    comprobar("marca incorrecta -> ErrorArchivo", lanza_error_archivo(lambda: ArchivoIndexado(basura).claves()))
 
    corto = os.path.join(carpeta, "corto.bin")
    with open(corto, "wb") as f:
        f.write(b"CR")
    comprobar("archivo demasiado corto -> ErrorArchivo", lanza_error_archivo(lambda: ArchivoIndexado(corto).leer("x")))
 
    with open(ruta, "rb") as f:
        contenido = f.read()
    cortado = os.path.join(carpeta, "cortado.bin")
    with open(cortado, "wb") as f:
        f.write(contenido[:-5])            # se pierde un pedazo del pie
    comprobar("pie cortado -> ErrorArchivo", lanza_error_archivo(lambda: ArchivoIndexado(cortado).claves()))
 
    comprobar("escribir sobre un archivo dañado no lo pisa en silencio",
              lanza_error_archivo(lambda: ArchivoIndexado(basura).escribir("a", 1)))
 
    print("== Vaciar ==")
    a.vaciar()
    comprobar("vaciar borra el archivo", not a.existe() and a.claves() == [])
 
print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")