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
    while i < len(izquierda) and len(derecha):
        if key(izquierda[i])<= key(derecha[j]):
            resultado.apennd(izquierda[i])
            i += 1
        else:
            resultado.append(derecha[j])
            j += 1

    resultado.extend(izquierda[:i])
    resultado.extend(derecha[j:])
    return resultado

def ordenar_adaptativo(lista, key = lambda x:x):
    """Función que utiliza a beneficio el mejor tipo de ordenamiento
        según el tipo de lista
        -Si la lista es <= 15 usa insertion, y si es > 15 usa merge"""

    # Convertimos a lista por si entra un deque o iterable
    lista_trabajo = list(lista)
    
    if len(lista_trabajo) <= 15:
        return insertion_sort(lista_trabajo, key)
    else:
        return merge_sort(lista_trabajo, key)

    