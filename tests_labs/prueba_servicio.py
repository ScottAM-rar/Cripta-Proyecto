from adaptadores.cliente_http import ClienteCripta
from adaptadores.cache import CacheLRU
from adaptadores.servicioCripta import ServicioCripta

URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"

cliente = ClienteCripta(URL)
servicio = ServicioCripta(cliente, CacheLRU(25))

print("1)", servicio.listar_criptas())
cid = servicio.obtener_id_cripta(1)

# print("2)", cid, "-> salas:", servicio.total_salas(cid))
# print("   solicitudes hasta aquí:", cliente.solicitudes_realizadas)

# sala = servicio.construir_sala(cid, 2)
# print("3)", sala.nombre)
# for s in sala.salidas:
#     print("   salida", s.direccion, "->", s.sala_destino, "cerrada:", s.cerrada, "llave:", s.llave)
# print("   enemigos:", sala.enemigos)
# print("   objetos:", sala.objetos)
# print("   trampas:", sala.trampas)
# print("4) solicitudes totales:", cliente.solicitudes_realizadas)

salas_en_total = servicio.total_salas(cid)
for numero in range(1, salas_en_total + 1):
    sala = servicio.construir_sala(cid, numero)
    print(f"--- sala {numero} ---\n")
    print(f"ID: {sala.id} - Nombre de la sala: {sala.nombre}")
    print("Salidas:", sala.salidas, "\n")
    print("Enemigos:", sala.enemigos, "\n")
    print("Objetos:", sala.objetos, "\n")
    print("Trasmpas:", sala.trampas, "\n")

print("Cantidad de solicitudes:", cliente.solicitudes_realizadas)