from DTO.EventoDTO import EventoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Controlador.Vista import VistaConsola
import random

class ControladorJuego:
    def __init__(self, servicio: EstadoJuegoServicio):
        self.servicio = servicio
        self.vista = VistaConsola()

    def iniciar(self):
        print("\n¡Bienvenido a Cripta!")
        
        # 1. Obtenemos las criptas disponibles desde el servicio
        criptas = self.servicio.listarCriptas()
        if not criptas:
            print("No se encontraron criptas disponibles.")
            return

        # 2. Mostramos el menú de selección al usuario
        print("\nSelecciona la cripta que deseas jugar:")
        for i, cripta in enumerate(criptas):
            print(f"  [{i + 1}] {cripta}")

        # 3. Validamos la entrada de la cripta
        while True:
            try:
                opcion = int(input("\nIngresa el número de la cripta: "))
                if 1 <= opcion <= len(criptas):
                    id_cripta = self.servicio.obtenerIdCripta(opcion)
                    break
                else:
                    print(f"Número inválido. Debe ser entre 1 y {len(criptas)}.")
            except ValueError:
                print("Por favor, ingresa un número válido.")

       # 4. Pedimos la semilla (opcional)
        entrada_semilla = input("Ingresa la semilla (deja en blanco para generar una aleatoria): ").strip()
        
        if entrada_semilla.isdigit():
            semilla = int(entrada_semilla)
            print(f"-> Usando semilla ingresada por el usuario: {semilla}")
        else:
            # Generamos una semilla aleatoria (por ejemplo, entre 1 y 99999)
            semilla = random.randint(1, 99999)
            print(f"-> No se ingresó semilla. Se generó automáticamente la semilla: {semilla}")

        # 5. Inicializamos el juego pasando la cripta y la semilla
        self.servicio.iniciarJuego(id_cripta, semilla)

        # 6. Entramos al bucle principal del juego...
        while True:
            jugador = self.servicio.getJudador()
            if not jugador:
                print("Error: No se pudo obtener el estado del jugador.")
                break
                
            if jugador.vida_actual <= 0:
                self.servicio.guardarLog("pruebasLog.log")
                break
                
            sala_actual = self.servicio.obtenerSala(jugador.id_sala_actual)
            
            self.vista.mostrar_juego(jugador, sala_actual)

            accion = input("\n¿Qué deseas hacer? Ir al (norte/sur/este/oeste, recoger[objeto], " \
            "\n usar[objeto], soltar[objeto], atacar, abrir[puerta], cerrar[puerta], salir: ").strip().lower()

            if accion == "salir":
                print("Cerrando el juego...")
                break

            evento = self._mapear_entrada_a_evento(accion, sala_actual, jugador)

            if evento == "IGNORAR":
                continue  
            elif evento:
                self.servicio.accionJugador(evento)
            else:
                print("Acción no reconocida o comando inválido.")

    def _mapear_entrada_a_evento(self, accion: str, sala_actual, jugador) -> EventoDTO | None:
        # Movimiento de salas
        if accion in ["norte", "sur", "este", "oeste"]:
            return EventoDTO(
                tiempo_ejecucion=100,
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

            # Validación de vida antes de crear el DTO de ataque
            if objetivo.vida_actual <= 0:
                print(f"¡{objetivo.nombre} ya está derrotado!")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=100,
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

        # Cerrar puerta (El backend exige que el actor sea la sala actual)
        elif accion == "cerrar":
            direccion = input("¿Qué dirección deseas cerrar? (norte/sur/este/oeste): ").strip().lower()
            return EventoDTO(
                tiempo_ejecucion=50,
                id_secuencia=0,
                actor=sala_actual,
                tipo_accion="CERRAR_PUERTA",
                datos_extra=[direccion]
            )

            
        # 1. RECOGER OBJETO (Menú interactivo por número basado en la sala)
        elif accion == "recoger":
            if not sala_actual.objetos:
                print("No hay objetos aquí para recoger.")
                return "IGNORAR"
            
            print("\n¿Qué objeto deseas recoger?")
            for i, obj in enumerate(sala_actual.objetos):
                print(f"  [{i+1}] {obj.nombre} (ID: {getattr(obj, 'id', 'N/A')})")
            
            try:
                opcion = int(input("Selecciona el número del objeto: ")) - 1
                if 0 <= opcion < len(sala_actual.objetos):
                    obj_encontrado = sala_actual.objetos[opcion]
                else:
                    print("Número de objeto inválido.")
                    return "IGNORAR"
            except ValueError:
                print("Por favor ingresa un número válido.")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=25,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="RECOGER_OBJETO",
                datos_extra=[obj_encontrado]
            )

        # 2. USAR OBJETO (Recorre la lista enlazada del compañero para mostrar el menú)
        elif accion == "usar":
            if not hasattr(jugador, "inventario") or not jugador.inventario or jugador.inventario.cabeza is None:
                print("Tu inventario está vacío.")
                return "IGNORAR"

            # Recorremos la lista enlazada oficial usando los punteros de tu compañero
            lista_temporal = []
            nodo_actual = jugador.inventario.cabeza
            
            print("\n¿Qué objeto deseas usar?")
            i = 1
            while nodo_actual is not None:
                obj = nodo_actual.objeto
                lista_temporal.append(obj)
                print(f"  [{i}] {obj.nombre} (ID: {getattr(obj, 'id', 'N/A')})")
                nodo_actual = nodo_actual.siguiente
                i += 1
            
            try:
                opcion = int(input("Selecciona el número del objeto: ")) - 1
                if 0 <= opcion < len(lista_temporal):
                    obj_encontrado = lista_temporal[opcion]
                else:
                    print("Número de objeto inválido.")
                    return "IGNORAR"
            except ValueError:
                print("Por favor ingresa un número válido.")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=50,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="USAR_OBJETO",
                datos_extra=[obj_encontrado]
            )

        # 3. SOLTAR OBJETO (Recorre la lista enlazada del compañero para mostrar el menú)
        elif accion == "soltar":
            if not hasattr(jugador, "inventario") or not jugador.inventario or jugador.inventario.cabeza is None:
                print("Tu inventario está vacío.")
                return "IGNORAR"

            # Recorremos la lista enlazada oficial usando los punteros de tu compañero
            lista_temporal = []
            nodo_actual = jugador.inventario.cabeza
            
            print("\n¿Qué objeto deseas soltar?")
            i = 1
            while nodo_actual is not None:
                obj = nodo_actual.objeto
                lista_temporal.append(obj)
                print(f"  [{i}] {obj.nombre} (ID: {getattr(obj, 'id', 'N/A')})")
                nodo_actual = nodo_actual.siguiente
                i += 1
            
            try:
                opcion = int(input("Selecciona el número del objeto: ")) - 1
                if 0 <= opcion < len(lista_temporal):
                    obj_encontrado = lista_temporal[opcion]
                else:
                    print("Número de objeto inválido.")
                    return "IGNORAR"
            except ValueError:
                print("Por favor ingresa un número válido.")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=25,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="SOLTAR_OBJETO",
                datos_extra=[obj_encontrado]
            )
        
        print("Objeto no especificado o no disponible en tu inventario.")
        return None