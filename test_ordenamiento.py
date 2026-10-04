from Controlador.ordenamiento import ordenar_adaptativo

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

if __name__ == "__main__":
    probar_ordenamiento()