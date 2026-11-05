# Feature Specification: Reproducir partida grabada hasta un instante dado (replay-hasta)

**Feature Branch**: `008-replay-hasta`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Capacidad: reproducir una partida grabada solo hasta un instante dado (nombre sugerido de la carpeta: replay-hasta). Prefijo de requisitos: FR-4xx. Escribe la especificación en español, desde el punto de vista del juego y de quien lo juega o lo revisa. No nombres estructuras de datos, clases ni módulos. Todo lo que no esté claro márcalo como [NEEDS CLARIFICATION] en vez de suponerlo."

## Contexto y motivación

Actualmente la opción `--replay` reproduce un archivo de registro (`PARTIDA.log`) de forma completa desde el inicio hasta el fin de la grabación. Cuando una persona necesita auditar o depurar un suceso específico de una partida (por ejemplo, entender qué ocurrió exactamente en el instante previo a la derrota del jugador o evaluar una secuencia crítica de turnos), se ve obligada a esperar la reproducción íntegra y analizar únicamente el estado final.

La opción `--hasta t` permite acotar la reproducción para que se detenga de forma determinista en un instante específico `t` del reloj virtual del juego, presentando cómo quedó el estado del juego en ese punto exacto. Quien revisa debe poder predecir con exactitud hasta dónde avanzará la simulación, tener la certeza de que dos ejecuciones con los mismos parámetros arrojan resultados idénticos, y verificar que el estado mostrado al detenerse en `t` es exactamente el que tenía la partida en ese instante durante la reproducción completa.

**Contexto existente y vigente (no se re-especifica)**:
- La opción `--replay PARTIDA.log` reproduce una partida previamente grabada de manera desatendida, sin interfaz gráfica ni interacción del usuario.
- El archivo de registro suministra la cripta, la semilla aleatoria, las versiones correspondientes de cripta y catálogo, y la secuencia ordenada de acciones ejecutadas por el jugador, cada una con su costo temporal.
- Al terminar la reproducción tradicional, el sistema reporta cuántas acciones del jugador se ejecutaron y si la partida concluyó.
- La reproducción no escribe un nuevo archivo de registro ni registra puntuaciones en la tabla de puntajes.
- El reloj del juego es virtual: los eventos programados para el jugador y para los enemigos se ordenan por su tiempo virtual y por su número de secuencia de desempate.
- El uso de `--replay` sin el modificador `--hasta` continúa operando con exactitud y sin cambios.

**Fuera de alcance**:
- Consulta interactiva o retrospectiva de historia (`historia <t>` o `#k`).
- Puntos de control manuales o automáticos (`--checkpoint-cada`).
- Modificaciones o adiciones al formato de los archivos de registro (`PARTIDA.log`).
- Reproducción inversa o hacia atrás en el tiempo.

## Clarificaciones

### Sesión 2026-11-04

- Q: ¿Cómo deben tratarse los eventos del juego programados exactamente para el instante virtual t? (FR-403) → A: Se ejecutan todos los eventos programados en t (límite inclusivo: se procesan todos los eventos con tiempo virtual menor o igual que t).
- Q: ¿Qué datos exactos del estado final del juego deben mostrarse al detenerse la reproducción acotada? (FR-404) → A: Estado exhaustivo: instante virtual alcanzado, cantidad de acciones reproducidas del jugador, sala actual del jugador, vida actual del jugador, llaves y objetos en su inventario, listado de enemigos presentes en la sala actual con sus vidas respectivas, y estado de la partida (en curso, victoria o derrota). (Ampliado el 2026-11-04 tras el análisis: se agregan estadísticas y efectos activos; ver la sesión de corrección.)

### Sesión 2026-11-04 (corrección tras el análisis de consistencia)

Estas correcciones se hacen primero en la especificación (constitución, principio X) y se apoyan en el enunciado de la Parte II, §3.6 y Apéndice B.

- Corrección 1 (FR-402, FR-403, FR-406): el enunciado define el estado en el instante `t` como el estado después de ejecutar todos los eventos con tiempo menor o igual que `t`, y añade que, si a `t` le corresponde una decisión del jugador, es el estado justo antes de tomarla. La respuesta A de la primera pregunta (límite inclusivo para todos los eventos) se afina: el límite inclusivo rige para los eventos de los demás actores; la decisión del jugador programada exactamente en `t` no se ejecuta. Con `t` igual a 0 el resultado es el estado inicial sin necesidad de una regla especial.
- Corrección 2 (FR-404): el enunciado pide para `--hasta` el mismo resumen que la consulta de historia (reloj, sala, vida y estadísticas, inventario, efectos activos, enemigos de la sala con su vida y mapa conocido). Se agregan las estadísticas del jugador y sus efectos activos. El mapa conocido depende de la capacidad de niebla de guerra y queda como requisito diferido (ver Assumptions).
- Corrección 3 (FR-405): el aviso de que el registro finalizó antes de `t` solo procede cuando la partida termina en un instante estrictamente menor que `t`.
- Corrección 4 (SC-003): el criterio de rendimiento pasa de una razón de tiempos de reloj, frágil en la máquina local, a un conteo de eventos procesados; la razón de tiempos queda como dato informativo. Es el mismo ajuste que se hizo en la capacidad 005.
- Corrección 5 (Historia 3, escenario 2 y FR-411): «reproducir hasta `t` y continuar» se expresa como propiedad de prefijo, porque la reproducción es un proceso por lotes sin reanudación interactiva.

## User Scenarios & Testing *(mandatory)*

### Historia 1 — Reproducción acotada hasta un instante intermedio (Prioridad: P1)

Como persona que revisa o audita partidas grabadas, quiero ejecutar la reproducción de un archivo de registro indicando un instante virtual límite `t` mediante `--replay PARTIDA.log --hasta t`, para que el juego ejecute únicamente lo ocurrido hasta `t` (con la regla de FR-402 y FR-403 para la decisión del jugador en `t`) y me muestre el estado exacto del juego en ese punto sin necesidad de reproducir la partida completa.

**Por qué esta prioridad**: Es la funcionalidad central y el valor esencial de la capacidad, permitiendo la inspección temporal acotada de partidas sin requerir la ejecución de todo el registro.

**Prueba independiente**: Tomar un archivo de registro con múltiples acciones cronológicas y ejecutar la reproducción especificando un instante `t` situado en medio de la partida; comprobar que los eventos posteriores no se ejecutan y que el estado reportado coincide con el esperado para ese instante.

**Escenarios de aceptación**:

1. **Dado** un archivo de registro con múltiples acciones cronológicas y un instante `t` situado en un punto intermedio de la partida, **cuando** se ejecuta `--replay PARTIDA.log --hasta t`, **entonces** no se ejecuta ningún evento con tiempo virtual mayor que `t`, la reproducción se detiene tras completar los eventos de los demás actores de `t` y el sistema informa el instante alcanzado, la cantidad de acciones del jugador ejecutadas y el estado exhaustivo del juego (sala, vida y estadísticas, inventario con llaves y objetos, efectos activos, enemigos en la sala con su vida, y si la partida sigue en curso). *(FR-401, FR-402, FR-403, FR-404)*
2. **Dado** un archivo de registro válido y un valor de `t` igual a 0, **cuando** se ejecuta `--replay PARTIDA.log --hasta 0`, **entonces** no se ejecuta ninguna acción del jugador del registro, porque su primera decisión corresponde justamente al instante 0 y se informa el estado justo antes de tomarla; es decir, el estado inicial exhaustivo del juego. *(FR-406, FR-403, FR-404)*
3. **Dado** un archivo de registro y un instante `t` que coincide exactamente con el tiempo programado de uno o más eventos, **cuando** se ejecuta `--replay PARTIDA.log --hasta t`, **entonces** se ejecutan todos los eventos de los demás actores programados en el instante `t` (límite inclusivo) y el estado resultante refleja sus consecuencias, pero la decisión del jugador programada en `t`, si la hay, no se ejecuta: el estado es el de justo antes de tomarla. Si una acción del jugador comenzó en un instante anterior a `t`, se ejecuta completa aunque su costo la lleve más allá de `t`, y el estado informado es el que tenía la partida en `t` según FR-403. *(FR-402, FR-403, FR-404)*
4. **Dado** un archivo de registro cuya partida termina, o cuyo registro se agota, en un instante estrictamente menor que el valor `t` solicitado, **cuando** se ejecuta `--replay PARTIDA.log --hasta t`, **entonces** se reproduce la totalidad de los eventos del registro y el sistema emite un aviso explícito indicando que el registro finalizó antes de alcanzar el instante `t`. *(FR-405, FR-404)*
5. **Dado** un archivo de registro en el cual la partida finaliza (por ejemplo, por muerte del jugador) en un instante virtual anterior a `t`, **cuando** se ejecuta la reproducción hasta `t`, **entonces** la simulación se detiene en el momento de la terminación y se informa explícitamente que la partida concluyó antes de alcanzar `t`, junto con la causa de terminación. *(FR-404, FR-405)*
6. **Dado** un archivo de registro cuya partida termina exactamente en el instante `t` solicitado, **cuando** se ejecuta `--replay PARTIDA.log --hasta t`, **entonces** se informa el estado final con su causa de terminación y no se emite el aviso de que el registro finalizó antes de alcanzar `t`, porque `t` sí se alcanzó. *(FR-404, FR-405)*

---

### Historia 2 — Validación de parámetros y preservación del comportamiento base (Prioridad: P2)

Como usuario o revisor del juego, quiero que el sistema valide rigurosamente los argumentos de línea de comandos correspondientes a `--hasta` para evitar ejecuciones erróneas o estados indefinidos, garantizando además que el modo `--replay` estándar sin `--hasta` no sufra ninguna alteración.

**Por qué esta prioridad**: Garantiza la robustez de la interfaz de línea de comandos, informa errores de uso de forma temprana y previene regresiones en el flujo existente de `--replay`.

**Prueba independiente**: Ejecutar el programa con combinaciones erróneas de parámetros (`--hasta` negativo, `--hasta` no entero, `--hasta` sin `--replay`) y verificar los mensajes de error; luego ejecutar `--replay` solo y comprobar que produce el resultado idéntico de siempre.

**Escenarios de aceptación**:

1. **Dado** un valor de `t` negativo o un valor que no representa un número entero, **cuando** se invoca el comando con dicho argumento, **entonces** el programa rechaza la solicitud con un mensaje claro de error y no reproduce ningún evento. *(FR-407)*
2. **Dado** una invocación en la línea de comandos que incluye `--hasta t` sin especificar `--replay`, **cuando** se ejecuta el comando, **entonces** el programa rechaza la invocación con un mensaje claro de error indicando que `--hasta` requiere `--replay`. *(FR-408)*
3. **Dado** un archivo de registro válido, **cuando** se ejecuta `--replay PARTIDA.log` sin especificar `--hasta`, **entonces** el sistema reproduce la partida completa conservando con total exactitud el comportamiento, formato y resultados previos. *(FR-409)*
4. **Dado** cualquier ejecución de `--replay` con `--hasta t`, **cuando** se realiza la reproducción, **entonces** no se muestra ninguna ventana ni interfaz visual, no se escribe ningún archivo de registro nuevo y no se inserta ninguna entrada en la tabla de puntajes. *(FR-410)*

---

### Historia 3 — Determinismo estricto y rendimiento proporcional (Prioridad: P2)

Como evaluador o revisor técnico, quiero que la reproducción acotada sea estrictamente determinista y que su costo computacional sea proporcional al tiempo reproducido y no al tamaño total del archivo, pudiendo auditarlo con mediciones automáticas.

**Por qué esta prioridad**: Asegura que las pruebas sean completamente reproducibles y que el uso de `--hasta` sea eficiente para inspeccionar momentos tempranos de partidas extensas.

**Prueba independiente**: Ejecutar dos veces el comando con idéntico registro y mismo valor `t` comparando la salida reportada; verificar que el estado al detenerse en `t` coincide con el de la reproducción completa en ese instante; y medir con `--bench` el tiempo de ejecución en función de `t`.

**Escenarios de aceptación**:

1. **Dado** un mismo archivo de registro y un mismo instante `t`, **cuando** se ejecutan dos reproducciones independientes bajo las mismas condiciones, **entonces** ambas ejecuciones arrojan salidas y estados finales idénticos. *(FR-411)*
2. **Dado** un archivo de registro y un instante `t`, **cuando** se reproduce hasta `t` y, en otra ejecución independiente, se reproduce la partida completa, **entonces** el estado informado al detenerse en `t` coincide exactamente con el estado que la reproducción completa tenía en ese mismo instante (propiedad de prefijo). *(FR-411)*
3. **Dado** un conjunto de partidas sintéticas generadas de forma determinista mediante semilla, **cuando** se ejecuta `--bench`, **entonces** la herramienta mide y reporta la cantidad de eventos procesados y el tiempo de la reproducción acotada, evidenciando que el costo no excede la reproducción completa y escala en proporción a lo reproducido. *(FR-412, FR-413)*

---

### Edge Cases

- **Instante `t` igual a cero**: La primera decisión del jugador corresponde al instante 0, por lo que no se consume ninguna acción del registro y se exhibe el estado del juego justo antes de esa decisión (FR-406, FR-403).
- **Eventos que coinciden exactamente en `t`**: Se ejecutan todos los eventos de los demás actores programados para ese instante; el corte temporal es inclusivo ($\le t$) para ellos. La decisión del jugador programada en `t` no se ejecuta (FR-403).
- **Múltiples eventos simultáneos en un mismo instante**: Si coinciden eventos de varios actores en un instante anterior a `t`, o de actores distintos del jugador en `t`, se preserva el orden determinista existente según el reloj virtual y el número de secuencia.
- **Instante `t` mayor que la duración del archivo**: La reproducción concluye pacíficamente al terminarse los eventos del registro, emitiendo una notificación de que el archivo finalizó antes de `t` (FR-405).
- **Partida que termina exactamente en `t`**: Se informa el estado final y su causa, sin el aviso de registro finalizado antes de `t` (FR-405).
- **Muerte o fin de partida antes de `t`**: El juego detiene la reproducción en el instante exacto en que termina la partida y notifica que concluyó antes de `t`, detallando si ocurrió por muerte del jugador o victoria (FR-404, FR-405).
- **Valores no válidos para `t`**: Valores negativos, números decimales, cadenas alfanuméricas o ausencia del valor numérico se rechazan con un mensaje explicativo sin procesar el archivo (FR-407).
- **Parámetro huérfano**: Especificar `--hasta` en conjunción con otros modos (como juego interactivo o `--verificar`) sin `--replay` genera un error explícito (FR-408).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-401**: El programa DEBE admitir el argumento de línea de comandos `--hasta <t>` única y exclusivamente cuando se invoque en conjunto con la opción `--replay <PARTIDA.log>`, donde `<t>` representa un instante del reloj virtual del juego.
- **FR-402**: La reproducción acotada DEBE detenerse al alcanzar el instante virtual `t`. Ningún evento del juego cuyo tiempo programado sea estrictamente mayor que `t` DEBE ejecutarse, ni tampoco la decisión del jugador programada exactamente en `t` (FR-403).
- **FR-403**: El estado informado DEBE ser el que tiene la partida después de ejecutar todos los eventos con tiempo virtual menor o igual que `t`, salvo que a `t` le corresponda una decisión del jugador: en ese caso DEBE ser el estado justo antes de tomarla. Por tanto, los eventos de los demás actores programados exactamente en `t` se ejecutan todos (límite inclusivo), la decisión del jugador programada exactamente en `t` no se ejecuta, y las decisiones del jugador anteriores a `t` se ejecutan completas. Dentro de un mismo instante rige el orden determinista del reloj virtual.
- **FR-404**: Al detenerse la reproducción acotada (sea en `t` o por terminación anticipada de la partida), el programa DEBE informar:
  1. El instante virtual efectivamente alcanzado.
  2. La cantidad de acciones del jugador ejecutadas.
  3. La sala actual en la que se encuentra el jugador.
  4. Los puntos de vida actuales del jugador y sus estadísticas (ataque, defensa y velocidad vigentes).
  5. El inventario actual del jugador, detallando las llaves y objetos en su poder.
  6. Los efectos activos sobre el jugador en ese instante (por ejemplo veneno, velocidad temporal por una poción o antorcha encendida).
  7. El listado de enemigos presentes en la sala actual del jugador junto con sus vidas respectivas.
  8. El estado de la partida: en curso, victoria o derrota (indicando explícitamente si la partida concluyó antes de alcanzar `t`).

  El mapa conocido por el jugador en ese instante forma parte del resumen exigido por el enunciado, pero depende de la capacidad de niebla de guerra y queda diferido (ver Assumptions).
- **FR-405**: Si la partida grabada concluye, o el registro se agota, en un instante estrictamente menor que `t`, el programa DEBE reproducir todos los eventos disponibles en el archivo de registro y DEBE emitir un mensaje indicando que el registro finalizó antes de alcanzar `t`. Si concluye exactamente en `t`, DEBE informar el estado final sin ese mensaje.
- **FR-406**: Si el valor de `t` es 0, el programa DEBE reportar el estado inicial exhaustivo del juego, previo a la primera decisión del jugador, como consecuencia de FR-403 y sin ejecutar ninguna acción del jugador del registro.
- **FR-407**: Si el valor proporcionado para `t` es negativo o no corresponde a una representación válida de número entero, el programa DEBE rechazar el argumento con un mensaje claro y descriptivo, sin reproducir ninguna acción del registro.
- **FR-408**: Si se especifica el argumento `--hasta` sin incluir la opción `--replay`, el programa DEBE rechazar la invocación con un mensaje claro de error sin iniciar ninguna partida ni modificar el estado del sistema.
- **FR-409**: La ejecución de `--replay` sin la presencia del modificador `--hasta` DEBE conservar de forma íntegra e inalterada su comportamiento y formato de salida existentes.
- **FR-410**: La reproducción acotada con `--replay ... --hasta` NO DEBE inicializar componentes de interfaz visual, NO DEBE generar un nuevo archivo de registro (`partida.log`) y NO DEBE registrar entradas en la tabla de puntajes.
- **FR-411**: Determinismo: Para un mismo archivo de registro y un mismo valor de `t`, dos o más ejecuciones DEBEN producir idéntico resultado y reporte de estado. Asimismo, el estado informado al detenerse en `t` DEBE coincidir exactamente con el que tenía la partida en el instante `t` durante la reproducción completa del mismo registro (propiedad de prefijo).
- **FR-412**: Rendimiento: El tiempo de cómputo requerido para reproducir hasta el instante `t` NO DEBE exceder el tiempo de la reproducción completa del mismo archivo, y DEBE ser proporcional a la cantidad de eventos procesados hasta `t` y no al tamaño total del archivo de registro.
- **FR-413**: Medición: La herramienta de evaluación de rendimiento `--bench` DEBE permitir medir y reportar el desempeño de la reproducción acotada hasta `t` utilizando partidas sintéticas generadas de manera determinista mediante semilla.

### Key Entities

- **Partida grabada (Log)**: Archivo de registro histórico que almacena los metadatos iniciales (cripta, semilla aleatoria, versiones de cripta y catálogo) y la secuencia temporal de acciones efectuadas por el jugador.
- **Instante virtual (`t`)**: Valor numérico entero no negativo que representa una coordenada de tiempo en el reloj virtual del juego.
- **Estado del juego**: Instantánea exhaustiva de las condiciones del juego al detenerse la simulación en `t`, que comprende la sala del jugador, su salud actual, los objetos y llaves en su inventario, los enemigos presentes en dicha sala con sus vidas, y la condición de la partida (en curso, victoria o derrota).
- **Acción del jugador**: Evento originado por la decisión del jugador (moverse, esperar, atacar, usar objeto) registrado en el archivo con su correspondiente costo de tiempo virtual.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los escenarios de aceptación descritos en las Historias 1, 2 y 3 se ejecutan y validan de forma consistente en pruebas automatizadas.
- **SC-002**: Para cualquier archivo de registro y valor de `t` válido, dos ejecuciones consecutivas bajo las mismas condiciones producen salidas idénticas carácter por carácter en el 100% de los casos.
- **SC-003**: En pruebas de rendimiento con partidas sintéticas de al menos 1000 acciones, la cantidad de eventos del juego procesados al reproducir hasta `t = T / 2` no supera el 55% de los procesados al reproducir la partida completa hasta su finalización `T`. La razón entre los tiempos de reloj se reporta como dato informativo, sin umbral de aprobación.
- **SC-004**: El 100% de las invocaciones con argumentos inválidos (`t` negativo, no entero, o `--hasta` sin `--replay`) son rechazadas en menos de 100 milisegundos con un mensaje de error explicativo para el usuario.
- **SC-005**: La ejecución tradicional con `--replay` sin `--hasta` conserva el 100% de equivalencia en comportamiento y resultados con respecto a la versión previa a esta capacidad.

## Assumptions

- El archivo de registro `PARTIDA.log` sigue el formato estándar existente de la Parte I y contiene acciones cronológicamente válidas.
- El reloj del juego avanza mediante incrementos discretos de tiempo gobernados por los costos de las acciones de los actores.
- Los mensajes informativos y de estado se emiten por la salida estándar, mientras que los mensajes de error por argumentos inválidos se emiten por la salida de error.
- La ejecución de `--replay ... --hasta` es de naturaleza desatendida y orientada a línea de comandos, por lo que no requiere entradas del usuario durante su transcurso.
- La medición de rendimiento en `--bench` utiliza semillas fijas para garantizar la repetibilidad de los resultados.
- El mapa conocido del jugador (niebla de guerra) todavía no existe en el programa. Cuando la capacidad de niebla de guerra esté disponible, el resumen de FR-404 deberá incluirlo; hasta entonces no se exige y no se inventa su contenido.
