
from __future__ import annotations
from typing import TYPE_CHECKING
from Controlador.Pantallas import texto_error, texto_fin_partida, texto_sala
if TYPE_CHECKING:
    from DTO.ResumenEstadoDTO import ResumenEstadoDTO


class VistaConsola:

   def mostrar_advertencias(self, advertencias):
        """Datos inválidos de la cripta que se corrigieron al leerlos (costos de salida, rangos de cazador)."""
        for advertencia in advertencias:
            print(f"AVISO: {advertencia}")
   
   def mostrar_reporte_verificacion(self, lineas):
        """Reporte de resolubilidad al iniciar una partida nueva (capacidad 011, FR-301): solo imprime las líneas recibidas."""
        for linea in lineas:
            print(linea)

   def mostrar_aviso(self, texto):
        """Un aviso de una línea (el de `--forzar` o el de verificación no disponible), con el prefijo AVISO si no lo trae."""
        print(texto if texto.startswith("AVISO:") else f"AVISO: {texto}")

   def mostrar_juego(self, jugador, sala_actual, sala_conocida, objeto_actual=None, mensajes=None, tiempo=None, llaves=None):
        """Pantalla de sala (FR-306): imprime lo que arma `Pantallas.texto_sala`, siempre con las mismas secciones y el mismo
        orden. No decide ni calcula nada: `sala_conocida` trae las salidas (FR-219), `llaves` la llave que pide cada salida
        cerrada (la resuelve el controlador) y `tiempo` el instante del reloj, ya calculado por el modelo."""
        print(texto_sala(jugador, tiempo, sala_actual, sala_conocida, llaves, objeto_actual, mensajes))

   def mostrar_fin_partida(self, motivo, puntaje, acciones, tiempo, vida_final, salas_exploradas,
                            id_cripta, version, enemigos_derrotados):
        """Resumen de fin de partida (FR-307): imprime lo que arma `Pantallas.texto_fin_partida`."""
        print(texto_fin_partida(motivo, puntaje, acciones, tiempo, vida_final, salas_exploradas,
                                id_cripta, version, enemigos_derrotados))

   def mostrar_ayuda(self, texto):
        """Lista de comandos (FR-309), tal como llega de `Pantallas.texto_ayuda`."""
        print(texto)

   def mostrar_error(self, texto):
        """Un rechazo o error (FR-310), tal como llega del catálogo de `Pantallas`."""
        print(texto)

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

   def mostrar_viaje(self, resultado):
        """Resultado de «ir a» (capacidad 006, contracts/comando-ir-a.md §3): solo imprime lo que viene en `resultado`
        (ResultadoViajeDTO). Un rechazo es una sola línea; un viaje terminado, su resumen."""
        if resultado.estado == "RECHAZADO":
            print(texto_error(resultado.mensaje, "Escribe 'mapa' para ver las salas que conoces."))
            return
        if resultado.estado == "LLEGADO":
            print(f"Llegaste a la sala {resultado.sala_final} tras {resultado.pasos} pasos (tiempo {resultado.tiempo}).")
            return
        if resultado.mensaje:
            print(resultado.mensaje)
        print(f"Te detuviste en la sala {resultado.sala_final} tras {resultado.pasos} pasos (tiempo {resultado.tiempo}).")

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
