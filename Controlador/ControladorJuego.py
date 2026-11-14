from DTO.EventoDTO import EventoDTO
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio, CriptaNoResoluble
from Controlador.Vista import VistaConsola
from Controlador import Pantallas as P
import random

SALIDA_NORMAL = 0
SALIDA_RECHAZADA = 1       # la partida no se abrió (sin criptas, cripta no resoluble sin --forzar)


class ControladorJuego:
    def __init__(self, servicio: EstadoJuegoServicio, k_checkpoint: int | None = None, forzar: bool = False):
        self.servicio = servicio
        self.vista = VistaConsola()
        self.k_checkpoint_cli = k_checkpoint
        self.forzar = forzar           # lo recibe de main.py y lo pasa tal cual a iniciarJuego (FR-305); aquí no se decide
        self._advertencias_mostradas = 0

    def _mostrar_advertencias_nuevas(self):
        """Muestra las advertencias de datos que aparecieron desde la última vez (cada una se muestra una sola vez)."""
        todas = self.servicio.advertenciasDeDatos()
        if len(todas) > self._advertencias_mostradas:
            self.vista.mostrar_advertencias(todas[self._advertencias_mostradas:])
            self._advertencias_mostradas = len(todas)

    def _llaves_de_las_salidas(self, sala_actual, sala_conocida) -> list:
        """La llave que pide cada salida cerrada de la sala actual, en el orden de `sala_conocida.salidas`. Es contenido de la
        sala que el jugador ve (se cruza la sala real con su conocimiento); la vista solo la presenta (FR-312)."""
        llaves = []
        for salida in sala_conocida.salidas:
            llave = None
            if salida.puerta == "cerrada":
                for real in sala_actual.salidas:
                    if real.direccion == salida.direccion:
                        llave = real.llave
            llaves.append(llave)
        return llaves

    def _mostrar_arranque_verificado(self):
        """Partida nueva (FR-301, FR-304): primero el reporte de resolubilidad, después el aviso de `--forzar` o de que la
        verificación no está disponible, y recién entonces los avisos de llaves y de datos y el primer turno."""
        reporte = self.servicio.reporteVerificacion()
        if reporte is not None:
            self.vista.mostrar_reporte_verificacion(reporte)
        aviso = self.servicio.avisoResolubilidad()
        if aviso is not None:
            self.vista.mostrar_aviso(aviso)

    def _mostrar_fin_de_partida(self, jugador):
        """Resumen de fin de partida (FR-307): junta datos que el servicio ya entrega; la función de pantalla arma el texto."""
        try:
            fin_dto = self.servicio.finPartida()
            _, motivo = self.servicio.terminado()
            try:
                mapa = self.servicio.mapaConocido()
                salas_exploradas = None if mapa is None else len(mapa.salas)
            except ValueError:                       # la cripta no entrega el esqueleto: no hay mapa conocido
                salas_exploradas = None
            self.vista.mostrar_fin_partida(motivo, self.servicio.puntaje(), fin_dto.acciones_jugador, fin_dto.tiempoReloj,
                                           jugador.vida_actual, salas_exploradas, fin_dto.id_Cripta, fin_dto.vers_Cripta,
                                           fin_dto.cantEnemigosDerrotados)
        except Exception as e:
            self.vista.mostrar_error(P.mensaje_resumen_fallido(e))

    def iniciar(self) -> int:
        """Bucle del juego. Devuelve el código de salida del programa: 0 normal; 1 si la partida no se abrió."""
        print("\n¡Bienvenido a Cripta!")

        if input("¿Deseas ver la tabla de puntajes? (s/n): ").strip().lower() == 's':
            self._mostrar_puntajes()

        # 1. PREGUNTAR SI DESEA CARGAR PARTIDA ANTES DE EMPEZAR
        cargar = input("¿Deseas cargar una partida guardada anterior? (s/n): ").strip().lower()
        partida_cargada = False
        if cargar == 's':
            nombre_archivo = input("Ingresa el nombre del archivo de la partida: ").strip()
            try:
                self.servicio.cargarPartida(nombre_archivo, k_checkpoint=self.k_checkpoint_cli)
                print("¡Partida cargada exitosamente!")
                partida_cargada = True
            except Exception as e:
                self.vista.mostrar_error(P.mensaje_carga_fallida(e))

        # Si NO se cargó una partida, procedemos a seleccionar la cripta y la semilla con normalidad
        if not partida_cargada:
            # 1. Obtenemos las criptas disponibles desde el servicio
            criptas = self.servicio.listarCriptas()
            if not criptas:
                self.vista.mostrar_error(P.mensaje_sin_criptas())
                return SALIDA_RECHAZADA

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
                        self.vista.mostrar_error(P.mensaje_numero_cripta_invalido(len(criptas)))
                except ValueError:
                    self.vista.mostrar_error(P.mensaje_no_es_numero())

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
            try:
                self.servicio.iniciarJuego(id_cripta, semilla, forzar=self.forzar)
            except CriptaNoResoluble as rechazo:
                # Sin --forzar: se muestra el reporte, qué hacer, y la partida no se abre (FR-301, FR-303, FR-310).
                self.vista.mostrar_reporte_verificacion(self.servicio.lineasDeReporte(rechazo.resultado))
                self.vista.mostrar_error(P.mensaje_cripta_no_resoluble(id_cripta))
                return SALIDA_RECHAZADA
            self._mostrar_arranque_verificado()
            # Partida nueva: si no se pudo obtener la ubicación de las llaves, se avisa y la partida sigue (FR-313).
            aviso_llaves = self.servicio.avisoLlaves()
            if aviso_llaves is not None:
                self.vista.mostrar_advertencias([aviso_llaves])

        # 6. Reportar intervalo de puntos de control e iniciar bucle principal
        print(f"Puntos de control cada: {self.servicio.k_checkpoint} acciones")
        # 6. Entramos al bucle principal del juego...
        while True:
            jugador = self.servicio.getJudador()
            if not jugador:
                self.vista.mostrar_error(P.mensaje_sin_jugador())
                return SALIDA_RECHAZADA
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

                # 3. Resumen de fin de partida (FR-307): motivo, puntaje, acciones, tiempo, vida final y salas exploradas
                self._mostrar_fin_de_partida(jugador)

                # Bucle interactivo post-partida (FR-427, plan.md §6)
                print("\nPartida concluida. Puedes consultar la historia ('historia <t>', 'historia #k') o escribir 'salir'.")
                while True:
                    try:
                        linea_post = input("\n[Post-partida] historia <t> / historia #k / ayuda / salir: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        break
                    if linea_post.lower() == "salir":
                        break
                    if linea_post.lower() == "ayuda":
                        self.vista.mostrar_ayuda(P.texto_ayuda(post_partida=True))
                        continue
                    if not self._procesar_comando_historia(linea_post):
                        self.vista.mostrar_error(P.mensaje_post_partida_desconocido())
                return SALIDA_NORMAL
                
            sala_actual = self.servicio.obtenerSala(jugador.id_sala_actual)
            
            sala_conocida = self.servicio.vistaSalaActual()
            print()                      # una línea en blanco separa la pantalla de lo que se imprimió antes
            self.vista.mostrar_juego(jugador, sala_actual, sala_conocida, self.servicio.objetoActualInventario(),
                                     self.servicio.ultimosMensajes(), self.servicio.tiempoActual(),
                                     self._llaves_de_las_salidas(sala_actual, sala_conocida))

            try:
                entrada_usuario = input("\n" + P.PROMPT).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if self._procesar_comando_historia(entrada_usuario):
                continue

            if self._procesar_comando_ir_a(entrada_usuario):
                continue

            accion = entrada_usuario.lower()

            if accion == "salir":
                guardar = input("¿Deseas guardar la partida antes de salir? (s/n): ").strip().lower()
                if guardar == 's':
                    nombre_archivo = input("Ingresa el nombre para guardar el archivo: ").strip()
                    try:
                        self.servicio.guardarPartida(nombre_archivo)
                        print("¡Partida guardada con éxito!")
                    except Exception as e:
                        self.vista.mostrar_error(P.mensaje_guardado_fallido(e))
                print("Saliendo del juego...")
                break

            if accion == "ayuda":
                # No es una acción del jugador: no avanza el reloj ni entra al historial ni al log (FR-309)
                self.vista.mostrar_ayuda(P.texto_ayuda())
                continue

            if accion == "mapa":
                # No es una acción del jugador: no pasa por accionJugador, no avanza el reloj ni entra al historial ni al log (FR-218)
                self.vista.mostrar_mapa_conocido(self.servicio.mapaConocido())
                continue

            evento = self._mapear_entrada_a_evento(accion, sala_actual, jugador)

            if evento == "IGNORAR":
                continue  
            elif evento:
                self.servicio.accionJugador(evento)
            # evento None: el mensaje de rechazo ya lo mostró _mapear_entrada_a_evento
        return SALIDA_NORMAL

    def _procesar_comando_ir_a(self, comando: str) -> bool:
        """Interpreta «ir a <id de sala>» (capacidad 006, FR-231). Devuelve True si la entrada era ese comando (con éxito
        o con un mensaje de error) y False si no lo era. Solo interpreta: el viaje lo decide el modelo y la vista imprime.
        No es un evento del reloj: un rechazo no consume tiempo ni cuenta como acción (FR-238)."""
        partes = comando.strip().lower().split()
        if len(partes) < 2 or partes[0] != "ir" or partes[1] != "a":
            return False
        if len(partes) != 3 or not partes[2].isdigit():
            self.vista.mostrar_error(P.mensaje_ir_a_destino_invalido())      # no hay orden que el modelo pueda rechazar
            return True
        try:
            resultado = self.servicio.irA(int(partes[2]))
        except ValueError as error:
            self.vista.mostrar_error(P.mensaje_ir_a_rechazada(error))
            return True
        self.vista.mostrar_viaje(resultado)
        return True

    def _procesar_comando_historia(self, comando: str) -> bool:
        """Interpreta comandos 'historia <t>', 'historia t', 'historia #k'.
        Retorna True si fue un comando de historia (procesado o con error formateado),
        o False si la entrada no es un comando de historia.
        """
        linea = comando.strip()
        partes = linea.split(maxsplit=1)
        if not partes or partes[0].lower() != "historia":
            return False

        if len(partes) == 1:
            self.vista.mostrar_error(P.mensaje_historia_sin_parametro())
            return True

        param = partes[1].strip()

        # Caso historia #k o historia # k
        if param.startswith("#"):
            resto = param[1:].strip()
            if "." in resto:
                try:
                    float(resto)
                    self.vista.mostrar_error(P.mensaje_historia_no_entero())
                    return True
                except ValueError:
                    pass
            try:
                k = int(resto)
            except ValueError:
                self.vista.mostrar_error(P.mensaje_historia_sin_parametro())
                return True

            if k < 0:
                self.vista.mostrar_error(P.mensaje_historia_negativo())
                return True
            if k == 0:
                self.vista.mostrar_error(P.mensaje_historia_accion_cero())
                return True

            try:
                resumen = self.servicio.consultarHistoria(accion=k)
                if self.vista is not None:
                    self.vista.mostrar_historia(resumen)
            except Exception as e:
                self.vista.mostrar_error(P.mensaje_historia_rechazada(e))
            return True

        # Caso historia <t> o historia t
        token = param
        if token.startswith("<") and token.endswith(">"):
            token = token[1:-1].strip()

        if "." in token:
            try:
                float(token)
                self.vista.mostrar_error(P.mensaje_historia_no_entero())
                return True
            except ValueError:
                pass

        try:
            t = int(token)
        except ValueError:
            self.vista.mostrar_error(P.mensaje_historia_sin_parametro())
            return True

        if t < 0:
            self.vista.mostrar_error(P.mensaje_historia_negativo())
            return True

        try:
            resumen = self.servicio.consultarHistoria(instante=t)
            if self.vista is not None:
                self.vista.mostrar_historia(resumen)
        except Exception as e:
            self.vista.mostrar_error(P.mensaje_historia_rechazada(e))
        return True

    def _registrar_puntaje(self):
        """Pide el nombre del jugador y registra la partida terminada en la tabla de puntajes (§2.12)."""
        maximo = self.servicio.MAX_NOMBRE_JUGADOR
        print("\n--- REGISTRO DE PUNTAJE ---")
        while True:
            nombre = input(f"Ingresa tu nombre (máx. {maximo} caracteres): ").strip()
            if not nombre:
                self.vista.mostrar_error(P.mensaje_puntaje_nombre_vacio())
                continue
            if len(nombre) > maximo:
                self.vista.mostrar_error(P.mensaje_puntaje_nombre_largo(maximo, len(nombre)))
                continue
            try:
                registro = self.servicio.registrarPuntaje(nombre)
                print("¡Puntaje registrado!")
            except Exception as e:
                self.vista.mostrar_error(P.mensaje_puntaje_fallido(e))
                return
            self._mostrar_puntajes(registro)
            return

    def _mostrar_puntajes(self, resaltar=None):
        """Muestra la tabla de puntajes; un archivo dañado se informa sin detener el juego."""
        try:
            self.vista.mostrar_puntajes(self.servicio.tablaPuntajes(), resaltar=resaltar)
        except Exception as e:
            self.vista.mostrar_error(P.mensaje_puntajes_ilegibles(e))

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
                print(P.mensaje_sin_salida(accion))
                return "IGNORAR"

            if salida.cerrada:
                if salida.llave:
                    print(P.mensaje_salida_cerrada_con_llave(accion, salida.llave))
                else:
                    print(P.mensaje_salida_cerrada(accion))
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
                print(P.mensaje_sin_enemigos())
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
                        print(P.mensaje_enemigo_invalido())
                        return None
                except ValueError:
                    print(P.mensaje_no_es_numero())
                    return None

            # Validación de vida antes de crear el DTO de ataque
            if objetivo.vida_actual <= 0:
                print(P.mensaje_enemigo_derrotado(objetivo.nombre))
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
                print(P.mensaje_sin_salidas())
                return "IGNORAR"

            # Mostramos únicamente las puertas cerradas
            puertas_cerradas = [
                salida for salida in sala_actual.salidas
                if salida.cerrada
            ]

            if not puertas_cerradas:
                print(P.mensaje_sin_puertas_cerradas())
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
                print(P.mensaje_direccion_vacia())
                return "IGNORAR"

            # Buscamos solamente entre las puertas cerradas mostradas
            salida_encontrada = None
            for salida in puertas_cerradas:
                if getattr(salida, "direccion", "").lower() == direccion:
                    salida_encontrada = salida
                    break

            if not salida_encontrada:
                print(P.mensaje_sin_puerta_cerrada(direccion))
                return "IGNORAR"

            # Validación de llave mediante el servicio
            id_llave_necesaria = salida_encontrada.llave

            if id_llave_necesaria:
                tiene_la_llave = self.servicio.tieneLlave(id_llave_necesaria)

                if not tiene_la_llave:
                    print(P.mensaje_falta_llave(id_llave_necesaria))
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
                print(P.mensaje_sin_objetos())
                return "IGNORAR"
            
            print("\n¿Qué objeto deseas recoger?")
            for i, obj in enumerate(sala_actual.objetos):
                print(f"  [{i+1}] {obj.nombre} (ID: {getattr(obj, 'id', 'N/A')})")
            
            try:
                opcion = int(input("Selecciona el número del objeto: ")) - 1
                if 0 <= opcion < len(sala_actual.objetos):
                    obj_encontrado = sala_actual.objetos[opcion]
                else:
                    print(P.mensaje_objeto_invalido())
                    return "IGNORAR"
            except ValueError:
                print(P.mensaje_no_es_numero())
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
                print(P.mensaje_objeto_rechazado(e))
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
                print(P.mensaje_objeto_rechazado(e))
            return "IGNORAR"

        # 3. USAR EL OBJETO ACTUAL
        elif accion == "usar":
            obj_actual = self.servicio.objetoActualInventario()
            if obj_actual is None:
                print(P.mensaje_inventario_vacio())
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
                print(P.mensaje_inventario_vacio())
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
                print(P.mensaje_inventario_uso())
                return "IGNORAR"
            criterio = partes[1] if len(partes) == 2 else None
            try:
                objetos = self.servicio.vistaInventario(criterio)
            except ValueError as e:
                print(P.mensaje_inventario_rechazado(e))
                return "IGNORAR"
            self.vista.mostrar_inventario(objetos, jugador, criterio)
            return "IGNORAR"
        
        print(P.mensaje_comando_desconocido(accion))
        return None