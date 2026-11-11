# Plan de implementación: Contrato de datos v2 y ubicación de llaves

**Rama**: `009-contrato-datos-v2` | **Fecha**: 2026-11-06 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/009-contrato-datos-v2/spec.md` (FR-301 a FR-325, con las 4 clarificaciones de la sesión 2026-11-06; la cuarta y la corrección de FR-313 son de después del `/speckit-analyze`)

## Resumen

La consulta de llaves entra al contrato de datos v2 como un método más de la interfaz común de clientes. Cada cliente la resuelve a su manera, y el servicio de cripta la entrega al modelo como listas paralelas. Se agregan además una fuente que lee solo de disco, la API falsa v2 y un bloque de `--bench` que mide el presupuesto con cazadores.

El enfoque, justificado en [research.md](research.md):

1. **`obtener_llaves(cripta_id, solo_guardadas=False)`** en `ClienteInterfaz`:
   - HTTP: una solicitud `GET /criptas/<id>/llaves`, contada por el `_solicitar` existente.
   - Persistente: disco primero; si falta, red, validación y después guardado.
   - Offline: solo disco, con `ErrorOffline` si falta.
2. **Guardado en el mismo archivo de la cripta** (clave `llaves` en `cripta_<id>.bin`). La validación de versión existente vacía el archivo completo, así que las llaves de otra versión o de la Parte I desaparecen sin borrar nada a mano. Se compara con un archivo aparte y con meterlas en `datos` (research.md §4).
3. **`ServicioCripta.ubicacion_llaves()`** decide si queda presupuesto, valida contra el esqueleto (y contra el contenido solo si ya está guardado), convierte a `UbicacionLlavesDTO` (listas paralelas `ids`, `salas`, `enemigos`) y memoriza el resultado por sesión. **`esqueleto()`** es el nombre público del esqueleto normalizado.
4. **Fallo sin cortar la partida**: todo fallo se traduce a `LlavesNoDisponibles`, un error del contrato del modelo. La lógica lo captura, guarda el aviso y sigue (FR-313). Con el presupuesto al límite, un 429 **no se reintenta**: se trata como fallo (SC-005).
5. **Llaves bajo demanda**: `EstadoJuegoLogica.obtenerLlaves()` es el único punto por el que el modelo pide las llaves. En una partida nueva, `iniciarJuego` lo llama enseguida; al cargar una partida guardada no se llama, y la primera vez que alguien lo usa entrega lo guardado o hace la única consulta si queda presupuesto (FR-325). `llaves` y `avisoLlaves` se inicializan en `__init__` y se reinician al restaurar.
6. **`FuenteSoloLocal`**: envuelve un `ServicioCripta` sobre `ClienteOffline`, compara la versión vigente y nunca escribe ni pide nada.
7. **API falsa v2** en `tests_labs/api_falsa.py` y **bloque `llaves` de `--bench`**: precarga por saltos frente a precarga por costo, que solo existe dentro del bench.

## Contexto técnico

**Lenguaje/versión**: Python 3.11+ (el del proyecto).

**Dependencias principales**: ninguna nueva. Se usan `requests` (ya permitido), `json` y código del repositorio: `ArchivoIndexado`, `AlmacenDisco`, `ordenar_adaptativo`, `CampoDeCostos` y `MonticuloMinimo`.

**Almacenamiento**: `datos_cripta/cripta_<id>.bin` (`ArchivoIndexado`) gana la clave `llaves`. No cambia `VERSION_FORMATO`.

**Pruebas**: `unittest` (`test_*.py` en la raíz, ayudas en `tests_labs/`). El cliente HTTP se prueba sustituyendo `requests.get` con `unittest.mock`, sin red.

**Plataforma**: consola, multiplataforma.

**Tipo de proyecto**: aplicación de consola por capas (Controlador → Servicio → Lógica, más adaptadores). Esta capacidad toca sobre todo los adaptadores y amplía de forma mínima el contrato del modelo.

**Objetivos de rendimiento**:
- Una sola consulta de llaves por cripta y versión. Ninguna en `--offline` ni en la lectura solo local (SC-001 a SC-003).
- Guardar las llaves por debajo de 50 ms con 5 000 salas con contenido (criterio para cambiar de alternativa).
- Validar O(k log k).

**Restricciones**: sin `dict`/`set` como índice, sin `heapq`/`bisect`/`collections`. El `dict` de `respuesta.json()` solo se lee en `leer_llaves`. El modelo no importa red, disco ni vista. Ningún id ni tamaño de una cripta concreta.

**Escala/alcance**: k llaves por cripta (decenas en las criptas reales, hasta 1 000 en el bench). Criptas sintéticas de 25 a 5 000 salas.

## Verificación de la constitución

*Compuerta: debe pasar antes de la investigación (Fase 0) y se reevalúa tras el diseño (Fase 1).*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Estructuras propias | Llaves en listas paralelas. Repetidos con `ordenar_adaptativo` y comparación entre vecinas. Existencia de salas con una lista de booleanos. Sin `dict`/`set`/`collections` en el código nuevo. El `deque` de `servicioCripta.py` es de la Parte I y no gana usos | Pasa, con observación R3 |
| II. Determinismo | Las llaves no dependen del azar y conservan el orden de la respuesta. No entran al `partida.log` ni al estado guardado, así que la reproducción da lo mismo con red o sin red. La API falsa v2 y el bench se generan por semilla | Pasa |
| III. Equivalencia ante el reuso | La memorización por sesión y el guardado en disco solo valen mientras la versión coincida, que es el único evento que puede cambiar las llaves. `test_llaves_version` compara lo reutilizado con una consulta desde cero | Pasa |
| IV. MVC y adaptadores | `LlavesNoDisponibles` y `DatoLocalFaltante` viven en el contrato del modelo. `--offline` y la lectura solo local cambian el cliente en la fábrica, no el modelo. `--bench` no crea la vista | Pasa |
| V. Sin datos de una cripta | Ningún id de llave, sala ni presupuesto fijo en el código. Los de la API falsa son datos de prueba | Pasa |
| VI. Presupuesto y versiones | La consulta cuenta en `solicitudes_realizadas`. Con el presupuesto agotado no se hace. La invalidación usa `_validar` y nunca se borra a mano | Pasa |
| VII. Rendimiento medido | Bloque `llaves` con las alternativas descartadas en A, B y C. Sección D con criterio de salida | Pasa |
| VIII. Especificación primero | No se agregan reglas. El reparto de capas está en este plan | Pasa |
| IX. Trazabilidad | Matriz FR → escenario → prueba en [quickstart.md](quickstart.md). Los 23 casos del Apéndice B quedaron transcritos (R2 mitigado) | Pasa |
| X. Cambios de especificación | Si `/llaves` real difiere (R1) y eso cambia una regla, primero se corrige la especificación en una confirmación aparte | Pasa |
| XI. Uso de LLM | Registrar en `PROMPTS_LLM.md` este `/speckit-plan`, el `/speckit-specify` y el `/speckit-clarify` | Acción del grupo |

### Observaciones y hallazgos

1. **El presupuesto hoy solo se reporta.** Esta capacidad lo hace cumplir solo para la consulta de llaves (FR-309, SC-005).
2. **El HTTP no puede validar contra el contenido.** Por eso la validación es una función pura que recibe quién lee el contenido guardado. El persistente valida **antes** de guardar (FR-310).
3. **`validar_cripta` vacía el archivo** si la versión no coincide. La lectura solo local no debe llamarlo, porque destruiría datos que la consulta histórica podría necesitar después.
4. **`--replay` pasa por `iniciarJuego`, pero no pide las llaves** (cambió el 2026-11-07, tras la pregunta de la capacidad 007 y T058): una reproducción no es una partida nueva y las llaves solo sirven para el aviso de resolubilidad, así que no gasta presupuesto ni emite el aviso. `iniciarJuego` recibe `pedir_llaves=True` y `repetirPartida` pasa `False`; `obtenerLlaves()` sigue pidiéndolas bajo demanda. El log no cambia.
5. **`--verificar` no es de esta capacidad**: qué hace cuando faltan las llaves lo especifica e implementa la capacidad 003 (FR-330 en adelante). Aquí solo quedan `obtenerLlaves()`, `llaves` y `avisoLlaves`.
6. **Partida cargada** (FR-325): la restauración no pasa por `iniciarJuego`; por eso `llaves` y `avisoLlaves` se inicializan en `__init__` y la restauración los reinicia a `None`, para no arrastrar las llaves de otra cripta.

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/009-contrato-datos-v2/
├── plan.md                 # Este archivo
├── research.md             # Fase 0: decisiones, alternativas, riesgos
├── data-model.md           # Fase 1: DTO, errores, archivo en disco, estado
├── quickstart.md           # Fase 1: validación y matriz de trazabilidad
├── contracts/
│   ├── consulta-llaves.md     # forma de /llaves y reglas de validación
│   ├── interfaz-clientes.md   # clientes, servicio, fuente solo local, fábrica
│   ├── api-falsa-v2.md        # API falsa v2 y casos del Apéndice B (transcritos)
│   └── bench-llaves.md        # secciones y criterios de --bench llaves
├── checklists/requirements.md
├── mediciones.md           # lo llena la implementación
└── tasks.md                # lo genera /speckit-tasks
```

### Código fuente (raíz del repositorio)

```text
adaptadores/
├── Interfaz.py              # MODIFICADO: obtener_llaves
├── cliente_http.py          # MODIFICADO: obtener_llaves (GET /criptas/<id>/llaves)
├── cliente_persistente.py   # MODIFICADO: obtener_llaves (disco → red → validar → guardar), contenido_en_disco
├── cliente_offline.py       # MODIFICADO: obtener_llaves, contenido_en_disco
├── AlmacenDisco.py          # MODIFICADO: guardar_llaves, leer_llaves
├── llaves.py                # NUEVO: leer_llaves, validar_llaves, LlavesInvalidas
├── servicioCripta.py        # MODIFICADO: esqueleto(), ubicacion_llaves(); obtener_mapa delega
├── fuente_solo_local.py     # NUEVO: FuenteSoloLocal
├── fabrica.py               # MODIFICADO: crear_fuente_solo_local
└── resolucion.py            # sin cambios de comportamiento (ver contracts/interfaz-clientes.md)

DTO/LlavesDTO.py             # NUEVO: UbicacionLlavesDTO
Logica/FuenteCripta.py       # MODIFICADO: esqueleto, ubicacion_llaves, LlavesNoDisponibles, DatoLocalFaltante
Logica/EstadoJuegoLogica.py  # MODIFICADO: llaves y avisoLlaves en __init__, obtenerLlaves() bajo demanda, llamada en iniciarJuego
Logica/EstadoGuardadoLogica.py # MODIFICADO mínimo: la restauración reinicia llaves y avisoLlaves (FR-325)
Controlador/ (vista)         # MODIFICADO mínimo: muestra avisoLlaves cuando aparece

bench/llaves.py              # NUEVO: bloque "llaves" (secciones A–D)
bench/__init__.py            # registra el bloque
main.py                      # ayuda de --bench menciona "llaves"

tests_labs/api_falsa.py      # AMPLIADO: API falsa v2 (obtener_llaves, fallo_llaves, cripta_v2, CASOS_APENDICE_B)
test_llaves_validacion.py    # NUEVO
test_llaves_clientes.py      # NUEVO
test_llaves_presupuesto.py   # NUEVO
test_llaves_version.py       # NUEVO
test_llaves_fallos.py        # NUEVO
test_fuente_solo_local.py    # NUEVO
test_llaves_partida_cargada.py # NUEVO (FR-325)
test_api_falsa_v2.py         # NUEVO
```

**No se modifican**: `precargar_vecinas` y `salas_vecinas` (FR-324), el formato de partida y el `partida.log` (capacidad 010), los comportamientos de enemigos ni `ArchivoIndexado`.

**Decisión de estructura**: se mantienen las capas de la Parte I. La consulta nueva sigue el mismo camino que `obtener_contenido`: el cliente trae y guarda, el servicio valida y convierte, el modelo recibe un DTO.

## Complejidad de las operaciones más frecuentes

*k = llaves, N = salas, C = salas con contenido guardado, B = bytes de `cripta_<id>.bin`.*

| Operación | Costo | Nota |
|---|---|---|
| Consulta de llaves (red) | 1 solicitud | Una vez por cripta y versión |
| `ubicacion_llaves` memorizada | O(1) | Misma sesión |
| Leer `llaves` del disco | O(claves del índice) + O(k) | `ArchivoIndexado.leer` |
| Guardar `llaves` | O(B) | Reescribe el archivo de la cripta; una vez por versión. Se mide (bench B) |
| Validar | O(N) para armar `existe` + O(k log k) para repetidos + O(k · enemigos por sala) | Sin solicitudes |
| `ubicaciones_de(id)` | O(k) | La capacidad 003 indexa si lo necesita |
| Comprobación de versión de la fuente solo local | O(claves del índice) por operación | Lectura de `version` |

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar.

| Decisión que podría parecer compleja | Por qué se necesita | Alternativa más simple descartada |
|---|---|---|
| Parámetro `limite_solicitudes` en la interfaz | SC-005 con 429: con el presupuesto al límite, el HTTP no debe reintentar | Reintentar siempre: un 429 con 1 solicitud restante excedería el presupuesto |
| Parámetro `solo_guardadas` en la interfaz | Hacer cumplir el presupuesto sin que el HTTP conozca reglas del juego, y sin gastar nada si las llaves ya están en disco | Que el servicio compruebe el presupuesto y no llame: no podría aprovechar lo guardado cuando no queda presupuesto |
| Validar en el persistente **y** en el servicio | El persistente debe validar antes de guardar (FR-310); el servicio cubre los caminos sin persistente (HTTP directo en pruebas, offline) | Validar solo en el servicio: guardaría respuestas inválidas |
| `FuenteSoloLocal` como envoltorio | FR-317 (versión vigente) y la garantía estructural de 0 solicitudes | Reusar `--offline`: acepta cualquier versión guardada |
