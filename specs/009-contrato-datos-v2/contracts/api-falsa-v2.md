# Contrato: API falsa v2 de pruebas (`tests_labs/api_falsa.py`)

Es infraestructura de pruebas, no forma parte del juego. Es determinista y no usa red (FR-318).

## Compatibilidad

`HttpFalso`, `HttpConfigurable`, `nueva_ejecucion` y `cargar_todo` conservan su firma y su comportamiento: las pruebas de la Parte I y de la capacidad 001 deben seguir pasando sin cambios.

## Lo que se agrega

| Pieza | Comportamiento |
|---|---|
| `HttpFalso.obtener_llaves(cripta_id, solo_guardadas=False, limite_solicitudes=None)` | Registra `("llaves", cripta_id)` y devuelve (si `solo_guardadas` es `True` lanza `LlavesNoDisponibles` sin registrar la llamada) `[{"id": "itm_llave_bronce", "sala": 1}, {"id": "itm_llave_negra", "sala": 3, "enemigo": "e-301"}]` |
| `HttpConfigurable(..., llaves=None, fallo_llaves=None, llave_salida=None, objetos=None)` | `llaves`: lista de `(id, sala, enemigo o None)`; con `None` se usan las de `HttpFalso`. `fallo_llaves`: `None`, `"sin_respuesta"` (lanza `ErrorSinConexion`) o `"invalida"` (lanza `LlavesInvalidas("respuesta sin llaves")`, lo mismo que daría `leer_llaves` sobre una respuesta sin la clave `llaves`; la API falsa entrega la lista ya extraída, como el HTTP real después de `leer_llaves`). Las respuestas que FR-311 rechaza por su contenido se arman pasando `llaves` malas. En los dos fallos la llamada se registra igual. `llave_salida`: id de la llave de salida de los datos generales; con `None` se usa la de `HttpFalso`. `objetos`: lista de `(sala, id de catálogo)` de objetos en el suelo; con `None` no hay objetos. `obtener_llaves` acepta también `solo_guardadas=False` y `limite_solicitudes=None`, con el mismo efecto que en `HttpFalso` |
| `cripta_v2(semilla=0)` | Devuelve un `HttpConfigurable` con una rejilla de 5×5 (`costo_max=9`), un cazador `ent_cazador` de rango 600 en la sala más lejana, la llave de salida soltada por el cazador, una llave en el suelo y la misma llave en dos salas (FR-319) |
| `CASOS_APENDICE_B` | Lista de `(código, descripción, constructor)` con los 23 casos, en el orden B-T, B-N, B-R, B-L. La descripción es la de la tabla de abajo, literal (`test_api_falsa_v2.py` la compara con este archivo, así que las filas `\| B-` no se pueden cambiar sin cambiar la prueba). El constructor no recibe argumentos y devuelve `(HttpConfigurable, guion)`. Es determinista y no usa red (FR-320) |
| `HttpCaso(..., trampas=None)` | Subclase de `HttpConfigurable` que usan los casos: `trampas` es una lista de `(sala, instancia, tipo)` que se agrega al contenido de cada sala. Existe para no cambiar la firma de `HttpConfigurable` |
| `PASOS_GUION` | Los 14 nombres de paso que pueden aparecer en un guion: `mover`, `esperar`, `recoger`, `ir_a`, `antorcha`, `pergamino`, `pergamino_en_viaje`, `cerrar_puerta`, `cambiar_velocidad`, `historia`, `replay_hasta`, `verificar`, `iniciar_sin_forzar` y `cargar_partida`. Su significado está en el comentario al inicio de la sección de casos de `tests_labs/api_falsa.py`. Hoy solo `mover` y `esperar` los ejecuta una prueba (`tests_labs/escenarios_terreno.py`); los demás solo nombran la acción que ejecuta la capacidad dueña del caso (002, 003, 004 o 010) o un cambio durante la partida que provoca la prueba |
| Archivo de B-L6 | El constructor arma a mano, con `struct`, un archivo de partida de la Parte I con formato 5 en una carpeta temporal y devuelve `("cargar_partida", ruta)` en el guion. `AlmacenPartidaBinario` lo rechaza con «Versión del formato de partida no soportada: 5 (este programa usa la 6)». Quien use el caso debe borrar la carpeta temporal |

## Casos del Apéndice B

Transcritos del enunciado de la Parte II (Apéndice B, «Casos que deben tener un resultado definido») el 2026-11-06. Cada fila se vuelve un escenario de aceptación con una prueba que cita su código y el requisito (principio IX). «P1 §x» remite al enunciado de la primera parte. El dueño es quien escribe el escenario en su especificación; esta API falsa solo ofrece la situación reproducible (FR-320).

### Terreno y cazador (dueño: Cesar, capacidad 001)

| Código | Caso |
|---|---|
| B-T1 | Un cazador no tiene ruta abierta hacia el jugador: espera con costo 100. |
| B-T2 | La ruta más barata del cazador cuesta más que su `rango`: espera con costo 100. |
| B-T3 | Existe una ruta de menos salas pero mayor costo y otra de más salas y menor costo: el cazador sigue la de menor costo. |
| B-T4 | Dos vecinas inician rutas de costo mínimo: el cazador va a la de menor id. |
| B-T5 | Una puerta de la ruta del cazador se cierra entre dos de sus turnos: en el turno siguiente decide como si calculara desde cero. |
| B-T6 | Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1. |
| B-T7 | Cambia la velocidad de un actor que atraviesa una salida costosa: el tiempo restante se escala según P1 §2.3. |

### Niebla de guerra e «ir a» (dueña: Fernanda, capacidad 002)

| Código | Caso |
|---|---|
| B-N1 | `ir a` hacia una sala no explorada: se rechaza y no consume tiempo. |
| B-N2 | El mapa recuerda abierta una puerta que en realidad está cerrada: al observarla, el mapa se actualiza y la ruta se recalcula; si no queda ruta, el viaje se detiene sin consumir tiempo adicional. |
| B-N3 | `ir a` entra a una sala con enemigos dormidos: los enemigos se activan según P1 §2.4 y el viaje se detiene. |
| B-N4 | Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni sus trampas. |
| B-N5 | Un pergamino revierte una entrada con antorcha encendida: las salas exploradas por la antorcha vuelven a su estado anterior. |
| B-N6 | Un pergamino durante un viaje: revierte solo el último paso y el viaje no continúa. |

### Resolubilidad (dueño: Scott, capacidad 003)

| Código | Caso |
|---|---|
| B-R1 | `llave_salida` está detrás de la única puerta que ella misma abre: no resoluble; el reporte señala el ciclo. |
| B-R2 | Una llave está en el campo `suelta` de un enemigo errante: la verificación la ubica en la sala inicial del enemigo. |
| B-R3 | Existen varios órdenes válidos de obtención de llaves: dos ejecuciones producen el mismo orden. |
| B-R4 | Cripta no resoluble sin `--forzar`: la partida no inicia y se muestra el reporte. |

### Línea de tiempo (dueño: JP, capacidad 004)

| Código | Caso |
|---|---|
| B-L1 | `historia <t>` con `t` mayor que el reloj actual: se rechaza. |
| B-L2 | `historia` después de usar un pergamino: no muestra las acciones revertidas. |
| B-L3 | Varios eventos ocurren en el mismo instante `t`: `historia <t>` muestra el estado después de todos ellos. |
| B-L4 | `historia` no consume tiempo virtual, no se registra en `partida.log` y no modifica el historial de retroceso. |
| B-L5 | `--replay partida.log --hasta t` con `t` posterior al final de la partida: muestra el estado final e indica que la partida terminó antes. |
| B-L6 | Se carga un archivo de partida de la primera parte: se reporta la incompatibilidad de formato o se migra explícitamente; nunca se carga en silencio (caso compartido con Scott, capacidad 010). |
