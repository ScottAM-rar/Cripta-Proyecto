from Servicio.EstadoJuegoServicio import EstadoJuegoServicio


if __name__ == "__main__":
    servicio = EstadoJuegoServicio()
    criptas = servicio.listarCriptas()
    print(criptas)
    idCripta = servicio.obtenerIdCripta(1)
    print(idCripta)
    servicio.iniciarJuego(idCripta)
    sala_inicial = servicio.obtenerSala(1)
    print(sala_inicial)
