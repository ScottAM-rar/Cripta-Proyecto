from DTO.ActorDTO import JugadorDTO,EnemigoDTO
from DTO.SalaDTO import SalaDTO
from DTO.Objeto import Objeto
from DTO.ResultadoEventoDTO import ResultadoEventoDTO
from Logica.ActorLogica import ActorLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from DTO.CambioDTO import CambioDTO
import random

class JugadorLogica(ActorLogica):
    def __init__(self,jugador : JugadorDTO, semilla: int = None, azar: random.Random | None = None):
        self.jugador = jugador
        self.semilla = semilla
        # Fuente de azar del modelo (una sola por partida). Si no se la pasan, se crea con la semilla.
        self.azar = azar if azar is not None else random.Random(semilla)
        self.retroceso = RetrocesoLogica()

    def mover_jugador(self, sala_actual: SalaDTO, direccion: str) -> ResultadoEventoDTO:
        respuesta = self._mover(self.jugador, sala_actual, direccion)
        if(respuesta.exito == True):
            self.retroceso.registrar_cambio([
                CambioDTO(
                    tipo_accion="MOVER",
                    objeto_afectado=self.jugador,
                    valor_anterior=sala_actual.id,
                    valor_nuevo=self.jugador.id_sala_actual,
                )
            ])
            respuesta.mensaje = f"El jugador se ha movido a la sala {self.jugador.id_sala_actual}"
        return respuesta

    def esta_muerto(self):
        return self.jugador.vida_actual <= 0

    def estaEnSalaFinal(self, salaFinal: int):
        return self.jugador.id_sala_actual == salaFinal
    def atacarEnemigo(self, enemigo : EnemigoDTO, sala_actual: SalaDTO | None = None,
                      obtener_botin=None) -> ResultadoEventoDTO:
        """`obtener_botin(enemigo)` entrega lo que suelta el enemigo (§2.6); si se pasa junto con la sala, al
        morir el enemigo eso queda en el suelo de la sala dentro de la misma acción (un pergamino lo deshace)."""
        if enemigo.vida_actual <= 0:
            return ResultadoEventoDTO(False, f"El jugador no atacó al enemigo {enemigo.id_instancia} ya que está muerto")
        if enemigo.id_sala_actual != self.jugador.id_sala_actual:
            return ResultadoEventoDTO(False, f"El jugador no puede atacar al enemigo {enemigo.id_instancia}: no está en su misma sala")
        vida_anterior = enemigo.vida_actual
        self._atacar(self.jugador,enemigo,self.azar)
        cambios = [CambioDTO(
            tipo_accion="ACTUALIZAR_VIDA",
            objeto_afectado=enemigo,
            valor_anterior=vida_anterior,
            valor_nuevo=enemigo.vida_actual,
        )]
        mensaje = "El jugador ha atacado al enemigo causando daño"
        if enemigo.vida_actual <= 0 and vida_anterior > 0:
            botin = self.resolver_muerte_enemigo(enemigo, sala_actual, obtener_botin, cambios)
            if obtener_botin is not None and sala_actual is not None:
                mensaje += "." + botin
        self.retroceso.registrar_cambio(cambios)
        return ResultadoEventoDTO(True, mensaje, puntaje=50)

    def resolver_muerte_enemigo(self, enemigo: EnemigoDTO, sala: SalaDTO | None, obtener_botin, cambios: list) -> str:
        """Todo lo que ocurre cuando un enemigo muere, sea cual sea la causa (§2.6): cuenta como derrotado y lo que suelta
        queda en el suelo de su sala. El cuerpo NO se retira de la sala: sigue ahí, con vida 0, para poder mostrarlo.
        Quien detecta la muerte (vida de >0 a 0) llama aquí UNA vez; los cambios se agregan a `cambios` para que el
        pergamino los deshaga junto con la acción. Devuelve el texto del botín para el mensaje."""
        eliminados_anteriores = self.jugador.enemigos_eliminados
        self.jugador.enemigos_eliminados += 1
        cambios.append(CambioDTO(
            tipo_accion="ENEMIGOS_ELIMINADOS",
            objeto_afectado=self.jugador,
            valor_anterior=eliminados_anteriores,
            valor_nuevo=self.jugador.enemigos_eliminados,
        ))
        if obtener_botin is None or sala is None:
            return ""
        return self._soltar_botin(enemigo, sala, obtener_botin, cambios)

    def _soltar_botin(self, enemigo: EnemigoDTO, sala_actual: SalaDTO, obtener_botin, cambios: list) -> str:
        """El enemigo murió: lo que suelta queda en el suelo de la sala. Devuelve el texto para el mensaje."""
        try:
            botin = obtener_botin(enemigo)
        except Exception as error:      # sin red ni disco el combate no se rompe: solo no hay botín
            return f" No se pudo obtener lo que suelta {enemigo.nombre}: {error}"
        if not botin:
            return ""
        sala_actual.objetos.extend(botin)
        cambios.append(CambioDTO(tipo_accion="BOTIN_ENEMIGO", objeto_afectado=sala_actual, elemento=botin))
        return f" {enemigo.nombre} suelta: {', '.join(objeto.nombre for objeto in botin)}."

    def recogerObjeto(self, objeto: Objeto, sala_actual: SalaDTO):
        try:
            if objeto not in sala_actual.objetos:
                raise ValueError("El objeto no se encuentra en la sala actual")
            if (
                self.jugador.inventario.cantidad_actual
                >= self.jugador.inventario.capacidad_maxima
            ):
                raise ValueError(
                    "No se puede agregar el objeto, el inventario está al máximo"
                )
            self.jugador.inventario.agregar_objeto(objeto)
            sala_actual.objetos.remove(objeto)
            self.retroceso.registrar_cambio([
                CambioDTO(
                    tipo_accion="RECOGER_OBJETO",
                    objeto_afectado=self.jugador,
                    valor_anterior=sala_actual.id,
                    elemento=objeto,
                )
            ])

        except ValueError as e:
            return ResultadoEventoDTO(False, str(e))
        return ResultadoEventoDTO(True, f"El jugador ha recogido el objeto {objeto.nombre}",puntaje=15)

    def soltarObjeto(self, salaActual: SalaDTO):
        try:
            if self.jugador.inventario.actual is None:
                raise ValueError("El inventario esta vacio")
            objeto_actual = self.jugador.inventario.actual.objeto
            indice_original = self.jugador.inventario.indice_de_objeto(objeto_actual)
            objeto = self.jugador.inventario.soltar_objeto_actual()
        except ValueError as e:
            return ResultadoEventoDTO(False, str(e))
        salaActual.objetos.append(objeto)
        self.retroceso.registrar_cambio([CambioDTO(
            tipo_accion="SOLTAR_OBJETO",
            objeto_afectado=self.jugador,
            valor_anterior=salaActual.id,
            elemento=objeto,
            indice=indice_original,
        )])
        return ResultadoEventoDTO(True, f"El jugador ha soltado el objeto {objeto.nombre}")
    def tiene_llave(self, id_llave: int) -> bool:
        """Comprueba si el jugador posee en su inventario un objeto llave con el ID dado."""
        nodo = self.jugador.inventario.cabeza
        while nodo is not None:
            if nodo.objeto.id_catalogo == id_llave:
                return True
            nodo = nodo.siguiente
        return False

    def enemigos_eliminados(self):
        return self.jugador.enemigos_eliminados

    
