# Especificación de capacidad: Puntos de control de la partida

**Carpeta**: `007-puntos-de-control`

**Creada**: 2026-11-07

**Estado**: Borrador

**Entrada**: Capacidad de la línea de tiempo (Parte II, §3.6): guardar copias completas del estado de la partida a intervalos configurables. Requisitos con prefijo FR-4xx, continuando desde FR-414.

## Contexto y motivación

La consulta de estados pasados (capacidad 004) necesita mostrar el estado de la partida en cualquier instante anterior. Copiar el estado completo en cada acción sería prohibitivo. El enunciado (§3.6) autoriza guardar copias completas llamadas **puntos de control**, pero no más de una cada K acciones del jugador. Esta capacidad define qué es un punto de control, cuándo se toma, cómo se configura K y qué garantías ofrece al jugador y a quien revisa la partida.

**Lo existente y vigente (no se re-especifica)**: el reloj virtual con agenda de eventos; el inventario del jugador; los comportamientos de los enemigos; el guardado binario versionado; `partida.log` y la reproducción con `--replay`; el pergamino de retroceso (limitado a 5 acciones); la caché persistente con validación de versión.

**Por qué importa**: sin puntos de control, la historia #k (capacidad 004) tendría que reproducir la partida desde el principio en cada consulta. Con ellos, puede partir desde el punto de control más cercano anterior a la acción pedida. Esta capacidad entrega la infraestructura de guardado periódico; no define los comandos que la aprovechan.

## Clarificaciones

### Sesión 2026-11-07

- Q: ¿Qué eventos provocados por el usuario se contabilizan exactamente como una acción del jugador para el avance del contador K? (FR-418) → A: Cuentan solo las acciones del jugador aceptadas y ejecutadas (las rechazadas no cuentan). El contador es el número de acciones de la línea de tiempo vigente: si el pergamino revierte m acciones, el contador disminuye en m. El uso del pergamino en sí no cuenta como acción.
- Q: ¿El estado inicial de la partida (antes de que el jugador ejecute su primera acción) debe registrarse automáticamente como un punto de control? (FR-418) → A: Sí, el estado inicial de la partida siempre se registra automáticamente como punto de control 0.
- Q: ¿En qué instante preciso del ciclo de turno se captura el punto de control correspondiente a un múltiplo n×K de acciones? (FR-418) → A: El punto de control n se toma cuando, completada la acción n×K, llega el turno del jugador: es el estado justo antes de su decisión n×K+1 (con el reloj ya avanzado y todos los eventos anteriores aplicados). Si la acción n×K termina la partida, no se toma.
- Q: ¿Qué sucede con los puntos de control que se hayan registrado con posterioridad a un estado temporal al que el pergamino de retroceso hace regresar? (FR-418) → A: Se descartan permanentemente todos los puntos de control tomados con posterioridad al estado al que se retrocedió.
- Q: ¿Qué valor del intervalo K rige la partida si se carga un archivo guardado con un intervalo de control distinto al especificado en la línea de comandos actual? (FR-414, FR-424) → A: Si se pasa `--checkpoint-cada`, prevalece el nuevo K para acciones futuras; si se omite, se conserva el K del archivo. Los puntos existentes se preservan.

*(Todas las ambigüedades identificadas en la especificación fueron resueltas durante la sesión).*

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Configurar el intervalo entre puntos de control (Prioridad: P1)

Quien inicia la partida decide cada cuántas acciones el programa guarda un punto de control, pasando `--checkpoint-cada K`. Si omite la bandera, el programa usa un valor por defecto que informa al arrancar. Si K no es válido, la partida no empieza y el programa explica el problema.

**Por qué esta prioridad**: sin la opción de configurar K no existe la capacidad; es el punto de entrada obligatorio.

**Prueba independiente**: lanzar el programa con distintos valores de K (válidos, cero, negativos, decimales, texto) y verificar que arranca o rechaza según corresponda, sin necesidad de jugar ninguna acción.

**Escenarios de aceptación**:

1. **Dado** que el jugador invoca la partida con `--checkpoint-cada 10`, **cuando** el programa arranca, **entonces** la partida se inicia y K queda fijado en 10. *(FR-414)*
2. **Dado** que el jugador invoca la partida con `--checkpoint-cada 1`, **cuando** el programa arranca, **entonces** la partida se inicia con K = 1 (el intervalo mínimo permitido). *(FR-414, FR-415)*
3. **Dado** que el jugador no incluye `--checkpoint-cada`, **cuando** el programa arranca, **entonces** la partida se inicia con el valor de K por defecto y el programa informa ese valor antes de que el jugador tome su primera decisión. *(FR-416)*
4. **Dado** que el jugador invoca la partida con `--checkpoint-cada 0`, **cuando** el programa intenta arrancar, **entonces** la partida no comienza y el programa muestra un mensaje claro indicando que K debe ser un entero mayor o igual que 1. *(FR-417)*
5. **Dado** que el jugador invoca la partida con `--checkpoint-cada -5`, **cuando** el programa intenta arrancar, **entonces** la partida no comienza y el programa muestra un mensaje claro. *(FR-417)*
6. **Dado** que el jugador invoca la partida con `--checkpoint-cada 2.5`, **cuando** el programa intenta arrancar, **entonces** la partida no comienza y el programa muestra un mensaje claro. *(FR-417)*
7. **Dado** que el jugador invoca la partida con `--checkpoint-cada abc`, **cuando** el programa intenta arrancar, **entonces** la partida no comienza y el programa muestra un mensaje claro. *(FR-417)*

---

### Historia 2 — Tomar puntos de control durante la partida (Prioridad: P1)

Mientras el jugador juega, el programa guarda silenciosamente un punto de control cada K acciones. El jugador no percibe ninguna pausa ni cambio en el juego; los puntos de control ocurren de forma transparente.

**Por qué esta prioridad**: es el comportamiento central de la capacidad; sin él, la historia #k (capacidad 004) no tiene de dónde arrancar.

**Prueba independiente**: jugar una partida corta con K pequeño y comprobar, mediante la reproducción con `--replay`, que existen puntos de control en los instantes esperados y que reanudar desde cada uno produce la misma partida.

**Escenarios de aceptación**:

1. **Dado** K = 5 y una partida de 15 acciones que continúa después de la acción 15, **cuando** el jugador completa su quinta, décima y quinceava acción y le llega el turno, **entonces** además del punto de control 0 el programa ha tomado un punto de control periódico justo antes de la decisión 6, de la 11 y de la 16, y no más. *(FR-418, FR-419)*
2. **Dado** K = 3 y una partida en curso, **cuando** el jugador ejecuta 7 acciones, **entonces** existen el punto de control 0 y exactamente 2 periódicos (justo antes de las decisiones 4 y 7), no uno más. *(FR-418, FR-419)*
3. **Dado** que se toma un punto de control, **cuando** ocurre, **entonces** el jugador no percibe ninguna pausa, interrupción ni mensaje adicional. *(FR-420)*
4. **Dado** que se toma un punto de control, **cuando** ocurre, **entonces** el punto de control incluye el estado completo: reloj virtual, posición e inventario del jugador, estado de cada enemigo, salas cargadas, puertas, bitácora, estado del generador aleatorio y, cuando exista, lo que el jugador conoce del mapa. *(FR-421)*

---

### Historia 3 — Reproducibilidad desde un punto de control (Prioridad: P1)

Reanudar la partida desde cualquier punto de control y seguir con exactamente las mismas acciones produce una partida idéntica a la original, incluyendo el azar, como si nunca se hubiera parado.

**Por qué esta prioridad**: si los puntos de control no son reproducibles, la historia #k no puede ser correcta ni verificable (Principio II).

**Prueba independiente**: tomar una partida con sus puntos de control, reanudar desde uno de ellos con las mismas acciones y comparar `partida.log` línea a línea con la original.

**Escenarios de aceptación**:

1. **Dado** una partida completa con puntos de control, **cuando** se reanuda desde el punto de control número n y se repiten las mismas acciones, **entonces** `partida.log` a partir de ese punto es idéntico al original, incluidos los eventos aleatorios. *(FR-422, Principio II)*
2. **Dado** la misma cripta, la misma semilla y las mismas acciones, **cuando** se juega con K = 1 y con K = 100, **entonces** el resultado final de la partida es el mismo en ambos casos. *(FR-423)*
3. **Dado** la misma cripta, la misma semilla y las mismas acciones, **cuando** se juega con K = 1 y con K = 1000 (mayor que el número de acciones), **entonces** el resultado final de la partida es el mismo. *(FR-423)*

---

### Historia 4 — Guardar y cargar una partida conserva sus puntos de control (Prioridad: P2)

Cuando el jugador guarda la partida y la vuelve a cargar, todos los puntos de control guardados hasta ese momento siguen disponibles. Un archivo de partida de una versión anterior se detecta como incompatible o se migra de forma explícita; nunca se carga sin avisar.

**Por qué esta prioridad**: sin esta garantía, los puntos de control se perderían al cerrar el programa, inutilizando la historia #k entre sesiones.

**Prueba independiente**: guardar una partida con varios puntos de control, cerrar el programa, cargarlo de nuevo y comprobar que los puntos de control están presentes y son reproducibles.

**Escenarios de aceptación**:

1. **Dado** una partida con N puntos de control guardados, **cuando** se guarda la partida y se carga en una nueva sesión, **entonces** los N puntos de control están disponibles y reproducen el mismo estado que antes de guardar. *(FR-424)*
2. **Dado** un archivo de partida generado con una versión anterior del programa (Apéndice B: «Se carga un archivo de partida de la primera parte»), **cuando** el programa intenta cargarlo, **entonces** lo rechaza con un mensaje claro o lo migra de forma explícita; nunca lo carga en silencio como si fuera compatible. *(FR-425, Principio VI)*

---

### Historia 5 — Rendimiento transparente (Prioridad: P2)

Tomar un punto de control no introduce ninguna pausa perceptible en el ciclo de decisiones del jugador. El tiempo entre dos decisiones consecutivas del jugador no supera el límite establecido ni siquiera en los instantes en que se toma un punto de control.

**Por qué esta prioridad**: si tomar un punto de control congela el juego, la experiencia se degrada en cada múltiplo de K, especialmente con K pequeño.

**Prueba independiente**: ejecutar `--bench` sobre la cripta de referencia (§6.1) con K = 1 (peor caso: punto de control en cada acción) y medir el tiempo del ciclo de eventos.

**Escenarios de aceptación**:

1. **Dado** la cripta de referencia (§6.1) y K = 1 (peor caso), **cuando** se ejecuta `--bench`, **entonces** el ciclo de eventos entre dos decisiones consecutivas del jugador no supera 20 ms en ningún punto de control. *(FR-426, Principio VII)*
2. **Dado** `--bench`, **cuando** se ejecuta sobre criptas sintéticas deterministas por semilla con distintos valores de K, **entonces** el informe incluye el tiempo del ciclo de eventos en los instantes de punto de control frente a los instantes sin punto de control. *(FR-426)*

---

### Casos límite

- `--checkpoint-cada 0`: se rechaza; el programa informa que K debe ser ≥ 1 y no inicia la partida. *(FR-417)*
- Valor negativo de K: se rechaza con mensaje claro. *(FR-417)*
- Valor decimal (p. ej. `2.5`): se rechaza con mensaje claro. *(FR-417)*
- Valor no numérico (p. ej. `abc`): se rechaza con mensaje claro. *(FR-417)*
- K mayor que el número total de acciones de la partida: existe el punto de control 0 inicial y no se genera ningún punto periódico adicional (⌊N/K⌋ = 0); no se emite ninguna advertencia ni error y la partida procede con normalidad.
- Estado inicial de la partida: se registra automáticamente como el punto de control 0 antes de procesar la primera acción del jugador.
- Instante exacto del punto de control n: se toma cuando, completada la acción n×K, llega el turno del jugador (estado justo antes de su decisión n×K + 1, con reloj avanzado y eventos aplicados). Si la acción n×K termina la partida, no se toma.
- Acciones rechazadas y uso del pergamino: las acciones rechazadas no incrementan el contador K. El uso del pergamino no cuenta como acción y, al revertir m acciones de la línea de tiempo vigente, el contador K disminuye en m.
- Puntos de control tras retroceso con pergamino: se descartan permanentemente todos los puntos de control tomados con posterioridad al estado al que se retrocedió.
- Carga de partida guardada con K distinto: si la invocación actual especifica `--checkpoint-cada K`, dicho valor prevalece para las acciones futuras; si se omite, se conserva el valor de K guardado en el archivo. En ambos casos se preservan todos los puntos de control existentes.

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Configuración de K**

- **FR-414**: La partida DEBE aceptar la bandera `--checkpoint-cada K`, donde K es un entero proporcionado por el jugador. Si la bandera está presente, la partida DEBE iniciarse con ese valor de K.
- **FR-415**: El valor de K DEBE ser un entero mayor o igual que 1. No se admiten valores menores que 1.
- **FR-416**: Cuando el jugador no proporciona `--checkpoint-cada`, el programa DEBE usar un valor de K por defecto. Ese valor por defecto DEBE ser un entero mayor o igual que 1. El programa DEBE informar el valor de K por defecto antes de que el jugador tome su primera decisión. La cifra concreta del valor por defecto no se fija en esta especificación; se decide en la fase de plan con mediciones.
- **FR-417**: Si el valor proporcionado para K es cero, negativo, decimal o no numérico, el programa DEBE rechazarlo con un mensaje claro que indique el motivo, y la partida NO DEBE iniciarse.

**Toma de puntos de control**

- **FR-418**: Al iniciar la partida, el estado inicial (antes de la primera acción del jugador) DEBE registrarse automáticamente como el punto de control 0. Durante la partida, el programa DEBE tomar un punto de control cada K acciones del jugador. Cuentan solo las acciones aceptadas y ejecutadas por el juego; las acciones rechazadas no incrementan el contador. El contador de acciones corresponde al número de acciones de la línea de tiempo vigente: si el pergamino de retroceso revierte m acciones, el contador disminuye en m y todos los puntos de control registrados con posterioridad a dicho estado DEBEN descartarse permanentemente. El uso del pergamino en sí no cuenta como acción. Cada punto de control periódico n DEBE tomarse cuando, completada la acción n×K, llega el turno del jugador (estado justo antes de su decisión n×K + 1, con el reloj avanzado y todos los eventos anteriores aplicados). Si la acción n×K termina la partida, no se toma dicho punto de control. El número de puntos de control periódicos tomados entre las acciones 1 y N (inclusive) de la línea de tiempo vigente DEBE ser exactamente ⌊N/K⌋ si la partida continúa tras la acción N. No se toman puntos de control adicionales fuera del inicial y los múltiplos de K.
- **FR-419**: No DEBE tomarse más de un punto de control cada K acciones del jugador. El programa DEBE contabilizar exactamente K acciones entre dos puntos de control consecutivos.
- **FR-420**: Tomar un punto de control DEBE ser transparente para el jugador: no DEBE producir ningún mensaje, pausa ni cambio visible en la interfaz.
- **FR-421**: Un punto de control DEBE ser una copia completa del estado de la partida en el instante en que se toma. El estado DEBE incluir, como mínimo: el reloj virtual y lo que está pendiente de ocurrir, la posición e inventario del jugador, el estado de cada enemigo, las salas ya visitadas o cargadas, el estado de las puertas, la bitácora de la partida (`partida.log` hasta ese instante), el estado del generador aleatorio y, cuando la capacidad de niebla de guerra esté activa, lo que el jugador conoce del mapa hasta ese instante. La lista detallada de campos y el número de versión del formato de archivo los define quien mantiene el formato, no esta especificación.

**Reproducibilidad**

- **FR-422**: Reanudar la partida desde cualquier punto de control y ejecutar las mismas acciones que en la partida original DEBE producir exactamente la misma secuencia de eventos, incluyendo todos los resultados aleatorios. Esto DEBE cumplirse incluso cuando el contenido de la cripta se descarga en un orden distinto al original (Principio II).
- **FR-423**: La elección de K NO DEBE cambiar el resultado final de la partida. Misma cripta, misma semilla y mismas acciones DEBEN producir la misma partida independientemente del valor de K.

**Persistencia**

- **FR-424**: Al guardar la partida, DEBEN guardarse también todos los puntos de control tomados hasta ese momento y el valor vigente de K. Al cargar la partida en una sesión posterior, esos puntos de control DEBEN estar disponibles y ser reproducibles. Si en la sesión de carga se especifica explícitamente `--checkpoint-cada K`, dicho nuevo valor de K DEBE regir la toma de puntos de control para las acciones futuras; si se omite la bandera, DEBE mantenerse el K guardado en el archivo. En ambos casos, todos los puntos de control previamente registrados DEBEN preservarse.
- **FR-425**: Un archivo de partida generado con una versión anterior del programa DEBE detectarse como incompatible y rechazarse con un mensaje claro, o migrarse de forma explícita con aviso al jugador. NUNCA DEBE cargarse en silencio como si fuera compatible con la versión actual (Principio VI, Apéndice B).

**Rendimiento**

- **FR-426**: Tomar un punto de control NO DEBE hacer que el ciclo de eventos entre dos decisiones consecutivas del jugador supere 20 ms en la cripta de referencia (§6.1), ni siquiera cuando el punto de control ocurre en ese ciclo. Este límite se mide con `--bench` sobre criptas sintéticas deterministas por semilla (Principio VII).

### Entidades clave

- **Punto de control**: copia completa e instantánea del estado de la partida en un instante determinado. Permite reanudar la partida desde ese instante con garantía de reproducibilidad. Se toma cada K acciones del jugador.
- **K (intervalo de punto de control)**: entero ≥ 1 que fija cuántas acciones del jugador deben transcurrir entre dos puntos de control consecutivos. Se configura con `--checkpoint-cada` o toma un valor por defecto.
- **Estado de la partida**: conjunto de toda la información necesaria para reproducir la partida desde ese instante: reloj, posición del jugador, inventario, enemigos, salas, puertas, bitácora y generador aleatorio (y mapa conocido cuando aplique).
- **Acción del jugador**: decisión aceptada y ejecutada por el juego que avanza la partida y la línea de tiempo vigente. Las órdenes rechazadas y el uso del pergamino no cuentan como acción; al revertir m acciones con el pergamino, el contador se reduce en m.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: El 100 % de los escenarios de aceptación de las Historias 1–5 pasan sin errores.
- **SC-002**: Reanudar desde cualquier punto de control y repetir las mismas acciones produce un `partida.log` idéntico al original a partir de ese instante, en el 100 % de las partidas de prueba.
- **SC-003**: Jugar la misma partida con K = 1 y con K igual al número total de acciones produce el mismo resultado final en el 100 % de las partidas de prueba.
- **SC-004**: Con K = 1 en la cripta de referencia (§6.1), el tiempo del ciclo de eventos entre dos decisiones del jugador medido con `--bench` no supera 20 ms en ninguna de las mediciones.
- **SC-005**: Cargar un archivo de partida de la Parte I (Apéndice B) produce un mensaje de incompatibilidad o migración explícita, nunca una carga silenciosa, en el 100 % de los intentos de carga.
- **SC-006**: El programa informa el valor de K (ya sea el proporcionado o el por defecto) antes de que el jugador tome su primera decisión, en el 100 % de las partidas iniciadas.

## Supuestos

- El contador de acciones del jugador comienza en 0 al inicio de la partida (donde se registra el punto de control 0). El siguiente punto de control se toma al alcanzar K acciones del jugador.
- «Acción del jugador» incluye únicamente decisiones aceptadas y ejecutadas por el juego. Excluye órdenes inválidas/rechazadas, comandos de consulta, el uso del pergamino en sí y las acciones internas del programa (como mover enemigos o actualizar el reloj).
- El valor por defecto de K existe y es un entero ≥ 1; su cifra concreta se decide en la fase de plan con mediciones de rendimiento, siguiendo el Principio VII.
- Los puntos de control se almacenan dentro del mismo archivo de partida que el guardado normal; no se crean archivos separados por punto de control.
- El estado del generador aleatorio es parte del estado de la partida y, por tanto, parte de cada punto de control, como exige el Principio II.
- «Cripta de referencia» en FR-426 y SC-004 se refiere a §6.1 del enunciado, que define la cripta y la carga usadas en los benchmarks oficiales.

## Fuera de alcance

- Los comandos `historia <t>` e `historia #k` y el recorte de la línea de tiempo por el pergamino (capacidad 004).
- La bandera `--replay … --hasta` (capacidad 008).
- La lista detallada de campos del punto de control y el número de versión del formato de archivo (los define quien mantiene el formato).
- El contenido del mapa conocido del jugador (capacidad de niebla de guerra).
- La lógica interna de cómo se almacenan o comprimen los puntos de control (es una decisión de plan, no de spec).
