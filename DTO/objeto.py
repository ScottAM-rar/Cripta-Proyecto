

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Objeto:
    id_catalogo : str
    nombre : str
    peso : int
    valor : int

#Suma un bonus de ataque al ataque base si esta equipada
@dataclass
class Arma(Objeto):
    ataque_bonus: int = 0

#Suma un bonus de defensa a la defensa base si esta equipada
@dataclass
class Armadura(Objeto):
    defensa_bonus: int = 0

#Se consume al usarla, puede curar o aumentar la velocidad de manera temporal, pero no tiene que hacer ambas a la vez
#deje todo junto ya que todavia no he revisado como vendra dado por la api
@dataclass
class Pocion(Objeto):
    cura: int = 0
    modificador_velocidad: int = 0
    duracion: int = 0

@dataclass
class Antidoto(Objeto):
    """Se consume al usarlo y cancela el veneno activo del jugador"""

@dataclass
class Llave(Objeto):
    """Permite abrir puertas cuya llave coincide con su id. No se consume.

    Para Persona 3: confirmar contra el Swagger que valor exacto
    trae el campo `abre`, el motor compara esto contra `Salida.llave` para decidir si una llave
    concreta abre una puerta.
    """

    abre: str = ""

@dataclass
class Antorcha(Objeto):
    """Se consume una unidad de uso al encenderla; permanece encendida
    durante `duracion` unidades virtuales"""

    duracion: int = 0

@dataclass
class PergaminoRetroceso(Objeto):
    """Se consume al usarlo y revierte la última acción del jugador"""