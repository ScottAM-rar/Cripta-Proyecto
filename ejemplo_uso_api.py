"""
EJEMPLO DE USO DE LA CAPA DE API 

Corre contra la API REAL:      py ejemplo_uso_api.py

Muestra, paso a paso, cómo se usa:
    ClienteCripta  -> habla con la API y devuelve datos crudos (dict / list)
    resolucion.py  -> convierte esos datos crudos en objetos del juego (DTO)
    CacheLRU       -> recuerda fichas del catálogo para no volver a pedirlas

REGLAS DE ORO
  1. Crear UN solo ClienteCripta por partida (lleva el Client-Id y el conteo de solicitudes).
  2. Nadie fuera de adaptadores/ usa 'requests' ni toca JSON: se pide al cliente y se resuelve.
  3. Para armar una sala completa: resolver_sala(cliente, cache, cripta_id, numero_sala).
  4. Cada solicitud HTTP real cuenta para el límite del enunciado (§5.1).
"""
from adaptadores.cliente_http import ClienteCripta
from adaptadores.resolucion import resolver_sala

from adaptadores.cache import CacheLRU

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def titulo(texto: str) -> None:
    print(f"\n=== {texto} ===")


def numero_de_sala(sala: dict) -> int:
    """Las salas del esqueleto identifican su número con 'id' (o 'sala' según el endpoint)."""
    return sala["id"] if "id" in sala else sala["sala"]


def main(cliente=None) -> None:
    # ------------------------------------------------------------------
    titulo("1. Crear el cliente y la caché (UNA vez por partida)")
    # ------------------------------------------------------------------
    cliente = cliente or ClienteCripta(BASE_URL)
    cache = CacheLRU(25)          # 25 fichas = valor por defecto del enunciado (--cache-size)
    print("Cliente y caché listos. Solicitudes hasta ahora:", cliente.solicitudes_realizadas)

    # ------------------------------------------------------------------
    titulo("2. Listar las criptas disponibles  ->  obtener_criptas()")
    # ------------------------------------------------------------------
    criptas = cliente.obtener_criptas()          # list[dict]: {id, nombre, salas, dificultad}
    for c in criptas:
        print(f"  {c['id']}: {c['nombre']} ({c['salas']} salas, dificultad {c['dificultad']})")
    cripta = criptas[0]                          # en el juego real elige el jugador
    cripta_id = cripta["id"]

    # ------------------------------------------------------------------
    titulo("3. Versiones (sirven para validar datos guardados en disco)")
    # ------------------------------------------------------------------
    print("  versión de la cripta :", cliente.obtener_version_cripta(cripta_id))
    print("  versión del catálogo :", cliente.obtener_version_catalogo())

    # ------------------------------------------------------------------
    titulo("4. El esqueleto: todas las salas  ->  obtener_salas(cripta_id)")
    # ------------------------------------------------------------------
    salas = cliente.obtener_salas(cripta_id)     # ya junta todas las páginas solo
    print(f"  {len(salas)} salas. Ejemplo de una sala cruda: {salas[0]}")

    # ------------------------------------------------------------------
    titulo("5. Lo que HAY en una sala  ->  obtener_contenido (datos CRUDOS)")
    # ------------------------------------------------------------------
    sala_con_enemigos = None
    for sala in salas:
        crudo = cliente.obtener_contenido(cripta_id, [numero_de_sala(sala)])[0]
        if crudo["enemigos"]:
            sala_con_enemigos = numero_de_sala(sala)
            print(f"  Sala {sala_con_enemigos} (crudo): {crudo}")
            print("  OJO: aquí solo dice QUÉ hay y DÓNDE. Faltan ataque, defensa, etc.")
            break
    if sala_con_enemigos is None:
        print("  (ninguna sala tiene enemigos; uso la primera)")
        sala_con_enemigos = numero_de_sala(salas[0])

    # ------------------------------------------------------------------
    titulo("6. Lo MISMO pero listo para jugar  ->  resolver_sala(...)")
    # ------------------------------------------------------------------
    antes = cliente.solicitudes_realizadas
    enemigos, objetos, trampas = resolver_sala(cliente, cache, cripta_id, sala_con_enemigos)
    print(f"  Costó {cliente.solicitudes_realizadas - antes} solicitudes "
          f"(1 de contenido + 1 de catálogo por las fichas que faltaban)")

    print("\n  ENEMIGOS (EnemigoDTO):")
    for e in enemigos:
        print(f"    {e.id_instancia} {e.nombre}: vida {e.vida_actual}/{e.vida_max}, "
              f"ataque {e.ataque}, defensa {e.defensa}, velocidad {e.velocidad}, "
              f"comportamiento={e.comportamiento!r}, suelta={e.suelta}")
    print("\n  OBJETOS en el suelo (Objeto y subclases):")
    for o in objetos:
        print(f"    {type(o).__name__}: {o}")
    print("\n  TRAMPAS (Trampa):")
    for t in trampas:
        print(f"    {t}")

    # ------------------------------------------------------------------
    titulo("7. La caché en acción: repetir la misma sala")
    # ------------------------------------------------------------------
    antes = cliente.solicitudes_realizadas
    resolver_sala(cliente, cache, cripta_id, sala_con_enemigos)
    print(f"  Segunda vez costó {cliente.solicitudes_realizadas - antes} solicitud "
          f"(solo el contenido; las fichas salieron de la caché)")

    # ------------------------------------------------------------------
    titulo("8. Qué NO se puede desalojar de la caché (§4.4): 'en uso'")
    # ------------------------------------------------------------------
    # El motor debe avisar a la caché cuando una ficha se está usando:
    #   cache.marcar_en_uso(id_catalogo)  -> aparece un enemigo vivo / entra a la sala actual
    #   cache.marcar_libre(id_catalogo)   -> el enemigo muere / el jugador sale de la sala
    # Mientras una ficha esté en uso, la caché no la libera aunque esté llena.
    if enemigos:
        ficha_id = enemigos[0].tipo
        cache.marcar_en_uso(ficha_id)
        print(f"  '{ficha_id}' marcada en uso (protegida del desalojo)")
        cache.marcar_libre(ficha_id)
        print(f"  '{ficha_id}' marcada libre otra vez")

    # ------------------------------------------------------------------
    titulo("9. Resumen")
    # ------------------------------------------------------------------
    print("  Solicitudes HTTP totales:", cliente.solicitudes_realizadas)


if __name__ == "__main__":
    main()