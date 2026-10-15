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

        # 1. PREGUNTAR SI DESEA CARGAR PARTIDA ANTES DE EMPEZAR
        cargar = input("¿Deseas cargar una partida guardada anterior? (s/n): ").strip().lower()
        partida_cargada = False
        if cargar == 's':
            nombre_archivo = input("Ingresa el nombre del archivo de la partida: ").strip()
            try:
                self.servicio.cargarPartida(nombre_archivo)
                print("¡Partida cargada exitosamente!")
                partida_cargada = True
            except Exception as e:
                print(f"Error al cargar la partida: {e}. Se iniciará una nueva.")

        # Si NO se cargó una partida, procedemos a seleccionar la cripta y la semilla con normalidad
        if not partida_cargada:
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
                print("\n" + "=" * 50)
                print("¡HAS MUERTO! Tu aventura en la cripta ha llegado a su fin.")
                print("=" * 50)
                # 1. Guardamos el log de pasos
                nombre_log = input("Ingresa el nombre del archivo para guardar el log de pasos: ").strip()
                if not nombre_log:
                    nombre_log = "pruebasLog.log"
                
                try:
                    self.servicio.guardarLog(nombre_log)
                    print(f"Log guardado exitosamente.")
                except Exception as e:
                    print(f"Error al guardar el log: {e}")
                
                # 2. MOSTRAR EL HISTORIAL CRONOLÓGICO AQUÍ (Al morir)
                print("\n-------- HISTORIAL CRONOLÓGICO DE TU JUEGO --------")
                try:
                    # Si tienes un método para obtener o repetir los eventos del log:
                    resultados = self.servicio.repetirPartida(nombre_log)
                    if resultados:
                        for res in resultados:
                            print(res)
                except Exception as e:
                    print(f"No se pudo mostrar el historial: {e}")

                # 3. Mostrar el resumen con FinPartidaDTO
                try:
                    fin_dto = self.servicio.finPartida()
                    print("\n--- RESUMEN DE PARTIDA FINALIZADA ---")
                    print(f"  > ID Cripta: {fin_dto.id_Cripta}")
                    print(f"  > Versión Cripta: {fin_dto.vers_Cripta}")
                    print(f"  > Acciones del jugador: {fin_dto.acciones_jugador}")
                    print(f"  > Enemigos derrotados: {fin_dto.cantEnemigosDerrotados}")
                    print(f"  > Tiempo total: {fin_dto.tiempoReloj}")
                    print("=" * 50)
                except Exception as e:
                    print(f"Error al obtener el resumen: {e}")
                break
                
            sala_actual = self.servicio.obtenerSala(jugador.id_sala_actual)
            
            self.vista.mostrar_juego(jugador, sala_actual)

            accion = input("\n¿Qué deseas hacer? Ir al (norte/sur/este/oeste, recoger[objeto], " \
            "\n usar[objeto actual],siguiente[objeto],anterior[objeto]," \
            "\n soltar, atacar, abrir[puerta], cerrar[puerta], salir: ").strip().lower()

            if accion == "salir":
                guardar = input("¿Deseas guardar la partida antes de salir? (s/n): ").strip().lower()
                if guardar == 's':
                    nombre_archivo = input("Ingresa el nombre para guardar el archivo: ").strip()
                    try:
                        self.servicio.guardarPartida(nombre_archivo)
                        print("¡Partida guardada con éxito!")
                    except Exception as e:
                        print(f"Error al guardar la partida: {e}")
                print("Saliendo del juego...")
                break

            evento = self._mapear_entrada_a_evento(accion, sala_actual, jugador)

            if evento == "IGNORAR":
                continue  
            elif evento:
                print("\n --------HISTORIAL CRONOLÓGICO DE TU JUEGO--------\n")
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
                
     # Abrir puerta o salida bloqueada
        elif accion == "abrir":
            if not hasattr(sala_actual, "salidas") or not sala_actual.salidas:
                print("No hay salidas en esta sala.")
                return "IGNORAR"
            
            # 1. Mostramos las salidas de la sala para que el jugador elija
            print("\n¿Qué puerta deseas abrir?")
            for salida in sala_actual.salidas:
                estado_puerta = "CERRADA" if salida.cerrada else "ABIERTA"
                print(f"  - {salida.direccion} [{estado_puerta}]")
            
            direccion = input("Ingresa la dirección de la puerta que deseas abrir: ").strip().lower()
            if not direccion:
                print("Dirección no válida.")
                return "IGNORAR"
            
            # 2. Buscamos la salida correspondiente
            salida_encontrada = None
            for salida in sala_actual.salidas:
                if getattr(salida, "direccion", "").lower() == direccion:
                    salida_encontrada = salida
                    break
            
            if not salida_encontrada:
                print(f"No hay ninguna salida hacia el '{direccion}'.")
                return "IGNORAR"
            
            # 3. Verificamos si la salida ya está abierta
            if not salida_encontrada.cerrada:
                print(f"La puerta hacia el '{direccion}' ya está abierta.")
                return "IGNORAR"
            
            # 4. Validación de llave mediante el servicio
            id_llave_necesaria = salida_encontrada.llave
            
            if id_llave_necesaria:
                tiene_la_llave = self.servicio.tieneLlave(id_llave_necesaria)
                if not tiene_la_llave:
                    print(f"La puerta está cerrada. Necesitas la llave: '{id_llave_necesaria}' para poder abrirla.")
                    return "IGNORAR"
            
            # 5. GestorEventos espera [sala_actual, direccion].
            return EventoDTO(
                tiempo_ejecucion=50,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="ABRIR_PUERTA",
                datos_extra=[sala_actual, direccion]
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

        # 1. MOVERSE AL SIGUIENTE OBJETO DEL INVENTARIO
        elif accion in ("siguiente", "sig"):
            try:
                movido = jugador.inventario.siguiente_objeto()
                if movido:
                    print("-> Te has movido al siguiente objeto del inventario.")
                else:
                    print("-> Ya estás en el último objeto del inventario.")
            except ValueError as e:
                print(f"-> {e}")
            return "IGNORAR"

        # 2. MOVERSE AL OBJETO ANTERIOR DEL INVENTARIO
        elif accion in ("anterior", "ant"):
            try:
                movido = jugador.inventario.anterior_objeto()
                if movido:
                    print("-> Te has movido al objeto anterior del inventario.")
                else:
                    print("-> Ya estás en el primer objeto del inventario.")
            except ValueError as e:
                print(f"-> {e}")
            return "IGNORAR"

        # 3. USAR EL OBJETO ACTUAL
        elif accion == "usar":
            if not hasattr(jugador, "inventario") or not jugador.inventario or jugador.inventario.actual is None:
                print("Tu inventario está vacío.")
                return "IGNORAR"
            
            try:
                # Obtenemos directamente el objeto actual usando el método de tu compañero
                obj_actual = jugador.inventario.mostrar_objeto_actual()
            except ValueError as e:
                print(f"-> {e}")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=50,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="USAR_OBJETO",
                datos_extra=[obj_actual]
            )

        # 4. SOLTAR EL OBJETO ACTUAL
        elif accion == "soltar":
            if not hasattr(jugador, "inventario") or not jugador.inventario or jugador.inventario.actual is None:
                print("Tu inventario está vacío.")
                return "IGNORAR"
            
            try:
                # Obtenemos el objeto actual que va a ser soltado
                obj_actual = jugador.inventario.mostrar_objeto_actual()
            except ValueError as e:
                print(f"-> {e}")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=25,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="SOLTAR_OBJETO",
                datos_extra=[obj_actual]
            )
        
        print("Objeto no especificado o no disponible en tu inventario.")
        return None