# Tareas: Contrato de datos v2 y ubicación de llaves

**Entrada**: documentos de diseño en `specs/009-contrato-datos-v2/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerrequisitos**: `spec.md` con las 3 clarificaciones de la sesión 2026-11-06; forma de `/llaves` confirmada con el Swagger (`LlavesResponse` / `KeyLocation`); 23 casos del Apéndice B transcritos en `contracts/api-falsa-v2.md`. Se apoya en código existente: `adaptadores/` (clientes, `AlmacenDisco`, `ServicioCripta`, `fabrica`), `Logica/ordenamiento.py`, `Logica/CampoDeCostos.py`, `tests_labs/api_falsa.py` y `tests_labs/cripta_sintetica.py`.

**Pruebas**: se incluyen en todas las historias porque la constitución (principio IX) exige una prueba automatizada por escenario de aceptación. Cada prueba se escribe **antes** del código que la hace pasar y debe fallar primero. Ninguna prueba usa red: el cliente HTTP se prueba sustituyendo `requests.get` con `unittest.mock.patch`.

**Organización**: tareas agrupadas por historia de usuario. Entre paréntesis, los requisitos o principios que atiende cada tarea.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias de tareas incompletas).
- **[USn]**: historia de `spec.md` a la que pertenece.
- Las rutas son relativas a la raíz del repositorio. Las pruebas usan `unittest` (`test_*.py` en la raíz).

## Reglas para todas las tareas (constitución)

- **No usar** `dict` ni `set` como índice, caché o tabla de búsqueda; ni `heapq`, `bisect`, `collections`, `networkx` ni bibliotecas de grafos. Se permiten `list`, `struct`, `json` y `requests`. Para ordenar se usa `ordenar_adaptativo` (`Logica/ordenamiento.py`), nunca `sorted()` ni `list.sort()`. El `dict` de `respuesta.json()` solo se lee en `adaptadores/llaves.py` (`leer_llaves`).
- El `deque` de `adaptadores/servicioCripta.py` es de la Parte I: **no agregar usos nuevos**.
- Ningún id de llave, sala o enemigo, presupuesto ni tamaño de una cripta concreta en código de producción.
- El modelo (`Logica/`, `DTO/`) no importa red, disco ni vista. Los errores que captura el modelo se definen en `Logica/FuenteCripta.py`.
- **No se modifican** `precargar_vecinas` ni `salas_vecinas` (FR-324), el formato de partida, el `partida.log` ni `ArchivoIndexado`.
- Las llaves **no** entran al estado guardado ni al `partida.log` (principio II, data-model.md).
- Los commits de especificación y plan van **antes** y **separados** de los de código (principio X).

---

## Fase 1: Preparación

**Propósito**: línea base y revisión de la constitución.

- [ ] T001 Revisar `plan.md`, `research.md` y este `tasks.md` contra la lista de prohibidos del principio I y anotar el resultado en la sección Notas de `specs/009-contrato-datos-v2/checklists/requirements.md`. Comprobar en especial que la detección de repetidos (`ordenar_adaptativo`), la lista `existe` de booleanos y la precarga por costo del bench (`CampoDeCostos`/`MonticuloMinimo`) no necesitan `dict`, `set` ni `collections`. (I)
- [ ] T002 [P] Ejecutar `python -m unittest discover -p "test_*.py"` y los laboratorios `tests_labs/prueba_cliente_persistente.py`, `tests_labs/prueba_cliente_offline.py`, `tests_labs/prueba_fabrica.py` y `tests_labs/prueba_precarga_presupuesto.py`, y anotar la línea base (pruebas que pasan y fallan) en las Notas de `specs/009-contrato-datos-v2/checklists/requirements.md`. Así se detectan regresiones de la Parte I, la 001 y la 005. (IX)

**Punto de control**: revisión anotada y línea base registrada.

---

## Fase 2: Fundamentos (bloquea todas las historias)

**Propósito**: contrato de errores, DTO, lector y validador, guardado y la consulta en la interfaz común. Como `obtener_llaves` es abstracto, los tres clientes lo implementan aquí; si no, ninguno se podría instanciar.

- [ ] T003 [P] En `Logica/FuenteCripta.py` agregar `class LlavesNoDisponibles(RuntimeError)` y `class DatoLocalFaltante(RuntimeError)`, y al `Protocol` `FuenteCripta` los métodos `esqueleto(self, cripta_id: str) -> MapaDTO` y `ubicacion_llaves(self, cripta_id: str) -> UbicacionLlavesDTO`. Sin importar adaptadores. (FR-309, FR-313, FR-315, IV)
- [ ] T004 [P] Crear `DTO/LlavesDTO.py` con `UbicacionLlavesDTO(cripta_id: str, version: str | None, ids: list[str], salas: list[int], enemigos: list[str | None])`:
  - Valida en el constructor la invariante «`len(ids) == len(salas) == len(enemigos)`» y lanza `ValueError` si no se cumple.
  - `cantidad()` es O(1).
  - `ubicaciones_de(id_llave) -> list[int]` devuelve, en O(k), las **posiciones** donde aparece la llave, en el orden de la respuesta.
  - Una lista vacía es válida («la cripta no tiene llaves»).
  - Sin `dict` ni `set`. (FR-302)
- [ ] T005 [P] Crear `test_llaves_validacion.py` con:
  - Las 9 filas de la tabla «Casos de validación» de `contracts/consulta-llaves.md`, una prueba por fila, con un nombre que cite FR-311 o FR-302.
  - Pruebas de `leer_llaves`: respuesta sin `llaves`, con `llaves` que no es lista y con `llaves: []`.
  - El caso «enemigo presente y contenido no guardado»: comprobar con un `contenido_guardado` espía que solo se consultó la sala indicada y que no hubo solicitudes.
  - Comprobar que el orden de la respuesta se conserva.

  Deben fallar porque `adaptadores/llaves.py` aún no existe. (FR-302, FR-311)
- [ ] T006 Crear `adaptadores/llaves.py`:
  - `class LlavesInvalidas(ValueError)` con un atributo `motivo`.
  - `leer_llaves(respuesta: dict) -> list[dict]`: devuelve `respuesta["llaves"]`; si falta o no es lista, lanza `LlavesInvalidas`.
  - `validar_llaves(crudas: list[dict], existe: list[bool], contenido_guardado) -> tuple[list[str], list[int], list[str | None]]`, en el orden de research.md §5:
    1. Cada entrada debe tener `id` (texto no vacío) y `sala` (entero, no `bool`); `enemigo`, si viene, debe ser texto o `None`.
    2. `0 <= sala < len(existe)` y `existe[sala]`.
    3. Entradas idénticas `(id, sala, enemigo o "")`: ordenar las posiciones `0..k-1` con `ordenar_adaptativo` por esa clave y comparar vecinas.
    4. Si hay `enemigo` y `contenido_guardado(sala)` no es `None`, el enemigo debe estar entre las `instancia` de `contenido["enemigos"]`.

    Debe hacer pasar T005. (FR-302, FR-310, FR-311)
- [ ] T007 [P] En `adaptadores/AlmacenDisco.py` agregar `guardar_llaves(cripta_id, llaves: list[dict])` (clave `"llaves"` del archivo de la cripta) y `leer_llaves(cripta_id) -> list[dict] | None`. `None` significa clave ausente y `[]` significa cripta sin llaves. Agregar al laboratorio `tests_labs/prueba_almacen_disco.py` tres casos:
  - Se guarda y se lee la lista de llaves.
  - Se guarda `[]` y se lee `[]`, distinto de `None`.
  - Tras `validar_cripta` con otra versión, `leer_llaves` devuelve `None`.

  (FR-305, FR-307)
- [ ] T008 [P] Ampliar `tests_labs/api_falsa.py` (sin cambiar lo que ya existe):
  - `HttpFalso.obtener_llaves(cripta_id)` registra `("llaves", cripta_id)` en `llamadas` y devuelve `[{"id": "itm_llave_bronce", "sala": 1}, {"id": "itm_llave_negra", "sala": 3, "enemigo": "e-301"}]`, la **lista** ya extraída, como hace el HTTP real tras `leer_llaves`.
  - `HttpConfigurable.__init__` acepta `llaves=None` (lista de `(id, sala, enemigo o None)`) y `fallo_llaves=None`. Con `"sin_respuesta"` lanza `ErrorSinConexion`, importada de `adaptadores/cliente_http.py`. Con `"invalida"` lanza `LlavesInvalidas("respuesta sin llaves")`, que es lo que daría `leer_llaves` sobre `{"sin_llaves": []}`.
  - La llamada se registra en ambos casos de fallo.

  Comprobar que los laboratorios existentes de la línea base (T002) siguen igual. (FR-318, FR-321)
- [ ] T009 En `adaptadores/Interfaz.py` agregar a `ClienteInterfaz` el método abstracto `obtener_llaves(self, cripta_id: str, solo_guardadas: bool = False) -> list[dict]`, con la docstring de `contracts/interfaz-clientes.md`. En el mismo cambio, implementarlo en `adaptadores/cliente_http.py` (`ClienteCripta`):
  - Con `solo_guardadas=True` lanza `LlavesNoDisponibles` (de `Logica/FuenteCripta.py`) con el texto «no queda presupuesto y no hay llaves guardadas de la cripta X», sin hacer la solicitud.
  - Si no, devuelve `leer_llaves(self._solicitar(f"/criptas/{cripta_id}/llaves"))`. El conteo ya lo hace `_solicitar`.

  (FR-301, FR-304, FR-309)
- [ ] T010 En `adaptadores/cliente_offline.py` (`ClienteOffline`) implementar:
  - `obtener_llaves(cripta_id, solo_guardadas=False)`: devuelve `almacen.leer_llaves(cripta_id)`; si es `None`, lanza `ErrorOffline(f"Faltan las llaves de la cripta {cripta_id}. Juega una vez con conexión.")`.
  - `contenido_en_disco(cripta_id, sala) -> dict | None`, que devuelve `almacen.leer_contenido`.

  No cambiar `cripta_disponible`: una cripta sin llaves sigue siendo jugable (FR-313). (FR-303, FR-312)
- [ ] T011 En `adaptadores/cliente_persistente.py` (`ClientePersistente`) implementar `obtener_llaves(cripta_id, solo_guardadas=False)`:
  1. `self._asegurar_cripta(cripta_id)`.
  2. Si `almacen.leer_llaves` no es `None`, devolverlo sin red.
  3. Si `solo_guardadas`, lanzar `LlavesNoDisponibles` («sin presupuesto»).
  4. Si no, `crudas = self.cliente.obtener_llaves(cripta_id)`. Armar `existe` desde `self.obtener_salas(cripta_id)` (lista de booleanos de tamaño `mayor id + 1`) y llamar a `validar_llaves(crudas, existe, lambda s: self.almacen.leer_contenido(cripta_id, s))`.
  5. **Solo si es válida**, `almacen.guardar_llaves(cripta_id, crudas)` y devolverla. Si `LlavesInvalidas`, se propaga sin guardar nada.

  Agregar también `contenido_en_disco(cripta_id, sala)`. (FR-301, FR-305, FR-306, FR-310)

**Punto de control**: `python -m unittest test_llaves_validacion` pasa. Los laboratorios de la línea base siguen igual: los tres clientes se pueden instanciar.

---

## Fase 3: Historia 1 — Conocer la ubicación de las llaves con una sola solicitud (P1) 🎯 MVP

**Objetivo**: al iniciar una partida el juego obtiene, una vez, la lista de llaves con su sala y, cuando corresponde, su enemigo. La solicitud se descuenta del presupuesto y aparece en el reporte final.

**Prueba independiente**: con `HttpConfigurable` y una carpeta temporal sin nada guardado, iniciar una partida y comprobar la lista, `veces("llaves") == 1`, el contador y el `reporte().texto()`.

### Pruebas de la Historia 1 (escribir primero; deben fallar)

- [ ] T012 [P] [US1] Crear `test_llaves_clientes.py`:
  - **(a)** `ClienteCripta.obtener_llaves` con `requests.get` sustituido por `unittest.mock.patch`, que devuelve 200 con `{"llaves": [...]}`. Comprobar la URL `…/criptas/<id>/llaves`, el encabezado `X-Cripta-Client-Id` y `solicitudes_realizadas == 1`. Con `solo_guardadas=True` no hay llamada.
  - **(b)** H1-2: llave `L` soltada por `E`, que inicia en la sala 7, devuelve `ids=[L]`, `salas=[7]`, `enemigos=[E]` en el DTO de `ServicioCripta.ubicacion_llaves`.
  - **(c)** H1-3: llave `M` en el suelo de la sala 3 devuelve `enemigos=[None]`.
  - **(d)** H1-5: `B` en las salas 3 y 9 da `ubicaciones_de("B")` con dos posiciones.
  - **(e)** H5-5 / FR-303: la misma cripta guardada da **la misma** lista por el HTTP simulado, por el persistente y por el offline.

  (FR-302, FR-303, FR-304)
- [ ] T013 [P] [US1] Crear `test_llaves_presupuesto.py`:
  - **(a)** H1-1: la primera partida en una carpeta vacía (con `nueva_ejecucion` o el equivalente con `HttpConfigurable`) hace exactamente un `("llaves", …)`, el contador sube en 1 respecto de la misma partida sin consulta de llaves (de 6 a 7 con `HttpFalso`, research.md §3), y `reporte(cid).texto()` refleja ese total.
  - **(b)** H1-4: llamar dos veces a `ubicacion_llaves` en la misma sesión deja `veces("llaves") == 1`.
  - **(c)** SC-005: con el presupuesto agotado (`presupuesto_solicitudes` de los datos igual a las solicitudes ya hechas) y sin llaves guardadas, **no** se llama a `("llaves", …)` y se lanza `LlavesNoDisponibles`, cuyo mensaje nombra la cripta.
  - **(d)** Con el presupuesto agotado y llaves guardadas, las devuelve sin solicitudes.

  (FR-301, FR-304, FR-309)

### Implementación de la Historia 1

- [ ] T014 [US1] En `adaptadores/servicioCripta.py` agregar `esqueleto(cripta_id) -> MapaDTO`, moviendo ahí el cuerpo actual de `obtener_mapa`, y hacer que `obtener_mapa` devuelva `self.esqueleto(cripta_id)`. Las pruebas de la capacidad 001 (`test_terreno_costos.py`, `test_cazador.py`, `test_mapa_cripta.py`) deben seguir pasando. (FR-301; contrato de `contracts/interfaz-clientes.md`)
- [ ] T015 [US1] En `adaptadores/servicioCripta.py` agregar `ubicacion_llaves(cripta_id) -> UbicacionLlavesDTO`, con los campos `_llaves_id` y `_llaves` para memorizar por sesión, como `_datos_id`/`_datos`:
  1. Si ya está memorizada para esa cripta, la devuelve.
  2. `solo_guardadas = self.presupuesto_solicitudes(cripta_id) - self.solicitudes_realizadas < 1`.
  3. `crudas = self.cliente.obtener_llaves(cripta_id, solo_guardadas)`.
  4. Arma `existe` desde `_cargar_esqueleto` y `contenido_guardado` con `getattr(self.cliente, "contenido_en_disco", None)`; si no existe, una función que devuelve `None`.
  5. `validar_llaves(...)`, construye `UbicacionLlavesDTO(cripta_id, self.version_cripta(cripta_id), ids, salas, enemigos)`, memoriza y devuelve.

  Debe hacer pasar T012 y T013 (b) y (d). (FR-301, FR-302, FR-303, FR-304)
- [ ] T016 [US1] En `adaptadores/servicioCripta.py`, dentro de `ubicacion_llaves`, convertir `ErrorOffline`, `ErrorSinConexion`, `RuntimeError` del HTTP y `LlavesInvalidas` en `LlavesNoDisponibles(f"No se pudieron obtener las llaves de la cripta {cripta_id}: {motivo}. La verificación de resolubilidad no está disponible.")`. `LlavesNoDisponibles` se deja pasar tal cual. Tras un fallo **no** se memoriza nada. Debe hacer pasar T013 (c). (FR-309, FR-310)
- [ ] T017 [US1] En `Logica/EstadoJuegoLogica.py`, en `iniciarJuego`, justo después de `cantSalas = self.comunicacion.total_salas(cripta)`, agregar `self.llaves = self.comunicacion.ubicacion_llaves(cripta)` y `self.avisoLlaves = None` dentro de un `try`. Con `except LlavesNoDisponibles as error`, poner `self.llaves = None` y `self.avisoLlaves = str(error)`; la partida sigue. Si la fuente no tiene `ubicacion_llaves` (se busca con `getattr`, como `obtener_mapa`), `llaves = None` sin aviso. No agregar nada al `logEventos` ni al estado guardado. (FR-301, FR-313, II, IV)

**Punto de control**: `python -m unittest test_llaves_clientes test_llaves_presupuesto` pasa y la suite de la línea base sigue igual.

---

## Fase 4: Historia 2 — Reutilizar las llaves guardadas mientras la versión coincida (P1)

**Objetivo**: con la misma versión no se vuelve a consultar; con otra versión, o con datos de la Parte I, se consulta una vez y se guarda, sin borrar archivos a mano.

**Prueba independiente**: dos ejecuciones seguidas con `nueva_ejecucion(carpeta, version_cripta="c1")` y una tercera con `"c2"`, contando `veces("llaves")` en cada una.

### Pruebas de la Historia 2 (escribir primero; deben fallar donde falte código)

- [ ] T018 [US2] Crear `test_llaves_version.py`:
  - **(a)** H2-1: la segunda ejecución con `c1` no hace `("llaves", …)` y la lista es igual a la de la primera.
  - **(b)** H2-2: con `c2` se hace exactamente una consulta, `AlmacenDisco.version_cripta == "c2"` y `leer_llaves` tiene la lista nueva. Configurar `HttpConfigurable` con llaves distintas en `c2` para distinguirlas.
  - **(c)** H2-3: un `cripta_<id>.bin` con la forma de la Parte I (`version`, `datos`, `salas` y contenido, **sin** `llaves`), creado con `AlmacenDisco` en una carpeta temporal, se consulta una vez y después tiene `llaves`. La prueba no borra ni edita archivos a mano.
  - **(d)** Principio III: la lista reutilizada (de disco o memorizada) es igual a una consulta desde cero sobre una carpeta vacía con la misma versión.

  (FR-305, FR-306, FR-307, FR-308, III)

### Implementación de la Historia 2

- [ ] T019 [US2] Ejecutar `test_llaves_version.py`. Si (b) o (c) fallan, corregir **solo** `adaptadores/cliente_persistente.py` (`obtener_llaves`, `_asegurar_cripta`) o `adaptadores/AlmacenDisco.py` sin tocar `_validar`. Si la decisión A de research.md §4 resultara insuficiente, documentarlo antes de cambiarla. (FR-306, FR-307, FR-308, VI)

**Punto de control**: `python -m unittest test_llaves_version` pasa.

---

## Fase 5: Historia 3 — Fallos claros del servicio y del modo sin red (P1)

**Objetivo**: los fallos del servicio, las respuestas inválidas y la falta de llaves en `--offline` muestran un mensaje que nombra la cripta. La partida continúa y nada inválido se guarda.

**Prueba independiente**: `HttpConfigurable(fallo_llaves="sin_respuesta" | "invalida")`, una respuesta con una sala inexistente, y `--offline` sobre una caché sin llaves.

### Pruebas de la Historia 3 (escribir primero; deben fallar donde falte código)

- [ ] T020 [US3] Crear `test_llaves_fallos.py`:
  - **(a)** H3-1: con `fallo_llaves="sin_respuesta"`, `ubicacion_llaves` lanza `LlavesNoDisponibles`, el mensaje contiene el id de la cripta y `leer_llaves` sigue en `None`.
  - **(b)** H3-2: con una sala inexistente, con una entrada idéntica repetida y con un enemigo ausente del contenido **guardado** (precargar esa sala antes), el resultado es `LlavesNoDisponibles` y no se guarda nada.
  - **(c)** H3-3 / FR-313: `EstadoJuegoLogica.iniciarJuego` sobre `crear_servicio(offline=True, carpeta=…)` con una cripta guardada sin llaves termina sin excepción, con `llaves is None`, `avisoLlaves` con el id de la cripta y `solicitudes_realizadas == 0`.
  - **(d)** H3-4: lo mismo con llaves guardadas da `llaves` no `None` y 0 solicitudes.
  - **(e)** Tras un fallo, una segunda llamada en la misma sesión vuelve a intentar: no se memorizó el fallo.

  (FR-309, FR-310, FR-311, FR-312, FR-313)

### Implementación de la Historia 3

- [ ] T021 [US3] En `Servicio/EstadoJuegoServicio.py` agregar `avisoLlaves(self) -> str | None`, que devuelve el `avisoLlaves` de la lógica, o `None` si no hay partida. En `Controlador/ControladorJuego.py`, justo después de iniciar una partida nueva, si `avisoLlaves()` no es `None`, imprimirlo con el formato de `_mostrar_advertencias_nuevas`. No mostrarlo en `--replay`, que no crea la vista. (FR-309, FR-312, FR-313, IV)
- [ ] T022 [US3] Ejecutar `test_llaves_fallos.py` y corregir lo que falle en `adaptadores/servicioCripta.py` (T016) o en `Logica/EstadoJuegoLogica.py` (T017), sin capturar excepciones más amplias de lo necesario. Comprobar a mano, con `python main.py --offline` sobre una carpeta de prueba sin llaves armada por un laboratorio, que el aviso aparece y que la partida se juega. (FR-312, FR-313)

**Punto de control**: `python -m unittest test_llaves_fallos` pasa. Las historias 1 a 3 (todas P1) funcionan juntas.

---

## Fase 6: Historia 4 — Leer solo de disco, sin gastar solicitudes (P2)

**Objetivo**: una fuente que lee solo de disco, falla con un mensaje claro si falta un dato o la versión no coincide, y nunca escribe ni pide nada.

**Prueba independiente**: una carpeta con la cripta guardada salvo el contenido de una sala, un `HttpFalso` espía y comparación de bytes del archivo antes y después.

### Pruebas de la Historia 4 (escribir primero; deben fallar)

- [ ] T023 [P] [US4] Crear `test_fuente_solo_local.py`:
  - **(a)** H4-1: falta `contenido:5` y `construir_sala(cid, 5)` lanza `DatoLocalFaltante`, cuyo mensaje contiene «sala 5» y el id de la cripta.
  - **(b)** H4-2: con la caché completa, `esqueleto`, `construir_sala`, `ubicacion_llaves`, `crear_jugador` y `total_salas` dan lo mismo que la vía normal (`ServicioCripta` sobre el persistente) con la misma carpeta.
  - **(c)** H4-3: con `version_vigente` distinta de la guardada, cualquier operación lanza `DatoLocalFaltante` que nombra las dos versiones.
  - **(d)** En todos los casos, el `HttpFalso` espía tiene `llamadas == []` y los bytes de `cripta_<id>.bin` no cambiaron.
  - **(e)** `precargar_vecinas` devuelve 0.

  (FR-314, FR-315, FR-316, FR-317, SC-003)

### Implementación de la Historia 4

- [ ] T024 [US4] Crear `adaptadores/fuente_solo_local.py` con `FuenteSoloLocal(fuente, almacen, version_vigente)`:
  - Antes de cada operación compara `almacen.version_cripta(cripta_id)` con `version_vigente`. Si son distintas, o si la guardada es `None`, lanza `DatoLocalFaltante`.
  - Delega en `fuente` y convierte `ErrorOffline` y `LlavesNoDisponibles` en `DatoLocalFaltante` con el dato y la cripta.
  - `precargar_vecinas` devuelve 0. **Nunca** llama a `validar_cripta` ni a ningún `guardar_*`.
  - Expone las operaciones listadas en data-model.md y `reporte()` con 0 solicitudes.

  (FR-314, FR-315, FR-316, FR-317)
- [ ] T025 [US4] En `adaptadores/fabrica.py` agregar `crear_fuente_solo_local(carpeta: str = CARPETA_DATOS, version_vigente: str | None = None) -> FuenteSoloLocal`. Arma `ServicioCripta(ClienteOffline(AlmacenDisco(carpeta)), CacheLRU(TAMANO_CACHE))` y lo envuelve. Si `version_vigente` es `None`, usa la versión guardada. No toca `_cliente_compartido`. Agregar un caso a `tests_labs/prueba_fabrica.py`. Debe hacer pasar T023. (FR-314)

**Punto de control**: `python -m unittest test_fuente_solo_local` pasa.

---

## Fase 7: Historia 5 — Probar sin red con la API falsa v2 (P2)

**Objetivo**: una cripta de referencia v2 y una situación reproducible por cada caso del Apéndice B, deterministas y sin red.

**Prueba independiente**: construir dos veces cada cripta y comparar respuestas; `requests.get` sustituido para fallar si se llama.

### Pruebas de la Historia 5 (escribir primero; deben fallar)

- [ ] T026 [P] [US5] Crear `test_api_falsa_v2.py`:
  - **(a)** H5-1: dos instancias de `cripta_v2(semilla=0)` dan respuestas idénticas en `obtener_salas`, `obtener_contenido`, `obtener_catalogo` y `obtener_llaves`. Con otra semilla cambia al menos una.
  - **(b)** H5-2: `cripta_v2` tiene al menos una salida con `costo != 100`, una ficha con `comportamiento == "cazador"` y `rango`, una llave sin enemigo, una con enemigo y una llave en dos salas. La llave de salida (`llave_salida` de los datos generales) la suelta el cazador.
  - **(c)** H5-3: `CASOS_APENDICE_B` tiene exactamente los 23 códigos B-T1…B-T7, B-N1…B-N6, B-R1…B-R4 y B-L1…B-L6, sin repetidos, y cada constructor devuelve una cripta jugable con `crear_servicio(cliente_http=…)`.
  - **(d)** H5-4: `fallo_llaves` produce el mismo fallo en dos llamadas seguidas.
  - **(e)** Todo el archivo corre con `requests.get` sustituido por una función que lanza `AssertionError`.

  (FR-318, FR-319, FR-320, FR-321)

### Implementación de la Historia 5

- [ ] T027 [US5] En `tests_labs/api_falsa.py` agregar `cripta_v2(semilla: int = 0) -> HttpConfigurable`:
  - `esqueleto_rejilla(5, 5, semilla, costo_max=9)` de `tests_labs/cripta_sintetica.py` y `ficha_cazador(rango=600)` en la sala más lejana de la 1 por número de salidas.
  - `llave_salida` soltada por el cazador (`enemigo` igual a su instancia, `sala` igual a su sala inicial).
  - Una llave en el suelo y otra llave con el mismo id en dos salas distintas.
  - Si hace falta, `HttpConfigurable` acepta `llave_salida` y `objetos` por sala para que el contenido sea coherente con `/llaves`.

  Todo derivado de `random.Random(semilla)`. (FR-318, FR-319)
- [ ] T028 [P] [US5] En `tests_labs/api_falsa.py` agregar a `CASOS_APENDICE_B` las 7 entradas **B-T1 a B-T7** de `contracts/api-falsa-v2.md`. Cada una es `(código, descripción literal de la tabla, constructor)` y el constructor devuelve `(HttpConfigurable, guion)`, con `guion` una lista de `("mover", dirección)` o `("esperar", veces)` como en `tests_labs/escenarios_terreno.py`. Para B-T5, el guion cierra la puerta entre dos turnos; para B-T7, cambia la velocidad durante el cruce. Reutilizar los esqueletos de `tests_labs/escenarios_terreno.py` cuando ya exista uno equivalente. (FR-320)
- [ ] T029 [P] [US5] En `tests_labs/api_falsa.py` agregar las 6 entradas **B-N1 a B-N6**. Cada constructor da la cripta y un guion con la situación (sala no explorada, puerta recordada abierta pero cerrada, sala con enemigos dormidos, antorcha, pergamino tras entrar con antorcha, pergamino durante un viaje). Las acciones que dependen de la capacidad 002 (`ir a`, antorcha) se escriben como pasos del guion con nombre (`("ir_a", sala)`); esta capacidad no las ejecuta. (FR-320)
- [ ] T030 [P] [US5] En `tests_labs/api_falsa.py` agregar las 4 entradas **B-R1 a B-R4**:
  - B-R1: `llave_salida` detrás de la única puerta que abre.
  - B-R2: la llave en el `suelta` de un enemigo errante, con `/llaves` que la ubica en la sala inicial del enemigo.
  - B-R3: dos órdenes válidos de obtención.
  - B-R4: una cripta no resoluble.

  `/llaves` debe ser coherente con el contenido. (FR-320)
- [ ] T031 [P] [US5] En `tests_labs/api_falsa.py` agregar las 6 entradas **B-L1 a B-L6**, con guiones que generan eventos simultáneos, uso de pergamino y una partida corta. Para B-L6, el constructor apunta a un archivo de partida de formato de la Parte I generado con el codec actual en una carpeta temporal. (FR-320)
- [ ] T032 [US5] Ejecutar `test_api_falsa_v2.py` y corregir hasta que pase. Comprobar que las pruebas de la Parte I y de la 001 que usan `HttpFalso`/`HttpConfigurable` siguen igual que en la línea base (T002). (FR-318 a FR-321)

**Punto de control**: `python -m unittest test_api_falsa_v2` pasa. Los dueños de 001 a 004 pueden usar `CASOS_APENDICE_B` en sus escenarios.

---

## Fase 8: Historia 6 — Medir el costo de red de los cazadores y la regla de precarga (P3)

**Objetivo**: medir las solicitudes extra que provoca un cazador y comparar la precarga por saltos con la precarga por costo. Medir también las alternativas de guardado y de detección de repetidos, y documentar todo sin cambiar la precarga.

**Prueba independiente**: `python main.py --bench llaves` termina con código 0 y `mediciones.md` contiene las tablas y la recomendación.

- [ ] T033 [US6] Crear `bench/llaves.py` con las alternativas descartadas, que existen **solo** aquí:
  - **(a)** `ServicioPrecargaPorCosto(ServicioCripta)`, que sobrescribe solo el orden con que `precargar_vecinas` llena el lote: el mismo límite de 10, las mismas indispensables y luego las salas faltantes por costo de ruta creciente desde la sala actual (`CampoDeCostos` o `MonticuloMinimo` sobre `esqueleto()`), con desempate por menor id.
  - **(b)** Guardado B: `llaves_<id>.bin` con su propia clave `version`, sobre `ArchivoIndexado`.
  - **(c)** Detección de repetidos comparando todas las parejas, O(k²).

  Sin `deque` ni `collections`. (FR-323, VII)
- [ ] T034 [US6] En `bench/llaves.py` implementar las secciones A a D de `contracts/bench-llaves.md`, con `bench/medicion.py`, la semilla de `bench/datos.py` y carpetas temporales:
  - **A**: lados 10, 20 y 40; 1, 4 y 16 cazadores de rango 600 a 4 o más salidas del jugador; guion fijo de 60 movimientos por salidas abiertas; reglas `saltos` y `costo` sobre las mismas criptas, semillas y guion; promedio de 5 semillas. Las solicitudes «disparadas por un enemigo» se cuentan envolviendo `EstadoJuegoLogica.ingresarEnSala` dentro del bench, sin modificar el juego.
  - **B**: 50, 500 y 5 000 salas con contenido; guardar y leer con la opción A frente a la B.
  - **C**: k = 10, 100 y 1 000; ordenar frente a todas las parejas, con verificación previa de que dan el mismo resultado.
  - **D**: la primera partida, la segunda con la misma versión y `--offline` deben dar exactamente 1, 0 y 0 `("llaves", …)`.

  (FR-322, FR-323, SC-001, SC-002, VII)
- [ ] T035 [US6] Registrar el bloque `llaves` en `BLOQUES` de `bench/__init__.py` (incluido en `--bench` sin argumentos) y mencionarlo en la ayuda de `--bench` en `main.py`. El código de salida es distinto de 0 si la sección D no da 1/0/0, si C no coincide en la verificación previa o si la opción A de B supera los 50 ms con 5 000 salas. A y los tiempos de C solo informan. (FR-322, SC-001, SC-002, VII)
- [ ] T036 [US6] Ejecutar `python main.py --bench llaves`. Crear `specs/009-contrato-datos-v2/mediciones.md` con la salida completa, una tabla «elegida frente a descartada, qué se midió, conclusión» para A, B y C, y la **recomendación** sobre la precarga (mantener por saltos o abrir una especificación aparte para pasar a costo). **No** modificar `precargar_vecinas` ni `salas_vecinas`. (FR-322, FR-323, FR-324)
- [ ] T037 [US6] **Revisar las decisiones con lo medido.**
  - Si B supera el límite, cambiar a la opción B de research.md §4 en `adaptadores/AlmacenDisco.py` y `adaptadores/cliente_persistente.py`, y documentar el antes y el después en `mediciones.md` y en `DECISIONES.md`.
  - Si C muestra que todas las parejas gana con claridad para k ≤ 1 000, cambiar `adaptadores/llaves.py` y documentarlo.
  - Si nada cambia, anotar «las decisiones se mantienen».

  (VII, X)

**Punto de control**: `--bench llaves` termina con 0. `mediciones.md` contiene la recomendación y la precarga no cambió.

---

## Fase 9: Cierre y transversales

- [ ] T038 [P] Completar la matriz de trazabilidad de `specs/009-contrato-datos-v2/quickstart.md` con los nombres reales de las pruebas (`clase.método`). Comprobar que ningún FR-301 a FR-324 queda sin prueba o medición y que cada escenario H1-1 a H6-2 tiene al menos una. (IX)
- [ ] T039 [P] Actualizar `DOCUMENTACION_API.md`:
  - `obtener_llaves` en la tabla de métodos del cliente (§3) y `ubicacion_llaves`/`esqueleto` en la del servicio.
  - La clave `llaves` en el esquema del archivo de cripta (§7).
  - En la tabla de solicitudes (§8), la primera vez pasa de 6 a 7.
  - La sección de la fuente solo local.

  (VI)
- [ ] T040 [P] Agregar la sección 009 a `DECISIONES.md` con enlaces a `spec.md` y `plan.md`, e indicar si cada decisión (guardado A, validación ordenando, `solo_guardadas`, fuente solo local) coincide con el plan y qué medición lo respalda. (X)
- [ ] T041 [P] Registrar en `PROMPTS_LLM.md` los comandos `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks` y `/speckit-implement` de esta capacidad con texto propio, con herramienta y modelo. (XI)
- [ ] T042 [P] Actualizar `README.md` con una línea sobre la capacidad 009, `python main.py --bench llaves` y la consulta de llaves en el conteo de solicitudes. (VII)
- [ ] T043 Comprobar con búsqueda que `adaptadores/llaves.py`, `adaptadores/fuente_solo_local.py`, `DTO/LlavesDTO.py`, `bench/llaves.py` y los cambios en los clientes, `AlmacenDisco`, `servicioCripta.py` y `EstadoJuegoLogica.py`:
  - No importan `heapq`, `bisect`, `collections` ni `networkx`.
  - No usan `dict`/`set` como índice ni `sorted()`/`list.sort()`.
  - No contienen ids de llaves, salas, enemigos ni presupuestos de una cripta concreta.
  - No agregan usos de `deque`.

  Comprobar que `Logica/` no importa nada de `adaptadores/`. (I, IV, V)
- [ ] T044 Ejecutar todas las pruebas (`python -m unittest discover -p "test_*.py"`), los laboratorios de la línea base (T002) y `python main.py --bench`. Comparar con la línea base y registrar cualquier fallo sin ocultarlo. (IX)
- [ ] T045 Comparar `spec.md` con el programa entregado y corregir cualquier desajuste primero en la especificación, en un commit aparte del código. (X)

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1** primero. T001 y T002 son paralelas.
- **Fase 2** depende de la Fase 1 y bloquea todas las historias:
  - T003, T004, T005, T007 y T008 son paralelas.
  - T006 depende de T004 y T005 (la prueba va primero).
  - T009 depende de T003 y T006.
  - T010 depende de T007 y T009.
  - T011 depende de T006, T007 y T009.
- **Fase 3 (US1, MVP)** depende de la Fase 2. T012 y T013 en paralelo; T014 → T015 → T016 → T017 (mismo archivo hasta T016).
- **Fase 4 (US2)** depende de la Fase 3 (usa `ubicacion_llaves`).
- **Fase 5 (US3)** depende de la Fase 3 (T016 y T017). Puede ir en paralelo con la Fase 4.
- **Fase 6 (US4)** depende de la Fase 3 (T015, para `ubicacion_llaves` sobre el offline). Es independiente de las Fases 4 y 5.
- **Fase 7 (US5)** depende de la Fase 2 (T008). T027 a T031 tocan el mismo archivo, `tests_labs/api_falsa.py`: si se hacen en paralelo, cada uno agrega su bloque en una sección distinta y se integran al final. B-R* y la prueba (c) de T026 necesitan `crear_servicio` con llaves (Fase 3).
- **Fase 8 (US6)** depende de la Fase 3 (sección D) y de T027 (criptas con cazador). Es independiente de las Fases 4 a 7 en lo demás.
- **Fase 9** al final.

### Dentro de cada historia

Primero la prueba, que debe fallar; luego la implementación; al final el punto de control. No se pasa a la siguiente historia con su punto de control en rojo.

### Oportunidades de paralelismo

- Fase 2: T003, T004, T005, T007 y T008 a la vez (cinco archivos distintos).
- Fase 3: T012 y T013 a la vez.
- Después de la Fase 3: US2, US3, US4 y US5 pueden repartirse entre integrantes.
- Fase 7: T028 a T031, por familia de casos (los dueños de 001, 002, 003 y 004 pueden escribir los suyos).
- Fase 9: T038 a T042 a la vez.

### Ejemplo: Fase 2 en paralelo

```text
T003 Logica/FuenteCripta.py       (errores y Protocol)
T004 DTO/LlavesDTO.py             (UbicacionLlavesDTO)
T005 test_llaves_validacion.py    (prueba que falla)
T007 adaptadores/AlmacenDisco.py  (guardar_llaves / leer_llaves)
T008 tests_labs/api_falsa.py      (obtener_llaves, fallo_llaves)
```

### Ejemplo: después del MVP

```text
Integrante A: Fase 4 (T018–T019)  versión y Parte I
Integrante B: Fase 5 (T020–T022)  fallos y aviso
Integrante C: Fase 6 (T023–T025)  fuente solo local
Integrante D: Fase 7 (T026–T032)  API falsa v2 y Apéndice B
```

---

## Estrategia de implementación

1. **MVP (Fases 1 a 3)**: el juego obtiene las llaves con una sola solicitud, contada en el presupuesto, y la capacidad 003 ya puede leerlas. Hay que validar con `test_llaves_clientes` y `test_llaves_presupuesto` antes de seguir.
2. **Completar las P1 (Fases 4 y 5)**: reutilización por versión y fallos claros. Con esto, la consulta queda lista para producción.
3. **P2 (Fases 6 y 7)**: la fuente solo local, que desbloquea la capacidad 004, y la API falsa v2 con el Apéndice B, que desbloquea las pruebas de 001 a 004.
4. **P3 (Fase 8)**: la medición y la recomendación sobre la precarga.
5. **Cierre (Fase 9)**.

Cada incremento se confirma por separado. La especificación y el plan ya están confirmados antes del primer commit de código (principio X).

---

## Cobertura de requisitos

| Requisito | Tareas |
|---|---|
| FR-301 | T009, T011, T013, T015, T017 |
| FR-302 | T004, T005, T006, T012, T015 |
| FR-303 | T010, T012, T015 |
| FR-304 | T009, T012, T013, T015 |
| FR-305 | T007, T011, T018 |
| FR-306 | T011, T018, T019 |
| FR-307 | T007, T018, T019 |
| FR-308 | T018, T019 |
| FR-309 | T003, T009, T013, T016, T020, T021 |
| FR-310 | T006, T011, T016, T020 |
| FR-311 | T005, T006, T020 |
| FR-312 | T010, T020, T021, T022 |
| FR-313 | T003, T017, T020, T021, T022 |
| FR-314 | T023, T024, T025 |
| FR-315 | T003, T023, T024 |
| FR-316 | T023, T024 |
| FR-317 | T023, T024 |
| FR-318 | T008, T026, T027, T032 |
| FR-319 | T026, T027 |
| FR-320 | T026, T028, T029, T030, T031 |
| FR-321 | T008, T026 |
| FR-322 | T034, T035, T036 |
| FR-323 | T033, T034, T036 |
| FR-324 | T036 |
| SC-001, SC-002 | T034, T035 |
| SC-003 | T023 |
| SC-005 | T013 |
