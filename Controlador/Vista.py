import os

class VistaConsola:
    
    def limpiar_pantalla(self):
        # Limpia la terminal para que se vea limpia como una pantalla de juego
        os.system('cls' if os.name == 'nt' else 'clear')

    def mostrar_juego(self, estado):
        """
        Recibe el diccionario de estado con los DTOs reales 
        y los dibuja ordenadamente en la consola.
        """
        self.limpiar_pantalla()
        
        sala = estado["sala"]
        jugador = estado["jugador"]
        bitacora = estado["bitacora"]

        print("=" * 60)
        print(f"SALA: {sala.nombre.upper()} (ID: {sala.id})")
        print("=" * 60)
        print(f"Último paso registrado en rastro: {sala.ultimo_paso}\n")

        # Mostrar Estado del Jugador (Hereda de ActorDTO)
        print(f"Jugador | Vida Max: {jugador.vida_max} | Ataque: {jugador.ataque} | Defensa: {jugador.defensa} | Velocidad: {jugador.velocidad}")
        print(f"Ubicación actual (Sala ID): {jugador.id_sala_actual}")
        print("-" * 60)

        # Mostrar Enemigos en la sala (Usando EnemigoDTO)
        if sala.enemigos:
            print("Enemigos presentes:")
            for e in sala.enemigos:
                print(f"   - {e.nombre} ({e.comportamiento}) | Vida actual: {e.vida_actual}/{e.vida_max} | Ataque: {e.ataque}")
        else:
            print("La sala está despejada de enemigos.")

        # Mostrar Objetos en el suelo (IDs de catálogo)
        if sala.objetos:
            print("Objetos en el suelo:")
            for obj_id in sala.objetos:
                print(f"   - {obj_id}")
        
        print("-" * 60)

        # Mostrar Salidas disponibles (Iterando sobre el deque de SalidaDTO)
        print("Salidas [Orden: Norte, Sur, Este, Oeste]:")
        for salida in sala.salidas:
            estado_puerta = "Abierta" if not salida.cerrada else f"Cerrada (Requiere llave: {salida.llave})"
            destino_str = f"Destino Sala ID: {salida.sala_destino}" if salida.sala_destino is not None else "Sin salida"
            print(f"   [{salida.direccion.upper()}] -> {destino_str} | {estado_puerta}")

        print("=" * 60)
        print("BITÁCORA DE EVENTOS:")
        for mensaje in bitacora:
            print(f"   > {mensaje}")
        print("=" * 60)