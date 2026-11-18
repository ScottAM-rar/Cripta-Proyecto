"""Texto de las pantallas de consola (capacidad 011; contracts/pantallas.md).

Todas las funciones de este módulo son PURAS: reciben datos ya listos (DTO ya creados o valores simples), devuelven un
`str` y no imprimen, no leen el servicio ni el modelo y no calculan reglas del juego. Así el mismo texto se compara en las
pruebas sin capturar la salida estándar, y dos llamadas con los mismos datos devuelven el mismo texto (FR-311).
Texto plano en español, sin colores ni secuencias de control. No importa `Servicio` ni `Logica` (principio IV) ni usa
`dict`/`set` como índice ni ordena (principio I): la ayuda y la validación salen de una sola lista de tuplas.
"""
from __future__ import annotations

ANCHO = 50
PROMPT = "¿Qué deseas hacer? (escribe 'ayuda' para ver los comandos): "

# (nombre o alias separados por «|», sintaxis, descripción). Es la ÚNICA lista de comandos: la ayuda la recorre y la
# validación de sintaxis la busca (research D3). Sin dos filas con el mismo nombre.
COMANDOS = (
    ("norte|sur|este|oeste", "norte | sur | este | oeste", "Moverte por esa salida; gasta el costo de la salida."),
    ("atacar", "atacar", "Atacar a un enemigo de la sala (si hay varios, eliges uno)."),
    ("abrir", "abrir", "Abrir una puerta cerrada de la sala (pide la dirección)."),
    ("recoger", "recoger", "Recoger un objeto de la sala (eliges de la lista)."),
    ("usar", "usar", "Usar el objeto actual del inventario."),
    ("soltar", "soltar", "Soltar el objeto actual en la sala."),
    ("siguiente|sig", "siguiente (o sig)", "Pasar al siguiente objeto del inventario."),
    ("anterior|ant", "anterior (o ant)", "Volver al objeto anterior del inventario."),
    ("esperar", "esperar", "Dejar pasar el tiempo sin hacer nada."),
    ("inventario", "inventario [peso|valor|nombre]", "Ver el inventario, en su orden o ordenado."),
    ("mapa", "mapa", "Ver las salas que conoces (no gasta tiempo)."),
    ("ir", "ir a <id de sala>", "Viajar a una sala ya explorada por la ruta más barata."),
    ("historia", "historia <t> | historia #k", "Ver el estado en el instante t o justo antes de tu acción k."),
    ("ayuda", "ayuda", "Mostrar esta lista de comandos."),
    ("salir", "salir", "Salir de la partida (te pregunta si quieres guardarla)."),
)
# Comandos que siguen valiendo cuando la partida ya terminó.
COMANDOS_POST_PARTIDA = ("historia", "ayuda", "salir")

_COLUMNA_SINTAXIS = 32


def _alias(fila) -> list[str]:
    return fila[0].split("|")


def buscar_comando(termino: str):
    """La fila de `COMANDOS` cuyo nombre o alias es `termino` (sin distinguir mayúsculas), o None. Búsqueda lineal."""
    buscado = termino.strip().lower()
    for fila in COMANDOS:
        for nombre in _alias(fila):
            if nombre == buscado:
                return fila
    return None


def texto_ayuda(post_partida: bool = False) -> str:
    """Lista de comandos con su sintaxis (FR-309). Con `post_partida`, solo los que valen cuando la partida terminó."""
    lineas = ["COMANDOS DISPONIBLES"]
    for fila in COMANDOS:
        if post_partida and fila[0] not in COMANDOS_POST_PARTIDA:
            continue
        lineas.append(f"  {fila[1]:<{_COLUMNA_SINTAXIS}}{fila[2]}")
    lineas.append("Los comandos no distinguen mayúsculas de minúsculas.")
    return "\n".join(lineas)


def texto_error(que_paso: str, que_hacer: str) -> str:
    """Un rechazo o error en la forma única «qué pasó + qué puede hacer el jugador» (FR-310)."""
    if not que_paso or not que_paso.strip() or not que_hacer or not que_hacer.strip():
        raise ValueError("un mensaje de error necesita decir qué pasó y qué puede hacer el jugador")
    return f"{que_paso.strip()} {que_hacer.strip()}"


# ----------------------------------------------------------------------------------------------------------------------
# Pantalla de sala (FR-306)
# ----------------------------------------------------------------------------------------------------------------------

def _mayuscula(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def _nombre_de(objeto, prefijo: str) -> tuple[str, str]:
    """(nombre, id) de un objeto o trampa que llega como DTO o como texto plano con el id de catálogo."""
    id_catalogo = getattr(objeto, "id_catalogo", None)
    nombre = getattr(objeto, "nombre", None)
    if id_catalogo is None:
        id_catalogo = str(objeto)
    if not nombre:
        limpio = id_catalogo[len(prefijo):] if id_catalogo.startswith(prefijo) else id_catalogo
        nombre = limpio.replace("_", " ")
    return _mayuscula(nombre), id_catalogo


def _linea_salida(salida, llave) -> str:
    if salida.puerta == "cerrada":
        estado = f"cerrada, requiere {llave}" if llave else "cerrada"
    elif salida.puerta == "abierta":
        estado = "abierta"
    else:
        estado = "sin observar"
    destino = salida.destino_nombre if salida.destino_explorado else "sala sin explorar"
    return f"  {salida.direccion:<6} -> {destino}  [{estado}]  costo {salida.costo}"


def texto_sala(jugador, tiempo, sala, sala_conocida, llaves, objeto_actual, mensajes) -> str:
    """Pantalla de sala: SIEMPRE las mismas secciones en el mismo orden y formato (FR-306, contrato §1).

    `sala_conocida.salidas` es la única fuente de las salidas (FR-219: nunca el id ni el nombre de una sala avistada);
    `llaves` trae, en el mismo orden, la llave que pide cada salida cerrada (o None). `tiempo` es el instante del reloj
    ya calculado por el modelo (o None). Una sección vacía muestra su título y «(ninguno)»; nunca desaparece."""
    lineas = ["=" * ANCHO, f"SALA: {sala.nombre} (id {sala.id})", "=" * ANCHO]

    lineas += ["", "--- SALIDAS ---"]
    if sala_conocida.salidas:
        for posicion, salida in enumerate(sala_conocida.salidas):
            llave = llaves[posicion] if llaves is not None and posicion < len(llaves) else None
            lineas.append(_linea_salida(salida, llave))
    else:
        lineas.append("  (ninguna)")

    lineas += ["", "--- ENEMIGOS ---"]
    if sala.enemigos:
        for enemigo in sala.enemigos:
            marca = "[cazador] " if enemigo.comportamiento == "cazador" else ""
            estado = "activo" if enemigo.activo else "dormido"
            lineas.append(f"  - {marca}{enemigo.nombre} [{estado}]  vida {enemigo.vida_actual}/{enemigo.vida_max}")
    else:
        lineas.append("  (ninguno)")

    lineas += ["", "--- OBJETOS ---"]
    if sala.objetos:
        for objeto in sala.objetos:
            nombre, id_catalogo = _nombre_de(objeto, "itm_")
            lineas.append(f"  - {nombre} (id {id_catalogo})")
    else:
        lineas.append("  (ninguno)")

    lineas += ["", "--- TRAMPAS ---"]
    if sala.trampas:
        for trampa in sala.trampas:
            nombre, _ = _nombre_de(trampa, "trp_")
            estado = "armada" if getattr(trampa, "armada", True) else "desarmada"
            lineas.append(f"  - {nombre} [daño {getattr(trampa, 'daño', 0)}] {estado}")
    else:
        lineas.append("  (ninguna)")

    lineas += ["", "--- ESTADO DEL JUGADOR ---",
               f"  Vida: {jugador.vida_actual}/{jugador.vida_max}",
               f"  Tiempo: {'no disponible' if tiempo is None else tiempo}"]
    if getattr(jugador, "antorcha_encendida", False):
        lineas.append(f"  Antorcha: encendida hasta t={jugador.antorcha_hasta}")
    else:
        lineas.append("  Antorcha: apagada")

    lineas += ["", "--- INVENTARIO ---"]
    if objeto_actual is not None:
        nombre = getattr(objeto_actual, "nombre", str(objeto_actual))
        lineas.append(f"  Objeto actual: {nombre} (id {getattr(objeto_actual, 'id_catalogo', 'N/A')})")
    else:
        lineas.append("  Objeto actual: (inventario vacío)")

    lineas += ["", "--- ÚLTIMOS MENSAJES (máx. 20) ---"]
    if mensajes:
        for mensaje in mensajes:
            lineas.append(f"  {mensaje}")
    else:
        lineas.append("  (sin mensajes)")
    return "\n".join(lineas)


# ----------------------------------------------------------------------------------------------------------------------
# Resumen de fin de partida (FR-307)
# ----------------------------------------------------------------------------------------------------------------------

def texto_fin_partida(motivo, puntaje, acciones, tiempo, vida_final, salas_exploradas,
                      id_cripta, version, enemigos_derrotados) -> str:
    """Resumen final con seis rótulos fijos, en este orden (contrato §2), y una línea de contexto de la cripta."""
    if motivo is None or not str(motivo).strip():
        motivo = "Motivo no informado"
    salas = "no disponible" if salas_exploradas is None else salas_exploradas
    version_texto = "sin versión" if not version else f"versión {version}"
    return "\n".join([
        "=" * ANCHO,
        "FIN DE LA PARTIDA",
        "=" * ANCHO,
        f"Motivo: {motivo}",
        f"Puntaje: {puntaje}",
        f"Acciones: {acciones}",
        f"Tiempo: {tiempo}",
        f"Vida final: {vida_final}",
        f"Salas exploradas: {salas}",
        "=" * ANCHO,
        f"Cripta: {id_cripta} ({version_texto}) | Enemigos derrotados: {enemigos_derrotados}",
    ])


# ----------------------------------------------------------------------------------------------------------------------
# Catálogo de mensajes de rechazo y de error (FR-308, FR-310; contrato §7). Todos usan `texto_error`.
# ----------------------------------------------------------------------------------------------------------------------

def _e(error) -> str:
    """El texto de un error del modelo sin su punto final, para que el mensaje no termine en «..»."""
    return str(error).strip().rstrip(".")


def mensaje_sin_criptas() -> str:
    return texto_error("No se encontraron criptas disponibles.",
                       "Revisa la conexión o inicia con --offline si ya descargaste datos.")


def mensaje_numero_cripta_invalido(maximo: int) -> str:
    return texto_error("El número no es válido.", f"Ingresa un número entre 1 y {maximo}.")


def mensaje_no_es_numero() -> str:
    return texto_error("Eso no es un número.", "Escribe solo dígitos, por ejemplo 1.")


def mensaje_carga_fallida(error) -> str:
    return texto_error(f"No se pudo cargar la partida: {_e(error)}.",
                       "Se iniciará una partida nueva; revisa el nombre del archivo si querías cargarla.")


def mensaje_sin_jugador() -> str:
    return texto_error("No se pudo obtener el estado del jugador.", "Cierra el juego y vuelve a abrirlo.")


def mensaje_historia_sin_parametro() -> str:
    return texto_error("No entendí el parámetro de 'historia'.", "Usa 'historia <t>' o 'historia #k'.")


def mensaje_historia_no_entero() -> str:
    return texto_error("El parámetro de 'historia' debe ser un número entero.", "Ejemplo: historia 200.")


def mensaje_historia_negativo() -> str:
    return texto_error("El instante o el número de acción no puede ser negativo.", "Usa 0 o un número mayor.")


def mensaje_historia_accion_cero() -> str:
    return texto_error("El número de acción debe ser 1 o mayor.", "Ejemplo: historia #1.")


def mensaje_historia_rechazada(error) -> str:
    return texto_error(f"No se pudo consultar la historia: {_e(error)}.", "Prueba con otro instante o número de acción.")


def mensaje_post_partida_desconocido() -> str:
    return texto_error("No reconozco ese comando.", "Usa 'historia <t>', 'historia #k', 'ayuda' o 'salir'.")


def mensaje_ir_a_destino_invalido() -> str:
    return texto_error("El destino de 'ir a' debe ser el número de una sala.", "Ejemplo: ir a 12.")


def mensaje_ir_a_rechazada(error) -> str:
    return texto_error(f"No se puede viajar: {_e(error)}.", "Escribe 'mapa' para ver las salas que conoces.")


def mensaje_sin_salida(direccion: str) -> str:
    return texto_error(f"No existe una salida hacia el '{direccion}'.",
                       "Mira la lista de SALIDAS y elige una dirección que aparezca.")


def mensaje_salida_cerrada(direccion: str) -> str:
    return texto_error(f"La salida hacia el '{direccion}' está cerrada.",
                       "Usa 'abrir' si tienes con qué, o elige otra salida.")


def mensaje_salida_cerrada_con_llave(direccion: str, llave: str) -> str:
    return texto_error(f"La salida hacia el '{direccion}' está cerrada y necesita la llave '{llave}'.",
                       "Búscala y usa 'abrir', o elige otra salida.")


def mensaje_sin_enemigos() -> str:
    return texto_error("No hay enemigos aquí para atacar.", "Muévete a otra sala o usa 'esperar'.")


def mensaje_enemigo_invalido() -> str:
    return texto_error("Ese número de enemigo no existe.", "Elige uno de la lista.")


def mensaje_enemigo_derrotado(nombre: str) -> str:
    return texto_error(f"{nombre} ya está derrotado.", "Elige otro objetivo o sigue explorando.")


def mensaje_sin_salidas() -> str:
    return texto_error("No hay salidas en esta sala.", "Usa 'mapa' para ver por dónde seguir.")


def mensaje_sin_puertas_cerradas() -> str:
    return texto_error("No hay puertas cerradas en esta sala.", "Elige una dirección de la lista de SALIDAS.")


def mensaje_direccion_vacia() -> str:
    return texto_error("No escribiste ninguna dirección.", "Escribe norte, sur, este u oeste.")


def mensaje_sin_puerta_cerrada(direccion: str) -> str:
    return texto_error(f"No hay ninguna puerta cerrada hacia el '{direccion}'.",
                       "Elige una de las direcciones mostradas.")


def mensaje_falta_llave(llave: str) -> str:
    return texto_error(f"La puerta está cerrada y necesitas la llave '{llave}' para abrirla.",
                       "Búscala en otras salas.")


def mensaje_sin_objetos() -> str:
    return texto_error("No hay objetos aquí para recoger.", "Revisa otras salas.")


def mensaje_objeto_invalido() -> str:
    return texto_error("Ese número de objeto no existe.", "Elige uno de la lista.")


def mensaje_inventario_vacio() -> str:
    return texto_error("Tu inventario está vacío.", "Recoge un objeto con 'recoger'.")


def mensaje_inventario_uso() -> str:
    return texto_error("Uso incorrecto de 'inventario'.",
                       "Escribe 'inventario', 'inventario peso', 'inventario valor' o 'inventario nombre'.")


def mensaje_inventario_rechazado(error) -> str:
    return texto_error(f"No se puede ordenar el inventario: {_e(error)}.", "Usa peso, valor o nombre.")


def mensaje_objeto_rechazado(error) -> str:
    return texto_error(f"No se puede cambiar de objeto: {_e(error)}.", "Recoge un objeto con 'recoger'.")


def mensaje_comando_desconocido(texto: str) -> str:
    return texto_error(f"No reconozco el comando '{texto}'.", "Escribe 'ayuda' para ver los comandos.")


def mensaje_guardado_fallido(error) -> str:
    return texto_error(f"No se pudo guardar la partida: {_e(error)}.", "Prueba con otro nombre de archivo.")


def mensaje_puntaje_nombre_vacio() -> str:
    return texto_error("El nombre no puede estar vacío.", "Escribe al menos una letra.")


def mensaje_puntaje_nombre_largo(maximo: int, largo: int) -> str:
    return texto_error(f"El nombre tiene {largo} caracteres y el máximo es {maximo}.", "Escribe uno más corto.")


def mensaje_puntaje_fallido(error) -> str:
    return texto_error(f"No se pudo registrar el puntaje: {_e(error)}.",
                       "La partida terminó igual; puedes seguir consultando la historia.")


def mensaje_puntajes_ilegibles(error) -> str:
    return texto_error(f"No se pudo leer la tabla de puntajes: {_e(error)}.",
                       "Sigue jugando; el archivo se revisa al registrar un puntaje.")


def mensaje_mensajes_ilegibles(error) -> str:
    return texto_error(f"No se pudieron mostrar los mensajes: {_e(error)}.",
                       "El registro completo está en el log de la partida.")


def mensaje_resumen_fallido(error) -> str:
    return texto_error(f"No se pudo obtener el resumen: {_e(error)}.", "Revisa el log de la partida.")


def mensaje_cripta_no_resoluble(id_cripta: str) -> str:
    return texto_error(f"La cripta {id_cripta} no tiene solución, por eso no se abrió la partida.",
                       "Elige otra cripta, o inicia con --forzar para jugarla de todos modos.")


# (nombre, función, argumentos de ejemplo): lista única para que las pruebas recorran TODO el catálogo (SC-306).
MENSAJES = (
    ("sin_criptas", mensaje_sin_criptas, ()),
    ("numero_cripta_invalido", mensaje_numero_cripta_invalido, (3,)),
    ("no_es_numero", mensaje_no_es_numero, ()),
    ("carga_fallida", mensaje_carga_fallida, ("archivo inexistente",)),
    ("sin_jugador", mensaje_sin_jugador, ()),
    ("historia_sin_parametro", mensaje_historia_sin_parametro, ()),
    ("historia_no_entero", mensaje_historia_no_entero, ()),
    ("historia_negativo", mensaje_historia_negativo, ()),
    ("historia_accion_cero", mensaje_historia_accion_cero, ()),
    ("historia_rechazada", mensaje_historia_rechazada, ("el instante aún no ha ocurrido",)),
    ("post_partida_desconocido", mensaje_post_partida_desconocido, ()),
    ("ir_a_destino_invalido", mensaje_ir_a_destino_invalido, ()),
    ("ir_a_rechazada", mensaje_ir_a_rechazada, ("Esa sala no está explorada.",)),
    ("sin_salida", mensaje_sin_salida, ("norte",)),
    ("salida_cerrada", mensaje_salida_cerrada, ("este",)),
    ("salida_cerrada_con_llave", mensaje_salida_cerrada_con_llave, ("este", "itm_llave_negra")),
    ("sin_enemigos", mensaje_sin_enemigos, ()),
    ("enemigo_invalido", mensaje_enemigo_invalido, ()),
    ("enemigo_derrotado", mensaje_enemigo_derrotado, ("Orco",)),
    ("sin_salidas", mensaje_sin_salidas, ()),
    ("sin_puertas_cerradas", mensaje_sin_puertas_cerradas, ()),
    ("direccion_vacia", mensaje_direccion_vacia, ()),
    ("sin_puerta_cerrada", mensaje_sin_puerta_cerrada, ("sur",)),
    ("falta_llave", mensaje_falta_llave, ("itm_llave_negra",)),
    ("sin_objetos", mensaje_sin_objetos, ()),
    ("objeto_invalido", mensaje_objeto_invalido, ()),
    ("inventario_vacio", mensaje_inventario_vacio, ()),
    ("inventario_uso", mensaje_inventario_uso, ()),
    ("inventario_rechazado", mensaje_inventario_rechazado, ("criterio desconocido",)),
    ("objeto_rechazado", mensaje_objeto_rechazado, ("el inventario está vacío",)),
    ("comando_desconocido", mensaje_comando_desconocido, ("xyz",)),
    ("guardado_fallido", mensaje_guardado_fallido, ("disco lleno",)),
    ("puntaje_nombre_vacio", mensaje_puntaje_nombre_vacio, ()),
    ("puntaje_nombre_largo", mensaje_puntaje_nombre_largo, (15, 20)),
    ("puntaje_fallido", mensaje_puntaje_fallido, ("disco lleno",)),
    ("puntajes_ilegibles", mensaje_puntajes_ilegibles, ("archivo dañado",)),
    ("mensajes_ilegibles", mensaje_mensajes_ilegibles, ("sin partida",)),
    ("resumen_fallido", mensaje_resumen_fallido, ("sin partida",)),
    ("cripta_no_resoluble", mensaje_cripta_no_resoluble, ("cripta-01",)),
)
