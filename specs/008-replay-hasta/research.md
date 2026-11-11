# Investigación (Fase 0): Reproducir partida grabada hasta un instante dado (replay-hasta)

No quedan marcadores `NEEDS CLARIFICATION` en la especificación [spec.md](spec.md). Este documento define el **cómo** técnico respetando la constitución del proyecto y los requisitos funcionales FR-401 a FR-413.

---

## 1. Código existente que se reutiliza (no se reescribe)

| Componente | Módulo | Función / Rol actual | Adaptación para esta capacidad |
|---|---|---|---|
| CLI Parser | `main.py` (`leer_argumentos`) | Analiza argumentos de consola con `argparse` (`--replay`, `--cache-size`). | Se añade el argumento opcional `--hasta` con validador de tipo `_instante_hasta` y verificación de compatibilidad antes de crear el servicio. |
| Función de reproducción | `main.py` (`reproducir`) | Ejecuta `servicio.repetirPartida(nombre)` e imprime el resumen final en consola. | Si se suministra `hasta`, delega la reproducción acotada y formatea en pantalla el `ResultadoReplayHastaDTO` recibido del servicio. |
| Servicio de Juego | `Servicio/EstadoJuegoServicio.py` | `repetirPartida(archivo)` lee el log de disco y delega en la lógica. | Admite el parámetro opcional `hasta: int | None`. Devuelve `ResultadoReplayHastaDTO` si se especificó `hasta`, o `list[ResultadoEventoDTO]` si `hasta is None`. |
| Lógica de Repetición | `Logica/EstadoJuegoLogica.py` | `repetirPartida(log)` recrea la partida paso a paso mediante `accionJugador`. | Propaga el tope `hasta` a `accionJugador`. Si el tope corta la simulación, cesa la lectura del log y construye el reporte exhaustivo (FR-404, FR-412). |
| Avance de Turno | `Logica/EstadoJuegoLogica.py` | `_avanzarHastaProximoTurno()` procesa eventos hasta el próximo turno del jugador. | Recibe `tope: int | None`. Se detiene sin extraer el siguiente evento si su tiempo es estrictamente mayor que `tope` (FR-402, FR-403). |
| Reloj Virtual | `Logica/RelojVirtual.py` | Agenda de eventos basada en montículo propio (`heap`) con `tiempo_actual`. | Se inspecciona `reloj.siguiente()` sin desapilar para evaluar la condición de corte respecto al tope. |

---

## 2. Decisión de truncamiento en el ciclo de eventos (Opción b)

### Enfoque elegido: Tope de tiempo opcional en `_avanzarHastaProximoTurno` y regla de la decisión del jugador

El ciclo de eventos de la lógica de juego gobierna la ejecución de los eventos de enemigos, trampas y efectos temporales entre dos decisiones consecutivas del jugador. En la Parte I el jugador decide en el instante actual del reloj y su acción ocurre en ese momento; su costo solo programa el turno siguiente (`accionJugador`).

Para acotar la ejecución según la especificación corregida (FR-402, FR-403, FR-406):
1. `_avanzarHastaProximoTurno` recibe un parámetro opcional `tope: int | None`.
2. Antes de desapilar el siguiente evento del reloj, se consulta `siguiente = reloj.siguiente()`.
3. Si `siguiente is not None` y `siguiente.tiempo_ejecucion > tope`, el bucle termina con `break` sin desapilar dicho evento (FR-402). Esto incluye un `TURNO_JUGADOR` posterior al tope, que permanece agendado.
4. El límite es inclusivo para los eventos de los demás actores (FR-403): si `siguiente.tiempo_ejecucion <= tope`, el evento se desapila y se ejecuta con normalidad. Si es el `TURNO_JUGADOR` (con tiempo $\le$ tope), se extrae y el ciclo devuelve el control, como hoy.
5. **Decisión del jugador en $t$ (FR-403, FR-406)**: en `EstadoJuegoLogica.repetirPartida`, antes de tomar cada registro del log (acción con costo, movimiento de cursor o pergamino) se comprueba `reloj.tiempo_actual < hasta`. Si no se cumple, se detiene la lectura: la decisión del jugador cuyo instante es mayor o igual que $t$ no se ejecuta. Con $t = 0$ el reloj vale 0 y no se ejecuta ninguna acción, sin regla especial.
6. **Compleción del instante $t$ (FR-403)**: si el `TURNO_JUGADOR` consumido tiene tiempo exactamente $t$, pueden quedar eventos de otros actores con tiempo $t$ y número de secuencia posterior. `_completarInstante(hasta)` los ejecuta con el mismo cuerpo de procesamiento del ciclo (se extrae a un método auxiliar compartido para no duplicar el código) y no ejecuta ninguna decisión del jugador. Así el estado es el posterior a todos los eventos de los demás actores en $t$.
7. Si la partida termina (`self.fin`) se detiene de inmediato, congelando el reloj en el instante de la terminación.
8. Al detenerse, `repetirPartida` cesa la lectura del log: los registros restantes no se procesan, logrando un costo proporcional a lo reproducido (FR-412).

### Alternativas consideradas y descartadas

| Alternativa | Descripción | Por qué se descarta (razón técnica concreta) |
|---|---|---|
| **Opción a: Cortar solo entre acciones del jugador** | En `repetirPartida`, comprobar si el tiempo acumulado o del siguiente registro supera `t` y detener la lectura del log. | **Incumple FR-402**. La acción del jugador programa su próximo turno para un instante futuro $t_{futuro}$. Si $t_{futuro} > t$, `_avanzarHastaProximoTurno` sin tope ejecutaría todos los eventos de enemigos hasta $t_{futuro}$, procesando eventos con tiempo virtual mayor que $t$. Si no se avanzara, los eventos de enemigos previos a $t$ no ocurrirían. |
| **Opción c: Reproducir el log completo y recortar la salida** | Ejecutar la simulación completa de la partida y luego consultar el estado histórico o reconstruir la salida en $t$. | **Incumple FR-412**. El tiempo de procesamiento dependería del tamaño total del log $N$ y no del instante $t$. Reproducir hasta $t=10$ en una partida de 4 000 acciones tardaría exactamente lo mismo que reproducir las 4 000 acciones. |

> [!NOTE]
> Las alternativas **a** y **c** se implementan como variantes instrumentadas dentro del módulo de pruebas de rendimiento `bench/replay.py` para demostrar empíricamente en `--bench` la superioridad y necesidad de la Opción b (Principio VII).

---

## 3. Decisiones de diseño específicas

### 3.1 Validación temprana de `--hasta` (FR-407, FR-408)
- En `main.py`, se define la función validadora `_instante_hasta(texto: str) -> int`:
  - Intenta convertir con `int(texto)`. Si falla, emite `argparse.ArgumentTypeError(f"{texto!r} no es un número entero")`.
  - Si el valor es negativo (`valor < 0`), emite `argparse.ArgumentTypeError("el instante virtual debe ser mayor o igual que 0")`.
- En `leer_argumentos` / `main()`, se valida la coexistencia de argumentos:
  - Si `args.hasta is not None and not args.replay`: se rechaza de inmediato con el mensaje claro `Error: el argumento --hasta requiere especificar una partida con --replay.` y el proceso termina con código de salida `2` (o `1`) sin crear `EstadoJuegoServicio`, sin conectar a la red y sin abrir ningún archivo (Principio IV y VI).

### 3.2 Estructura de salida y separación de responsabilidades (FR-404, Principio IV)
- La capa de lógica (`EstadoJuegoLogica`) no interactúa con `sys.stdout` ni con la consola.
- Se crea la clase `ResultadoReplayHastaDTO` en `DTO/ResultadoReplayHastaDTO.py` con los campos descritos en [data-model.md](data-model.md): instante pedido y alcanzado, acciones reproducidas, sala, vida, estadísticas vigentes (ataque, defensa, velocidad), llaves, objetos, efectos activos, enemigos de la sala (identificador de instancia, nombre y vida), fin de partida con su motivo y log agotado.
- El mapa conocido del jugador no se incluye: depende de la capacidad de niebla de guerra y está diferido (Assumptions de `spec.md`).
- La función `reproducir()` en `main.py` recibe este DTO y formatea la salida de texto (ver `contracts/salida-texto.md`).

### 3.3 Registros del log sin costo temporal (FR-403)
- Ciertas acciones del log, como la navegación en la mochila (`MOVER_CURSOR_SIGUIENTE`, `MOVER_CURSOR_ANTERIOR`) o el uso del pergamino, no avanzan el reloj por sí mismas: forman parte de la decisión del jugador en el instante actual.
- Se reproducen solo si `reloj.tiempo_actual < hasta`, igual que cualquier otra decisión del jugador. Si el reloj ya alcanzó $t$, no se procesan más registros.

### 3.4 Detección de fin de partida y log agotado (FR-404, FR-405)
- **Partida terminada**: se detecta si `self.fin` es verdadero tras ejecutar una acción o el avance de turno. El reloj queda congelado en el instante exacto de la terminación y se reporta `partida_terminada = True` junto con su motivo. El aviso de que la partida concluyó «antes de alcanzar $t$» se emite solo si `instante_alcanzado < instante_pedido`; si concluye exactamente en $t$, se informa el estado final sin ese aviso.
- **Log agotado**: se detecta cuando los registros del log se terminan mientras `reloj.tiempo_actual < t` y la partida no ha terminado (`not self.fin`). Se reporta `log_agotado = True` y se emite la advertencia de FR-405. Si el reloj llegó exactamente a $t$ no hay aviso.

### 3.5 Definición formal de «instante alcanzado»
- El «instante alcanzado» corresponde al valor `self.estadoJuego.reloj.tiempo_actual` al finalizar la ejecución, es decir, el tiempo del último evento efectivamente ejecutado.
- Garantía: `instante_alcanzado <= t`. Con $t = 0$ vale 0.

### 3.6 Determinismo estricto (FR-411, Principio II)
- El orden de ejecución de eventos simultáneos está determinado por la tupla `(tiempo_ejecucion, id_secuencia)` del `RelojVirtual`.
- La lista de enemigos en la sala se ordena por identificador único de enemigo para que la salida en pantalla no dependa de ningún orden interno de almacenamiento o iteración.

---

## 4. Mediciones de rendimiento con `--bench` (Principio VII)

Se define un bloque de evaluación de rendimiento denominado `replay` en `bench/replay.py`:
- **Cargas sintéticas**: Se implementa un generador determinista de partidas sintéticas basado en semilla (`tests_labs/generador_partidas.py`) que genera archivos de log válidos con longitudes de:
  - 250 acciones
  - 1 000 acciones
  - 4 000 acciones
- **Experimentos comparativos**:
  1. **Reproducción completa vs Acotada a $t = T/2$**: Compara el conteo de eventos y tiempo de CPU de la Opción b al reproducir la mitad del tiempo virtual frente a la reproducción completa.
  2. **Opción b frente a Alternativa a (corte por acción)**: Comprueba que la opción b no procesa eventos espurios más allá de $t$.
  3. **Opción b frente a Alternativa c (reproducción total y recorte)**: Demuestra que la Opción b consume aproximadamente el 50% de operaciones en $T/2$, mientras que la opción c consume el 100% independientemente de $t$.
- **Criterio de aceptación duro** (SC-003 de `spec.md`): conteo de eventos procesados para $t = T/2$ menor o igual que $0.55 \times$ los de la reproducción completa. La razón de tiempos se reporta como métrica informativa para evitar falsos negativos por jitter del sistema operativo.
