"""Niebla de guerra y mapa conocido (FR-223 a FR-226, SC-006): lo que cuesta consultar, explorar y deshacer, con la
ALTERNATIVA DESCARTADA de cada decisión (principio VII). Contrato: specs/002-niebla-de-guerra/contracts/bench-mapa.md.

  A. Consulta            elegida: arreglo por id de sala        | descartada: recorrer una lista de salas conocidas
  B. Exploración         `entrar` sin y con antorcha            | criterio DURO por conteo (FR-224)
  C. Antorcha            bucle directo sobre las salidas        | descartada: RecorridoPorNiveles con límite 1
  D. Orden del comando   ordenar al consultar (ordenar_adaptativo) | descartadas: escanear el arreglo; lista siempre ordenada
  E. Reversión           diferencias con valor anterior         | descartada: instantánea de los arreglos
  F. Observación         aviso al cambiar + lectura al entrar   | descartada: sondeo de las puertas tras cada evento
  G. Vista para rutas    consulta directa a los arreglos        | descartada: mapa conocido materializado
  H. Equivalencia        el conocimiento incremental coincide con la referencia reconstruida desde cero

Lección de la 005: el criterio duro es por CONTEO; la razón de tiempos solo se informa. Las alternativas descartadas existen
SOLO aquí. Criptas sintéticas deterministas por semilla; sin red ni vista. Sin dict/set/sorted().
"""
from __future__ import annotations

from bench.datos import azar
from bench.medicion import anotar, medir, nota, texto, verificar
from DTO.SalaDTO import SalaDTO, SalidaDTO
from Logica.BuscadorRutas import BuscadorRutas
from Logica.MapaConocido import MapaConocido, VistaMapaConocido, EXPLORADA, ABIERTA, AVISTADA
from Logica.MapaCripta import MapaCripta
from Logica.PuertasLogica import fijar_cerrada
from Logica.RecorridoPorNiveles import RecorridoPorNiveles
from Logica.ordenamiento import ordenar_adaptativo
from tests_labs.cripta_sintetica import esqueleto_rejilla, mapa_dto_desde_esqueleto

SECCION_A = "Mapa conocido (A): consulta del estado de una sala y de una puerta (FR-223, SC-006)"
SECCION_B = "Mapa conocido (B): exploración al entrar, sin y con antorcha (FR-224)"
SECCION_C = "Mapa conocido (C): antorcha, bucle directo frente a RecorridoPorNiveles con límite 1"
SECCION_D = "Mapa conocido (D): orden de las exploradas para el comando mapa (FR-217)"
SECCION_E = "Mapa conocido (E): reversión con el pergamino, diferencias frente a instantánea de arreglos (FR-225)"
SECCION_F = "Mapa conocido (F): observación de puertas, aviso al cambiar frente a sondeo tras cada evento"
SECCION_G = "Mapa conocido (G): vista para rutas, consulta directa frente a mapa materializado"
SECCION_H = "Mapa conocido (H): equivalencia con la referencia reconstruida desde cero (SC-003)"

TAMANOS = ((20, 20), (20, 100), (100, 200))          # 400, 2 000 y 20 000 salas: el mayor, 50 veces el menor
CONSULTAS = 1000


class _Jugador:
    def __init__(self, sala: int) -> None:
        self.id_sala_actual = sala


class _ListaContada(list):
    lecturas = 0

    def __getitem__(self, i):
        _ListaContada.lecturas += 1
        return list.__getitem__(self, i)


def _cripta(ancho: int, alto: int, explorado: int):
    """Conocimiento sobre una rejilla con `explorado` salas ya exploradas (las primeras por id, lejos del centro)."""
    esqueleto = esqueleto_rejilla(ancho, alto, semilla=1, costo_max=300, fraccion_cerradas=0.1)
    mapa_dto = mapa_dto_desde_esqueleto(esqueleto)
    mapa = MapaCripta(mapa_dto)
    nombres = [("" if s is None else s.nombre) for s in mapa_dto.salas]
    registrados: list = []
    c = MapaConocido(mapa, nombres, [None] * mapa.tamano, _Jugador(1), registrados.append)
    for sala in range(1, explorado + 1):
        c.entrar(sala)
    registrados.clear()
    return c, registrados, esqueleto


def _centro(ancho: int, alto: int) -> int:
    return (alto // 2) * ancho + ancho // 2 + 1


def _deshacer_todo(c, registrados: list) -> None:
    for cambios in reversed(registrados):
        for cambio in reversed(cambios):
            c.deshacer(cambio)
    registrados.clear()


# --------------------------------------------------------------------------- A

def seccion_a(filas: list) -> bool:
    cumple = True
    for ancho, alto in TAMANOS:
        total = ancho * alto
        for etiqueta, explorado in (("k=1", 1), ("k=N/10", total // 10)):
            c, _, _ = _cripta(ancho, alto, explorado)
            salas_probadas = [1 + (i * 37) % total for i in range(CONSULTAS)]
            conocidas = list(c.exploradas)                         # alternativa: lista de salas conocidas

            def arreglo():
                t = 0
                for s in salas_probadas:
                    t += c.estado_de(s) + c.puerta_recordada(s, 2)

            def lista():
                t = 0
                for s in salas_probadas:
                    for conocida in conocidas:
                        if conocida == s:
                            t += 2
                            break

            c.estado = _ListaContada(c.estado)
            c.puertas = _ListaContada(c.puertas)
            _ListaContada.lecturas = 0
            c.estado_de(total // 2)
            lecturas_estado = _ListaContada.lecturas
            _ListaContada.lecturas = 0
            c.puerta_recordada(total // 2, 2)
            lecturas_puerta = _ListaContada.lecturas
            c.estado = list(c.estado)
            c.puertas = list(c.puertas)
            cumple = verificar(filas, SECCION_A, f"{total:>6} salas, {etiqueta}: una posición leída por consulta (estado y puerta)",
                               lecturas_estado == 1 and lecturas_puerta == 1) and cumple
            anotar(filas, SECCION_A, f"{total:>6} salas, {etiqueta:<7} {CONSULTAS} consultas, arreglo (elegida)", medir(arreglo))
            if explorado * CONSULTAS <= 2_000_000:
                anotar(filas, SECCION_A, f"{total:>6} salas, {etiqueta:<7} {CONSULTAS} consultas, lista de conocidas (descartada)", medir(lista, repeticiones=3))
    return cumple


# --------------------------------------------------------------------------- B

def seccion_b(filas: list) -> bool:
    cumple = True
    medidas_sin: list = []
    medidas_con: list = []
    for ancho, alto in TAMANOS:
        total = ancho * alto
        for etiqueta, explorado in (("mapa vacío", 1), ("k=N/10", total // 10)):
            c, registrados, _ = _cripta(ancho, alto, explorado)
            centro = _centro(ancho, alto)
            for antorcha in (False, True):
                def preparar():
                    _deshacer_todo(c, registrados)

                def entrar(_):
                    c.entrar(centro, antorcha)

                preparar()
                c.entrar(centro, antorcha)
                (medidas_con if antorcha else medidas_sin).append((c.salas_reveladas, c.salidas_examinadas, len(registrados[0])))
                preparar()
                anotar(filas, SECCION_B, f"{total:>6} salas, {etiqueta:<10} entrar {'con' if antorcha else 'sin'} antorcha",
                       medir(entrar, preparar))
    for antorcha in (False, True):
        medidas = medidas_con if antorcha else medidas_sin
        iguales = all(m == medidas[0] for m in medidas)
        cumple = verificar(filas, SECCION_B, f"{'con' if antorcha else 'sin'} antorcha: salas reveladas, salidas examinadas y cambios iguales "
                           f"en los tres tamaños y con el mapa vacío o grande {medidas[0]}", iguales) and cumple
    return cumple


# --------------------------------------------------------------------------- C

def seccion_c(filas: list) -> bool:
    cumple = True
    for ancho, alto in TAMANOS:
        total = ancho * alto
        c, _, _ = _cripta(ancho, alto, 1)
        mapa = c.mapa
        recorrido = RecorridoPorNiveles(mapa)
        centro = _centro(ancho, alto)

        def vecinas_directo():
            estado = [0] * mapa.tamano
            for a in mapa.salidas(centro):
                d = a.destino
                if 0 <= d < mapa.tamano and mapa.existe[d]:
                    estado[d] = 2
                    for b in mapa.salidas(d):
                        if estado[b.destino] == 0:
                            estado[b.destino] = 1
            return estado

        def vecinas_recorrido():
            estado = [0] * mapa.tamano
            for s in recorrido.recorrer(centro, 1).salas:
                if s == centro:
                    continue
                estado[s] = 2
                for b in mapa.salidas(s):
                    if estado[b.destino] == 0:
                        estado[b.destino] = 1
            return estado

        a, b = vecinas_directo(), vecinas_recorrido()
        a[centro] = b[centro] = 0
        cumple = verificar(filas, SECCION_C, f"{total:>6} salas: ambos exploran el mismo conjunto de vecinas", a == b) and cumple
        anotar(filas, SECCION_C, f"{total:>6} salas, bucle directo (elegida)", medir(vecinas_directo))
        anotar(filas, SECCION_C, f"{total:>6} salas, RecorridoPorNiveles límite 1 (descartada)", medir(vecinas_recorrido))
    return cumple


# --------------------------------------------------------------------------- D

def _insertar_ordenada(lista: list, valor: int) -> None:
    bajo, alto = 0, len(lista)
    while bajo < alto:                                   # búsqueda binaria propia (sin bisect)
        medio = (bajo + alto) // 2
        if lista[medio] < valor:
            bajo = medio + 1
        else:
            alto = medio
    lista.insert(bajo, valor)


def seccion_d(filas: list) -> bool:
    cumple = True
    rng = azar(3)
    for ancho, alto in TAMANOS:
        total = ancho * alto
        for k in (50, 500, 5000):
            if k > total // 2:
                continue
            descubrimiento = []                               # orden de descubrimiento: un paseo aleatorio en la rejilla
            x, y = ancho // 2, alto // 2
            vistos = [False] * (total + 1)
            while len(descubrimiento) < k:
                n = y * ancho + x + 1
                if not vistos[n]:
                    vistos[n] = True
                    descubrimiento.append(n)
                dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                x, y = min(ancho - 1, max(0, x + dx)), min(alto - 1, max(0, y + dy))
            estado = [0] * (total + 1)
            for s in descubrimiento:
                estado[s] = 2

            def ordenar_al_consultar():
                return ordenar_adaptativo(descubrimiento)

            def escanear_el_arreglo():
                r = []
                for s in range(1, total + 1):
                    if estado[s] == 2:
                        r.append(s)
                return r

            def mantener_ordenada():
                r = []
                for s in descubrimiento:
                    _insertar_ordenada(r, s)
                return r

            a, b, m = ordenar_al_consultar(), escanear_el_arreglo(), mantener_ordenada()
            cumple = verificar(filas, SECCION_D, f"{total:>6} salas, k={k}: los tres métodos dan el mismo orden", a == b == m) and cumple
            anotar(filas, SECCION_D, f"{total:>6} salas, k={k:<5} ordenar al consultar (elegida)", medir(ordenar_al_consultar))
            anotar(filas, SECCION_D, f"{total:>6} salas, k={k:<5} escanear el arreglo (descartada)", medir(escanear_el_arreglo))
            anotar(filas, SECCION_D, f"{total:>6} salas, k={k:<5} mantener ordenada, k inserciones (descartada)", medir(mantener_ordenada))
            if k == 5000 or (k == 500 and total < 20000):
                # tiempo del comando completo: armar el DTO con k salas
                c, _, _ = _cripta(ancho, alto, k)
                anotar(filas, SECCION_D, f"{total:>6} salas, k={k:<5} comando completo (instantánea)", medir(c.instantanea, repeticiones=3))
    nota(filas, SECCION_D, "Se informan los cruces: el escaneo gana cuando k pasa de aprox. N/8; ordenar gana con k pequeño (research §3)")
    return cumple


# --------------------------------------------------------------------------- E

def seccion_e(filas: list) -> bool:
    cumple = True
    contados = []
    for ancho, alto in TAMANOS:
        total = ancho * alto
        for habitaciones in (1, 4, 16):
            c, registrados, _ = _cripta(ancho, alto, 1)
            centros = [((total // 2) + i * (ancho + 3)) % total + 1 for i in range(habitaciones)]

            def preparar():
                _deshacer_todo(c, registrados)
                for sala in centros:
                    c.entrar(sala, True)

            def deshacer_diferencias(_=None):
                n = 0
                for cambios in reversed(registrados):
                    for cambio in reversed(cambios):
                        c.deshacer(cambio)
                        n += 1
                registrados.clear()
                return n

            preparar()
            r = sum(len(cambios) for cambios in registrados)
            antes_estado, antes_puertas = list(c.estado), list(c.puertas)
            revertidos = deshacer_diferencias()
            cumple = verificar(filas, SECCION_E, f"{total:>6} salas, {habitaciones} entradas: cambios revertidos = cambios registrados ({r})", revertidos == r) and cumple
            if habitaciones == 1:
                contados.append(revertidos)
            preparar()

            def instantanea_copiar_y_restaurar(_=None):
                copia = (list(c.estado), list(c.puertas), list(c.exploradas))
                c.estado[:] = antes_estado
                c.puertas[:] = antes_puertas
                return copia

            anotar(filas, SECCION_E, f"{total:>6} salas, r={r:<3} diferencias (elegida)", medir(deshacer_diferencias, preparar))
            anotar(filas, SECCION_E, f"{total:>6} salas, r={r:<3} instantánea de arreglos (descartada)", medir(instantanea_copiar_y_restaurar))
    cumple = verificar(filas, SECCION_E, "revertir una entrada con antorcha cuesta los mismos cambios en los tres tamaños", all(n == contados[0] for n in contados)) and cumple
    return cumple


# --------------------------------------------------------------------------- F

def _salas_reales(esqueleto: list, ancho: int, alto: int) -> list:
    salas = [None] * (len(esqueleto) + 1)
    nombre_de = ("norte", "sur", "este", "oeste")
    letras = ("N", "S", "E", "O")
    for datos in esqueleto:
        sala = SalaDTO(datos["id"], datos["nombre"])
        for i in range(4):
            if letras[i] in datos["salidas"]:
                d = datos["salidas"][letras[i]]
                sala.salidas.append(SalidaDTO(nombre_de[i], d["sala"], d.get("cerrada", False), None, None, d.get("costo", 100)))
        salas[datos["id"]] = sala
    return salas


def seccion_f(filas: list) -> bool:
    cumple = True
    ancho, alto = 20, 20
    eventos = 1000
    for etiqueta, cada in (("cambios raros (1 %)", 100), ("cambios frecuentes (50 %)", 2)):
        puertas_de: list = []
        lecturas_de: list = []
        for metodo in ("aviso", "sondeo"):
            c, _, esqueleto = _cripta(ancho, alto, 1)
            salas = _salas_reales(esqueleto, ancho, alto)
            c.salas = salas
            jugador = c.jugador
            jugador.id_sala_actual = _centro(ancho, alto)
            c.iniciar(jugador.id_sala_actual)
            sala = salas[jugador.id_sala_actual]
            salida = sala.salidas[0]
            contador = [0]                                     # lecturas del esqueleto para saber el estado real de una puerta
            original = c.mapa.esta_abierta

            def contada(arista, s, original=original, contador=contador):
                contador[0] += 1
                return original(arista, s)
            c.mapa.esta_abierta = contada

            def sondear():
                for arista in list(c.mapa.salidas(jugador.id_sala_actual)) + list(c.mapa.entrantes(jugador.id_sala_actual)):
                    c._observar(arista, [])

            def correr():
                contador[0] = 0
                for i in range(eventos):
                    cambia = i % cada == 0
                    if cambia:
                        fijar_cerrada(salida, not salida.cerrada, c.puerta_cambio if metodo == "aviso" else None)
                    if metodo == "sondeo":
                        sondear()
                return contador[0]

            lecturas = correr()
            puertas_de.append(list(c.puertas))
            lecturas_de.append(lecturas)
            anotar(filas, SECCION_F, f"{etiqueta:<26} {metodo:<7} {eventos} eventos", medir(correr, repeticiones=5))
            c.mapa.esta_abierta = original
        cumple = verificar(filas, SECCION_F, f"{etiqueta}: aviso y sondeo dejan las mismas puertas recordadas", puertas_de[0] == puertas_de[1]) and cumple
        cumple = verificar(filas, SECCION_F, f"{etiqueta}: con el aviso, 0 lecturas del esqueleto por evento (el sondeo hizo {lecturas_de[1]})",
                           lecturas_de[0] == 0) and cumple
    return cumple


# --------------------------------------------------------------------------- G

class _VistaMaterializada:
    """ALTERNATIVA DESCARTADA: un mapa nuevo con copias de las salidas de las salas exploradas, reconstruido tras cada cambio."""

    def __init__(self, c: MapaConocido) -> None:
        self.tamano = c.mapa.tamano
        self._salientes = [[] for _ in range(self.tamano)]
        self._entrantes = [[] for _ in range(self.tamano)]
        for sala in c.exploradas:
            for a in c.mapa.salidas(sala):
                if 0 <= a.destino < self.tamano and c.estado[a.destino] == EXPLORADA \
                        and c.puertas[a.origen * 4 + c.indice_direccion(a.direccion)] == ABIERTA:
                    self._salientes[sala].append(a)
                    self._entrantes[a.destino].append(a)

    def salidas(self, sala):
        return self._salientes[sala]

    def entrantes(self, sala):
        return self._entrantes[sala]

    def transitable(self, arista):
        return True


def seccion_g(filas: list) -> bool:
    cumple = True
    for ancho, alto in TAMANOS:
        total = ancho * alto
        c, _, _ = _cripta(ancho, alto, min(300, total // 4))
        destino = c.exploradas[len(c.exploradas) // 2]
        buscador_a, buscador_b = BuscadorRutas(), BuscadorRutas()
        buscador_a.distancias_hacia(destino, VistaMapaConocido(c), 10 ** 9)
        buscador_b.distancias_hacia(destino, _VistaMaterializada(c), 10 ** 9)
        iguales = True
        for sala in range(c.mapa.tamano):
            if buscador_a.costo(sala) != buscador_b.costo(sala):
                iguales = False
        cumple = verificar(filas, SECCION_G, f"{total:>6} salas: ambas vistas dan los mismos costos", iguales) and cumple

        def con_vista():
            BuscadorRutas().distancias_hacia(destino, VistaMapaConocido(c), 10 ** 9)

        def con_materializado():
            BuscadorRutas().distancias_hacia(destino, _VistaMaterializada(c), 10 ** 9)

        anotar(filas, SECCION_G, f"{total:>6} salas, tras un cambio: vista directa (elegida)", medir(con_vista, repeticiones=5))
        anotar(filas, SECCION_G, f"{total:>6} salas, tras un cambio: materializar y buscar (descartada)", medir(con_materializado, repeticiones=5))
    return cumple


# --------------------------------------------------------------------------- H

def seccion_h(filas: list) -> bool:
    from DTO.Objeto import PergaminoRetroceso
    from tests_labs.partida_prueba import jugar, nueva_partida
    from tests_labs.referencia_conocimiento import capturar_reales, comprobar_invariantes, diferencias, reconstruir
    rng = azar(5)
    logica = nueva_partida(esqueleto_rejilla(10, 10, semilla=2))
    c = logica.mapaConocido
    salas = logica.estadoJuego.salas
    jugador = logica.estadoJuego.jugador
    grupos = [[("entrar", jugador.id_sala_actual, False, capturar_reales(c.mapa, salas, jugador.id_sala_actual))]]
    deshacibles = 0
    pasos = 150
    coinciden = 0
    for _ in range(pasos):
        opcion = rng.random()
        if opcion < 0.2:
            objeto = PergaminoRetroceso("itm_pergamino", "Pergamino", 1, 1)
            jugador.inventario.agregar_objeto(objeto)
            jugar(logica, "USAR_OBJETO", [objeto])
            if deshacibles > 0:
                grupos.pop()
                deshacibles -= 1
        else:
            antorcha = rng.random() < 0.4
            jugador.antorcha_encendida = antorcha
            sala = salas[jugador.id_sala_actual]
            direccion = rng.choice([s.direccion for s in sala.salidas])
            jugar(logica, "MOVER_JUGADOR", [sala, str(getattr(direccion, "value", direccion))])
            actual = jugador.id_sala_actual
            grupos.append([("entrar", actual, antorcha, capturar_reales(c.mapa, salas, actual))])
            deshacibles = min(5, deshacibles + 1)
        historia = []
        for g in grupos:
            historia.extend(g)
        if diferencias(c, reconstruir(c.mapa, historia)) == [] and comprobar_invariantes(c, c.mapa, salas, jugador) == []:
            coinciden += 1
    return verificar(filas, SECCION_H, f"{coinciden} de {pasos} pasos idénticos a la referencia (acciones y pergaminos)", coinciden == pasos)


def ejecutar(filas: list) -> bool:
    cumple = seccion_a(filas)
    cumple = seccion_b(filas) and cumple
    cumple = seccion_c(filas) and cumple
    cumple = seccion_d(filas) and cumple
    cumple = seccion_e(filas) and cumple
    cumple = seccion_f(filas) and cumple
    cumple = seccion_g(filas) and cumple
    cumple = seccion_h(filas) and cumple
    return cumple
