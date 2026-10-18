
class VistaConsola:
   
   def mostrar_juego(self, jugador, sala_actual, objeto_actual=None, mensajes=None):
        
        print("\n" + "="*50)
        print(f"SALA: {sala_actual.nombre} (ID: {sala_actual.id})")
        print(f"VIDA JUGADOR: {jugador.vida_actual}/{jugador.vida_max}")
        
        print("\n--- SALIDAS ---")
        for salida in sala_actual.salidas:
            if salida.cerrada:
                if salida.llave:
                    estado_puerta = f"CERRADA (Requiere: {salida.llave})"
                else:
                    estado_puerta = "CERRADA"
            else:
                estado_puerta = "Abierta"

            print(
                f"  > {salida.direccion.capitalize()} -> "
                f"Sala {salida.sala_destino} [{estado_puerta}]"
            )
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

        print("\n--- INVENTARIO ---")
        if objeto_actual is not None:
            print(f"  > Objeto Actual: {objeto_actual.nombre} "
                  f"(ID: {getattr(objeto_actual, 'id_catalogo', 'N/A')})")
        else:
            print("  > Objeto Actual: [Inventario vacío]")

        # §4.8 y §10.2: la pantalla muestra únicamente los últimos 20 mensajes del juego
        print("\n--- ÚLTIMOS MENSAJES (máx. 20) ---")
        if mensajes:
            for mensaje in mensajes:
                print(f"  {mensaje}")
        else:
            print("  (sin mensajes)")

   def mostrar_inventario(self, objetos, jugador, criterio=None):
        """Lista de objetos del inventario (§4.5, §10.2): en su orden real o ordenada por `criterio`."""
        orden = "orden real" if criterio is None else f"ordenado por {criterio}"
        print(f"\n--- INVENTARIO ({orden}) ---")
        if not objetos:
            print("  (vacío)")
            return
        for posicion, objeto in enumerate(objetos, start=1):
            equipado = " [equipado]" if objeto is jugador.arma or objeto is jugador.armadura else ""
            print(f"  {posicion}. {objeto.nombre} | peso: {objeto.peso} | valor: {objeto.valor}{equipado}")

   def mostrar_puntajes(self, registros, limite=10, resaltar=None):
        """Tabla de puntajes (§2.12): los `limite` mejores, ya ordenados. `resaltar` marca el registro recién guardado."""
        print("\n" + "=" * 78)
        print("TABLA DE PUNTAJES")
        print("=" * 78)
        if not registros:
            print("Todavía no hay partidas registradas.")
            print("=" * 78)
            return
        print(f"{'#':>3}  {'Nombre':<15}  {'Cripta':<10}  {'Vers.':<6}  {'Acc.':>5}  {'Enem.':>5}  {'Tiempo':>7}  Resultado")
        for puesto, r in enumerate(registros[:limite], start=1):
            marca = "  <-- tú" if r is resaltar or r == resaltar else ""
            resultado = "Victoria" if r.victoria else "Derrota"
            print(f"{puesto:>3}  {r.nombre:<15}  {r.id_cripta:<10}  {r.version_cripta:<6}  "
                  f"{r.acciones_jugador:>5}  {r.enemigos_derrotados:>5}  {r.tiempo_final:>7}  {resultado}{marca}")
        if resaltar is not None and resaltar in registros[limite:]:
            puesto = registros.index(resaltar) + 1
            print(f"  ...\n{puesto:>3}  {resaltar.nombre:<15}  (tu puesto)")
        print("=" * 78)
