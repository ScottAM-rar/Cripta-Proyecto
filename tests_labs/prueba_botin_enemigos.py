"""Pruebas de lo que sueltan los enemigos al morir (§2.6). Sin internet.

    py -m tests_labs.prueba_botin_enemigos
"""
import os
import tempfile
from types import SimpleNamespace

from adaptadores import fabrica
from adaptadores.servicioCripta import ServicioCripta
from DTO.EventoDTO import EventoDTO
from DTO.Objeto import Arma, Pocion, PergaminoRetroceso
from Servicio.EstadoJuegoServicio import EstadoJuegoServicio
from tests_labs.api_falsa import HttpFalso

resultados = []


def comprobar(nombre, condicion, detalle=""):
    print(f"  [{'OK   ' if condicion else 'FALLO'}] {nombre} {detalle}")
    resultados.append(condicion)


class HttpBotin(HttpFalso):
    """Sala 2 con un ladrón (suelta 2 pociones y una daga) y un esqueleto (no suelta nada); los dos con 1 de vida."""

    def obtener_contenido(self, cripta_id, salas):
        self.llamadas.append(("contenido", list(salas)))
        contenidos = []
        for numero in salas:
            enemigos = []
            if numero == 2:
                enemigos = [{"instancia": "e-901", "tipo": "ent_ladron", "vida": 1},
                            {"instancia": "e-902", "tipo": "ent_hueso", "vida": 1}]
            contenidos.append({"sala": numero, "enemigos": enemigos, "objetos": [], "trampas": []})
        return contenidos

    def obtener_catalogo(self, ids):
        self.llamadas.append(("catalogo", list(ids)))
        fichas = [
            {"id": "ent_ladron", "clase": "enemigo", "nombre": "Ladrón", "vida_max": 8, "ataque": 3, "defensa": 0,
             "velocidad": 100, "comportamiento": "guardián",
             "suelta": ["itm_pocion_menor", "itm_pocion_menor", "itm_daga_oxidada"]},
            {"id": "ent_hueso", "clase": "enemigo", "nombre": "Esqueleto", "vida_max": 8, "ataque": 3, "defensa": 0,
             "velocidad": 100, "comportamiento": "guardián", "suelta": []},
            {"id": "itm_pocion_menor", "clase": "pocion", "nombre": "Poción menor", "peso": 1, "valor": 10,
             "cura": 8, "modificador_velocidad": 0, "duracion": 0},
            {"id": "itm_daga_oxidada", "clase": "arma", "nombre": "Daga oxidada", "peso": 2, "valor": 15,
             "ataque_bonus": 3},
        ]
        return [ficha for ficha in fichas if ficha["id"] in ids]


def servicio_de_servicio(carpeta, http, offline=False):
    """Un ServicioCripta armado como lo hace el juego, sobre un cliente de red falso."""
    fabrica.reiniciar_cliente_compartido()
    return fabrica.crear_servicio(offline=offline, carpeta=carpeta, cliente_http=http)


def partida(carpeta, http, offline=False):
    return EstadoJuegoServicio(comunicacion=servicio_de_servicio(carpeta, http, offline), offline=offline)


def empezar_en_sala_2(juego, semilla=7):
    juego.iniciarJuego(juego.obtenerIdCripta(1), semilla)
    jugador = juego.getJudador()
    juego.accionJugador(EventoDTO(100, 0, jugador, "MOVER_JUGADOR", [juego.obtenerSala(1), "norte"]))
    return jugador, juego.obtenerSala(2)


def atacar(juego, jugador, enemigo):
    return juego.accionJugador(EventoDTO(100, 0, jugador, "ATACAR", [enemigo]))


def nombres(objetos):
    return [o.nombre for o in objetos]


with tempfile.TemporaryDirectory() as raiz:
    anterior = os.getcwd()
    os.chdir(raiz)                 # logs/ y "Partidas Guardadas/" se crean aquí
    try:
        print("== 1) El método: servicio.objetos_que_suelta(enemigo) ==")
        http = HttpBotin()
        servicio = servicio_de_servicio(os.path.join(raiz, "d1"), http)
        servicio.listar_criptas()
        cid = servicio.obtener_id_cripta(1)
        servicio.crear_jugador(cid)
        salas = servicio.construir_todas(cid)
        ladron, esqueleto = salas[1].enemigos
        solicitudes = http.solicitudes_realizadas
        botin = servicio.objetos_que_suelta(ladron)
        comprobar("devuelve lo que dice el campo suelta, en orden",
                  nombres(botin) == ["Poción menor", "Poción menor", "Daga oxidada"], f"-> {nombres(botin)}")
        comprobar("cada objeto es del tipo que corresponde",
                  isinstance(botin[0], Pocion) and isinstance(botin[2], Arma) and botin[2].ataque_bonus == 3)
        comprobar("quedan en la sala del enemigo (2)", all(o.id_sala == 2 for o in botin))
        comprobar("un id repetido da instancias distintas", botin[0] is not botin[1])
        comprobar("pedirlo otra vez da instancias nuevas", servicio.objetos_que_suelta(ladron)[0] is not botin[0])
        comprobar("un enemigo que no suelta nada da []", servicio.objetos_que_suelta(esqueleto) == [])
        comprobar("no cuesta solicitudes: las fichas llegaron con la sala", http.solicitudes_realizadas == solicitudes,
                  f"(antes {solicitudes}, después {http.solicitudes_realizadas})")
        comprobar("al cargar la sala se pidió el catálogo 2 veces: enemigos y, aparte, su botín",
                  http.veces("catalogo") == 2, f"({http.veces('catalogo')})")

        print("== 2) Si la ficha no se había traído, se pide sola y en un solo lote ==")
        http2 = HttpBotin()
        servicio2 = servicio_de_servicio(os.path.join(raiz, "d2"), http2)
        servicio2.listar_criptas()
        sin_traer = SimpleNamespace(suelta=["itm_pocion_menor", "itm_daga_oxidada"], id_sala_actual=2)
        antes = http2.solicitudes_realizadas
        botin2 = servicio2.objetos_que_suelta(sin_traer)
        comprobar("sale el botín completo", nombres(botin2) == ["Poción menor", "Daga oxidada"])
        comprobar("las dos fichas se pidieron juntas, en UNA solicitud de catálogo", http2.veces("catalogo") == 1)
        comprobar("la única otra solicitud fue la verificación de versión del catálogo",
                  http2.solicitudes_realizadas - antes == 2 and http2.veces("version_catalogo") == 1,
                  f"({http2.solicitudes_realizadas - antes})")
        antes = http2.solicitudes_realizadas
        servicio2.objetos_que_suelta(sin_traer)
        comprobar("la segunda vez sale de la caché: 0 solicitudes", http2.solicitudes_realizadas == antes)

        print("== 3) En el juego: al derrotar al enemigo su botín queda en el suelo ==")
        carpeta = os.path.join(raiz, "d3")
        http3 = HttpBotin()
        juego = partida(carpeta, http3)
        jugador, sala = empezar_en_sala_2(juego)
        ladron, esqueleto = sala.enemigos
        comprobar("antes de pelear no hay nada en el suelo", sala.objetos == [])
        solicitudes = http3.solicitudes_realizadas
        resultado = atacar(juego, jugador, ladron)
        comprobar("el ataque tuvo éxito y el ladrón murió", resultado.exito and ladron.vida_actual <= 0)
        comprobar("el mensaje cuenta qué suelta", "Ladrón suelta: Poción menor, Poción menor, Daga oxidada" in resultado.mensaje,
                  f"-> {resultado.mensaje!r}")
        sala = juego.obtenerSala(2)
        comprobar("en el suelo hay 2 pociones y la daga", nombres(sala.objetos) == ["Poción menor", "Poción menor", "Daga oxidada"])
        comprobar("matar no gastó solicitudes", http3.solicitudes_realizadas == solicitudes)
        resultado = atacar(juego, jugador, ladron)
        comprobar("atacar a un enemigo ya muerto no vuelve a soltar nada",
                  not resultado.exito and len(sala.objetos) == 3)
        resultado = atacar(juego, jugador, esqueleto)
        comprobar("un enemigo sin botín no agrega nada", resultado.exito and len(sala.objetos) == 3
                  and "suelta" not in resultado.mensaje, f"-> {resultado.mensaje!r}")

        print("== 4) El jugador puede recoger lo que soltaron ==")
        daga = sala.objetos[2]
        juego.accionJugador(EventoDTO(25, 0, jugador, "RECOGER_OBJETO", [daga]))
        comprobar("recoger la daga la mueve al inventario", daga not in sala.objetos and jugador.inventario.cantidad_actual == 1)

        print("== 5) El pergamino de retroceso deshace la muerte y el botín juntos ==")
        http5 = HttpBotin()
        juego5 = partida(os.path.join(raiz, "d5"), http5)
        jugador5, sala5 = empezar_en_sala_2(juego5)
        ladron5 = sala5.enemigos[0]
        atacar(juego5, jugador5, ladron5)
        comprobar("tras matar hay 3 objetos en el suelo", len(juego5.obtenerSala(2).objetos) == 3)
        pergamino = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
        jugador5.inventario.agregar_objeto(pergamino)
        resultado = juego5.accionJugador(EventoDTO(50, 0, jugador5, "USAR_OBJETO", [pergamino]))
        comprobar("el pergamino funciona", resultado.exito, f"-> {resultado.mensaje!r}")
        comprobar("el ladrón volvió a la vida", ladron5.vida_actual > 0, f"(vida {ladron5.vida_actual})")
        comprobar("y el suelo quedó vacío otra vez", juego5.obtenerSala(2).objetos == [])
        atacar(juego5, jugador5, ladron5)
        comprobar("al matarlo de nuevo vuelve a soltar lo mismo (sin duplicar)",
                  nombres(juego5.obtenerSala(2).objetos) == ["Poción menor", "Poción menor", "Daga oxidada"])

        print("== 6) Guardar y cargar la partida conserva lo que quedó en el suelo ==")
        http6 = HttpBotin()
        juego6 = partida(os.path.join(raiz, "d6"), http6)
        jugador6, sala6 = empezar_en_sala_2(juego6)
        atacar(juego6, jugador6, sala6.enemigos[0])
        juego6.guardarPartida("con_botin")
        cargada = partida(os.path.join(raiz, "d6"), HttpBotin())
        cargada.cargarPartida("con_botin")
        comprobar("la partida cargada tiene el botín en el suelo",
                  nombres(cargada.obtenerSala(2).objetos) == ["Poción menor", "Poción menor", "Daga oxidada"])

        print("== 7) --replay reproduce lo mismo, también sin red (--offline) ==")
        nombre_log = juego6.nombreLog()
        repetida = partida(os.path.join(raiz, "d6"), HttpBotin())
        repetida.repetirPartida(nombre_log)
        comprobar("la reproducción deja el mismo botín en el suelo",
                  nombres(repetida.obtenerSala(2).objetos) == ["Poción menor", "Poción menor", "Daga oxidada"])
        sin_red = HttpBotin()
        offline = partida(os.path.join(raiz, "d6"), sin_red, offline=True)
        offline.repetirPartida(nombre_log)
        comprobar("y con --offline también (las fichas del botín quedaron en disco)",
                  nombres(offline.obtenerSala(2).objetos) == ["Poción menor", "Poción menor", "Daga oxidada"]
                  and sin_red.solicitudes_realizadas == 0)

        print("== 8) Si no se puede obtener el botín, el combate sigue ==")
        juego8 = partida(os.path.join(raiz, "d8"), HttpBotin())
        jugador8, sala8 = empezar_en_sala_2(juego8)

        def roto(_enemigo):
            raise OSError("disco no disponible")
        juego8._estadoJuegoLogica.gestorEventos.obtener_botin = roto
        resultado = atacar(juego8, jugador8, sala8.enemigos[0])
        comprobar("el ataque sigue siendo válido y el enemigo muere",
                  resultado.exito and sala8.enemigos[0].vida_actual <= 0)
        comprobar("el mensaje avisa que no se pudo obtener el botín", "No se pudo obtener" in resultado.mensaje,
                  f"-> {resultado.mensaje!r}")
        comprobar("no queda nada en el suelo", juego8.obtenerSala(2).objetos == [])
    finally:
        os.chdir(anterior)

print()
print(f"{sum(resultados)} de {len(resultados)} comprobaciones correctas")
raise SystemExit(0 if all(resultados) else 1)
