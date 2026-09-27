from Controlador.MotorJuegoStub import MotorJuegoStub
from Controlador.Vista import VistaConsola

def main():
    motor = MotorJuegoStub()
    vista = VistaConsola()

    while True:
        estado = motor.obtener_estado_actual()
    
        vista.mostrar_juego(estado)

        accion = input("\n¿Qué deseas hacer? (ej: norte, sur, este, oeste, atacar, salir): ").strip().lower()

        if accion == "salir":
            print("Cerrando el juego...")
            break
        
        elif accion in ["n", "s", "e", "o", "norte", "sur", "este", "oeste"]:
            dir_map = {
                "norte": "norte", "n": "norte",
                "sur": "sur", "s": "sur",
                "este": "este", "e": "este",
                "oeste": "oeste", "o": "oeste" # esto era solo para probar, no se va a quedar así
            }
            direccion = dir_map.get(accion)
            motor.ejecutar_accion("moverse", direccion)
            
        elif accion == "atacar":
            motor.ejecutar_accion("atacar")
        else:
            motor.mensajes_bitacora.append(f"Acción no reconocida: '{accion}'")

if __name__ == "__main__":
    main()