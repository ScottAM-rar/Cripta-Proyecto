import os
import tempfile

from DTO.EventoDTO import EventoDTO
from Logica.EstadoJuegoLogica import EstadoJuegoLogica
from Logica.RetrocesoLogica import RetrocesoLogica
from adaptadores.cache import CacheLRU
from adaptadores.PersistenciaPartida import PersistenciaPartida
from adaptadores.servicioCripta import ServicioCripta
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from tests_labs.api_falsa import HttpFalso

resultados = []


def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(bool(condicion))


def lanza_value_error(funcion):
    try:
        funcion()
    except ValueError:
        return True
    return False


class HttpResistente(HttpFalso):
    def obtener_datos_generales(self, cripta_id):
        datos = super().obtener_datos_generales(cripta_id)
        datos["jugador"]["vida_max"] = 5000
        return datos


def nueva_logica():
    logica = EstadoJuegoLogica()
    logica.comunicacion = ServicioCripta(HttpResistente(), CacheLRU(25))
    return logica


def evento(logica, tipo, datos=None, actor=None):
    jugador = logica.estadoJuego.jugador
    return EventoDTO(100, 0, jugador if actor is None else actor, tipo, [] if datos is None else datos)


def mover(logica, direccion):
    jugador = logica.estadoJuego.jugador
    sala = logica.ingresarEnSala(jugador.id_sala_actual)
    return logica.accionJugador(evento(logica, "MOVER_JUGADOR", [sala, direccion]))


def atacar(logica):
    jugador = logica.estadoJuego.jugador
    sala = logica.ingresarEnSala(jugador.id_sala_actual)
    vivos = [e for e in sala.enemigos if e.vida_actual > 0]
    if not vivos:
        return None
    return logica.accionJugador(evento(logica, "ATACAR", [vivos[0]]))


def esperar(logica):
    return logica.accionJugador(evento(logica, "ESPERAR"))


def foto(logica):
    estado = logica.estadoJuego
    salas = []
    for sala in estado.salas:
        if sala is None:
            salas.append(None)
        else:
            salas.append((
                sala.id,
                sala.ultimo_paso,
                [(e.id_instancia, e.vida_actual, e.id_sala_actual) for e in sala.enemigos],
                [(t.id_instancia, t.armada) for t in sala.trampas],
                list(sala.objetos),
                [(s.direccion, s.sala_destino, s.cerrada) for s in sala.salidas],
            ))
    heap = [(e.tiempo_ejecucion, e.id_secuencia, e.tipo_accion) for e in estado.reloj.heap]
    jugador = estado.jugador
    return {
        "salas": salas,
        "heap": heap,
        "tiempo": estado.reloj.tiempo_actual,
        "secuencia": estado.reloj.secuencia_actual,
        "puntaje": estado.puntaje,
        "vida": jugador.vida_actual,
        "sala_jugador": jugador.id_sala_actual,
        "inventario": jugador.inventario.cantidad_actual,
        "fin": logica.fin,
        "semilla": logica.semilla,
        "cripta": logica.idCripta,
        "retroceso": (
            RetrocesoLogica().cantidad_acciones,
            RetrocesoLogica().cantidad_actual,
        ),
    }


def resumen(resultado):
    if resultado is None:
        return None
    return (resultado.exito, resultado.mensaje, resultado.puntaje)


def guion_posterior(logica):
    salida = []
    salida.append(resumen(atacar(logica)))
    salida.append(resumen(atacar(logica)))
    salida.append(resumen(esperar(logica)))
    salida.append(resumen(atacar(logica)))
    salida.append(resumen(mover(logica, "sur")))
    salida.append(resumen(mover(logica, "norte")))
    salida.append(resumen(esperar(logica)))
    return salida


carpeta = tempfile.mkdtemp()
archivo = os.path.join(carpeta, "partida.sav")

print("== Preparar partida ==")
original = nueva_logica()
original.iniciarJuego("cripta-01", 7)
original.ingresarEnSala(original.estadoJuego.jugador.id_sala_actual)
resultado_mover = mover(original, "norte")
comprobar("el jugador se movió a la sala 2", original.estadoJuego.jugador.id_sala_actual == 2, resumen(resultado_mover))
atacar(original)
esperar(original)

print("== Guardar ==")
foto_guardada = foto(original)
original.guardarPartida(archivo)
comprobar("se creó el archivo", os.path.isfile(archivo))
comprobar("no queda archivo temporal", not os.path.exists(archivo + ".tmp"))
comprobar("guardar no altera el estado", foto(original) == foto_guardada)

print("== Seguir jugando sin cargar (referencia) ==")
referencia = guion_posterior(original)
foto_referencia = foto(original)

print("== Cargar en un objeto nuevo y repetir el guion ==")
cargada = nueva_logica()
comunicacion_previa = cargada.comunicacion
cargada.cargarPartida(archivo)
comprobar("el estado cargado es igual al guardado", foto(cargada) == foto_guardada)
comprobar("se conserva la comunicación del objeto", cargada.comunicacion is comunicacion_previa)
comprobar("está marcado como iniciado", cargada.iniciado)

estado = cargada.estadoJuego
jugador = estado.jugador
print("== Referencias compartidas ==")
comprobar("gestor y estado comparten la lista de salas", cargada.gestorEventos.salas is estado.salas)
comprobar("jugadorLogica apunta al jugador del estado", cargada.jugadorLogica.jugador is jugador)
comprobar("gestor apunta al jugador del estado", cargada.gestorEventos.jugador_logica.jugador is jugador)
comprobar("objeto_logica apunta al jugador del estado", cargada.gestorEventos.objeto_logica.jugador is jugador)
comprobar("el singleton de retroceso se mantiene", cargada.jugadorLogica.retroceso is RetrocesoLogica())
comprobar("cargar_sala quedó enlazado al objeto cargado", cargada.gestorEventos.cargar_sala == cargada.ingresarEnSala)
comprobar("el reloj apunta al singleton de retroceso", estado.reloj.retroceso is RetrocesoLogica())
comprobar("el singleton de retroceso apunta al reloj cargado", RetrocesoLogica().reloj is estado.reloj)
comprobar("pergamino y objeto_logica comparten pergamino", cargada.gestorEventos.objeto_logica.pergamino_logica is cargada.gestorEventos.pergamino_logica)

enemigos_en_salas = []
for sala in estado.salas:
    if sala is not None:
        enemigos_en_salas.extend(sala.enemigos)
actores_ok = True
for pendiente in estado.reloj.heap:
    actor = pendiente.actor
    if actor is jugador:
        continue
    esta = False
    for enemigo in enemigos_en_salas:
        if enemigo is actor:
            esta = True
    actores_ok = actores_ok and esta
comprobar("los actores del heap son los mismos objetos de las salas", actores_ok, f"({len(estado.reloj.heap)} eventos)")

catalogo_ok = True
for enemigo in estado.catalogo_enemigos:
    encontrado = False
    for otro in enemigos_en_salas:
        if otro is enemigo:
            encontrado = True
    catalogo_ok = catalogo_ok and encontrado
comprobar("catalogo_enemigos referencia los mismos enemigos de las salas", catalogo_ok)

posterior = guion_posterior(cargada)
comprobar("las acciones posteriores dan los mismos resultados", posterior == referencia)
comprobar("el estado final es idéntico", foto(cargada) == foto_referencia)

print("== Cargar sobre una partida ya en curso ==")
otra = nueva_logica()
otra.iniciarJuego("cripta-01", 99)
mover(otra, "norte")
otra.cargarPartida(archivo)
comprobar("reemplaza la partida en curso", foto(otra) == foto_guardada)
comprobar("semilla restaurada", otra.semilla == 7)

print("== A través del servicio ==")
servicio = EstadoJuegoServicio()
servicio._estadoJuegoLogica.comunicacion = ServicioCripta(HttpResistente(), CacheLRU(25))
servicio.iniciarJuego("cripta-01", 3)
servicio.guardarPartida(os.path.join(carpeta, "servicio.sav"))
servicio.cargarPartida(os.path.join(carpeta, "servicio.sav"))
comprobar("guardar y cargar por el servicio", servicio.getJudador().id_sala_actual == 1)

print("== Errores ==")
sin_iniciar = nueva_logica()
comprobar("guardar sin partida iniciada falla", lanza_value_error(lambda: sin_iniciar.guardarPartida(archivo)))
comprobar("cargar un archivo inexistente falla", lanza_value_error(lambda: nueva_logica().cargarPartida(os.path.join(carpeta, "no_existe.sav"))))
basura = os.path.join(carpeta, "basura.sav")
with open(basura, "wb") as f:
    f.write(b"esto no es una partida")
comprobar("cargar un archivo corrupto falla", lanza_value_error(lambda: nueva_logica().cargarPartida(basura)))
vacio = os.path.join(carpeta, "vacio.sav")
open(vacio, "wb").close()
comprobar("cargar un archivo vacío falla", lanza_value_error(lambda: nueva_logica().cargarPartida(vacio)))
comprobar("nombre de archivo vacío falla", lanza_value_error(lambda: original.guardarPartida("  ")))

import pickle
ajeno = os.path.join(carpeta, "ajeno.sav")
with open(ajeno, "wb") as f:
    pickle.dump({"hola": 1}, f)
comprobar("un pickle ajeno falla", lanza_value_error(lambda: nueva_logica().cargarPartida(ajeno)))

version_mala = os.path.join(carpeta, "version.sav")
with open(version_mala, "wb") as f:
    pickle.dump({"formato": PersistenciaPartida.FORMATO, "version": 999, "estado": None}, f)
comprobar("una versión distinta falla", lanza_value_error(lambda: nueva_logica().cargarPartida(version_mala)))

original.fin = True
comprobar("guardar una partida terminada falla", lanza_value_error(lambda: original.guardarPartida(archivo)))

print()
print(f"{sum(resultados)}/{len(resultados)} comprobaciones correctas")
raise SystemExit(0 if all(resultados) else 1)
