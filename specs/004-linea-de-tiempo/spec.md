# Especificación de capacidad: Línea de tiempo — consulta de estados pasados

**Carpeta**: `004-linea-de-tiempo`

**Creada**: 2026-11-08

**Estado**: Borrador

**Entrada**: Capacidad de la línea de tiempo (Parte II, §3.6 y §5.5): los comandos `historia <t>` e `historia #k` para consultar el estado del juego en un instante pasado. Requisitos con prefijo FR-4xx, continuando desde FR-427.

## Contexto y motivación

Cuando una partida ha avanzado varias acciones, el jugador —o quien revise la partida— puede querer saber exactamente cómo estaba el juego en un instante anterior: en qué sala estaba el jugador, cuánta vida tenía, qué enemigos había en la sala, o qué tenía en su inventario. Reconstruir ese estado a mano, buscando en el log, resulta tedioso y propenso a errores.

Los comandos `historia <t>` e `historia #k` resuelven esto: el jugador escribe una orden y el juego responde con el estado del pasado pedido, sin interrumpir ni modificar la partida en curso.

**Lo existente y vigente (no se re-especifica)**: el reloj virtual con agenda de eventos; el inventario del jugador; el comportamiento de los enemigos; el guardado binario versionado; `partida.log` y la reproducción con `--replay`; el pergamino de retroceso (limitado a 5 acciones); los puntos de control automáticos con `--checkpoint-cada K` (capacidad 007); la opción `--replay … --hasta t` (capacidad 008).

**Por qué importa**: el jugador y quien revisa la partida necesitan saber cómo estaba el juego en un momento pasado sin alterar la partida en curso. La capacidad aprovecha los puntos de control de la capacidad 007 para garantizar que cualquier consulta sea respondida en tiempo acotado, sin reproducir la partida desde el principio.

## Clarificaciones

### Sesión 2026-11-08

[NEEDS CLARIFICATION – Q1]: ¿`historia #k` con k igual al número de acciones realizadas más uno (es decir, el estado actual del juego) se acepta y devuelve el estado presente, o también se rechaza como instante futuro? Impacto: define el límite superior de k válido.

[NEEDS CLARIFICATION – Q2]: ¿La consulta `historia` en una partida ya terminada (victoria o derrota) se acepta y muestra el estado final histórico, o se rechaza porque ya no hay partida en curso?

[NEEDS CLARIFICATION – Q3]: Mientras la capacidad de niebla de guerra (002) no esté integrada, ¿el campo «mapa conocido» se omite de la salida, se muestra vacío, o se muestra un literal como «(pendiente de integración)»?

*(Las demás ambigüedades se resolvieron con las decisiones del enunciado y las decisiones heredadas de 007).*

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Consultar el estado por instante de reloj `historia <t>` (Prioridad: P1)

Mientras juega, el jugador escribe `historia <t>` donde `t` es un instante del reloj virtual. El juego le muestra el estado completo de la partida en ese instante: sala, vida y estadísticas, inventario, efectos activos, enemigos con su vida y mapa conocido, sin interrumpir ni modificar la partida en curso.

**Por qué esta prioridad**: es la función principal de la capacidad; sin ella no existe la consulta temporal.

**Prueba independiente**: jugar una partida corta con acciones conocidas y verificar que `historia <t>` devuelve el estado exacto esperado para cada t, que el log no cambia, que la partida continúa igual y que el historial del pergamino no se altera.

**Escenarios de aceptación**:

1. **Dado** una partida en curso con reloj en T y un instante `t` con 0 ≤ t ≤ T, **cuando** el jugador escribe `historia <t>`, **entonces** el juego muestra el estado después de ejecutar todos los eventos con tiempo virtual ≤ t (si a t le corresponde una decisión del jugador, el estado es justo antes de tomarla), sin ejecutar ni modificar ningún evento de la partida en curso. *(FR-427, FR-428)*

2. **Dado** una partida con reloj en T y un instante `t` al que corresponde exactamente una decisión del jugador, **cuando** el jugador escribe `historia <t>`, **entonces** el estado mostrado es el que tenía la partida justo antes de que el jugador tomara esa decisión en t (misma regla que `--replay --hasta t` de la capacidad 008). *(FR-428)*

3. **Dado** una partida con reloj en T y un instante `t` al que corresponden varios eventos simultáneos de enemigos y del entorno (ninguno del jugador), **cuando** el jugador escribe `historia <t>`, **entonces** el estado mostrado incluye las consecuencias de todos esos eventos, respetando el orden determinista del reloj virtual. *(FR-427, FR-428)*

4. **Dado** una partida con reloj en T, **cuando** el jugador escribe `historia <0>`, **entonces** el juego muestra el estado inicial (punto de control 0: antes de que el jugador tomara su primera decisión). *(FR-427, FR-430)*

5. **Dado** una partida en curso, **cuando** el jugador escribe `historia <t>` con t > T (instante futuro), **entonces** el juego rechaza la consulta con un mensaje claro que indica que ese instante aún no ha ocurrido, sin mostrar ningún estado y sin alterar la partida. *(FR-433, Apéndice B: caso 1)*

6. **Dado** una partida en la que el jugador usó un pergamino de retroceso y revirtió m acciones, **cuando** el jugador escribe `historia <t>` para un instante anterior al retroceso, **entonces** el estado mostrado describe la partida tal como quedó tras el retroceso: las acciones revertidas no aparecen en la línea de tiempo y el estado refleja el camino que sí ocurrió. *(FR-434, Apéndice B: caso 2)*

7. **Dado** una partida en curso, **cuando** el jugador escribe `historia <t>`, **entonces** el tiempo virtual del reloj no avanza, la consulta no aparece en `partida.log`, el historial del pergamino de retroceso no se modifica y la partida continúa exactamente como si no se hubiera hecho la consulta. *(FR-432, Apéndice B: caso 4)*

---

### Historia 2 — Consultar el estado por número de acción `historia #k` (Prioridad: P1)

El jugador escribe `historia #k` donde k es un número entero que identifica una acción del jugador. El juego muestra el estado justo antes de que el jugador tomara la acción número k, es decir, el estado que el jugador tenía cuando fue su turno por k-ésima vez.

**Por qué esta prioridad**: complementa la consulta por instante con una forma más intuitiva de navegar la historia propia; los jugadores recuerdan «mi tercera acción» más fácilmente que un instante de reloj exacto.

**Prueba independiente**: jugar una partida con acciones numeradas y verificar que `historia #k` devuelve el mismo estado que `historia <t>` cuando t corresponde exactamente al instante antes de la acción k.

**Escenarios de aceptación**:

1. **Dado** una partida con al menos k acciones realizadas, **cuando** el jugador escribe `historia #k`, **entonces** el juego muestra el estado justo antes de que el jugador tomara la acción número k (estado del punto de control o de la reconstrucción correspondiente). *(FR-429)*

2. **Dado** una partida en curso, **cuando** el jugador escribe `historia #1`, **entonces** el juego muestra el estado inicial (punto de control 0: antes de la primera decisión del jugador). *(FR-430)*

3. **Dado** una partida en curso, **cuando** el jugador escribe `historia #0`, **entonces** el juego rechaza la consulta con un mensaje claro que indica que el número de acción debe ser mayor o igual que 1. *(FR-435)*

4. **Dado** una partida con N acciones realizadas, **cuando** el jugador escribe `historia #k` con k > N + 1 (o k > N según resolución de Q1), **entonces** el juego rechaza la consulta con un mensaje claro indicando que esa acción aún no ha ocurrido. *(FR-436)*

5. **Dado** una partida en la que el jugador usó un pergamino de retroceso y revirtió m acciones, dejando la línea de tiempo con N' acciones vigentes, **cuando** el jugador escribe `historia #k` para un k ≤ N', **entonces** el estado mostrado corresponde a la línea de tiempo vigente; las acciones revertidas no forman parte de la historia. *(FR-434, Apéndice B: caso 2)*

6. **Dado** cualquier consulta `historia #k`, **cuando** el jugador la escribe, **entonces** el tiempo virtual no avanza, la consulta no aparece en `partida.log` y el historial del pergamino no se modifica. *(FR-432)*

---

### Historia 3 — La consulta no altera la partida en curso (Prioridad: P1)

Cualquier consulta de `historia`, sea por instante o por número de acción, es transparente para la partida: no consume tiempo virtual, no cuenta como acción, no aparece en el log y no modifica el historial del pergamino.

**Por qué esta prioridad**: si la consulta alterara la partida, el jugador no podría usarla sin consecuencias; esto anularía su utilidad.

**Prueba independiente**: ejecutar una secuencia de acciones, intercalar varias consultas `historia` entre ellas, guardar la partida, y verificar que el log y el estado final son idénticos a los de la misma secuencia sin consultas.

**Escenarios de aceptación**:

1. **Dado** una partida en curso con un pergamino que tiene m retrocesos registrados y un reloj en T, **cuando** el jugador escribe `historia <t>` o `historia #k`, **entonces** el reloj sigue en T, el pergamino sigue con m retrocesos en su historial y `partida.log` no incluye ninguna entrada por la consulta. *(FR-432, Apéndice B: caso 4)*

2. **Dado** una secuencia de acciones A1, `historia #2`, A2, A3, **cuando** el jugador las ejecuta en orden, **entonces** el log y el estado final son idénticos a ejecutar A1, A2, A3 sin la consulta intermedia. *(FR-432)*

---

### Historia 4 — Coherencia con el pergamino de retroceso (Prioridad: P2)

Las acciones que el pergamino ha revertido dejan de existir en la línea de tiempo. La consulta `historia` describe únicamente la historia de la partida tal como quedó; no muestra estados de caminos abandonados.

**Por qué esta prioridad**: la coherencia con el pergamino es necesaria para que el jugador no vea estados contradictorios con la partida que está jugando.

**Prueba independiente**: jugar 10 acciones, revertir las últimas 3 con el pergamino, consultar varios instantes pasados y verificar que la línea de tiempo muestra solo las 7 acciones vigentes y el estado resultante de ellas.

**Escenarios de aceptación**:

1. **Dado** una partida en la que se ejecutaron N acciones y luego el pergamino revirtió las últimas m, dejando N - m acciones vigentes, **cuando** el jugador consulta `historia` para cualquier instante t' correspondiente a las m acciones revertidas, **entonces** esos instantes ya no pertenecen a la línea de tiempo vigente: `historia <t'>` puede resultar en el estado del momento del retroceso o posterior (según el reloj vigente), y `historia #k` con k > N - m es rechazado. *(FR-434, Apéndice B: caso 2)*

2. **Dado** la misma situación anterior, **cuando** el jugador consulta `historia #k` con k ≤ N - m, **entonces** el estado mostrado es el correspondiente a la línea de tiempo vigente, igual al que habría mostrado antes del uso del pergamino para esa acción. *(FR-434)*

---

### Historia 5 — Persistencia: guardar y cargar conserva la línea de tiempo (Prioridad: P2)

Cuando el jugador guarda la partida y la vuelve a cargar, `historia` responde exactamente igual que antes de guardar, para cualquier instante o número de acción válido.

**Por qué esta prioridad**: si la línea de tiempo se perdiera al cerrar el programa, el jugador no podría consultar el pasado entre sesiones.

**Prueba independiente**: jugar una partida, consultar varios instantes, guardar, recargar y verificar que las mismas consultas devuelven los mismos resultados.

**Escenarios de aceptación**:

1. **Dado** una partida con sus puntos de control y un conjunto de consultas `historia` que producen ciertos estados, **cuando** se guarda la partida y se carga en una nueva sesión, **entonces** las mismas consultas `historia` producen resultados idénticos a los de antes de guardar. *(FR-441)*

2. **Dado** un archivo de partida de la Parte I (versión anterior del programa), **cuando** el programa intenta cargarlo, **entonces** lo rechaza con un mensaje claro o lo migra de forma explícita; nunca lo carga en silencio ni permite consultas `historia` sobre él. *(Ref. FR-425 de capacidad 007, Apéndice B: caso 6)*

---

### Historia 6 — Rendimiento: la consulta responde en tiempo acotado (Prioridad: P2)

La consulta `historia` responde en un tiempo proporcional a la distancia entre el instante pedido y el punto de control anterior más cercano, sin importar el tamaño total de la partida. Para el intervalo K por defecto y una partida de al menos 5 000 acciones, la respuesta llega en 50 ms o menos.

**Por qué esta prioridad**: si la consulta tardara varios segundos en partidas largas, el jugador dejaría de usarla.

**Prueba independiente**: ejecutar `--bench` sobre la cripta de referencia (§6.1) con al menos 5 000 acciones y el K por defecto, midiendo el tiempo de respuesta de `historia` para instantes a distintas distancias del punto de control más cercano.

**Escenarios de aceptación**:

1. **Dado** la cripta de referencia (§6.1) con al menos 5 000 acciones del jugador y K = valor por defecto, **cuando** se ejecuta `--bench` y se mide el tiempo de respuesta de `historia <t>` e `historia #k`, **entonces** ninguna consulta supera 50 ms. *(FR-442, Principio VII)*

2. **Dado** `--bench` con distintos valores de K, **cuando** se mide el tiempo de respuesta de varias consultas `historia`, **entonces** el informe evidencia que el tiempo crece como máximo proporcionalmente a K y no a la longitud total de la partida. *(FR-442)*

---

### Casos límite

- `historia <0>` y `historia #1`: equivalen al estado inicial (punto de control 0); se aceptan siempre. *(FR-427, FR-430)*
- `t` o `k` negativos: se rechazan con mensaje claro. *(FR-437)*
- `t` o `k` decimales (p. ej. `historia 2.5` o `historia #3.0`): se rechazan con mensaje claro. *(FR-437)*
- Valor no numérico (p. ej. `historia abc`): se rechazado con mensaje claro. *(FR-437)*
- Partida sin ninguna acción: `historia <0>` y `historia #1` devuelven el estado inicial; cualquier `t` > 0 y `k` > 1 se rechazan. *(FR-438)*
- `historia #k` con k = acciones_realizadas + 1: pendiente de Q1 (ver clarificaciones). *(FR-436)*
- `historia` en una partida terminada: pendiente de Q2 (ver clarificaciones). *(FR-427)*
- Múltiples eventos en el mismo instante t: se muestran tras aplicar todos, respetando el orden determinista del reloj virtual. *(FR-427, Apéndice B: caso 3)*
- Reconstrucción necesita más de K acciones: imposible por FR-439; el programa informa un error claro sin dejar la partida a medias. *(FR-439, FR-440)*
- K mayor que el número total de acciones: solo existe el punto de control 0; `historia` puede consultar cualquier instante reproduciendo desde 0. *(FR-439)*

---

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Consulta por instante de reloj**

- **FR-427**: El juego DEBE aceptar el comando `historia <t>` durante la partida interactiva, donde `t` es un entero no negativo que representa un instante del reloj virtual. El estado devuelto DEBE ser el estado después de ejecutar todos los eventos con tiempo virtual menor o igual que `t`.
- **FR-428**: Si al instante `t` le corresponde una decisión del jugador, el estado devuelto por `historia <t>` DEBE ser el estado justo antes de que el jugador tomara esa decisión (misma regla que la capacidad 008 en `--replay --hasta t`). Los eventos de los demás actores programados exactamente en `t` se incluyen en el estado; la decisión del jugador programada en `t` no se incluye.

**Consulta por número de acción**

- **FR-429**: El juego DEBE aceptar el comando `historia #k` durante la partida interactiva, donde k es un entero ≥ 1. El estado devuelto DEBE ser el estado justo antes de que el jugador tomara la acción número k de la línea de tiempo vigente.
- **FR-430**: `historia #1` DEBE devolver el estado inicial de la partida (punto de control 0: el estado antes de que el jugador tomara su primera decisión). Esto es equivalente a `historia <0>` cuando la primera acción del jugador ocurre en el instante 0.

**Contenido mínimo del estado mostrado**

- **FR-431**: Tanto `historia <t>` como `historia #k` DEBEN mostrar como mínimo la siguiente información referida al instante histórico consultado:
  1. El instante del reloj virtual en el estado devuelto.
  2. La sala en la que se encontraba el jugador.
  3. Los puntos de vida del jugador y sus estadísticas (ataque, defensa y velocidad vigentes).
  4. El inventario del jugador (llaves y objetos).
  5. Los efectos activos sobre el jugador en ese instante.
  6. Los enemigos presentes en esa sala con su vida respectiva.
  7. El mapa conocido por el jugador en ese instante (pendiente de la capacidad 002; ver Supuestos).

**La consulta no altera la partida**

- **FR-432**: Cualquier consulta `historia` NO DEBE consumir tiempo virtual, NO DEBE contabilizarse como acción del jugador, NO DEBE producir ninguna entrada en `partida.log` y NO DEBE modificar el historial del pergamino de retroceso ni ningún otro estado de la partida en curso.

**Rechazo de consultas inválidas**

- **FR-433**: Si el instante `t` proporcionado es estrictamente mayor que el reloj actual de la partida en curso, el juego DEBE rechazar la consulta con un mensaje claro que indique que ese instante no ha ocurrido todavía. No DEBE mostrarse ningún estado y la partida NO DEBE verse alterada.
- **FR-435**: Si el número de acción k es 0 o negativo, el juego DEBE rechazar la consulta con un mensaje claro que indique que el número de acción debe ser mayor o igual que 1.
- **FR-436**: Si el número de acción k supera el número de acciones realizadas en la línea de tiempo vigente (más el margen que se defina al resolver Q1), el juego DEBE rechazar la consulta con un mensaje claro que indique que esa acción aún no ha ocurrido.
- **FR-437**: Si el valor de `t` o de `k` es negativo, decimal o no numérico, el juego DEBE rechazar la consulta con un mensaje claro y descriptivo, sin mostrar ningún estado y sin alterar la partida.

**Coherencia con el pergamino de retroceso**

- **FR-434**: Las acciones revertidas por el pergamino de retroceso NO DEBEN formar parte de la línea de tiempo que `historia` describe. `historia` DEBE responder exclusivamente sobre la historia de la partida tal como quedó; los instantes y acciones revertidos no existen en la línea de tiempo vigente.

**Partida sin acciones y estado inicial**

- **FR-438**: En una partida en la que el jugador aún no ha tomado ninguna acción, `historia <0>` y `historia #1` DEBEN devolver el estado inicial. Cualquier `t` > 0 y cualquier `k` > 1 DEBEN rechazarse como instantes futuros.

**Límite de reconstrucción**

- **FR-439**: Una consulta `historia` NO DEBE requerir reconstruir más de K acciones del jugador desde el punto de control más cercano anterior al instante pedido (K = intervalo de puntos de control vigente, capacidad 007). Si esto no fuera posible, el juego DEBE informar el problema con un mensaje claro sin dejar la partida a medias.
- **FR-440**: La reconstrucción del estado histórico NO DEBE realizar solicitudes de red ni acceder a recursos externos. Si falta algún dato local necesario para completar la consulta, el juego DEBE informar el problema con un mensaje claro sin dejar la partida en un estado inconsistente.

**Persistencia**

- **FR-441**: Guardar y cargar una partida DEBE conservar toda la información necesaria para que `historia` responda de manera idéntica a como respondía antes de guardar, para cualquier consulta válida. (El mecanismo de almacenamiento es responsabilidad de la capacidad 007 y del formato de partida.)

**Rendimiento**

- **FR-442**: El tiempo de respuesta de `historia <t>` y de `historia #k` NO DEBE superar 50 ms en una partida de al menos 5 000 acciones del jugador con el valor de K por defecto (§6.1), medido con `--bench` sobre criptas sintéticas deterministas por semilla (Principio VII).

**Interfaz**

- **FR-443**: El juego DEBE aceptar los comandos `historia <t>` e `historia #k` como comandos de la interfaz interactiva durante una partida en curso (§7.3). La sintaxis exacta (separadores, mayúsculas/minúsculas, etc.) la define el plan; esta especificación solo fija que ambas formas sean reconocidas.

### Entidades clave

- **Instante de reloj (`t`)**: valor entero no negativo que representa una coordenada de tiempo en el reloj virtual del juego.
- **Número de acción del jugador (`k`)**: entero ≥ 1 que identifica la k-ésima decisión aceptada y ejecutada por el juego en la línea de tiempo vigente. `k = 1` corresponde al estado inicial.
- **Estado histórico consultado**: instantánea del estado de la partida en el instante pedido, que incluye el contenido mínimo de FR-431. No es el estado actual; no reemplaza ni altera ningún estado en curso.
- **Línea de tiempo vigente**: la secuencia de acciones del jugador aceptadas que constituyen la historia real de la partida tal como quedó, descontadas las que el pergamino ha revertido.
- **Punto de control**: copia completa del estado de la partida tomada automáticamente cada K acciones (capacidad 007). La consulta `historia` parte del punto de control anterior más cercano para reconstruir el estado pedido.
- **Acción del jugador**: decisión aceptada y ejecutada por el juego que avanza la partida y la línea de tiempo vigente. Las órdenes rechazadas, los movimientos del cursor del inventario, el uso del pergamino y las consultas `historia` no cuentan como acción (decisión heredada de 007).

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: El 100 % de los escenarios de aceptación de las Historias 1–6 pasan sin errores en pruebas automatizadas.
- **SC-002**: Para cualquier partida de prueba, `historia <t>` y `historia #k` —cuando corresponden al mismo instante— producen el mismo estado en el 100 % de los casos.
- **SC-003**: Tras guardar y cargar una partida, el 100 % de las consultas `historia` devuelven el mismo resultado que antes de guardar.
- **SC-004**: El 100 % de las consultas inválidas (t futuro, k negativo, k = 0, valores no numéricos o decimales) producen un mensaje de error sin alterar la partida.
- **SC-005**: Ninguna consulta `historia` —válida o inválida— deja rastro en `partida.log` ni modifica el historial del pergamino en ningún caso.
- **SC-006**: Con al menos 5 000 acciones y el K por defecto, el tiempo de respuesta medido con `--bench` no supera 50 ms en ninguna consulta `historia` de las partidas de referencia.

## Supuestos

- El mapa conocido del jugador (FR-431, ítem 7) queda diferido hasta que la capacidad de niebla de guerra (002) se integre. Mientras tanto, ese campo no se muestra o se indica como no disponible (pendiente de resolución de Q3).
- La numeración de acciones en `#k` es 1-based: la primera acción aceptada es la acción 1 y el estado inicial es el que muestra `historia #1`.
- La línea de tiempo que `historia` describe es exactamente la que forman los puntos de control de la capacidad 007 y los eventos registrados entre ellos.
- La reconstrucción del estado histórico usa los puntos de control de la capacidad 007; esta especificación no describe su mecanismo interno.
- El formato binario de partida v7 (capacidad 007) ya almacena los puntos de control necesarios para que `historia` funcione.
- Los mensajes de respuesta y de error se emiten por la interfaz interactiva (mismos canales que el resto de los mensajes del juego).
- Una «acción del jugador» para los efectos de `#k` es exactamente la misma que para los efectos de los puntos de control de 007: decisión aceptada y ejecutada que avanza la partida. Las órdenes rechazadas, los movimientos del cursor del inventario, el uso del pergamino y las consultas `historia` no cuentan.

## Fuera de alcance

- Los puntos de control automáticos y la bandera `--checkpoint-cada K` (capacidad 007).
- La reproducción con `--replay … --hasta t` (capacidad 008).
- El contenido del mapa conocido del jugador (capacidad de niebla de guerra 002).
- La lógica interna de cómo se reconstruye el estado histórico desde un punto de control (decisión de plan).
- La visualización del log o del historial del pergamino como tal.
- Deshacer o revertir acciones (eso es el pergamino, capacidad no numerada en este documento).
- Toda navegación o búsqueda sobre el log de partida que no sea una consulta de estado puntual.
