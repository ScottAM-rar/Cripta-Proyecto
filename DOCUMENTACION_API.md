# Capa de comunicación con la API: documentación

Autor de esta capa: Persona 3 (Cliente de API, caché y persistencia).
Archivos que documenta: `adaptadores/cliente_http.py`, `adaptadores/resolucion.py`,
`adaptadores/cache.py` (hoy `Cache.py`), `ejemplo_uso_api.py` y `prueba_completa.py`.

---

## 1. La idea en una imagen

```
 API en internet
      │  JSON crudo (diccionarios y listas)
      ▼
 ClienteCripta  ── habla con la API. Devuelve datos CRUDOS.
      │
      ▼
 resolucion.py  ── traduce lo crudo a objetos del juego (DTO).
      │
      ▼
 CacheLRU       ── recuerda fichas del catálogo para no volver a pedirlas.
```

Cada pieza tiene **un solo trabajo**. Por eso el resto del equipo nunca toca
`requests` ni JSON: pide al cliente y recibe objetos.

---

## 2. Reglas de oro para el equipo

1. **Un solo `ClienteCripta` por partida.** Genera un `client_id` (uuid) que la API usa para
   identificarnos y lleva el contador `solicitudes_realizadas`. Si cada módulo crea el suyo,
   la API nos ve como jugadores distintos y el conteo queda partido.
2. **Nadie fuera de `adaptadores/` usa `requests` ni lee JSON.** Así el cliente online se puede
   cambiar por uno offline sin que nadie más se entere (patrón Adaptador).
3. **Para una sala completa se usa `resolver_sala(cliente, cache, cripta_id, numero_sala)`.**
4. **Cada solicitud HTTP real cuenta** para el límite del enunciado (§5.1).
5. **No se usan `dict` ni `set` como índice o caché** de datos del juego (restricción: solo Pila, Cola, Array, Lista simple y Lista doble).

---

## 3. Qué devuelve cada endpoint y qué método lo llama

| Método de `ClienteCripta` | Endpoint | Devuelve |
|---|---|---|
| `obtener_criptas()` | `GET /criptas` | `list[dict]` con `{id, nombre, salas, dificultad}` |
| `obtener_datos_generales(id)` | `GET /criptas/{id}` | `dict` con los datos de la cripta |
| `obtener_version_cripta(id)` | `GET /criptas/{id}/version` | `str` (la versión) |
| `obtener_salas(id)` | `GET /criptas/{id}/salas?pagina=N` | `list[dict]` con **todas** las salas |
| `obtener_contenido(id, [salas])` | `GET /criptas/{id}/contenido?salas=1,2,..` | `list[dict]`: qué hay en cada sala |
| `obtener_catalogo([ids])` | `GET /catalogo?ids=a,b,..` | `list[dict]`: fichas completas |
| `obtener_version_catalogo()` | `GET /catalogo/version` | `str` |

Todas las llamadas llevan el header `X-Cripta-Client-Id`.

### Lo que el cliente hace solo
- **Lotes de 10.** La API acepta máximo 10 salas o 10 ids por llamada. Con 25 salas el cliente
  hace 3 solicitudes (10 + 10 + 5). Se hace con `range(0, len(lista), 10)` y rebanadas.
- **Paginación.** `obtener_salas` repite la petición hasta llegar a `total_paginas`.
- **Error 429.** Duerme `reintentar_en` segundos y reintenta; el reintento **también cuenta**
  como solicitud.
- **Otros errores** (400, 404, 500) lanzan `RuntimeError` con la URL y el código.

---

## 4. Las dos fuentes de un enemigo (lo más importante de entender)

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

Analogía: `/contenido` es la lista de quién está en cada sala; `/catalogo` es el expediente
de cada tipo.

**Regla de la vida:** si la colocación trae un número, ese es el daño ya sufrido y se respeta
(por ejemplo al cargar una partida). Si trae `null` **o no trae la clave**, el enemigo está sano
y `vida_actual = ficha.vida_max`.

----------------------------------------------------------------------------------------------------------------------------------

## 5. `resolucion.py` función por función

### `resolver_objeto(ficha) -> Objeto`
Convierte la ficha cruda de un objeto en la subclase correcta (`Arma`, `Armadura`, `Pocion`,
`Antidoto`, `Llave`, `Antorcha`, `PergaminoRetroceso`) según el campo `clase`.
- Renombra `id` → `id_catalogo`, porque así se llama en el DTO.
- Quita `clase`, porque el DTO no tiene ese campo (la clase de Python ya es esa información).
- Trabaja sobre una **copia** (`dict(ficha)`) para no modificar la ficha original, que puede
  estar guardada en la caché.
- Usa `Clase(**datos)`: los `**` convierten el diccionario en argumentos con nombre. Si la API
  manda un campo que el DTO no tiene (o falta uno), Python falla de inmediato, y eso es
  deseable: avisa pronto de que algo no cuadra.
- Si `clase` no es un objeto (por ejemplo `trampa` o `enemigo`) lanza `ValueError`.

### `resolver_ficha_enemigo(ficha) -> EnemigoCatalogoDTO`
Igual idea: la "plantilla" de un tipo de enemigo, sin ser todavía un enemigo concreto.

### `resolver_enemigo(colocacion, ficha, id_sala) -> EnemigoDTO`
El cruce de las dos fuentes (sección 4). Detalles:
- `colocacion.get("vida")` en vez de `colocacion["vida"]`: la API real a veces **no incluye**
  la clave. Se descubrió con la prueba live (`KeyError('vida')`).
- `suelta=list(ficha.suelta)` hace una **copia**. Sin ella, todas las ratas compartirían la misma
  lista en memoria y quitarle un drop a una se lo quitaría a todas (error clásico con listas
  mutables).

### `resolver_trampa(colocacion, ficha) -> Trampa`
`instancia` sale de la colocación; `daño` y `rearme` salen de la ficha.

### `resolver_sala(cliente, cache, cripta_id, numero_sala) -> (enemigos, objetos, trampas)`
Coordina todo lo anterior:

1. Pide el contenido de la sala (siempre a la API; el contenido cambia).
2. `_ids_necesarios`: junta los ids de catálogo que hacen falta, **sin repetidos**.
3. `_obtener_fichas`: para cada id mira primero la caché; **solo los que faltan** se piden a la
   API, **en una sola tanda**, y se guardan en la caché.
4. Resuelve cada enemigo, objeto y trampa con su ficha (`_buscar_ficha`).

Por qué está hecha así:
- **Sin repetidos:** dos ratas necesitan una sola ficha, así que se pide una vez.
- **Una sola tanda:** minimiza solicitudes; `obtener_catalogo` ya parte en lotes de 10 si hace falta.
- **Recibe `cliente` y `cache` como parámetros:** así funciona con cualquier cliente que cumpla
  `ClienteInterfaz` (online u offline) y es fácil de probar con un cliente falso.
- **Listas con `in` en vez de `set`:** un `set` es una tabla hash, no permitida en el proyecto.
  La búsqueda lineal es suficiente para el tamaño de una sala.
- **Sala sin contenido:** lanza `ValueError` claro. Sala vacía: devuelve `([], [], [])` sin
  pedir nada al catálogo.

---

## 6. La caché (`CacheLRU`)

Guarda fichas por id. Capacidad por defecto: **25** (`--cache-size`, §4.4).

- **Estructura:** un `deque` de entradas `[clave, valor, contador_en_uso]`. Sin `dict`.
- **LRU (menos recientemente usada):** lo más reciente va al frente (`appendleft`); cuando está
  llena se desaloja de atrás hacia adelante. Es la política que justificamos: lo usado hace
  mucho tiene menos probabilidad de volver a necesitarse.
- **`obtener(clave)`:** busca, mueve la entrada al frente y devuelve el valor (o `None`).
- **`insertar(clave, valor)`:** si ya existe, actualiza y mueve al frente; si no, desaloja si
  está llena y agrega.
- **`marcar_en_uso(clave)` / `marcar_libre(clave)`:** un contador. Una ficha con contador > 0
  **no se puede desalojar** (§4.4: enemigo vivo en cualquier sala; objeto en inventario o suelo
  de la sala actual; trampa de la sala actual). Es un contador y no un booleano porque varias
  cosas pueden usar la misma ficha a la vez (dos ratas usan la ficha `ent_rata_gigante`).
- Costo de buscar: recorrido lineal, O(n) con n ≤ capacidad (25).

---

## 7. El archivo `ejemplo_uso_api.py`, paso por paso

Se ejecuta con `py ejemplo_uso_api.py` y habla con la API real.

| Paso | Qué hace | Por qué |
|---|---|---|
| 1 | Crea `ClienteCripta(BASE_URL)` y `CacheLRU(25)` | Una sola instancia por partida (regla de oro 1) |
| 2 | `obtener_criptas()` y elige la primera | En el juego real elige el jugador |
| 3 | `obtener_version_cripta` y `obtener_version_catalogo` | Las versiones validan los datos guardados en disco (§4.4) |
| 4 | `obtener_salas(cripta_id)` | Es el esqueleto del mapa; el cliente ya une las páginas |
| 5 | Busca una sala con enemigos y muestra el contenido **crudo** | Para que se vea que solo dice qué hay y dónde, sin stats |
| 6 | `resolver_sala(...)` y muestra los DTO | Lo mismo, listo para jugar; también muestra cuántas solicitudes costó |
| 7 | Repite `resolver_sala` en la misma sala | Demuestra la caché: solo se vuelve a pedir el contenido |
| 8 | `marcar_en_uso` y `marcar_libre` | Muestra la mecánica que el motor debe usar |
| 9 | Imprime `solicitudes_realizadas` | Es el número que importa para §5.1 |

Detalles de diseño del ejemplo:
- `numero_de_sala(sala)` acepta `"id"` o `"sala"` como clave, para no depender de un detalle
  del formato.
- El paso 5 recorre salas **una por una** hasta encontrar enemigos, lo que gasta solicitudes.
  Es solo para la demostración; el juego real no debería explorar así.
- `main(cliente=None)` acepta un cliente para poder probar la lógica con uno falso.

---

## 8. Pruebas: `prueba_completa.py`

- `py prueba_completa.py`: **31 pruebas offline**, sin internet y sin gastar solicitudes.
- `py prueba_completa.py --live`: además corre una prueba contra la API real que recorre todas
  las salas de la primera cripta.
- Agregar `-v` muestra el detalle del error si algo falla.

Qué cubren:
- **Resolvedores:** las 7 clases de objeto, campos específicos, que no modifiquen la ficha,
  clase desconocida, vida `None` / con valor / sin clave, `suelta` como copia, trampa.
- **Caché:** insertar y obtener, actualizar, desalojo LRU, no exceder la capacidad, protección
  "en uso", `marcar_libre`, contador acumulado, claves inexistentes.
- **`resolver_sala`:** contenido correcto, una sola tanda sin repetidos, caché en la segunda
  llamada, pedir solo lo que falta, sala vacía, sala inexistente, caché de capacidad 1.
- **`ClienteCripta` real con `requests.get` y `time.sleep` simulados:** URL y header, lotes de
  10 (25 salas = 3 solicitudes), paginación, reintento en 429, errores, versiones.

Lección que dejó la prueba live: el cliente falso lo escribimos nosotros con la forma de datos
que *creíamos* correcta. La API real tenía una diferencia (`vida` ausente) que solo apareció
contra los datos reales. Por eso conviene mantener las dos clases de prueba.

---

## 9. Particularidades de la API descubiertas

- `comportamiento` llega en minúscula y **con tilde**: `"guardián"`, `"errante"`, `"rastreador"`.
  El `ComportamientoFactory` del equipo compara contra `"GUARDIAN"`, `"ERRANTE"`,
  `"RASTREADOR"` en mayúscula y sin tilde, así que **no coincidirá**. Hay que normalizar en un
  solo lugar.
- `vida` de un enemigo en `/contenido` puede ser `null` o no venir.
- Las trampas no tienen `peso` ni `valor`.

---

## 10. Decisiones y trabajo pendiente

2. **`SalaDTO` vs `resolver_sala`:** el `SalaDTO` guarda `objetos` como lista de ids y `trampas`
   como `TrampaDTO` (solo `id_instancia` y `tipo`); `resolver_sala` devuelve objetos y trampas
   ya resueltos. Hay que acordar con Persona 1/2 cuál usar.
3. **Conectar `marcar_en_uso` / `marcar_libre` al motor** con los alcances de §4.4.
4. **Persistencia:** caché que sobreviva al cierre del programa, fichas liberadas legibles desde
   disco, validación con versiones de cripta y catálogo, guardado binario indexado (§4.10).
5. **Precarga por lotes** (§4.2) y **`cliente_offline.py`** (implementar `ClienteInterfaz`).
6. **`_CLASES_OBJETO` es un `dict`** (tabla fija de 7 entradas, no un índice de datos). Consultar
   al profesor si está permitido; si no, sustituirlo por una cadena de `if`.
7. Avisar del problema de `ComportamientoFactory` (sección 9).
