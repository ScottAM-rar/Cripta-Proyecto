from Controlador.MotorJuegoStub import MotorJuegoStub
from Controlador.Vista import VistaConsola

def main():
    motor = MotorJuegoStub()
    vista = VistaConsola()

    while True:
        estado = motor.obtener_estado_actual()
        vista.mostrar_juego(estado)

        accion = input("\n¿Qué deseas hacer? (ej: norte, sur, este, oeste, atacar, salir): ").strip().lower()

        # Usamos match-case (el equivalente moderno al switch en Python)
        match accion:
            case "salir":
                print("Cerrando el juego...")
                break
                
            case "norte" | "n":
                motor.ejecutar_accion("moverse", "norte")
                
            case "sur" | "s":
                motor.ejecutar_accion("moverse", "sur")
                
            case "este" | "e":
                motor.ejecutar_accion("moverse", "este")
                
            case "oeste" | "o":
                motor.ejecutar_accion("moverse", "oeste")
                
            case "atacar":
                motor.ejecutar_accion("atacar")
                
            case _:
                motor.mensajes_bitacora.append(f"Acción no reconocida: '{accion}'")

if __name__ == "__main__":
    main()