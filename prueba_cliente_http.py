from adaptadores.cliente_http import ClienteCripta
from adaptadores.resolucion import resolver_trampa

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
cliente = ClienteCripta(BASE_URL)
cripta_id = "cripta-01"

todas_salas = cliente.obtener_salas(cripta_id)
ids_salas = [sala["id"] for sala in todas_salas]
contenido = cliente.obtener_contenido(cripta_id, ids_salas)

tipos_enemigos = set()
for entrada in contenido:
    for enemigo in entrada["enemigos"]:
        tipos_enemigos.add(enemigo["tipo"])

print("Tipos de enemigos encontrados:", tipos_enemigos)

fichas = cliente.obtener_catalogo(list(tipos_enemigos))
for ficha in fichas:
    print(ficha["nombre"], "->", repr(ficha["comportamiento"]))


fichas_trampas = cliente.obtener_catalogo(["trp_dardos"])
ficha_trampa = fichas_trampas[0]

contenido_sala_2 = cliente.obtener_contenido(cripta_id, [2])
for entrada in contenido_sala_2:
    for colocacion in entrada["trampas"]:
        trampa = resolver_trampa(colocacion, ficha_trampa)
        print(trampa)