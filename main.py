from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Controlador.ControladorJuego import ControladorJuego

def main():
    print("Inicializando Cripta...")
    servicio = EstadoJuegoServicio()
    
    # Obtenemos las criptas disponibles y seleccionamos la primera por defecto
    criptas = servicio.listarCriptas()
    if not criptas:
        print("No se encontraron criptas disponibles.")
        return
        
    id_cripta = servicio.obtenerIdCripta(1) 
    servicio.iniciarJuego(id_cripta)
    
    # Le pasamos el servicio ya inicializado al controlador
    controlador = ControladorJuego(servicio)
    controlador.iniciar()

if __name__ == "__main__":
    main()