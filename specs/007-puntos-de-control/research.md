# Investigación y Decisiones Técnicas: Puntos de control de la partida

**Capacidad**: `007-puntos-de-control` | **Fecha**: 2026-11-07 | **Especificación**: [spec.md](spec.md)

Este documento analiza las alternativas técnicas, restricciones arquitectónicas de la Constitución y del código base, y fundamenta las decisiones tomadas para la implementación de los puntos de control de la partida (FR-414 a FR-426).

---

## 1. Contador de la línea de tiempo vigente vs. `accionesJugador`

### Contexto del código
En `EstadoJuegoLogica.py` existe el atributo `self.accionesJugador`, introducido en la Parte I. Dicho contador:
1. Se incrementa en 1 en cada acción que consume tiempo virtual (`self.accionesJugador += 1`, línea 663).
2. Se serializa en el formato de guardado binario desde la versión 4 (`VERSION_FORMATO = 4`).
3. Constituye la métrica oficial para el cálculo de puntaje y ranking del juego (§2.12 del enunciado).
4. **No se decrementa** cuando el jugador utiliza el pergamino de retroceso; esto es deliberado para evitar que el uso del pergamino permita «inflar» o manipular el puntaje de acciones realizadas.

### Problema
El intervalo $K$ de los puntos de control mide acciones del jugador en la **línea de tiempo vigente** (clarificación a y FR-418). Si el pergamino revierte $m$ acciones, el contador temporal debe disminuir en $m$ y los puntos de control posteriores a esa posición deben descartarse. Reutilizar `accionesJugador` rompería el cálculo de puntaje o desincronizaría el intervalo de puntos de control.

### Decisión
- **Introducir un atributo nuevo e independiente**: `self.acciones_linea_tiempo: int = 0` en `EstadoJuegoLogica`.
- `acciones_linea_tiempo` inicia en 0 con la partida.
- Suma 1 por cada acción aceptada y ejecutada por el jugador, es decir, el mismo conjunto de acciones que hoy incrementa `accionesJugador` (acciones aceptadas que consumen tiempo, línea 663). Los movimientos del cursor del inventario no consumen tiempo, no pasan por ese punto y no cuentan. **Debe confirmarse con quien implementa 004** que `historia #k` numera las acciones con el mismo criterio.
- Resta $m$ (en la práctica 1 por uso de pergamino) cuando el pergamino revierte exitosamente acciones.
- `accionesJugador` se mantiene intacto con su semántica original (§2.12).

---

## 2. Punto exacto de captura en el ciclo de vida del turno

### Contexto del código
En `EstadoJuegoLogica.accionJugador(self, evento, tope=None)`:
1. Se valida el inicio del juego y se comprueba si la acción fue rechazada (`accion.exito is False`). Si es rechazada, retorna de inmediato sin consumir tiempo.
2. Si es uso de pergamino (`GestorEventos.es_uso_de_pergamino(evento)`), se procesa el retroceso, se registra en el log y la función retorna anticipadamente (línea 650).
3. Para acciones normales de juego (movimiento, combate, consumo de objetos, etc.):
   - Se activan trampas si aplica.
   - Se incrementan puntajes y `accionesJugador`.
   - Se verifica si la partida terminó (`self._comprobarFinal()`).
   - Si no terminó, se reprograma el turno del jugador y se llama a `self._avanzarHastaProximoTurno(tope=tope)`.
   - Se actualiza `self.tiempoMovimientoJugador = reloj.tiempo_actual`.
   - Se registra la acción en el log (`self._registrarAccionEnLog(evento)`).
   - Se actualizan las fichas en uso.

### Decisión
- **Punto de captura periódico**: Justo al final de `accionJugador`, después de `_registrarAccionEnLog(evento)`, verificando que `not self.fin` y que `self.acciones_linea_tiempo - self.puntos_control[-1].acciones_linea_tiempo >= self.k_checkpoint` (con K fijo es «múltiplo de K»; si K cambia al cargar una partida, garantiza al menos K acciones entre puntos, FR-419). En ese instante exacto, el reloj virtual ya avanzó al instante del siguiente turno del jugador y todos los eventos intermedios (enemigos, trampas, regeneraciones) ya fueron procesados; es el estado exacto previo a la decisión $n \times K + 1$.
- **Partida finalizada**: Si la acción causó `self.fin = True` (victoria o muerte), no se captura punto de control (acordado en clarificación c).
- **Punto de captura inicial (Punto 0)**: `iniciarJuego` no carga la sala inicial ni programa el primer turno; eso lo hace el controlador (`obtenerSala`) o `repetirPartida`. Por eso el punto 0 se captura de forma perezosa: al empezar `accionJugador` (antes de procesar la primera decisión) o en `exportar_estado`, si `puntos_control` está vacía, con `acciones = 0`. Así es el estado justo antes de la primera decisión.
- **Poda por retroceso**: En la rama de `GestorEventos.es_uso_de_pergamino`:
  1. Se ejecuta el retroceso en `PergaminoLogica`.
  2. Se decrementa `self.acciones_linea_tiempo -= 1` (`RetrocesoLogica.obtener_cambios_retroceso` revierte exactamente una acción por uso).
  3. Se podan de la lista de puntos de control todos aquellos con `acciones > self.acciones_linea_tiempo`. Si un punto de control coincide con el nuevo valor de `acciones_linea_tiempo`, se conserva.

---

## 3. Reutilización de `EstadoGuardadoLogica` y Alternativa de Bitácora

### Contexto del código
`EstadoGuardadoLogica.exportar(juego)` ya genera una instantánea completa y profunda en un `EstadoGuardadoDTO` (versión de estado 3), desconectada de los objetos vivos del juego. Incluye:
- Reloj y agenda de eventos completa.
- Jugador (vida, inventario, estado de antorcha, veneno).
- Salas cargadas, salidas, puertas, enemigos y trampas.
- Estado interno del generador aleatorio `random.Random.getstate()`.
- Bitácora de mensajes y líneas del log de reproducción.

### Alternativa de diseño a medir (Principio VII)
- **Alternativa A (copia completa exhaustiva)**: Clonar en cada punto de control toda la bitácora y todas las líneas de `acciones_log`.
  - *Problema*: Como el log es estrictamente de adición (*append-only*), en una partida de 5 000 acciones con $K=1$, guardar 5 000 copias completas de un log acumulativo implicaría almacenar $\approx \frac{5000 \times 5001}{2} \approx 12.5$ millones de entradas de log, disparando el uso de memoria RAM a cientos de megabytes y degradando el tiempo de captura por encima de 20 ms.
- **Alternativa B (instantánea de estado con marca de longitud en historiales)**: Guardar el estado completo de las entidades vivas, reloj y azar, pero en los historiales (*bitácora* y *acciones_log*) registrar únicamente la longitud actual (`len(bitacora)`, `len(acciones_log)`), o rebanadas (*slices*) compartidas. Al restaurar un punto de control, simplemente se trunca la bitácora viva a esa longitud.
- **Elección para el plan**: Se adopta la Alternativa B y la Alternativa A queda como la descartada que se mide en `--bench`. Concreción: `PuntoControlDTO` guarda `longitud_bitacora` y `longitud_acciones_log`, y su `estado` va con `bitacora` y `acciones_log` vacías (son prefijos de los historiales vivos, que solo crecen: el uso del pergamino se agrega al log, no lo recorta). Un test debe comprobar esa propiedad de prefijo.
- **Advertencia de costo**: la bitácora no es lo único grande; cada punto copia todas las salas cargadas. Si con K=1 el punto no cabe en 20 ms (FR-426), la contingencia a evaluar en el benchmark es copiar solo las salas cambiadas desde el punto anterior. Se decide con datos de `--bench`, no antes.

---

## 4. Formato binario v7 y política de compatibilidad

### Contexto del código
`adaptadores/AlmacenPartidaBinario.py` gestiona el formato binario de partida persistente:
- Cabecera: `MAGIA = b"CRPP"`, `VERSION_FORMATO = 6`.
- Estructura: tabla de salas al inicio, bloques nombrados empaquetados con `struct`, y pie al final con posiciones y offsets.
- Si `version != VERSION_FORMATO`, lanza `ErrorPartida(f"Versión del formato de partida no soportada: {version}...")`.

### Decisión
- **Incremento de versión**: `VERSION_FORMATO` pasa de 6 a 7.
- **Nuevos campos en v7**:
  1. `_CAMPO_K_CHECKPOINT`: entero unsigned de 16 o 32 bits indicando el valor de $K$ vigente de la partida.
  2. `_CAMPO_PUNTOS_CONTROL`: bloque que contiene el número de puntos de control guardados, seguido de la secuencia de puntos de control. Cada punto almacena:
     - `acciones_linea_tiempo` (uint32).
     - Longitud del sub-bloque de estado.
     - `EstadoGuardadoDTO` serializado con la estructura estándar de bloques.
- **Rechazo vs. Migración**:
  - Se decide **rechazo explícito** con mensaje claro (FR-425 y Principio VI).
  - *Justificación*: Una partida de la versión 6 o anterior no contiene puntos de control intermedios ni el historial de estados necesarios para sintetizarlos sin re-ejecutar toda la simulación desde el inicio. Intentar migrar silenciosamente crearía un archivo v7 ficticio sin puntos de control previos o exigiría reproducir la partida desde red (violando el presupuesto de red y la reproducibilidad offline). Un mensaje explicativo que indica que el archivo corresponde a una versión previa es transparente, determinista y seguro.

---

## 5. Validación temprana en CLI e interacción con `--replay`

### Contexto del código
En `main.py`, argumentos como `--hasta` se validan mediante conversores (`_instante_hasta`) que lanzan `argparse.ArgumentTypeError` ante valores no enteros o negativos. `argparse` atrapa este error, imprime el mensaje y finaliza la ejecución con código de salida 2 antes de inicializar servicios o adaptadores.

### Decisión
- **Conversor validador**: Crear `_intervalo_checkpoint(texto: str) -> int` en `main.py`:
  - Rechaza strings no numéricos o flotantes (`"2.5"`, `"abc"`): `"no es un número entero"`.
  - Rechaza enteros $\le 0$: `"el intervalo entre puntos de control debe ser un entero mayor o igual que 1"`.
  - Provoca salida inmediata con código 2 sin iniciar el juego ni tocar disco.
- **Reporte inicial de $K$**: En el controlador o al inicio de la sesión interactiva, el juego informa el valor de $K$ que rige la partida (por ejemplo: `Puntos de control cada: 10 acciones`) antes de recibir la primera orden del jugador (FR-416, SC-006).
- **Interacción con `--replay`**:
  - `--replay` opera en modo desatendido por lotes y sin vista (Principio IV).
  - Dado que la toma de puntos de control es puramente observacional y no afecta el azar ni los desempates (Principio II, FR-423), la partida reproducida llega al mismo desenlace independientemente de si se toman o no puntos de control.
  - `repetirPartida` (`--replay` y `--hasta`) no toma puntos de control: no cambian el desenlace y encarecerían la reproducción acotada de 008.

---

## 6. Estructuras de datos propias (Principio I)

### Restricciones constitucionales
- **Prohibido**: `dict` y `set` como índice o caché; `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`), `networkx`.
- **Permitido**: `list` como almacenamiento contiguo, `dataclass`, `tuple`, `struct`.

### Decisión de estructura
- **Estructura en memoria**: Clase envoltorio o lista contigua `list[PuntoControlDTO]` en `EstadoJuegoLogica` (o un módulo de apoyo `Logica/GestorPuntosControl.py`).
- **Invariante de orden**: Como las acciones del jugador avanzan de forma estrictamente monótona, cada nuevo punto de control capturado se añade al final (`append`). La lista está permanentemente ordenada por `acciones_linea_tiempo`.
- **Poda en retroceso**: Truncado desde el final con `pop()` mientras el último elemento tenga `acciones > limite`. Complejidad $O(m)$ donde $m \le 5$, sumamente eficiente.
- **Consulta para la capacidad 004**: Dado $k$, se expone `obtener_punto_control_reciente(k: int) -> PuntoControlDTO | None`.
  - Al estar la lista ordenada por `acciones`, se implementa una búsqueda hacia atrás lineal simple ($O(N/K)$) o una búsqueda binaria implementada a mano sin usar `bisect`. Como para 5 000 acciones con $K=10$ solo hay 500 elementos, el recorrido o la búsqueda binaria a mano toman menos de 0.05 ms.

---

## 7. Diseño del Benchmark `puntos_control` en `bench/`

### Objetivos (Principio VII, FR-426)
1. **Medición de ciclo de eventos con $K=1$**: Comprobar que en la cripta sintética de referencia el tiempo de turno con punto de control no supera 20 ms.
2. **Evaluación de distintos valores de $K$**: Comparar $K \in \{1, 10, 50, 100\}$ en partidas de hasta 5 000 acciones.
3. **Métricas a recolectar**:
   - Tiempo promedio y máximo de captura de un punto de control (ms).
   - Tiempo de ciclo de turno en instantes CON punto de control vs. SIN punto de control.
   - Consumo de memoria / tamaño de archivo serializado a 5 000 acciones.
   - Pasos de reproducción necesarios desde el punto más cercano hasta una acción arbitraria $k$ (debe ser $< K$).
4. **Comparativa de alternativas**:
   - Alternativa A: Copia completa de historiales.
   - Alternativa B (elegida): Copia de estado con marca de longitud en historiales.
   - Alternativa C (línea base): Sin puntos de control (reproducir siempre desde el inicio).
5. **Derivación de $K$ por defecto**:
   - A partir de la relación entre sobrecarga de tiempo ($\le 20$ ms), uso de memoria y distancia máxima de recuperación ($< K$), fijar el valor por defecto empíricamente defendible (preliminarmente propuesto $K=10$).

---

## 8. El historial del pergamino no forma parte del punto de control

`EstadoGuardadoLogica.restaurar` reinicia el historial de retroceso (`retroceso.reiniciar()`, "el historial del pergamino no se guarda"). Reanudar desde un punto de control se comporta igual: el pergamino no puede deshacer acciones anteriores al punto. Consecuencias:

- FR-422 se cumple para secuencias de acciones que no usan el pergamino sobre acciones previas al punto (en la práctica, en las 5 primeras acciones tras el punto). Las pruebas de T016 se escriben con esa condición.
- Para la capacidad 004: reconstruir un estado pasado debe reaplicar la secuencia efectiva de acciones (las acciones revertidas por el pergamino «dejan de existir»), no los usos del pergamino. Avisar a quien implementa 004.
- Guardar el historial en cada punto exigiría serializar `CambioDTO` con referencias a objetos vivos; queda fuera de esta capacidad.
