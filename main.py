from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Controlador.ControladorJuego import ControladorJuego

def main():
    print("Inicializando Cripta...")
    servicio = EstadoJuegoServicio()
    
    # El controlador se encarga de todo el flujo y la interacción inicial
    controlador = ControladorJuego(servicio)
    controlador.iniciar()

if __name__ == "__main__":
    main()