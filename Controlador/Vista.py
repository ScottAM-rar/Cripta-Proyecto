
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from DTO.ResumenEstadoDTO import ResumenEstadoDTO


class VistaConsola:

   def mostrar_advertencias(self, advertencias):
        """Datos inválidos de la cripta que se corrigieron al leerlos (costos de salida, rangos de cazador)."""
        for advertencia in advertencias:
            print(f"AVISO: {advertencia}")
   
   def mostrar_juego(self, jugador, sala_actual, sala_conocida, objeto_actual=None, mensajes=None):
        """`sala_conocida`: la sala actual en el formato del conocimiento del jugador (SalaConocidaDTO). Las salidas salen
        SOLO de ahí (FR-219): el destino lleva nombre únicamente si está explorado y nunca se muestra el id ni el nombre de
        una sala avistada. El resto (objetos, enemigos, trampas) es contenido de la sala actual, que el jugador ve."""

        print("\n" + "="*50)
        print(f"SALA: {sala_actual.nombre} (ID: {sala_actual.id})")
        print(f"VIDA JUGADOR: {jugador.vida_actual}/{jugador.vida_max}")

        print("\n--- SALIDAS ---")
        for salida in sala_conocida.salidas:
            if salida.puerta == "cerrada":
                llave = None
                for real in sala_actual.salidas:         # la llave que pide una puerta de la sala actual es contenido de la sala
                    if real.direccion == salida.direccion:
                        llave = real.llave
                estado_puerta = f"CERRADA (Requiere: {llave})" if llave else "CERRADA"
            elif salida.puerta == "abierta":
                estado_puerta = "Abierta"
            else:
                estado_puerta = "Sin observar"
            destino = salida.destino_nombre if salida.destino_explorado else "sala sin explorar"

            print(
                f"  > {salida.direccion.capitalize()} -> "
                f"{destino} [{estado_puerta}] costo {salida.costo}"
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
                marca = "[CAZADOR] " if enm.comportamiento == "cazador" else ""
                print(f"  - {marca}{enm.nombre} (Vida: {enm.vida_actual}/{enm.vida_max})")
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

   def mostrar_mapa_conocido(self, mapa):
        """Mapa conocido (FR-216, FR-217, FR-219): solo lo que viene en `mapa` (MapaConocidoDTO). Las salas exploradas, en el
        orden recibido; el destino de una salida con nombre si está explorado y «sala sin explorar» si no."""
        print("\n" + "=" * 20 + " MAPA CONOCIDO " + "=" * 20)
        print(f"Salas exploradas: {len(mapa.salas)}   (estás en la sala marcada con *)")
        for sala in mapa.salas:
            marca = "*" if sala.id == mapa.sala_actual else " "
            print(f" {marca} {sala.nombre} (id {sala.id})")
            for salida in sala.salidas:
                if salida.destino_explorado:
                    destino = f"{salida.destino_nombre} (id {salida.destino_id})"
                else:
                    destino = "sala sin explorar"
                print(f"     {salida.direccion:<6} -> {destino:<34} costo {salida.costo:<5} {salida.puerta}")
        print("=" * 55)

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

   def mostrar_historia(self, resumen: ResumenEstadoDTO) -> None:
        """Presenta el estado histórico de forma estructurada según FR-431 y el contrato CLI."""
        print("\n" + "=" * 50)
        print(f"ESTADO HISTÓRICO: Instante <{resumen.instante}> | Acción #{resumen.acciones_jugador}")
        print("=" * 50)
        print(f"SALA: {resumen.id_sala_jugador}")
        print(f"VIDA: {resumen.vida_jugador}")
        print(f"ESTADÍSTICAS: Ataque: {resumen.ataque_jugador} | Defensa: {resumen.defensa_jugador} | Velocidad: {resumen.velocidad_jugador}")

        print("\n--- INVENTARIO ---")
        llaves_txt = ", ".join(resumen.inventario_llaves) if resumen.inventario_llaves else "Ninguna"
        objetos_txt = ", ".join(resumen.inventario_objetos) if resumen.inventario_objetos else "Ninguno"
        print(f"  Llaves: {llaves_txt}")
        print(f"  Objetos: {objetos_txt}")

        print("\n--- EFECTOS ACTIVOS ---")
        efectos_txt = ", ".join(resumen.efectos_activos) if resumen.efectos_activos else "Ninguno"
        print(f"  {efectos_txt}")

        print("\n--- ENEMIGOS EN LA SALA ---")
        if resumen.enemigos_sala:
            for inst_id, nombre, vida in resumen.enemigos_sala:
                print(f"  - {nombre} (ID: {inst_id}, Vida: {vida})")
        else:
            print("  No había enemigos en esta sala")
        print("=" * 50)
