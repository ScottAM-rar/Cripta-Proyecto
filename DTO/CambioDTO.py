from dataclasses import dataclass


@dataclass
class CambioDTO:
    """Representa un cambio individual que puede revertirse."""

    tipo_accion: str #Accion que se realizó, como "ATACAR", "MOVER", "RECOGER_OBJETO", etc.
    objeto_afectado: object | None = None # Quien hizo la accion, como un jugador o enemigo
    atributo: str | None = None # El atributo del objeto afectado que se modificó, como "vida_actual", "id_sala_actual", etc.
    valor_anterior: object | None = None # El valor del atributo antes de la acción, como 100 para vida_actual o 1 para id_sala_actual.
    valor_nuevo: object | None = None # El valor del atributo después de la acción, como 80 para vida_actual o 2 para id_sala_actual.
    cantidad: int | None = None #
    elemento: object | None = None # 
    indice: int | None = None # 
    tiempo_ejecucion: int = 0 # Tiempo en el que se ejecutó la acción.