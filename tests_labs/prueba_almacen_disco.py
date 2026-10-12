"""Pruebas de AlmacenDisco. Sin internet y sin gastar solicitudes.
 
Ejecutar desde la raíz del proyecto:
    py -m tests_labs.prueba_almacen_disco
"""
import os
import tempfile
 
from adaptadores.AlmacenDisco import AlmacenDisco
 
resultados = []
 
 
def comprobar(nombre, condicion):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre}")
    resultados.append(condicion)
 
 
def lanza_valueerror(funcion):
    try:
        funcion()
    except ValueError:
        return True
    return False
 
 
FICHA_RATA = {"id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante",
              "vida_max": 12, "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]}
FICHA_GUARDIAN = {"id": "ent_guardian_oseo", "clase": "enemigo", "nombre": "Guardián óseo",
                  "vida_max": 20, "comportamiento": "guardián", "suelta": []}
CONTENIDO_2 = {"sala": 2, "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": None}],
               "objetos": ["itm_daga_oxidada"], "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]}
CONTENIDO_3 = {"sala": 3, "enemigos": [], "objetos": [], "trampas": []}
 
with tempfile.TemporaryDirectory() as raiz:
    carpeta = os.path.join(raiz, "datos_cripta")
    a = AlmacenDisco(carpeta)
 
    print("== Almacén vacío ==")
    comprobar("leer_criptas() es None", a.leer_criptas() is None)
    comprobar("version_catalogo() es None", a.version_catalogo() is None)
    comprobar("leer_ficha() es None", a.leer_ficha("ent_rata_gigante") is None)
    comprobar("leer_contenido() es None", a.leer_contenido("cripta-01", 2) is None)
    comprobar("cripta_completa() es False", not a.cripta_completa("cripta-01", [2, 3]))
 
    print("== Lista de criptas ==")
    criptas = [{"id": "cripta-01", "nombre": "Osario menor", "salas": 6, "dificultad": 1}]
    a.guardar_criptas(criptas)
    comprobar("se lee lo que se guardó", a.leer_criptas() == criptas)
 
    print("== Catálogo y versiones ==")
    comprobar("primera vez: validar_catalogo() es False (no había nada)", not a.validar_catalogo("v1"))
    a.guardar_fichas([FICHA_RATA, FICHA_GUARDIAN])
    comprobar("se lee una ficha", a.leer_ficha("ent_rata_gigante") == FICHA_RATA)
    comprobar("conserva la tilde", a.leer_ficha("ent_guardian_oseo")["comportamiento"] == "guardián")
    comprobar("ficha inexistente es None", a.leer_ficha("ent_fantasma") is None)
    comprobar("misma versión: validar_catalogo() es True", a.validar_catalogo("v1"))
    comprobar("con la misma versión las fichas siguen ahí", a.leer_ficha("ent_rata_gigante") == FICHA_RATA)
    comprobar("versión distinta: validar_catalogo() es False", not a.validar_catalogo("v2"))
    comprobar("con otra versión las fichas viejas desaparecen", a.leer_ficha("ent_rata_gigante") is None)
    comprobar("y la versión guardada es la nueva", a.version_catalogo() == "v2")
 
    print("== Cripta ==")
    comprobar("primera vez: validar_cripta() es False", not a.validar_cripta("cripta-01", "c1"))
    datos = {"id": "cripta-01", "salas_total": 6, "sala_inicial": 1,
             "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}
    salas = [{"id": 1, "nombre": "Entrada derruida", "salidas": {"N": {"sala": 2}}}]
    a.guardar_datos("cripta-01", datos)
    a.guardar_salas("cripta-01", salas)
    a.guardar_contenido("cripta-01", [2, 3], [CONTENIDO_2, CONTENIDO_3])
    comprobar("datos", a.leer_datos("cripta-01") == datos)
    comprobar("salas", a.leer_salas("cripta-01") == salas)
    comprobar("contenido de la sala 2", a.leer_contenido("cripta-01", 2) == CONTENIDO_2)
    comprobar("contenido de la sala 3", a.leer_contenido("cripta-01", 3) == CONTENIDO_3)
    comprobar("contenido de una sala que no se guardó es None", a.leer_contenido("cripta-01", 4) is None)
    comprobar("cripta_completa con las salas guardadas", a.cripta_completa("cripta-01", [2, 3]))
    comprobar("cripta_completa falla si falta una sala", not a.cripta_completa("cripta-01", [2, 3, 4]))
    comprobar("guardar_contenido con listas de distinto largo -> ValueError",
              lanza_valueerror(lambda: a.guardar_contenido("cripta-01", [2, 3], [CONTENIDO_2])))
 
    print("== Las criptas no se mezclan ==")
    a.validar_cripta("cripta-02", "x1")
    a.guardar_datos("cripta-02", {"id": "cripta-02"})
    comprobar("cada cripta tiene sus datos", a.leer_datos("cripta-02") == {"id": "cripta-02"}
              and a.leer_datos("cripta-01") == datos)
    comprobar("misma versión: validar_cripta() es True", a.validar_cripta("cripta-01", "c1"))
    comprobar("versión nueva en cripta-01: validar_cripta() es False", not a.validar_cripta("cripta-01", "c2"))
    comprobar("cripta-01 queda vacía", a.leer_datos("cripta-01") is None and a.leer_contenido("cripta-01", 2) is None)
    comprobar("cripta-02 no se toca", a.leer_datos("cripta-02") == {"id": "cripta-02"})
 
    print("== Persistencia entre ejecuciones ==")
    a.validar_catalogo("v2")
    a.guardar_fichas([FICHA_RATA])
    otro = AlmacenDisco(carpeta)       # como si se cerrara y volviera a abrir el programa
    comprobar("una instancia nueva ve la lista de criptas", otro.leer_criptas() == criptas)
    comprobar("una instancia nueva ve las fichas", otro.leer_ficha("ent_rata_gigante") == FICHA_RATA)
    comprobar("y la versión", otro.validar_catalogo("v2"))
 
    print("== Archivo dañado ==")
    with open(os.path.join(carpeta, "catalogo.bin"), "wb") as f:
        f.write(b"basura que no es un archivo de Cripta")
    comprobar("un catálogo dañado se descarta y empieza de nuevo", not otro.validar_catalogo("v2"))
    comprobar("después de descartarlo queda utilizable", otro.leer_ficha("ent_rata_gigante") is None
              and otro.validar_catalogo("v2"))
 
    print("== Ids peligrosos ==")
    comprobar("un id con '..' se rechaza", lanza_valueerror(lambda: a.leer_datos("../fuera")))
    comprobar("un id con '/' se rechaza", lanza_valueerror(lambda: a.guardar_datos("a/b", {})))
    comprobar("un id vacío se rechaza", lanza_valueerror(lambda: a.leer_salas("")))
 
print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")