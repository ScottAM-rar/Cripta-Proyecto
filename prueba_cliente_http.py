from adaptadores.cliente_http import ClienteCripta
from adaptadores.resolucion import resolver_objeto
from adaptadores.resolucion import resolver_ficha_enemigo, resolver_enemigo

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"

cliente = ClienteCripta(BASE_URL)

criptas = cliente.obtener_criptas()
print("Criptas disponibles:", criptas)

cripta_id = criptas[0]["id"]
print("Versión de la cripta:", cliente.obtener_version_cripta(cripta_id))
print("Versión del catálogo:", cliente.obtener_version_catalogo())

salas = cliente.obtener_salas(cripta_id)
print(f"{len(salas)} salas recibidas")

ids_salas = [sala["id"] for sala in salas[:3]]
contenido = cliente.obtener_contenido(cripta_id, ids_salas)
print("Contenido de las primeras 3 salas:", contenido)

print("Solicitudes realizadas:", cliente.solicitudes_realizadas)

ids_objetos = ["itm_antorcha", "itm_daga_oxidada", "itm_llave_bronce", "itm_coraza_cuero"]
fichas = cliente.obtener_catalogo(ids_objetos)

for ficha in fichas:
    objeto = resolver_objeto(ficha)
    print(objeto)

fichas_enemigos = cliente.obtener_catalogo(["ent_rata_gigante"])
ficha_rata = resolver_ficha_enemigo(fichas_enemigos[0])
print(ficha_rata)

contenido_sala_2 = cliente.obtener_contenido(cripta_id, [2])
for entrada in contenido_sala_2:
    for colocacion in entrada["enemigos"]:
        enemigo = resolver_enemigo(colocacion, ficha_rata, id_sala=entrada["sala"])
        print(enemigo)