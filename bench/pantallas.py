"""Pantallas de consola (capacidad 011, constitución VII; contracts/bench-pantallas.md): lo que cuesta construir el texto
de la pantalla de sala y del resumen final, con la ALTERNATIVA DESCARTADA de la decisión D2 (research.md).

  A. Sala con 0, 10 y 100 enemigos (y objetos y trampas en la misma cantidad)
        elegida: lista de líneas + "\\n".join (`Pantallas.texto_sala`)  | descartada: concatenar con `+=` línea a línea
  B. Resumen de fin de partida     elegida: lista + join                | descartada: concatenar con `+=`
  C. Ayuda                         elegida: recorrer la tabla COMANDOS  | descartada: texto fijo escrito a mano (INFORMATIVA)

Criterios duros: en A y B el texto de la elegida es IDÉNTICO al de la descartada y dos construcciones con los mismos datos
dan el mismo texto (FR-311); la sala con 100 enemigos se construye en menos de 20 ms, mediana y máximo (el presupuesto de
un ciclo de eventos, §5.2). La razón de tiempos entre elegida y descartada solo se informa. Las pantallas se construyen
entre dos decisiones del jugador, fuera del ciclo de eventos; `--bench ciclo` se repite aparte para dejar constancia de
que el camino de eventos no cambió. Datos sintéticos deterministas; sin red ni vista; sin estructuras prohibidas.
"""
from __future__ import annotations

import gc

from Controlador import Pantallas as P
from DTO.ActorDTO import EnemigoDTO, JugadorDTO
from DTO.ConocimientoDTO import SalaConocidaDTO, SalidaConocidaDTO
from DTO.Objeto import Objeto
from DTO.SalaDTO import SalaDTO
from DTO.TrampaDTO import Trampa
from bench.medicion import anotar, medir, nota, texto, verificar

SECCION_A = "Pantallas (A): sala con 0, 10 y 100 enemigos, lista + join frente a concatenar con +="
SECCION_B = "Pantallas (B): resumen de fin de partida, lista + join frente a concatenar con +="
SECCION_C = "Pantallas (C): ayuda, recorrer la tabla frente a texto fijo (INFORMATIVA)"
CANTIDADES = (0, 10, 100)
LIMITE_US = 20_000          # 20 ms: el presupuesto de un ciclo de eventos (constitución VII)
REPETICIONES = 30


# ----------------------------------------------------------------------------------------------- datos sintéticos

def _datos_de_sala(cantidad: int):
    jugador = JugadorDTO(80, 100, 10, 5, 100, id_sala_actual=1, antorcha_encendida=True, antorcha_hasta=900)
    enemigos = [EnemigoDTO(vida_actual=30, vida_max=40, ataque=5, defensa=1, velocidad=100, id_instancia=f"e-{i}",
                           tipo="ent_orco", nombre=f"Orco {i}", comportamiento="cazador" if i % 5 == 0 else "errante",
                           activo=i % 2 == 0) for i in range(cantidad)]
    objetos = [Objeto(f"itm_{i}", f"objeto {i}", 1, 1) for i in range(cantidad)]
    trampas = [Trampa(f"t-{i}", f"trp_{i}", 1, 7, 100, i % 2 == 0) for i in range(cantidad)]
    sala = SalaDTO(1, "Entrada", enemigos=enemigos, objetos=objetos, trampas=trampas)
    conocida = SalaConocidaDTO(1, "Entrada", [SalidaConocidaDTO("norte", 100, "abierta", True, 2, "Pasillo"),
                                              SalidaConocidaDTO("este", 250, "cerrada"),
                                              SalidaConocidaDTO("sur", 70, "sin observar"),
                                              SalidaConocidaDTO("oeste", 100, "abierta", False)])
    llaves = [None, "itm_llave_negra", None, None]
    mensajes = [f"Mensaje {i}." for i in range(20)]
    return jugador, sala, conocida, llaves, mensajes


def _datos_de_resumen() -> tuple:
    """(motivo, puntaje, acciones, tiempo, vida_final, salas_exploradas, id_cripta, version, enemigos_derrotados)"""
    return ("El jugador ha llegado a la sala final", 120, 14, 1850, 77, 6, "cripta-01", "v3", 4)


# --------------------------------------------------------------------------- alternativas DESCARTADAS (solo aquí)

def texto_sala_concatenado(jugador, tiempo, sala, sala_conocida, llaves, objeto_actual, mensajes) -> str:
    """Lo mismo que `Pantallas.texto_sala`, pero acumulando en un solo `str` con `+=` (decisión D2, alternativa B)."""
    cuerpo = "=" * P.ANCHO + "\n" + f"SALA: {sala.nombre} (id {sala.id})" + "\n" + "=" * P.ANCHO + "\n"
    cuerpo += "\n--- SALIDAS ---\n"
    for posicion in range(len(sala_conocida.salidas)):
        cuerpo += P._linea_salida(sala_conocida.salidas[posicion], llaves[posicion]) + "\n"
    cuerpo += "\n--- ENEMIGOS ---\n"
    if sala.enemigos:
        for enemigo in sala.enemigos:
            marca = "[cazador] " if enemigo.comportamiento == "cazador" else ""
            estado = "activo" if enemigo.activo else "dormido"
            cuerpo += f"  - {marca}{enemigo.nombre} [{estado}]  vida {enemigo.vida_actual}/{enemigo.vida_max}\n"
    else:
        cuerpo += "  (ninguno)\n"
    cuerpo += "\n--- OBJETOS ---\n"
    if sala.objetos:
        for objeto in sala.objetos:
            nombre, id_catalogo = P._nombre_de(objeto, "itm_")
            cuerpo += f"  - {nombre} (id {id_catalogo})\n"
    else:
        cuerpo += "  (ninguno)\n"
    cuerpo += "\n--- TRAMPAS ---\n"
    if sala.trampas:
        for trampa in sala.trampas:
            nombre, _ = P._nombre_de(trampa, "trp_")
            estado = "armada" if trampa.armada else "desarmada"
            cuerpo += f"  - {nombre} [daño {trampa.daño}] {estado}\n"
    else:
        cuerpo += "  (ninguna)\n"
    cuerpo += "\n--- ESTADO DEL JUGADOR ---\n"
    cuerpo += f"  Vida: {jugador.vida_actual}/{jugador.vida_max}\n  Tiempo: {tiempo}\n"
    cuerpo += (f"  Antorcha: encendida hasta t={jugador.antorcha_hasta}\n" if jugador.antorcha_encendida
               else "  Antorcha: apagada\n")
    cuerpo += "\n--- INVENTARIO ---\n  Objeto actual: (inventario vacío)\n"
    cuerpo += "\n--- ÚLTIMOS MENSAJES (máx. 20) ---\n"
    if mensajes:
        for mensaje in mensajes:
            cuerpo += f"  {mensaje}\n"
    else:
        cuerpo += "  (sin mensajes)\n"
    return cuerpo[:-1]


def texto_fin_partida_concatenado(motivo, puntaje, acciones, tiempo, vida_final, salas_exploradas,
                                  id_cripta, version, enemigos_derrotados) -> str:
    cuerpo = "=" * P.ANCHO + "\nFIN DE LA PARTIDA\n" + "=" * P.ANCHO + "\n"
    cuerpo += f"Motivo: {motivo}\nPuntaje: {puntaje}\nAcciones: {acciones}\nTiempo: {tiempo}\n"
    cuerpo += f"Vida final: {vida_final}\nSalas exploradas: {salas_exploradas}\n" + "=" * P.ANCHO + "\n"
    cuerpo += f"Cripta: {id_cripta} (versión {version}) | Enemigos derrotados: {enemigos_derrotados}"
    return cuerpo


TEXTO_AYUDA_FIJO = "\n".join(
    ["COMANDOS DISPONIBLES"] + [f"  {fila[1]:<32}{fila[2]}" for fila in P.COMANDOS]
    + ["Los comandos no distinguen mayúsculas de minúsculas."])


def texto_ayuda_fijo() -> str:
    """La alternativa descartada de D3: un texto escrito a mano (aquí se arma una vez y se devuelve)."""
    return TEXTO_AYUDA_FIJO


# ------------------------------------------------------------------------------------------------------ secciones

def _sala(filas: list) -> bool:
    cumple = True
    for cantidad in CANTIDADES:
        jugador, sala, conocida, llaves, mensajes = _datos_de_sala(cantidad)
        args = (jugador, 250, sala, conocida, llaves, None, mensajes)
        elegida, descartada = P.texto_sala(*args), texto_sala_concatenado(*args)
        igual = elegida == descartada and elegida == P.texto_sala(*args)
        cumple = verificar(filas, SECCION_A, f"{cantidad:>3} enemigos: el texto de las dos formas es idéntico", igual) and cumple
        gc.collect()
        resultado = medir(lambda: P.texto_sala(*args), repeticiones=REPETICIONES)
        alterna = medir(lambda: texto_sala_concatenado(*args), repeticiones=REPETICIONES)
        anotar(filas, SECCION_A, f"{cantidad:>3} enemigos  elegida: lista + join", resultado)
        anotar(filas, SECCION_A, f"{cantidad:>3} enemigos  descartada: concatenar con +=", alterna)
        nota(filas, SECCION_A, f"    razón descartada / elegida: {alterna[0] / resultado[0]:.2f} (solo informa); "
                               f"{len(elegida.splitlines())} líneas")
        if cantidad == CANTIDADES[-1]:
            ok = resultado[0] < LIMITE_US and resultado[2] < LIMITE_US
            filas.append((SECCION_A, f"    ¿la sala con {cantidad} enemigos < 20 ms (mediana y máximo)?",
                          "CUMPLE" if ok else "NO CUMPLE", f"(mediana {texto(resultado[0])}, máx {texto(resultado[2])})"))
            cumple = ok and cumple
    return cumple


def _resumen(filas: list) -> bool:
    datos = _datos_de_resumen()
    elegida, descartada = P.texto_fin_partida(*datos), texto_fin_partida_concatenado(*datos)
    igual = elegida == descartada and elegida == P.texto_fin_partida(*datos)
    cumple = verificar(filas, SECCION_B, "el texto de las dos formas es idéntico", igual)
    anotar(filas, SECCION_B, "resumen  elegida: lista + join", medir(lambda: P.texto_fin_partida(*datos), repeticiones=REPETICIONES))
    anotar(filas, SECCION_B, "resumen  descartada: concatenar con +=",
           medir(lambda: texto_fin_partida_concatenado(*datos), repeticiones=REPETICIONES))
    return cumple


def _ayuda(filas: list) -> bool:
    cumple = verificar(filas, SECCION_C, "la ayuda armada desde la tabla es igual al texto fijo", P.texto_ayuda() == texto_ayuda_fijo())
    anotar(filas, SECCION_C, f"ayuda ({len(P.COMANDOS)} comandos)  elegida: recorrer la tabla", medir(P.texto_ayuda, repeticiones=REPETICIONES))
    anotar(filas, SECCION_C, "ayuda  descartada: texto fijo", medir(texto_ayuda_fijo, repeticiones=REPETICIONES))
    nota(filas, SECCION_C, "    el texto fijo es más rápido, pero se desactualiza: nada obliga a que coincida con los comandos reales")
    return cumple


def ejecutar(filas: list) -> bool:
    """Devuelve False si el texto de una forma difiere del de la otra o si la sala con 100 enemigos supera 20 ms."""
    cumple_sala = _sala(filas)
    cumple_resumen = _resumen(filas)
    cumple_ayuda = _ayuda(filas)
    return cumple_sala and cumple_resumen and cumple_ayuda
