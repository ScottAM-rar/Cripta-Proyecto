from DTO.EventoDTO import EventoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Controlador.Vista import VistaConsola

class ControladorJuego:
    def __init__(self, servicio: EstadoJuegoServicio):
        self.servicio = servicio
        self.vista = VistaConsola()

    def iniciar(self):
        print("\n¡Bienvenido a Cripta!")
        
        while True:
            # Obtenemos el jugador y su sala actual de forma dinámica a través del servicio
            jugador = self.servicio.getJudador()
            if not jugador:
                print("Error: No se pudo obtener el estado del jugador.")
                break
                
            sala_actual = self.servicio.obtenerSala(jugador.id_sala_actual)
            
            # Mostramos el estado visual actual usando la Vista
            
            self.vista.mostrar_juego(jugador, sala_actual)

            accion = input("\n¿Qué deseas hacer? (norte/sur/este/oeste, recoger [objeto], atacar, abrir, salir): ").strip().lower()

            if accion == "salir":
                print("Cerrando el juego...")
                break


            # Mapeamos la entrada del usuario a un EventoDTO oficial
            evento = self._mapear_entrada_a_evento(accion, sala_actual, jugador)

            if evento == "IGNORAR":
                continue  # Vuelve a empezar el turno limpiamente sin hacer nada
            elif evento:
                self.servicio.accionJugador(evento)
            else:
                print("Acción no reconocida o comando inválido.")

    def _mapear_entrada_a_evento(self, accion: str, sala_actual, jugador) -> EventoDTO | None:
        # Movimiento de salas
        if accion in ["norte", "sur", "este", "oeste"]:
            return EventoDTO(
                tiempo_ejecucion=10,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="MOVER_JUGADOR",
                datos_extra=[sala_actual, accion]
            )
            
        # Atacar a un enemigo seleccionado
        elif accion == "atacar":
            if not sala_actual.enemigos:
                print("No hay enemigos aquí para atacar.")
                return None
            
            if len(sala_actual.enemigos) == 1:
                objetivo = sala_actual.enemigos[0]
            else:
                print("\n¿A cuál enemigo deseas atacar?")
                for i, enm in enumerate(sala_actual.enemigos):
                    print(f"  [{i+1}] {enm.nombre} (Vida: {enm.vida_actual}/{enm.vida_max})")
                
                try:
                    opcion = int(input("Selecciona el número del objetivo: ")) - 1
                    if 0 <= opcion < len(sala_actual.enemigos):
                        objetivo = sala_actual.enemigos[opcion]
                    else:
                        print("Número de enemigo inválido.")
                        return None
                except ValueError:
                    print("Por favor ingresa un número válido.")
                    return None
                
            print(f"[DEBUG] Atacando a {objetivo.nombre} con vida: {objetivo.vida_actual}")

            # 1. PRIMERO validamos si está muerto ANTES de crear cualquier DTO de ataque
            if objetivo.vida_actual <= 0:
                print(f"¡{objetivo.nombre} ya está derrotado!")
                return "IGNORAR"

            # 2. SOLO SI ESTÁ VIVO, armamos y retornamos el EventoDTO
            return EventoDTO(
                tiempo_ejecucion=10,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="ATACAR",
                datos_extra=[objetivo]
            )
                
        # Abrir puerta bloqueada
        elif accion == "abrir":
            direccion = input("¿Qué dirección deseas abrir? (norte/sur/este/oeste): ").strip().lower()
            return EventoDTO(
                tiempo_ejecucion=10,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="ABRIR_PUERTA",
                datos_extra=[sala_actual, direccion]
            )
            
        # Recoger objeto
        elif accion.startswith("recoger"):
            partes = accion.split(maxsplit=1)
            if len(partes) > 1 and sala_actual.objetos:
                busqueda = partes[1].lower()
                obj_encontrado = next((obj for obj in sala_actual.objetos if busqueda in str(obj).lower()), None)
                if obj_encontrado:
                    return EventoDTO(
                        tiempo_ejecucion=10,
                        id_secuencia=0,
                        actor=jugador,
                        tipo_accion="RECOGER_OBJETO",
                        datos_extra=[obj_encontrado]
                    )
            print("Objeto no especificado o no disponible en la sala.")
            return None

        return None