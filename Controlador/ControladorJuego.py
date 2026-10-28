from DTO.EventoDTO import EventoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from Controlador.Vista import VistaConsola
import random

class ControladorJuego:
    def __init__(self, servicio: EstadoJuegoServicio):
        self.servicio = servicio
        self.vista = VistaConsola()
        self._advertencias_mostradas = 0

    def _mostrar_advertencias_nuevas(self):
        """Muestra las advertencias de datos que aparecieron desde la última vez (cada una se muestra una sola vez)."""
        todas = self.servicio.advertenciasDeDatos()
        if len(todas) > self._advertencias_mostradas:
            self.vista.mostrar_advertencias(todas[self._advertencias_mostradas:])
            self._advertencias_mostradas = len(todas)

    def iniciar(self):
        print("\n¡Bienvenido a Cripta!")

        if input("¿Deseas ver la tabla de puntajes? (s/n): ").strip().lower() == 's':
            self._mostrar_puntajes()

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
            self._mostrar_advertencias_nuevas()
                
            terminado, _ = self.servicio.terminado()
            if terminado or jugador.vida_actual <= 0:
                print("\n" + "=" * 50)
                if jugador.vida_actual <= 0:
                    print("¡HAS MUERTO! Tu aventura en la cripta ha llegado a su fin.")
                else:
                    print("¡HAS LLEGADO A LA SALA DE SALIDA! Has escapado de la cripta.")
                print("=" * 50)
                # El puntaje se registra primero, antes de mostrar nada más de la partida
                self._registrar_puntaje()
                # 1. El log se fue grabando solo durante la partida
                nombre_log = self.servicio.nombreLog()
                if nombre_log:
                    print(f"Log de la partida guardado en logs/{nombre_log} (para reproducirlo: python main.py --replay {nombre_log})")
                
                # 2. Los últimos mensajes del juego (§4.8: máximo 20); el registro completo está en el log
                print("\n-------- ÚLTIMOS MENSAJES DEL JUEGO (máx. 20) --------")
                try:
                    mensajes = self.servicio.ultimosMensajes()
                    if mensajes:
                        for mensaje in mensajes:
                            print(mensaje)
                    else:
                        print("(sin mensajes)")
                except Exception as e:
                    print(f"No se pudieron mostrar los mensajes: {e}")

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
            
            self.vista.mostrar_juego(jugador, sala_actual, self.servicio.objetoActualInventario(), self.servicio.ultimosMensajes())

            accion = input("\n¿Qué deseas hacer? Ir al (norte/sur/este/oeste, recoger[objeto], " \
            "\n usar[objeto actual],siguiente[objeto],anterior[objeto]," \
            "\n soltar, atacar, esperar, abrir[puerta], cerrar[puerta]," \
            "\n inventario[peso/valor/nombre], salir: ").strip().lower()

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
                self.servicio.accionJugador(evento)
            else:
                print("Acción no reconocida o comando inválido.")

    def _registrar_puntaje(self):
        """Pide el nombre del jugador y registra la partida terminada en la tabla de puntajes (§2.12)."""
        maximo = self.servicio.MAX_NOMBRE_JUGADOR
        print("\n--- REGISTRO DE PUNTAJE ---")
        while True:
            nombre = input(f"Ingresa tu nombre (máx. {maximo} caracteres): ").strip()
            if not nombre:
                print("El nombre no puede estar vacío.")
                continue
            if len(nombre) > maximo:
                print(f"El nombre no puede pasar de {maximo} caracteres (tiene {len(nombre)}).")
                continue
            try:
                registro = self.servicio.registrarPuntaje(nombre)
                print("¡Puntaje registrado!")
            except Exception as e:
                print(f"No se pudo registrar el puntaje: {e}")
                return
            self._mostrar_puntajes(registro)
            return

    def _mostrar_puntajes(self, resaltar=None):
        """Muestra la tabla de puntajes; un archivo dañado se informa sin detener el juego."""
        try:
            self.vista.mostrar_puntajes(self.servicio.tablaPuntajes(), resaltar=resaltar)
        except Exception as e:
            print(f"No se pudo leer la tabla de puntajes: {e}")

    def _mapear_entrada_a_evento(self, accion: str, sala_actual, jugador) -> EventoDTO | None:
       # Movimiento de salas
        if accion in ["norte", "sur", "este", "oeste"]:
            salida = next(
                (
                    salida for salida in sala_actual.salidas
                    if salida.direccion.lower() == accion
                ),
                None
            )

            if salida is None:
                print(f"No existe una salida hacia el '{accion}'.")
                return "IGNORAR"

            if salida.cerrada:
                if salida.llave:
                    print(
                        f"La salida hacia el '{accion}' está cerrada. "
                        f"Necesitas la llave: '{salida.llave}'."
                    )
                else:
                    print(f"La salida hacia el '{accion}' está cerrada.")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=salida.costo,      # moverse cuesta lo que cuesta la salida (FR-103)
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

            # Mostramos únicamente las puertas cerradas
            puertas_cerradas = [
                salida for salida in sala_actual.salidas
                if salida.cerrada
            ]

            if not puertas_cerradas:
                print("No hay puertas cerradas en esta sala.")
                return "IGNORAR"

            print("\n¿Qué puerta deseas abrir?")
            for salida in puertas_cerradas:
                if salida.llave:
                    print(
                        f"  - {salida.direccion} "
                        f"[CERRADA - Requiere: {salida.llave}]"
                    )
                else:
                    print(f"  - {salida.direccion} [CERRADA]")

            direccion = input(
                "Ingresa la dirección de la puerta que deseas abrir: "
            ).strip().lower()

            if not direccion:
                print("Dirección no válida.")
                return "IGNORAR"

            # Buscamos solamente entre las puertas cerradas mostradas
            salida_encontrada = None
            for salida in puertas_cerradas:
                if getattr(salida, "direccion", "").lower() == direccion:
                    salida_encontrada = salida
                    break

            if not salida_encontrada:
                print(f"No hay ninguna puerta cerrada hacia el '{direccion}'.")
                return "IGNORAR"

            # Validación de llave mediante el servicio
            id_llave_necesaria = salida_encontrada.llave

            if id_llave_necesaria:
                tiene_la_llave = self.servicio.tieneLlave(id_llave_necesaria)

                if not tiene_la_llave:
                    print(
                        f"La puerta está cerrada. Necesitas la llave: "
                        f"'{id_llave_necesaria}' para poder abrirla."
                    )
                    return "IGNORAR"

            # GestorEventos espera [sala_actual, direccion]
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
                movido = self.servicio.siguienteObjetoInventario()
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
                movido = self.servicio.anteriorObjetoInventario()
                if movido:
                    print("-> Te has movido al objeto anterior del inventario.")
                else:
                    print("-> Ya estás en el primer objeto del inventario.")
            except ValueError as e:
                print(f"-> {e}")
            return "IGNORAR"

        # 3. USAR EL OBJETO ACTUAL
        elif accion == "usar":
            obj_actual = self.servicio.objetoActualInventario()
            if obj_actual is None:
                print("Tu inventario está vacío.")
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
            obj_actual = self.servicio.objetoActualInventario()
            if obj_actual is None:
                print("Tu inventario está vacío.")
                return "IGNORAR"

            return EventoDTO(
                tiempo_ejecucion=25,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="SOLTAR_OBJETO",
                datos_extra=[obj_actual]
            )

        # 5. ESPERAR (§2.3: costo 100; no cambia nada, solo deja pasar el tiempo)
        elif accion == "esperar":
            return EventoDTO(
                tiempo_ejecucion=100,
                id_secuencia=0,
                actor=jugador,
                tipo_accion="ESPERAR",
                datos_extra=[]
            )

        # 6. VER EL INVENTARIO (§4.5, §10.2): orden real, o vista ordenada por peso, valor o nombre. No consume tiempo
        elif accion.split()[:1] == ["inventario"]:
            partes = accion.split()
            if len(partes) > 2:
                print("Uso: inventario [peso|valor|nombre]")
                return "IGNORAR"
            criterio = partes[1] if len(partes) == 2 else None
            try:
                objetos = self.servicio.vistaInventario(criterio)
            except ValueError as e:
                print(f"-> {e}")
                return "IGNORAR"
            self.vista.mostrar_inventario(objetos, jugador, criterio)
            return "IGNORAR"
        
        print("Comando no reconocido.")
        return None