
class VistaConsola:
    def mostrar_juego(self, estado_juego, sala_actual):
        print("\n" + "="*50)
        print(f"SALA: {sala_actual.nombre} (ID: {sala_actual.id})")
        print(f"VIDA JUGADOR: {estado_juego.jugador.vida_actual}/{estado_juego.jugador.vida_max}")
        
        print("\n--- SALIDAS ---")
        for salida in sala_actual.salidas:
            estado_puerta = "CERRADA (Requiere llave)" if salida.cerrada else "Abierta"
            print(f"  > {salida.direccion.capitalize()} -> Sala {salida.sala_destino} [{estado_puerta}]")
            
        print("\n--- OBJETOS EN LA SALA ---")
        if sala_actual.objetos:
            for obj in sala_actual.objetos:
                # Limpiamos el prefijo 'itm_' y formateamos el texto bonito
                nombre_limpio = str(obj).replace("itm_", "").replace("_", " ").capitalize()
                print(f"  - {nombre_limpio} (ID: {obj})")
        else:
            print("  (No hay objetos)")
            
        print("\n--- ENEMIGOS ---")
        if sala_actual.enemigos:
            for enm in sala_actual.enemigos:
                print(f"  - {enm.nombre} (Vida: {enm.vida_actual}/{enm.vida_max})")
        else:
            print("  (No hay enemigos)")
            
        print("\n--- TRAMPAS ---")
        if sala_actual.trampas:
            for trampa in sala_actual.trampas:
                # Mostramos los atributos limpios de tu DTO Trampa
                estado_t = "Armada" if trampa.armada else "Desarmada"
                print(f"  - {trampa.id_catalogo.capitalize()} [Daño: {trampa.daño}] - Estado: {estado_t}")
        else:
            print("  (Sin trampas)")
        print("="*50)