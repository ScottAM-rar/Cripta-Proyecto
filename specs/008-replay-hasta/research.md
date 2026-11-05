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

### Enfoque elegido: Tope de tiempo opcional en `_avanzarHastaProximoTurno`

El ciclo de eventos de la lógica de juego gobierna la ejecución de los eventos de enemigos, trampas y efectos temporales entre dos decisiones consecutivas del jugador.

Para acotar la ejecución:
1. `_avanzarHastaProximoTurno` recibe un parámetro opcional `tope: int | None`.
2. Antes de desapilar el siguiente evento del reloj, se consulta `siguiente = reloj.siguiente()`.
3. Si `siguiente is not None` y `siguiente.tiempo_ejecucion > tope`, el bucle `while` termina inmediatamente mediante `break` sin desapilar dicho evento (FR-402).
4. El límite es inclusivo (FR-403, clarificación Q1): si `siguiente.tiempo_ejecucion <= tope`, el evento se desapila y se ejecuta con normalidad.
5. Si `siguiente.tipo_accion == "TURNO_JUGADOR"` y su tiempo es $\le tope$, se extrae y se da paso al siguiente turno del jugador. Si su tiempo es $> tope$, se interrumpe el avance y el turno del jugador permanece agendado en el reloj sin consumirse.
6. En `EstadoJuegoLogica.repetirPartida`, si tras ejecutar una acción o al evaluar el inicio de la siguiente el reloj se detuvo por alcanzar el tope, se interrumpe la iteración sobre el log. De este modo, los registros restantes del archivo no se procesan, logrando un costo computacional proporcional a lo reproducido (FR-412).

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
- Se crea la clase `ResultadoReplayHastaDTO` en `DTO/ResultadoReplayHastaDTO.py` con los siguientes campos:
  - `instante_alcanzado: int` (tiempo del reloj tras el último evento procesado).
  - `acciones_reproducidas: int` (contador de acciones del jugador ejecutadas).
  - `id_sala_jugador: int` (sala donde quedó el jugador).
  - `vida_jugador: int` (puntos de vida actuales).
  - `inventario_llaves: list[str]` (identificadores de llaves en poder del jugador).
  - `inventario_objetos: list[str]` (nombres o identificadores de objetos en posesión).
  - `enemigos_sala: list[tuple[str, int]]` (lista de pares `(nombre_o_id, vida_actual)` de enemigos vivos en la sala actual).
  - `partida_terminada: bool` (indica si la partida concluyó antes o al llegar a $t$).
  - `motivo_terminacion: str | None` (detalle de la causa de fin: victoria, muerte por enemigo/trampa, o `None` si sigue en curso).
  - `log_agotado: bool` (verdadero si el archivo de registro se terminó antes de alcanzar el instante $t$).
- La función `reproducir()` en `main.py` recibe este DTO y formatea la salida de texto en la consola de manera legible (ver `contracts/salida-texto.md`).

### 3.3 Tratamiento de registros del log sin costo temporal
- Ciertas acciones del log, como la navegación en la mochila (`MOVER_CURSOR_SIGUIENTE`, `MOVER_CURSOR_ANTERIOR`), tienen costo temporal 0.
- Si el reloj virtual actual es $\le t$ y la simulación no ha sido cortada por el tope, estas acciones se reproducen para mantener la consistencia del cursor del inventario con las acciones del jugador.
- Si el reloj ya alcanzó el tope y se cortó el ciclo de turnos, no se procesan más registros.

### 3.4 Detección de fin de partida y log agotado (FR-404, FR-405)
- **Partida terminada antes de $t$**: Se detecta si `self.fin` es verdadero tras ejecutar una acción o evento de avance de turno, con `reloj.tiempo_actual <= t`. En este caso, el reloj se congela en el instante exacto de la terminación (por ejemplo, el momento de la muerte) y se reporta `partida_terminada = True` junto con su motivo.
- **Log agotado antes de $t$**: Se detecta cuando el iterador de registros cronológicos del log se vacía por completo mientras `reloj.tiempo_actual < t` y la partida aún no ha terminado (`not self.fin`). Se reporta `log_agotado = True` y se emite la advertencia requerida por FR-405.

### 3.5 Definición formal de «instante alcanzado»
- El «instante alcanzado» corresponde estrictamente al valor `self.estadoJuego.reloj.tiempo_actual` al momento de finalizar la ejecución.
- Garantía matemática: `instante_alcanzado <= t`. Si no hubo eventos programados exactamente en $t$, el reloj refleja el instante del último evento efectivamente ejecutado.

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
- **Criterio de aceptación duro**: Conteo de eventos procesados y acciones ejecutadas ($K_{b} \le K_{total} / 2$). La razón de tiempos se reporta como métrica informativa para evitar falsos negativos por jitter del sistema operativo.
