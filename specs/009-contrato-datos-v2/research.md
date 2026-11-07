# Investigación (Fase 0): Contrato de datos v2 y ubicación de llaves

**Capacidad**: `009-contrato-datos-v2` | **Fecha**: 2026-11-06 | **Especificación**: [spec.md](spec.md)

Cada sección sigue el formato **Decisión / Motivo / Alternativas descartadas**. k = llaves de la cripta, N = salas de la cripta, C = salas con contenido guardado, B = bytes del archivo de la cripta.

## 0. Lo que ya existe y se reutiliza

| Pieza | Dónde | Uso en esta capacidad |
|---|---|---|
| Contrato común de clientes | `adaptadores/Interfaz.py` (`ClienteInterfaz`) | Se agrega `obtener_llaves` |
| Cliente HTTP | `adaptadores/cliente_http.py` (`ClienteCripta._solicitar`) | Cada `_solicitar` suma 1 a `solicitudes_realizadas`, incluidos los 429. La consulta de llaves usa ese mismo camino, así que cuenta para el presupuesto sin código nuevo de conteo |
| Cliente persistente | `adaptadores/cliente_persistente.py` | `_asegurar_cripta` valida la versión una vez por sesión. Si no coincide, `AlmacenDisco._validar` **vacía** `cripta_<id>.bin` |
| Cliente offline | `adaptadores/cliente_offline.py` | Lee solo de `AlmacenDisco`, lanza `ErrorOffline` con mensaje |
| Almacén en disco | `adaptadores/AlmacenDisco.py` sobre `ArchivoIndexado` | Archivo por cripta con claves `version`, `datos`, `salas`, `contenido:<n>`. La escritura va a un temporal y se reemplaza el archivo, así que un corte no deja un archivo a medias (caso límite «fallo a medio guardar») |
| Servicio de cripta | `adaptadores/servicioCripta.py` | Memoriza datos generales y esqueleto por cripta; `reporte()` arma el reporte final con `solicitudes_realizadas` |
| Ordenamiento propio | `Logica/ordenamiento.py` (`ordenar_adaptativo`) | Detección de entradas repetidas (§5) |
| Campo de costos y montículo | `Logica/CampoDeCostos.py`, `Logica/MonticuloMinimo.py` | Precarga por costo en el bench (§8) |
| API falsa de la Parte I | `tests_labs/api_falsa.py` (`HttpFalso`, `HttpConfigurable`) | Se amplía a v2 (§7) |

## 1. Forma de la respuesta de `/criptas/<id>/llaves`

**Decisión**: esta forma, confirmada con el Swagger el 2026-11-06 (esquemas `LlavesResponse`: `llaves` obligatorio, lista de objetos; y `KeyLocation`: `id` texto, `sala` entero, `enemigo` texto o `null`):

```json
{"llaves": [{"id": "itm_llave_bronce", "sala": 3},
            {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}]}
```

`enemigo` ausente o `null` significa que la llave está en el suelo. Toda la lectura del JSON queda en una sola función (`leer_llaves`, contrato en [contracts/consulta-llaves.md](contracts/consulta-llaves.md)): si los nombres reales son otros, se cambia solo esa función.

**Motivo**: el Swagger del servicio define esta forma (`LlavesResponse` / `KeyLocation`). Coincide con la convención de `/contenido` (`instancia` para enemigos, ids de catálogo para objetos). `api_completa.txt` es anterior a la consulta y no la incluye.

**Pendiente**: ninguno. R1 está mitigado por el Swagger (§9). La comprobación con una llamada real es opcional (paso 0 de `quickstart.md`); si la respuesta real difiriera, se corrige solo `leer_llaves` y este contrato.

**Alternativas descartadas**: un lector tolerante que acepta varios nombres de campo. Esconde errores del servicio y contradice FR-311 (una respuesta mal formada debe rechazarse).

## 2. Dónde vive cada parte de la consulta

**Decisión**:

| Capa | Responsabilidad |
|---|---|
| `ClienteInterfaz.obtener_llaves(cripta_id, solo_guardadas=False) -> list[dict]` | Devuelve la lista cruda (lo que trae `"llaves"`). Igual que el resto de la interfaz, que devuelve JSON crudo |
| `ClienteCripta` | Una solicitud `GET /criptas/<id>/llaves`. Con `solo_guardadas=True` no hace la solicitud y lanza `LlavesNoDisponibles` (no tiene disco) |
| `ClientePersistente` | Si `llaves` está en `cripta_<id>.bin` (ya validado por versión), lo devuelve sin red. Si falta y `solo_guardadas`, lanza `LlavesNoDisponibles` («sin presupuesto»). Si no, pide al HTTP, **valida** (§5) y solo después guarda |
| `ClienteOffline` | Lee `llaves` del disco; si falta, lanza `ErrorOffline` con «Faltan las llaves de la cripta X» |
| `ServicioCripta.ubicacion_llaves(cripta_id) -> UbicacionLlavesDTO` | Decide `solo_guardadas` según el presupuesto (§3), valida (§5), convierte a listas paralelas y lo memoriza por cripta para la sesión (FR-301). Traduce `ErrorOffline`, `ErrorSinConexion`, `RuntimeError` HTTP y `LlavesInvalidas` a `LlavesNoDisponibles` con un mensaje que nombra la cripta |
| `ServicioCripta.esqueleto(cripta_id) -> MapaDTO` | Nombre público del esqueleto normalizado. `obtener_mapa` pasa a delegar en él (se conserva por compatibilidad con la capacidad 001) |
| `EstadoJuegoLogica.obtenerLlaves()` | Único punto por el que el modelo pide las llaves. Si `llaves` ya está, la devuelve. Si no, llama a `ubicacion_llaves`; con `LlavesNoDisponibles` guarda el aviso, deja `llaves = None` y la partida sigue (FR-313). No memoriza el fallo |
| `EstadoJuegoLogica.iniciarJuego` | En una partida nueva llama a `obtenerLlaves()` enseguida |
| Restauración de una partida guardada | No pide nada: reinicia `llaves` y `avisoLlaves` a `None`; las llaves llegan la primera vez que alguien llama a `obtenerLlaves()` (FR-325) |

`LlavesNoDisponibles` y `DatoLocalFaltante` se definen en `Logica/FuenteCripta.py`, el contrato del modelo. Así el modelo captura un error suyo sin importar adaptadores (principio IV).

**Motivo**: repite el reparto que ya tiene `obtener_contenido`: el cliente trae y guarda, el servicio resuelve y entrega al modelo objetos propios.

**Alternativas descartadas**:
- *Validar solo en `ServicioCripta`*: el persistente ya habría guardado la respuesta antes de validarla, lo que viola FR-310 o exige un «deshacer guardado».
- *Pedir las llaves de forma perezosa también en la partida nueva*: la capacidad 003 verifica al iniciar, así que no se ahorraría nada y el momento de la solicitud quedaría menos predecible. En la partida **cargada** sí se piden bajo demanda (FR-325): al cargar no hay verificación, y pedirlas en ese momento gastaría una solicitud que quizá nadie use.
- *Pedirlas al restaurar una partida guardada*: contradice FR-325 (al cargar no se consulta nada).

## 3. Presupuesto

**Decisión**: antes de pedir las llaves, `ServicioCripta` calcula `restante = presupuesto_solicitudes - solicitudes_realizadas`. Si `restante < 1`, llama con `solo_guardadas=True`: si están en disco no gasta nada; si no, se lanza `LlavesNoDisponibles` («sin presupuesto», FR-309). La solicitud que sí se hace queda en `solicitudes_realizadas` y por eso aparece en `reporte()` (FR-304), sin código nuevo en el reporte.

**Efecto medido sobre la primera partida** (con `HttpFalso`): hoy, la primera vez que se juega una cripta se gastan 6 solicitudes (`DOCUMENTACION_API.md` §8); con esta capacidad son 7. Con la misma versión, la segunda partida suma 0 por las llaves (SC-001). Se verifica en `test_llaves_presupuesto.py`.

**429 con el presupuesto al límite** (decisión tras el analyze): `ServicioCripta` pasa además `limite_solicitudes = restante`. El HTTP reintenta un 429 solo mientras el total de solicitudes de **esta** consulta no llegue a ese límite; con `restante == 1`, un 429 **no se reintenta**: lanza `RuntimeError` («429 sin presupuesto para reintentar»), que el servicio convierte en `LlavesNoDisponibles` (aviso de FR-313). Así la consulta de llaves nunca hace que la partida supere el presupuesto (SC-005). Sin límite (`None`), el HTTP conserva su regla actual (`MAX_REINTENTOS_429`).

**Alternativas descartadas**: que el cliente HTTP conozca el presupuesto. Mezcla una regla de juego con el transporte, y el presupuesto llega en los datos generales, que el HTTP no interpreta. El límite que recibe es solo un número de solicitudes para esa llamada, no la regla de juego.

**Hallazgo**: hoy el presupuesto solo se **reporta**, no se hace cumplir. Esta capacidad lo hace cumplir **únicamente** para la consulta de llaves (FR-309, SC-005). Hacerlo cumplir para el contenido de las salas queda fuera de alcance.

## 4. Guardado y versión: alternativas comparadas

| | **A. Clave `llaves` dentro de `cripta_<id>.bin`** (elegida) | B. Archivo aparte `llaves_<id>.bin` con su propia `version` | C. Las llaves dentro del registro `datos` |
|---|---|---|---|
| Invalidación por versión (FR-307) | Automática: `_validar` vacía el archivo completo y las llaves desaparecen con lo demás | Hay que validar dos archivos. Si se valida uno y el otro no, las llaves quedan sueltas | Automática, pero `datos` se reescribe en cada cambio de versión **antes** de pedir las llaves: hay una ventana con `datos` nuevos sin llaves |
| Datos de la Parte I (FR-308) | El archivo no tiene la clave → se consulta una vez. Sin borrar nada a mano | El archivo no existe → se consulta. Sin borrar nada | `datos` existe sin campo de llaves: hay que distinguir «sin llaves» de «la cripta no tiene llaves» dentro del mismo registro |
| Lista vacía válida | `[]` se distingue de `None` (clave ausente) | Igual que A | Hay que usar un centinela dentro de `datos` |
| Costo de guardar | O(B): `escribir_varios` reescribe el archivo completo, **una vez** por cripta y versión | O(k): archivo pequeño | O(B) |
| Costo de leer | O(claves del índice) + O(k) | O(1 clave) + O(k) | Se lee `datos` completo |
| Lectura solo local (FR-314) | Un archivo por cripta: `cripta_completa` y el envoltorio miran un solo lugar | Dos lugares que deben coincidir en versión | Un lugar |
| Cambios en `AlmacenDisco` | `guardar_llaves`, `leer_llaves` (2 métodos de una línea) | Lo mismo, más `validar_llaves` y un archivo y nombre nuevos | Modificar el formato de `datos`, que también usan el log y los puntajes |

**Decisión**: A.

**Motivo**: reutiliza tal cual la validación de versión existente (principio VI), tiene un único punto de invalidación y no hay estado intermedio inconsistente. El único costo extra de A frente a B, reescribir el archivo completo, ocurre **una vez por cripta y versión**, y se mide (bench `llaves`, sección B) para confirmar que es despreciable frente a una solicitud de red.

**Criterio para cambiar de decisión**: si en la cripta sintética de 5 000 salas con contenido completo guardar las llaves con A supera los 50 ms, se pasa a B. El antes y el después se registran en `DECISIONES.md`.

## 5. Validación de la respuesta (FR-311, con las clarificaciones 2 y 3)

**Decisión**: una función pura `validar_llaves(crudas, existe, contenido_guardado) -> (ids, salas, enemigos)` que lanza `LlavesInvalidas(motivo)`:

1. Cada entrada debe tener `id` (texto no vacío) y `sala` (entero); `enemigo`, si viene, debe ser texto.
2. `existe[sala]` debe ser verdadero. `existe` es una lista de booleanos de tamaño `mayor id + 1`, armada desde el esqueleto, igual que `MapaCripta.existe`.
3. **Entradas idénticas repetidas**: se arma una lista de posiciones `0..k-1` y se ordena con `ordenar_adaptativo` por la clave `(id, sala, enemigo o "")`. Después se comparan vecinas. Costo O(k log k).
4. **Enemigo**: si la entrada trae `enemigo` y `contenido_guardado(sala)` no es `None`, el enemigo debe aparecer entre las `instancia` de ese contenido. Si el contenido no está guardado, se acepta sin hacer solicitudes.

`contenido_guardado` es una función que entrega quien llama: el persistente y el offline leen `AlmacenDisco.leer_contenido` y el HTTP solo devuelve `None`. Nunca hace solicitudes.

**Alternativas descartadas**:
- *Comparar todas las parejas* O(k²): más simple, se mide como alternativa (bench `llaves`, sección C). Se descarta si con k = 1 000 es más lenta, pero con k chica cualquiera de las dos sirve.
- *`set` de tuplas*: prohibido por el principio I.

## 6. Fuente solo local (FR-314 a FR-317)

**Decisión**: `adaptadores/fuente_solo_local.py`, clase `FuenteSoloLocal(fuente, almacen, version_vigente)`. Envuelve un `ServicioCripta` armado sobre `ClienteOffline(AlmacenDisco)` (con `fabrica.crear_fuente_solo_local(carpeta, version_vigente)`):

- Antes de cada operación compara `almacen.version_cripta(id)` con `version_vigente`. Si son distintas, lanza `DatoLocalFaltante("la cripta X está guardada con la versión v1, se necesita v2")` (FR-317).
- Convierte `ErrorOffline` en `DatoLocalFaltante` con el dato y la cripta (FR-315).
- `precargar_vecinas` no hace nada y devuelve 0. La consulta histórica no precarga.
- **No escribe nada**: `ClienteOffline` no tiene métodos de escritura y el envoltorio no llama a `validar_cripta`, que **vacía** el archivo si la versión no coincide. Llamarlo violaría FR-315 («sin modificar lo guardado»).

**Garantía de 0 solicitudes (SC-003)**: estructural. La composición no contiene ningún cliente HTTP. La prueba lo comprueba además con un `HttpFalso` espía que no debe recibir ninguna llamada.

**Alternativas descartadas**:
- *Usar `--offline` tal cual*: no cumple FR-317. `ClienteOffline` acepta cualquier versión guardada.
- *Un indicador `solo_local` dentro de `ClientePersistente`*: mezcla dos políticas en una clase y deja la red al alcance por error.

## 7. API falsa v2 (FR-318 a FR-321)

**Decisión**: se amplía `tests_labs/api_falsa.py` sin romper a quienes la usan hoy:

- `HttpFalso.obtener_llaves(cripta_id)`: llaves de su cripta de 3 salas. Una en el suelo de la sala 1 y `itm_llave_negra` soltada por `e-301` en la sala 3. Se registra en `llamadas` como `("llaves", cripta_id)`, así que cuenta en `solicitudes_realizadas`.
- `HttpConfigurable(..., llaves=None, fallo_llaves=None)`: `llaves` es una lista de `(id, sala, enemigo o None)`. `fallo_llaves` vale `"sin_respuesta"` (lanza `ErrorSinConexion`), `"invalida"` (lanza `LlavesInvalidas("respuesta sin llaves")`, lo mismo que daría `leer_llaves` sobre una respuesta sin la clave `llaves`, porque la API falsa entrega la lista ya extraída) o `None`. Las respuestas que FR-311 rechaza por su contenido se arman pasando `llaves` malas.
- `cripta_v2(semilla)`: cripta de referencia con costos distintos de 100, un cazador con rango, una llave en el suelo, una soltada por un enemigo y una llave repetida en dos salas.
- `CASOS_APENDICE_B`: lista de `(código, descripción, constructor)`, uno por caso del Apéndice B.

**Determinismo**: sin `random` global ni hora. Las criptas sintéticas usan `random.Random(semilla)`, como `cripta_sintetica.py`.

**Apéndice B**: el texto no estaba en el repositorio y se transcribió el 2026-11-06 en [contracts/api-falsa-v2.md](contracts/api-falsa-v2.md): 23 casos con códigos B-T1 a B-T7, B-N1 a B-N6, B-R1 a B-R4 y B-L1 a B-L6. `CASOS_APENDICE_B` tiene una entrada por código.

## 8. Medición: cazador que cruza salas sin cargar, precarga por saltos frente a por costo (FR-322 a FR-324)

**Qué cuesta hoy**: cuando un enemigo entra a una sala que no está en el modelo, `EstadoJuegoLogica._cargarSala` la construye **sin precargar** (comentario en la línea 370). Eso cuesta una solicitud de contenido, más las fichas que falten, si la sala no estaba ya en disco por la precarga del jugador.

**Decisión**: bloque nuevo de `--bench` llamado `llaves` con estas secciones:

| Sección | Mide | Elegida | Alternativa |
|---|---|---|---|
| A. Presupuesto con cazadores | Solicitudes extra que dispara un cazador (cargas iniciadas por un enemigo) y total de solicitudes de la partida | Precarga actual por saltos (`precargar_vecinas`) | Precarga por costo: mismo lote de 10, llenado por costo de ruta creciente desde la sala del jugador (`CampoDeCostos`, con desempate por menor id) |
| B. Guardar llaves | Tiempo de guardar y leer `llaves` con 50, 500 y 5 000 salas con contenido | A (en el archivo de la cripta) | B (archivo aparte) |
| C. Entradas repetidas | Tiempo de validar con k = 10, 100 y 1 000 | Ordenar y comparar vecinas | Comparar todas las parejas |

**Cómo se arma la sección A**: rejillas `esqueleto_rejilla(lado, semilla, costo_max=9)` de 10×10, 20×20 y 40×40, con 1, 4 y 16 cazadores de rango 600 colocados por semilla. El jugador sigue un guion fijo de 60 movimientos. Las dos reglas corren sobre **las mismas** criptas, semillas y guion, con `HttpConfigurable` contando solicitudes. La precarga por costo se implementa **solo dentro de `bench/llaves.py`**, como subclase de `ServicioCripta` que cambia el orden del lote: el juego no cambia (FR-324).

**Salida**: tabla en `--bench` y resumen en `mediciones.md` con la recomendación (mantener o cambiar). Si la recomendación es cambiar, se abre una especificación aparte.

**Alternativas descartadas**: medir con la cripta real. Gasta presupuesto, no es determinista y viola el principio V.

## 9. Riesgos y pendientes

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | La forma real de `/llaves` es distinta de la asumida | **Mitigado**: la forma se confirmó con el Swagger (`LlavesResponse` / `KeyLocation`) el 2026-11-06. Se mantiene un único lector (§1) y la comprobación con una llamada real queda opcional |
| R2 | Casos del Apéndice B no transcritos | **Mitigado**: transcritos el 2026-11-06 (§7) |
| R3 | `adaptadores/servicioCripta.py` ya importa `collections.deque` (Parte I, `salas_vecinas` y `_armar_salidas`), lo que viola el principio I | Esta capacidad **no** agrega usos nuevos. Ya se registró en la capacidad 005 (observación 2); retirarlo corresponde a la capacidad que adopte el recorrido por niveles en la precarga |
| R5 | Una partida restaurada sobre una lógica que ya jugó otra cripta arrastra sus llaves | La restauración reinicia `llaves` y `avisoLlaves` a `None` (FR-325); lo prueba `test_llaves_partida_cargada` |
| R4 | `--replay` llama a `iniciarJuego`: con red pediría las llaves | Con el persistente, las llaves ya están en disco y la reproducción no gasta nada. En `--offline` sin llaves se emite el aviso y la reproducción sigue (FR-313), así que el `partida.log` no cambia |
