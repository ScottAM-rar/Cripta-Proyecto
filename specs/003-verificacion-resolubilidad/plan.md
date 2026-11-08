# Plan de implementación: Verificación de resolubilidad

**Rama**: `Scott-Persona3` (carpeta `003-verificacion-resolubilidad`) | **Fecha**: 2026-11-08 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/003-verificacion-resolubilidad/spec.md` (FR-330 a FR-346, con las 3 clarificaciones de la sesión 2026-11-08: completar = llegar a la sala de salida con la llave de salida obtenible; desempate por menor id de sala y luego id de llave; aviso de `--forzar` solo al iniciar).

## Resumen

La verificación es una función pura de Logica que recibe el mapa, la sala inicial, la sala de salida, la llave de salida y la ubicación de llaves de la 009, y devuelve un `ResultadoVerificacion`. Una sola operación `verificar` junta esos datos desde la fuente y la usan `--verificar` (que conecta Fernanda) y el inicio de partida.

El enfoque, justificado en [research.md](research.md):

0. **Primero, el hallazgo**: la API publica la llave de cada puerta en la salida, pero el mapa la descarta. Se agrega `llave: str | None = None` a `AristaMapaDTO` y `AristaCripta`, y `ServicioCripta.esqueleto()` la llena. `--offline` y `FuenteSoloLocal` la heredan sin cambios (se prueba). Es la primera tarea, con sus pruebas ([contracts/mapa-con-llaves.md](contracts/mapa-con-llaves.md)).
1. **Un solo recorrido incremental por oleadas** desde la sala inicial: `ColaCircular` para las salas; las puertas cerradas esperan a su llave en una lista por número de llave y se liberan cuando la llave se obtiene. Las llaves obtenibles de cada oleada salen de un `MonticuloMinimo` por `(id de sala, número de llave)`, que da el desempate de FR-335 y el orden de FR-336. Costo O(S + E + L log L + (L + E) log K).
2. **Índice propio de llaves** (`IndiceLlaves`): ids ordenados con `ordenar_adaptativo`, sin repetidos, y búsqueda binaria escrita a mano.
3. **Alternativa descartada medida**: repetir el recorrido completo en cada oleada, O(K · (S + E)). Bloque `--bench resolubilidad` con criptas de llaves encadenadas a n = 300 y n = 3 000, límite de 200 ms y razón de crecimiento.
4. **Capas**: resultado en `DTO/ResultadoVerificacionDTO.py`; algoritmo y `verificar(fuente, cripta_id, llaves=None)` en `Logica/VerificacionResolubilidad.py`; texto del reporte en `Logica/ReporteVerificacion.py`; `EstadoJuegoServicio.verificar(cripta_id)` para el controlador. `FuenteCripta` gana `obtener_sala_inicial` y `obtener_llave_salida`.
5. **Códigos de salida** 0 / 1 / 2 desde `ResultadoVerificacion.codigo_salida()`; los errores de datos nunca dan un resultado inventado.
6. **Inicio de partida**: `iniciarJuego(..., forzar=False)`. Con las llaves que ya pidió, verifica; si no es resoluble y no se forzó, lanza `CriptaNoResoluble` antes de marcar la partida como iniciada y antes de abrir el log. Con `forzar`, inicia y deja `avisoResolubilidad`. Sin llaves, sigue el aviso de FR-313. Reproducción y partida cargada no verifican.
7. **Entrega temprana para Fernanda**: el primer grupo de tareas fija firmas y DTO con cuerpo provisional ([contracts/interfaz-verificacion.md](contracts/interfaz-verificacion.md)). Esta capacidad no cablea `--verificar` ni `--forzar`.

## Contexto técnico

**Lenguaje/versión**: Python 3.11+ (el del proyecto).

**Dependencias principales**: ninguna nueva. Código del repositorio: `MapaCripta`, `ColaCircular`, `MonticuloMinimo`, `ordenar_adaptativo`, `RecorridoPorNiveles` (005), `UbicacionLlavesDTO` y `FuenteSoloLocal` (009), API falsa v2 y `CASOS_APENDICE_B`.

**Almacenamiento**: ninguno nuevo. La llave de la puerta ya estaba en el esqueleto crudo guardado; no cambia el formato de la caché ni el de partida.

**Pruebas**: `unittest` (`test_*.py` en la raíz, ayudas en `tests_labs/`), sin red, con la API falsa v2 y `FuenteSoloLocal`. Pruebas primero, con evidencia roja honesta (falla de aserción o el `NotImplementedError`/resultado provisional, nunca un error de importación).

**Plataforma**: consola, multiplataforma.

**Tipo de proyecto**: aplicación de consola por capas (Controlador → Servicio → Lógica, más adaptadores). Esta capacidad agrega sobre todo Logica y un DTO, y amplía de forma mínima el mapa, el contrato del modelo y el servicio.

**Objetivos de rendimiento**:
- Menos de 200 ms en la cripta publicada más grande con los datos guardados (FR-345); el bench lo comprueba sobre criptas sintéticas mucho mayores.
- Crecimiento aproximadamente lineal: con el tamaño ×10, el tiempo ≤ ×20 (FR-346, SC-007).
- 0 solicitudes nuevas: a lo sumo la consulta de llaves de la 009 (FR-341).

**Restricciones**: sin `dict`/`set` como índice; sin `heapq`, `bisect`, `collections`, `networkx`, `sorted()` ni `.sort()`. La lógica no importa adaptadores. No se tocan `AlmacenPartidaBinario`, `EstadoGuardadoDTO` ni `codec_partida`. Ningún id ni tamaño de una cripta concreta.

**Escala/alcance**: criptas publicadas de decenas de salas; bench hasta 5 000 salas de pasillo (≈ 10 000 salas en total) y K ≈ 5 000 llaves.

**NEEDS CLARIFICATION**: ninguno. Las tres dudas de la spec quedaron resueltas el 2026-11-08 y el resto se decide en research.md.

## Verificación de la constitución

*Compuerta: debe pasar antes de la investigación (Fase 0) y se reevalúa tras el diseño (Fase 1). Resultado: pasa en las dos.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Estructuras propias | `ColaCircular`, `MonticuloMinimo` y `ordenar_adaptativo` del repositorio; `IndiceLlaves` con búsqueda binaria propia; listas por id de sala y por número de llave. Sin `dict`/`set`/`heapq`/`bisect`/`collections`/`networkx`/`sorted()`/`.sort()` (revisión con el paso 5 de [quickstart.md](quickstart.md)). Cada tarea generada se revisa contra esta lista antes de implementar | Pasa |
| II. Determinismo | El resultado depende solo de los datos: el orden sale del montículo con clave `(sala, número)` y números en orden de id; las salas alcanzables, de recorrer por id; los bloqueos, de recorrer salas por id y salidas en N, S, E, O; la elección de ubicación (suelo antes que enemigo, menor instancia) no depende del orden de la respuesta. No usa azar, hora ni qué contenido está descargado. Prueba con la respuesta de llaves invertida y con y sin contenido guardado | Pasa |
| III. Equivalencia ante el reuso | El inicio de partida reutiliza las llaves ya pedidas y el esqueleto memorizado: son los mismos datos que leería `verificar` desde cero (la versión de la cripta no cambia en la sesión; la 009 ya lo garantiza). El recorrido incremental reutiliza lo alcanzado entre oleadas; `Equivalencia` lo compara con la estrategia repetida desde cero en criptas al azar por semilla, y la sección A del bench falla si difieren | Pasa |
| IV. MVC y adaptadores | `VerificacionResolubilidad`, `IndiceLlaves` y `ReporteVerificacion` no importan adaptadores, red, disco ni vista; los fallos de datos se capturan por `LlavesNoDisponibles`, `DatoLocalFaltante` y las clases base `RuntimeError`/`OSError`. `--offline` y la lectura solo local cambian la fuente, no el modelo. La operación `verificar(cripta_id)` no crea la vista; `--bench` tampoco | Pasa |
| V. Sin datos de una cripta | Ningún id de llave, sala ni tamaño fijo. Los tamaños del bench son parámetros sintéticos; la cripta publicada más grande se mide a mano y se anota en `mediciones.md`, no en el código | Pasa |
| VI. Presupuesto y versiones | Sin solicitudes nuevas: la consulta de llaves es la de la 009, con su control de presupuesto. No se toca el formato de partida ni la validación de versión | Pasa |
| VII. Rendimiento medido | Bloque `resolubilidad` con la alternativa descartada (recorrido repetido) y la búsqueda lineal; límite de 200 ms y crecimiento; criptas sintéticas por semilla; resultados en `mediciones.md` con la máquina libre | Pasa |
| VIII. Especificación primero | No agrega reglas: el contenido del reporte, los tipos de bloqueo y la forma de las oleadas concretan FR-335 a FR-338 sin cambiarlos. El cambio del mapa es de contrato interno, no de reglas | Pasa |
| IX. Trazabilidad | Matriz FR → escenario → prueba, casos B-R1 a B-R4 y criterios de éxito en [quickstart.md](quickstart.md). Cada prueba cita su FR o su código B-R en el nombre | Pasa |
| X. Cambios de especificación | Si la implementación contradice la spec (por ejemplo, R1: puertas reales sin `llave`), se corrige primero `spec.md` en una confirmación aparte | Pasa |
| XI. Uso de LLM | Registrar en `PROMPTS_LLM.md` el `/speckit-specify`, el clarify de la spec y este `/speckit-plan`. Lo hace Scott por lotes; este plan no modifica `PROMPTS_LLM.md` | Acción del grupo |

### Observaciones y hallazgos

1. **La llave de la puerta se perdía al armar el mapa** (research.md §1). Se resuelve antes que nada, con valor por defecto para no romper a quien ya construye aristas.
2. **La sala inicial y la llave de salida no estaban en el contrato del modelo**: la primera solo salía dentro de `crear_jugador`, la segunda solo en el `dict` de datos generales. Se agregan `obtener_sala_inicial` y `obtener_llave_salida` a `FuenteCripta`, junto a `obtener_sala_salida`.
3. **El log se abre después de `iniciarJuego` de Logica** (`EstadoJuegoServicio._abrirLog`), así que lanzar `CriptaNoResoluble` dentro de `iniciarJuego` basta para que no se escriba nada en el registro de partida (B-R4).
4. **Verificación con datos inválidos al iniciar** (por ejemplo, la sala de salida no existe en el esqueleto): la partida no se bloquea y se avisa, por coherencia con FR-339 («sin datos para verificar, no se bloquea»). `--verificar` sí termina con código 2.
5. **`--replay`/`--hasta` y partida cargada** no verifican: `pedir_llaves=False` implica no verificar, y la restauración solo reinicia los dos atributos nuevos.
6. **`MonticuloMinimo` se usa sin modificar** con la clave `(sala, número de llave)` aunque sus parámetros se llamen `costo` y `sala` (R3); lo usan la 001 y la 009.

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/003-verificacion-resolubilidad/
├── plan.md                 # Este archivo
├── research.md             # Fase 0: decisiones, alternativas, costos, riesgos
├── data-model.md           # Fase 1: cambio del mapa, resultado, estructuras internas, estado
├── quickstart.md           # Fase 1: validación y matriz de trazabilidad
├── contracts/
│   ├── mapa-con-llaves.md          # cambio de contrato del mapa (primera tarea)
│   ├── interfaz-verificacion.md    # operación, DTO y entrega provisional para Fernanda
│   ├── reporte-verificacion.md     # texto del reporte, aviso de --forzar, códigos 0/1/2
│   └── bench-resolubilidad.md      # secciones y criterios de --bench resolubilidad
├── checklists/requirements.md
├── mediciones.md           # lo llena la implementación
└── tasks.md                # lo genera /speckit-tasks
```

### Código fuente (raíz del repositorio)

```text
DTO/MapaDTO.py                     # MODIFICADO: AristaMapaDTO.llave (primera tarea)
Logica/MapaCripta.py               # MODIFICADO: AristaCripta.llave y su copia (primera tarea)
adaptadores/servicioCripta.py      # MODIFICADO: esqueleto() llena llave; obtener_sala_inicial, obtener_llave_salida
adaptadores/fuente_solo_local.py   # MODIFICADO: obtener_sala_inicial, obtener_llave_salida (esqueleto sin cambios)
Logica/FuenteCripta.py             # MODIFICADO: obtener_sala_inicial, obtener_llave_salida en el protocolo

DTO/ResultadoVerificacionDTO.py    # NUEVO: ResultadoVerificacion, PasoLlaveDTO, BloqueoDTO
Logica/IndiceLlaves.py             # NUEVO: índice ordenado + búsqueda binaria propia
Logica/VerificacionResolubilidad.py # NUEVO: verificar_resolubilidad (pura), verificar(fuente, ...), CriptaNoResoluble
Logica/ReporteVerificacion.py      # NUEVO: lineas_reporte, aviso_forzado
Logica/EstadoJuegoLogica.py        # MODIFICADO: iniciarJuego(forzar), resultadoVerificacion, avisoResolubilidad
Logica/EstadoGuardadoLogica.py     # MODIFICADO mínimo: la restauración reinicia los dos atributos nuevos
Servicio/EstadoJuegoServicio.py    # MODIFICADO: verificar(cripta_id), iniciarJuego(forzar), avisoResolubilidad()

bench/resolubilidad.py             # NUEVO: secciones A–D
bench/__init__.py                  # MODIFICADO: registra "resolubilidad" y su indicador
main.py                            # MODIFICADO mínimo: la ayuda de --bench menciona "resolubilidad" (no cablea --verificar ni --forzar)
tests_labs/cripta_sintetica.py     # AMPLIADO: esqueleto_llaves_encadenadas
tests_labs/sin_red.py              # AMPLIADO: agrega las pruebas de la capacidad

test_mapa_con_llaves.py            # NUEVO (primera tarea)
test_indice_llaves.py              # NUEVO
test_resolubilidad_regla.py        # NUEVO
test_resolubilidad_apendice_b.py   # NUEVO (B-R1 a B-R4)
test_resolubilidad_determinismo.py # NUEVO
test_resolubilidad_datos.py        # NUEVO
test_resolubilidad_inicio.py       # NUEVO
test_resolubilidad_reporte.py      # NUEVO (incluye la prueba de contrato de la interfaz)
```

**No se modifican**: `AlmacenPartidaBinario`, `EstadoGuardadoDTO`, `codec_partida` y el formato de partida (010); `partida.log`; `MonticuloMinimo`, `ColaCircular`, `RecorridoPorNiveles`; los clientes HTTP, persistente y offline; `AlmacenDisco`; `Controlador/` y la vista (los cablea Fernanda).

**Decisión de estructura**: se mantienen las capas de la Parte I. El servicio junta los datos, Logica decide con una función pura y el resultado viaja como DTO, igual que en la 009.

## Complejidad de las operaciones más frecuentes

*S = salas (cota de ids), E = salidas, L = ubicaciones de llaves, K = ids de llave distintos.*

| Operación | Costo | Nota |
|---|---|---|
| Construir `IndiceLlaves` | O(K log K) | `ordenar_adaptativo` + quitar repetidos |
| `numero(id)` | O(log K) | Búsqueda binaria propia; L + E consultas por verificación |
| Recorrido incremental completo | O(S + E + L log L) | Cada sala y salida una vez; cada ubicación entra al montículo una vez |
| Salas alcanzables y bloqueos | O(S + E) | Recorrer por id, sin ordenar |
| Camino ignorando puertas (solo si no es resoluble) | O(S log S + E) | Un `RecorridoPorNiveles` de la 005 |
| Verificación total | O(S + E + (L + E) log K + L log L) | ≈ O((S + E + K) log K) con L del orden de K |
| Alternativa repetida (descartada) | O(K · (S + E)) | Medida en el bench |
| Verificar al iniciar la partida | La verificación total, 0 solicitudes | Reutiliza llaves y esqueleto |
| Texto del reporte | O(longitud del resultado) | Sin ordenar |

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar.

| Decisión que podría parecer compleja | Por qué se necesita | Alternativa más simple descartada |
|---|---|---|
| Oleadas en lugar de sacar una llave por vez | Da un significado preciso a «se vuelven obtenibles en el mismo momento» (FR-335) y hace el orden explicable | Una por vez: también determinista, pero una llave descubierta después puede adelantarse a una pendiente desde antes |
| `IndiceLlaves` con búsqueda binaria | Ids de texto no densos, sin `dict` (principio I) y con el orden que necesita el desempate | Búsqueda lineal: O((L + E) · K), medida en el bench (sección B) |
| Dos `verificar` (Logica y Servicio) | Respetar las capas: el controlador habla con Servicio; Logica no conoce el servicio de juego | Una sola en Servicio: el inicio de partida (Logica) no podría usarla sin invertir dependencias |
| `RecorridoPorNiveles` extra en el camino no resoluble | Distinguir `CICLO` de `LLAVE_SIN_CAMINO` y `SALIDA_SIN_CAMINO` (FR-338) | No distinguirlos: el reporte no diría si el problema son las puertas o el mapa |
| Dos operaciones nuevas en `FuenteCripta` | La sala inicial y la llave de salida no estaban en el contrato del modelo | Leer el `dict` de datos generales desde Logica: rompe la separación (principio IV) |
