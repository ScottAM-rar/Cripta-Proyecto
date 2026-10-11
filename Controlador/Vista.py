
class VistaConsola:
   
   def mostrar_juego(self, jugador, sala_actual):
        
        print("\n" + "="*50)
        print(f"SALA: {sala_actual.nombre} (ID: {sala_actual.id})")
        print(f"VIDA JUGADOR: {jugador.vida_actual}/{jugador.vida_max}")
        
        print("\n--- SALIDAS ---")
        for salida in sala_actual.salidas:
            estado_puerta = "CERRADA (Requiere llave)" if salida.cerrada else "Abierta"
            print(f"  > {salida.direccion.capitalize()} -> Sala {salida.sala_destino} [{estado_puerta}]")
            
        print("\n--- OBJETOS EN LA SALA ---")
        if sala_actual.objetos:
            for obj in sala_actual.objetos:
                # Verificamos si el objeto es una instancia con atributos DTO
                if hasattr(obj, 'nombre') and hasattr(obj, 'id_catalogo'):
                    print(f"  - {obj.nombre.capitalize()} (ID: {obj.id_catalogo})")
                else:
                    # Por si acaso viene como texto plano
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
                # Verificamos si la trampa tiene un atributo de nombre o id_catalogo
                nombre_trampa = getattr(trampa, 'nombre', None)
                if not nombre_trampa and hasattr(trampa, 'id_catalogo'):
                    # Limpiamos el id_catalogo (ej: 'trp_dardos' -> 'Dardos')
                    nombre_trampa = str(trampa.id_catalogo).replace("trp_", "").replace("_", " ").capitalize()
                elif not nombre_trampa:
                    nombre_trampa = "Trampa desconocida"

                estado_t = "Armada" if getattr(trampa, 'armada', True) else "Desarmada"
                daño = getattr(trampa, 'daño', 0)
                
                print(f"  - {nombre_trampa} [Daño: {daño}] - Estado: {estado_t}")
        else:
            print("  (Sin trampas)")