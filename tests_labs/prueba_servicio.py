from adaptadores.cliente_http import ClienteCripta
from adaptadores.servicioCripta import ServicioCripta
from adaptadores.cache import CacheLRU

def comprobar(nombre, condicion, detalle=""):
    estado = "OK   " if condicion else "FALLO"
    print(f"  [{estado}] {nombre} {detalle}")
    resultados.append(condicion)

URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"

resultados = []

cliente = ClienteCripta(URL)
servicio = ServicioCripta(cliente, CacheLRU(25))

print("== Criptas ==")
criptas = servicio.listar_criptas()
print("  ", criptas)
comprobar("hay al menos una cripta", len(criptas) >= 1)
cid = servicio.obtener_id_cripta(1)
comprobar("existe_cripta con un id real", servicio.existe_cripta(cid))
comprobar("existe_cripta con un id falso da False", not servicio.existe_cripta("cripta-xx"))


print("== Datos generales y jugador ==")
datos = servicio.datos_cripta(cid)
jugador = servicio.crear_jugador(cid)
comprobar("vida inicial = vida máxima", jugador.vida_actual == jugador.vida_max)
comprobar("stats vienen de la API", jugador.ataque == datos["jugador"]["ataque"]
          and jugador.defensa == datos["jugador"]["defensa"]
          and jugador.velocidad == datos["jugador"]["velocidad"])
comprobar("empieza en la sala inicial", jugador.id_sala_actual == datos["sala_inicial"])
comprobar("inventario con la capacidad de la API",
          jugador.inventario.capacidad_maxima == datos["inventario_max"])

print("== Salas ==")
total = servicio.total_salas(cid)
comprobar("total_salas coincide con salas_total", total == datos["salas_total"], f"({total})")

for numero in range(1, total + 1):
    sala = servicio.construir_sala(cid, numero)
    destinos_validos = True
    for salida in sala.salidas:
        if salida.sala_destino < 1 or salida.sala_destino > total:
            destinos_validos = False
    enemigos_validos = True
    for enemigo in sala.enemigos:
        if enemigo.vida_actual <= 0 or enemigo.vida_actual > enemigo.vida_max \
                or enemigo.id_sala_actual != numero:
            enemigos_validos = False
    comprobar(f"sala {numero} '{sala.nombre}'",
              sala.id == numero and destinos_validos and enemigos_validos,
              f"salidas={len(sala.salidas)} enemigos={len(sala.enemigos)} "
              f"objetos={len(sala.objetos)} trampas={len(sala.trampas)}")

print("== Presupuesto ==")
usadas = cliente.solicitudes_realizadas
presupuesto = datos["presupuesto_solicitudes"]
print(f"   solicitudes usadas: {usadas} de {presupuesto}")
comprobar("dentro del presupuesto", usadas <= presupuesto)

print()
print(f"{resultados.count(True)} de {len(resultados)} comprobaciones OK")






















# print("1)", servicio.listar_criptas())
# cid = servicio.obtener_id_cripta(1)

# # print("2)", cid, "-> salas:", servicio.total_salas(cid))
# # print("   solicitudes hasta aquí:", cliente.solicitudes_realizadas)

# # sala = servicio.construir_sala(cid, 2)
# # print("3)", sala.nombre)
# # for s in sala.salidas:
# #     print("   salida", s.direccion, "->", s.sala_destino, "cerrada:", s.cerrada, "llave:", s.llave)
# # print("   enemigos:", sala.enemigos)
# # print("   objetos:", sala.objetos)
# # print("   trampas:", sala.trampas)
# # print("4) solicitudes totales:", cliente.solicitudes_realizadas)

# salas_en_total = servicio.total_salas(cid)
# for numero in range(1, salas_en_total + 1):
#     sala = servicio.construir_sala(cid, numero)
#     print(f"--- sala {numero} ---\n")
#     print(f"ID: {sala.id} - Nombre de la sala: {sala.nombre}")
#     print("Salidas:", sala.salidas, "\n")
#     print("Enemigos:", sala.enemigos, "\n")
#     print("Objetos:", sala.objetos, "\n")
#     print("Trasmpas:", sala.trampas, "\n")

# print("Cantidad de solicitudes:", cliente.solicitudes_realizadas)