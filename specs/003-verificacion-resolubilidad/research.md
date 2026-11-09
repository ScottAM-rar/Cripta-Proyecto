# Investigación (Fase 0): Verificación de resolubilidad

**Capacidad**: `003-verificacion-resolubilidad` | **Fecha**: 2026-11-08 | **Especificación**: [spec.md](spec.md)

Cada sección sigue el formato **Decisión / Motivo / Alternativas descartadas**. S = salas del esqueleto (cota de ids), E = salidas, L = ubicaciones de llaves (filas de la consulta de llaves), K = ids de llave distintos (los de las ubicaciones, los de las puertas y la llave de salida), O = oleadas del recorrido (≤ K + 1).

## 0. Lo que ya existe y se reutiliza

| Pieza | Dónde | Uso en esta capacidad |
|---|---|---|
| Esqueleto normalizado | `adaptadores/servicioCripta.py` (`normalizar_esqueleto`, `esqueleto()`) | `normalizar_esqueleto` copia cada salida con `dict(salida)`, así que el campo `llave` de la API **ya llega** hasta `esqueleto()`; ahí se pierde, porque `AristaMapaDTO` no tiene dónde guardarlo (§1) |
| Mapa del modelo | `Logica/MapaCripta.py` (`MapaCripta`, `AristaCripta`) | Salientes por sala en listas contiguas, `existe[id]`, orden N, S, E, O. La verificación lo recorre sin copiarlo |
| Ubicación de llaves | `DTO/LlavesDTO.py` (`UbicacionLlavesDTO`), `ServicioCripta.ubicacion_llaves` (009) | Listas paralelas `ids`, `salas`, `enemigos`; si hay enemigo, `salas[i]` ya es su sala inicial (FR-302 de la 009), así que B-R2 no necesita contenido de salas |
| Llaves de la partida | `EstadoJuegoLogica.obtenerLlaves()` y `self.llaves` (009) | `iniciarJuego` ya las pide; la verificación del inicio las reutiliza sin otra consulta (FR-341) |
| Cola propia | `Logica/ColaCircular.py` | Frontera del recorrido incremental (§2) |
| Montículo propio | `Logica/MonticuloMinimo.py` (clave `(int, int)`) | Llaves pendientes de cada oleada, por `(id de sala, número de llave)` (§3) |
| Ordenamiento propio | `Logica/ordenamiento.py` (`ordenar_adaptativo`, estable) | Construir el índice de ids de llave (§4) |
| Recorrido por niveles | `Logica/RecorridoPorNiveles.py` (005) | Solo en el camino «no resoluble», para saber si una sala tiene camino aunque se tuvieran todas las llaves (§6) |
| Lectura solo local | `adaptadores/fuente_solo_local.py` (009) | Envuelve un `ServicioCripta` sobre `ClienteOffline`; su `esqueleto()` delega, así que hereda el campo `llave` sin código propio (§1) |
| API falsa v2 y casos B-R | `tests_labs/api_falsa.py` (`_puerta_con_llave`, `_b_r1` a `_b_r4`, `CASOS_APENDICE_B`) | `_puerta_con_llave` ya escribe `"llave"` en las dos salidas de la puerta. Los cuatro casos existen; esta capacidad ejecuta sus pasos `verificar` e `iniciar_sin_forzar` |
| Criptas sintéticas | `tests_labs/cripta_sintetica.py` | Base del bench; se agrega un generador de llaves encadenadas (§9) |

## 1. Hallazgo previo: la llave de cada puerta no llega al mapa

**Problema**: la API publica la llave de una puerta en la propia salida (`"E": {"sala": 5, "cerrada": true, "llave": "itm_llave_bronce"}`, ver `api_completa.txt`). `ServicioCripta.esqueleto()` arma `AristaMapaDTO(direccion, destino, costo, cerrada_inicial)` y descarta `llave`; `MapaCripta` copia a `AristaCripta` los mismos cuatro campos. Sin ese dato la verificación no puede saber qué llave abre cada puerta (FR-333). El contenido de salas no sirve: no trae las puertas, y pedirlo violaría FR-341.

**Decisión**: agregar `llave: str | None = None` al final de `AristaMapaDTO` (dataclass) y de `AristaCripta` (parámetro con valor por defecto y una entrada más en `__slots__`). `esqueleto()` lo llena con `datos.get("llave")`; `MapaCripta.__init__` lo copia. Es la **primera tarea** de la capacidad, con sus pruebas (contrato en [contracts/mapa-con-llaves.md](contracts/mapa-con-llaves.md)).

- `FuenteSoloLocal.esqueleto()` delega en el `ServicioCripta` que envuelve, y `ClienteOffline`/`AlmacenDisco` guardan las salas tal como vinieron de la API: la llave aparece también en `--offline` y en la lectura solo local sin tocar esos adaptadores. Se comprueba con una prueba, no se supone.
- La API falsa v2 ya la emite (`_puerta_con_llave`). `esqueleto_rejilla(..., fraccion_cerradas>0)` cierra puertas **sin** llave: siguen siendo válidas (puerta que nunca se cruza, FR-333).
- No cambia el formato de la caché ni el de partida: la llave ya estaba guardada en el esqueleto crudo; solo se deja de descartar al convertir. `AlmacenPartidaBinario`, `EstadoGuardadoDTO` y `codec_partida` no se tocan (son de la 010).
- Quien construye hoy estos objetos (`servicioCripta.py:263`, `MapaCripta.py:38`) sigue funcionando sin pasar el campo.

**Motivo**: es el dato mínimo que falta y su lugar natural es la arista: es una propiedad de la salida, igual que `cerrada_inicial`. El valor por defecto mantiene compatibles a todos los que ya construyen aristas (pruebas de la 001 y la 005, el bench de terreno).

**Alternativas descartadas**:
- *Una lista aparte de puertas con llave (origen, dirección, llave) que entrega el servicio*: duplica la fuente de verdad del mapa y obliga a cruzarla con las aristas (O(E log E) o un índice por arista).
- *Leer la llave del `SalaDTO` (`SalidaDTO.llave` ya existe)*: exige el contenido de cada sala, es decir, solicitudes (viola FR-341) y depende de qué está descargado (viola el principio II).

## 2. Algoritmo: un solo recorrido incremental por oleadas

**Decisión**: un único recorrido en anchura desde la sala inicial, con `ColaCircular` como frontera y una lista de booleanos `alcanzable[id]`. Al sacar una sala se examinan sus salidas en el orden del mapa:

1. destino inexistente → se ignora (como en la 005);
2. destino ya alcanzable → nada;
3. salida no cerrada → el destino pasa a alcanzable y entra a la cola;
4. cerrada sin llave asignada → nunca se cruza (FR-333); queda anotada como candidata a bloqueo;
5. cerrada con llave ya obtenida → se cruza;
6. cerrada con llave aún no obtenida → la arista se agrega a `esperando[número de llave]`.

Cuando una sala se vuelve alcanzable, cada ubicación de llave que está en esa sala (suelo o enemigo que inicia ahí, FR-334) entra al montículo de pendientes como `(id de sala, número de llave)`, salvo que la llave ya esté obtenida; además `obtenible[número] = True`.

Cuando la cola se vacía termina una **oleada**:

- si la sala de salida es alcanzable y `obtenible[llave de salida]` es verdadero, se vacían los pendientes de la oleada al orden y la cripta es **resoluble** (FR-332);
- si no hay pendientes, la cripta **no es resoluble** (punto fijo);
- si no, se sacan **todos** los pendientes de la oleada en orden del montículo; cada llave que no estaba obtenida se marca obtenida, se agrega al orden (con la sala y, si corresponde, el enemigo) y se liberan sus aristas de `esperando`: cada destino aún no alcanzable pasa a alcanzable y entra a la cola. Empieza la oleada siguiente.

**Costo**: cada sala entra a la cola una vez, cada salida se examina una vez desde su origen y se libera como máximo una vez desde `esperando`, cada ubicación entra al montículo como máximo una vez. Total **O(S + E + L log L)** más el índice (§4): O(K log K + E log K). Con L del orden de K, es el O((S + E + K) log K) esperado. Memoria O(S + E + L).

**Motivo**:
- Las llaves no se gastan y las puertas no cambian durante la verificación (supuestos de la spec), así que «alcanzable» y «obtenible» solo crecen: el conjunto final no depende del orden en que se exploren las salas, y un solo recorrido basta.
- La **oleada** es la forma precisa de «se vuelven obtenibles en el mismo momento» (FR-335): todas las llaves que aparecen antes de que haga falta abrir otra puerta. Dentro de la oleada el montículo da el orden por sala y por id; entre oleadas manda el momento.
- La salida del algoritmo (orden, salas alcanzables, bloqueos) no depende del orden de la cola ni del orden de la respuesta de llaves: el orden sale del montículo, las salas alcanzables de recorrer `alcanzable` por id creciente y los bloqueos de recorrer las salas alcanzables por id y sus salidas en N, S, E, O (§6). Eso cumple el principio II sin ordenar listas de salida.

**Alternativas descartadas** (costo en el peor caso: una cadena de K puertas, cada llave detrás de la anterior):

| Alternativa | Costo | Por qué no |
|---|---|---|
| **Repetir el recorrido completo** desde la sala inicial cada vez que se obtiene una llave (o cada oleada) | O(K · (S + E)) | Cuadrático en criptas encadenadas. Es la alternativa que **mide el bench** (§9): da el mismo resultado, así que también sirve de oráculo en las pruebas de equivalencia (`tests_labs/referencia_resolubilidad.py`, `verificar_repetida`). El oráculo **para igual** que el algoritmo: al final de la oleada en que la sala de salida es alcanzable y la llave de salida es obtenible (e incluye las llaves de esa oleada), o cuando una oleada no agrega ninguna llave nueva |
| Punto fijo sobre la lista de puertas: repasar todas las puertas cerradas hasta que ninguna se abra | O(K · E) | Igual de cuadrático y sin orden natural por oleadas |
| Una llave por vez del montículo (sacar solo el mínimo y volver al recorrido) | Mismo costo | Es determinista, pero una llave descubierta después puede adelantarse a una que estaba pendiente desde antes; contradice «primero lo que es obtenible antes» y hace el reporte menos explicable. Las oleadas dan el mismo resultado en B-R3 y en la cadena |
| Búsqueda exhaustiva de órdenes (permutaciones, retroceso) | O(K!) | Innecesaria: con llaves que no se gastan, la alcanzabilidad es monótona |

## 3. Pendientes de cada oleada: `MonticuloMinimo`

**Decisión**: reutilizar `MonticuloMinimo` con la clave `(id de sala, número de llave)`. Como los números de llave salen de un índice ordenado por id (§4), comparar números es comparar ids: el montículo entrega exactamente el desempate de FR-335 (menor sala; dentro de la sala, menor id de llave). Una misma llave puede entrar varias veces (varias ubicaciones alcanzables en la oleada); al sacar una entrada de una llave ya obtenida en esa misma oleada, se descarta. La primera que sale es la de menor sala, que es la que se informa (FR-336).

Si una llave tiene en esa sala ubicaciones en el suelo y en enemigos, el reporte nombra **la del suelo**; entre enemigos, la de menor instancia. Así el reporte no depende del orden de la respuesta (FR-335). La búsqueda recorre solo las ubicaciones de esa llave (lista por número de llave, §4).

**Motivo**: es la estructura propia que ya existe con la forma de clave exacta, y cada oleada necesita sacar sus pendientes en orden: O(P log P) para P pendientes, sin ordenar la oleada aparte.

**Alternativas descartadas**:
- *Juntar los pendientes en una lista y ordenarla con `ordenar_adaptativo` al terminar la oleada*: mismo O(P log P) y también válida; se prefiere el montículo porque las entradas llegan de a una durante el recorrido y porque así el orden de la oleada no depende de un ordenamiento estable sobre un orden de llegada.
- *`heapq`*: prohibido (principio I).

## 4. Índice de ids de llave a número

**Decisión**: `IndiceLlaves` en Logica. Junta los ids de las ubicaciones, de las aristas con llave y la llave de salida en una lista; la ordena con `ordenar_adaptativo` (estable, comparación de cadenas); elimina repetidos comparando vecinos. `numero(id)` es una **búsqueda binaria escrita a mano** sobre esa lista: devuelve la posición o −1. Con el índice se arman tres listas indexadas por número: `obtenida`, `obtenible` y `ubicaciones_por_llave` (posiciones en `UbicacionLlavesDTO`), más `esperando` (aristas por número de llave). Y una lista por id de sala, `ubicaciones_por_sala`.

Una llave que aparece en una puerta o como llave de salida pero no en ninguna ubicación tiene número igual, con `ubicaciones_por_llave` vacía: así el reporte la puede nombrar como «no existe en la cripta» (FR-338).

**Costo**: construir O(K log K); cada consulta O(log K); se consulta una vez por ubicación y una vez por arista con llave: O((L + E) log K).

**Motivo**: sin `dict` ni `set` (principio I), y con ids de texto no densos, la búsqueda binaria sobre un arreglo ordenado es la opción propia más simple con costo logarítmico. Ordenar el índice además fija el orden de los números, que es el que usa el montículo (§3).

**Alternativas descartadas**:
- *`dict` id → número*: prohibido (principio I).
- *Búsqueda lineal del id en la lista de llaves*: O(K) por consulta, O((L + E) · K) en total: cuadrático en criptas de muchas llaves. Se mide en la sección B del bench como alternativa descartada del índice.
- *Tabla hash propia*: costo esperado O(1), pero más código y con un orden que no sirve para el desempate; habría que ordenar aparte igual.
- *`bisect`* o *`sorted()`/`.sort()`*: prohibidos por la entrada de esta capacidad.

## 5. Dónde vive cada parte

**Decisión**:

| Parte | Lugar | Por qué |
|---|---|---|
| Resultado (`ResultadoVerificacion`, `PasoLlaveDTO`, `BloqueoDTO`) | `DTO/ResultadoVerificacionDTO.py` (NUEVO) | Lo comparten Logica, Servicio y el controlador de Fernanda; los DTO no importan nada de las capas |
| Algoritmo puro `verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves)` | `Logica/VerificacionResolubilidad.py` (NUEVO) | Lógica pura: recibe `MapaCripta` y `UbicacionLlavesDTO`, no importa adaptadores (principio IV) |
| Índice de llaves | `Logica/IndiceLlaves.py` (NUEVO) | Estructura propia reutilizable y probable por separado |
| Operación `verificar(fuente, cripta_id, llaves=None)` | `Logica/VerificacionResolubilidad.py` | Junta los datos desde `FuenteCripta` (solo el contrato del modelo) y llama al algoritmo; traduce los fallos de datos a `motivo_error` (FR-343) |
| Operación pública `verificar(cripta_id)` | `Servicio/EstadoJuegoServicio.py` (MODIFICADO) | Es la que usa el controlador (`--verificar`) y la que recibe Fernanda; delega en la de Logica con la fuente que el servicio ya tiene |
| Texto del reporte | `Logica/ReporteVerificacion.py` (NUEVO): `lineas_reporte(resultado) -> list[str]` y `aviso_forzado(resultado) -> str` | Un solo lugar para el texto (decisión 5 de la entrada). Es una función pura sin E/S: no es la vista, así que `--verificar` no instancia la vista (principio IV) |
| Datos generales que faltan en el contrato | `FuenteCripta.obtener_sala_inicial` y `obtener_llave_salida` (MODIFICADO, junto a `obtener_sala_salida`); implementados en `ServicioCripta` y `FuenteSoloLocal` desde `datos_cripta` | La sala inicial hoy solo se obtiene dentro de `crear_jugador`, y la llave de salida no está en el contrato. Leerlas del `dict` en Logica rompería la separación |
| Inicio de partida | `EstadoJuegoLogica.iniciarJuego(..., forzar=False)` (MODIFICADO) | §7 |

**Motivo**: mismo reparto que la 009 (el servicio junta, Logica decide, el DTO viaja). `verificar(cripta_id)` existe en dos niveles solo para respetar las capas: el de Servicio no repite la regla, solo pasa la fuente (FR-344).

**Alternativas descartadas**:
- *El algoritmo en `adaptadores/`*: tendría acceso a todo, pero la lógica de juego no puede vivir en un adaptador y el inicio de partida (Logica) no podría usarlo sin importar adaptadores.
- *El texto del reporte en el controlador*: el aviso de `--forzar` lo arma el inicio de partida y el reporte lo usa `--verificar`; dos lugares para el mismo texto rompen FR-335 (mismo reporte) en cuanto cambie uno.
- *`ResultadoVerificacion` dentro de Logica*: obligaría a la vista y a `main.py` a importar Logica para leer un resultado; los demás resultados viajan como DTO.

## 6. Contenido del resultado y clasificación de bloqueos

**Decisión**: con la cripta no resoluble, el resultado lleva:

- `salas_alcanzables`: recorrer `alcanzable` por id creciente (O(S), sin ordenar).
- `salas_no_alcanzables`: cantidad de salas que existen y no son alcanzables.
- `bloqueos`: cada salida desde una sala alcanzable hacia una sala no alcanzable que no se pudo cruzar, en orden de sala de origen creciente y, dentro de la sala, N, S, E, O. Cada bloqueo trae la llave que pide y las salas donde está esa llave, y un **tipo**:

| Tipo | Cuándo |
|---|---|
| `SIN_LLAVE` | La puerta está cerrada y no tiene llave asignada |
| `LLAVE_INEXISTENTE` | Ninguna ubicación tiene esa llave |
| `CICLO` | La llave existe y alguna de sus ubicaciones está en una sala no alcanzable a la que sí se llegaría abriendo todas las puertas: está detrás de esta puerta o de otras puertas bloqueadas (FR-338) |
| `LLAVE_SIN_CAMINO` | La llave existe, pero ninguna de sus ubicaciones tiene camino desde la sala inicial ni ignorando todas las puertas |

- `causas`: lista ordenada fija de causas generales, para el encabezado del reporte: `LLAVE_SALIDA_INEXISTENTE` (la llave de salida no tiene ubicaciones), `SALIDA_SIN_CAMINO` (la sala de salida no tiene camino ni ignorando las puertas), `SALIDA_BLOQUEADA` (tiene camino, pero las puertas lo impiden), `LLAVE_SALIDA_INALCANZABLE` (se llega a la sala de salida, pero la llave de salida no es obtenible).

«Camino ignorando las puertas» se calcula **solo en el camino no resoluble**, con un `RecorridoPorNiveles` (005) desde la sala inicial sin criterio de transitabilidad: O(S log S + E), una vez.

Con la cripta resoluble: `orden` (lista de `PasoLlaveDTO(llave, sala, enemigo)`), que incluye la llave de salida, y `salas_alcanzables` hasta el momento de completarla.

**Motivo**: FR-337 y FR-338 piden salas alcanzables, puertas con su llave y dónde está, y distinguir ciclo de bloqueo. B-R1 queda como un `CICLO` (la llave de salida está en la sala 2, detrás de la única puerta, y la sala 2 tiene camino sin puertas). B-R4 queda como `LLAVE_INEXISTENTE` (`itm_llave_perdida`).

**Alternativas descartadas**:
- *Buscar el ciclo mínimo de dependencias entre llaves y puertas* (componentes fuertemente conexas sobre un grafo llave → puerta): explicaría ciclos largos con más detalle, pero es otro algoritmo con su propio costo y la spec solo pide señalar las llaves y puertas del ciclo o bloqueo y hasta dónde se llega. Se puede agregar después sin cambiar el contrato (el tipo `CICLO` ya existe).
- *Informar solo la primera puerta bloqueada*: incumple «varios bloqueos independientes: el reporte los muestra todos» (casos límite de la spec).

## 7. Inicio de partida con verificación y `--forzar`

**Decisión**:

- Firma: `EstadoJuegoLogica.iniciarJuego(cripta, semilla=None, pedir_llaves=True, forzar=False)` y `EstadoJuegoServicio.iniciarJuego(cripta, semilla=None, offline=None, nombre_log=None, forzar=False)`. Los dos con valor por defecto: quien no pasa `forzar` sigue funcionando.
- Dentro de `iniciarJuego`, justo después de `self.obtenerLlaves()` y **antes** de `self.iniciado = True`:
  - `self.resultadoVerificacion` y `self.avisoResolubilidad` vuelven a `None`;
  - si `self.llaves` es `None` (FR-313): no se verifica, la partida sigue con `avisoLlaves` (FR-339);
  - si hay llaves pero la verificación da error de datos (`resoluble is None`, por ejemplo la sala de salida no existe en el mapa; escenario H4-5): la partida inicia con `avisoResolubilidad` = el `motivo_error` seguido de «La verificación de resolubilidad no está disponible.»; `--verificar` sobre la misma cripta da código 2 (FR-339, FR-343);
  - si no, `resultado = verificar(self.comunicacion, cripta, llaves=self.llaves)`; se guarda en `self.resultadoVerificacion`;
  - si `resultado.resoluble is False` y no `forzar`: se lanza `CriptaNoResoluble(resultado)` (en `Logica/VerificacionResolubilidad.py`, hereda de `RuntimeError`, `str()` es el reporte completo) y `iniciado` queda en `False`;
  - si `resultado.resoluble is False` y `forzar`: `self.avisoResolubilidad = aviso_forzado(resultado)` y la partida sigue.
- `EstadoJuegoServicio.iniciarJuego` deja pasar `CriptaNoResoluble`: como el log se abre **después** (`_abrirLog`), no se crea el archivo ni se escribe nada en el registro de partida (B-R4). `EstadoJuegoServicio.avisoResolubilidad()` lo expone igual que `avisoLlaves()`, para que el controlador lo muestre **solo al iniciar** (clarificación Q3).
- `pedir_llaves=False` (reproducción, `--replay`, `--hasta`) implica no verificar. La partida cargada no pasa por `iniciarJuego`; `EstadoGuardadoLogica.restaurar` vuelve a poner `resultadoVerificacion` y `avisoResolubilidad` en `None` (una línea, como hizo la 009 con las llaves; no toca el formato de guardado).
- La verificación del inicio usa la misma función `verificar` que `--verificar` (FR-344) y las llaves que `iniciarJuego` ya pidió: 0 solicitudes nuevas. El esqueleto sale de `obtener_mapa`, memorizado por `ServicioCripta`.

**Motivo**: lanzar una excepción del contrato del modelo es lo que ya hace `iniciarJuego` con «No existe la cripta solicitada», y `main.py` ya captura `RuntimeError` para salir con un mensaje. Lanzar antes de `iniciado = True` y antes de `_abrirLog` garantiza que no queda partida ni log a medias; un segundo intento sobre el mismo objeto funciona porque `iniciado` sigue en `False`.

**Alternativas descartadas**:
- *Devolver el resultado y que el controlador decida*: el controlador ya habría abierto el log (`EstadoJuegoServicio.iniciarJuego` lo abre al final) y la regla «no resoluble no inicia» quedaría fuera del modelo, en el código de Fernanda.
- *Verificar antes de construir el estado*: obligaría a pedir las llaves fuera de `obtenerLlaves()`, que es el único punto de la 009 por el que se piden.
- *Guardar `forzar` en el estado guardado*: no hace falta (la partida cargada no verifica) y tocaría el formato de la 010.

## 8. Códigos de salida y errores de datos

**Decisión**: `ResultadoVerificacion.codigo_salida()` devuelve **0** si es resoluble, **1** si no lo es y **2** si hubo error de datos (FR-331). `verificar(fuente, cripta_id)` captura solo errores esperables del contrato y los traduce a `motivo_error` con `resoluble = None`:

| Situación | Cómo llega a Logica | `motivo_error` |
|---|---|---|
| Cripta inexistente | `existe_cripta()` falso | «La cripta X no existe» |
| Llaves no disponibles (servicio, presupuesto, inválidas, `--offline` sin llaves) | `LlavesNoDisponibles` (009) | El mensaje de la 009, que ya nombra la cripta |
| Dato faltante por la lectura solo local | `DatoLocalFaltante` (009) | Su mensaje |
| Fallo de red o de disco al pedir esqueleto o datos generales | Subclases de `RuntimeError`/`OSError` de los adaptadores (`ErrorSinConexion`, `ErrorOffline`) | «No se pudieron obtener los datos de la cripta X: <motivo>» |
| Sala inicial o de salida que no existe en el esqueleto | Comprobación en el algoritmo | «Datos inválidos en la cripta X: …» |

Se capturan por las clases base (`RuntimeError`, `OSError`), así Logica no importa adaptadores. Los `ValueError` de programación no se tragan, salvo el de «cripta inexistente», que se comprueba antes con `existe_cripta`.

**Motivo**: FR-343 prohíbe inventar un resultado; separar el código 2 del 1 permite a un guion distinguir «no resoluble» de «no se pudo saber».

**Alternativas descartadas**: *lanzar en vez de devolver*: Fernanda tendría que capturar varias excepciones distintas para armar el mismo reporte; con el resultado, `main.py` hace `imprimir(lineas_reporte(r)); return r.codigo_salida()`.

## 9. Medición: bloque `resolubilidad` de `--bench`

**Decisión**: `bench/resolubilidad.py`, registrado como `resolubilidad` en `bench/__init__.py`. Usa `esqueleto_llaves_encadenadas(n, semilla)` (NUEVO en `tests_labs/cripta_sintetica.py`): un pasillo principal de n salas en el que la puerta i → i+1 se abre con la llave `k_i`, ubicada en una sala lateral colgada de la sala i (el orden de las salas laterales y los ids de llave se barajan con la semilla, para que el orden de ids no coincida con el de la cadena); la llave de salida está en la última sala lateral. K ≈ n, S ≈ 2n, E ≈ 4n. Es el peor caso de la alternativa repetida: K oleadas, cada una agrega pocas salas.

Secciones (contrato en [contracts/bench-resolubilidad.md](contracts/bench-resolubilidad.md)):

| Sección | Qué mide | Alternativa descartada | Falla si |
|---|---|---|---|
| A. Estrategias | ms de la verificación incremental y de la repetida, a dos tamaños: n = 300 y n = 3 000 (factor 10). Mediana de 5 repeticiones (la repetida en el tamaño grande, 1 repetición si supera 10 s, y se informa) | Recorrido repetido por oleada (§2) | Los resultados de las dos estrategias difieren (equivalencia, principio III) |
| B. Índice de llaves | µs de construir el índice y resolver todas las consultas con búsqueda binaria frente a búsqueda lineal, K = 100, 1 000, 10 000 | Búsqueda lineal (§4) | Informativa |
| C. Límite de 200 ms | ms de la verificación incremental sobre una cripta sintética de llaves encadenadas con n = 5 000 (mucho mayor que cualquier cripta publicada hoy), más una rejilla de 70 × 70 con puertas y llaves al azar | — | La incremental supera 200 ms (FR-345) |
| D. Crecimiento | Razón de tiempos (n = 3 000) / (n = 300) de la incremental | La misma razón para la repetida: medida 1 112,8, no cerca de 100 como se preveía, porque el oráculo, además de recorrer desde cero en cada oleada, busca linealmente si una llave ya se obtuvo y su costo se acerca a O(K² · (S + E)) (ver [mediciones.md](mediciones.md)) | La razón de la incremental supera 20, es decir, el doble del factor de tamaño (SC-007, FR-346) |

El tiempo se mide sobre la función pura, con el `MapaCripta` y la `UbicacionLlavesDTO` ya construidos (los datos «ya descargados»), con `time.perf_counter_ns`. La medición en la cripta publicada más grande se hace además a mano, porque `--bench` no usa red ni la caché del usuario: con los datos guardados (mapa, datos generales y llaves) y sin `FuenteSoloLocal` ni `--offline`, que exigen la cripta completa con el contenido de todas las salas, aunque la verificación no lo necesita (paso 3 de [quickstart.md](quickstart.md); con una cripta completa, `--offline` y `FuenteSoloLocal` siguen siendo una alternativa). Los resultados van a [mediciones.md](mediciones.md), corridos con la máquina libre.

**Motivo**: el principio VII pide medir la alternativa descartada con criptas sintéticas por semilla; la cadena de llaves es la carga que separa O(S + E) de O(K · (S + E)). Los tamaños son parámetros del bench, no datos de una cripta (principio V).

**Alternativas descartadas**:
- *Medir solo el tiempo total de `--verificar`*: mezcla red, disco y conversión; no aísla la decisión de estructura.
- *n = 10 000 en la sección A*: la alternativa repetida tardaría minutos; el factor 10 entre 300 y 3 000 ya muestra la diferencia de orden.

## 10. Pruebas

**Decisión**: `unittest`, en la raíz, una prueba por comportamiento con el FR o el código B-R en el nombre. Las pruebas se escriben primero y se ejecutan en rojo antes de implementar, con la salida guardada como evidencia en la tarea (falla de aserción o el `NotImplementedError` del cuerpo provisional, no un error de importación).

| Archivo | Cubre |
|---|---|
| `test_mapa_con_llaves.py` | §1: `AristaMapaDTO`/`AristaCripta` con `llave`, `esqueleto()` con la API falsa v2, `--offline` (`ClienteOffline`) y `FuenteSoloLocal`; valores por defecto que no rompen a quien ya construye aristas |
| `test_indice_llaves.py` | §4: orden, repetidos, búsqueda presente y ausente, lista vacía |
| `test_resolubilidad_regla.py` | FR-332 a FR-334 y FR-336 a FR-338 sobre mapas hechos a mano (cadena, salida de un solo sentido, sala inicial = salida, puerta sin llave, misma llave en varias puertas, varios bloqueos) |
| `test_resolubilidad_apendice_b.py` | B-R1 a B-R4 con `CASOS_APENDICE_B`, ejecutando sus pasos `verificar` e `iniciar_sin_forzar` |
| `test_resolubilidad_determinismo.py` | FR-335: dos ejecuciones, orden de la respuesta de llaves invertido, con y sin contenido guardado, cliente HTTP falso / `--offline` / `FuenteSoloLocal` (FR-342); equivalencia con la estrategia repetida en criptas al azar por semilla (principio III) |
| `test_resolubilidad_datos.py` | FR-341 y FR-343: 0 solicitudes con llaves guardadas, a lo sumo la consulta de la 009 sin ellas, sin `obtener_contenido`; errores de datos con código 2 |
| `test_resolubilidad_inicio.py` | FR-339, FR-340, FR-344: sin `forzar` no inicia y no crea log; con `forzar` inicia con aviso; resoluble sin aviso; llaves no disponibles sigue con el aviso de FR-313; misma operación y mismo resultado que `verificar`; reproducción y partida cargada no verifican |
| `test_resolubilidad_reporte.py` | FR-330, FR-331, FR-336 a FR-338: texto del reporte y códigos de salida 0/1/2 |

Todas corren sin red con la API falsa v2; las de la capacidad se agregan a `tests_labs/sin_red.py`.

## 11. Riesgos

| Id | Riesgo | Mitigación |
|---|---|---|
| R1 | Alguna puerta real cerrada sin `llave` en el esqueleto, o con la llave solo en el contenido | Se trata como `SIN_LLAVE` (FR-333) y el reporte lo dice; si aparece en una cripta publicada, se revisa la spec antes del código (principio X) |
| R2 | El interfaz provisional (§12) cambia después de que Fernanda lo conecte | El primer grupo de tareas fija firmas y campos con pruebas de contrato; cualquier cambio posterior se avisa y pasa por este plan |
| R3 | `MonticuloMinimo` tiene nombres de parámetro `costo`, `sala` | Se usa tal cual con `(sala, número)`; el código nuevo lo comenta. No se modifica el montículo (lo usan la 001 y la 009) |
| R4 | La cripta publicada más grande cambia | El código no tiene tamaños fijos; la medición manual se repite con la que haya y la sección C del bench usa una sintética mucho mayor |
| R5 | Medir con la máquina cargada | Las mediciones de `mediciones.md` se corren con la máquina libre y se anotan versión de Python y fecha (cabecera del bench) |

## 12. Entrega temprana para Fernanda

**Decisión**: el primer grupo de tareas (después del hallazgo §1) entrega:

- `DTO/ResultadoVerificacionDTO.py` completo (campos, `codigo_salida()`);
- `Logica/VerificacionResolubilidad.py` con las firmas `verificar_resolubilidad(...)`, `verificar(fuente, cripta_id, llaves=None)` y `CriptaNoResoluble`, con **cuerpo provisional** que devuelve `ResultadoVerificacion(cripta_id, resoluble=None, motivo_error="La verificación de resolubilidad todavía no está implementada.")` (código 2);
- `Logica/ReporteVerificacion.py` con `lineas_reporte` y `aviso_forzado` que ya formatean el caso de error;
- `EstadoJuegoServicio.verificar(cripta_id)`, `avisoResolubilidad()` y el parámetro `forzar` en `iniciarJuego` (aceptado y todavía sin efecto).

Con eso Fernanda conecta `--verificar` y `--forzar` en `main.py` y la vista contra el contrato de [contracts/interfaz-verificacion.md](contracts/interfaz-verificacion.md) mientras se implementa el algoritmo. Esta capacidad **no** cablea esas opciones.

**Motivo**: desacopla los dos trabajos sin que ninguno tenga que inventar la forma del otro.

**Alternativas descartadas**: *esperar a que el algoritmo esté listo*: bloquea a Fernanda varias tareas sin necesidad.
