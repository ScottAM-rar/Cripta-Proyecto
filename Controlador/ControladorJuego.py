from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.EventoDTO import EventoDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Controlador.Vista import VistaConsola

class ControladorJuego:
    def __init__(self, estado_juego: EstadoJuego):
        self.estado_juego = estado_juego
        self.juego_logica = EstadoJuegoLogica(self.estado_juego)
        self.vista = VistaConsola()

    def iniciar(self):
        print("¡Bienvenido a Cripta!")
        
        while True:
            sala_actual = self.obtener_sala_actual_del_jugador()
            
            # 1. Mostramos la sala, objetos, enemigos y trampas reales
            self.vista.mostrar_juego(self.estado_juego, sala_actual)

            accion = input("\n¿Qué deseas hacer? (norte/sur/este/oeste, recoger [objeto], atacar, abrir, salir): ").strip().lower()

            if accion == "salir":
                print("Cerrando el juego...")
                break

            # 2. Convertimos la entrada de texto directamente en un EventoDTO 
            # que respeta los casos exactos del GestorEventos 
            evento = self._mapear_entrada_a_evento(accion, sala_actual)

            if evento:
                # 3. Se lo pasamos a la lógica del estado (que usa el RelojVirtual y el GestorEventos)
                resultado = self.juego_logica.accionJugador(evento)
                

    def _mapear_entrada_a_evento(self, accion: str, sala_actual) -> EventoDTO | None:
        jugador = self.estado_juego.jugador
        
        # Movimiento de salas
        if accion in ["norte", "sur", "este", "oeste"]:
            return EventoDTO(
                tiempo_ejecucion=10,
                id_secuencia=0, # El reloj se encarga de esto
                actor=jugador,
                tipo_accion="MOVER_JUGADOR",
                datos_extra=[sala_actual, accion]
            )
            
        # Atacar al primer enemigo disponible en la sala
        elif accion == "atacar":
            if sala_actual.enemigos:
                objetivo = sala_actual.enemigos[0]
                return EventoDTO(
                    tiempo_ejecucion=10,
                    id_secuencia=0,
                    actor=jugador,
                    tipo_accion="ATACAR",
                    datos_extra=[objetivo]
                )
            else:
                print("No hay enemigos aquí para atacar.")
                return None
                
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
            
        # Recoger objeto del suelo
        elif accion.startswith("recoger"):
            partes = accion.split(maxsplit=1)
            if len(partes) > 1 and sala_actual.objetos:
                busqueda = partes[1].lower()
                # Buscamos si coincide de manera parcial (ej: escribir 'antorcha' encuentra 'itm_antorcha')
                obj_encontrado = next((obj for obj in sala_actual.objetos if busqueda in str(obj).lower()), None)
                if obj_encontrado:
                    return EventoDTO(
                        tiempo_ejecucion=10,
                        id_secuencia=0,
                        actor=jugador,
                        tipo_accion="RECOGER_OBJETO",
                        datos_extra=[obj_encontrado]
                    )
            print("Ese objeto no se encontró en la sala.")
            return None

        return None

    def obtener_sala_actual_del_jugador(self):
        # Obtenemos el ID de la sala en la que se encuentra el jugador actualmente
        id_sala_jugador = self.estado_juego.jugador.id_sala_actual
        
        # Buscamos en la lista de salas del estado del juego
        for sala in self.estado_juego.salas:
            if sala.id == id_sala_jugador:
                return sala
                
        # Por seguridad, si no la encuentra, devuelve la primera
        return self.estado_juego.salas[0]