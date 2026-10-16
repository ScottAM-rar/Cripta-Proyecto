# Capa de comunicación, caché y persistencia: documentación

Autor de esta capa: Persona 3 (Cliente de API, caché y persistencia).
Carpeta: `adaptadores/`. Pruebas: `tests_labs/`.

Este documento tiene dos usos:

- **Para el equipo:** la sección 2 ("Guía rápida") dice qué llamar desde el motor y desde `main`, sin
  necesidad de leer el resto.
- **Para entender cómo funciona por dentro:** las secciones 4 a 9 explican cada pieza, en el orden en que
  se construyeron.

---

## 1. La idea en una imagen

```
 API en internet                              disco (carpeta datos_cripta/)
      ▲                                              ▲
      │ HTTP                                         │ archivos binarios
 ┌────┴──────────┐   ┌─────────────────┐   ┌─────────┴───────┐
 │ ClienteCripta │   │ ClientePersis-  │   │  AlmacenDisco   │
 │ (cliente_http)│◄──┤ tente           ├──►│ → ArchivoIndex. │
 └───────────────┘   └────────▲────────┘   └─────────▲───────┘
                              │                      │
        ┌─────────────────────┴──┐        ┌──────────┴────────┐
        │ ServicioCripta         │        │ ClienteOffline    │
        │ (usa UNO de los dos)   │        │ (solo lee disco)  │
        └───────────▲────────────┘        └───────────────────┘
                    │ SalaDTO, JugadorDTO
              el motor del juego
```

Las capas, de arriba hacia abajo:

| Capa | Archivo | Su único trabajo |
|---|---|---|
| Fábrica | `fabrica.py` | Armar todo lo de abajo según `--offline` y `--cache-size` |
| Servicio | `servicioCripta.py` | Entregar `SalaDTO` y `JugadorDTO` ya listos |
| Resolución | `resolucion.py` | Traducir el JSON de la API a objetos del juego (DTO) |
| Caché | `cache.py` | Recordar fichas del catálogo en memoria (LRU) |
| Cliente con disco | `cliente_persistente.py` | Usar el disco antes que la red, validando versiones |
| Cliente sin conexión | `cliente_offline.py` | Servir todo desde el disco, sin red |
| Almacén | `AlmacenDisco.py` | Guardar/leer lo de la API en archivos, con versión |
| Archivo | `Archivo_indexado.py` | El formato binario con índice |
| Cliente de red | `cliente_http.py` | Hablar con la API |
| Contrato | `Interfaz.py` | Lo que todo cliente debe saber hacer (`ClienteInterfaz`) |

Todos los clientes cumplen el mismo contrato (`ClienteInterfaz`: 7 métodos y la propiedad `solicitudes_realizadas`). Por eso `ServicioCripta`
no sabe si le llegan datos de internet o del disco, y cambiar de modo no afecta a nadie más.

---

## 2. Guía rápida para el equipo

### 2.1 Arrancar

```python
from adaptadores.fabrica import crear_servicio

servicio = crear_servicio(offline=False, cache_size=25)
```

- `offline=True` juega solo con lo guardado en disco (flag `--offline`).
- `cache_size` es la capacidad de la caché de fichas (flag `--cache-size`, por defecto 25).
- **Un solo servicio por partida.** No crear `ClienteCripta` ni `ServicioCripta` a mano.

### 2.2 Lo que se puede pedir

```python
servicio.listar_criptas()               # ['Cripta 1: Osario menor']  (para mostrar un menú)
cid = servicio.obtener_id_cripta(1)     # 'cripta-01' (la posición empieza en 1)
servicio.existe_cripta(cid)             # True / False
servicio.total_salas(cid)               # 6

jugador = servicio.crear_jugador(cid)   # JugadorDTO con las stats que define la cripta
servicio.precargar(cid)                 # trae TODAS las salas de golpe (ver 2.3)
sala = servicio.construir_sala(cid, 3)  # SalaDTO de la sala 3 (los ids de sala empiezan en 1)

servicio.obtener_sala_salida(cid)       # id de la sala donde se gana
servicio.datos_cripta(cid)["llave_salida"]   # id de la llave que hace falta para ganar

servicio.solicitudes_realizadas         # solicitudes de red usadas hasta ahora (0 si es offline)
servicio.presupuesto_solicitudes(cid)   # el máximo permitido (9)
```

### 2.3 Orden recomendado al iniciar una partida

```python
servicio = crear_servicio(offline=args.offline, cache_size=args.cache_size)
print(servicio.listar_criptas())
cid = servicio.obtener_id_cripta(eleccion)
jugador = servicio.crear_jugador(cid)
servicio.precargar(cid)                     # 1 vez: deja todo en disco, en pocas solicitudes
sala = servicio.construir_sala(cid, jugador.id_sala_actual)
```

Sin `precargar`, cada sala nueva cuesta 2 solicitudes (contenido + fichas) y una cripta de 6 salas se
pasa del límite de 9. Con `precargar`, las `construir_sala` siguientes salen del disco y cuestan 0.

### 2.4 Cosas que hay que saber

- **`construir_sala` devuelve una `SalaDTO` NUEVA cada vez.** Si el motor ya la construyó, tiene que
  guardarla (en `estadoJuego.salas`) y no volver a pedirla; si no, pierde puertas abiertas, enemigos
  muertos, etc.
- **Los ids de sala empiezan en 1**, no en 0. Una lista de N salas indexada por id necesita N + 1 posiciones.
- **Victoria:** el jugador gana al estar en `obtener_sala_salida(cid)` con la llave `datos["llave_salida"]`.
  El servicio solo entrega los datos; la comprobación la hace el motor.
- **Errores que el motor/`main` debe capturar** (detalle en la sección 10):
  `ErrorSinConexion` (sugerir `--offline`) y `ErrorOffline` (sugerir jugar una vez con conexión).
- **Al terminar:** mostrar `servicio.solicitudes_realizadas` frente a `presupuesto_solicitudes(cid)`.

---

## 3. Reglas de oro

1. **Un solo servicio por partida, creado con `crear_servicio()`.** El `ClienteCripta` genera un
   `client_id` (uuid) que la API usa para identificarnos y lleva el contador de solicitudes. Si cada
   módulo crea el suyo, la API nos ve como jugadores distintos y el conteo queda partido.
2. **Nadie fuera de `adaptadores/` usa `requests` ni lee JSON.** Así el cliente online se cambia por el
   offline sin que nadie más se entere (patrón Adaptador).
3. **Cada solicitud HTTP real cuenta** para el límite del enunciado (§5.1). Los 429 también.
4. **Estructuras permitidas: Pila, Cola, Array, Lista simple, Lista doble.** No hay árboles, hash,
   `set` ni `dict` propios (ni como índice, ni como caché, ni como tabla de búsqueda). Las únicas
   excepciones son los diccionarios que la API/JSON entregan por naturaleza: se **leen**
   (`ficha["campo"]`) en la frontera, pero no se usan como estructura del programa. Las búsquedas son
   lineales sobre listas, y las decisiones por tipo usan `match/case`.
5. **Nada se guarda en el repo:** la carpeta `datos_cripta/` está en `.gitignore`.

---

## 4. El cliente de red (`cliente_http.py`)

`ClienteCripta(base_url)` es la única clase que habla con internet. Todo pasa por `_solicitar(ruta)`.

| Método | Endpoint | Devuelve |
|---|---|---|
| `obtener_criptas()` | `GET /criptas` | `list[dict]` con `{id, nombre, salas, dificultad}` |
| `obtener_datos_generales(id)` | `GET /criptas/{id}` | `dict`: `version`, `sala_inicial`, `sala_salida`, `llave_salida`, `inventario_max`, `presupuesto_solicitudes`, `jugador` |
| `obtener_version_cripta(id)` | `GET /criptas/{id}/version` | `str` |
| `obtener_salas(id)` | `GET /criptas/{id}/salas?pagina=N` | `list[dict]` con **todas** las salas (el esqueleto del mapa) |
| `obtener_contenido(id, [salas])` | `GET /criptas/{id}/contenido?salas=1,2,..` | `list[dict]`: qué hay en cada sala |
| `obtener_catalogo([ids])` | `GET /catalogo?ids=a,b,..` | `list[dict]`: fichas completas |
| `obtener_version_catalogo()` | `GET /catalogo/version` | `str` |

Todas las llamadas llevan el header `X-Cripta-Client-Id`.

**Lo que el cliente hace solo:**

- **Lotes de 10.** La API acepta como máximo 10 salas o 10 ids por llamada. Con 25 salas el cliente hace
  3 solicitudes (10 + 10 + 5).
- **Paginación.** `obtener_salas` repite hasta llegar a `total_paginas`.
- **Error 429** (demasiadas solicitudes): espera `reintentar_en` segundos y reintenta, hasta
  `MAX_REINTENTOS_429 = 5` veces; después lanza `RuntimeError`. El reintento **también cuenta** como solicitud.
- **Sin conexión o tiempo agotado:** lanza `ErrorSinConexion` con un mensaje que sugiere `--offline`.
  Una solicitud que nunca llegó al servidor no suma al contador.
- **Otros errores** (400, 404, 500): `RuntimeError` con la URL y el código.

---

## 5. De JSON a objetos del juego

### 5.1 Las dos fuentes de un enemigo (lo más importante de entender)

`/contenido` solo dice **qué hay y dónde**:

```python
{"sala": 2,
 "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": None}],
 "objetos": ["itm_antorcha"],
 "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]}
```

No trae ataque, defensa ni vida máxima. Eso está en la **ficha del catálogo**
(`/catalogo?ids=ent_rata_gigante`). Para tener un enemigo completo hay que **cruzar las dos**:

| Fuente | Aporta |
|---|---|
| `/contenido` (colocación) | `instancia` (cuál rata concreta), `tipo`, `vida` actual |
| `/catalogo` (ficha) | nombre, `vida_max`, ataque, defensa, velocidad, comportamiento, `suelta` |

Analogía: `/contenido` es la lista de quién está en cada sala; `/catalogo` es el expediente de cada tipo.

**Regla de la vida:** si la colocación trae un número, ese es el daño ya sufrido y se respeta. Si trae
`null` **o no trae la clave**, el enemigo está sano y `vida_actual = ficha.vida_max`.

### 5.2 `resolucion.py` función por función

- **`resolver_objeto(ficha, id_sala=None) -> Objeto`**: convierte la ficha en la subclase correcta
  (`Arma`, `Armadura`, `Pocion`, `Antidoto`, `Llave`, `Antorcha`, `PergaminoRetroceso`) según su campo
  `clase`, que se decide con `_clase_de_objeto` (un `match/case`). Renombra `id` a `id_catalogo`, quita
  `clase`, y agrega `id_sala` solo si se indica (un objeto del inventario no está en ninguna sala). Trabaja
  sobre una copia para no alterar la ficha original. Una clase desconocida lanza `ValueError`.
- **`resolver_ficha_enemigo(ficha) -> EnemigoCatalogoDTO`**: la plantilla de un tipo de enemigo.
- **`resolver_enemigo(colocacion, ficha, id_sala) -> EnemigoDTO`**: el cruce de la sección 5.1.
  `colocacion.get("vida")` porque la API a veces no incluye la clave, y `suelta=list(ficha.suelta)` es una
  **copia**: sin ella, todas las ratas compartirían la misma lista en memoria.
- **`resolver_trampa(colocacion, ficha, id_sala) -> Trampa`**: `instancia` sale de la colocación;
  `daño` y `rearme` de la ficha; `id_sala` lo da quien llama.
- **`resolver_sala(cliente, cache, cripta_id, numero_sala)`**: pide el contenido de una sala, junta los
  ids de catálogo necesarios (sin repetidos), mira primero la caché, pide **solo lo que falta en una sola
  tanda** y arma `(enemigos, objetos, trampas)`.
- **`resolver_salas(cliente, cache, cripta_id, numeros)`**: lo mismo para varias salas a la vez. El
  contenido se pide en lotes de 10 y cada ficha se pide una sola vez aunque se repita entre salas.

---

## 6. La caché (`CacheLRU`)

Guarda fichas por id en memoria. Capacidad por defecto: **25** (`--cache-size`, §4.4).

- **Estructura:** un `deque` de entradas `[clave, valor, veces_en_uso]`. Sin `dict`. Lo más reciente va al
  frente; las búsquedas son lineales (n ≤ capacidad).
- **LRU:** cuando está llena se desaloja la entrada menos usada (la del fondo).
- **`obtener(clave)`:** devuelve el valor y lo pasa al frente; `None` si no está.
- **`insertar(clave, valor)`:** actualiza si existe; si no, desaloja si hace falta y agrega. Devuelve
  `True` si se guardó y `False` si no hubo lugar.
- **`marcar_en_uso(clave)` / `marcar_libre(clave)`:** un **contador** (no un booleano, porque varias cosas
  pueden usar la misma ficha: dos ratas usan `ent_rata_gigante`). Una ficha con contador > 0 **no se
  desaloja**. El contador nunca baja de 0.
- **Nunca se supera la capacidad:** si está llena y todo está en uso, la ficha nueva no se guarda. Quien la
  pidió igual la usa, y sigue en disco.
- Ayudas: `len(cache)`, `cache.capacidad`, `cache.claves()`.

Estado actual: la protección "en uso" existe y está probada, pero **el motor todavía no llama a
`marcar_en_uso` / `marcar_libre`** (ver sección 13).

---

## 7. `ServicioCripta`: la cara que ve el motor

Recibe un cliente (online u offline) y una caché por el constructor; `crear_servicio` los arma.

| Método | Qué hace | Solicitudes |
|---|---|---|
| `listar_criptas()` | Textos `"Cripta N: nombre"` para el menú | 1 (la primera vez) |
| `obtener_id_cripta(pos)` | Id de la cripta en esa posición (desde 1) | 0 |
| `existe_cripta(id)` | `True`/`False` | 0 |
| `datos_cripta(id)` | Datos generales de la cripta (una vez por cripta) | 1 (la primera vez) |
| `crear_jugador(id)` | `JugadorDTO` con las stats de la API, vida llena, en la sala inicial | 0 extra |
| `obtener_sala_salida(id)` | Id de la sala donde se gana | 0 extra |
| `presupuesto_solicitudes(id)` | Máximo de solicitudes permitido | 0 extra |
| `total_salas(id)` | Cantidad de salas | 1 (la primera vez) |
| `construir_sala(id, n)` | `SalaDTO` de una sala (nueva cada vez) | 0 si hubo `precargar` |
| `construir_salas(id, [n])` | Varias `SalaDTO` en lote | las mínimas |
| `construir_todas(id)` | Todas las salas de la cripta | las mínimas |
| `precargar(id, [n]=None)` | Trae todo (o esas salas) de golpe y lo deja en disco | las mínimas |
| `solicitudes_realizadas` | Contador de solicitudes de red (propiedad) | |

Cómo arma una `SalaDTO`: toma el esqueleto (`nombre`, `salidas` en letras N/S/E/O) y el contenido ya
resuelto. Las salidas van en un `deque(maxlen=4)` con el orden N, S, E, O, solo con las que existen, con
la dirección como `"norte"`, `"sur"`, `"este"`, `"oeste"` y los campos `cerrada`, `llave` y
`cierre_automatico` si la API los trae.

---

## 8. Persistencia y modo sin conexión

### 8.1 `ArchivoIndexado` (`Archivo_indexado.py`): el formato binario

Guarda pares *clave de texto → valor* en un solo archivo. Estructura (números en big-endian):

```
 ┌───────────────────────────────┐
 │ ENCABEZADO  "CRPT" + versión  │  6 bytes
 ├───────────────────────────────┤
 │ REGISTROS   (uno tras otro)   │  el valor de cada clave, en JSON/UTF-8
 ├───────────────────────────────┤
 │ ÍNDICE      una entrada por   │  [largo de clave: 2][clave][posición: 8][largo: 4]
 │             clave             │
 ├───────────────────────────────┤
 │ PIE         posición del      │  12 bytes, siempre al final
 │             índice + cantidad │
 └───────────────────────────────┘
```

- **Leer una clave** no carga todo el archivo: se lee el pie (al final), con él se llega al índice, se
  recorre buscando la clave y se salta directo al registro con `seek`.
- **El índice es una lista de tuplas** `(clave, posición, largo)`; la búsqueda es lineal (sin `dict`).
- **Escritura atómica:** se reescribe todo en `archivo.tmp`, se hace `fsync` y se cambia por el real con
  `os.replace`. Si el programa se corta a mitad, queda el archivo viejo intacto, nunca uno a medias.
- **Daño:** el encabezado (`CRPT`), el pie y el índice se validan; si algo no cuadra se lanza
  `ErrorArchivo`.
- Métodos: `existe`, `claves`, `contiene`, `leer`, `escribir`, `escribir_varios`, `vaciar`.

### 8.2 `AlmacenDisco`: qué se guarda y con qué versión

Solo guarda y lee; no habla con la red. Organización de la carpeta (`datos_cripta/` por defecto):

```
datos_cripta/
    criptas.bin            clave "lista"
    catalogo.bin           clave "version" + una clave "ficha:<id>" por ficha
    cripta_<id>.bin        "version" + "datos" + "salas" + "contenido:<n>" por sala
```

Cada archivo del catálogo y de las criptas recuerda la **versión** con la que se descargó:

- `validar_catalogo(version)` / `validar_cripta(id, version)` comparan con la versión guardada. Si
  **coincide**, lo guardado sirve y devuelve `True`. Si **no coincide**, o el archivo no existe o está
  dañado, se borra, se anota la versión nueva y devuelve `False`.
- Los ids de cripta forman parte del nombre del archivo, por eso se rechazan los peligrosos (`..`, `/`, `\`, `:`,
  etc.) con `ValueError`.
- `cripta_completa(id, numeros)` dice si hay en disco todo lo necesario para jugar esa cripta sin red.

### 8.3 `ClientePersistente`: disco primero, red solo si falta

Se coloca entre `ServicioCripta` y `ClienteCripta`. Reglas:

1. **Lo que baja de la API se guarda en disco.**
2. **Antes de usar lo guardado se comprueba su versión, una vez por sesión:**
   - la de la cripta viene dentro de los datos generales (`datos["version"]`; si no vinieran, se usa el
     endpoint de versión);
   - la del catálogo se pide una vez (`/catalogo/version`).
   Si la versión cambió, lo guardado de esa parte se descarta y se vuelve a pedir.
3. **Solo se pide a la red lo que falta:** contenido de las salas que no están, fichas que no están.
   El resultado siempre sale en el mismo orden en que se pidió.
4. La lista de criptas no tiene versión: siempre se pide y se guarda (la usará el modo offline).

Solicitudes con una cripta de 3 salas (API falsa):

| Situación | Solicitudes | Qué se pide |
|---|---|---|
| Primera vez | 6 | criptas, datos, salas, contenido, versión del catálogo, catálogo |
| Segunda vez, nada cambió | 3 | criptas, datos, versión del catálogo |
| Cambió la versión de la cripta | 5 | salas y contenido otra vez; el catálogo no |
| Cambió la versión del catálogo | 4 | el catálogo otra vez; salas y contenido no |

### 8.4 `ClienteOffline`: solo disco

Cumple `ClienteInterfaz` leyendo únicamente de `AlmacenDisco`. `solicitudes_realizadas` siempre es 0.

- `obtener_criptas()` devuelve **solo las criptas que se pueden jugar completas** (con datos, salas y el
  contenido de todas sus salas). Así el menú nunca ofrece una que luego falle.
- Si falta algo, lanza `ErrorOffline` con un mensaje claro ("Juega una vez con conexión...").
- Límite conocido: no comprueba que estén todas las fichas del catálogo; si faltara una, el error aparece
  al construir la sala. `precargar` en una partida con conexión las deja todas guardadas.

### 8.5 `fabrica.py`: dónde se decide todo

```python
crear_servicio(offline=False, cache_size=25, carpeta="datos_cripta", url=URL_API, cliente_http=None)
```

- Con conexión: `ServicioCripta(ClientePersistente(ClienteCripta(url), AlmacenDisco(carpeta)), CacheLRU(n))`.
- Sin conexión: `ServicioCripta(ClienteOffline(AlmacenDisco(carpeta)), CacheLRU(n))`.
- `cache_size < 1` lanza `ValueError`. `cliente_http` solo sirve para pruebas (inyectar uno falso).

---

## 9. Presupuesto de solicitudes (§5.1)

Límite: **9 por cripta**.

| Forma de cargar | Solicitudes (cripta de 6 salas) |
|---|---|
| Sala por sala, sin persistencia | 14 (medido con la API real). **Se pasa del límite** |
| `precargar` en la primera partida | 6 (medido con la API falsa) |
| `precargar`, partidas siguientes | 3 (medido con la API falsa) |
| Modo offline | 0 |

Pendiente: confirmar con la API real la cuenta de `precargar` y que `datos["version"]` coincide con
`/criptas/{id}/version`.

---

## 10. Errores y qué hacer con cada uno

| Error | De dónde sale | Cuándo | Qué debe hacer quien lo captura |
|---|---|---|---|
| `ErrorSinConexion` | `cliente_http` | Sin internet, servidor caído o tiempo agotado | Mostrar el mensaje; sugerir `--offline` |
| `ErrorOffline` | `cliente_offline` | Modo offline sin datos guardados | Sugerir jugar una vez con conexión |
| `RuntimeError` | `cliente_http` | Código HTTP inesperado, o 429 repetido más de 5 veces | Mostrar el mensaje |
| `ValueError` | varios | Cripta o sala inexistente, id de archivo no válido, `cache_size < 1`, clase de objeto desconocida | Es un error de uso o de datos |
| `ErrorArchivo` | `Archivo_indexado` | Archivo dañado | `AlmacenDisco` lo trata como "no hay nada guardado" y lo vuelve a pedir |

---

## 11. Pruebas

Todas se corren **desde la raíz del proyecto**, como módulo y sin `.py`:

```
py -m tests_labs.prueba_archivo_indexado
```

| Prueba | Qué cubre | Esperado | ¿Usa internet? |
|---|---|---|---|
| `prueba_archivo_indexado` | Formato binario, daño, escritura atómica | 23 de 23 | No |
| `prueba_almacen_disco` | Versiones, criptas separadas, archivo dañado, ids peligrosos | 37 de 37 | No |
| `prueba_cliente_persistente` | 6/3/5/4 solicitudes, pedir solo lo que falta, orden | 23 de 23 | No |
| `prueba_cliente_offline` | Mismo juego sin red, criptas incompletas, errores claros | 13 de 13 | No |
| `prueba_fabrica` | `crear_servicio`, `precargar`, presupuesto, modo offline | 13 de 13 | No |
| `prueba_cliente_http_errores` | 429 con tope, sin conexión, otros códigos | 13 de 13 | No |
| `prueba_cache_uso` | LRU, protección "en uso", capacidad, contador | 13 de 13 | No |
| `api_falsa` | No es una prueba: la API falsa que usan las demás | | No |
| `prueba_cache`, `laboratorio*` | Laboratorios manuales para ver resultados | | Algunos |
| `prueba_servicio`, `prueba_cliente_http` | Contra la API real | | **Sí, gasta solicitudes** |

Lección que dejó la prueba con la API real: la API falsa la escribimos con la forma de datos que
*creíamos* correcta, y la real tenía diferencias (por ejemplo, `vida` ausente). Por eso conviene mantener
los dos tipos de prueba.

---

## 12. Particularidades de la API descubiertas

- `comportamiento` llega en minúscula y **con tilde**: `"guardián"`, `"errante"`, `"rastreador"`.
  `ComportamientoFactory` compara contra mayúsculas sin tilde: **hay que verificar** que normalice.
- `vida` de un enemigo en `/contenido` puede ser `null` o no venir.
- Las trampas no tienen `peso` ni `valor`.
- Los ids de sala empiezan en 1.
- Cada solicitud tiene el mismo costo, sea un 429 o un 200.

---

## 13. Pendientes y decisiones abiertas

| # | Qué | Quién |
|---|---|---|
| 1 | **Error en `EstadoJuegoLogica`:** reserva `[None] * total_salas` pero los ids van de 1 a N; la última sala no se puede entrar. Reservar `total + 1` y validar `0 < sala < len(salas)` | Cesar |
| 2 | `EstadoJuegoLogica` crea `ClienteCripta` directo con la URL fija. Debe usar `crear_servicio(...)` y llamar a `precargar(cripta)` al iniciar | Cesar |
| 3 | Condición de **victoria**: sala de `obtener_sala_salida` + llave `llave_salida` | Cesar |
| 4 | `main.py` usa el stub. Debe usar el motor real, con `--offline` y `--cache-size`, y mostrar el reporte de solicitudes | Fernanda |
| 5 | Capturar `ErrorSinConexion` / `ErrorOffline` y mostrar el mensaje | Fernanda / Cesar |
| 6 | **`marcar_en_uso` / `marcar_libre`**: acordar qué significa "en uso" (propuesta: una ficha está en uso mientras haya una sala cargada que la necesita) y conectarlo al motor | Cesar + Persona 3 |
| 7 | `SalaDTO.objetos` está tipado `list[str]` pero ahora contiene objetos `Objeto`; la vista debe imprimir el nombre | Cesar / Fernanda |
| 8 | `obtenerJugador()` falla con `AttributeError` si se llama antes de `iniciarJuego` | Cesar |
| 9 | **Guardado binario de la partida** (§4.10), sin `dict`: jugador, inventario, salas visitadas, cola de eventos, pila de retroceso | Persona 3 |
| 10 | Confirmar con la API real: `datos["version"]` = endpoint de versión; solicitudes de `precargar` | Persona 3 |
| 11 | Verificar la normalización de `comportamiento` (sección 12) | Quien lleve enemigos |

Confirmado con el enunciado: el modo offline se activa con `--offline` (§3.4) y "en uso" (§4.4) significa
una ficha referenciada por un enemigo vivo, un objeto del inventario o del suelo de la sala actual, o una
trampa de la sala actual. Sigue abierto: el formato del "paquete de respuestas previamente descargadas" que
publicará el curso para `--offline` (nuestro `ClienteOffline` lee el formato propio de `AlmacenDisco`).

## 14. Precarga perezosa, sesión compartida y mediciones

### 14.1 Qué se agregó a `ServicioCripta`

| Método | Devuelve | Para qué |
|---|---|---|
| `salas_vecinas(cripta_id, sala, profundidad=1)` | `list[int]` | Ids alcanzables por las salidas (de la más cercana a la más lejana). No usa la red |
| `precargar_vecinas(cripta_id, sala_actual, profundidad=None, max_salas=10)` | `int` (salas traídas) | Precarga **perezosa** por vecindad (ver 14.2) |
| `reporte(cripta_id)` | `ReporteSolicitudes` | Solicitudes, presupuesto, aciertos y fallos de caché; `.texto()` para imprimir al final (§5.1) |
| `version_cripta(cripta_id)` / `version_catalogo()` | `str` | Para el encabezado del log y la tabla de puntajes. No cuestan solicitudes extra |
| `retener_fichas(ids)` / `liberar_fichas(ids)` | `None` | Marcan fichas "en uso" (§4.4): una llamada por cada instancia activa que las referencia |

### 14.2 Cómo funciona `precargar_vecinas` y por qué

- **Garantía (§4.2):** al terminar, la sala actual y todas las que se alcanzan en UN movimiento ya están traídas.
- **Perezosa:** si esa garantía ya se cumple devuelve 0 y no hace nada. Solo cuando falta una sala trae un lote.
- **El lote se llena:** con las salas faltantes más cercanas, hasta `max_salas` (10 = lo que cabe en una solicitud de
  contenido). Como una solicitud cuesta lo mismo con 1 que con 10 salas, una tanda cubre varios pasos del jugador.
- **Nunca la cripta completa:** el tope de 10 salas por tanda lo impide en criptas grandes. `precargar(cripta_id)` sin
  lista sí trae todo y queda solo para pruebas.
- **Llamada recomendada:** `servicio.precargar_vecinas(cripta_id, sala)` sin más argumentos, cada vez que el jugador
  entra a una sala. Pasar `profundidad` pequeña (2 o 3) reduce lo que se trae por tanda y gasta más solicitudes.

### 14.3 Sesión compartida (una solicitud menos por cada servicio extra)

`crear_servicio` reutiliza durante toda la ejecución el mismo cliente de red (un UUID, §3.1) y el mismo
`ClientePersistente`. La lista de criptas, los datos generales y la versión del catálogo se piden una vez por
ejecución aunque se creen varios servicios (por ejemplo, uno para listar criptas y otro al iniciar la partida).

### 14.4 Mediciones (`py -m adaptadores.bench_red`)

Datos sintéticos y sin internet; la solicitud real se supone de ~400 ms (§3.4).

**Solicitudes para recorrer un pasillo de 60 salas**

| Estrategia | Solicitudes |
|---|---|
| Sala por sala, sin precarga | 63 |
| Actual y vecinas en cada paso (profundidad 2) | 61 |
| Perezosa, profundidad 2 | 33 |
| **Perezosa, por defecto (lote de 10)** | **9** |

**Búsqueda en la caché** (µs por operación, peor caso de la búsqueda lineal)

| Fichas | `deque` lineal (acierto) | Tabla hash propia (descartada) |
|---|---|---|
| 25 (valor por defecto) | 1.3 | 0.3 |
| 1000 | 35 | 0.3 |
| 5000 | 195 | 0.4 |

Con el tamaño por defecto la diferencia es irrelevante frente a los 20 ms de §5.2. La búsqueda lineal deja de ser
apropiada hacia varios miles de fichas (cientos de µs por consulta); entonces conviene una tabla hash propia con listas.

**Recuperar una ficha liberada desde disco:** 0.03 ms con 25 fichas, 0.09 ms con 200 y 0.37 ms con 1000, contra
~400 ms de una solicitud de red. **Guardar 10 fichas** (reescribe el archivo completo): 1.7 a 2.9 ms.
**Planear la vecindad** en una cripta de 1000 salas: 25 µs (1 paso) a 59 µs (2 pasos); si no falta nada, 38 µs.
