from DTO.ActorDTO import *

jugador = JugadorDTO(
    vida_max=100, 
    ataque=15, 
    defensa=10, 
    velocidad=5, 
    inventario_max=15
)

# 2. Consultas el límite directamente desde la deque
print(jugador.inventario.maxlen)  # Imprime: 15

# 3. Compruebas que NO se guardó ningún atributo innecesario
print(hasattr(jugador, "capacidad_inventario"))  # Imprime: False