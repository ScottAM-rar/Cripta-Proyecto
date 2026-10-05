from Controlador.ordenamiento import ordenar_adaptativo
from Logica.InventarioLogica import InventarioLogica

# Clase simulada de un objeto del juego para la prueba
class ObjetoInventarioMock:
    def __init__(self, nombre, valor, peso):
        self.nombre = nombre
        self.valor = valor
        self.peso = peso

    def __repr__(self):
        return f"{self.nombre} (Valor: {self.valor}, Peso: {self.peso})"

def probar_ordenamiento():
    print("=== PRUEBA DEL MODULO DE ORDENAMIENTO ===")
    
    # Creamos una lista desordenada de objetos
    inventario = [
        ObjetoInventarioMock("Poción de Vida", 50, 1.5),
        ObjetoInventarioMock("Espada Corta", 150, 5.0),
        ObjetoInventarioMock("Antorcha", 10, 2.0),
        ObjetoInventarioMock("Armadura de Cuero", 200, 12.0)
    ]

    print("\n1. Lista original:")
    for item in inventario:
        print(item)

    # Probando ordenar por valor monetario usando lambda
    print("\n2. Ordenado por VALOR (de menor a mayor):")
    ordenado_valor = ordenar_adaptativo(inventario, key=lambda x: x.valor)
    for item in ordenado_valor:
        print(item)

    # Probando ordenar por nombre alfabéticamente usando lambda
    print("\n3. Ordenado por NOMBRE alfabéticamente:")
    ordenado_nombre = ordenar_adaptativo(inventario, key=lambda x: x.nombre)
    for item in ordenado_nombre:
        print(item)

    print("\nPrueba finalizada con exito. Cero funciones nativas de Python utilizadas.")

def probar_inventario():
    print("\n=== PRUEBA DEL INVENTARIO ===")
    
    inv = InventarioLogica(capacidad_maxima=3)
    pocion = ObjetoInventarioMock("Poción de Vida", 50, 1.5)
    espada = ObjetoInventarioMock("Espada Corta", 150, 5.0)
    antorcha = ObjetoInventarioMock("Antorcha", 10, 2.0)
    
    inv.agregar_objeto(pocion)
    inv.agregar_objeto(espada)
    inv.agregar_objeto(antorcha)
    print("Inventario hasta el limite")
    
    assert inv.cantidad_actual == 3
    assert inv.cabeza.objeto is pocion
    assert inv.cola.objeto is antorcha
    
    try:
        inv.agregar_objeto(ObjetoInventarioMock("Armadura de Cuero", 200, 12.0))
    except ValueError as e:
        print(f"Error esperado al agregar objeto extra: {e}")
    
    print("Prueba de capacidad maxima del inventario finalizada.")
    
def probar_navegacion():
    print("\n=== PRUEBA DE NAVEGACION DEL INVENTARIO ===")
        
    inv = InventarioLogica(capacidad_maxima=5)
    a = ObjetoInventarioMock("A", 10, 1)
    b = ObjetoInventarioMock("B", 20, 2)
    c = ObjetoInventarioMock("C", 30, 3)
        
    for obj in [a, b, c]:
        inv.agregar_objeto(obj)
            
    assert inv.actual.objeto is a
        
    assert inv.siguiente_objeto() is True
    assert inv.actual.objeto is b
        
    assert inv.siguiente_objeto() is True
    assert inv.actual.objeto is c
        
    assert inv.siguiente_objeto() is False  # No hay siguiente
    assert inv.actual.objeto is c  # Sigue siendo C
        
    assert inv.anterior_objeto() is True
    assert inv.actual.objeto is b
        
    print("Prueba de navegacion del inventario finalizada.")
        
        
def probar_eliminacion():
    print("\n=== PRUEBA DE ELIMINACION DE OBJETOS DEL INVENTARIO ===")
        
    inv = InventarioLogica(capacidad_maxima=5)
    a = ObjetoInventarioMock("A", 10, 1)
    b = ObjetoInventarioMock("B", 20, 2)
    c = ObjetoInventarioMock("C", 30, 3)
        
    for obj in [a, b, c]:
        inv.agregar_objeto(obj)
            
    inv.eliminar_objeto_utilizado(b)
    assert inv.cantidad_actual == 2
        
    try:
        inv.eliminar_objeto_utilizado(b)  # Intentar eliminar de nuevo
        assert False, "Se esperaba un ValueError al eliminar un objeto no existente"
    except ValueError as e:
        print(f"Error esperado al eliminar objeto no existente: {e}")
            
def probar_soltar_objeto():
    print("\n=== PRUEBA DE SOLTAR OBJETO DEL INVENTARIO ===")
        
    inv = InventarioLogica(capacidad_maxima=5)
    a = ObjetoInventarioMock("A", 10, 1)
    b = ObjetoInventarioMock("B", 20, 2)
        
    for obj in [a, b]:
        inv.agregar_objeto(obj)
            
    inv.siguiente_objeto()  # Mueve el actual a 'b'
    assert inv.actual.objeto is b
    soltado = inv.soltar_objeto_actual()
        
    assert soltado is b
    assert inv.cantidad_actual == 1
    assert inv.actual.objeto is a  # Ahora el actual debería ser 'a'
    assert inv.cabeza.objeto is a
    assert inv.cola.objeto is a
    print("Prueba de soltar objeto del inventario finalizada.")
    

def probar_equipar_objeto():
    print("\n=== PRUEBA DE EQUIPAR OBJETO DEL INVENTARIO ===")
        
    inv = InventarioLogica(capacidad_maxima=5)
    a = ObjetoInventarioMock("A", 10, 1)
    b = ObjetoInventarioMock("B", 20, 2)
    c = ObjetoInventarioMock("C", 30, 3)
        
    for obj in [a, b, c]:
        inv.agregar_objeto(obj)
            
    inv.siguiente_objeto()  # Mueve el actual a 'b'
    inv.siguiente_objeto()  # Mueve el actual a 'c'
    assert inv.actual.objeto is c
    equipado = inv.equipar_objeto_actual()
        
    assert equipado is c
    assert inv.cantidad_actual == 3
    assert inv.cabeza.objeto is c  # Ahora el objeto 'c' debería estar en la cabeza del inventario
    assert inv.cola.objeto is b  # El objeto 'b' debería estar en la cola del inventario
    
    inv.actual = inv.cabeza  
    equipado_agaiiin = inv.equipar_objeto_actual()
    assert equipado_agaiiin is c  # Equipar de nuevo debería devolver el mismo objeto
    assert inv.cantidad_actual == 3  # La cantidad no debería cambiar
    assert inv.cabeza.objeto is c  # La cabeza sigue siendo 'c'
    assert inv.cola.objeto is b  # La cola sigue siendo 'b'
    
    print("Prueba de equipar objeto del inventario finalizada.")
    
def probar_vista_ordenada_no_altera_el_orden_actual():
    print("\n=== PRUEBA: VISTA ORDENADA NO CAMBIA EL ORDEN REAL ===")

    inv = InventarioLogica(capacidad_maxima=5)
    espada = ObjetoInventarioMock("Espada", 150, 5.0)
    pocion = ObjetoInventarioMock("Poción", 50, 1.5)
    escudo = ObjetoInventarioMock("Escudo", 80, 8.0)
    llave = ObjetoInventarioMock("Llave", 5, 0.5)
    for obj in (espada, pocion, escudo, llave):
        inv.agregar_objeto(obj)

    vista = inv.obtener_vista_ordenada("peso")

    # La vista si debe estar ordenada por peso
    pesos = [o.peso for o in vista]
    assert pesos == sorted(pesos)
    print(f"Vista ordenada por peso: {vista}")

    # Pero el orden REAL de la lista enlazada no debe cambiar
    assert inv.cabeza.objeto is espada
    assert inv.cola.objeto is llave
    print("El orden real de la lista enlazada no ha cambiado tras obtener la vista ordenada.")

    # Criterio invalido deberia de fallar
    try:
        inv.obtener_vista_ordenada("color")
        print("ERROR: deberia haber lanzado ValueError por criterio invalido")
    except ValueError as e:
        print(f"Criterio invalido lanza error correctamente: {e}")
    
def probar_todas_las_funciones():
    probar_ordenamiento()
    probar_inventario()
    probar_navegacion()
    probar_eliminacion()
    probar_soltar_objeto()
    probar_equipar_objeto()
    probar_vista_ordenada_no_altera_el_orden_actual()
        
        
if __name__ == "__main__":
    probar_todas_las_funciones()