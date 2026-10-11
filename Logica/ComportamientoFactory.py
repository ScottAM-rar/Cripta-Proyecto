from Logica.ComportamientoEnemigo import *
from Logica.CompGuardian import ComportamientoGuardian
from Logica.CompErrante import ComportamientoErrante
from Logica.CompRastreador import ComportamientoRastreador
class ComportamientoFactory:

    @staticmethod
    def crearComportamiento(tipo : str)->ComportamientoEnemigo:
        match tipo:
            case "GUARDIAN":
                return ComportamientoGuardian()
            case "ERRANTE": 
                return ComportamientoErrante()
            case "RASTREADOR":
                return ComportamientoRastreador()
            case _:
                raise ValueError(f"El comportamiento '{tipo}' no existe")
