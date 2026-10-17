def insertion_sort(lista, key= lambda x:x):
    """Ordenamiento de insertion para listas pequeñas o casi ordenadas """
    for i in range(1,len(lista)):
        clave = lista[i]
        j = i-1
        # se compara usando la función 'key' (por ejemplo, para ordenar por valor, peso o nombre)
        while j >= 0 and key(lista[j]) > key(clave):
            lista[j+1] = lista[j]
            j-= 1

        lista[j+1] = clave
    return lista

    

def merge_sort(lista, key = lambda x:x):
    """Ordenamiento por merge para listas grandes y que sean aleatorias"""
    if len(lista) <= 1:
        return lista
    medio = len(lista) // 2
    izquierda = merge_sort(lista[:medio], key)
    derecha = merge_sort(lista[medio:], key)

    return _mezclar(izquierda, derecha, key)

def _mezclar(izquierda, derecha, key):
    resultado = []
    i = j = 0
    while i < len(izquierda) and j < len(derecha):
        if key(izquierda[i])<= key(derecha[j]):
            resultado.append(izquierda[i])
            i += 1
        else:
            resultado.append(derecha[j])
            j += 1

    resultado.extend(izquierda[i:])
    resultado.extend(derecha[j:])
    return resultado

FACTOR_PRESUPUESTO = 4        # la inserción se rinde si necesita más de FACTOR_PRESUPUESTO * n desplazamientos
LIMITE_PRUEBA_DE_ORDEN = 64   # solo se prueba la inserción en listas de hasta este tamaño (medido con --bench)


def _insercion_con_presupuesto(lista, key, maximo):
    """Inserción estable que cuenta los desplazamientos. Si pasan de `maximo` (los datos NO estaban casi
    ordenados) se rinde y devuelve None sin haber tocado `lista`; si no, devuelve la lista ordenada."""
    trabajo = list(lista)
    desplazamientos = 0
    for i in range(1, len(trabajo)):
        clave = trabajo[i]
        valor = key(clave)
        j = i - 1
        while j >= 0 and key(trabajo[j]) > valor:
            trabajo[j + 1] = trabajo[j]
            j -= 1
            desplazamientos += 1
            if desplazamientos > maximo:
                return None
        trabajo[j + 1] = clave
    return trabajo


def ordenar_adaptativo(lista, key = lambda x:x):
    """Elige el algoritmo según propiedades medibles de los datos (§4.9):
        - tamaño: con 15 elementos o menos usa inserción;
        - orden previo: hasta LIMITE_PRUEBA_DE_ORDEN elementos prueba la inserción con un presupuesto de
          FACTOR_PRESUPUESTO * n desplazamientos. Si los datos estaban casi ordenados termina dentro del
          presupuesto; si no, se rinde y usa mezcla (lo gastado es de microsegundos y el resultado es el mismo:
          ambas son estables). Más allá de ese tamaño la mezcla ya gana incluso con datos casi ordenados
          (medido con --bench), así que va directo a ella."""

    # Convertimos a lista por si entra un deque o iterable
    lista_trabajo = list(lista)

    if len(lista_trabajo) <= 15:
        return insertion_sort(lista_trabajo, key)

    if len(lista_trabajo) <= LIMITE_PRUEBA_DE_ORDEN:
        resultado = _insercion_con_presupuesto(lista_trabajo, key, FACTOR_PRESUPUESTO * len(lista_trabajo))
        if resultado is not None:
            return resultado
    return merge_sort(lista_trabajo, key)
