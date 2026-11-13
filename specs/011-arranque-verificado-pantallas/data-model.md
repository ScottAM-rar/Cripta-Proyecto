# Modelo de datos: Arranque verificado y pantallas de consola claras

No se crea ni se cambia ningún dato persistente (formato 8, estado 5, `partida.log`). Esta capacidad define **lo que reciben las funciones de pantalla**, todo ya existente o derivado en el momento. Los datos no se guardan.

## 1. Entradas de las funciones de pantalla

### `texto_sala(...)` — pantalla de sala (FR-306)

| Dato | Tipo | Origen (ya existe) | Uso |
|---|---|---|---|
| `jugador` | `JugadorDTO` | `servicio.getJudador()` | vida (`vida_actual`, `vida_max`), antorcha (`antorcha_encendida`, `antorcha_hasta`) |
| `tiempo` | `int` | reloj de la partida (acceso de lectura del servicio) | «Tiempo» del estado del jugador |
| `sala` | `SalaDTO` | `servicio.obtenerSala(id)` | nombre, id, objetos, enemigos, trampas |
| `salidas` | lista de `SalidaConocidaDTO` + llave pedida | `servicio.vistaSalaActual().salidas` | dirección, destino, estado de puerta, costo (FR-219: no se revela lo no explorado) |
| `llaves_pedidas` | lista de `str \| None`, una por salida, mismo orden | cruce hecho en el controlador con `sala.salidas` | «Requiere: …» en puertas cerradas |
| `objeto_actual` | objeto o `None` | `servicio.objetoActualInventario()` | línea del inventario |
| `mensajes` | `list[str]` | `servicio.ultimosMensajes()` | últimos 20 mensajes |

Reglas de la función: no lee el servicio ni el modelo; no ordena (conserva el orden recibido, que ya es determinista); no calcula tiempos, costos ni daños.

### `texto_fin_partida(...)` — resumen final (FR-307)

| Dato | Tipo | Origen |
|---|---|---|
| `motivo` | `str` | segundo valor de `servicio.terminado()` |
| `puntaje` | `int` | acceso de lectura al puntaje de la partida |
| `acciones` | `int` | `finPartida().acciones_jugador` |
| `tiempo` | `int` | `finPartida().tiempoReloj` |
| `vida_final` | `int` | `getJudador().vida_actual` |
| `salas_exploradas` | `int \| None` | `len(servicio.mapaConocido().salas)`; `None` si no hay mapa |
| contexto | `FinPartidaDTO` | `id_Cripta`, `vers_Cripta`, `cantEnemigosDerrotados` (línea de contexto) |

### `texto_ayuda()` / `buscar_comando(termino)`

| Dato | Tipo | Nota |
|---|---|---|
| `COMANDOS` | `tuple` de `(nombre, sintaxis, descripcion)` | una sola lista; es a la vez fuente de la ayuda y de la validación de sintaxis |

### `texto_error(que_paso, que_hacer)`

Dos `str`. Devuelve una sola línea `"<que_paso> <que_hacer>"`; ambas partes no vacías (si falta una, `ValueError`: es un defecto del programa, no del jugador).

### Reporte de verificación (arranque)

| Dato | Tipo | Origen |
|---|---|---|
| `lineas` | `list[str]` | `servicio.reporteVerificacion()` → `lineas_reporte(resultadoVerificacion)` (003, sin cambios) |
| `aviso` | `str \| None` | `servicio.avisoResolubilidad()` (003) |
| `rechazo` | `CriptaNoResoluble` | excepción de la 003; el mensaje es el reporte |

## 2. Estados y transiciones

```text
Arranque (partida nueva)
  iniciarJuego(cripta, semilla, forzar)
    ├─ resoluble ........................ reporte → (sin aviso) → partida abierta
    ├─ no resoluble, forzar ............. reporte → AVISO de forzar → partida abierta
    ├─ no resoluble, sin forzar ......... reporte → guía de qué hacer → no se abre (salida 1)
    └─ no se pudo verificar ............. reporte «NO SE PUDO VERIFICAR» + aviso de la 003 → partida abierta

--verificar <cripta>
    ├─ resoluble ........................ reporte → salida 0
    ├─ no resoluble ..................... reporte → salida 1
    └─ no se pudo verificar / uso ....... reporte o mensaje → salida 2
```

La partida cargada y la reproducción no pasan por el arranque verificado (no hay reporte de inicio).

## 3. Validaciones

- La lista `COMANDOS` no tiene dos filas con el mismo `nombre`.
- Todo comando que el controlador reconoce tiene una fila (prueba de claridad).
- `texto_sala` conserva siempre las mismas secciones y el mismo orden, aunque estén vacías.
- Ninguna función de pantalla devuelve secuencias ANSI ni caracteres de control salvo `\n`.
