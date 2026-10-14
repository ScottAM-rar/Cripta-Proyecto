from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from DTO.ActorDTO import JugadorDTO
from DTO.EventoDTO import EventoDTO

if __name__ == "__main__":
    servicio = EstadoJuegoServicio()
    resultados = servicio.repetirPartida("pruebasLog.log")
    servicio.guardarLog("repeticion.log")

    for x in resultados:
        print(x.mensaje)