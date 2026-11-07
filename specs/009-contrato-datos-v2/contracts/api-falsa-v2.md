# Contrato: API falsa v2 de pruebas (`tests_labs/api_falsa.py`)

Es infraestructura de pruebas, no forma parte del juego. Es determinista y no usa red (FR-318).

## Compatibilidad

`HttpFalso`, `HttpConfigurable`, `nueva_ejecucion` y `cargar_todo` conservan su firma y su comportamiento: las pruebas de la Parte I y de la capacidad 001 deben seguir pasando sin cambios.

## Lo que se agrega

| Pieza | Comportamiento |
|---|---|
| `HttpFalso.obtener_llaves(cripta_id)` | Registra `("llaves", cripta_id)` y devuelve `[{"id": "itm_llave_bronce", "sala": 1}, {"id": "itm_llave_negra", "sala": 3, "enemigo": "e-301"}]` |
| `HttpConfigurable(..., llaves=None, fallo_llaves=None)` | `llaves`: lista de `(id, sala, enemigo o None)`; con `None` se usan las de `HttpFalso`. `fallo_llaves`: `None`, `"sin_respuesta"` (lanza `ErrorSinConexion`) o `"invalida"` (devuelve `{"sin_llaves": []}`). Las respuestas inválidas más finas se arman pasando `llaves` malas |
| `cripta_v2(semilla=0)` | Devuelve un `HttpConfigurable` con una rejilla de 5×5 (`costo_max=9`), un cazador `ent_cazador` de rango 600 en la sala más lejana, la llave de salida soltada por el cazador, una llave en el suelo y la misma llave en dos salas (FR-319) |
| `CASOS_APENDICE_B` | Lista de `(código, descripción, constructor)`. Cada constructor devuelve una cripta configurada y, si hace falta, un guion (FR-320) |

## Casos del Apéndice B

> **BLOQUEO**: el texto del Apéndice B no está en el repositorio. El grupo debe completar esta tabla antes de `/speckit-tasks`. Cada fila se vuelve un escenario de aceptación con una prueba que cita su código (principio IX).

| Código | Caso | Estado |
|---|---|---|
| B-? | Una acción rechazada no cambia nada ni consume tiempo (citado en `GestorEventos.py` y `EstadoJuegoLogica.py`) | Deducido del código; confirmar el número |
| B-? | … | Pendiente de transcribir |
