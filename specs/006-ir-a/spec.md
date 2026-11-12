# Especificación de capacidad: Comando «ir a»

**Carpeta**: `006-ir-a`

**Creada**: 2026-11-11

**Estado**: Borrador

**Entrada**: Capacidad «ir a» de la Parte II (segunda mitad de la capacidad 2xx): viajar hasta una sala ya explorada por la ruta más barata conocida. Requisitos con prefijo FR-23x.

## Contexto y motivación

Con la niebla de guerra (002) el jugador ya tiene un mapa de lo que ha explorado, pero para volver a una sala lejana debe escribir a mano cada movimiento. El comando «ir a» le permite indicar una sala ya explorada y viajar hasta ella con un solo comando, siguiendo la ruta más barata **que él conoce**, no la que existe en la cripta real.

Quien juega debe poder confiar en que el viaje respeta lo que sabe: no usa salas ni puertas que nunca vio, se detiene cuando algo cambia o lo amenaza, y gasta el mismo tiempo que si hubiera caminado paso a paso. Quien revisa debe poder predecir, dada una cripta, una semilla y unas acciones, exactamente qué viaje se hace.

**Lo existente y vigente (no se re-especifica)**: salas, salidas, puertas y su cierre automático; costo de cada salida y reloj de la partida; antorcha; pergamino de retroceso (deshace la última acción y lo ocurrido hasta la siguiente decisión, máximo 5 acciones); enemigos dormidos y su activación al entrar el jugador a una sala (Parte I, §2.4); mapa conocido y estados de conocimiento (explorada, avistada, desconocida), puertas recordadas y exploración con antorcha (002, FR-201 a FR-226); partida guardada, `partida.log` y reproducción.

**Fuera de alcance**: la niebla de guerra y el mapa conocido en sí (002); el cazador y los costos de las salidas (001); la línea de tiempo (004); el formato binario de partida.

## Clarificaciones

### Sesión 2026-11-11

- Q: ¿Cuándo se considera que una puerta recordada abierta «resulta cerrada»? → A: Cuando, al entrar a una sala del viaje, el jugador observa (002, FR-207) una puerta de esa sala cuyo estado real es cerrada y la ruta pendiente la usaba como abierta.
- Q: ¿Qué pasa con el tiempo del paso que no se pudo dar por una puerta cerrada? → A: No se consume; el tiempo solo se consume por salidas efectivamente atravesadas.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Viajar a una sala explorada por la ruta más barata (Prioridad: P1)

Quien juega indica una sala ya explorada y el personaje camina hasta ella, paso a paso, por la ruta de menor costo total entre las que su mapa conocido permite, consumiendo el tiempo de cada salida atravesada.

**Por qué esta prioridad**: es el núcleo de la capacidad; sin viaje no hay comando.

**Prueba independiente**: en una cripta pequeña con dos caminos de distinto costo hacia una sala explorada, ejecutar «ir a» y comprobar la secuencia de salas, el tiempo total consumido y que coincide con caminar la misma ruta a mano.

**Escenarios de aceptación**:

1. **Dado** el jugador en una sala y una sala explorada alcanzable por dos rutas conocidas de costo distinto, **cuando** ejecuta «ir a» esa sala, **entonces** recorre la de menor costo total y el reloj avanza la suma de los costos de las salidas atravesadas. *(FR-231, FR-232, FR-233)*
2. **Dado** dos rutas conocidas de igual costo total, **cuando** ejecuta «ir a», **entonces** elige la que desempata por menor id de sala según la regla de desempate de la ruta más barata, y repetirlo da siempre la misma. *(FR-234)*
3. **Dado** el jugador ya en la sala indicada, **cuando** ejecuta «ir a» esa misma sala, **entonces** no se mueve ni consume tiempo y se le informa de que ya está allí. *(FR-231)*
4. **Dado** una ruta conocida que pasa por una puerta recordada como cerrada, **cuando** ejecuta «ir a», **entonces** esa puerta no se considera atravesable al calcular la ruta. *(FR-235)*
5. **Dado** un viaje que termina con éxito, **cuando** el jugador llega, **entonces** queda en la sala destino con el conocimiento actualizado como si hubiera caminado cada entrada a mano. *(FR-236)*

---

### Historia 2 — Rechazo sin costo (Prioridad: P1)

Si el destino no se puede alcanzar con lo que el jugador sabe, el comando se rechaza de inmediato, con un motivo claro, y la partida queda exactamente igual.

**Por qué esta prioridad**: es un caso del Apéndice B (B-N1) y protege al jugador de perder tiempo por una orden inválida.

**Prueba independiente**: pedir «ir a» una sala avistada, una desconocida y una explorada sin ruta conocida, y comprobar que el reloj y el conocimiento no cambian.

**Escenarios de aceptación**:

1. **Dado** una sala solo avistada o desconocida, **cuando** el jugador ejecuta «ir a» esa sala (B-N1), **entonces** el comando se rechaza indicando que el destino no está explorado, el reloj no avanza y no se cuenta como acción. *(FR-237, FR-238)*
2. **Dado** una sala explorada a la que no existe ninguna ruta por puertas no recordadas como cerradas, **cuando** el jugador ejecuta «ir a», **entonces** se rechaza indicando que no hay ruta conocida, sin consumir tiempo. *(FR-237, FR-238)*
3. **Dado** un identificador que no corresponde a ninguna sala, **cuando** se ejecuta «ir a», **entonces** se rechaza con un mensaje de destino inexistente, sin efectos. *(FR-237)*
4. **Dado** un comando rechazado, **cuando** el jugador usa el pergamino, **entonces** el pergamino deshace la acción anterior al rechazo, no el rechazo. *(FR-238)*

---

### Historia 3 — Una puerta recordada abierta resulta cerrada (Prioridad: P1)

El mapa del jugador puede estar desactualizado: una puerta que recuerda abierta puede haberse cerrado por cierre automático. El viaje lo descubre al llegar a una de sus salas, actualiza el mapa y busca otra ruta; si no hay, se detiene.

**Por qué esta prioridad**: es un caso del Apéndice B (B-N2) y es lo que distingue viajar con un mapa recordado de viajar con el mapa real.

**Prueba independiente**: abrir una puerta con cierre automático, alejarse hasta que se cierre, y pedir un viaje cuya ruta más barata la usa; comprobar la actualización del mapa, la nueva ruta o la detención.

**Escenarios de aceptación**:

1. **Dado** una ruta cuya puerta recordada abierta está realmente cerrada y existe una ruta alterna conocida, **cuando** el viaje llega a la sala de esa puerta y la observa cerrada, **entonces** el mapa recuerda la puerta cerrada, la ruta se recalcula desde la sala actual y el viaje continúa por la alterna. *(FR-239, FR-240)*
2. **Dado** el mismo caso sin ruta alterna conocida (B-N2), **cuando** el viaje observa la puerta cerrada, **entonces** el viaje se detiene en esa sala, el mapa queda actualizado y no se consume tiempo adicional por el paso no dado. *(FR-239, FR-241)*
3. **Dado** un viaje detenido por una puerta cerrada, **cuando** el jugador pide de nuevo «ir a» el mismo destino, **entonces** se evalúa con el mapa ya actualizado (rechazo por falta de ruta si sigue sin haberla). *(FR-241, FR-237)*
4. **Dado** una puerta recordada abierta que sigue abierta en la realidad, **cuando** el viaje la atraviesa, **entonces** no hay recálculo ni detención. *(FR-239)*

---

### Historia 4 — Peligro y pergamino detienen el viaje (Prioridad: P1)

El viaje se detiene al entrar a una sala con enemigos dormidos, que se activan como en cualquier entrada normal. Un pergamino usado durante el viaje deshace solo el último paso y el viaje no sigue.

**Por qué esta prioridad**: son los casos B-N3 y B-N6 y definen la seguridad del viaje.

**Prueba independiente**: preparar una ruta que atraviesa una sala con enemigos dormidos y comprobar activación y detención; en otro viaje, usar el pergamino a mitad y comprobar el estado.

**Escenarios de aceptación**:

1. **Dado** una ruta que entra a una sala con enemigos dormidos (B-N3), **cuando** el viaje entra a ella, **entonces** los enemigos se activan exactamente como si el jugador hubiera entrado a mano (Parte I, §2.4) y el viaje se detiene en esa sala, aunque no sea el destino. *(FR-242, FR-243)*
2. **Dado** una sala con enemigos dormidos que es el propio destino, **cuando** el viaje llega, **entonces** se activan y el viaje termina allí. *(FR-242)*
3. **Dado** un viaje en curso con varios pasos dados (B-N6), **cuando** el jugador usa el pergamino, **entonces** se revierte únicamente el último paso (la última entrada a una sala y lo ocurrido hasta su siguiente decisión), el jugador queda en la sala anterior y el viaje no continúa. *(FR-244, FR-245)*
4. **Dado** que el pergamino revirtió el último paso de un viaje, **cuando** el jugador usa el pergamino otra vez, **entonces** revierte el paso anterior del viaje, uno por uso, dentro del máximo de 5 acciones. *(FR-244)*
5. **Dado** una sala del viaje sin enemigos dormidos, **cuando** el viaje la atraviesa, **entonces** no se detiene. *(FR-243)*

---

### Historia 5 — Antorcha encendida durante el viaje (Prioridad: P2)

Con la antorcha encendida, cada sala a la que entra el viaje explora sus vecinas igual que una entrada a mano.

**Por qué esta prioridad**: asegura que viajar no pierde conocimiento respecto de caminar, pero no cambia el viaje en sí.

**Prueba independiente**: encender la antorcha, viajar por una ruta de varias salas y comparar el mapa conocido final con el obtenido caminando a mano la misma ruta.

**Escenarios de aceptación**:

1. **Dado** la antorcha encendida, **cuando** cada paso del viaje entra a una sala, **entonces** las vecinas de esa sala pasan a exploradas según 002 (FR-210 a FR-212), sin activar sus enemigos ni trampas. *(FR-246)*
2. **Dado** la antorcha encendida y una ruta que 002 ya ha ampliado con vecinas nuevas, **cuando** se recalcula tras una puerta cerrada, **entonces** la nueva ruta puede usar las salas recién exploradas por la antorcha. *(FR-246, FR-240)*
3. **Dado** la antorcha que se apaga a mitad del viaje, **cuando** el viaje sigue, **entonces** las entradas posteriores exploran o no según su estado en el instante de cada entrada. *(FR-246)*

---

### Historia 6 — Viaje reproducible (Prioridad: P2)

La misma cripta, la misma semilla y las mismas acciones producen siempre el mismo viaje, con independencia de qué contenido se haya descargado.

**Por qué esta prioridad**: es una regla transversal del proyecto y permite depurar y comparar.

**Prueba independiente**: ejecutar dos veces la misma partida con «ir a» y comparar `partida.log`; repetir con y sin contenido de salas descargado.

**Escenarios de aceptación**:

1. **Dado** dos ejecuciones idénticas con «ir a», **cuando** se comparan, **entonces** el recorrido, el tiempo, el mapa conocido y el registro son idénticos. *(FR-247)*
2. **Dado** una partida guardada y cargada a mitad de la partida, **cuando** se ejecuta el mismo «ir a», **entonces** el resultado es el mismo que sin guardar. *(FR-247)*
3. **Dado** una sala del trayecto cuyo contenido aún no se ha descargado, **cuando** se calcula la ruta, **entonces** el cálculo no depende de ese contenido ni lo requiere. *(FR-248)*

---

### Casos límite

- ¿Qué pasa si el destino es una sala explorada solo por la antorcha, a la que el jugador nunca ha entrado? Es explorada para este comando: se puede viajar a ella si hay ruta conocida. *(FR-231)*
- ¿Qué pasa si una puerta de la ruta aparece «sin observar»? No se considera atravesable al calcular la ruta, porque el jugador nunca ha visto su estado; la ruta solo usa puertas recordadas abiertas. *(FR-235)*
- ¿Qué pasa si el cierre automático cierra una puerta en medio del viaje, justo tras atravesarla? Solo importa lo que el jugador observa al llegar a cada sala; el cierre a su espalda actualiza la puerta solo si la observa (002, FR-207). *(FR-239)*
- ¿Qué pasa si hay un enemigo ya activo que alcanza al jugador en medio del viaje? Rige la regla vigente de combate; el viaje se detiene si el jugador sufre un evento que, de ocurrir caminando a mano, le exigiría decidir. *(FR-249)*
- ¿Qué pasa si el pergamino se usa antes del primer paso del viaje? No hay paso del viaje que revertir: deshace la acción anterior al comando, que no llegó a mover al jugador. *(FR-244)*
- ¿Qué pasa si no quedan pasos que revertir en el pergamino (máximo de 5 acciones)? Rige la regla vigente del pergamino.
- ¿Qué pasa si el destino cambia de estado de puerta mientras se viaja a él? Se resuelve igual que cualquier puerta: por observación al llegar.

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Comando y ruta**

- **FR-231**: El jugador DEBE disponer de un comando «ir a» que reciba una sala destino y lo lleve hasta ella. El destino DEBE estar explorada (002, FR-201), tanto si el jugador entró a ella como si la exploró la antorcha. Si el jugador ya está en el destino, el comando DEBE informarlo sin mover al jugador ni consumir tiempo.
- **FR-232**: La ruta del viaje DEBE ser la de menor costo total entre las que conecta el mapa conocido del jugador, donde el costo de una ruta es la suma de los costos de sus salidas (001).
- **FR-233**: El viaje DEBE avanzar paso a paso: cada paso atraviesa una salida de la ruta, consume el tiempo de esa salida y deja al jugador en la sala siguiente, con el mismo efecto sobre la partida que un movimiento normal a esa sala (incluida la actualización del conocimiento de 002).
- **FR-234**: Cuando dos o más rutas tengan el mismo costo total, o dos salidas lleven al mismo costo parcial, el desempate DEBE ser por menor id de sala, aplicado de forma explícita y fija.
- **FR-235**: La ruta DEBE calcularse solo con lo que el jugador conoce: salas exploradas, salidas conocidas con su costo y puertas recordadas abiertas. NO DEBE usar salas avistadas o desconocidas como paso intermedio, puertas recordadas como cerradas ni puertas «sin observar», ni el estado real de las puertas.
- **FR-236**: Al llegar al destino, el jugador DEBE quedar en esa sala con el conocimiento resultante de haber entrado a cada sala de la ruta, y el reloj DEBE haber avanzado exactamente la suma de los costos de las salidas atravesadas.

**Rechazo**

- **FR-237**: El comando DEBE rechazarse, con un mensaje que indique el motivo, cuando el destino no exista, no esté explorado (avistado o desconocido) o no haya ruta conocida desde la sala actual (FR-235).
- **FR-238**: Un comando rechazado NO DEBE consumir tiempo, NO DEBE alterar el conocimiento ni ningún otro estado de la partida y NO DEBE contar como acción para el pergamino.

**Puertas que cambian**

- **FR-239**: Al entrar a cada sala del viaje, el jugador DEBE observar sus puertas (002, FR-207). Si la puerta que la ruta pendiente usaba como abierta está realmente cerrada, su estado recordado DEBE actualizarse a cerrada.
- **FR-240**: Tras actualizarse una puerta por FR-239, la ruta DEBE recalcularse desde la sala actual hacia el mismo destino, con el mapa conocido actualizado, y el viaje continúa por la nueva ruta si existe.
- **FR-241**: Si tras el recálculo no existe ruta conocida, el viaje DEBE detenerse en la sala actual sin consumir tiempo adicional por el paso no dado, con un mensaje que indique el motivo.

**Detenciones**

- **FR-242**: Al entrar a una sala con enemigos dormidos, ya sea intermedia o destino, estos DEBEN activarse exactamente según la regla de la Parte I (§2.4), igual que en una entrada a mano.
- **FR-243**: El viaje DEBE detenerse al entrar a una sala con enemigos dormidos (FR-242), dejando al jugador en esa sala; NO DEBE continuar con los pasos restantes. Una sala sin enemigos dormidos NO DEBE detener el viaje.
- **FR-249**: El viaje DEBE detenerse en cuanto ocurra un evento que, de caminar a mano, exigiría al jugador una nueva decisión (por ejemplo, ser alcanzado por un enemigo ya activo); el mensaje DEBE indicar el motivo.

**Pergamino**

- **FR-244**: Cada paso del viaje DEBE contar como una acción propia para el pergamino. Usar el pergamino durante o tras un viaje DEBE revertir únicamente el último paso (la última entrada a una sala y lo ocurrido hasta su siguiente decisión, incluido su conocimiento, 002 FR-214), de modo que revertir varias veces recorre los pasos al revés uno por uno, dentro del máximo vigente.
- **FR-245**: Tras usar el pergamino, el viaje en curso DEBE quedar cancelado: NO DEBE continuar con los pasos restantes ni reanudarse solo.

**Antorcha**

- **FR-246**: Con la antorcha encendida en el instante de cada entrada del viaje, la exploración de las salas vecinas DEBE ocurrir exactamente como en una entrada normal (002, FR-210 a FR-212): sin activar sus enemigos ni sus trampas. Las salas así exploradas DEBEN estar disponibles para recalcular la ruta (FR-240).

**Determinismo**

- **FR-247**: Misma cripta, misma semilla y mismas acciones DEBEN producir el mismo viaje: la misma secuencia de salas, el mismo tiempo, el mismo mapa conocido y el mismo registro, con independencia de si la partida se guardó y cargó por el camino.
- **FR-248**: El cálculo de la ruta NO DEBE depender de qué contenido de sala ya fue descargado ni requerir descargar contenido no necesario; solo usa el mapa conocido.

**Rendimiento y mediciones**

- **FR-250**: Cada paso del viaje (atravesar una salida, actualizar el conocimiento y, si procede, recalcular la ruta) DEBE completarse en 5 ms o menos en el peor caso medido.
- **FR-251**: `--bench` DEBE poder medir un paso de «ir a» en criptas sintéticas de varios tamaños generadas de forma determinista por semilla, y al menos una medición DEBE comparar la decisión adoptada con una alternativa descartada, de modo que el límite de 5 ms se respalde con datos.

### Entidades clave

- **Viaje**: orden de ir a una sala destino explorada; tiene un origen, un destino, una ruta pendiente y un estado (en curso, llegado o detenido con motivo). Se cancela con el pergamino o por una detención.
- **Ruta conocida**: secuencia de salas y salidas de menor costo calculada solo sobre el mapa conocido del jugador.
- **Paso del viaje**: una entrada a una sala siguiendo una salida; cuenta como una acción para el pergamino y consume el tiempo de la salida.
- **Motivo de detención**: razón por la que un viaje no termina (puerta cerrada sin alterna, enemigos dormidos, evento que exige decisión, pergamino).

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-201**: En el 100 % de los viajes de prueba, el tiempo consumido es igual a la suma de los costos de las salidas atravesadas y el estado final coincide con caminar la misma ruta a mano.
- **SC-202**: En el 100 % de los rechazos de prueba (B-N1 y destinos sin ruta), el reloj, el conocimiento y el historial de acciones quedan idénticos a antes del comando.
- **SC-203**: En los casos del Apéndice B B-N1, B-N2, B-N3 y B-N6, el resultado observable coincide con lo descrito en la tabla del Apéndice, verificado por una prueba automatizada por caso.
- **SC-204**: Dos ejecuciones de la misma partida con «ir a» producen un `partida.log` idéntico en el 100 % de las pruebas, con y sin contenido descargado.
- **SC-205**: Un paso de «ir a» tarda 5 ms o menos en cripta sintética del tamaño máximo medido, según `--bench`.
- **SC-206**: Ninguna ruta de prueba usa una puerta recordada cerrada, una sala solo avistada o una puerta «sin observar» como paso.

## Trazabilidad con el Apéndice B

| Caso | Historia | Requisitos |
|---|---|---|
| B-N1 | Historia 2, escenario 1 | FR-237, FR-238 |
| B-N2 | Historia 3, escenario 2 | FR-239, FR-240, FR-241 |
| B-N3 | Historia 4, escenario 1 | FR-242, FR-243 |
| B-N6 | Historia 4, escenario 3 | FR-244, FR-245 |

B-N4 y B-N5 (antorcha y pergamino sin viaje) pertenecen a la especificación 002.

## Supuestos

- «Explorada» incluye las salas exploradas por la antorcha, aunque el jugador nunca haya entrado a ellas.
- El mapa conocido de 002 es la única fuente de la ruta: el estado real de las puertas solo entra al jugador por observación (FR-239).
- El desempate «menor id» es el mismo que usa la ruta más barata del cazador (001) para mantener una sola regla en el proyecto.
- La numeración FR-249 se asigna a la regla de eventos que exigen decisión para mantener los ids estables; los FR-23x/24x/25x son los de esta capacidad (constitución IX).
- Los casos B-N4 y B-N5 quedan cubiertos por 002 y aquí solo se verifica la interacción con el viaje (Historia 5).
- No se admite encadenar varios destinos en un solo comando ni reanudar un viaje cancelado: se pide un nuevo «ir a».
