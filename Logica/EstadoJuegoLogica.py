from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.SalaDTO import *
from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import JugadorDTO
from DTO.FinPartidaDTO import FinPartidaDTO
from Logica.GestorEventos import GestorEventos
from Logica.JugadorLogica import JugadorLogica
from Logica.LogEventos import LogEventos, ReferenciaEvento, RegistroEvento
from Logica.BitacoraLogica import BitacoraLogica
from Logica.RelojVirtual import RelojVirtual
from Logica.RetrocesoLogica import RetrocesoLogica
from DTO.CambioDTO import CambioDTO
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from adaptadores.cache import CacheLRU
from adaptadores.cliente_http import ClienteCripta
from adaptadores.servicioCripta import ServicioCripta
from adaptadores.PersistenciaPartida import PersistenciaPartida
class EstadoJuegoLogica:
    def __init__(self,semilla: int = None, cripta: str = None):
        self.tiempoMovimientoJugador = 0
        self.comunicacion = self._crearComunicacion()
        
        self.iniciado = False
        self.fin = False
        self.motivoFin = None
        
        if(cripta is not None):
            self.iniciarJuego(cripta)

    @staticmethod
    def _crearComunicacion() -> ServicioCripta:
        return ServicioCripta(ClienteCripta("https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"),
                              CacheLRU(25))

    def __getstate__(self):
        estado = self.__dict__.copy()
        estado.pop("comunicacion", None)
        return estado

    def __setstate__(self, estado):
        self.__dict__.update(estado)
        self.comunicacion = self._crearComunicacion()

    def _enlazarCallbacks(self):
        self.gestorEventos.cargar_sala = self.ingresarEnSala

    def guardarPartida(self, nombre_archivo: str) -> None:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if self.fin:
            raise ValueError("No se puede guardar una partida que ya terminó")
        PersistenciaPartida.guardar(nombre_archivo, self)

    def cargarPartida(self, nombre_archivo: str) -> None:
        cargado = PersistenciaPartida.cargar(nombre_archivo)
        if not isinstance(cargado, EstadoJuegoLogica) or not cargado.iniciado:
            raise ValueError("El archivo no contiene una partida válida")
        estado = cargado.__dict__.copy()
        estado["comunicacion"] = self.comunicacion
        self.__dict__.clear()
        self.__dict__.update(estado)
        self._enlazarCallbacks()

    def iniciarJuego(self,  cripta: str,semilla: int = None,):
        if self.iniciado:
            raise ValueError("No se puede iniciar un juego ya iniciado")
        if not self.comunicacion.existe_cripta(cripta):
            raise ValueError("No existe la cripta solicitada")
        self.semilla = 0 if semilla is None else semilla
        self.logEventos = LogEventos(self.semilla, cripta)
        self.logEventosJuego = BitacoraLogica()
        
        cantSalas = self.comunicacion.total_salas(cripta)
        #TODO obtener version de la cripta
        salas = [None] * cantSalas
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
        )
        self.jugadorLogica = JugadorLogica(jugador,self.semilla)
        self.logEventos.vaciar()
        self.idCripta = cripta
        self.iniciado = True
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
        
    def repetirPartida(self, archivo: str) ->list[ResultadoEventoDTO]:
        log_original = LogEventos()
        log_original.cargar_log(archivo)

        if log_original.id_cripta is None:
            raise ValueError("El log no contiene el ID de la cripta")
        if self.iniciado:
            raise ValueError("No se puede repetir una partida durante otra partida")

        self.iniciarJuego(log_original.id_cripta, log_original.semilla)
        self.ingresarEnSala(self.estadoJuego.jugador.id_sala_actual)

        resultados = []
        for registro in log_original.obtener_registros_cronologicos():
            evento = self._crear_evento_repeticion(registro)
            resultados.append(self.accionJugador(evento))

        return resultados

    def _crear_evento_repeticion(self, registro: RegistroEvento) -> EventoDTO:
        tipo = registro.tipo_accion
        datos = registro.datos_extra
        actor_registro = registro.actor
        if not isinstance(tipo, str) or not isinstance(datos, list):
            raise ValueError("El registro del log no contiene un evento válido")

        jugador = self.estadoJuego.jugador
        if tipo == "MOVER_JUGADOR":
            sala, direccion = self._datos_sala_direccion(datos)
            return EventoDTO(100, 0, jugador, tipo, [sala, direccion])

        if tipo == "ABRIR_PUERTA":
            sala, direccion = self._datos_sala_direccion(datos)
            return EventoDTO(100, 0, jugador, tipo, [sala, direccion])

        if tipo == "ATACAR":
            enemigo = self._buscar_enemigo(self._id_referencia(datos, "enemigo"))
            return EventoDTO(100, 0, jugador, tipo, [enemigo])

        if tipo in {"RECOGER_OBJETO", "USAR_OBJETO"}:
            objeto = self._buscar_objeto(
                self._id_referencia(datos, "objeto"),
                tipo == "USAR_OBJETO",
            )
            return EventoDTO(100, 0, jugador, tipo, [objeto])

        if tipo == "SOLTAR_OBJETO" or tipo == "ESPERAR":
            return EventoDTO(100, 0, jugador, tipo, [])

        if tipo in {"ARMAR_TRAMPA", "ACTIVAR_TRAMPA"}:
            id_trampa = self._id_actor(actor_registro, "trampa")
            trampa = self._buscar_trampa(id_trampa)
            sala, = self._datos_sala(datos)
            return EventoDTO(100, 0, trampa, tipo, [sala])

        if tipo == "CERRAR_PUERTA":
            id_sala = self._id_actor(actor_registro, "sala")
            sala = self.ingresarEnSala(id_sala)
            direccion, = datos
            return EventoDTO(100, 0, sala, tipo, [direccion])

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
        return self.comunicacion.listar_criptas()

    def obtenerIdCripta(self, posicion: int) -> str:
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
        if(sala < 0 or sala >= len(self.estadoJuego.salas)):
            raise ValueError("No existe la sala que se desea consultar")
        if(self.estadoJuego.salas[sala] is not None):
            return self.estadoJuego.salas[sala]
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
            for trampa in sala_cargada.trampas:
                self.cargarEvento(EventoDTO(50, 0, trampa, "ACTIVAR_TRAMPA", [sala_cargada]))
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
            accion = self.gestorEventos.procesar_evento(evento)
            self._registrarEnBitacora(accion)
            respuesta = accion
            print(accion.mensaje)

            self.comprobarFinal()
            if not self.fin and (
                accion.eventoResultado is not None
            ):
                self.cargarEvento(accion.eventoResultado)
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

        
    
    def cargarEvento(self, evento : EventoDTO) -> int:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        return self.estadoJuego.reloj.encolar(evento.tiempo_ejecucion,evento.actor,evento.tipo_accion,evento.datos_extra)

    def accionJugador(self, evento: EventoDTO):
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        self.tiempoMovimientoJugador = self.cargarEvento(evento)
        respuesta = self._siguienteAccion()
        self.logEventos.registrar_evento(evento)
        return respuesta

    def guardarLog(self, nombre_archivo: str) -> None:
        if not self.iniciado:
            raise ValueError("El juego no ha sido iniciado")
        if not self.fin:
            raise ValueError(
                "No se puede guardar el log si la partida no ha terminado"
            )
        self.logEventos.guardar_log(nombre_archivo)

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