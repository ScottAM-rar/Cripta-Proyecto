"""Resultado de un viaje de «ir a» (capacidad 006): datos simples que cruzan Servicio → Controlador → Vista.
Contrato: specs/006-ir-a/data-model.md. El modelo no conoce la vista; el texto de cada motivo es el que se muestra."""
from dataclasses import dataclass, field

# Estados del viaje
EN_CURSO = "EN_CURSO"
LLEGADO = "LLEGADO"
DETENIDO = "DETENIDO"
RECHAZADO = "RECHAZADO"

# Motivos (rechazo o detención)
DESTINO_INEXISTENTE = "DESTINO_INEXISTENTE"
NO_EXPLORADO = "NO_EXPLORADO"
SIN_RUTA_INICIAL = "SIN_RUTA_INICIAL"
YA_ESTAS_ALLI = "YA_ESTAS_ALLI"
SIN_RUTA = "SIN_RUTA"
ENEMIGOS_DORMIDOS = "ENEMIGOS_DORMIDOS"
ENEMIGO_ACTIVO = "ENEMIGO_ACTIVO"
DANO = "DANO"
MUERTE = "MUERTE"
PERGAMINO = "PERGAMINO"
MOVIMIENTO_RECHAZADO = "MOVIMIENTO_RECHAZADO"
CANCELADO_POR_JUGADOR = "CANCELADO_POR_JUGADOR"
FIN_PARTIDA = "FIN_PARTIDA"      # la partida terminó (sin morir) antes de llegar al destino

# Texto de cada motivo para el jugador
MENSAJES = (
    (DESTINO_INEXISTENTE, "No existe esa sala."),
    (NO_EXPLORADO, "Esa sala no está explorada."),
    (SIN_RUTA_INICIAL, "No hay ruta conocida hasta esa sala."),
    (YA_ESTAS_ALLI, "Ya estás en esa sala."),
    (SIN_RUTA, "Una puerta que recordabas abierta está cerrada y no hay otra ruta conocida."),
    (ENEMIGOS_DORMIDOS, "Entraste a una sala con enemigos dormidos y se despertaron."),
    (ENEMIGO_ACTIVO, "Un enemigo activo está en la sala."),
    (DANO, "Recibiste daño."),
    (MUERTE, "Moriste durante el viaje."),
    (PERGAMINO, "El pergamino canceló el viaje."),
    (MOVIMIENTO_RECHAZADO, "No se pudo dar el siguiente paso."),
    (CANCELADO_POR_JUGADOR, "Viaje cancelado."),
    (FIN_PARTIDA, "La partida terminó."),
)


def mensaje_de(motivo) -> str:
    """Texto fijo de un motivo ('' si no hay motivo)."""
    for clave, texto in MENSAJES:
        if clave == motivo:
            return texto
    return ""


@dataclass
class ResultadoViajeDTO:
    estado: str = EN_CURSO
    motivo: str | None = None
    mensaje: str = ""
    sala_final: int = 0
    pasos: int = 0
    tiempo: int = 0
    recorrido: list = field(default_factory=list)
