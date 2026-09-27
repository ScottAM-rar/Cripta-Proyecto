from DTO.SalaDTO import SalaDTO, SalidaDTO
from DTO.ActorDTO import JugadorDTO, EnemigoDTO
from DTO.EventoDTO import EventoDTO
from collections import deque

class MotorJuegoStub:
    """Simula el núcleo del juego usando los DTOs oficiales del equipo"""
    def __init__(self):
        # 1. Creamos una salida de ejemplo usando SalidaDTO
        salidas_ejemplo = deque([
            SalidaDTO(direccion="norte", sala_destino=2, cerrada=False, llave=None),
            SalidaDTO(direccion="sur", sala_destino=0, cerrada=True, llave="itm_llave_hierro"),
            SalidaDTO(direccion="este", sala_destino=3, cerrada=False, llave=None),
            SalidaDTO(direccion="oeste", sala_destino=0, cerrada=False, llave=None)
        ], maxlen=4)

        # 2. Creamos un enemigo real usando EnemigoDTO
        enemigo_ejemplo = EnemigoDTO(
            vida_max=50,
            ataque=12,
            defensa=5,
            velocidad=10,
            id_instancia="t-01",
            tipo="trp_goblin",
            nombre="Goblin Guardián",
            comportamiento="guardian",
            vida_actual=50
        )

        # 3. Armamos la SalaDTO oficial
        self.sala_actual = SalaDTO(
            id=1,
            nombre="Vestíbulo Oscuro",
            salidas=salidas_ejemplo,
            enemigos=[enemigo_ejemplo],
            objetos=["itm_antorcha", "itm_pocion"],
            trampas=[],
            ultimo_paso=0
        )

        # 4. Creamos el JugadorDTO oficial
        self.jugador = JugadorDTO(
            vida_max=100,
            ataque=15,
            defensa=10,
            velocidad=12,
            inventario_max=5,
            id_sala_actual=1
        )

        self.mensajes_bitacora = [
            "Bienvenido a Cripta.",
            "Has entrado al Vestíbulo Oscuro.",
            "Escuchas ruidos extraños al norte."
        ]
        self._contador_secuencia = 0

    def obtener_estado_actual(self):
        return {
            "sala": self.sala_actual,
            "jugador": self.jugador,
            "bitacora": self.mensajes_bitacora[-20:]
        }

    def ejecutar_accion(self, accion, parametro=None):
        self._contador_secuencia += 1
        
        nuevo_evento = EventoDTO(
            tiempo_ejecucion=10,
            id_secuencia=self._contador_secuencia,
            actor=self.jugador,
            tipo_accion=accion.upper(),
            datos_extra=[parametro] if parametro else []
        )

        if accion == "moverse":
            # Buscamos en el deque de salidas la dirección correspondiente
            for salida in self.sala_actual.salidas:
                if salida.direccion == parametro:
                    if not salida.cerrada:
                        self.mensajes_bitacora.append(f"Te moviste hacia el {parametro} (Evento ID: {nuevo_evento.id_secuencia}).")
                        return True
                    else:
                        self.mensajes_bitacora.append(f"La puerta al {parametro} está cerrada. Requiere: {salida.llave}.")
                        return False
            self.mensajes_bitacora.append(f"No hay salida hacia el {parametro}.")
            return False
            
        elif accion == "atacar":
            self.mensajes_bitacora.append(f"Atacaste al enemigo (Evento ID: {nuevo_evento.id_secuencia}).")
            return True
            
        return False