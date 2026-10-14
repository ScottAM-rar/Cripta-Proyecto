from unittest import case

from collections.abc import Callable
from DTO.EventoDTO import EventoDTO
from DTO.ActorDTO import *
from DTO.SalaDTO import *
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from DTO.EstadoJuegoDTO import EstadoJuego
from DTO.Objeto import Objeto
from DTO.TrampaDTO import Trampa
from Logica.JugadorLogica import JugadorLogica
from Logica.EnemigosLogica import EnemigoLogica
from Logica.SalasLogica import SalaLogica
from Logica.TrampaLogica import TrampaLogica# from Logica.RetrocesoLogica import RetrocesoLogica
from Logica.ObjetoLogica import ObjetoLogica
from Logica.PergaminoLogica import PergaminoLogica
from DTO.CambioDTO import CambioDTO
#Aquí van a ir TODOS los eventos que se pueden manejar, para hacer un acción se va a consultar aquí


class GestorEventos:

    def __init__(self, salas : list[SalaDTO],jugador: JugadorDTO, cargar_sala: Callable[[int],SalaDTO], semilla: int = None
    ):
        #EnemigosLogica: enemigos_logica: 
        
        self.salas = salas
        self.cargar_sala = cargar_sala
        # Inyección de dependencias de la capa de lógica
        self.jugador_logica = JugadorLogica(jugador, semilla)
        self.pergamino_logica = PergaminoLogica(
            self.jugador_logica.retroceso,
            salas,
        )
        self.objeto_logica = ObjetoLogica(jugador, self.pergamino_logica)
        self.salas_logica = SalaLogica(None)
        self.enemigo_logica = EnemigoLogica(None,semilla)

    def procesar_evento(self, evento: EventoDTO, estado_juego: EstadoJuego | None = None) -> ResultadoEventoDTO:
        """ENRUTADOR, REVISA EL EVENTO Y LO MANDA A RESOLVER DONDE SEA CONVENIENTE"""

        if not isinstance(evento, EventoDTO):
            raise TypeError("El evento debe ser una instancia de EventoDTO")
        if not isinstance(evento.tipo_accion, str) or not evento.tipo_accion:
            raise ValueError("El evento debe tener un tipo de acción no vacío")
        if not isinstance(evento.tiempo_ejecucion, int) or evento.tiempo_ejecucion < 0:
            raise ValueError("El tiempo de ejecución debe ser un entero no negativo")
        if not isinstance(evento.datos_extra, list):
            raise TypeError("Los datos extra del evento deben estar en una lista")

        jugador = self.jugador_logica.jugador
        if jugador is None:
            raise ValueError("El gestor no tiene un jugador configurado")

        if evento.actor is jugador:
            if not isinstance(jugador.id_sala_actual, int):
                raise TypeError("La sala actual del jugador debe ser un entero")
            if jugador.id_sala_actual < 0 or jugador.id_sala_actual >= len(self.salas):
                raise ValueError("La sala actual del jugador no existe")
            if self.salas[jugador.id_sala_actual] is None:
                raise ValueError("La sala actual del jugador no está cargada")
            self.salas_logica.sala = self.salas[jugador.id_sala_actual]
            self.salas_logica.actualizarTiempo(evento.tiempo_ejecucion)

        match evento.tipo_accion:
            
            case "MOVER_JUGADOR":
                # Datos extra: [sala_actual, direccion]
                self._validar_actor_jugador(evento)
                self._validar_cantidad_datos(evento, 2)
                sala_actual: SalaDTO = evento.datos_extra[0]
                direccion: str = evento.datos_extra[1]
                self._validar_sala(sala_actual)
                self._validar_direccion(direccion)
                res = self.jugador_logica.mover_jugador(
                    sala_actual, direccion
                )
                if res.exito == True:
                    self.cargar_sala(jugador.id_sala_actual)
                return res 
            
            case "RECOGER_OBJETO":
                #Datos extra: [objeto]
                self._validar_actor_jugador(evento)
                self._validar_cantidad_datos(evento, 1)
                objeto: Objeto = evento.datos_extra[0]
                if not isinstance(objeto, Objeto):
                    raise TypeError("El objeto a recoger debe ser una instancia de Objeto")
                sala_actual = self.salas[jugador.id_sala_actual]
                return self.jugador_logica.recogerObjeto(objeto, sala_actual)

            case "SOLTAR_OBJETO":
                self._validar_actor_jugador(evento)

                jugador = self.jugador_logica.jugador
                sala = self.salas[jugador.id_sala_actual]

                if sala is None:
                    raise ValueError("La sala actual del jugador no está cargada")

                return self.jugador_logica.soltarObjeto(sala)
            case "ATACAR":
                # Datos extra: [objetivo]
                self._validar_cantidad_datos(evento, 1)
                objetivo: ActorDTO = evento.datos_extra[0]
                atacante: ActorDTO = evento.actor

                # Si el atacante es el jugador
                if isinstance(atacante, JugadorDTO):
                    if atacante is not jugador:
                        raise ValueError("El atacante jugador no pertenece a esta partida")
                    if not isinstance(objetivo, EnemigoDTO):
                        raise TypeError("El objetivo del jugador debe ser un enemigo")
                    return self.jugador_logica.atacarEnemigo(objetivo)

                # Si el atacante es un enemigo
                elif isinstance(atacante, EnemigoDTO):
                    if not isinstance(objetivo, JugadorDTO):
                        raise TypeError("El objetivo del enemigo debe ser un jugador")
                    self.enemigo_logica.setEnemigo(atacante)
                    return self.enemigo_logica.atacarJugador(objetivo)

                raise TypeError("El atacante debe ser un jugador o un enemigo")

            
            case "ABRIR_PUERTA":
                #Datos Adicionales [Sala, Direccion]
                self._validar_actor_jugador(evento)
                self._validar_cantidad_datos(evento, 2)
                sala: SalaDTO
                direccion: str
                sala,direccion = evento.datos_extra
                self._validar_sala(sala)
                self._validar_direccion(direccion)
                self.salas_logica.sala = sala
                salida = self.salas_logica._obtener_salida(Direccion(direccion))
                cerrada_anterior = salida.cerrada if salida is not None else None
                resultado = self.salas_logica.intentarAbrirPuerta(jugador,direccion)
                if resultado.exito:
                    self.jugador_logica.retroceso.nueva_accion()
                    self.jugador_logica.retroceso.registrar_cambio([CambioDTO(
                        tipo_accion="CAMBIAR_PUERTA",
                        objeto_afectado=salida,
                        valor_anterior=cerrada_anterior,
                        valor_nuevo=salida.cerrada,
                    )])
                return resultado

            case "CERRAR_PUERTA":
                self._validar_cantidad_datos(evento, 1)

                if not isinstance(evento.actor, SalaDTO):
                    raise TypeError("El actor de CERRAR_PUERTA debe ser una sala")

                direccion: str = evento.datos_extra[0]
                self._validar_direccion(direccion)

                self.salas_logica.sala = evento.actor
                salida = self.salas_logica._obtener_salida(Direccion(direccion))
                cerrada_anterior = salida.cerrada if salida is not None else None
                resultado = self.salas_logica.cerrarPuerta(direccion)
                if resultado.exito:
                    self.jugador_logica.retroceso.registrar_cambio([CambioDTO(
                        tipo_accion="CAMBIAR_PUERTA",
                        objeto_afectado=salida,
                        valor_anterior=cerrada_anterior,
                        valor_nuevo=salida.cerrada,
                    )])
                return resultado

            case "ACCION_ENEMIGO":
                #Datos Adicionales [Jugador] (se necesitan también las salas pero estas se sacan del estado de juego para evitar desfases)
                if not isinstance(evento.actor, EnemigoDTO):
                    raise TypeError("El actor de ACCION_ENEMIGO debe ser un enemigo")
                sala_enemigo = evento.actor.id_sala_actual
                self._validar_cantidad_datos(evento, 1)
                jugador = evento.datos_extra[0]
                if not isinstance(jugador, JugadorDTO):
                    raise TypeError("El objetivo de ACCION_ENEMIGO debe ser un jugador")
                if jugador is not self.jugador_logica.jugador:
                    raise ValueError("El jugador del evento no pertenece a esta partida")
                vida_jugador_anterior = jugador.vida_actual
                vida_enemigo_anterior = evento.actor.vida_actual
                sala_anterior = evento.actor.id_sala_actual
                self.enemigo_logica.setEnemigo(evento.actor)
                res =  self.enemigo_logica.decidirAccion(jugador,self.salas)
                if evento.actor.id_sala_actual != sala_enemigo:
                    self.cargar_sala(evento.actor.id_sala_actual).enemigos.append(evento.actor)
                cambios = []
                if evento.actor.id_sala_actual != sala_anterior:
                    cambios.append(CambioDTO(
                        tipo_accion="MOVER",
                        objeto_afectado=evento.actor,
                        valor_anterior=sala_anterior,
                        valor_nuevo=evento.actor.id_sala_actual,
                    ))
                if jugador.vida_actual != vida_jugador_anterior:
                    cambios.append(CambioDTO(
                        tipo_accion="ACTUALIZAR_VIDA",
                        objeto_afectado=jugador,
                        valor_anterior=vida_jugador_anterior,
                        valor_nuevo=jugador.vida_actual,
                    ))
                if evento.actor.vida_actual != vida_enemigo_anterior:
                    cambios.append(CambioDTO(
                        tipo_accion="ACTUALIZAR_VIDA",
                        objeto_afectado=evento.actor,
                        valor_anterior=vida_enemigo_anterior,
                        valor_nuevo=evento.actor.vida_actual,
                    ))
                if cambios:
                    self.jugador_logica.retroceso.registrar_cambio(cambios[:2])
                return res

            case "ARMAR_TRAMPA":
                self._validar_trampa(evento)
                self._validar_cantidad_datos(evento, 1)
                trampa: Trampa = evento.actor
                salaTrampa = evento.datos_extra[0]
                self._validar_sala_trampa(salaTrampa, trampa)
                armada_anterior = trampa.armada
                logica = TrampaLogica(trampa)
                resultado = logica.rearmar(salaTrampa)
                if resultado.exito:
                    self.jugador_logica.retroceso.registrar_cambio([CambioDTO(
                        tipo_accion="CAMBIAR_TRAMPA",
                        objeto_afectado=trampa,
                        valor_anterior=armada_anterior,
                        valor_nuevo=trampa.armada,
                    )])
                return resultado

            case "ACTIVAR_TRAMPA":
                self._validar_trampa(evento)
                trampa: Trampa = evento.actor
                if len(evento.datos_extra) == 0:
                    salaTrampa = self._obtener_sala_trampa(trampa)
                elif len(evento.datos_extra) == 1:
                    salaTrampa = evento.datos_extra[0]
                    self._validar_sala_trampa(salaTrampa, trampa)
                else:
                    raise ValueError(
                        "La acción ACTIVAR_TRAMPA acepta cero o un dato extra"
                    )
                vidas_anteriores = [(jugador, jugador.vida_actual)]
                vidas_anteriores.extend(
                    (enemigo, enemigo.vida_actual) for enemigo in salaTrampa.enemigos
                )
                armada_anterior = trampa.armada
                logica = TrampaLogica(trampa)
                resultado = logica.activar(self.jugador_logica.jugador,salaTrampa)
                cambios = []
                for actor, vida_anterior in vidas_anteriores:
                    if actor.vida_actual != vida_anterior:
                        cambios.append(CambioDTO(
                            tipo_accion="ACTUALIZAR_VIDA",
                            objeto_afectado=actor,
                            valor_anterior=vida_anterior,
                            valor_nuevo=actor.vida_actual,
                        ))
                if trampa.armada != armada_anterior and len(cambios) < 2:
                    cambios.append(CambioDTO(
                        tipo_accion="CAMBIAR_TRAMPA",
                        objeto_afectado=trampa,
                        valor_anterior=armada_anterior,
                        valor_nuevo=trampa.armada,
                    ))
                if cambios:
                    self.jugador_logica.retroceso.registrar_cambio(cambios)
                return resultado
            case "USAR_OBJETO":
                self._validar_actor_jugador(evento)
                self._validar_cantidad_datos(evento, 1)

                objeto = evento.datos_extra[0]

                if not isinstance(objeto, Objeto):
                    raise TypeError("El objeto a usar debe ser una instancia de Objeto")

                return self.objeto_logica.usar_objeto(objeto)
            case "REVERTIR_MODIFICADOR_VELOCIDAD":
                self._validar_cantidad_datos(evento, 1)
                velocidad_anterior = self.jugador_logica.jugador.modificador_velocidad
                self.objeto_logica.revertir_modificador_velocidad(evento.datos_extra[0])
                self.jugador_logica.retroceso.registrar_cambio([CambioDTO(
                    tipo_accion="REVERTIR_MODIFICADOR_VELOCIDAD",
                    objeto_afectado=self.jugador_logica.jugador,
                    valor_anterior=velocidad_anterior,
                    valor_nuevo=self.jugador_logica.jugador.modificador_velocidad,
                )])
                return ResultadoEventoDTO(True, "El modificador de velocidad ha terminado.")

            case "APAGAR_ANTORCHA":
                self._validar_cantidad_datos(evento, 0)
                antorcha_anterior = self.jugador_logica.jugador.antorcha_encendida
                self.objeto_logica.apagar_antorcha()
                self.jugador_logica.retroceso.registrar_cambio([CambioDTO(
                    tipo_accion="APAGAR_ANTORCHA",
                    objeto_afectado=self.jugador_logica.jugador,
                    valor_anterior=antorcha_anterior,
                    valor_nuevo=self.jugador_logica.jugador.antorcha_encendida,
                )])
                return ResultadoEventoDTO(True, "La antorcha se ha apagado.")
            case "ESPERAR":
                return ResultadoEventoDTO(True, "El jugador ha esperado en su turno")

            case _:
                raise ValueError(f"Tipo de acción no soportado: {evento.tipo_accion}")

    def _validar_actor_jugador(self, evento: EventoDTO) -> None:
        if evento.actor is not self.jugador_logica.jugador:
            raise ValueError("El evento debe pertenecer al jugador de esta partida")

    def _validar_cantidad_datos(self, evento: EventoDTO, cantidad: int) -> None:
        if len(evento.datos_extra) != cantidad:
            raise ValueError(
                f"La acción {evento.tipo_accion} requiere exactamente "
                f"{cantidad} dato(s) extra"
            )

    def _validar_sala(self, sala: SalaDTO) -> None:
        if not isinstance(sala, SalaDTO):
            raise TypeError("La sala del evento debe ser una instancia de SalaDTO")
        if not isinstance(sala.id, int):
            raise TypeError("El ID de la sala debe ser un entero")
        if sala.id < 0 or sala.id >= len(self.salas):
            raise ValueError("La sala del evento no existe")
        if self.salas[sala.id] is None:
            raise ValueError("La sala del evento no está cargada")
        if self.salas[sala.id] is not sala:
            raise ValueError("La sala del evento no corresponde a la sala almacenada")

    def _validar_direccion(self, direccion: str) -> None:
        if not isinstance(direccion, str):
            raise TypeError("La dirección debe ser una cadena de texto")
        try:
            Direccion(direccion)
        except ValueError as error:
            raise ValueError(f"Dirección no válida: {direccion}") from error

    def _validar_trampa(self, evento: EventoDTO) -> None:
        if not isinstance(evento.actor, Trampa):
            raise TypeError("El actor del evento debe ser una instancia de Trampa")
        if not isinstance(evento.actor.id_sala, int):
            raise TypeError("El ID de sala de la trampa debe ser un entero")

    def _validar_sala_trampa(self, sala: SalaDTO, trampa: Trampa) -> None:
        self._validar_sala(sala)
        if sala.id != trampa.id_sala:
            raise ValueError("La sala del evento no corresponde a la sala de la trampa")

    def _obtener_sala_trampa(self, trampa: Trampa) -> SalaDTO:
        if trampa.id_sala < 0 or trampa.id_sala >= len(self.salas):
            raise ValueError("La sala de la trampa no existe")
        sala = self.salas[trampa.id_sala]
        if sala is None:
            raise ValueError("La sala de la trampa no está cargada")
        self._validar_sala_trampa(sala, trampa)
        return sala

                


                




                

            

            
                