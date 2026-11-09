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

- [X] T010 Crear `test_resolubilidad_reporte.py` con la clase `Contrato` (importaciones dentro de cada prueba con `try/except ImportError: self.fail(...)`):
  - `test_fr344_firmas_de_la_interfaz`: con `inspect.signature`, comprobar `verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id="")`, `verificar(fuente, cripta_id, llaves=None)`, `EstadoJuegoServicio.verificar(self, cripta_id, offline=None)`, `EstadoJuegoServicio.iniciarJuego(..., forzar=False)`, `EstadoJuegoLogica.iniciarJuego(self, cripta, semilla=None, pedir_llaves=True, forzar=False)`, `EstadoJuegoServicio.avisoResolubilidad(self)`, `lineas_reporte(resultado)` y `aviso_forzado(resultado)`.
  - `test_fr331_codigo_salida`: `ResultadoVerificacion(..., resoluble=True/False/None)` da 0 / 1 / 2.
  - `test_fr344_campos_del_resultado`: `ResultadoVerificacion` tiene `cripta_id`, `resoluble`, `orden`, `salas_alcanzables`, `salas_no_alcanzables`, `bloqueos`, `causas`, `llave_salida`, `sala_salida`, `motivo_error`; `PasoLlaveDTO` tiene `llave`, `sala`, `enemigo`; `BloqueoDTO` tiene `sala_origen`, `direccion`, `sala_destino`, `llave`, `salas_de_la_llave`, `tipo`; las listas por defecto están vacías y no se comparten entre instancias.
  - `test_fr339_cripta_no_resoluble_es_runtime_error`: `CriptaNoResoluble` hereda de `RuntimeError` y guarda `resultado`.
  - `test_fr344_fuente_entrega_sala_inicial_y_llave_salida`: con `HttpFalso`, `ServicioCripta.obtener_sala_inicial("cripta-01") == 1` y `obtener_llave_salida(...) == "itm_llave_negra"`; con `FuenteSoloLocal` sobre la misma cripta guardada, los mismos valores y 0 solicitudes; `FuenteCripta` declara ambos métodos.
  - `test_fr343_cuerpo_provisional_devuelve_codigo_2`: `verificar(...)` devuelve `resoluble is None`, `motivo_error == "La verificación de resolubilidad todavía no está implementada."` y `codigo_salida() == 2`; `lineas_reporte` de ese resultado da las dos líneas del caso de error de `contracts/reporte-verificacion.md`. (Esta prueba se **reemplaza** en el grupo D, T032, cuando el cuerpo deja de ser provisional; anotarlo en el docstring.)

  **Terminado**: el archivo corre sin errores de importación. (FR-331, FR-339, FR-343, FR-344)
- [X] T011 Ejecutar `python -m unittest test_resolubilidad_reporte` y registrar la evidencia roja: todas fallan por `self.fail` («todavía no existe») o por aserción. **Terminado**: evidencia anotada. (IX)
- [X] T012 [P] Crear `DTO/ResultadoVerificacionDTO.py` (sin importar `Logica/` ni `adaptadores/`), según [data-model.md §3](data-model.md):
  - Constantes de tipo de bloqueo `SIN_LLAVE`, `LLAVE_INEXISTENTE`, `CICLO`, `LLAVE_SIN_CAMINO` y de causas `LLAVE_SALIDA_INEXISTENTE`, `SALIDA_SIN_CAMINO`, `SALIDA_BLOQUEADA`, `LLAVE_SALIDA_INALCANZABLE`, más la tupla `CAUSAS_EN_ORDEN` en ese orden fijo.
  - `@dataclass PasoLlaveDTO(llave: str, sala: int, enemigo: str | None = None)`.
  - `@dataclass BloqueoDTO(sala_origen: int, direccion: str, sala_destino: int, llave: str | None, salas_de_la_llave: list[int], tipo: str)`.
  - `@dataclass ResultadoVerificacion(cripta_id: str, resoluble: bool | None, orden, salas_alcanzables, salas_no_alcanzables: int = 0, bloqueos, causas, llave_salida: str | None = None, sala_salida: int | None = None, motivo_error: str | None = None)`, con las listas en `field(default_factory=list)`.
  - `codigo_salida()`: «0 si `resoluble is True`, 1 si `resoluble is False`, 2 si `resoluble is None`».
  - Docstring con las invariantes literales: «`resoluble is None` ⇔ `motivo_error is not None`»; «`resoluble is True` ⇒ la llave de salida figura exactamente una vez en `orden`; `bloqueos` y `causas` vacías»; «`resoluble is False` ⇒ `orden` vacía y `causas` no vacía»; «cada id de llave aparece como máximo una vez en `orden`». (FR-331, FR-336 a FR-338, FR-343, FR-344)
- [X] T013 [P] En `Logica/FuenteCripta.py` agregar al `Protocol` `obtener_sala_inicial(self, cripta_id: str) -> int: ...` y `obtener_llave_salida(self, cripta_id: str) -> str | None: ...`, junto a `obtener_sala_salida`. (FR-344, IV)
- [X] T014 En `adaptadores/servicioCripta.py` agregar `obtener_sala_inicial` (`self.datos_cripta(cripta_id)["sala_inicial"]`) y `obtener_llave_salida` (`self.datos_cripta(cripta_id).get("llave_salida")`), con docstring como el de `obtener_sala_salida`. Sin solicitudes nuevas (los datos generales ya se piden una vez). (FR-341, FR-344)
- [X] T015 En `adaptadores/fuente_solo_local.py` agregar los dos métodos con `self._leer(cripta_id, "los datos generales", lambda: self.fuente.obtener_...(cripta_id))`, como `obtener_sala_salida`. (FR-342, FR-344)
- [X] T016 [P] Crear `Logica/VerificacionResolubilidad.py` con la **entrega provisional**:
  - `MOTIVO_PROVISIONAL = "La verificación de resolubilidad todavía no está implementada."`.
  - `class CriptaNoResoluble(RuntimeError)`: `__init__(self, resultado)` guarda `self.resultado` y usa como mensaje `"\n".join(lineas_reporte(resultado))`.
  - `verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id="") -> ResultadoVerificacion` y `verificar(fuente, cripta_id, llaves=None) -> ResultadoVerificacion`: ambas devuelven `ResultadoVerificacion(cripta_id, resoluble=None, motivo_error=MOTIVO_PROVISIONAL)`.
  - Docstring del módulo que remite a `research.md` §2 a §8. Sin importar adaptadores. (FR-343, FR-344)
- [X] T017 [P] Crear `Logica/ReporteVerificacion.py` con `lineas_reporte(resultado) -> list[str]` y `aviso_forzado(resultado) -> str`. En esta entrega solo el caso de error (`resoluble is None`): `["Verificación de la cripta <id>: NO SE PUDO VERIFICAR.", <motivo_error>]`. Para los otros casos lanzar `NotImplementedError("se completa en el grupo E (T036)")`. (FR-330, FR-343)
- [X] T018 En `Logica/EstadoJuegoLogica.py`: `__init__` agrega `self.resultadoVerificacion = None` y `self.avisoResolubilidad = None`; `iniciarJuego(self, cripta, semilla=None, pedir_llaves=True, forzar=False)` acepta `forzar` **sin efecto** todavía. En `Logica/EstadoGuardadoLogica.py`, la restauración pone los dos atributos en `None` (una línea cada uno, junto a `llaves` y `avisoLlaves`). No tocar `DTO/EstadoGuardadoDTO.py`. (FR-339, FR-340)
- [X] T019 En `Servicio/EstadoJuegoServicio.py`:
  - `verificar(self, cripta_id: str, offline: bool | None = None) -> ResultadoVerificacion`: `self._asegurarServicio(offline)` y devuelve `VerificacionResolubilidad.verificar(self._estadoJuegoLogica.comunicacion, cripta_id)`; no inicia partida ni abre log.
  - `iniciarJuego(..., forzar: bool = False)`: pasa `forzar` a la lógica.
  - `avisoResolubilidad(self) -> str | None`: igual que `avisoLlaves()` (`None` si no hay partida iniciada).

  (FR-330, FR-344)
- [X] T020 Ejecutar `python -m unittest test_resolubilidad_reporte test_mapa_con_llaves` y la suite de la línea base. **Terminado**: todas las de `Contrato` pasan y la suite sigue igual.

**🛑 Punto de parada (fin del grupo B)**: detenerse aquí. Scott avisa a Fernanda que la interfaz está lista ([contracts/interfaz-verificacion.md](contracts/interfaz-verificacion.md)) y hace un commit aparte con los grupos A y B. No seguir con el grupo C hasta que Scott lo confirme.

---

## Grupo C: Índice de llaves (bloquea D)

**Propósito**: ids de llave de texto → número denso con el orden de los ids, sin `dict` ([research.md §4](research.md)).

- [X] T021 [P] Crear `test_indice_llaves.py`, clase `IndiceLlavesPrueba` (importación con `try/except ImportError: self.fail(...)`):
  - (a) `test_fr335_ids_quedan_en_orden_creciente`: con ids desordenados, `id_de(0..n-1)` es creciente.
  - (b) `test_fr335_repetidos_cuentan_una_vez`: `cantidad()` cuenta ids distintos.
  - (c) `test_fr335_numero_de_un_id_presente`: `numero(id) == i` si `id_de(i) == id`.
  - (d) `test_fr335_numero_de_un_id_ausente_es_menos_uno`: menor que todos, mayor que todos e intermedio.
  - (e) `test_lista_vacia`: `cantidad() == 0` y `numero("x") == -1`.
  - (f) `test_un_solo_elemento`.
  - (g) `test_prefijos_compartidos`: `itm_llave_a` e `itm_llave_ab` se distinguen.
  - (h) `test_fr335_igual_que_busqueda_lineal`: 1 000 ids generados con `random.Random(semilla)` (semillas 0 a 4); para cada id presente y 200 ausentes, `numero` coincide con una búsqueda lineal sobre `id_de`.

  (FR-335, I)
- [X] T022 Ejecutar `python -m unittest test_indice_llaves` y registrar la evidencia roja (falla por `self.fail`: el módulo no existe). (IX)
- [X] T023 Crear `Logica/IndiceLlaves.py`, `class IndiceLlaves`: `__init__(self, ids: list[str])` ordena con `ordenar_adaptativo` y quita repetidos comparando vecinos; `numero(id) -> int` es una **búsqueda binaria escrita a mano** (bucle con `bajo`/`alto`), −1 si no está; `id_de(numero) -> str`; `cantidad() -> int`. Docstring con costos: construir O(K log K), consultar O(log K). Sin `bisect`, `sorted()`, `.sort()`, `dict` ni `set`. (FR-335, I)
- [X] T024 Ejecutar `python -m unittest test_indice_llaves`. **Terminado**: las 8 pruebas pasan.

**Punto de control**: índice listo y equivalente a la búsqueda lineal.

---

## Grupo D: Algoritmo de resolubilidad (US1, US2, US3) 🎯 MVP

**Objetivo**: la regla de FR-332 a FR-334, el orden por oleadas de FR-335 y FR-336, y los bloqueos de FR-337 y FR-338, con la función pura y la operación `verificar` real.

**Prueba independiente**: con la API falsa v2, `verificar` sobre los casos B-R1 a B-R4 da los resultados de [contracts/reporte-verificacion.md](contracts/reporte-verificacion.md).

### Pruebas (escribir primero; deben fallar)

- [X] T025 [P] [US1] Crear `test_resolubilidad_regla.py`. Los mapas se arman con `esqueleto_de_conexiones`/`mapa_desde_esqueleto` (`tests_labs/cripta_sintetica.py`) y `_puerta_con_llave` (`tests_labs/api_falsa.py`); las llaves, con `UbicacionLlavesDTO` directo; se llama a `verificar_resolubilidad`.
  - Clase `Regla`: `test_fr332_h1_1_salida_alcanzable_y_llave_obtenible_es_resoluble`; `test_fr332_sala_inicial_es_salida`; `test_fr332_no_exige_puerta_hacia_la_salida` (la salida se alcanza por salidas abiertas y la llave de salida está en una sala alcanzable: resoluble); `test_fr333_h1_3_cadena_de_puertas` (orden `k1`, `k2`, `k3`, salida); `test_fr333_h1_6_respeta_salidas_de_un_solo_sentido`; `test_fr333_puerta_sin_llave_nunca_se_cruza`; `test_fr333_una_llave_abre_varias_puertas`; `test_fr334_h2_2_enemigo_tras_puerta` (obtenible si la puerta se abre y no obtenible si no); `test_fr334_h2_3_basta_una_ubicacion_alcanzable`; `test_fr336_llave_salida_en_el_orden_una_vez`.
  - Clase `Bloqueos`: `test_fr332_fr338_h1_4_salida_sin_camino` (`causas == ["SALIDA_SIN_CAMINO"]`); `test_fr332_fr338_h1_5_llave_salida_inexistente` (`"LLAVE_SALIDA_INEXISTENTE"` en `causas`); `test_fr337_salas_alcanzables_crecientes_y_cantidad_no_alcanzables`; `test_fr338_varios_bloqueos_en_orden` (por sala de origen creciente y N, S, E, O); `test_fr338_puerta_sin_llave_es_bloqueo_sin_llave`; `test_fr338_h1_7_llave_en_sala_sin_camino_es_bloqueo_no_ciclo` (tipo `LLAVE_SIN_CAMINO`); `test_fr338_ciclo_a_traves_de_otras_puertas` (la llave está detrás de dos puertas bloqueadas: tipo `CICLO`).

  (FR-332 a FR-334, FR-336 a FR-338)
- [X] T026 [P] [US1] Crear `test_resolubilidad_apendice_b.py`, clase `CasosB`. Un ayudante busca el caso por código en `CASOS_APENDICE_B`, arma un `ServicioCripta` sobre su `HttpConfigurable` y ejecuta los pasos `("verificar",)` del guion con `verificar(servicio, cripta_id)`:
  - `test_b_r1_fr338_ciclo`: `resoluble is False`, `causas == ["SALIDA_BLOQUEADA"]`, un solo bloqueo 1 → 2 de tipo `CICLO` con `llave == "itm_llave_salida"` y `salas_de_la_llave == [2]`, `salas_alcanzables == [1]`, `salas_no_alcanzables == 1`.
  - `test_b_r2_fr334_llave_de_errante_en_su_sala_inicial`: `orden == [PasoLlaveDTO("itm_llave_salida", 3, "e-errante")]`.
  - `test_b_r3_fr335_dos_ejecuciones_mismo_orden`: las dos verificaciones del guion dan `itm_llave_a` (sala 2), `itm_llave_b` (sala 3), `itm_llave_salida` (sala 5) y resultados iguales campo por campo.
  - `test_b_r4_fr338_llave_inexistente`: bloqueo de tipo `LLAVE_INEXISTENTE` con `llave == "itm_llave_perdida"` y `salas_de_la_llave == []`.

  (B-R1, B-R2, B-R3, B-R4; FR-334, FR-335, FR-338)
- [X] T027 [P] [US3] Crear `test_resolubilidad_determinismo.py`:
  - Clase `Determinismo`: `test_fr335_h3_2_dos_oleadas` (escenario H3-2 literal: sala inicial 5; en la primera oleada `X` en la sala 4, `B` y `A` en la sala 2; la llave `C` en la sala 3, detrás de la puerta que se abre con `A`; el orden es `A`, `B`, `X`, `C`: `C` va última aunque su sala tenga menor id que la de `X`, porque es de la oleada siguiente); `test_fr335_orden_de_la_respuesta_no_importa` (las tres listas de `UbicacionLlavesDTO` invertidas dan el mismo resultado); `test_fr335_suelo_antes_que_enemigo_y_menor_instancia` (misma llave y sala en el suelo y en un enemigo: `enemigo is None`; en dos enemigos: la menor instancia); `test_fr335_dos_ejecuciones_iguales`.
  - Clase `Equivalencia`: `test_fr335_fr346_incremental_igual_a_repetida_en_criptas_al_azar`: para las semillas 0 a 19, `cripta_al_azar_con_llaves(semilla)` (T028) y `verificar_resolubilidad` igual a `verificar_repetida` campo por campo. (III)

  (FR-335, FR-346, II, III)
- [X] T028 [P] [US3] Crear `tests_labs/referencia_resolubilidad.py` (oráculo, como `tests_labs/referencia_recorrido.py`):
  - `verificar_repetida(mapa, sala_inicial, sala_salida, llave_salida, llaves, cripta_id="") -> ResultadoVerificacion`: en cada oleada recorre **desde cero** desde la sala inicial con las llaves obtenidas hasta ahora; **para igual que el algoritmo**: al final de la oleada en que la sala de salida es alcanzable y la llave de salida es obtenible (incluye las llaves de esa oleada en el orden), o cuando una oleada no agrega ninguna llave nueva (no resoluble); las llaves nuevas de la oleada se ordenan con `ordenar_adaptativo` por `(sala, id)`; bloqueos, tipos y causas calculados de forma independiente con la definición de `spec.md` (FR-338) y `research.md` §6. Costo O(K · (S + E)): es la alternativa descartada que mide el bench.
  - `cripta_al_azar_con_llaves(semilla, salas=60) -> (mapa, sala_inicial, sala_salida, llave_salida, llaves)`: `esqueleto_dirigido_aleatorio` con puertas cerradas al azar, llaves asignadas a esas puertas y ubicadas en salas al azar (algunas en enemigos, algunas inexistentes), todo con `random.Random(semilla)`.

  Sin `dict`, `set`, `sorted()` ni `.sort()`. (III, VII)
- [X] T029 Ejecutar `python -m unittest test_resolubilidad_regla test_resolubilidad_apendice_b test_resolubilidad_determinismo` y registrar la evidencia roja: fallan por aserción porque el cuerpo provisional devuelve `resoluble is None`. Si alguna pasa a la primera (por ejemplo, una que compare dos resultados provisionales iguales), anotar qué aserción la haría fallar y reforzarla. **Terminado**: evidencia anotada. (IX)

### Implementación

- [X] T030 [US1] En `Logica/VerificacionResolubilidad.py`, `verificar_resolubilidad` (camino resoluble), según [research.md §2 y §3](research.md) y [data-model.md §4](data-model.md):
  - Si la sala inicial o la de salida no existe en `mapa.existe`: `resoluble=None`, `motivo_error="Datos inválidos en la cripta <id>: …"` (nombrar cuál).
  - `IndiceLlaves` con los ids de `llaves.ids`, de las aristas con `llave` y la llave de salida; listas `ubicaciones_por_sala`, `ubicaciones_por_llave`, `obtenible`, `obtenida`, `esperando`, `alcanzable`.
  - Recorrido por oleadas con `ColaCircular`: salidas en orden del mapa; destino inexistente se ignora; abierta se cruza; cerrada sin llave nunca; cerrada con llave obtenida se cruza; si no, a `esperando[número]`. Al alcanzar una sala, sus ubicaciones entran a `MonticuloMinimo` como `(sala, número)` (comentar que los parámetros del montículo se llaman `costo`/`sala`).
  - Fin de oleada: si la sala de salida es alcanzable y la llave de salida es obtenible → vaciar los pendientes de la oleada al orden y devolver resoluble; si no hay pendientes → no resoluble (T031); si no, sacar **todos** los pendientes en orden, marcar obtenidas, agregar `PasoLlaveDTO` (suelo antes que enemigo, menor instancia comparando cadenas a mano) y liberar `esperando`.
  - `salas_alcanzables` recorriendo `alcanzable` por id creciente.

  (FR-332 a FR-336)
- [X] T031 [US1] En el mismo archivo, camino no resoluble ([research.md §6](research.md)): `salas_alcanzables` y `salas_no_alcanzables`; un solo `RecorridoPorNiveles` sin criterio desde la sala inicial (solo en este camino) para «camino ignorando las puertas»; `bloqueos` recorriendo las salas alcanzables por id y sus salidas en N, S, E, O, con tipo `SIN_LLAVE`, `LLAVE_INEXISTENTE`, `CICLO` (alguna ubicación de la llave tiene camino ignorando puertas) o `LLAVE_SIN_CAMINO` (ninguna lo tiene), y `salas_de_la_llave` creciente sin repetir; `causas` en el orden de `CAUSAS_EN_ORDEN`. (FR-337, FR-338)
- [X] T032 [US1] En el mismo archivo, `verificar(fuente, cripta_id, llaves=None)` real ([research.md §8](research.md)): `existe_cripta` (si no, `motivo_error` «La cripta <id> no existe»); `MapaCripta(fuente.obtener_mapa(cripta_id))`; `obtener_sala_inicial`, `obtener_sala_salida`, `obtener_llave_salida`; `ubicacion_llaves` solo si `llaves is None`. Capturar `LlavesNoDisponibles` y `DatoLocalFaltante` (su mensaje) y `RuntimeError`/`OSError` («No se pudieron obtener los datos de la cripta <id>: <motivo>»). Quitar `MOTIVO_PROVISIONAL` y reemplazar en `test_resolubilidad_reporte.py` la prueba `test_fr343_cuerpo_provisional_devuelve_codigo_2` por `test_fr343_sin_datos_devuelve_codigo_2` (con `fallo_llaves="sin_respuesta"`). (FR-341, FR-343, FR-344)
- [X] T033 Ejecutar `python -m unittest test_resolubilidad_regla test_resolubilidad_apendice_b test_resolubilidad_determinismo test_indice_llaves test_resolubilidad_reporte` y la suite de la línea base. **Terminado**: todo pasa, incluida `Equivalencia` con las 20 semillas.

**Punto de control (MVP)**: la verificación da el resultado correcto en los cuatro casos B-R y coincide con el oráculo.

---

## Grupo E: Texto del reporte y códigos de salida (US1)

**Objetivo**: un solo lugar para el texto, idéntico entre ejecuciones ([contracts/reporte-verificacion.md](contracts/reporte-verificacion.md)).

- [X] T034 [P] [US1] Ampliar `test_resolubilidad_reporte.py`:
  - Clase `Texto`: `test_fr336_resoluble_muestra_orden_con_sala_y_enemigo` (líneas exactas de B-R3 y la línea con enemigo de B-R2); `test_fr337_lista_salas_alcanzables`; `test_fr338_texto_por_tipo_de_bloqueo` (los 4 tipos); `test_fr338_texto_por_causa` (las 4 causas, una línea `Motivo:` por causa en orden); `test_fr338_b_r1_reporte_completo` (las 5 líneas del ejemplo del contrato, con el id `cripta-01` que publica la API falsa v2); `test_fr343_reporte_de_error`.
  - Clase `CodigosDeSalida`: `test_fr331_resoluble_0_no_resoluble_1_error_2` con B-R3, B-R1 y `fallo_llaves="sin_respuesta"`.
  - Clase `VerificarSinPartida`: `test_fr330_verificar_no_inicia_partida_ni_crea_log_ni_vista`: tras `EstadoJuegoServicio.verificar`, la lógica sigue con `iniciado is False`, `AlmacenLogTexto.abrir` (con `unittest.mock.patch`) no se llamó y no se instanció `Controlador.Vista`.
  - Clase `AvisoForzado`: `test_fr340_aviso_forzado_una_linea` con el texto del contrato.

  (FR-330, FR-331, FR-336 a FR-338, FR-340, FR-343)
- [X] T035 Ejecutar `python -m unittest test_resolubilidad_reporte` y registrar la evidencia roja: `Texto` y `AvisoForzado` fallan (envolver en las pruebas el `NotImplementedError` de T017 con `self.fail`); `CodigosDeSalida` y `VerificarSinPartida` probablemente pasan ya (el DTO y `verificar` existen): anotar que fallarían si `codigo_salida` cambiara el mapeo o si `verificar` iniciara la partida. (IX)
- [X] T036 [US1] Completar `Logica/ReporteVerificacion.py` con los textos exactos de [contracts/reporte-verificacion.md](contracts/reporte-verificacion.md): encabezado por caso, orden numerado con `(llave de salida)`, líneas `Motivo:`, `Puertas bloqueadas:` con el texto por tipo, `Salas alcanzables (n): …`, `Salas no alcanzables: n`, y `aviso_forzado`. Solo a partir del resultado: sin hora, rutas ni contadores. (FR-335 a FR-338, FR-340)
- [X] T037 Ejecutar `python -m unittest test_resolubilidad_reporte`. **Terminado**: todo pasa.

**Punto de control**: `lineas_reporte(r)` y `r.codigo_salida()` son todo lo que necesita `--verificar`.

---

## Grupo F: Datos y solicitudes (US3, US5)

**Objetivo**: las tres fuentes dan lo mismo, con 0 solicitudes si las llaves están guardadas, y errores de datos claros con código 2.

- [X] T038 [P] [US5] Crear `test_resolubilidad_datos.py`:
  - Clase `Solicitudes`: `test_fr341_llaves_guardadas_cero_solicitudes` (con `ClientePersistente` en carpeta temporal: una primera sesión obtiene las llaves; en una sesión nueva, `verificar` no agrega llamadas `("llaves", …)` y el contador no cambia); `test_fr341_sin_llaves_solo_la_consulta_de_la_009` (exactamente una llamada `("llaves", id)`); `test_fr341_nunca_pide_contenido` (ninguna llamada `obtener_contenido` en `HttpConfigurable.llamadas`).
  - Clase `ErroresDeDatos`: `test_fr343_servicio_sin_respuesta` (`fallo_llaves="sin_respuesta"`: `resoluble is None`, código 2, el motivo nombra la cripta); `test_fr343_offline_sin_llaves_sin_solicitudes` (`ClienteOffline` sobre una caché sin llaves); `test_fr343_cripta_inexistente`; `test_fr343_h4_5_sala_de_salida_inexistente` (`HttpConfigurable(sala_salida=<id sin sala>)`: código 2 y «Datos inválidos»).
  - Clase `CasosLimite` (casos límite de `spec.md` que no tenían prueba): `test_fr333_salida_a_sala_inexistente_se_ignora` (una salida apunta a un id sin sala: se ignora, la sala no aparece en `salas_alcanzables` y el resto del resultado no cambia); `test_fr343_ubicacion_de_llave_en_sala_inexistente_es_error_de_datos` (la consulta de llaves trae una sala que no existe: la 009 la rechaza y `verificar` da `resoluble is None`, código 2, sin resultado inventado); `test_fr339_cambio_de_version_entre_verificar_y_la_partida` (con `ClientePersistente`: `verificar` con la versión `v1` es resoluble; el servicio publica `v2` con la puerta de la salida pidiendo una llave inexistente; una partida nueva vuelve a verificar con los datos de `v2` y no inicia sin `forzar`).

  (FR-341, FR-343, SC-003, SC-004)
- [X] T039 [P] [US3] Ampliar `test_resolubilidad_determinismo.py`: clase `Fuentes` con `test_fr342_h3_4_http_offline_y_solo_local_dan_lo_mismo` (`ServicioCripta` sobre `HttpConfigurable`, `ClienteOffline` tras guardar con `ClientePersistente`, y `FuenteSoloLocal`: resultados iguales campo por campo); y en `Determinismo`, `test_fr335_h3_3_con_y_sin_contenido_guardado` (precargar todas las salas y verificar de nuevo: resultado igual). (FR-335, FR-342)
- [X] T040 Ejecutar `python -m unittest test_resolubilidad_datos test_resolubilidad_determinismo`. Como el algoritmo y `verificar` ya existen, varias pruebas pueden pasar a la primera: por cada una, anotar en «Evidencia en rojo» qué aserción fallaría y con qué cambio (por ejemplo, «fallaría si `verificar` llamara a `ubicacion_llaves` aunque reciba `llaves`»). Registrar como rojo solo lo que falle de verdad. (IX)
- [X] T041 [US5] Corregir en `Logica/VerificacionResolubilidad.py` lo que haya fallado en T040 (por ejemplo, la traducción de un error de datos). Si la corrección exige tocar un adaptador, hacerlo solo en `adaptadores/servicioCripta.py` o `adaptadores/fuente_solo_local.py` y anotarlo. Si todo pasó en T040, marcar la tarea como «sin cambios» con la explicación. (FR-341 a FR-343)
- [X] T042 Ejecutar `python -m unittest test_resolubilidad_datos test_resolubilidad_determinismo`. **Terminado**: todo pasa.

**Punto de control**: FR-341 a FR-343 cubiertos con las tres fuentes.

---

## Grupo G: Inicio de partida y `--forzar` (US4)

**Objetivo**: la cripta no resoluble no inicia sin `--forzar` y no deja log; con `--forzar` inicia con aviso solo al iniciar; sin llaves o con datos inválidos inicia con aviso ([research.md §7](research.md), [data-model.md §5](data-model.md)).

- [X] T043 [P] [US4] Crear `test_resolubilidad_inicio.py` (con `EstadoJuegoServicio` sobre `ServicioCripta` + API falsa v2 y `unittest.mock.patch` sobre `AlmacenLogTexto.abrir` para espiar el log):
  - Clase `Inicio`: `test_fr339_no_resoluble_no_inicia_y_no_crea_log` (B-R1 sin `forzar`: lanza `CriptaNoResoluble` cuyo `str` contiene `NO RESOLUBLE`, `iniciado is False`, `abrir` no se llamó); `test_fr339_resoluble_inicia_sin_aviso`; `test_fr339_fr313_sin_llaves_sigue_con_aviso` (`fallo_llaves="sin_respuesta"`: inicia, `avisoLlaves` no `None`, `avisoResolubilidad is None`); `test_fr339_h4_5_datos_invalidos_inicia_con_aviso` (sala de salida inexistente con llaves válidas: inicia y `avisoResolubilidad` termina con «La verificación de resolubilidad no está disponible.»); `test_fr339_replay_y_partida_cargada_no_verifican` (`iniciarJuego(..., pedir_llaves=False)` sobre B-R4 inicia con `resultadoVerificacion is None`; `restaurar_estado` deja los dos atributos en `None`); `test_fr339_reintento_tras_no_resoluble` (después de `CriptaNoResoluble`, `iniciarJuego` con `forzar=True` sobre el mismo objeto funciona).
  - Clase `Forzar`: `test_fr340_forzar_inicia_con_aviso_solo_al_iniciar` (B-R1 con `forzar=True`: inicia, `avisoResolubilidad() == aviso_forzado(resultado)`, y el aviso no aparece en `ultimosMensajes()` ni en el log después de una acción); `test_fr340_forzar_sin_efecto_en_resoluble`.
  - Clase `MismaOperacion`: `test_fr344_inicio_y_verificar_dan_el_mismo_resultado` (`logica.resultadoVerificacion` igual a `servicio.verificar(...)` en B-R3, y con `patch` se comprueba que `iniciarJuego` llamó a `VerificacionResolubilidad.verificar` con `llaves=` las de la partida).

  (FR-313, FR-339, FR-340, FR-344, SC-005)
  - **Agregado (pendiente del grupo F, T040)**: `Inicio.test_fr339_cambio_de_version_la_partida_nueva_no_inicia_sin_forzar`: con `ClientePersistente`, la verificación de la versión `v1` es resoluble; una partida nueva sobre la versión `v2` (la puerta de la salida pide una llave inexistente) no inicia sin `forzar` y sí inicia con `forzar`, con aviso.
- [X] T044 [P] [US4] En `test_resolubilidad_apendice_b.py`, `CasosB.test_b_r4_fr339_no_inicia_sin_forzar`: ejecutar el paso `("iniciar_sin_forzar",)` del guion de B-R4 con `EstadoJuegoServicio.iniciarJuego`: lanza `CriptaNoResoluble`, la partida no inicia, `AlmacenLogTexto.abrir` no se llamó y el mensaje es el reporte (contiene `itm_llave_perdida`). (B-R4, FR-339)
- [X] T045 [P] [US4] En `test_resolubilidad_datos.py`, `Solicitudes.test_fr341_inicio_reutiliza_las_llaves_de_la_partida`: una partida nueva hace una sola llamada `("llaves", id)` en total y `ubicacion_llaves` se invoca una sola vez (la verificación no la repite). (FR-341)
- [X] T046 Ejecutar `python -m unittest test_resolubilidad_inicio test_resolubilidad_apendice_b test_resolubilidad_datos` y registrar la evidencia roja: las de `Inicio`, `Forzar`, `MismaOperacion` y B-R4 fallan por aserción porque `forzar` todavía no tiene efecto y `iniciarJuego` no verifica. `test_fr339_fr313_sin_llaves_sigue_con_aviso` y `test_fr341_inicio_reutiliza_las_llaves_de_la_partida` pueden pasar ya: anotar qué aserción fallaría. (IX)
- [X] T047 [US4] En `Logica/EstadoJuegoLogica.py`, `iniciarJuego`: al empezar, `resultadoVerificacion` y `avisoResolubilidad` en `None`; después de `self.obtenerLlaves()` y **antes** de `self.iniciado = True`, aplicar las transiciones de [data-model.md §5](data-model.md): sin llaves no verifica; con llaves, `verificar(self.comunicacion, cripta, llaves=self.llaves)`; resoluble sigue; no resoluble con `forzar` → `avisoResolubilidad = aviso_forzado(resultado)`; no resoluble sin `forzar` → `raise CriptaNoResoluble(resultado)`; error de datos → `avisoResolubilidad = <motivo_error> + " La verificación de resolubilidad no está disponible."`. `pedir_llaves=False` no verifica. (FR-339, FR-340, FR-344)
- [X] T048 [US4] En `Servicio/EstadoJuegoServicio.py`, comprobar que `iniciarJuego` deja pasar `CriptaNoResoluble` **antes** de `_abrirLog` y que `AlmacenLogTexto(nombre_log).comprobar_nombre()` no crea archivos; ajustar solo si la prueba lo exige y anotar el resultado. (FR-339)
- [X] T049 Ejecutar `python -m unittest test_resolubilidad_inicio test_resolubilidad_apendice_b test_resolubilidad_datos` y la suite de la línea base. **Terminado**: todo pasa, incluidos los cuatro casos B-R.

**Punto de control**: las historias US1 a US5 funcionan juntas.

---

## Grupo H: Medición (US6)

**Objetivo**: bloque `--bench resolubilidad` con la alternativa descartada ([contracts/bench-resolubilidad.md](contracts/bench-resolubilidad.md), [research.md §9](research.md)).

- [X] T050 [P] [US6] En `test_resolubilidad_determinismo.py`, clase `CadenaSintetica`: `test_fr346_cadena_determinista_por_semilla` (dos llamadas con la misma semilla dan lo mismo; con otra semilla cambian los ids); `test_fr346_cadena_es_resoluble_con_n_llaves` (n = 50: resoluble, `orden` con n llaves incluida la de salida, en el orden de la cadena); `test_fr346_ids_no_siguen_la_cadena` (el orden de ids no coincide con el de la cadena). (FR-346, V)
- [X] T051 Ejecutar `python -m unittest test_resolubilidad_determinismo` y registrar la evidencia roja de `CadenaSintetica` (falla por `self.fail`: `esqueleto_llaves_encadenadas` no existe). (IX)
- [X] T052 [US6] En `tests_labs/cripta_sintetica.py`, `esqueleto_llaves_encadenadas(n, semilla) -> (esqueleto, llaves, llave_salida, sala_salida)` según [data-model.md §7](data-model.md): pasillo de n salas y una lateral por sala; la puerta i → i+1 (en los dos sentidos) se abre con `k_<j>`, ubicada en la lateral de la sala i; los nombres `j` y el orden de las laterales se barajan con `random.Random(semilla)`; la llave de salida en la lateral de la última sala. `llaves` como lista de tuplas `(id, sala, None)`. Sin tamaños fijos. (FR-346, V)
- [X] T053 [US6] Crear `bench/resolubilidad.py` con `ejecutar(filas: list) -> bool` y las secciones A a D del contrato: A (incremental y `verificar_repetida` de `tests_labs/referencia_resolubilidad.py`, n = 300 y 3 000, mediana de 5; la repetida con n = 3 000 con 1 repetición si la primera supera 10 s, anotado en la fila; falla si los resultados difieren); B (búsqueda binaria de `IndiceLlaves` frente a búsqueda lineal escrita en el bench, K = 100, 1 000, 10 000; informativa); C (incremental en la cadena con n = 5 000 y en la rejilla de 70 × 70 con `fraccion_cerradas=0.15` y llaves asignadas por semilla; falla si supera 200 ms); D (razón t(3 000)/t(300) de cada estrategia; falla si la de la incremental supera 20). Mide con `time.perf_counter_ns` sobre la función pura, con `MapaCripta` y `UbicacionLlavesDTO` ya construidos. Sin red, vista ni caché del usuario. (FR-345, FR-346, VII)
- [X] T054 [US6] Registrar el bloque en `bench/__init__.py` (`("resolubilidad", resolubilidad.ejecutar)` en `BLOQUES`, indicador `cumple_resolubilidad` y su línea en el resumen: «Resolubilidad (FR-345, FR-346): CUMPLE.» o el motivo), y mencionar `resolubilidad` en la ayuda de `--bench` de `main.py` (solo ese texto). (VII)
- [X] T055 [US6] En `tests_labs/sin_red.py`, agregar las pruebas de la capacidad (`test_mapa_con_llaves`, `test_indice_llaves`, `test_resolubilidad_regla`, `test_resolubilidad_apendice_b`, `test_resolubilidad_determinismo`, `test_resolubilidad_datos`, `test_resolubilidad_inicio`, `test_resolubilidad_reporte`). (SC-002, IX)
- [X] T056 Con la máquina libre, ejecutar `python main.py --bench resolubilidad` y `python -m tests_labs.sin_red`. Guardar la salida del bench (cabecera con Python, sistema, fecha y semilla) para `mediciones.md`. **Terminado**: el bench termina con 0 (o se anota con honestidad qué criterio no se cumple) y `sin_red` pasa. (FR-345, FR-346, SC-006, SC-007)

**Punto de control**: el bench muestra las dos estrategias, el límite y el crecimiento.

---

## Grupo I: Cierre

**Propósito**: medición manual, documentos, trazabilidad, revisión final. Los documentos van en tareas aparte del código.

- [X] T057 Medir a mano la cripta publicada más grande (paso 3 de `quickstart.md`): con su caché vigente en `datos_cripta/`, `crear_fuente_solo_local` y `verificar(fuente, <id>)` cronometrado con `time.perf_counter_ns` (mediana de 5), con un guion temporal en la carpeta temporal de la sesión (no en el repositorio). Si la caché no está, indicarlo a Scott en lugar de descargarla: descargarla gasta solicitudes. Anotar id, salas, tiempo y solicitudes (0). (FR-345, SC-006)
- [X] T058 [P] Crear `specs/003-verificacion-resolubilidad/mediciones.md`: cabecera de la máquina, tablas de las secciones A a D de T056, la medición manual de T057, el estado de FR-345, FR-346, SC-006 y SC-007, y la conclusión (se mantiene el recorrido incremental o, si una medición lo contradice, qué cambia). (VII)
- [X] T059 [P] Agregar la sección 003 a `DECISIONES.md` con enlaces a `spec.md` y `plan.md`: para cada decisión (llave en la arista, oleadas, `MonticuloMinimo`, `IndiceLlaves`, dónde vive cada parte, `CriptaNoResoluble` antes del log, códigos 0/1/2), si coincide con el plan y qué prueba o medición la respalda. Incluir lo anotado en T009 y T041 si hubo cambios. (X)
- [X] T060 [P] Actualizar `DOCUMENTACION_API.md`: `AristaMapaDTO.llave` y `AristaCripta.llave`; `obtener_sala_inicial` y `obtener_llave_salida` en el contrato y en las fuentes; `verificar` (Logica y Servicio), `ResultadoVerificacion`, `PasoLlaveDTO`, `BloqueoDTO`, `CriptaNoResoluble`, `iniciarJuego(..., forzar)`, `avisoResolubilidad()`; códigos 0/1/2. (IV, IX)
- [X] T061 [P] Actualizar `README.md` con una línea sobre la capacidad 003, `python main.py --bench resolubilidad` y que `--verificar`/`--forzar` los conecta la capacidad de Fernanda sobre esta interfaz. (VII)
- [X] T062 [P] Completar la matriz de `specs/003-verificacion-resolubilidad/quickstart.md` con los nombres reales (`archivo: Clase.método`) tomados de los archivos que existen; comprobar que ningún FR-330 a FR-346 ni escenario H1-1 a H6-2 queda sin prueba o medición, y que B-R1 a B-R4 están. Si `research.md` §1 necesita la nota de T009, agregarla aquí. (IX)
- [X] T063 Comprobar con búsqueda (paso 5 de `quickstart.md`) que `DTO/ResultadoVerificacionDTO.py`, `Logica/IndiceLlaves.py`, `Logica/VerificacionResolubilidad.py`, `Logica/ReporteVerificacion.py`, `bench/resolubilidad.py`, `tests_labs/referencia_resolubilidad.py` y los cambios en `MapaDTO.py`, `MapaCripta.py`, `servicioCripta.py`, `fuente_solo_local.py`, `EstadoJuegoLogica.py` y `EstadoJuegoServicio.py`: no importan `heapq`, `bisect`, `collections` ni `networkx`; no usan `dict`/`set` como índice ni `sorted()`/`.sort()`; no contienen ids ni tamaños de una cripta concreta; `Logica/` y `DTO/` no importan adaptadores. Comprobar con `git diff --stat` que `AlmacenPartidaBinario.py`, `EstadoGuardadoDTO.py` y `codec_partida.py` no cambiaron, y que todos los archivos nuevos o modificados están en CRLF. (I, IV, V)
- [X] T064 Ejecutar `python -m unittest discover -p "test_*.py"`, `python -m tests_labs.sin_red` y `python main.py --bench`. Comparar con la línea base de T002 y registrar cualquier fallo sin ocultarlo. (IX)
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

### T011 — 2026-11-08 — `python -m unittest -v test_resolubilidad_reporte` (clase `Contrato`, antes de crear o tocar código del grupo B)

Resultado: `Ran 6 tests`, `FAILED (failures=6)`, 0 errores. Todas fallan por aserción (`self.fail` o `assertTrue`), ninguna por error de importación.

| Prueba | Aserción |
|---|---|
| `test_fr344_firmas_de_la_interfaz` | `Logica.VerificacionResolubilidad todavía no existe: No module named 'Logica.VerificacionResolubilidad'` |
| `test_fr331_codigo_salida` | `DTO.ResultadoVerificacionDTO todavía no existe: No module named 'DTO.ResultadoVerificacionDTO'` |
| `test_fr344_campos_del_resultado` | `DTO.ResultadoVerificacionDTO todavía no existe` |
| `test_fr339_cripta_no_resoluble_es_runtime_error` | `Logica.VerificacionResolubilidad todavía no existe` |
| `test_fr344_fuente_entrega_sala_inicial_y_llave_salida` | `False is not true : FuenteCripta no declara obtener_sala_inicial` |
| `test_fr343_cuerpo_provisional_devuelve_codigo_2` | `Logica.VerificacionResolubilidad todavía no existe` |

Ninguna pasó a la primera.

### T022 — 2026-11-08 — `python -m unittest -v test_indice_llaves` (antes de crear `Logica/IndiceLlaves.py`)

Resultado: `Ran 8 tests`, `FAILED (failures=8)`, 0 errores. Las 8 pruebas, (a) a (h), fallan por la misma aserción: `self.fail("Logica.IndiceLlaves todavía no existe: No module named 'Logica.IndiceLlaves'")`. Ninguna pasó a la primera ni falló por error de importación.

### T029 — 2026-11-08 — `python -m unittest -v test_resolubilidad_regla test_resolubilidad_apendice_b test_resolubilidad_determinismo` (cuerpo provisional de T016; antes de T030)

Resultado: `Ran 26 tests`, `FAILED (failures=26)`, 0 errores. Todas fallan por aserción porque `verificar_resolubilidad` y `verificar` devuelven `resoluble is None`:

| Aserción | Pruebas |
|---|---|
| `None is not True` | 14: las de `Regla` que esperan resoluble (H1-1, sala inicial = salida, no exige puerta, H1-3, H1-6 —falla en su primera parte—, una llave abre varias puertas, H2-2, H2-3, llave de salida una vez), `CasosB` B-R2 y B-R3, y `Determinismo` H3-2, orden de la respuesta, suelo antes que enemigo, dos ejecuciones |
| `None is not False` | 10: H1-4, H1-5, salas alcanzables (FR-337), ciclo a través de otras puertas, H1-7, varios bloqueos, puerta sin llave nunca se cruza, B-R1, B-R4 y la primera parte de H1-6 |
| `Lists differ: [] != [BloqueoDTO(1, 'este', 2, None, [], 'SIN_LLAVE')]` | 1: `Bloqueos.test_fr338_puerta_sin_llave_es_bloqueo_sin_llave` (no comprueba `resoluble` primero) |
| `unexpectedly None : semilla 0: no se verificó` | 1: `Equivalencia.test_fr335_fr346_incremental_igual_a_repetida_en_criptas_al_azar` |

Ninguna pasó a la primera. Refuerzos hechos al escribirlas, para que dos resultados provisionales iguales no basten: `test_fr335_dos_ejecuciones_iguales`, `test_fr335_orden_de_la_respuesta_no_importa` y `test_b_r3_fr335_dos_ejecuciones_mismo_orden` comprueban `resoluble is True` antes de comparar los dos resultados; `Equivalencia` comprueba `resoluble is not None` en cada semilla antes de compararlo con el oráculo.

**Cordura de las expectativas**: con un guion temporal (fuera del repositorio) que pone `verificar_repetida` en lugar de las dos funciones provisionales, las 26 pruebas pasan. Lo que esperan es coherente con el oráculo, que deriva la regla de `spec.md`. En 20 criptas al azar, el oráculo produce 10 resolubles y 10 no resolubles, y aparecen los 4 tipos de bloqueo y las 4 causas.

### T035 — 2026-11-08 — `python -m unittest -v test_resolubilidad_reporte` (antes de completar `Logica/ReporteVerificacion.py`)

Resultado: `Ran 16 tests`, `FAILED (failures=7)`, 0 errores. Las 6 de `Contrato` (grupos B y D) siguen pasando. De las 10 nuevas:

| Prueba | Resultado | Aserción o explicación |
|---|---|---|
| `Texto.test_fr336_resoluble_muestra_orden_con_sala_y_enemigo` | FAIL | `self.fail("lineas_reporte todavía no implementa este caso: se completa en el grupo E (T036)")` (envuelve el `NotImplementedError` de T017) |
| `Texto.test_fr337_lista_salas_alcanzables` | FAIL | La misma |
| `Texto.test_fr338_texto_por_tipo_de_bloqueo` | FAIL | La misma |
| `Texto.test_fr338_texto_por_causa` | FAIL | La misma |
| `Texto.test_fr338_b_r1_reporte_completo` | FAIL | La misma |
| `Texto.test_fr335_mismo_resultado_mismo_reporte` | FAIL | La misma (prueba agregada: dos verificaciones de B-R1 dan el mismo texto carácter por carácter) |
| `AvisoForzado.test_fr340_aviso_forzado_una_linea` | FAIL | `self.fail("aviso_forzado todavía no está implementado: se completa en el grupo E (T036)")` |
| `Texto.test_fr343_reporte_de_error` | **pasa a la primera** | La rama de error de datos ya la implementó T017 (entrega temprana). Fallaría si `lineas_reporte` cambiara el encabezado `Verificación de la cripta <id>: NO SE PUDO VERIFICAR.` o no copiara `motivo_error` tal cual en la segunda línea |
| `CodigosDeSalida.test_fr331_resoluble_0_no_resoluble_1_error_2` | **pasa a la primera** | `codigo_salida()` existe desde T012 y el algoritmo desde T030. Fallaría si `codigo_salida` cambiara el mapeo 0/1/2 (por ejemplo, si devolviera 1 también para `resoluble is None`) o si `verificar` dejara de devolver `resoluble=None` cuando el servicio no responde |
| `VerificarSinPartida.test_fr330_verificar_no_inicia_partida_ni_crea_log_ni_vista` | **pasa a la primera** | `EstadoJuegoServicio.verificar` existe desde T019 y no inicia partida. Fallaría si `verificar` llamara a `iniciarJuego` (quedaría `iniciado = True` y se llamaría `AlmacenLogTexto.abrir`), si abriera el log, o si creara `VistaConsola` (el parche lanza `AssertionError`) |

### T040 — 2026-11-08 — `python -m unittest -v test_resolubilidad_datos test_resolubilidad_determinismo`

Resultado: `Ran 17 tests`, `OK`. **No hubo rojo**: el algoritmo y `verificar` existen desde T030 a T032, y las 12 pruebas nuevas (10 de `test_resolubilidad_datos` y 2 de `test_resolubilidad_determinismo`) pasan a la primera. No se registra ningún rojo inventado. Para cada una se comprobó que la aserción **puede** fallar: un guion fuera del repositorio aplica con `mock.patch` una mutación concreta, corre la prueba y verifica que falla. El código real no se tocó.

| Prueba | Fallaría si… (mutación aplicada) | Resultado con la mutación |
|---|---|---|
| `Solicitudes.test_fr341_llaves_guardadas_cero_solicitudes` | `verificar` volviera a pedir las llaves a la red aunque estén guardadas | FALLA: `http.llamadas` trae una llamada `("llaves", …)` además del arranque |
| `Solicitudes.test_fr341_sin_llaves_solo_la_consulta_de_la_009` | `verificar` pidiera además el contenido de una sala | FALLA: aparece `("contenido", …)` |
| `Solicitudes.test_fr341_nunca_pide_contenido` | La misma | FALLA en B-R1 |
| `ErroresDeDatos.test_fr343_servicio_sin_respuesta` | Sin llaves, `verificar` siguiera con una lista vacía (resultado inventado) | FALLA: `False is not None` |
| `ErroresDeDatos.test_fr343_offline_sin_llaves_sin_solicitudes` | La misma | FALLA: `False is not None` |
| `ErroresDeDatos.test_fr343_cripta_inexistente` | `existe_cripta` respondiera siempre que sí | FALLA: `True is not None` |
| `ErroresDeDatos.test_fr343_h4_5_sala_de_salida_inexistente` | `_existe` no comprobara que la sala exista | FALLA (error `IndexError`) |
| `CasosLimite.test_fr333_salida_a_sala_inexistente_se_ignora` | La misma | FALLA (error `IndexError`) |
| `CasosLimite.test_fr343_ubicacion_de_llave_en_sala_inexistente_es_error_de_datos` | Sin llaves válidas, `verificar` siguiera con una lista vacía | FALLA: `False is not None` |
| `CasosLimite.test_fr339_cambio_de_version_entre_verificar_y_la_partida` | La verificación reutilizara el resultado de la versión anterior | FALLA: `True is not False` |
| `Fuentes.test_fr342_h3_4_http_offline_y_solo_local_dan_lo_mismo` | `FuenteSoloLocal.obtener_llave_salida` devolviera `None` | FALLA: la lectura solo local da `LLAVE_SALIDA_INEXISTENTE` y las otras fuentes no |
| `DeterminismoConContenido.test_fr335_h3_3_con_y_sin_contenido_guardado` | El resultado cambiara cuando ya se trajo el contenido de las salas | FALLA: `salas_no_alcanzables` difiere |

Notas:
- **Primer intento del guion de mutaciones**: dio falsos «no detectada» por un defecto del guion, no de las pruebas. `test_resolubilidad_datos` importa `verificar` por nombre (había que parchear también ese nombre), y la primera importación ocurría dentro de un parche. Corregido el guion, todas detectan su mutación.
- **«Pide contenido» frente a `test_fr341_llaves_guardadas_cero_solicitudes`**: esa mutación no se detecta en esta prueba porque en la primera sesión el contenido pedido queda guardado y en la segunda sale del disco sin solicitud. La detectan las otras dos pruebas de `Solicitudes`; esta prueba detecta la regresión que le corresponde (volver a pedir las llaves).
- **Arranque de una sesión nueva**: con las llaves guardadas, una sesión nueva con `ClientePersistente` pide `("criptas", None)` y `("datos", "cripta-01")`. Es el arranque de la Parte I (lista de criptas y datos generales con la validación de versión) y no lo agrega la verificación. La prueba exige exactamente esas dos llamadas y ninguna de llaves, salas o contenido. SC-003 dice «0 solicitudes» de forma literal; ver T041.
- **Cambio de versión (`test_fr339_…`)**: se prueba sobre la operación `verificar` que usa el inicio de partida (FR-344), con una sesión nueva sobre la versión `v2`. La parte «la partida no inicia sin `forzar`» depende de la verificación al iniciar, que se implementa en el grupo G (T047); la cubren `Inicio.test_fr339_no_resoluble_no_inicia_y_no_crea_log` (T043) y, para este caso, una aserción que se agrega en T043.
- **Nombres**: la prueba con y sin contenido quedó en la clase `DeterminismoConContenido` (necesita la preparación con servicio y red bloqueada) y no en `Determinismo`. T062 pone el nombre real en la matriz.

### T041 — 2026-11-08 — sin cambios

Nada falló en T040, así que no se tocó `Logica/VerificacionResolubilidad.py` ni ningún adaptador. Queda un punto de **especificación**, no de código: SC-003 dice «Con las llaves guardadas, `--verificar` hace 0 solicitudes», pero toda sesión nueva hace las 2 solicitudes de arranque de la Parte I (lista de criptas y datos generales para validar la versión), antes y fuera de la verificación. FR-341 sí lo describe bien («no hace solicitudes más allá de la consulta de llaves y de la descarga del mapa existente»). Si se quiere alinear SC-003, va en un commit de especificación aparte (principio X).

### T046 — 2026-11-08 — `python -m unittest -v test_resolubilidad_inicio test_resolubilidad_apendice_b.CasosB.test_b_r4_fr339_no_inicia_sin_forzar test_resolubilidad_datos.Solicitudes.test_fr341_inicio_reutiliza_las_llaves_de_la_partida` (antes de tocar `Logica/EstadoJuegoLogica.py`)

Resultado: `Ran 12 tests`, `FAILED (failures=10)`, 0 errores.

| Prueba | Resultado | Aserción |
|---|---|---|
| `Inicio.test_fr339_no_resoluble_no_inicia_y_no_crea_log` | FAIL | `CriptaNoResoluble not raised` |
| `Inicio.test_fr339_resoluble_inicia_sin_aviso` | FAIL | `unexpectedly None : iniciarJuego no verificó la cripta` |
| `Inicio.test_fr339_h4_5_datos_invalidos_inicia_con_aviso` | FAIL | `unexpectedly None : con datos inválidos la partida debe iniciar con aviso` |
| `Inicio.test_fr339_replay_y_partida_cargada_no_verifican` | FAIL | `unexpectedly None : la partida forzada debía tener aviso antes de restaurar` (refuerzo: sin él, la parte de restaurar pasaría con atributos que nunca se llenaron) |
| `Inicio.test_fr339_reintento_tras_no_resoluble` | FAIL | `CriptaNoResoluble not raised` |
| `Inicio.test_fr339_cambio_de_version_la_partida_nueva_no_inicia_sin_forzar` | FAIL | `CriptaNoResoluble not raised` |
| `Forzar.test_fr340_forzar_inicia_con_aviso_solo_al_iniciar` | FAIL | `unexpectedly None : iniciarJuego no verificó la cripta` |
| `Forzar.test_fr340_forzar_sin_efecto_en_resoluble` | FAIL | La misma |
| `MismaOperacion.test_fr344_inicio_y_verificar_dan_el_mismo_resultado` | FAIL | `Expected 'verificar' to have been called once. Called 0 times.` |
| `CasosB.test_b_r4_fr339_no_inicia_sin_forzar` | FAIL | `CriptaNoResoluble not raised` |
| `Inicio.test_fr339_fr313_sin_llaves_sigue_con_aviso` | **pasa a la primera** | Hoy no hay verificación, así que tampoco se verifica sin llaves. Fallaría si la verificación al iniciar se hiciera también sin llaves: `resultadoVerificacion` dejaría de ser `None` y aparecería un `avisoResolubilidad`. Comprobado después de T047 con una mutación fuera del repositorio (`_verificarAlIniciar` que verifica sin mirar `self.llaves`): FALLA en `assertIsNone(logica.resultadoVerificacion)` |
| `Solicitudes.test_fr341_inicio_reutiliza_las_llaves_de_la_partida` | **pasa a la primera** | Hoy el inicio no verifica, así que `ubicacion_llaves` se llama una vez. Fallaría si la verificación al iniciar no recibiera las llaves de la partida y las volviera a pedir. Comprobado después de T047 con una mutación (`verificar(..., llaves=None)`): FALLA con `2 != 1` |

Defecto **de la prueba** corregido después de T047: en `Forzar.test_fr340_forzar_inicia_con_aviso_solo_al_iniciar`, la acción `ESPERAR` daba `ValueError: La sala actual del jugador no está cargada`. Al iniciar, el controlador carga la sala inicial (`obtenerSala`) antes de la primera acción, y la prueba no lo hacía. Se agregó esa línea, igual que hace `jugar_y_exportar` de la 009; no cambia lo que se comprueba.

### T049 — 2026-11-08 — bloqueada por una prueba de la capacidad 009 (resuelto: ver «T049, cierre»)

`test_resolubilidad_inicio`, `test_resolubilidad_apendice_b` y `test_resolubilidad_datos`: `Ran 26 tests`, OK. Suite completa: `Ran 375 tests`, `FAILED (errors=1)`; `tests_labs.sin_red`: 95, 1 error. El error es `test_llaves_partida_cargada.OtraCripta.test_fr325_e_restaurar_otra_cripta_no_arrastra_las_llaves_anteriores` (capacidad 009): sus criptas de prueba «cripta-A» y «cripta-B» no tienen la llave de salida de los datos generales (`itm_llave_negra` de `HttpFalso`), así que ahora son **no resolubles** (`LLAVE_SALIDA_INEXISTENTE`) y `iniciarJuego` lanza `CriptaNoResoluble` (FR-339), como pide la spec. No se modificó esa prueba (es de otro grupo): queda a decisión de Scott.

### T049, cierre — 2026-11-08 — decisión de Scott: opción A

- **Prueba de la 009 tocada**: `test_llaves_partida_cargada.OtraCripta.test_fr325_e_restaurar_otra_cripta_no_arrastra_las_llaves_anteriores`. Sus criptas «cripta-A» y «cripta-B» no tienen la llave de salida (`itm_llave_negra`); con la regla nueva (FR-339) son **no resolubles** (`LLAVE_SALIDA_INEXISTENTE`) e `iniciarJuego` lanzaba `CriptaNoResoluble`. La prueba trata de las llaves al cargar una partida (FR-325), no de resolubilidad, así que se inicia con `forzar=True`.
- **Cambio mínimo en `test_llaves_partida_cargada.py`**: el ayudante `jugar_y_exportar` gana el parámetro opcional `forzar=False` y lo pasa a `iniciarJuego`; en esa prueba, `forzar=True` en la llamada con «cripta-B» y en la llamada directa a `logica.iniciarJuego("cripta-A", 1)`, con una línea de comentario que explica por qué. Las demás pruebas de la 009 no cambian (usan el valor por defecto). No se tocó `Logica/EstadoJuegoLogica.py` ni ninguna otra prueba.
- **Resultado**: `test_resolubilidad_inicio`, `test_resolubilidad_apendice_b` y `test_resolubilidad_datos`: 26 OK. `test_llaves_partida_cargada`: 10 OK. Suite completa: 375, OK, 0 fallas. `tests_labs.sin_red`: 95, 0 fallos y 0 errores.

### T051 — 2026-11-08 — `python -m unittest -v test_resolubilidad_determinismo.CadenaSintetica` (antes de crear `esqueleto_llaves_encadenadas`)

Resultado: `Ran 3 tests`, `FAILED (failures=3)`, 0 errores. Las tres (`test_fr346_cadena_determinista_por_semilla`, `test_fr346_cadena_es_resoluble_con_n_llaves` y `test_fr346_ids_no_siguen_la_cadena`) fallan por la misma aserción: `self.fail("esqueleto_llaves_encadenadas todavía no existe: module 'tests_labs.cripta_sintetica' has no attribute 'esqueleto_llaves_encadenadas'")`. Ninguna pasó a la primera.

### T056 — 2026-11-08 — `python main.py --bench resolubilidad` y `python -m tests_labs.sin_red` (máquina libre, sin nada más corriendo)

Salida completa del bench (para copiarla a `mediciones.md` en T058). Una sola corrida, sin ruido evidente: las medianas del incremental son coherentes entre secciones (34 ms con n = 3 000 en A; 59 ms con n = 5 000 en C).

```text
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-08 19:05 · semilla 2026
... midiendo resolubilidad

Resolubilidad (A): incremental frente a recorrido repetido, cadena de llaves encadenadas
  verificación: n = 300: el incremental y la repetida dan el mismo resultado (300 llaves en el orden) OK
  n = 300 (600 salas): incremental (elegido)                         2.71 ms  mediana de 5
  n = 300 (600 salas): repetida (oráculo, descartada)                198.41 ms  mediana de 5
  verificación: n = 3,000: el incremental y la repetida dan el mismo resultado (3,000 llaves en el orden) OK
  n = 3,000 (6,000 salas): incremental (elegido)                     34.29 ms  mediana de 5
  n = 3,000 (6,000 salas): repetida (oráculo, descartada)            220,792.58 ms  1 repetición (la primera superó 10 s)

Resolubilidad (B): índice de llaves, búsqueda binaria frente a búsqueda lineal (INFORMATIVA)
  verificación: K = 100: binaria y lineal dan la misma posición      OK
  K = 100, 100 consultas: búsqueda binaria (elegida)                 44.5 µs  mediana de 5
  K = 100, 100 consultas: búsqueda lineal (descartada)               108.0 µs  mediana de 5
  verificación: K = 1,000: binaria y lineal dan la misma posición    OK
  K = 1,000, 1,000 consultas: búsqueda binaria (elegida)             794.4 µs  mediana de 5
  K = 1,000, 1,000 consultas: búsqueda lineal (descartada)           11.11 ms  mediana de 5
  verificación: K = 10,000: binaria y lineal dan la misma posición   OK
  K = 10,000, 10,000 consultas: búsqueda binaria (elegida)           10.69 ms  mediana de 5
  K = 10,000, 10,000 consultas: búsqueda lineal (descartada)         1,194.44 ms  1 repetición

Resolubilidad (C): límite de 200 ms del incremental (FR-345)
  cadena n = 5,000 (10,000 salas, 5,000 llaves, resoluble)           58.51 ms  mediana de 5; límite 200 ms: CUMPLE
  rejilla 70 × 70 con puertas y llaves al azar (4,900 salas, 1,461 llaves, resoluble) 16.00 ms  mediana de 5; límite 200 ms: CUMPLE

Resolubilidad (D): crecimiento t(3 000) / t(300) (FR-346, SC-007)
  incremental (elegido)                                              12.7  tamaño ×10; límite 20: CUMPLE
  repetida (oráculo, descartada)                                     1,112.8  INFORMATIVA
  Una razón cercana a 10 es crecimiento lineal; cerca de 100, cuadrático. 

Resolubilidad (FR-345, FR-346): CUMPLE.
exit=0
```

Resumen: **CUMPLE** (código de salida 0).
- **A**: resultados iguales en n = 300 y n = 3 000. Incremental: 2,71 ms y 34,29 ms. Repetida: 198,41 ms y 220 792,58 ms (1 repetición: la primera superó 10 s).
- **C**: cadena con n = 5 000, 58,51 ms; rejilla de 70 × 70, 16,00 ms. Las dos por debajo de 200 ms.
- **D**: razón del incremental 12,7 (límite 20); de la repetida, 1 112,8.

Hallazgo para el grupo I (`mediciones.md`, `DECISIONES.md`): la razón de la repetida (1 112,8 con tamaño ×10) es mayor que la «cercana a 100» que preveía el contrato para O(K · (S + E)). El oráculo `verificar_repetida` no es solo «recorrer desde cero en cada oleada»: también averigua si una llave ya se obtuvo con búsquedas lineales sobre listas (`_contiene`), lo que agrega un factor K. Su costo real es cercano a O(K² · (S + E)). Eso no cambia la conclusión (el incremental crece de forma lineal y la alternativa descartada, mucho más rápido). El oráculo no se modificó.

`tests_labs.sin_red`: 178 pruebas con `requests.get` bloqueado (95 de antes + 83 de las 8 pruebas de la capacidad 003), 0 fallos y 0 errores.

### T057 — 2026-11-09 — medición manual en las criptas publicadas (sin red, guion temporal fuera del repositorio)

- **Primer intento (paso 3 de `quickstart.md`, con `FuenteSoloLocal`)**: no sirvió. Primero no había llaves guardadas. Después de que Scott verificó en línea las cinco criptas del catálogo, cripta-06 (la más grande, 300 salas) tenía guardados el mapa, los datos y las llaves, pero no el contenido de sus salas. `ClienteOffline` solo da por existente una cripta completa, así que `verificar` respondía «no está en la lista de criptas guardada en disco». Lo mismo pasaba con cripta-02 y cripta-03. Decisión de Scott: no descargar el contenido (la verificación no lo usa y gasta solicitudes) y medir sin `FuenteSoloLocal`.
- **Fuente más realista sin red**: `ServicioCripta(ClientePersistente(<HTTP que lanza un error>, AlmacenDisco))`. Necesita red en el arranque de la Parte I (`obtener_criptas`, único intento en las cinco criptas, sin escrituras en disco). Se usó en su lugar `ServicioCripta` sobre una subclase temporal de `ClienteOffline` sin el filtro de cripta completa.
- **Resultado**: cripta-06, RESOLUBLE, 2,925 ms (completa) y 0,391 ms (pura). cripta-04, RESOLUBLE. cripta-03 y cripta-02, RESOLUBLES. **cripta-05, NO RESOLUBLE** (no inicia sin `--forzar`). 0 solicitudes; sha1 de `datos_cripta/` igual antes y después. Tabla y reportes completos en [mediciones.md](mediciones.md).
- **Fuera de alcance, para Scott**: el paso 3 de `quickstart.md`, la última sección de `contracts/bench-resolubilidad.md` y research.md §9 («a mano con `--offline` sobre la caché») describen la medición con `FuenteSoloLocal` o `--offline`. No se cambiaron.

### Nota de documentos (separada del código) — 2026-11-09 — razón de la repetida en el contrato

`contracts/bench-resolubilidad.md` (sección D, columna «Alternativa descartada») y `research.md` §9 (tabla de secciones, fila D) decían que la razón t(3 000)/t(300) de la repetida sería «cercana a 100». Se corrigió a lo medido en T056: **1 112,8**. La causa: el oráculo `verificar_repetida`, además de recorrer desde cero en cada oleada, busca con búsquedas lineales (`_contiene`) si una llave ya se obtuvo, y su costo real se acerca a O(K² · (S + E)). Solo cambian esas dos celdas de documentación; el código y el oráculo no se tocaron. `quickstart.md` §2 todavía dice «la de la repetida cerca de 100» y no se cambió en esta tarea.

### T059 a T062 — 2026-11-09 — documentos

- **T059**: sección 003 en `DECISIONES.md` (decisiones del plan con su prueba o medición, T009, T041 y las decisiones de la implementación).
- **T060**: `DOCUMENTACION_API.md`: §2.2, §7 y §8.6 con `obtener_sala_inicial` y `obtener_llave_salida`; §7 con la llave en `esqueleto()`; §7.2 nueva (mapa con llaves, `FuenteCripta`, `verificar`, `ResultadoVerificacion`, `PasoLlaveDTO`, `BloqueoDTO`, `lineas_reporte`, `aviso_forzado`, códigos 0/1/2, `iniciarJuego(..., forzar)`, `avisoResolubilidad()`); §10 con `CriptaNoResoluble`.
- **T061**: una línea en `README.md`.
- **T062**: la matriz de `quickstart.md` lleva los nombres reales. Las 83 pruebas de los 8 archivos aparecen y ninguna citada falta en el código; se corrigieron `DeterminismoConContenido.test_fr335_h3_3_con_y_sin_contenido_guardado` y `Contrato.test_fr343_sin_datos_devuelve_codigo_2`. Se agregó una tabla por escenario: FR-330 a FR-346, H1-1 a H6-2 y B-R1 a B-R4 tienen todos prueba o medición. La parte de consola de algunos escenarios (`--verificar`, `--forzar`, mostrar el aviso) es de la capacidad de Fernanda, y H3-4 prueba «el cliente real» con el HTTP falso. `research.md` §1 no necesitó la nota de T009 (checklist: G3 y G4 pasaron sin cambios). Se alinearon con lo que se hizo en T057 los cuatro textos que la nota de T057 dejaba para Scott: el paso 3 y §2 de `quickstart.md`, la última sección de `contracts/bench-resolubilidad.md` y la última frase de la tabla de `research.md` §9. `spec.md` no se cambió.

### Corrección de documentos — 2026-11-09 — paso 4 de `quickstart.md`

El paso 4 usaba cripta-01, que ya no está en la lista guardada de criptas, y hablaba del cuerpo provisional. Ahora usa cripta-04 (número 3 del menú: código 0, resoluble) y cripta-05 (número 4: código 1, no resoluble), con el texto de `contracts/reporte-verificacion.md`. Queda como paso opcional con red: sin red solo funciona si la cripta está completa en disco.

### T063 — 2026-11-09 — revisión por búsqueda (base: `e47a18a`, padre del primer commit de la 003, `2a31a68`)

Archivos de producción revisados: los 18 que la capacidad crea o modifica según `git diff --stat e47a18a`. Son `DTO/MapaDTO.py`, `DTO/ResultadoVerificacionDTO.py`, `Logica/EstadoGuardadoLogica.py`, `Logica/EstadoJuegoLogica.py`, `Logica/FuenteCripta.py`, `Logica/IndiceLlaves.py`, `Logica/MapaCripta.py`, `Logica/ReporteVerificacion.py`, `Logica/VerificacionResolubilidad.py`, `Servicio/EstadoJuegoServicio.py`, `adaptadores/fuente_solo_local.py`, `adaptadores/servicioCripta.py`, `bench/__init__.py`, `bench/resolubilidad.py`, `main.py`, `tests_labs/cripta_sintetica.py`, `tests_labs/referencia_resolubilidad.py` y `tests_labs/sin_red.py`.

| Comprobación | Resultado |
|---|---|
| `heapq`, `bisect`, `collections`, `networkx` | **Cumple.** Solo hay dos coincidencias, `from collections import deque` en `Logica/EstadoGuardadoLogica.py:10` y en `adaptadores/servicioCripta.py:2`, y las dos ya estaban en `e47a18a` (de la Parte I). Ninguna línea agregada por la capacidad importa esos módulos |
| `sorted()` / `.sort()` | **Cumple.** Las 4 coincidencias son docstrings que dicen que no se usan (`Logica/IndiceLlaves.py:9`, `Logica/VerificacionResolubilidad.py:25`, `bench/resolubilidad.py:15`, `tests_labs/referencia_resolubilidad.py:25`) |
| `dict`/`set` como índice | **Cumple** (revisión a mano de las líneas agregadas). Las coincidencias son f-strings, docstrings y, en `tests_labs/cripta_sintetica.py` y `tests_labs/referencia_resolubilidad.py`, los `dict` del formato crudo del esqueleto de la API (`{"id", "nombre", "salidas"}`), igual que el `esqueleto_rejilla` que ya existía: son registros, no índices. En `adaptadores/servicioCripta.py` la línea agregada lee `datos.get("llave")` de la salida cruda de la API |
| Ids o tamaños de una cripta concreta | **Cumple.** `cripta-0` no aparece en el código de producción. `itm_llave_` aparece solo en `bench/resolubilidad.py:140`, como prefijo de ids sintéticos al azar (`f"itm_llave_{azar.randrange(10 ** 9)}"`) para la sección B. Los números agregados son textos de error o de reporte; los tamaños del bench (`TAMANO_CHICO = 300`, `TAMANO_GRANDE = 3000`, `TAMANO_LIMITE = 5000`, `LADO_REJILLA = 70`, `CANTIDADES_INDICE`) son parámetros sintéticos del contrato, no datos de una cripta |
| `Logica/` y `DTO/` no importan adaptadores | **Cumple**: `grep -rnE "^\s*(from\|import)\s+(adaptadores\|Controlador\|Servicio)" Logica DTO` no encuentra nada |
| `AlmacenPartidaBinario.py`, `EstadoGuardadoDTO.py`, `codec_partida.py` | **Cumple**: `git diff --stat e47a18a` no muestra cambios en ninguno de los tres |
| CRLF en todos los archivos nuevos o modificados por la capacidad | **No cumple en dos documentos.** `specs/003-verificacion-resolubilidad/mediciones.md` (las 191 líneas en LF) y `specs/003-verificacion-resolubilidad/quickstart.md` (las 147 líneas en LF). Los escribió el asistente en T058 y T062 con una herramienta que guarda en LF. La comprobación de entonces (`grep -vc $'\r$'` en Git Bash) daba un falso 0; ahora se contó con Python sobre los bytes. Hace falta convertirlos a CRLF; no se tocaron, como pide T063. Los demás 40 archivos del diff están en CRLF. (`PROMPTS_Scott.md`, también en LF, no es de la capacidad) |

### T064 — 2026-11-09 — suite, `sin_red` y `python main.py --bench` (máquina libre, una cosa a la vez)

- `python -m unittest discover -p "test_*.py"`: **378 pruebas, OK** (0 fallos, 0 errores). Línea base de T002: 295; último registro: 378.
- `python -m tests_labs.sin_red`: **178 pruebas, OK** con `requests.get` bloqueado (0 fallos, 0 errores). Línea base: 95; último registro: 178.
- `python main.py --bench` completo (2026-11-09 01:21): **falla, código de salida 1.** Corta en el bloque `guardado` con `CriptaNoResoluble`, antes de imprimir la tabla, así que no hay cifras de esa corrida:

  ```text
  File "bench/guardado.py", line 54, in ejecutar → bench/juego.py, line 79, in partida_base → line 71, in nuevo_juego
      juego = EstadoJuegoLogica(1, cripta, servicio)
  File "Logica/EstadoJuegoLogica.py", line 128, in _verificarAlIniciar
  Logica.VerificacionResolubilidad.CriptaNoResoluble: Verificación de la cripta sintetica: NO RESOLUBLE.
  Motivo: la llave de salida itm_llave no existe en la cripta.
  Salas alcanzables (25): 1, 2, …, 25
  Salas no alcanzables: 0
  ```

  **Causa (regresión de la 003, igual que la de la 009 en T054)**: la cripta sintética del bench (`ClienteDeBatalla` en `bench/juego.py`) publica la llave de salida `itm_llave` en sus datos generales (`adaptadores/bench_red_mejorado.py:50`), pero `ClienteDeBatalla.obtener_llaves` devuelve `[]` (`bench/juego.py:48-50`). Con FR-339, `EstadoJuegoLogica.__init__` → `iniciarJuego` verifica, la cripta es no resoluble (`LLAVE_SALIDA_INEXISTENTE`) y no inicia sin `forzar`. Afecta a los dos bloques que usan `nuevo_juego`: `guardado` y `ciclo`. `python main.py --bench ciclo` solo falla igual (código 1). T056 no lo vio porque corrió solo `--bench resolubilidad`. **No se corrigió**: hace falta decidir entre que `ClienteDeBatalla.obtener_llaves` ubique `itm_llave` en una sala de la rejilla, iniciar la partida del bench con `forzar=True` o quitar la llave de salida de los datos del bench. Cualquiera de las tres va en una tarea aparte.
- **Los demás bloques**, corridos juntos sin `guardado` ni `ciclo` (`--bench agenda,cache,salas,inventario,retroceso,ordenamiento,bitacora,terreno,recorrido,llaves,resolubilidad`, 2026-11-09 01:26, `PYTHONIOENCODING=utf-8`): **código de salida 0, todos los criterios cumplen.** Un primer intento de esa misma corrida con la salida redirigida a un archivo midió todo, pero cortó al imprimir la tabla con `UnicodeEncodeError` («≤» en cp1252). Fue por la redirección a archivo en Windows, no por el programa, y se repitió con UTF-8.

  | Criterio | Resultado |
  |---|---|
  | Terreno A: peor de 25 ciclos < 20 ms (1, 10 y 50 cazadores, quieto y moviéndose) | CUMPLE (el peor: 224,6 µs con 50 cazadores moviéndose) |
  | Recorrido por niveles (SC-004, equivalencia, verificaciones) | CUMPLE (13 salas y 20 salidas con límite 2 en 400, 4 900 y 40 000 salas; razón 0,99×) |
  | Llaves B: guardar con A y 5 000 salas ≤ 50 ms | CUMPLE (16,38 ms) |
  | Llaves D: 1 / 0 / 0 | CUMPLE |
  | Resolubilidad A: mismo resultado en n = 300 y 3 000 | OK. Incremental 2,43 ms y 32,70 ms; repetida 192,89 ms y 165 929,88 ms (1 repetición) |
  | Resolubilidad C: < 200 ms | CUMPLE (cadena 56,73 ms; rejilla 17,49 ms) |
  | Resolubilidad D: razón de la incremental ≤ 20 | CUMPLE (13,4; repetida 860,2, informativa) |
  | §5.2 ciclo de eventos ≤ 20 ms | **Sin medir**: el bloque `ciclo` no corre (regresión de arriba). La línea «§5.2: el ciclo de eventos CUMPLE» del resumen sale por defecto porque el bloque no se ejecutó, no es una medición |
  | `guardado` | **Sin medir** (regresión de arriba) |

  Las 53 verificaciones `OK` previas a las mediciones pasaron. La razón de la repetida (860,2 ahora, 1 112,8 en T056) varía porque la n = 3 000 se mide con 1 sola repetición; la de la incremental (13,4 frente a 12,7) se mantiene. No se cambiaron umbrales ni código.

### T065 — 2026-11-09 — comparación de `spec.md` con el programa y con `mediciones.md` (sin corregir; T065 queda abierta)

Desajustes encontrados:

1. **`--offline` exige la cripta completa aunque la verificación no use el contenido de las salas** (FR-341, FR-342, H5-2). Con `--offline` (`crear_servicio(offline=True)`), una cripta con mapa, datos y llaves guardados, pero sin el contenido de todas sus salas, da código 2 con un mensaje engañoso: comprobado con cripta-06, sin red y con sha1 de `datos_cripta/` igual antes y después:

   ```text
   Verificación de la cripta cripta-06: NO SE PUDO VERIFICAR.
   La cripta cripta-06 no existe.
   ```

   La cripta existe: `ClienteOffline.obtener_criptas` solo lista las criptas completas (Parte I). `FuenteSoloLocal` da otro mensaje, «no está en la lista de criptas guardada en disco». La spec dice que la verificación usa solo el mapa, los datos generales y las llaves, y que funciona igual con `--offline`. Hace falta decidir si la spec agrega esa condición previa («con `--offline`, la cripta debe estar completa en disco») o si se cambia el programa en otra capacidad. Al menos, el mensaje no debería decir «no existe».
2. **El `--bench` completo de la Parte II deja de funcionar por FR-339** (ver T064): la cripta sintética de `guardado` y `ciclo` no tiene la ubicación de su llave de salida. No es una contradicción con un FR, pero la spec no prevé el efecto de FR-339 sobre las criptas sintéticas que inician partidas sin llaves.
3. **Un dato general sin `sala_inicial` o sin `sala_salida` haría lanzar a `verificar`** (FR-343: «no DEBE dar un resultado…: DEBE informar un error claro»). `ServicioCripta.obtener_sala_inicial` y `obtener_sala_salida` leen `datos["sala_inicial"]` y `datos["sala_salida"]`, y un `KeyError` no lo captura `verificar`, que solo captura `LlavesNoDisponibles`, `DatoLocalFaltante`, `RuntimeError` y `OSError`. Hallado por lectura del código, **sin prueba que lo ejecute**; no se probó con datos reales. `obtener_llave_salida` usa `.get` y no tiene el problema.
4. **Texto (menor): FR-338 llama «bloqueo» a «la llave de salida no existe» y a «la sala de salida no tiene camino».** El programa los modela como `causas` (líneas «Motivo:» del reporte), no como `BloqueoDTO`, y agrega dos causas que la spec no nombra (`SALIDA_BLOQUEADA` y `LLAVE_SALIDA_INALCANZABLE`). La entidad «Bloqueo» de la spec dice «y si forma un ciclo»; el programa tiene 4 tipos y la dirección de la salida. El reporte informa todo lo que pide FR-338: es una diferencia de nombres, no de comportamiento.
5. **Texto (menor): FR-339 no tiene la frase «en esta capacidad el comportamiento se verifica en la operación…»** que sí tienen FR-330, FR-331 y FR-340, aunque «DEBE mostrarse el reporte» depende de quien conecta las opciones. El programa lanza `CriptaNoResoluble` con el reporte como mensaje; mostrarlo es de la capacidad de Fernanda.

Sin desajuste: la regla (FR-332 a FR-335, oleadas y desempate), el reporte (FR-336, FR-337), `--forzar` (FR-340: el aviso no entra a los mensajes ni al log; mostrarlo una vez es del controlador), FR-341 (no pide contenido), FR-344, las clarificaciones, los casos límite (salida a sala inexistente, versión que cambia, reproducción y partida cargada sin verificar, datos inválidos al iniciar), SC-001 a SC-005 y SC-007 por las pruebas y el bench, y FR-345 y SC-006 por `mediciones.md` (cripta-06, 2,925 ms). El Estado de `spec.md` sigue en «Borrador», como se pidió.
