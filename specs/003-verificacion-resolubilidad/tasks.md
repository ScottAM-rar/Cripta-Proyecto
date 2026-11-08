# Tareas: Verificación de resolubilidad

**Entrada**: documentos de diseño en `specs/003-verificacion-resolubilidad/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Prerrequisitos**: `spec.md` con las 6 clarificaciones de la sesión 2026-11-08 (completar = llegar a la sala de salida con la llave de salida obtenible; orden por **oleadas** con desempate por menor sala y luego id; aviso de `--forzar` solo al iniciar; datos inválidos al iniciar: la partida inicia con aviso; llave en sala sin camino: bloqueo con su motivo, no ciclo). Se apoya en código existente: `Logica/MapaCripta.py`, `Logica/ColaCircular.py`, `Logica/MonticuloMinimo.py`, `Logica/ordenamiento.py` (`ordenar_adaptativo`), `Logica/RecorridoPorNiveles.py` (005), `DTO/LlavesDTO.py` y `adaptadores/fuente_solo_local.py` (009), `tests_labs/api_falsa.py` (`HttpConfigurable`, `CASOS_APENDICE_B`, `_b_r1` a `_b_r4`) y `tests_labs/cripta_sintetica.py`.

**Pruebas**: se incluyen en todos los grupos porque el principio IX exige una prueba automatizada por escenario de aceptación. Cada prueba se escribe **antes** del código que la hace pasar. En cada grupo hay una tarea que ejecuta las pruebas nuevas y registra la **evidencia roja honesta** en la sección «Evidencia en rojo» al final de este archivo, antes de implementar:

- El rojo debe ser una **falla de aserción** (o un `self.fail(...)` explícito), nunca un error de importación ni una excepción sin capturar. Para eso, las pruebas importan los módulos nuevos dentro de cada prueba o de `setUp` con `try/except ImportError: self.fail("<módulo> todavía no existe")`, y leen campos nuevos con `getattr(obj, "campo", "<sin campo>")`.
- Si una prueba pasa a la primera porque el código ya existe (por ejemplo, una garantía de regresión), se anota **qué aserción fallaría** y con qué cambio del código. Nunca se inventa un rojo.

**Organización**: grupos con letra (A a I), en el orden pedido. Las tareas de una historia de `spec.md` llevan su etiqueta `[USn]`; las de los grupos de fundamentos (A, B, C) y de cierre (I) no. Entre paréntesis, los requisitos, casos del Apéndice B o principios que atiende cada tarea, y el criterio de terminado.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias de tareas incompletas).
- **[USn]**: historia de `spec.md`: US1 saber si la cripta se puede completar, US2 llaves que suelta un enemigo, US3 orden siempre igual, US4 inicio de partida y `--forzar`, US5 errores claros, US6 rendimiento.
- Las rutas son relativas a la raíz del repositorio. Las pruebas usan `unittest` (`test_*.py` en la raíz).

## Reglas para todas las tareas (constitución y entrada)

- **No usar** `dict` ni `set` como índice, caché o tabla de búsqueda; ni `heapq`, `bisect`, `collections`, `networkx` ni bibliotecas de grafos; ni `sorted()` ni `.sort()`. Para ordenar: `ordenar_adaptativo` (`Logica/ordenamiento.py`). Para la cola: `ColaCircular`. Para el montículo: `MonticuloMinimo` (sin modificarlo). Vale también para `tests_labs/` y `bench/`. (I)
- `Logica/` y `DTO/` **no importan** `adaptadores/`, `Servicio/` ni `Controlador/`. Los fallos de datos se capturan por `LlavesNoDisponibles`, `DatoLocalFaltante` (contrato del modelo) y las clases base `RuntimeError`/`OSError`. (IV)
- **No se modifican** `adaptadores/AlmacenPartidaBinario.py`, `DTO/EstadoGuardadoDTO.py` ni `adaptadores/codec_partida.py` (formato de guardado, capacidad 010), ni `Logica/MonticuloMinimo.py`, `Logica/ColaCircular.py`, `Logica/RecorridoPorNiveles.py`, los clientes HTTP/persistente/offline ni `AlmacenDisco`.
- Ningún id de llave, sala o enemigo ni tamaño de una cripta concreta en código de producción. (V)
- Sin solicitudes nuevas a la API: a lo sumo la consulta de llaves de la 009. (FR-341, VI)
- Todos los archivos nuevos o modificados (código y documentos) en **CRLF**.
- Los documentos `.md` se modifican en tareas **aparte** de las de código.
- **No ejecutar** `tests_labs/prueba_cliente_http.py` ni `tests_labs/prueba_servicio.py`. De `main.py` solo se ejecutan variantes de `--bench`. Esta capacidad **no** cablea `--verificar` ni `--forzar` (lo hace Fernanda).
- No hacer commits salvo donde lo indica el punto de parada del grupo B (lo hace Scott). No modificar `PROMPTS_LLM.md`.

---

## Grupo A: Preparación y cambio del mapa (bloquea todo)

**Propósito**: línea base, matriz actualizada con los escenarios del clarify, y la llave de cada puerta en el mapa ([contracts/mapa-con-llaves.md](contracts/mapa-con-llaves.md), G1 a G6). Es lo primero.

- [X] T001 [P] Revisar `plan.md`, `research.md`, `data-model.md` y este `tasks.md` contra la lista de prohibidos del principio I y las reglas de arriba, y anotar el resultado en la sección Notas de `specs/003-verificacion-resolubilidad/checklists/requirements.md`. Comprobar en especial que `IndiceLlaves`, el recorrido por oleadas, la elección de ubicación y el oráculo de `tests_labs/referencia_resolubilidad.py` no necesitan `dict`, `set`, `collections`, `sorted()` ni `.sort()`. **Terminado**: nota con fecha y «sin hallazgos» o la lista de hallazgos. (I)
- [X] T002 [P] Ejecutar `python -m unittest discover -p "test_*.py"` y `python -m tests_labs.sin_red`, y anotar la línea base (cantidad de pruebas, las que fallan y por qué) en las Notas de `specs/003-verificacion-resolubilidad/checklists/requirements.md`. No ejecutar `prueba_cliente_http` ni `prueba_servicio`. **Terminado**: línea base anotada antes de cualquier cambio de código. (IX)
- [X] T003 [P] En la matriz de trazabilidad de `specs/003-verificacion-resolubilidad/quickstart.md` agregar los escenarios del clarify con sus pruebas previstas: H1-7 en la fila FR-338 (`Bloqueos.test_fr338_h1_7_llave_en_sala_sin_camino_es_bloqueo_no_ciclo`); H4-5 en las filas FR-339 y FR-343 (`Inicio.test_fr339_h4_5_datos_invalidos_inicia_con_aviso`, `ErroresDeDatos.test_fr343_h4_5_sala_de_salida_inexistente`); el ejemplo de dos oleadas de H3-2 en la fila FR-335 (`Determinismo.test_fr335_h3_2_dos_oleadas`); comprobar que la numeración H3-1 a H3-5 de la matriz coincide con la de la spec; y **alinear los nombres de prueba que ya están en la matriz** con los de este `tasks.md` (por ejemplo, `test_fr333_cadena_de_puertas` → `test_fr333_h1_3_cadena_de_puertas`, `test_fr335_desempate_sala_y_luego_id` → `test_fr335_h3_2_dos_oleadas`, `test_fr342_http_offline_y_solo_local_dan_lo_mismo` → `test_fr342_h3_4_http_offline_y_solo_local_dan_lo_mismo`), incluidas las pruebas de casos límite de T038. Solo el documento. **Terminado**: cada escenario H1-1 a H6-2 de `spec.md` aparece en al menos una fila. (IX)
- [X] T004 Crear `test_mapa_con_llaves.py`, clase `MapaConLlaves`, una prueba por garantía de `contracts/mapa-con-llaves.md`, leyendo el campo con `getattr(arista, "llave", "<sin campo>")`:
  - `test_fr333_g1_esqueleto_copia_la_llave`: con el `HttpConfigurable` de `_b_r3` (de `CASOS_APENDICE_B`) y un `ServicioCripta`, `esqueleto()` da `itm_llave_a` en las salidas 1→4 y 4→1, `itm_llave_b` en 4→5 y 5→4, y `None` en 1→2 y 1→3.
  - `test_fr333_g2_mapa_cripta_copia_la_llave`: lo mismo leyendo `MapaCripta(...).salidas(n)`.
  - `test_fr342_g3_offline_igual_que_con_red`: guardar con `ClientePersistente` sobre ese `HttpConfigurable` en una carpeta temporal y leer con `ClienteOffline`; las ternas `(origen, dirección, llave)` coinciden.
  - `test_fr342_g4_fuente_solo_local_igual_sin_solicitudes`: `FuenteSoloLocal.esqueleto()` da las mismas ternas y el contador de solicitudes no cambia.
  - `test_g5_construccion_sin_llave_sigue_funcionando`: `AristaMapaDTO` con 4 argumentos y `AristaCripta` con 5 posicionales dan `llave is None`; con `llave="x"` por nombre, el campo vale `"x"` (envolver la construcción en `try/except TypeError: self.fail(...)`).
  - `test_fr341_g6_sin_solicitudes_nuevas`: `obtener_salas` se llama **exactamente una vez** y la lista de llamadas del `HttpConfigurable` es la misma que anotó la línea base de T002 para el mismo recorrido (ninguna llamada nueva).

  **Terminado**: el archivo existe y corre sin errores de importación. (FR-333, FR-341, FR-342)
- [X] T005 Ejecutar `python -m unittest test_mapa_con_llaves` y registrar en «Evidencia en rojo» la salida resumida. Se espera: G1 a G4 fallan por aserción (`'<sin campo>' != 'itm_llave_a'`), G5 falla por `self.fail` (el constructor no acepta `llave`). G6 probablemente pasa a la primera: anotar que es una garantía de regresión y que fallaría si `esqueleto()` hiciera una segunda llamada a `obtener_salas`. **Terminado**: evidencia anotada, sin inventar rojos. (IX)
- [X] T006 [P] En `DTO/MapaDTO.py` agregar a `AristaMapaDTO` el campo `llave: str | None = None` **al final** y actualizar el docstring: «Id de catálogo de la llave que abre la puerta de esta salida, tal como lo publica la API en la salida (`"llave"`). `None` si la API no lo trae». (FR-333)
- [X] T007 [P] En `Logica/MapaCripta.py`: `AristaCripta.__slots__` pasa a `("origen", "direccion", "destino", "costo", "cerrada_inicial", "llave")`; el constructor recibe `llave: str | None = None` al final; `MapaCripta.__init__` pasa `a.llave`. Nada más cambia (`version_puertas`, `esta_abierta`, salientes, entrantes). (FR-333)
- [X] T008 En `adaptadores/servicioCripta.py`, `esqueleto()`: pasar `llave=datos.get("llave")` al construir cada `AristaMapaDTO`. Sin otros cambios y sin usos nuevos de `deque`. (FR-333)
- [X] T009 Ejecutar `python -m unittest test_mapa_con_llaves` y la suite de la línea base. **Terminado**: las 6 pruebas pasan; la suite queda igual que en T002. Si G3 o G4 fallaran (la llave no llega por `--offline` o por la lectura solo local), corregir solo en `adaptadores/servicioCripta.py` o `adaptadores/fuente_solo_local.py` (como T041) y anotarlo en Notas del checklist para actualizar `research.md` §1 en el grupo I. Si la llave se pierde en otro lado (clientes HTTP, persistente u offline, o `AlmacenDisco`), **detenerse y consultar a Scott** sin modificar esos archivos. (FR-333, FR-342)

**Punto de control**: el mapa conoce la llave de cada puerta por las tres fuentes y nada anterior se rompió.

---

## Grupo B: Entrega temprana para Fernanda (bloquea C a I)

**Propósito**: fijar firmas, DTO y operaciones con cuerpo provisional que devuelve código 2 ([contracts/interfaz-verificacion.md](contracts/interfaz-verificacion.md), [research.md §12](research.md)), para que Fernanda conecte `--verificar` y `--forzar` mientras se implementa el algoritmo.

- [ ] T010 Crear `test_resolubilidad_reporte.py` con la clase `Contrato` (importaciones dentro de cada prueba con `try/except ImportError: self.fail(...)`):
  - `test_fr344_firmas_de_la_interfaz`: con `inspect.signature`, comprobar `verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id="")`, `verificar(fuente, cripta_id, llaves=None)`, `EstadoJuegoServicio.verificar(self, cripta_id, offline=None)`, `EstadoJuegoServicio.iniciarJuego(..., forzar=False)`, `EstadoJuegoLogica.iniciarJuego(self, cripta, semilla=None, pedir_llaves=True, forzar=False)`, `EstadoJuegoServicio.avisoResolubilidad(self)`, `lineas_reporte(resultado)` y `aviso_forzado(resultado)`.
  - `test_fr331_codigo_salida`: `ResultadoVerificacion(..., resoluble=True/False/None)` da 0 / 1 / 2.
  - `test_fr344_campos_del_resultado`: `ResultadoVerificacion` tiene `cripta_id`, `resoluble`, `orden`, `salas_alcanzables`, `salas_no_alcanzables`, `bloqueos`, `causas`, `llave_salida`, `sala_salida`, `motivo_error`; `PasoLlaveDTO` tiene `llave`, `sala`, `enemigo`; `BloqueoDTO` tiene `sala_origen`, `direccion`, `sala_destino`, `llave`, `salas_de_la_llave`, `tipo`; las listas por defecto están vacías y no se comparten entre instancias.
  - `test_fr339_cripta_no_resoluble_es_runtime_error`: `CriptaNoResoluble` hereda de `RuntimeError` y guarda `resultado`.
  - `test_fr344_fuente_entrega_sala_inicial_y_llave_salida`: con `HttpFalso`, `ServicioCripta.obtener_sala_inicial("cripta-01") == 1` y `obtener_llave_salida(...) == "itm_llave_negra"`; con `FuenteSoloLocal` sobre la misma cripta guardada, los mismos valores y 0 solicitudes; `FuenteCripta` declara ambos métodos.
  - `test_fr343_cuerpo_provisional_devuelve_codigo_2`: `verificar(...)` devuelve `resoluble is None`, `motivo_error == "La verificación de resolubilidad todavía no está implementada."` y `codigo_salida() == 2`; `lineas_reporte` de ese resultado da las dos líneas del caso de error de `contracts/reporte-verificacion.md`. (Esta prueba se **reemplaza** en el grupo D, T032, cuando el cuerpo deja de ser provisional; anotarlo en el docstring.)

  **Terminado**: el archivo corre sin errores de importación. (FR-331, FR-339, FR-343, FR-344)
- [ ] T011 Ejecutar `python -m unittest test_resolubilidad_reporte` y registrar la evidencia roja: todas fallan por `self.fail` («todavía no existe») o por aserción. **Terminado**: evidencia anotada. (IX)
- [ ] T012 [P] Crear `DTO/ResultadoVerificacionDTO.py` (sin importar `Logica/` ni `adaptadores/`), según [data-model.md §3](data-model.md):
  - Constantes de tipo de bloqueo `SIN_LLAVE`, `LLAVE_INEXISTENTE`, `CICLO`, `LLAVE_SIN_CAMINO` y de causas `LLAVE_SALIDA_INEXISTENTE`, `SALIDA_SIN_CAMINO`, `SALIDA_BLOQUEADA`, `LLAVE_SALIDA_INALCANZABLE`, más la tupla `CAUSAS_EN_ORDEN` en ese orden fijo.
  - `@dataclass PasoLlaveDTO(llave: str, sala: int, enemigo: str | None = None)`.
  - `@dataclass BloqueoDTO(sala_origen: int, direccion: str, sala_destino: int, llave: str | None, salas_de_la_llave: list[int], tipo: str)`.
  - `@dataclass ResultadoVerificacion(cripta_id: str, resoluble: bool | None, orden, salas_alcanzables, salas_no_alcanzables: int = 0, bloqueos, causas, llave_salida: str | None = None, sala_salida: int | None = None, motivo_error: str | None = None)`, con las listas en `field(default_factory=list)`.
  - `codigo_salida()`: «0 si `resoluble is True`, 1 si `resoluble is False`, 2 si `resoluble is None`».
  - Docstring con las invariantes literales: «`resoluble is None` ⇔ `motivo_error is not None`»; «`resoluble is True` ⇒ la llave de salida figura exactamente una vez en `orden`; `bloqueos` y `causas` vacías»; «`resoluble is False` ⇒ `orden` vacía y `causas` no vacía»; «cada id de llave aparece como máximo una vez en `orden`». (FR-331, FR-336 a FR-338, FR-343, FR-344)
- [ ] T013 [P] En `Logica/FuenteCripta.py` agregar al `Protocol` `obtener_sala_inicial(self, cripta_id: str) -> int: ...` y `obtener_llave_salida(self, cripta_id: str) -> str | None: ...`, junto a `obtener_sala_salida`. (FR-344, IV)
- [ ] T014 En `adaptadores/servicioCripta.py` agregar `obtener_sala_inicial` (`self.datos_cripta(cripta_id)["sala_inicial"]`) y `obtener_llave_salida` (`self.datos_cripta(cripta_id).get("llave_salida")`), con docstring como el de `obtener_sala_salida`. Sin solicitudes nuevas (los datos generales ya se piden una vez). (FR-341, FR-344)
- [ ] T015 En `adaptadores/fuente_solo_local.py` agregar los dos métodos con `self._leer(cripta_id, "los datos generales", lambda: self.fuente.obtener_...(cripta_id))`, como `obtener_sala_salida`. (FR-342, FR-344)
- [ ] T016 [P] Crear `Logica/VerificacionResolubilidad.py` con la **entrega provisional**:
  - `MOTIVO_PROVISIONAL = "La verificación de resolubilidad todavía no está implementada."`.
  - `class CriptaNoResoluble(RuntimeError)`: `__init__(self, resultado)` guarda `self.resultado` y usa como mensaje `"\n".join(lineas_reporte(resultado))`.
  - `verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id="") -> ResultadoVerificacion` y `verificar(fuente, cripta_id, llaves=None) -> ResultadoVerificacion`: ambas devuelven `ResultadoVerificacion(cripta_id, resoluble=None, motivo_error=MOTIVO_PROVISIONAL)`.
  - Docstring del módulo que remite a `research.md` §2 a §8. Sin importar adaptadores. (FR-343, FR-344)
- [ ] T017 [P] Crear `Logica/ReporteVerificacion.py` con `lineas_reporte(resultado) -> list[str]` y `aviso_forzado(resultado) -> str`. En esta entrega solo el caso de error (`resoluble is None`): `["Verificación de la cripta <id>: NO SE PUDO VERIFICAR.", <motivo_error>]`. Para los otros casos lanzar `NotImplementedError("se completa en el grupo E (T036)")`. (FR-330, FR-343)
- [ ] T018 En `Logica/EstadoJuegoLogica.py`: `__init__` agrega `self.resultadoVerificacion = None` y `self.avisoResolubilidad = None`; `iniciarJuego(self, cripta, semilla=None, pedir_llaves=True, forzar=False)` acepta `forzar` **sin efecto** todavía. En `Logica/EstadoGuardadoLogica.py`, la restauración pone los dos atributos en `None` (una línea cada uno, junto a `llaves` y `avisoLlaves`). No tocar `DTO/EstadoGuardadoDTO.py`. (FR-339, FR-340)
- [ ] T019 En `Servicio/EstadoJuegoServicio.py`:
  - `verificar(self, cripta_id: str, offline: bool | None = None) -> ResultadoVerificacion`: `self._asegurarServicio(offline)` y devuelve `VerificacionResolubilidad.verificar(self._estadoJuegoLogica.comunicacion, cripta_id)`; no inicia partida ni abre log.
  - `iniciarJuego(..., forzar: bool = False)`: pasa `forzar` a la lógica.
  - `avisoResolubilidad(self) -> str | None`: igual que `avisoLlaves()` (`None` si no hay partida iniciada).

  (FR-330, FR-344)
- [ ] T020 Ejecutar `python -m unittest test_resolubilidad_reporte test_mapa_con_llaves` y la suite de la línea base. **Terminado**: todas las de `Contrato` pasan y la suite sigue igual.

**🛑 Punto de parada (fin del grupo B)**: detenerse aquí. Scott avisa a Fernanda que la interfaz está lista ([contracts/interfaz-verificacion.md](contracts/interfaz-verificacion.md)) y hace un commit aparte con los grupos A y B. No seguir con el grupo C hasta que Scott lo confirme.

---

## Grupo C: Índice de llaves (bloquea D)

**Propósito**: ids de llave de texto → número denso con el orden de los ids, sin `dict` ([research.md §4](research.md)).

- [ ] T021 [P] Crear `test_indice_llaves.py`, clase `IndiceLlavesPrueba` (importación con `try/except ImportError: self.fail(...)`):
  - (a) `test_fr335_ids_quedan_en_orden_creciente`: con ids desordenados, `id_de(0..n-1)` es creciente.
  - (b) `test_fr335_repetidos_cuentan_una_vez`: `cantidad()` cuenta ids distintos.
  - (c) `test_fr335_numero_de_un_id_presente`: `numero(id) == i` si `id_de(i) == id`.
  - (d) `test_fr335_numero_de_un_id_ausente_es_menos_uno`: menor que todos, mayor que todos e intermedio.
  - (e) `test_lista_vacia`: `cantidad() == 0` y `numero("x") == -1`.
  - (f) `test_un_solo_elemento`.
  - (g) `test_prefijos_compartidos`: `itm_llave_a` e `itm_llave_ab` se distinguen.
  - (h) `test_fr335_igual_que_busqueda_lineal`: 1 000 ids generados con `random.Random(semilla)` (semillas 0 a 4); para cada id presente y 200 ausentes, `numero` coincide con una búsqueda lineal sobre `id_de`.

  (FR-335, I)
- [ ] T022 Ejecutar `python -m unittest test_indice_llaves` y registrar la evidencia roja (falla por `self.fail`: el módulo no existe). (IX)
- [ ] T023 Crear `Logica/IndiceLlaves.py`, `class IndiceLlaves`: `__init__(self, ids: list[str])` ordena con `ordenar_adaptativo` y quita repetidos comparando vecinos; `numero(id) -> int` es una **búsqueda binaria escrita a mano** (bucle con `bajo`/`alto`), −1 si no está; `id_de(numero) -> str`; `cantidad() -> int`. Docstring con costos: construir O(K log K), consultar O(log K). Sin `bisect`, `sorted()`, `.sort()`, `dict` ni `set`. (FR-335, I)
- [ ] T024 Ejecutar `python -m unittest test_indice_llaves`. **Terminado**: las 8 pruebas pasan.

**Punto de control**: índice listo y equivalente a la búsqueda lineal.

---

## Grupo D: Algoritmo de resolubilidad (US1, US2, US3) 🎯 MVP

**Objetivo**: la regla de FR-332 a FR-334, el orden por oleadas de FR-335 y FR-336, y los bloqueos de FR-337 y FR-338, con la función pura y la operación `verificar` real.

**Prueba independiente**: con la API falsa v2, `verificar` sobre los casos B-R1 a B-R4 da los resultados de [contracts/reporte-verificacion.md](contracts/reporte-verificacion.md).

### Pruebas (escribir primero; deben fallar)

- [ ] T025 [P] [US1] Crear `test_resolubilidad_regla.py`. Los mapas se arman con `esqueleto_de_conexiones`/`mapa_desde_esqueleto` (`tests_labs/cripta_sintetica.py`) y `_puerta_con_llave` (`tests_labs/api_falsa.py`); las llaves, con `UbicacionLlavesDTO` directo; se llama a `verificar_resolubilidad`.
  - Clase `Regla`: `test_fr332_h1_1_salida_alcanzable_y_llave_obtenible_es_resoluble`; `test_fr332_sala_inicial_es_salida`; `test_fr332_no_exige_puerta_hacia_la_salida` (la salida se alcanza por salidas abiertas y la llave de salida está en una sala alcanzable: resoluble); `test_fr333_h1_3_cadena_de_puertas` (orden `k1`, `k2`, `k3`, salida); `test_fr333_h1_6_respeta_salidas_de_un_solo_sentido`; `test_fr333_puerta_sin_llave_nunca_se_cruza`; `test_fr333_una_llave_abre_varias_puertas`; `test_fr334_h2_2_enemigo_tras_puerta` (obtenible si la puerta se abre y no obtenible si no); `test_fr334_h2_3_basta_una_ubicacion_alcanzable`; `test_fr336_llave_salida_en_el_orden_una_vez`.
  - Clase `Bloqueos`: `test_fr332_fr338_h1_4_salida_sin_camino` (`causas == ["SALIDA_SIN_CAMINO"]`); `test_fr332_fr338_h1_5_llave_salida_inexistente` (`"LLAVE_SALIDA_INEXISTENTE"` en `causas`); `test_fr337_salas_alcanzables_crecientes_y_cantidad_no_alcanzables`; `test_fr338_varios_bloqueos_en_orden` (por sala de origen creciente y N, S, E, O); `test_fr338_puerta_sin_llave_es_bloqueo_sin_llave`; `test_fr338_h1_7_llave_en_sala_sin_camino_es_bloqueo_no_ciclo` (tipo `LLAVE_SIN_CAMINO`); `test_fr338_ciclo_a_traves_de_otras_puertas` (la llave está detrás de dos puertas bloqueadas: tipo `CICLO`).

  (FR-332 a FR-334, FR-336 a FR-338)
- [ ] T026 [P] [US1] Crear `test_resolubilidad_apendice_b.py`, clase `CasosB`. Un ayudante busca el caso por código en `CASOS_APENDICE_B`, arma un `ServicioCripta` sobre su `HttpConfigurable` y ejecuta los pasos `("verificar",)` del guion con `verificar(servicio, cripta_id)`:
  - `test_b_r1_fr338_ciclo`: `resoluble is False`, `causas == ["SALIDA_BLOQUEADA"]`, un solo bloqueo 1 → 2 de tipo `CICLO` con `llave == "itm_llave_salida"` y `salas_de_la_llave == [2]`, `salas_alcanzables == [1]`, `salas_no_alcanzables == 1`.
  - `test_b_r2_fr334_llave_de_errante_en_su_sala_inicial`: `orden == [PasoLlaveDTO("itm_llave_salida", 3, "e-errante")]`.
  - `test_b_r3_fr335_dos_ejecuciones_mismo_orden`: las dos verificaciones del guion dan `itm_llave_a` (sala 2), `itm_llave_b` (sala 3), `itm_llave_salida` (sala 5) y resultados iguales campo por campo.
  - `test_b_r4_fr338_llave_inexistente`: bloqueo de tipo `LLAVE_INEXISTENTE` con `llave == "itm_llave_perdida"` y `salas_de_la_llave == []`.

  (B-R1, B-R2, B-R3, B-R4; FR-334, FR-335, FR-338)
- [ ] T027 [P] [US3] Crear `test_resolubilidad_determinismo.py`:
  - Clase `Determinismo`: `test_fr335_h3_2_dos_oleadas` (escenario H3-2 literal: sala inicial 5; en la primera oleada `X` en la sala 4, `B` y `A` en la sala 2; la llave `C` en la sala 3, detrás de la puerta que se abre con `A`; el orden es `A`, `B`, `X`, `C`: `C` va última aunque su sala tenga menor id que la de `X`, porque es de la oleada siguiente); `test_fr335_orden_de_la_respuesta_no_importa` (las tres listas de `UbicacionLlavesDTO` invertidas dan el mismo resultado); `test_fr335_suelo_antes_que_enemigo_y_menor_instancia` (misma llave y sala en el suelo y en un enemigo: `enemigo is None`; en dos enemigos: la menor instancia); `test_fr335_dos_ejecuciones_iguales`.
  - Clase `Equivalencia`: `test_fr335_fr346_incremental_igual_a_repetida_en_criptas_al_azar`: para las semillas 0 a 19, `cripta_al_azar_con_llaves(semilla)` (T028) y `verificar_resolubilidad` igual a `verificar_repetida` campo por campo. (III)

  (FR-335, FR-346, II, III)
- [ ] T028 [P] [US3] Crear `tests_labs/referencia_resolubilidad.py` (oráculo, como `tests_labs/referencia_recorrido.py`):
  - `verificar_repetida(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id="") -> ResultadoVerificacion`: en cada oleada recorre **desde cero** desde la sala inicial con las llaves obtenidas hasta ahora; **para igual que el algoritmo**: al final de la oleada en que la sala de salida es alcanzable y la llave de salida es obtenible (incluye las llaves de esa oleada en el orden), o cuando una oleada no agrega ninguna llave nueva (no resoluble); las llaves nuevas de la oleada se ordenan con `ordenar_adaptativo` por `(sala, id)`; bloqueos, tipos y causas calculados de forma independiente con la definición de `spec.md` (FR-338) y `research.md` §6. Costo O(K · (S + E)): es la alternativa descartada que mide el bench.
  - `cripta_al_azar_con_llaves(semilla, salas=60) -> (mapa, sala_inicial, sala_salida, llave_salida, llaves)`: `esqueleto_dirigido_aleatorio` con puertas cerradas al azar, llaves asignadas a esas puertas y ubicadas en salas al azar (algunas en enemigos, algunas inexistentes), todo con `random.Random(semilla)`.

  Sin `dict`, `set`, `sorted()` ni `.sort()`. (III, VII)
- [ ] T029 Ejecutar `python -m unittest test_resolubilidad_regla test_resolubilidad_apendice_b test_resolubilidad_determinismo` y registrar la evidencia roja: fallan por aserción porque el cuerpo provisional devuelve `resoluble is None`. Si alguna pasa a la primera (por ejemplo, una que compare dos resultados provisionales iguales), anotar qué aserción la haría fallar y reforzarla. **Terminado**: evidencia anotada. (IX)

### Implementación

- [ ] T030 [US1] En `Logica/VerificacionResolubilidad.py`, `verificar_resolubilidad` (camino resoluble), según [research.md §2 y §3](research.md) y [data-model.md §4](data-model.md):
  - Si la sala inicial o la de salida no existe en `mapa.existe`: `resoluble=None`, `motivo_error="Datos inválidos en la cripta <id>: …"` (nombrar cuál).
  - `IndiceLlaves` con los ids de `llaves.ids`, de las aristas con `llave` y la llave de salida; listas `ubicaciones_por_sala`, `ubicaciones_por_llave`, `obtenible`, `obtenida`, `esperando`, `alcanzable`.
  - Recorrido por oleadas con `ColaCircular`: salidas en orden del mapa; destino inexistente se ignora; abierta se cruza; cerrada sin llave nunca; cerrada con llave obtenida se cruza; si no, a `esperando[número]`. Al alcanzar una sala, sus ubicaciones entran a `MonticuloMinimo` como `(sala, número)` (comentar que los parámetros del montículo se llaman `costo`/`sala`).
  - Fin de oleada: si la sala de salida es alcanzable y la llave de salida es obtenible → vaciar los pendientes de la oleada al orden y devolver resoluble; si no hay pendientes → no resoluble (T031); si no, sacar **todos** los pendientes en orden, marcar obtenidas, agregar `PasoLlaveDTO` (suelo antes que enemigo, menor instancia comparando cadenas a mano) y liberar `esperando`.
  - `salas_alcanzables` recorriendo `alcanzable` por id creciente.

  (FR-332 a FR-336)
- [ ] T031 [US1] En el mismo archivo, camino no resoluble ([research.md §6](research.md)): `salas_alcanzables` y `salas_no_alcanzables`; un solo `RecorridoPorNiveles` sin criterio desde la sala inicial (solo en este camino) para «camino ignorando las puertas»; `bloqueos` recorriendo las salas alcanzables por id y sus salidas en N, S, E, O, con tipo `SIN_LLAVE`, `LLAVE_INEXISTENTE`, `CICLO` (alguna ubicación de la llave tiene camino ignorando puertas) o `LLAVE_SIN_CAMINO` (ninguna lo tiene), y `salas_de_la_llave` creciente sin repetir; `causas` en el orden de `CAUSAS_EN_ORDEN`. (FR-337, FR-338)
- [ ] T032 [US1] En el mismo archivo, `verificar(fuente, cripta_id, llaves=None)` real ([research.md §8](research.md)): `existe_cripta` (si no, `motivo_error` «La cripta <id> no existe»); `MapaCripta(fuente.obtener_mapa(cripta_id))`; `obtener_sala_inicial`, `obtener_sala_salida`, `obtener_llave_salida`; `ubicacion_llaves` solo si `llaves is None`. Capturar `LlavesNoDisponibles` y `DatoLocalFaltante` (su mensaje) y `RuntimeError`/`OSError` («No se pudieron obtener los datos de la cripta <id>: <motivo>»). Quitar `MOTIVO_PROVISIONAL` y reemplazar en `test_resolubilidad_reporte.py` la prueba `test_fr343_cuerpo_provisional_devuelve_codigo_2` por `test_fr343_sin_datos_devuelve_codigo_2` (con `fallo_llaves="sin_respuesta"`). (FR-341, FR-343, FR-344)
- [ ] T033 Ejecutar `python -m unittest test_resolubilidad_regla test_resolubilidad_apendice_b test_resolubilidad_determinismo test_indice_llaves test_resolubilidad_reporte` y la suite de la línea base. **Terminado**: todo pasa, incluida `Equivalencia` con las 20 semillas.

**Punto de control (MVP)**: la verificación da el resultado correcto en los cuatro casos B-R y coincide con el oráculo.

---

## Grupo E: Texto del reporte y códigos de salida (US1)

**Objetivo**: un solo lugar para el texto, idéntico entre ejecuciones ([contracts/reporte-verificacion.md](contracts/reporte-verificacion.md)).

- [ ] T034 [P] [US1] Ampliar `test_resolubilidad_reporte.py`:
  - Clase `Texto`: `test_fr336_resoluble_muestra_orden_con_sala_y_enemigo` (líneas exactas de B-R3 y la línea con enemigo de B-R2); `test_fr337_lista_salas_alcanzables`; `test_fr338_texto_por_tipo_de_bloqueo` (los 4 tipos); `test_fr338_texto_por_causa` (las 4 causas, una línea `Motivo:` por causa en orden); `test_fr338_b_r1_reporte_completo` (las 5 líneas del ejemplo del contrato, con el id `cripta-01` que publica la API falsa v2); `test_fr343_reporte_de_error`.
  - Clase `CodigosDeSalida`: `test_fr331_resoluble_0_no_resoluble_1_error_2` con B-R3, B-R1 y `fallo_llaves="sin_respuesta"`.
  - Clase `VerificarSinPartida`: `test_fr330_verificar_no_inicia_partida_ni_crea_log_ni_vista`: tras `EstadoJuegoServicio.verificar`, la lógica sigue con `iniciado is False`, `AlmacenLogTexto.abrir` (con `unittest.mock.patch`) no se llamó y no se instanció `Controlador.Vista`.
  - Clase `AvisoForzado`: `test_fr340_aviso_forzado_una_linea` con el texto del contrato.

  (FR-330, FR-331, FR-336 a FR-338, FR-340, FR-343)
- [ ] T035 Ejecutar `python -m unittest test_resolubilidad_reporte` y registrar la evidencia roja: `Texto` y `AvisoForzado` fallan (envolver en las pruebas el `NotImplementedError` de T017 con `self.fail`); `CodigosDeSalida` y `VerificarSinPartida` probablemente pasan ya (el DTO y `verificar` existen): anotar que fallarían si `codigo_salida` cambiara el mapeo o si `verificar` iniciara la partida. (IX)
- [ ] T036 [US1] Completar `Logica/ReporteVerificacion.py` con los textos exactos de [contracts/reporte-verificacion.md](contracts/reporte-verificacion.md): encabezado por caso, orden numerado con `(llave de salida)`, líneas `Motivo:`, `Puertas bloqueadas:` con el texto por tipo, `Salas alcanzables (n): …`, `Salas no alcanzables: n`, y `aviso_forzado`. Solo a partir del resultado: sin hora, rutas ni contadores. (FR-335 a FR-338, FR-340)
- [ ] T037 Ejecutar `python -m unittest test_resolubilidad_reporte`. **Terminado**: todo pasa.

**Punto de control**: `lineas_reporte(r)` y `r.codigo_salida()` son todo lo que necesita `--verificar`.

---

## Grupo F: Datos y solicitudes (US3, US5)

**Objetivo**: las tres fuentes dan lo mismo, con 0 solicitudes si las llaves están guardadas, y errores de datos claros con código 2.

- [ ] T038 [P] [US5] Crear `test_resolubilidad_datos.py`:
  - Clase `Solicitudes`: `test_fr341_llaves_guardadas_cero_solicitudes` (con `ClientePersistente` en carpeta temporal: una primera sesión obtiene las llaves; en una sesión nueva, `verificar` no agrega llamadas `("llaves", …)` y el contador no cambia); `test_fr341_sin_llaves_solo_la_consulta_de_la_009` (exactamente una llamada `("llaves", id)`); `test_fr341_nunca_pide_contenido` (ninguna llamada `obtener_contenido` en `HttpConfigurable.llamadas`).
  - Clase `ErroresDeDatos`: `test_fr343_servicio_sin_respuesta` (`fallo_llaves="sin_respuesta"`: `resoluble is None`, código 2, el motivo nombra la cripta); `test_fr343_offline_sin_llaves_sin_solicitudes` (`ClienteOffline` sobre una caché sin llaves); `test_fr343_cripta_inexistente`; `test_fr343_h4_5_sala_de_salida_inexistente` (`HttpConfigurable(sala_salida=<id sin sala>)`: código 2 y «Datos inválidos»).
  - Clase `CasosLimite` (casos límite de `spec.md` que no tenían prueba): `test_fr333_salida_a_sala_inexistente_se_ignora` (una salida apunta a un id sin sala: se ignora, la sala no aparece en `salas_alcanzables` y el resto del resultado no cambia); `test_fr343_ubicacion_de_llave_en_sala_inexistente_es_error_de_datos` (la consulta de llaves trae una sala que no existe: la 009 la rechaza y `verificar` da `resoluble is None`, código 2, sin resultado inventado); `test_fr339_cambio_de_version_entre_verificar_y_la_partida` (con `ClientePersistente`: `verificar` con la versión `v1` es resoluble; el servicio publica `v2` con la puerta de la salida pidiendo una llave inexistente; una partida nueva vuelve a verificar con los datos de `v2` y no inicia sin `forzar`).

  (FR-341, FR-343, SC-003, SC-004)
- [ ] T039 [P] [US3] Ampliar `test_resolubilidad_determinismo.py`: clase `Fuentes` con `test_fr342_h3_4_http_offline_y_solo_local_dan_lo_mismo` (`ServicioCripta` sobre `HttpConfigurable`, `ClienteOffline` tras guardar con `ClientePersistente`, y `FuenteSoloLocal`: resultados iguales campo por campo); y en `Determinismo`, `test_fr335_h3_3_con_y_sin_contenido_guardado` (precargar todas las salas y verificar de nuevo: resultado igual). (FR-335, FR-342)
- [ ] T040 Ejecutar `python -m unittest test_resolubilidad_datos test_resolubilidad_determinismo`. Como el algoritmo y `verificar` ya existen, varias pruebas pueden pasar a la primera: por cada una, anotar en «Evidencia en rojo» qué aserción fallaría y con qué cambio (por ejemplo, «fallaría si `verificar` llamara a `ubicacion_llaves` aunque reciba `llaves`»). Registrar como rojo solo lo que falle de verdad. (IX)
- [ ] T041 [US5] Corregir en `Logica/VerificacionResolubilidad.py` lo que haya fallado en T040 (por ejemplo, la traducción de un error de datos). Si la corrección exige tocar un adaptador, hacerlo solo en `adaptadores/servicioCripta.py` o `adaptadores/fuente_solo_local.py` y anotarlo. Si todo pasó en T040, marcar la tarea como «sin cambios» con la explicación. (FR-341 a FR-343)
- [ ] T042 Ejecutar `python -m unittest test_resolubilidad_datos test_resolubilidad_determinismo`. **Terminado**: todo pasa.

**Punto de control**: FR-341 a FR-343 cubiertos con las tres fuentes.

---

## Grupo G: Inicio de partida y `--forzar` (US4)

**Objetivo**: la cripta no resoluble no inicia sin `--forzar` y no deja log; con `--forzar` inicia con aviso solo al iniciar; sin llaves o con datos inválidos inicia con aviso ([research.md §7](research.md), [data-model.md §5](data-model.md)).

- [ ] T043 [P] [US4] Crear `test_resolubilidad_inicio.py` (con `EstadoJuegoServicio` sobre `ServicioCripta` + API falsa v2 y `unittest.mock.patch` sobre `AlmacenLogTexto.abrir` para espiar el log):
  - Clase `Inicio`: `test_fr339_no_resoluble_no_inicia_y_no_crea_log` (B-R1 sin `forzar`: lanza `CriptaNoResoluble` cuyo `str` contiene `NO RESOLUBLE`, `iniciado is False`, `abrir` no se llamó); `test_fr339_resoluble_inicia_sin_aviso`; `test_fr339_fr313_sin_llaves_sigue_con_aviso` (`fallo_llaves="sin_respuesta"`: inicia, `avisoLlaves` no `None`, `avisoResolubilidad is None`); `test_fr339_h4_5_datos_invalidos_inicia_con_aviso` (sala de salida inexistente con llaves válidas: inicia y `avisoResolubilidad` termina con «La verificación de resolubilidad no está disponible.»); `test_fr339_replay_y_partida_cargada_no_verifican` (`iniciarJuego(..., pedir_llaves=False)` sobre B-R4 inicia con `resultadoVerificacion is None`; `restaurar_estado` deja los dos atributos en `None`); `test_fr339_reintento_tras_no_resoluble` (después de `CriptaNoResoluble`, `iniciarJuego` con `forzar=True` sobre el mismo objeto funciona).
  - Clase `Forzar`: `test_fr340_forzar_inicia_con_aviso_solo_al_iniciar` (B-R1 con `forzar=True`: inicia, `avisoResolubilidad() == aviso_forzado(resultado)`, y el aviso no aparece en `ultimosMensajes()` ni en el log después de una acción); `test_fr340_forzar_sin_efecto_en_resoluble`.
  - Clase `MismaOperacion`: `test_fr344_inicio_y_verificar_dan_el_mismo_resultado` (`logica.resultadoVerificacion` igual a `servicio.verificar(...)` en B-R3, y con `patch` se comprueba que `iniciarJuego` llamó a `VerificacionResolubilidad.verificar` con `llaves=` las de la partida).

  (FR-313, FR-339, FR-340, FR-344, SC-005)
- [ ] T044 [P] [US4] En `test_resolubilidad_apendice_b.py`, `CasosB.test_b_r4_fr339_no_inicia_sin_forzar`: ejecutar el paso `("iniciar_sin_forzar",)` del guion de B-R4 con `EstadoJuegoServicio.iniciarJuego`: lanza `CriptaNoResoluble`, la partida no inicia, `AlmacenLogTexto.abrir` no se llamó y el mensaje es el reporte (contiene `itm_llave_perdida`). (B-R4, FR-339)
- [ ] T045 [P] [US4] En `test_resolubilidad_datos.py`, `Solicitudes.test_fr341_inicio_reutiliza_las_llaves_de_la_partida`: una partida nueva hace una sola llamada `("llaves", id)` en total y `ubicacion_llaves` se invoca una sola vez (la verificación no la repite). (FR-341)
- [ ] T046 Ejecutar `python -m unittest test_resolubilidad_inicio test_resolubilidad_apendice_b test_resolubilidad_datos` y registrar la evidencia roja: las de `Inicio`, `Forzar`, `MismaOperacion` y B-R4 fallan por aserción porque `forzar` todavía no tiene efecto y `iniciarJuego` no verifica. `test_fr339_fr313_sin_llaves_sigue_con_aviso` y `test_fr341_inicio_reutiliza_las_llaves_de_la_partida` pueden pasar ya: anotar qué aserción fallaría. (IX)
- [ ] T047 [US4] En `Logica/EstadoJuegoLogica.py`, `iniciarJuego`: al empezar, `resultadoVerificacion` y `avisoResolubilidad` en `None`; después de `self.obtenerLlaves()` y **antes** de `self.iniciado = True`, aplicar las transiciones de [data-model.md §5](data-model.md): sin llaves no verifica; con llaves, `verificar(self.comunicacion, cripta, llaves=self.llaves)`; resoluble sigue; no resoluble con `forzar` → `avisoResolubilidad = aviso_forzado(resultado)`; no resoluble sin `forzar` → `raise CriptaNoResoluble(resultado)`; error de datos → `avisoResolubilidad = <motivo_error> + " La verificación de resolubilidad no está disponible."`. `pedir_llaves=False` no verifica. (FR-339, FR-340, FR-344)
- [ ] T048 [US4] En `Servicio/EstadoJuegoServicio.py`, comprobar que `iniciarJuego` deja pasar `CriptaNoResoluble` **antes** de `_abrirLog` y que `AlmacenLogTexto(nombre_log).comprobar_nombre()` no crea archivos; ajustar solo si la prueba lo exige y anotar el resultado. (FR-339)
- [ ] T049 Ejecutar `python -m unittest test_resolubilidad_inicio test_resolubilidad_apendice_b test_resolubilidad_datos` y la suite de la línea base. **Terminado**: todo pasa, incluidos los cuatro casos B-R.

**Punto de control**: las historias US1 a US5 funcionan juntas.

---

## Grupo H: Medición (US6)

**Objetivo**: bloque `--bench resolubilidad` con la alternativa descartada ([contracts/bench-resolubilidad.md](contracts/bench-resolubilidad.md), [research.md §9](research.md)).

- [ ] T050 [P] [US6] En `test_resolubilidad_determinismo.py`, clase `CadenaSintetica`: `test_fr346_cadena_determinista_por_semilla` (dos llamadas con la misma semilla dan lo mismo; con otra semilla cambian los ids); `test_fr346_cadena_es_resoluble_con_n_llaves` (n = 50: resoluble, `orden` con n llaves incluida la de salida, en el orden de la cadena); `test_fr346_ids_no_siguen_la_cadena` (el orden de ids no coincide con el de la cadena). (FR-346, V)
- [ ] T051 Ejecutar `python -m unittest test_resolubilidad_determinismo` y registrar la evidencia roja de `CadenaSintetica` (falla por `self.fail`: `esqueleto_llaves_encadenadas` no existe). (IX)
- [ ] T052 [US6] En `tests_labs/cripta_sintetica.py`, `esqueleto_llaves_encadenadas(n, semilla) -> (esqueleto, llaves, llave_salida, sala_salida)` según [data-model.md §7](data-model.md): pasillo de n salas y una lateral por sala; la puerta i → i+1 (en los dos sentidos) se abre con `k_<j>`, ubicada en la lateral de la sala i; los nombres `j` y el orden de las laterales se barajan con `random.Random(semilla)`; la llave de salida en la lateral de la última sala. `llaves` como lista de tuplas `(id, sala, None)`. Sin tamaños fijos. (FR-346, V)
- [ ] T053 [US6] Crear `bench/resolubilidad.py` con `ejecutar(filas: list) -> bool` y las secciones A a D del contrato: A (incremental y `verificar_repetida` de `tests_labs/referencia_resolubilidad.py`, n = 300 y 3 000, mediana de 5; la repetida con n = 3 000 con 1 repetición si la primera supera 10 s, anotado en la fila; falla si los resultados difieren); B (búsqueda binaria de `IndiceLlaves` frente a búsqueda lineal escrita en el bench, K = 100, 1 000, 10 000; informativa); C (incremental en la cadena con n = 5 000 y en la rejilla de 70 × 70 con `fraccion_cerradas=0.15` y llaves asignadas por semilla; falla si supera 200 ms); D (razón t(3 000)/t(300) de cada estrategia; falla si la de la incremental supera 20). Mide con `time.perf_counter_ns` sobre la función pura, con `MapaCripta` y `UbicacionLlavesDTO` ya construidos. Sin red, vista ni caché del usuario. (FR-345, FR-346, VII)
- [ ] T054 [US6] Registrar el bloque en `bench/__init__.py` (`("resolubilidad", resolubilidad.ejecutar)` en `BLOQUES`, indicador `cumple_resolubilidad` y su línea en el resumen: «Resolubilidad (FR-345, FR-346): CUMPLE.» o el motivo), y mencionar `resolubilidad` en la ayuda de `--bench` de `main.py` (solo ese texto). (VII)
- [ ] T055 [US6] En `tests_labs/sin_red.py`, agregar las pruebas de la capacidad (`test_mapa_con_llaves`, `test_indice_llaves`, `test_resolubilidad_regla`, `test_resolubilidad_apendice_b`, `test_resolubilidad_determinismo`, `test_resolubilidad_datos`, `test_resolubilidad_inicio`, `test_resolubilidad_reporte`). (SC-002, IX)
- [ ] T056 Con la máquina libre, ejecutar `python main.py --bench resolubilidad` y `python -m tests_labs.sin_red`. Guardar la salida del bench (cabecera con Python, sistema, fecha y semilla) para `mediciones.md`. **Terminado**: el bench termina con 0 (o se anota con honestidad qué criterio no se cumple) y `sin_red` pasa. (FR-345, FR-346, SC-006, SC-007)

**Punto de control**: el bench muestra las dos estrategias, el límite y el crecimiento.

---

## Grupo I: Cierre

**Propósito**: medición manual, documentos, trazabilidad, revisión final. Los documentos van en tareas aparte del código.

- [ ] T057 Medir a mano la cripta publicada más grande (paso 3 de `quickstart.md`): con su caché vigente en `datos_cripta/`, `crear_fuente_solo_local` y `verificar(fuente, <id>)` cronometrado con `time.perf_counter_ns` (mediana de 5), con un guion temporal en la carpeta temporal de la sesión (no en el repositorio). Si la caché no está, indicarlo a Scott en lugar de descargarla: descargarla gasta solicitudes. Anotar id, salas, tiempo y solicitudes (0). (FR-345, SC-006)
- [ ] T058 [P] Crear `specs/003-verificacion-resolubilidad/mediciones.md`: cabecera de la máquina, tablas de las secciones A a D de T056, la medición manual de T057, el estado de FR-345, FR-346, SC-006 y SC-007, y la conclusión (se mantiene el recorrido incremental o, si una medición lo contradice, qué cambia). (VII)
- [ ] T059 [P] Agregar la sección 003 a `DECISIONES.md` con enlaces a `spec.md` y `plan.md`: para cada decisión (llave en la arista, oleadas, `MonticuloMinimo`, `IndiceLlaves`, dónde vive cada parte, `CriptaNoResoluble` antes del log, códigos 0/1/2), si coincide con el plan y qué prueba o medición la respalda. Incluir lo anotado en T009 y T041 si hubo cambios. (X)
- [ ] T060 [P] Actualizar `DOCUMENTACION_API.md`: `AristaMapaDTO.llave` y `AristaCripta.llave`; `obtener_sala_inicial` y `obtener_llave_salida` en el contrato y en las fuentes; `verificar` (Logica y Servicio), `ResultadoVerificacion`, `PasoLlaveDTO`, `BloqueoDTO`, `CriptaNoResoluble`, `iniciarJuego(..., forzar)`, `avisoResolubilidad()`; códigos 0/1/2. (IV, IX)
- [ ] T061 [P] Actualizar `README.md` con una línea sobre la capacidad 003, `python main.py --bench resolubilidad` y que `--verificar`/`--forzar` los conecta la capacidad de Fernanda sobre esta interfaz. (VII)
- [ ] T062 [P] Completar la matriz de `specs/003-verificacion-resolubilidad/quickstart.md` con los nombres reales (`archivo: Clase.método`) tomados de los archivos que existen; comprobar que ningún FR-330 a FR-346 ni escenario H1-1 a H6-2 queda sin prueba o medición, y que B-R1 a B-R4 están. Si `research.md` §1 necesita la nota de T009, agregarla aquí. (IX)
- [ ] T063 Comprobar con búsqueda (paso 5 de `quickstart.md`) que `DTO/ResultadoVerificacionDTO.py`, `Logica/IndiceLlaves.py`, `Logica/VerificacionResolubilidad.py`, `Logica/ReporteVerificacion.py`, `bench/resolubilidad.py`, `tests_labs/referencia_resolubilidad.py` y los cambios en `MapaDTO.py`, `MapaCripta.py`, `servicioCripta.py`, `fuente_solo_local.py`, `EstadoJuegoLogica.py` y `EstadoJuegoServicio.py`: no importan `heapq`, `bisect`, `collections` ni `networkx`; no usan `dict`/`set` como índice ni `sorted()`/`.sort()`; no contienen ids ni tamaños de una cripta concreta; `Logica/` y `DTO/` no importan adaptadores. Comprobar con `git diff --stat` que `AlmacenPartidaBinario.py`, `EstadoGuardadoDTO.py` y `codec_partida.py` no cambiaron, y que todos los archivos nuevos o modificados están en CRLF. (I, IV, V)
- [ ] T064 Ejecutar `python -m unittest discover -p "test_*.py"`, `python -m tests_labs.sin_red` y `python main.py --bench`. Comparar con la línea base de T002 y registrar cualquier fallo sin ocultarlo. (IX)
- [ ] T065 Comparar `spec.md` con el programa entregado; si hay desajustes, corregir primero la especificación en una tarea y un commit aparte (X). Después, poner el **Estado** de `spec.md` en «Implementada (T001 a T066)» y marcar con `[X]` las tareas terminadas de este archivo. (X)
- [ ] T066 Preparar, **sin editar `PROMPTS_LLM.md`**, el texto de las filas de esta capacidad (`/speckit-specify`, respuestas del clarify de la spec, `/speckit-plan`, `/speckit-clarify`, `/speckit-tasks`, `/speckit-implement` y los prompts literales sin comando), con fecha, persona, herramienta y modelo, y entregarlo en el informe final para que Scott lo pase por lotes. (XI)

---

## Dependencias y orden de ejecución

### Entre grupos

- **A** primero. T001, T002 y T003 son paralelas; T004 → T005 → (T006 ∥ T007) → T008 → T009.
- **B** depende de A. T010 → T011 → (T012 ∥ T013 ∥ T016 ∥ T017) → T014 → T015 → T018 → T019 → T020. T016 importa T017; se prueban juntos en T020. **Punto de parada** al terminar: no seguir sin la confirmación de Scott.
- **C** depende de B (punto de parada). T021 → T022 → T023 → T024. Puede hacerse en paralelo con las pruebas del grupo D (T025 a T028), que no dependen de `IndiceLlaves`.
- **D** depende de C (la implementación usa `IndiceLlaves`). T025, T026, T027 y T028 en paralelo → T029 → T030 → T031 → T032 → T033.
- **E** depende de D. T034 → T035 → T036 → T037.
- **F** depende de D (T032). Puede ir en paralelo con E: T038 ∥ T039 → T040 → T041 → T042. T039 y T027 tocan el mismo archivo: T039 después de T033.
- **G** depende de D y E (`aviso_forzado`). T043 ∥ T044 ∥ T045 → T046 → T047 → T048 → T049. T045 después de T038 (mismo archivo); T044 después de T026.
- **H** depende de D (T028 y T032). Puede ir en paralelo con E, F y G salvo por `test_resolubilidad_determinismo.py` (T050 después de T039). T050 → T051 → T052 → T053 → T054 → T055 → T056.
- **I** al final. T057 primero (los datos de T058); T058 a T062 en paralelo; T063 → T064 → T065 → T066.

### Dentro de cada grupo

Primero la prueba; luego la ejecución que registra la evidencia roja; luego la implementación; al final el punto de control. No se pasa al grupo siguiente con su punto de control en rojo.

### Oportunidades de paralelismo

- Grupo A: T001, T002, T003; luego T006 y T007.
- Grupo B: T012, T013, T016 y T017 (cuatro archivos distintos).
- Grupos C y D: las pruebas T021, T025, T026, T027 y T028 a la vez.
- Después del grupo D: E, F y H pueden repartirse entre integrantes (cuidando los archivos compartidos indicados arriba).
- Grupo I: T058 a T062.

### Ejemplo: grupo B en paralelo

```text
T012 DTO/ResultadoVerificacionDTO.py        (DTO del resultado)
T013 Logica/FuenteCripta.py                 (dos operaciones del protocolo)
T016 Logica/VerificacionResolubilidad.py    (firmas y cuerpo provisional)
T017 Logica/ReporteVerificacion.py          (caso de error)
```

### Ejemplo: pruebas del grupo D en paralelo

```text
T025 test_resolubilidad_regla.py
T026 test_resolubilidad_apendice_b.py
T027 test_resolubilidad_determinismo.py
T028 tests_labs/referencia_resolubilidad.py (oráculo)
```

---

## Estrategia de implementación

1. **Fundamentos (A y B)**: el mapa conoce las llaves de las puertas y la interfaz queda fija con cuerpo provisional. **Punto de parada**: Scott avisa a Fernanda y hace un commit aparte.
2. **MVP (C y D)**: índice y algoritmo; los cuatro casos B-R dan el resultado correcto y coinciden con el oráculo.
3. **Reporte (E)**: `--verificar` ya tiene todo lo que necesita (texto y código de salida).
4. **Datos (F) e inicio de partida (G)**: las tres fuentes, los errores de datos, la regla de no iniciar y `--forzar`.
5. **Medición (H)** y **cierre (I)**.

Cada incremento se confirma por separado. La especificación y el plan se confirman antes del primer commit de código (principio X).

---

## Cobertura de requisitos

| Requisito / caso | Tareas |
|---|---|
| FR-330 | T017, T019, T034, T036 |
| FR-331 | T010, T012, T034, T036 |
| FR-332 | T025, T030 |
| FR-333 | T004, T006, T007, T008, T009, T025, T030, T038 |
| FR-334 | T025, T026, T030 |
| FR-335 | T021, T023, T026, T027, T028, T030, T036, T039 |
| FR-336 | T012, T025, T026, T030, T034, T036 |
| FR-337 | T012, T025, T031, T034, T036 |
| FR-338 | T012, T025, T026, T031, T034, T036 |
| FR-339 | T010, T018, T038, T043, T044, T047, T048 |
| FR-340 | T018, T034, T036, T043, T047 |
| FR-341 | T004, T014, T032, T038, T045 |
| FR-342 | T004, T015, T039, T041 |
| FR-343 | T010, T016, T017, T032, T038, T041 |
| FR-344 | T010, T013, T014, T015, T016, T019, T043, T047 |
| FR-345 | T053, T056, T057, T058 |
| FR-346 | T027, T050, T052, T053, T056, T058 |
| B-R1 | T026, T034, T043 |
| B-R2 | T026, T034 |
| B-R3 | T026, T034, T043 |
| B-R4 | T026, T044 |
| Cambio del mapa (G1 a G6) | T004 a T009 |
| Escenarios del clarify (H1-7, H3-2 con dos oleadas, H4-5) | T003, T025, T027, T038, T043 |

---

## Evidencia en rojo

*Cada tarea de ejecución (T005, T011, T022, T029, T035, T040, T046, T051) agrega aquí: fecha, comando, resumen de la salida (pruebas que fallan y la aserción) y, para las que pasaron a la primera, qué aserción fallaría y con qué cambio del código.*

### T005 — 2026-11-08 — `python -m unittest -v test_mapa_con_llaves` (antes de tocar `DTO/MapaDTO.py`, `Logica/MapaCripta.py` y `adaptadores/servicioCripta.py`)

Resultado: `Ran 6 tests`, `FAILED (failures=5)`, 0 errores.

| Prueba | Resultado | Aserción |
|---|---|---|
| `test_fr333_g1_esqueleto_copia_la_llave` | FAIL | `Lists differ: [(1, 'sur', '<sin campo>'), (1, 'este', '<sin campo>') …] != [(1, 'sur', 'itm_llave_a'), (1, 'este', None) …]`: `AristaMapaDTO` no tiene `llave` |
| `test_fr333_g2_mapa_cripta_copia_la_llave` | FAIL | La misma diferencia leyendo `MapaCripta.salidas(n)`: `AristaCripta` no tiene `llave` |
| `test_fr342_g3_offline_igual_que_con_red` | FAIL | Con red y offline coinciden (las dos sin campo); falla la comparación con las ternas esperadas |
| `test_fr342_g4_fuente_solo_local_igual_sin_solicitudes` | FAIL | La misma diferencia por `FuenteSoloLocal.esqueleto()` |
| `test_g5_construccion_sin_llave_sigue_funcionando` | FAIL | `'<sin campo>' is not None` (la primera aserción; el `self.fail` por `TypeError` queda detrás) |
| `test_fr341_g6_sin_solicitudes_nuevas` | **pasa a la primera** | Es una garantía de regresión: hoy el esqueleto hace exactamente `[('criptas', None), ('salas', 'cripta-01')]` (línea base anotada en T002). Fallaría si el cambio hiciera que `esqueleto()` pidiera de nuevo las salas (`veces("salas") == 2`) o agregara cualquier otra llamada al `HttpConfigurable` (por ejemplo, pedir el contenido para buscar las llaves) |

Nota: la primera ejecución dio 2 errores en G3 y G4 por un defecto **de la prueba**, no del código: `ClienteOffline` solo acepta criptas guardadas por completo (`ErrorOffline: Ninguna cripta está guardada por completo`). Se corrigió la preparación (guardar también todo el contenido y las llaves, como `guardar_cripta_completa` de `test_fuente_solo_local`) y la salida de arriba es la de la prueba corregida, todavía sin cambios de código.
