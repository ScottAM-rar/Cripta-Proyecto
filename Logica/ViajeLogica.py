"""Viaje de «ir a» (capacidad 006): lleva al jugador hasta una sala ya explorada por la ruta más barata que CONOCE.

Orquesta pasos del jugador; no tiene reglas de movimiento propias: cada paso es el mismo MOVER_JUGADOR que arma el
controlador, entregado a `accionJugador`, y después `ingresarEnSala` (que activa a los enemigos dormidos, §2.4), como
hace el controlador al empezar cada turno. Así el reloj, la agenda, las trampas, la antorcha, la observación de puertas
(002), el pergamino, el log y los puntos de control son los de siempre (research.md D2).

La ruta sale de `BuscadorRutas` sobre `VistaMapaConocido` (solo salas exploradas y puertas recordadas abiertas): el campo
de costos hacia el destino y `siguiente_paso` dan el desempate de FR-234 (D1). El campo se recalcula solo si cambió
`version_conocimiento` (D3). Sin dict/set/heapq/bisect/collections (principio I); no importa red, disco ni vista.
Contrato: specs/006-ir-a/contracts/viaje-logica.md.
"""
from __future__ import annotations

from DTO.ResultadoViajeDTO import (EN_CURSO, LLEGADO, DETENIDO, RECHAZADO, DESTINO_INEXISTENTE, NO_EXPLORADO,
                                   SIN_RUTA_INICIAL, YA_ESTAS_ALLI, SIN_RUTA, ENEMIGOS_DORMIDOS, ENEMIGO_ACTIVO, DANO,
                                   MUERTE, PERGAMINO, MOVIMIENTO_RECHAZADO, CANCELADO_POR_JUGADOR, FIN_PARTIDA,
                                   ResultadoViajeDTO, mensaje_de)
from DTO.EventoDTO import EventoDTO
from Logica.BuscadorRutas import BuscadorRutas
from Logica.MapaConocido import VistaMapaConocido, EXPLORADA

LIMITE_SIN_COTA = 1 << 62        # sin cota de costo: el campo cubre todo lo conocido


class ViajeLogica:
    def __init__(self, logica) -> None:
        self.logica = logica
        self.buscador = BuscadorRutas()
        self.vista = VistaMapaConocido(logica.mapaConocido)
        self.destino = 0
        self.estado = EN_CURSO
        self.motivo = None
        self.pasos = 0
        self.tiempo = 0
        self.version_vista = -1
        self.recorrido: list[int] = []
        self._reloj_inicial = 0

    # --- orden ---

    def iniciar(self, destino) -> ResultadoViajeDTO:
        """Valida la orden y, si procede, calcula el campo de costos y queda EN_CURSO sin dar ningún paso."""
        logica = self.logica
        conocimiento = logica.mapaConocido
        jugador = logica.estadoJuego.jugador
        self.destino = destino
        self.recorrido = []
        self.pasos = 0
        self.tiempo = 0
        # Las comprobaciones van en este orden y la primera que falla rechaza sin tocar nada (FR-237, FR-238).
        if (isinstance(destino, bool) or not isinstance(destino, int) or not 0 < destino < conocimiento.mapa.tamano
                or not conocimiento.mapa.existe[destino]):
            return self._rechazar(DESTINO_INEXISTENTE)
        if conocimiento.estado_de(destino) != EXPLORADA:
            return self._rechazar(NO_EXPLORADO)
        if destino == jugador.id_sala_actual:
            return self._rechazar(YA_ESTAS_ALLI)
        self._calcular()
        if self.buscador.costo(jugador.id_sala_actual) is None:
            return self._rechazar(SIN_RUTA_INICIAL)
        self._reloj_inicial = logica.estadoJuego.reloj.tiempo_actual
        self.estado = EN_CURSO
        self.motivo = None
        logica._registrarMarcaViaje("IR_A", [destino])       # la orden aceptada queda en el log (FR-252)
        return self._resultado()

    # --- pasos ---

    def avanzar(self) -> ResultadoViajeDTO:
        """Da un paso (o termina el viaje). Un paso es un movimiento normal entregado a `accionJugador`."""
        if self.estado != EN_CURSO:
            return self._resultado()
        logica = self.logica
        jugador = logica.estadoJuego.jugador
        origen = jugador.id_sala_actual
        if logica.fin:
            return self._terminar(DETENIDO, MUERTE if jugador.vida_actual <= 0 else FIN_PARTIDA)
        if not self._hay_ruta(origen):                         # el mapa cambió desde el último paso (FR-239 a FR-241)
            return self._terminar(DETENIDO, SIN_RUTA)          # sin dar el paso: ni tiempo, ni acción, ni registro
        arista = self.buscador.siguiente_paso(origen)          # desempate por menor id (FR-234)
        vida_antes = jugador.vida_actual
        activaciones_antes = logica.activaciones_enemigos
        sala = logica.ingresarEnSala(origen)
        salida = self._salida_de(sala, arista.direccion)
        evento = EventoDTO(salida.costo, 0, jugador, "MOVER_JUGADOR", [sala, salida.direccion])
        respuesta = logica.accionJugador(evento)
        if respuesta.exito is False:                           # no debería ocurrir: lo recordado coincide con lo observado
            return self._terminar(DETENIDO, MOVIMIENTO_RECHAZADO)
        nueva = logica.ingresarEnSala(jugador.id_sala_actual)        # lo que hace el controlador al empezar su turno (§2.4)
        self.recorrido.append(nueva.id)
        self.pasos += 1
        self.tiempo = logica.estadoJuego.reloj.tiempo_actual - self._reloj_inicial
        parada = self._parada(nueva, vida_antes, activaciones_antes)
        if parada is not None:
            return parada
        if not self._hay_ruta(nueva.id):                       # la sala nueva reveló un cambio (p. ej. una puerta cerrada)
            return self._terminar(DETENIDO, SIN_RUTA)
        return self._resultado()

    def ejecutar(self) -> ResultadoViajeDTO:
        """Repite pasos hasta que el viaje deje de estar EN_CURSO."""
        resultado = self._resultado()
        while self.estado == EN_CURSO:
            resultado = self.avanzar()
        return resultado

    def cancelar(self, motivo: str) -> None:
        """Pasa a DETENIDO(motivo). No hace nada si el viaje ya terminó; no recalcula ni da pasos (FR-245)."""
        if self.estado == EN_CURSO:
            self._terminar(DETENIDO, motivo)

    # --- apoyo ---

    def _calcular(self) -> None:
        """Campo de costos hacia el destino sobre el conocimiento actual.

        Si ya había un campo y la ruta que seguía sigue siendo transitable, el costo de lo que queda de esa ruta acota la
        búsqueda (research.md D3, política C): cualquier ruta mejor cuesta menos que ella, y todas sus salas quedan a ese
        costo del destino, así que la decisión es la misma que sin cota. Si la ruta dejó de valer (una puerta se cerró) o es
        el primer cálculo, no hay cota. Se adoptó tras medir en `--bench ir_a` (sección G): sin cota, un recálculo cercano al
        destino costaba más de 5 ms en 20 000 salas."""
        limite = LIMITE_SIN_COTA
        if self.version_vista >= 0:
            restante = self._restante_vigente()
            if restante is not None:
                limite = restante
        self.buscador.distancias_hacia(self.destino, self.vista, limite)
        self.version_vista = self.vista.version_conocimiento

    def _restante_vigente(self):
        """Costo de lo que queda de la ruta del campo anterior bajo el conocimiento actual, o None si dejó de ser transitable.
        Recorre el campo anterior (O(largo de la ruta)) antes de que se reemplace."""
        sala = self.logica.estadoJuego.jugador.id_sala_actual
        total = 0
        while sala != self.destino:
            arista = self.buscador.siguiente_paso(sala)
            if arista is None:
                return None
            total += arista.costo
            sala = arista.destino
        return total

    @staticmethod
    def _salida_de(sala, direccion):
        for salida in sala.salidas:
            if salida.direccion.lower() == direccion:
                return salida
        raise ValueError(f"La sala {sala.id} no tiene salida hacia {direccion}")

    def _parada(self, sala, vida_antes: int, activaciones_antes: int):
        """Evalúa tras un paso, en este orden, si el viaje termina o se detiene (research.md D4). Devuelve el resultado o
        None si el viaje sigue. Solo mira la sala actual: O(enemigos de la sala), sin leer salas no visitadas (FR-248)."""
        logica = self.logica
        jugador = logica.estadoJuego.jugador
        if logica.fin and jugador.vida_actual <= 0:
            return self._terminar(DETENIDO, MUERTE)                          # FR-249c
        if sala.id == self.destino:
            return self._terminar(LLEGADO, None)                             # llegar gana a las demás condiciones
        if logica.fin:
            return self._terminar(DETENIDO, FIN_PARTIDA)
        if logica.activaciones_enemigos > activaciones_antes:
            return self._terminar(DETENIDO, ENEMIGOS_DORMIDOS)               # FR-242, FR-243
        for enemigo in sala.enemigos:
            if enemigo.activo and enemigo.vida_actual > 0:
                return self._terminar(DETENIDO, ENEMIGO_ACTIVO)              # FR-249a
        if jugador.vida_actual < vida_antes:
            return self._terminar(DETENIDO, DANO)                            # FR-249b: trampas, veneno...
        return None

    def _hay_ruta(self, sala: int) -> bool:
        """¿Hay ruta conocida desde `sala`? El campo se reutiliza mientras `version_conocimiento` no cambie: sin cambios en
        el conocimiento el recálculo daría el mismo campo (principio III, research.md D3)."""
        if self.vista.version_conocimiento != self.version_vista:
            self._calcular()
        return self.buscador.costo(sala) is not None

    def _terminar(self, estado: str, motivo) -> ResultadoViajeDTO:
        self.estado = estado
        self.motivo = motivo
        self.logica._registrarMarcaViaje(
            "FIN_IR_A", [estado, "ninguno" if motivo is None else motivo, self.logica.estadoJuego.jugador.id_sala_actual])
        return self._resultado()

    def _rechazar(self, motivo: str) -> ResultadoViajeDTO:
        """La orden no se cumple: no consume tiempo, no escribe en el log y no cuenta como acción (FR-238)."""
        self.estado = RECHAZADO
        self.motivo = motivo
        return self._resultado()

    def _resultado(self) -> ResultadoViajeDTO:
        mensaje = mensaje_de(self.motivo)
        return ResultadoViajeDTO(self.estado, self.motivo, mensaje, self.logica.estadoJuego.jugador.id_sala_actual,
                                 self.pasos, self.tiempo, list(self.recorrido))
