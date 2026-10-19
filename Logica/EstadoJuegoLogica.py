from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import *
from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import JugadorDTO, EnemigoDTO
from DTO.FinPartidaDTO import FinPartidaDTO
from Logica.GestorEventos import GestorEventos, PERIODO_REGENERACION
from Logica.ActorLogica import ActorLogica
from Logica.JugadorLogica import JugadorLogica
from DTO.LogPartidaDTO import LogPartidaDTO
from Logica.LogEventos import LogEventos, ReferenciaEvento, RegistroEvento, TIPOS_CURSOR_INVENTARIO
from Logica.BitacoraLogica import BitacoraLogica
from Logica.RelojVirtual import RelojVirtual
from Logica.RetrocesoLogica import RetrocesoLogica
from DTO.CambioDTO import CambioDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.FuenteCripta import FuenteCripta
from DTO.EstadoGuardadoDTO import EstadoGuardadoDTO
from Logica import EstadoGuardadoLogica

class EstadoJuegoLogica:
    def __init__(self,semilla: int = None, cripta: str = None, comunicacion: FuenteCripta | None = None):
        self.tiempoMovimientoJugador = 0
        self.accionesJugador = 0       # acciones del jugador que consumieron tiempo virtual (§2.12)
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
        self._actualizarFichasEnUso()

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
        self.gestorEventos.reloj = relojvirtual
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
            if registro.tipo_accion in TIPOS_CURSOR_INVENTARIO:
                self._repetirMovimientoDeCursor(registro.tipo_accion)
                continue
            evento = self._crear_evento_repeticion(registro)
            resultado = self.accionJugador(evento)
            if resultado.exito is False:     # el log solo guarda acciones aceptadas: si ahora se rechaza, ya no es fiel
                raise ValueError(
                    f"La reproducción no es fiel: {evento.tipo_accion} fue rechazada ({resultado.mensaje})"
                )
            resultados.append(resultado)

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

        if tipo == "SOLTAR_OBJETO":
            if not datos:       # los logs anteriores no guardaban el objeto: se suelta el del cursor
                return EventoDTO(costo, 0, jugador, tipo, [])
            objeto = self._buscar_objeto(self._id_referencia(datos, "objeto"), True)
            return EventoDTO(costo, 0, jugador, tipo, [objeto])

        if tipo == "ESPERAR":
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
            actual = self.estadoJuego.jugador.inventario.actual
            if actual is not None and actual.objeto.id_catalogo == id_objeto:
                return actual.objeto        # con ids repetidos manda el cursor, que es lo que eligió el jugador
            nodo = self.estadoJuego.jugador.inventario.cabeza
            while nodo is not None:
                if nodo.objeto.id_catalogo == id_objeto:
                    return nodo.objeto
                nodo = nodo.siguiente

        # Recoger solo ocurre en la sala del jugador: se busca ahí primero para no tomar un objeto con el mismo id
        # de otra sala (la reproducción divergería).
        sala_actual = self.estadoJuego.salas[self.estadoJuego.jugador.id_sala_actual]
        if sala_actual is not None:
            for objeto in sala_actual.objetos:
                if objeto.id_catalogo == id_objeto:
                    return objeto
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
        if(self.estadoJuego.salas[sala] is None):
            self._cargarSala(sala)
        sala_cargada = self.estadoJuego.salas[sala]
        if sala == self.estadoJuego.jugador.id_sala_actual:
            if sala_cargada.ultimo_paso < 0 and self.accionesJugador == 0:
                sala_cargada.ultimo_paso = self.estadoJuego.reloj.tiempo_actual
            self._activarEnemigos(sala_cargada)
            self._actualizarFichasEnUso()
        return sala_cargada

    def fichasEnUso(self) -> list[str]:
        """Ids de catálogo referenciados por instancias activas (§4.4), uno por instancia: enemigos vivos y
        activos, los dormidos de la sala actual, el inventario y los objetos y trampas del suelo de la sala actual."""
        ids: list[str] = []
        jugador = self.estadoJuego.jugador
        sala_actual = None
        if 0 <= jugador.id_sala_actual < len(self.estadoJuego.salas):
            sala_actual = self.estadoJuego.salas[jugador.id_sala_actual]
        for enemigo in self.estadoJuego.catalogo_enemigos:
            if enemigo.vida_actual > 0 and (enemigo.activo or enemigo.id_sala_actual == jugador.id_sala_actual):
                ids.append(enemigo.tipo)
        nodo = jugador.inventario.cabeza
        while nodo is not None:
            ids.append(nodo.objeto.id_catalogo)
            nodo = nodo.siguiente
        if sala_actual is not None:
            for objeto in sala_actual.objetos:
                ids.append(objeto.id_catalogo)
            for trampa in sala_actual.trampas:
                ids.append(trampa.id_catalogo)
        return ids

    def _actualizarFichasEnUso(self) -> None:
        """Le dice a la fuente qué fichas no puede liberar. El modelo no conoce la caché."""
        fijar = getattr(self.comunicacion, "fijar_fichas_en_uso", None)
        if fijar is not None:
            fijar(self.fichasEnUso())

    def _cargarSala(self, sala: int) -> None:
        """Incorpora el contenido de la sala al modelo. Cargar una sala NO activa a sus enemigos (§2.4)."""
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
        for enemigo in sala_cargada.enemigos:
            self.estadoJuego.catalogo_enemigos.append(enemigo)
        for objeto in sala_cargada.objetos:
            self.estadoJuego.catalogo_objetos.append(objeto)

    def _activarEnemigos(self, sala: SalaDTO) -> None:
        """Activa a los enemigos dormidos (y vivos) de `sala`, en orden ascendente de id de instancia, para que reciban
        números de secuencia deterministas (§2.4). Su primera acción se programa desde el reloj actual con costo 100.
        Un enemigo que ya está activo no se toca. Dentro de una acción del jugador, la activación se puede deshacer."""
        pendientes = [e for e in sala.enemigos if not e.activo and e.vida_actual > 0]
        while pendientes:
            menor = pendientes[0]
            for candidato in pendientes:
                if candidato.id_instancia < menor.id_instancia:
                    menor = candidato
            pendientes.remove(menor)
            menor.activo = True
            self.jugadorLogica.retroceso.registrar_cambio([CambioDTO(
                tipo_accion="ACTIVAR_ENEMIGO",
                objeto_afectado=menor,
                valor_anterior=False,
                valor_nuevo=True,
            )])
            self.cargarEvento(EventoDTO(100, 0, menor, "ACCION_ENEMIGO", [self.estadoJuego.jugador]))
            if menor.regeneracion > 0:      # §2.10: recupera vida cada PERIODO_REGENERACION mientras esté activo y vivo
                self.cargarEvento(EventoDTO(PERIODO_REGENERACION, 0, None, "REGENERAR", [menor]))

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

    def _avanzarHastaProximoTurno(self) -> None:
        """Ejecuta, en orden, los eventos que ocurren mientras el jugador espera su próximo turno (§2.3, §2.5).
        Termina sacando el evento TURNO_JUGADOR: el reloj queda en el instante en que el jugador vuelve a decidir.
        Si la partida termina por el camino (el jugador muere), se corta ahí: el reloj se queda en ese instante y el
        turno NO se saca, así el tiempo final es el de la muerte y los eventos posteriores no se ejecutan."""
        reloj = self.estadoJuego.reloj
        jugador = self.estadoJuego.jugador
        while not self.fin:
            siguiente = reloj.siguiente()
            if siguiente is None:
                break
            if siguiente.tipo_accion == "TURNO_JUGADOR":
                reloj.desencolar()
                return
            evento = reloj.desencolar()
            velocidad_antes = ActorLogica.velocidad_efectiva(jugador)
            accion = self.gestorEventos.procesar_evento(evento)
            # Si un efecto (el vencimiento de una poción) cambió la velocidad del jugador, su turno ya programado
            # conserva el progreso realizado (§2.3).
            velocidad_despues = ActorLogica.velocidad_efectiva(jugador)
            if velocidad_despues != velocidad_antes:
                reloj.reajustar_velocidad(jugador, velocidad_antes, velocidad_despues)
            if accion.mensaje:              # los eventos silenciosos (p. ej. regenerar con la vida llena) no ensucian la bitácora
                self._registrarEnBitacora(accion)
            self._comprobarFinal()
            if not self.fin and accion.eventoResultado is not None:
                self.cargarEvento(accion.eventoResultado)

    def _registrarEnBitacora(self, accion: ResultadoEventoDTO):
        descartado = self.logEventosJuego.agregar_evento(accion)
        self.jugadorLogica.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="BITACORA_AGREGADA",
            objeto_afectado=self.logEventosJuego,
            valor_anterior=descartado,
            elemento=accion,
        )])

    def ultimosMensajes(self) -> list[str]:
        """Los mensajes de la bitácora de la partida (máximo 20, §4.8), del más viejo al más reciente.
        Solo lee: no reproduce ni modifica nada."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return [r.mensaje for r in self.logEventosJuego.obtener_eventos() if r.mensaje]

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
        """El jugador decide en el instante actual del reloj y su acción ocurre AHORA (§2.3). El costo (que viene en
        evento.tiempo_ejecucion) solo sirve para programar su próximo turno. Después se ejecuta todo lo que pasa antes
        de ese turno. Una acción rechazada no cambia nada ni consume tiempo (Apéndice B)."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.fin:
            raise ValueError("El juego ha finalizado, no se generan más acciones")
        costo = evento.tiempo_ejecucion
        if not isinstance(costo, int) or isinstance(costo, bool) or costo <= 0:
            raise ValueError("El costo de la acción del jugador debe ser un entero positivo")
        reloj = self.estadoJuego.reloj
        jugador = self.estadoJuego.jugador

        accion = self.gestorEventos.procesar_evento(evento)
        self._registrarEnBitacora(accion)
        if accion.exito is False:
            return accion                       # rechazada: sin tiempo, sin historial y fuera del log
        if GestorEventos.es_uso_de_pergamino(evento):
            self._registrarAccionEnLog(evento)  # el retroceso no consume tiempo, pero sí es parte de la partida
            self.tiempoMovimientoJugador = reloj.tiempo_actual
            self._actualizarFichasEnUso()
            return accion

        respuesta = accion
        resultados_trampas = []
        # Entrar a una sala con trampas armadas las activa justo al terminar el movimiento, antes del siguiente evento
        if evento.tipo_accion == "MOVER_JUGADOR" and accion.exito:
            resultados_trampas = self.gestorEventos.activar_trampas(self.estadoJuego.salas[jugador.id_sala_actual])
            for resultado in resultados_trampas:
                self._registrarEnBitacora(resultado)
            if resultados_trampas:
                mensajes = "\n".join(r.mensaje for r in resultados_trampas)
                respuesta = ResultadoEventoDTO(accion.exito, f"{accion.mensaje}\n{mensajes}", accion.eventoResultado, accion.puntaje)

        self.accionesJugador += 1
        self._sumarPuntaje(accion.puntaje)
        self._comprobarFinal()
        if not self.fin:
            if accion.eventoResultado is not None:
                self.cargarEvento(accion.eventoResultado)
            for resultado in resultados_trampas:
                if resultado.eventoResultado is not None:
                    self.cargarEvento(resultado.eventoResultado)
            # El próximo turno usa la velocidad con que el jugador termina esta acción (p. ej. la que dio una poción)
            intervalo = RelojVirtual.intervalo_por_velocidad(costo, ActorLogica.velocidad_efectiva(jugador))
            reloj.programar(intervalo, jugador, "TURNO_JUGADOR", [])
            self._avanzarHastaProximoTurno()
        self.tiempoMovimientoJugador = reloj.tiempo_actual
        self._registrarAccionEnLog(evento)
        self._actualizarFichasEnUso()
        return respuesta

    def vistaInventario(self, criterio: str | None = None) -> list:
        """Objetos del inventario en su orden real (criterio=None) o en una vista ordenada por "peso", "valor" o "nombre"
        (§4.5). Solo lee: no cambia el orden real, el cursor, el reloj ni el log."""
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        inventario = self.estadoJuego.jugador.inventario
        if criterio is None:
            return inventario.listar_objetos()
        return inventario.obtener_vista_ordenada(criterio)

    def siguienteObjetoInventario(self) -> bool:
        """Mueve el cursor del inventario al siguiente objeto. False si ya estaba en el último; ValueError si está vacío.
        No consume tiempo ni entra al retroceso, pero queda en el log: usar y soltar actúan sobre el objeto del cursor."""
        return self._moverCursorInventario(siguiente=True)

    def anteriorObjetoInventario(self) -> bool:
        """Mueve el cursor del inventario al objeto anterior. False si ya estaba en el primero; ValueError si está vacío."""
        return self._moverCursorInventario(siguiente=False)

    def _moverCursorInventario(self, siguiente: bool) -> bool:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.fin:
            raise ValueError("El juego ha finalizado, no se generan más acciones")
        inventario = self.estadoJuego.jugador.inventario
        movido = inventario.siguiente_objeto() if siguiente else inventario.anterior_objeto()
        if movido:      # si el cursor no se movió el estado no cambió: no hay nada que repetir
            self.logEventos.registrar_cursor("SIGUIENTE_OBJETO" if siguiente else "ANTERIOR_OBJETO")
            if self.registrador_log is not None:
                self.registrador_log.agregar(self.logEventos.cola.accion)
        return movido

    def _repetirMovimientoDeCursor(self, tipo_accion: str) -> None:
        movido = self.siguienteObjetoInventario() if tipo_accion == "SIGUIENTE_OBJETO" else self.anteriorObjetoInventario()
        if not movido:
            raise ValueError(f"El log pide {tipo_accion} pero el cursor no se pudo mover: la reproducción no es fiel")

    def _registrarAccionEnLog(self, evento: EventoDTO) -> None:
        self.logEventos.registrar_evento(evento)
        if self.registrador_log is not None:
            self.registrador_log.agregar(self.logEventos.cola.accion)

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
            self.comunicacion.version_cripta(self.idCripta) if self.comunicacion is not None else None,
            self.accionesJugador,
            self.jugadorLogica.enemigos_eliminados(),
            self.estadoJuego.reloj.tiempo_actual,
            not self.jugadorLogica.esta_muerto(),
        )