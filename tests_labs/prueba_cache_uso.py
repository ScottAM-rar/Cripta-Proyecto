"""Pruebas de CacheLRU: desalojo, protección "en uso" y capacidad.

    py -m tests_labs.prueba_cache_uso
"""
from adaptadores.cache import CacheLRU

resultados = []


def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)


def lanza_valueerror(funcion):
    try:
        funcion()
    except ValueError:
        return True
    return False


print("== 1) Se desaloja la menos usada ==")
c = CacheLRU(3)
c.insertar("a", 1); c.insertar("b", 2); c.insertar("c", 3)
c.obtener("a")                       # 'a' pasa al frente; la menos usada ahora es 'b'
c.insertar("d", 4)
comprobar("se fue 'b'", c.claves() == ["d", "a", "c"], f"({c.claves()})")
comprobar("obtener devuelve el valor", c.obtener("a") == 1 and c.obtener("b") is None)

print("== 2) Una ficha en uso no se desaloja ==")
c = CacheLRU(2)
c.insertar("a", 1); c.insertar("b", 2)
c.marcar_en_uso("a")                 # 'a' es la menos reciente, pero está en uso
c.insertar("c", 3)
comprobar("se fue 'b' y se quedó 'a'", c.obtener("a") == 1 and c.obtener("b") is None and c.obtener("c") == 3)

print("== 3) Todo en uso: no se supera la capacidad ==")
c = CacheLRU(2)
c.insertar("a", 1); c.insertar("b", 2)
c.marcar_en_uso("a"); c.marcar_en_uso("b")
guardada = c.insertar("c", 3)
comprobar("insertar devuelve False", guardada is False)
comprobar("el tamaño sigue siendo 2", len(c) == 2 and len(c) <= c.capacidad)
comprobar("'c' no quedó guardada", c.obtener("c") is None)
c.marcar_libre("a")
comprobar("al liberar 'a' ya hay lugar", c.insertar("c", 3) is True and c.obtener("a") is None and c.obtener("c") == 3)
comprobar("'b' sigue protegida", c.obtener("b") == 2)

print("== 4) Contador de uso ==")
c = CacheLRU(2)
c.insertar("a", 1); c.insertar("b", 2)
c.marcar_libre("a")                  # liberar sin haber usado no debe dejarlo en negativo
c.marcar_en_uso("a")
c.insertar("c", 3); c.insertar("d", 4)
comprobar("'a' quedó protegida (no se desalojó)", c.obtener("a") == 1)
c = CacheLRU(2)
c.insertar("a", 1); c.insertar("b", 2)
c.marcar_en_uso("a"); c.marcar_en_uso("a"); c.marcar_libre("a")
c.insertar("c", 3)
comprobar("dos usos y una liberación: sigue en uso", c.obtener("a") == 1)

print("== 5) Otros ==")
c = CacheLRU(2)
c.insertar("a", 1); c.insertar("a", 9)
comprobar("reinsertar actualiza sin crecer", len(c) == 1 and c.obtener("a") == 9)
comprobar("marcar una clave inexistente no falla", c.marcar_en_uso("zzz") is None and c.marcar_libre("zzz") is None)
comprobar("capacidad 0 -> ValueError", lanza_valueerror(lambda: CacheLRU(0)))

print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")
