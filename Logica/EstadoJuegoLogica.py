from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import *
from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import JugadorDTO, EnemigoDTO
from DTO.FinPartidaDTO import FinPartidaDTO
from Logica.GestorEventos import GestorEventos
from Logica.ActorLogica import ActorLogica
from Logica.JugadorLogica import JugadorLogica
from DTO.LogPartidaDTO import LogPartidaDTO
from Logica.LogEventos import LogEventos, ReferenciaEvento, RegistroEvento
from Logica.BitacoraLogica import BitacoraLogica
from Logica.RelojVirtual import RelojVirtual
from Logica.RetrocesoLogica import RetrocesoLogica
from DTO.CambioDTO import CambioDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from adaptadores.servicioCripta import ServicioCripta
from DTO.EstadoGuardadoDTO import EstadoGuardadoDTO
from Logica import EstadoGuardadoLogica
class EstadoJuegoLogica:
    def __init__(self,semilla: int = None, cripta: str = None, comunicacion: ServicioCripta | None = None):
        self.tiempoMovimientoJugador = 0
        # Quien arma el juego entrega el servicio de criptas ya listo; al modelo no le importa de dónde saca los datos.
        self.comunicacion = comunicacion
        
        self.iniciado = False
        self.fin = False
        self.motivoFin = None
        self.idCripta = None           # se fija al iniciar o restaurar una partida; None = todavía no hay cripta elegida
        self.precargaInicialHecha = False
        self.registrador_log = None    # opcional: algo con agregar(linea); el modelo solo le avisa cada acción
        
        if(cripta is not None):
            self.iniciarJuego(cripta)

    def exportar_estado(self) -> EstadoGuardadoDTO:
        """Instantánea de la partida en datos simples; no toca archivos ni red."""
        return EstadoGuardadoLogica.exportar(self)

    def restaurar_estado(self, estado: EstadoGuardadoDTO) -> None:
        """Deja la partida como estaba cuando se exportó `estado`. El historial del pergamino empieza vacío."""
        self._exigirServicio()
        EstadoGuardadoLogica.restaurar(self, estado)

    def _exigirServicio(self) -> None:
        if self.comunicacion is None:
            raise ValueError("El juego no tiene un servicio de criptas")

    def iniciarJuego(self,  cripta: str,semilla: int = None):
        if self.iniciado:
            raise ValueError("No se puede iniciar un juego ya iniciado")
        self._exigirServicio()
        if not self.comunicacion.existe_cripta(cripta):
            raise ValueError("No existe la cripta solicitada")
        self.semilla = 0 if semilla is None else semilla
        self.logEventos = LogEventos(self.semilla, cripta)
        self.logEventos.version_cripta = self.comunicacion.version_cripta(cripta)
        self.logEventos.version_catalogo = self.comunicacion.version_catalogo()
        self.logEventosJuego = BitacoraLogica()
        
        cantSalas = self.comunicacion.total_salas(cripta)
        salas = [None] * (cantSalas+1)
        relojvirtual = RelojVirtual()
        retroceso = RetrocesoLogica()
        retroceso.reiniciar()
        retroceso.reloj = relojvirtual
        relojvirtual.retroceso = retroceso
        jugador =self.comunicacion.crear_jugador(cripta)
        self.estadoJuego = EstadoJuego(relojvirtual,jugador,[],[],salas)
        self.gestorEventos = GestorEventos(
            self.estadoJuego.salas,
            jugador,
            self.ingresarEnSala,
            self.semilla,
            obtener_botin=self.comunicacion.objetos_que_suelta,
        )
        self.jugadorLogica = JugadorLogica(jugador,self.semilla,self.gestorEventos.azar)
        self.logEventos.vaciar()
        self.idCripta = cripta
        self.iniciado = True
        self.registrador_log = None
        self.fin = False
        self.motivoFin = None

    def _comprobarFinal(self):
        if self.jugadorLogica.esta_muerto():
            self.fin = True
            self.motivoFin = "El jugador ha muerto"
        elif self.jugadorLogica.estaEnSalaFinal(
            self.comunicacion.obtener_sala_salida(self.idCripta)
        ):
            self.fin = True
            self.motivoFin = "El jugador ha llegado a la sala final"

    def terminado(self):
        return self.fin, (
            self.motivoFin if self.motivoFin is not None else "No ha terminado"
        )

    def reporteSolicitudes(self):
        """Reporte de red de la cripta que se está jugando (§5.1): solicitudes realizadas, presupuesto,
        aciertos y fallos de caché. Solo lee contadores, así que consultarlo no cuesta ninguna solicitud.
        Devuelve None mientras todavía no se haya elegido una cripta."""
        if self.comunicacion is None or self.idCripta is None:
            return None
        return self.comunicacion.reporte(self.idCripta)
        
    def exportar_log(self) -> LogPartidaDTO:
        """Log de reproducción de la partida en datos simples; no toca archivos."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.logEventos.a_dto()

    def repetirPartida(self, log: LogPartidaDTO) -> list[ResultadoEventoDTO]:
        log_original = LogEventos.desde_dto(log)

        if log_original.id_cripta is None:
            raise ValueError("El log no contiene el ID de la cripta")
        if self.iniciado:
            raise ValueError("No se puede repetir una partida durante otra partida")

        self.iniciarJuego(log_original.id_cripta, log_original.semilla)
        try:
            self._verificarVersionesReplay(log_original)
        except ValueError:
            self.iniciado = False
            raise
        self.ingresarEnSala(self.estadoJuego.jugador.id_sala_actual)

        resultados = []
        for registro in log_original.obtener_registros_cronologicos():
            evento = self._crear_evento_repeticion(registro)
            resultados.append(self.accionJugador(evento))

        return resultados

    def _verificarVersionesReplay(self, log: LogEventos) -> None:
        """Solo se reproduce si cripta y catálogo son exactamente los del log (§4.11)."""
        actuales = (
            ("cripta", log.version_cripta, self.logEventos.version_cripta),
            ("catálogo", log.version_catalogo, self.logEventos.version_catalogo),
        )
        for nombre, guardada, actual in actuales:
            if guardada is None or actual is None:
                raise ValueError(
                    f"No se puede garantizar una reproducción fiel: falta la versión de {nombre} "
                    f"(en el log: {guardada or 'desconocida'}, disponible: {actual or 'desconocida'})"
                )
            if guardada != actual:
                raise ValueError(
                    f"No se puede garantizar una reproducción fiel: la versión de {nombre} cambió "
                    f"({guardada} en el log, {actual} disponible)"
                )

    def _crear_evento_repeticion(self, registro: RegistroEvento) -> EventoDTO:
        tipo = registro.tipo_accion
        datos = registro.datos_extra
        actor_registro = registro.actor
        if not isinstance(tipo, str) or not isinstance(datos, list):
            raise ValueError("El registro del log no contiene un evento válido")
        costo = registro.tiempo_ejecucion   # en el log se guarda el costo (o retraso) original del evento
        if not isinstance(costo, int) or isinstance(costo, bool) or costo <= 0:
            raise ValueError("El registro del log no contiene un costo válido")

        jugador = self.estadoJuego.jugador
        if tipo == "MOVER_JUGADOR":
            sala, direccion = self._datos_sala_direccion(datos)
            return EventoDTO(costo, 0, jugador, tipo, [sala, direccion])

        if tipo == "ABRIR_PUERTA":
            sala, direccion = self._datos_sala_direccion(datos)
            return EventoDTO(costo, 0, jugador, tipo, [sala, direccion])

        if tipo == "ATACAR":
            enemigo = self._buscar_enemigo(self._id_referencia(datos, "enemigo"))
            return EventoDTO(costo, 0, jugador, tipo, [enemigo])

        if tipo in {"RECOGER_OBJETO", "USAR_OBJETO"}:
            objeto = self._buscar_objeto(
                self._id_referencia(datos, "objeto"),
                tipo == "USAR_OBJETO",
            )
            return EventoDTO(costo, 0, jugador, tipo, [objeto])

        if tipo == "SOLTAR_OBJETO" or tipo == "ESPERAR":
            return EventoDTO(costo, 0, jugador, tipo, [])

        if tipo in {"ARMAR_TRAMPA", "ACTIVAR_TRAMPA"}:
            id_trampa = self._id_actor(actor_registro, "trampa")
            trampa = self._buscar_trampa(id_trampa)
            sala, = self._datos_sala(datos)
            return EventoDTO(costo, 0, trampa, tipo, [sala])

        if tipo == "CERRAR_PUERTA":
            id_sala = self._id_actor(actor_registro, "sala")
            sala = self.ingresarEnSala(id_sala)
            direccion, = datos
            return EventoDTO(costo, 0, sala, tipo, [direccion])

        raise ValueError(f"No se puede repetir el evento {tipo!r}")

    def _datos_sala_direccion(self, datos: list) -> tuple[SalaDTO, str]:
        if len(datos) != 2 or not isinstance(datos[1], str):
            raise ValueError("El evento requiere una sala y una dirección")
        sala, direccion = datos
        if not isinstance(sala, ReferenciaEvento) or sala.tipo != "sala":
            raise ValueError("El evento no contiene una referencia de sala válida")
        return self.ingresarEnSala(sala.id), direccion

    def _datos_sala(self, datos: list) -> tuple[SalaDTO]:
        if len(datos) != 1:
            raise ValueError("El evento requiere una sala")
        sala = datos[0]
        if not isinstance(sala, ReferenciaEvento) or sala.tipo != "sala":
            raise ValueError("El evento no contiene una referencia de sala válida")
        return (self.ingresarEnSala(sala.id),)

    @staticmethod
    def _id_referencia(datos: list, tipo: str) -> str | int:
        if len(datos) != 1 or not isinstance(datos[0], ReferenciaEvento):
            raise ValueError("El evento no contiene un objetivo válido")
        referencia = datos[0]
        if referencia.tipo != tipo or referencia.id is None:
            raise ValueError(f"El evento no contiene un objetivo de tipo {tipo}")
        return referencia.id

    @staticmethod
    def _id_actor(actor, tipo: str) -> str | int:
        if not isinstance(actor, ReferenciaEvento) or actor.tipo != tipo:
            raise ValueError(f"El evento no contiene un actor de tipo {tipo}")
        if actor.id is None:
            raise ValueError("El actor no contiene un identificador")
        return actor.id

    def _buscar_enemigo(self, id_enemigo: str | int):
        for sala in self.estadoJuego.salas:
            if sala is not None:
                for enemigo in sala.enemigos:
                    if enemigo.id_instancia == id_enemigo:
                        return enemigo
        raise ValueError(f"No se encontró el enemigo {id_enemigo!r}")

    def _buscar_objeto(self, id_objeto: str | int, en_inventario: bool):
        if en_inventario:
            nodo = self.estadoJuego.jugador.inventario.cabeza
            while nodo is not None:
                if nodo.objeto.id_catalogo == id_objeto:
                    return nodo.objeto
                nodo = nodo.siguiente

        for sala in self.estadoJuego.salas:
            if sala is not None:
                for objeto in sala.objetos:
                    if objeto.id_catalogo == id_objeto:
                        return objeto
        raise ValueError(f"No se encontró el objeto {id_objeto!r}")

    def _buscar_trampa(self, id_trampa: str | int):
        for sala in self.estadoJuego.salas:
            if sala is not None:
                for trampa in sala.trampas:
                    if trampa.id_instancia == id_trampa:
                        return trampa
        raise ValueError(f"No se encontró la trampa {id_trampa!r}")

    

    def listarCriptas(self) -> list[str]:
        self._exigirServicio()
        return self.comunicacion.listar_criptas()

    def obtenerIdCripta(self, posicion: int) -> str:
        self._exigirServicio()
        return self.comunicacion.obtener_id_cripta(posicion)
        
    #TODO Este va a recibir: el numero de cripta y partir de eso se comunica con comunicador para saber
    #1. Cuantas salas existen (solo reservar la memoria)
    #2. Crear el reloj virtual
    #3. Preguntar al comuniador por el jugador inicial (JugadorDTO)
    # Este lo asigna a self.estadoJuego
    # Devolver en que sala inicial el jugador
    # ejecuta ingresarEnSala(salainicial) y cargar algunas al rededor para el inicio

    def ingresarEnSala(self, sala: int)-> SalaDTO:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if(sala < 1 or sala >= len(self.estadoJuego.salas)):
            raise ValueError("No existe la sala que se desea consultar")
        if(self.estadoJuego.salas[sala] is not None):
            return self.estadoJuego.salas[sala]
        # El jugador acaba de entrar (o empieza aquí): se trae el contenido por adelantado y en lotes antes de armar la sala.
        # Una sola vez, al inicio, se precarga profundo (3); después el entorno cercano (profundidad 2),
        # y precargar_vecinas únicamente pide las salas que todavía no estaban guardadas. Si la sala la carga un enemigo
        # al desplazarse (no es la del jugador) no se precarga nada para no gastar presupuesto.
        if sala == self.estadoJuego.jugador.id_sala_actual:
            if getattr(self, "precargaInicialHecha", False):
                self.comunicacion.precargar_vecinas(self.idCripta, sala, 2)
            else:
                self.comunicacion.precargar_vecinas(self.idCripta, sala, 3)
                self.precargaInicialHecha = True
        self.estadoJuego.salas[sala] = self.comunicacion.construir_sala(self.idCripta,sala) 
        sala_cargada = self.estadoJuego.salas[sala]
        with self.jugadorLogica.retroceso.sin_registro():
            for enemigo in sala_cargada.enemigos:
                self.estadoJuego.catalogo_enemigos.append(enemigo)
                self.cargarEvento(
                    EventoDTO(
                        100,
                        0,
                        enemigo,
                        "ACCION_ENEMIGO",
                        [self.estadoJuego.jugador]
                    )
                )
        for objeto in sala_cargada.objetos:
            self.estadoJuego.catalogo_objetos.append(objeto)
        return sala_cargada

    #TODO va a revisar la seccion del vector de la memoria
    #si la sala está (no es None) la devuelve
    #si no, se comunica con el comunicador, recibe la sala y la inserta en el vector y la devuelve
    #inicial todos los enemigos de las salas

    def obtenerJugador(self):
        if self.estadoJuego is None:
            return None
        return self.estadoJuego.jugador 
        

    def tieneLlave(self,id_llave : str):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.jugadorLogica.tiene_llave(id_llave)

    def _siguienteAccion(self):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.fin:
            raise ValueError("El juego ha finalizado, no se generan más acciones")
        respuesta = None
        while self.fin is False:
            evento = self.estadoJuego.reloj.desencolar()

            if not evento:
                break

            print(
                f"Evento: {evento.tipo_accion} | "
                f"Tiempo: {evento.tiempo_ejecucion}"
            )
            jugador = self.estadoJuego.jugador
            velocidad_antes = ActorLogica.velocidad_efectiva(jugador)
            accion = self.gestorEventos.procesar_evento(evento)
            if not GestorEventos.es_uso_de_pergamino(evento):
                # Si un efecto (una poción o su vencimiento) cambió la velocidad del jugador, la acción que ya
                # tenía programada conserva el progreso realizado (§2.3). El pergamino ya restaura toda la agenda.
                velocidad_despues = ActorLogica.velocidad_efectiva(jugador)
                if velocidad_despues != velocidad_antes:
                    self.estadoJuego.reloj.reajustar_velocidad(jugador, velocidad_antes, velocidad_despues)
            self._registrarEnBitacora(accion)
            respuesta = accion
            print(accion.mensaje)

            # Entrar a una sala con trampas armadas las activa justo al terminar el movimiento, antes del siguiente evento
            resultados_trampas = []
            if evento.tipo_accion == "MOVER_JUGADOR" and evento.actor is jugador and accion.exito:
                resultados_trampas = self.gestorEventos.activar_trampas(self.estadoJuego.salas[jugador.id_sala_actual])
                for resultado in resultados_trampas:
                    self._registrarEnBitacora(resultado)
                    print(resultado.mensaje)
                if resultados_trampas:
                    mensajes = "\n".join(r.mensaje for r in resultados_trampas)
                    respuesta = ResultadoEventoDTO(accion.exito, f"{accion.mensaje}\n{mensajes}", accion.eventoResultado, accion.puntaje)

            self._comprobarFinal()
            if not self.fin and (
                accion.eventoResultado is not None
            ):
                self.cargarEvento(accion.eventoResultado)
            if not self.fin:
                for resultado in resultados_trampas:
                    if resultado.eventoResultado is not None:
                        self.cargarEvento(resultado.eventoResultado)
            if evento.actor is self.estadoJuego.jugador:
                self._sumarPuntaje(accion.puntaje)
                break

        return respuesta

    def _registrarEnBitacora(self, accion: ResultadoEventoDTO):
        descartado = self.logEventosJuego.agregar_evento(accion)
        self.jugadorLogica.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="BITACORA_AGREGADA",
            objeto_afectado=self.logEventosJuego,
            valor_anterior=descartado,
            elemento=accion,
        )])

    def _sumarPuntaje(self, puntaje: int):
        if not puntaje:
            return
        anterior = self.estadoJuego.puntaje
        self.estadoJuego.puntaje += puntaje
        self.jugadorLogica.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="ACTUALIZAR_PUNTAJE",
            objeto_afectado=self.estadoJuego,
            valor_anterior=anterior,
            valor_nuevo=self.estadoJuego.puntaje,
        )])

    @staticmethod
    def _obtener_id_afectado(evento: EventoDTO) -> str | int | None:
        """Obtiene el identificador del objeto que recibió la acción."""
        if evento.tipo_accion == "ATACAR" and evento.datos_extra:
            afectado = evento.datos_extra[0]
        elif evento.tipo_accion in {"RECOGER_OBJETO", "USAR_OBJETO"} and evento.datos_extra:
            afectado = evento.datos_extra[0]
        elif evento.tipo_accion == "MOVER_JUGADOR" and evento.datos_extra:
            afectado = evento.datos_extra[0]
        elif evento.tipo_accion == "ABRIR_PUERTA" and evento.datos_extra:
            afectado = evento.datos_extra[0]
        else:
            afectado = evento.actor

        for nombre in ("id_instancia", "id_catalogo", "id"):
            identificador = getattr(afectado, nombre, None)
            if identificador is not None:
                return identificador
        return None

        
    
    @staticmethod
    def _intervalo(evento: EventoDTO) -> int:
        """Tiempo que tarda el evento en ocurrir desde el reloj actual.
        Si el actor es el jugador o un enemigo, tiempo_ejecucion trae el COSTO de la acción y el intervalo
        sale de la velocidad del actor (§2.3). Los eventos del entorno (cierre de puerta, trampas,
        vencimiento de efectos) traen el retraso exacto y no dependen de ninguna velocidad."""
        if isinstance(evento.actor, (JugadorDTO, EnemigoDTO)):
            return RelojVirtual.intervalo_por_velocidad(
                evento.tiempo_ejecucion, ActorLogica.velocidad_efectiva(evento.actor)
            )
        return evento.tiempo_ejecucion

    def cargarEvento(self, evento : EventoDTO) -> int:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.estadoJuego.reloj.encolar(self._intervalo(evento),evento.actor,evento.tipo_accion,evento.datos_extra)

    def accionJugador(self, evento: EventoDTO):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        self.tiempoMovimientoJugador = self.cargarEvento(evento)
        respuesta = self._siguienteAccion()
        self.logEventos.registrar_evento(evento)
        if self.registrador_log is not None:
            self.registrador_log.agregar(self.logEventos.cola.accion)
        return respuesta

    def obtenerPuntaje(self) -> int:
        return self.estadoJuego.puntaje

    def finPartida(self) -> FinPartidaDTO:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")

        if not self.fin:
            raise ValueError(
                "No se puede tener el resultado final de una partida si no ha terminado"
            )

        return FinPartidaDTO(
            self.idCripta,
            "1.0",
            self.logEventosJuego.imprimir_mensajes(),
            self.jugadorLogica.enemigos_eliminados(),
            self.estadoJuego.reloj.tiempo_actual,
        )