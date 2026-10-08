from adaptadores.cache import CacheLRU

cache = CacheLRU(capacidad=3)
cache.insertar("itm_antorcha", "ficha_antorcha")
cache.insertar("itm_daga_oxidada", "ficha_daga")
cache.insertar("itm_llave_bronce", "ficha_llave")

cache.obtener("itm_antorcha")  # la usamos: pasa al frente, ya no es la menos usada

cache.insertar("itm_coraza_cuero", "ficha_coraza")  # el cache está lleno: debe desalojar algo

print([entrada[0] for entrada in cache._entradas])