from Servicio.EstadoJuegoServicio import EstadoJuegoServicio

if __name__ == "__main__":
    servicio = EstadoJuegoServicio()
    resultados = servicio.repetirPartida("pruebasLog")

    for x in resultados:
        print(x.mensaje)