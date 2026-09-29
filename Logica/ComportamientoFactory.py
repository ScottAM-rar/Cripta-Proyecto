from Logica.ComportamientoEnemigo import *
from Logica.CompGuardian import ComportamientoGuardian
from Logica.CompErrante import ComportamientoErrante
class ComportamientoFactory:

    @staticmethod
    def crearComportamiento(tipo : str)->ComportamientoEnemigo:
        match tipo:
            case "GUARDIAN":
                return ComportamientoGuardian()
            case "Errante": 
                return ComportamientoErrante()
