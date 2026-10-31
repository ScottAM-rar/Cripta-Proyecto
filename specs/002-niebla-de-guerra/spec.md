# Especificación de capacidad: Niebla de guerra y mapa conocido

**Carpeta**: `002-niebla-de-guerra`

**Creada**: 2026-10-31

**Estado**: Borrador

**Entrada**: Capacidad 2 de la Parte II (primera mitad) — niebla de guerra y mapa conocido del jugador. Requisitos con prefijo FR-2xx.

## Contexto y motivación

Hoy la vista solo pinta la sala actual y el jugador no recuerda lo que ya recorrió. Con la niebla de guerra el jugador solo conoce la parte de la cripta que ha explorado, la recuerda tal como la vio por última vez y puede consultarla en cualquier momento.

Quien juega debe sentir que la cripta se descubre poco a poco y que su mapa puede estar desactualizado (una puerta que recuerda abierta puede haberse cerrado). Quien revisa debe poder predecir, dado un estado y una secuencia de acciones, exactamente qué sabe el jugador y qué muestra el mapa.

**Lo existente y vigente (no se re-especifica)**: salas, salidas y puertas (abiertas, cerradas, con llave y con cierre automático); antorcha (encendida durante un tiempo); pergamino de retroceso, que deshace la última acción del jugador y lo ocurrido hasta su siguiente decisión, con un máximo de 5 acciones; partida guardada en formato binario versionado; `partida.log` y reproducción; costo de las salidas y cazador (especificación 001). El cazador conoce el esqueleto completo y no depende de la niebla del jugador (FR-117).

**Fuera de alcance**: el comando «ir a» (otra especificación); el cazador y los costos (001); la línea de tiempo; el formato binario v6 en sí (lo codifica otra persona; esta especificación solo dice qué conocimiento se guarda).

## Clarificaciones

### Sesión 2026-10-31

- Q: Cuando la antorcha explora una vecina, ¿sus puertas nunca vistas aparecen «sin observar» o con su estado real? → A: Aparecen «sin observar» hasta que el jugador esté en una de las dos salas que conecta la puerta.
- Q: ¿Qué pasa al cargar una partida guardada por una versión sin niebla? → A: Se rechaza con un mensaje que indique la versión encontrada y la esperada.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Explorar y avistar salas (Prioridad: P1)

Quien juega empieza conociendo solo la sala inicial y sabe que detrás de cada una de sus salidas hay una sala. Al entrar a una sala nueva, la conoce (nombre, salidas, costos, puertas) y pasa a saber que existen las salas detrás de sus salidas, aunque no sepa nada más de ellas.

**Por qué esta prioridad**: es la base de la niebla; sin estados de conocimiento no hay mapa.

**Prueba independiente**: en una cripta pequeña conocida, mover al jugador por varias salas y comprobar tras cada entrada el estado de cada sala.

**Escenarios de aceptación**:

1. **Dado** una partida nueva, **cuando** se consulta el conocimiento en el instante 0, **entonces** la sala inicial está explorada, las salas destino de sus salidas están avistadas y todas las demás son desconocidas. *(FR-201, FR-202, FR-203)*
2. **Dado** el jugador en una sala explorada con una salida hacia una sala avistada, **cuando** entra a esa sala, **entonces** pasa a explorada y el jugador conoce su nombre, sus salidas, el costo de cada salida y el estado de sus puertas. *(FR-204, FR-206)*
3. **Dado** el jugador que entra a una sala nueva con tres salidas hacia salas desconocidas, una de ellas con la puerta cerrada, **cuando** termina de entrar, **entonces** las tres salas destino pasan a avistadas, incluida la que está detrás de la puerta cerrada. *(FR-203, FR-204)*
4. **Dado** una sala avistada, **cuando** se consulta lo que el jugador sabe de ella, **entonces** solo sabe que existe detrás de una salida conocida: no conoce su nombre, sus salidas ni su contenido. *(FR-203)*
5. **Dado** una sala nueva con una salida hacia una sala ya explorada, **cuando** el jugador entra, **entonces** la sala ya explorada sigue explorada y no pasa a avistada. *(FR-204, FR-205)*
6. **Dado** una sala ya explorada, **cuando** el jugador vuelve a entrar, **entonces** ninguna sala pierde estado y solo se actualiza la memoria de las puertas que observa. *(FR-205, FR-207)*
7. **Dado** una sala B con una salida de un solo sentido hacia la sala A explorada, y A sin salida hacia B, **cuando** el jugador está en A, **entonces** B no pasa a avistada por esa conexión. *(FR-203)*

---

### Historia 2 — El mapa recuerda las puertas como las vio por última vez (Prioridad: P1)

Quien juega recuerda el estado de cada puerta tal como estaba la última vez que estuvo en una de las dos salas que conecta. Si la puerta cambia mientras no está, su mapa queda desactualizado hasta que vuelva a observarla.

**Por qué esta prioridad**: es lo que distingue un mapa recordado de una vista del mapa real, y es un caso del Apéndice B.

**Prueba independiente**: abrir una puerta con cierre automático, alejarse hasta que se cierre, consultar el mapa y luego volver a una de sus salas.

**Escenarios de aceptación**:

1. *(Apéndice B)* **Dado** una puerta con cierre automático que el jugador dejó abierta y que se cerró mientras él estaba en otra parte, de modo que el mapa la recuerda abierta, **cuando** el jugador entra a cualquiera de las dos salas que conecta, **entonces** la observa y el mapa pasa a mostrarla cerrada. *(FR-207, FR-208)*
2. **Dado** el escenario anterior antes de volver, **cuando** el jugador consulta el mapa desde una sala lejana, **entonces** la puerta figura abierta aunque en realidad esté cerrada. *(FR-208, FR-219)*
3. **Dado** el jugador en una de las dos salas que conecta una puerta, **cuando** la puerta cambia de estado mientras él sigue en esa sala (la abre él o se cierra sola), **entonces** el mapa refleja el nuevo estado en ese mismo instante. *(FR-207)*
4. **Dado** una puerta entre la sala actual y una sala avistada, **cuando** el jugador está en la sala actual, **entonces** el mapa recuerda el estado de esa puerta como parte de las salidas de la sala actual. *(FR-206, FR-207)*

---

### Historia 3 — La antorcha ilumina las salas vecinas (Prioridad: P2)

Con la antorcha encendida, al entrar a una sala el jugador también explora todas sus vecinas: conoce su nombre y sus salidas, pero no ve su contenido ni despierta lo que hay dentro.

**Por qué esta prioridad**: amplía la exploración con un objeto existente; depende de la historia 1. Es un caso del Apéndice B.

**Prueba independiente**: entrar con la antorcha encendida a una sala cuyas vecinas tienen enemigos y trampas, y comprobar conocimiento y estado de esas vecinas.

**Escenarios de aceptación**:

1. *(Apéndice B)* **Dado** la antorcha encendida y una sala cuyas vecinas contienen enemigos y trampas, **cuando** el jugador entra a esa sala, **entonces** todas sus vecinas pasan a exploradas, el jugador conoce su nombre y sus salidas, no ve su contenido, y ningún enemigo ni trampa de esas vecinas se activa. *(FR-210, FR-211, FR-213)*
2. **Dado** la antorcha encendida, **cuando** el jugador entra a una sala y la antorcha explora una vecina, **entonces** las salas destino de las salidas de esa vecina pasan a avistadas si no estaban exploradas. *(FR-203, FR-210)*
3. **Dado** la antorcha encendida y una vecina detrás de una puerta cerrada, **cuando** el jugador entra a la sala, **entonces** esa vecina también queda explorada. *(FR-210)*
4. **Dado** la antorcha apagada, **cuando** el jugador entra a una sala, **entonces** sus vecinas solo pasan a avistadas. *(FR-204, FR-210)*
5. **Dado** el jugador ya dentro de una sala con la antorcha apagada, **cuando** la enciende, **entonces** sus vecinas no cambian de estado hasta la siguiente entrada a una sala. *(FR-212)*
6. **Dado** salas exploradas por la antorcha, **cuando** la antorcha se apaga, **entonces** esas salas siguen exploradas. *(FR-205, FR-212)*
7. **Dado** una vecina explorada por la antorcha en la que el jugador nunca estuvo, **cuando** se consulta el estado de las puertas de sus salidas que no dan a la sala actual, **entonces** figuran como «sin observar» y pasan a mostrar su estado real cuando el jugador entra a una de las dos salas que conectan cada una de esas puertas. *(FR-209, FR-207)*

---

### Historia 4 — El pergamino de retroceso también deshace lo descubierto (Prioridad: P1)

Al usar el pergamino, el conocimiento del jugador vuelve exactamente a como estaba antes de la acción deshecha: las salas exploradas o avistadas por esa acción dejan de estarlo y las puertas vuelven a recordarse como antes.

**Por qué esta prioridad**: sin esto el pergamino dejaría al jugador sabiendo cosas de un futuro deshecho; es un caso del Apéndice B.

**Prueba independiente**: tomar el conocimiento antes de una acción, ejecutarla, usar el pergamino y comparar.

**Escenarios de aceptación**:

1. *(Apéndice B)* **Dado** la antorcha encendida y el jugador que entra a una sala nueva, de modo que la sala y sus vecinas quedan exploradas, **cuando** usa el pergamino, **entonces** la sala y cada vecina explorada por la antorcha vuelven al estado que tenían antes (avistada o desconocida), y las salas avistadas por esa entrada vuelven a desconocidas si antes lo eran. *(FR-214)*
2. **Dado** el jugador que entra a una sala nueva sin antorcha, **cuando** usa el pergamino, **entonces** la sala vuelve a avistada y las salas que esa entrada había avistado vuelven a desconocidas. *(FR-214)*
3. **Dado** una acción durante la cual el jugador observó una puerta que había cambiado (o vio cambiar una puerta mientras estaba en su sala), **cuando** usa el pergamino, **entonces** el mapa vuelve a recordar el estado anterior de esa puerta. *(FR-214)*
4. **Dado** el jugador que nunca actuó, **cuando** intenta usar el pergamino, **entonces** la sala inicial sigue explorada y sus vecinas siguen avistadas. *(FR-215)*
5. **Dado** cinco acciones seguidas que exploraron salas, **cuando** se usan cinco pergaminos, **entonces** el conocimiento es idéntico al que había antes de la primera de esas acciones. *(FR-214)*

---

### Historia 5 — Ver el mapa conocido (Prioridad: P1)

Quien juega usa un comando para ver su mapa: las salas exploradas con sus salidas y las salas avistadas detrás de ellas. El mapa nunca revela nada que el jugador no sepa.

**Por qué esta prioridad**: es el valor visible de la capacidad; sin consulta el conocimiento no le sirve al jugador.

**Prueba independiente**: tras explorar parte de una cripta, mostrar el mapa y comprobarlo contra el conocimiento; luego alterar las partes desconocidas de la cripta y comprobar que el mapa no cambia.

**Escenarios de aceptación**:

1. **Dado** el jugador que exploró varias salas, **cuando** usa el comando de mapa, **entonces** se muestra cada sala explorada con su nombre y, por cada salida, su dirección, su costo, el estado recordado de la puerta y el destino: el nombre si está explorado o una marca de «sala sin explorar» si está avistado. *(FR-216, FR-217)*
2. **Dado** una sala desconocida, **cuando** se muestra el mapa, **entonces** no aparece de ninguna forma. *(FR-217)*
3. **Dado** dos partidas idénticas salvo por el nombre, las salidas o el contenido de salas desconocidas o avistadas, **cuando** se muestra el mapa en el mismo instante, **entonces** la salida es idéntica en las dos. *(FR-219)*
4. **Dado** dos salidas de salas exploradas que llevan a la misma sala avistada, **cuando** se muestra el mapa, **entonces** ambas aparecen como «sala sin explorar» sin revelar que se trata de la misma sala. *(FR-219)*
5. **Dado** la vista de la sala actual, **cuando** muestra sus salidas, **entonces** el destino de cada una aparece con nombre solo si la sala destino está explorada. *(FR-219)*
6. **Dado** una partida en curso, **cuando** el jugador consulta el mapa, **entonces** no avanza el reloj, no se registra una acción, el pergamino no la cuenta y la partida sigue idéntica a como habría seguido sin la consulta. *(FR-218)*

---

### Historia 6 — Guardar y cargar una partida con niebla (Prioridad: P2)

Quien juega guarda la partida y, al cargarla, conserva exactamente el mismo mapa conocido.

**Por qué esta prioridad**: el conocimiento es estado de la partida; perderlo al cargar rompería la experiencia. Depende de las historias 1 y 2.

**Prueba independiente**: explorar, guardar, cargar y comparar el conocimiento y la salida del mapa antes y después.

**Escenarios de aceptación**:

1. **Dado** una partida con salas exploradas, avistadas y puertas recordadas con un estado distinto del real, **cuando** se guarda y se carga, **entonces** cada sala tiene el mismo estado, cada puerta el mismo estado recordado y el mapa se muestra igual. *(FR-220)*
2. **Dado** una partida guardada y cargada, **cuando** se continúa con las mismas acciones que una partida que no se guardó, **entonces** el conocimiento resultante es idéntico en las dos. *(FR-220, FR-222)*
3. **Dado** un archivo de partida guardado por una versión sin niebla de guerra, **cuando** se intenta cargar, **entonces** se rechaza con un mensaje que indica la versión encontrada y la esperada, y no se carga. *(FR-221)*

---

### Historia 7 — Niebla determinista, neutral para los enemigos y rápida (Prioridad: P3)

Quien revisa reproduce una partida y obtiene el mismo mapa conocido; comprueba que los enemigos actúan igual con o sin niebla, y mide con `--bench` que el conocimiento se consulta, crece y se revierte con el costo esperado.

**Por qué esta prioridad**: garantía de calidad transversal; se prueba una vez que las historias anteriores existen.

**Prueba independiente**: ejecutar dos veces la misma partida y comparar; ejecutar `--bench` y leer sus secciones.

**Escenarios de aceptación**:

1. **Dado** la misma cripta, la misma semilla y las mismas acciones, **cuando** se juega dos veces, **entonces** el mapa conocido es idéntico en cada instante, con el contenido de las salas descargado o sin descargar. *(FR-222)*
2. **Dado** un enemigo en una sala desconocida para el jugador, **cuando** le toca actuar, **entonces** actúa exactamente igual que si la sala estuviera explorada. *(FR-213)*
3. **Dado** criptas sintéticas de tamaños distintos, **cuando** se mide la consulta del estado de una sala y del estado recordado de una puerta, **entonces** el tiempo no crece con el tamaño de la cripta ni del mapa conocido. *(FR-223, FR-226)*
4. **Dado** un mapa conocido grande, **cuando** el jugador entra a una sala que revela pocas salas nuevas, **entonces** el costo de actualizar el conocimiento depende de lo revelado y no del tamaño del mapa conocido ni de la cripta. *(FR-224, FR-226)*
5. **Dado** una acción que cambió k elementos del conocimiento, **cuando** se revierte con el pergamino, **entonces** el costo depende de k y no del tamaño del mapa conocido. *(FR-225, FR-226)*

---

### Casos límite

- Sala inicial: explorada desde el instante 0, con sus vecinas avistadas y sus puertas observadas; el pergamino no puede deshacer ese conocimiento (FR-202, FR-215).
- Salida con puerta cerrada o con llave: su destino se avista igual que el de una abierta (FR-204).
- Conexión de un solo sentido: solo avista quien tiene la salida, no la sala de destino (FR-203).
- Volver a entrar a una sala explorada: no cambia estados de salas; solo refresca la memoria de puertas (FR-205, FR-207).
- Puerta que cambia mientras el jugador está en una de sus salas: el mapa se actualiza en ese instante (FR-207).
- Puerta que cambia mientras el jugador está lejos: el mapa conserva el estado viejo hasta la siguiente observación (FR-208).
- Encender la antorcha dentro de una sala: no explora las vecinas hasta la siguiente entrada (FR-212).
- La antorcha se apaga: lo explorado con ella sigue explorado (FR-205).
- Vecina explorada por la antorcha: no se ve su contenido ni se activan sus enemigos ni trampas (FR-211); sus puertas no compartidas con la sala actual figuran como «sin observar» (FR-209).
- Varias salidas hacia la misma sala avistada: el mapa no revela que es la misma (FR-219).
- Consultar el mapa no es una acción: no consume tiempo ni pergamino (FR-218).

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Estados de conocimiento**

- **FR-201**: Para el jugador, cada sala de la cripta DEBE estar en exactamente uno de tres estados: explorada, avistada o desconocida.
- **FR-202**: La sala inicial DEBE estar explorada desde el instante 0; en ese instante el jugador DEBE observar sus puertas y avistar las salas destino de sus salidas, como si acabara de entrar a ella.
- **FR-203**: Una sala DEBE estar avistada si y solo si no está explorada y es destino de al menos una salida de una sala explorada, sin importar cómo llegó a estar explorada esa sala. De una sala avistada el jugador solo sabe que existe detrás de esa salida: NO conoce su nombre, sus salidas ni su contenido. Una sala que solo tiene una salida hacia una explorada, sin salida de vuelta, NO queda avistada por esa conexión.
- **FR-204**: Al entrar el jugador a una sala, esta DEBE pasar a explorada y cada sala destino de cualquiera de sus salidas, abierta o cerrada, DEBE pasar a avistada si no estaba explorada.
- **FR-205**: Una sala explorada NO DEBE volver a avistada ni a desconocida, y una avistada NO DEBE volver a desconocida, salvo por el pergamino de retroceso (FR-214). Volver a entrar a una sala explorada no cambia el estado de ninguna sala.
- **FR-206**: De cada sala explorada el jugador DEBE conocer su nombre, sus salidas (dirección y sala destino), el costo de cada salida y el estado recordado de la puerta de cada salida (abierta, cerrada o «sin observar», FR-209).

**Memoria de puertas**

- **FR-207**: El jugador DEBE observar una puerta en todo instante en que esté en cualquiera de las dos salas que conecta: al entrar a una de ellas y cada vez que la puerta cambie de estado mientras él siga allí. Observar una puerta hace que su estado recordado pase a ser el estado real en ese instante.
- **FR-208**: El estado recordado de una puerta NO DEBE cambiar mientras el jugador no la observe, aunque su estado real cambie (por ejemplo, por cierre automático).
- **FR-209**: Una puerta que el jugador nunca ha observado (solo posible en salas exploradas por la antorcha) DEBE figurar como «sin observar»; la antorcha NO DEBE observar puertas. Pasa a tener estado recordado en la primera observación (FR-207).

**Antorcha**

- **FR-210**: Si la antorcha está encendida en el instante en que el jugador entra a una sala, además de lo dispuesto en FR-204, cada sala destino de cualquiera de las salidas de esa sala, abierta o cerrada, DEBE pasar a explorada; y por FR-203, los destinos de las salidas de esas vecinas pasan a avistados si no estaban explorados.
- **FR-211**: Explorar una sala con la antorcha DEBE revelar solo su nombre, sus salidas y el costo de cada salida; NO DEBE revelar su contenido (objetos, enemigos, trampas), NO DEBE activar sus enemigos ni sus trampas y NO DEBE contar como entrar a esa sala para ninguna regla existente.
- **FR-212**: La antorcha DEBE actuar solo en el instante de entrar a una sala: encenderla dentro de una sala no explora sus vecinas, y apagarla no quita lo explorado.

**Enemigos**

- **FR-213**: El conocimiento del jugador NO DEBE afectar a ningún enemigo: sus decisiones, movimientos y activaciones DEBEN ser los mismos sea cual sea el estado de conocimiento de cualquier sala.

**Pergamino de retroceso**

- **FR-214**: Todo cambio al conocimiento (explorar, avistar u observar una puerta con un estado distinto del recordado) producido por una acción del jugador o por lo ocurrido hasta su siguiente decisión DEBE formar parte de esa acción; al deshacerla con el pergamino, el conocimiento DEBE quedar exactamente como estaba antes de ella, incluidas las salas exploradas por la antorcha.
- **FR-215**: El conocimiento del instante 0 (FR-202) NO DEBE poder deshacerse con el pergamino.

**Mapa conocido y vista**

- **FR-216**: El jugador DEBE disponer de un comando que muestre el mapa conocido: cada sala explorada con su nombre y, por cada salida, su dirección, su costo, el estado recordado de su puerta (abierta, cerrada o «sin observar») y su destino (el nombre si la sala destino está explorada, o una marca de «sala sin explorar» si está avistada).
- **FR-217**: El mapa DEBE listar las salas exploradas en orden ascendente de id y las salidas de cada sala en el orden en que la sala las declara; las salas avistadas aparecen solo como destino de salidas y las desconocidas NO DEBEN aparecer.
- **FR-218**: Consultar el mapa NO DEBE avanzar el reloj, contar como acción ni ser deshecho por el pergamino, y NO DEBE alterar en nada la partida.
- **FR-219**: Todo lo que la vista muestre sobre la cripta fuera del contenido de la sala actual (en el mapa y en la vista de la sala actual) DEBE obtenerse solo del conocimiento del jugador, nunca del mapa completo ni del estado real de las puertas. En particular, el destino de una salida se muestra con nombre solo si está explorado, y la vista NO DEBE revelar la identidad de una sala avistada ni que dos salidas llevan a la misma sala avistada.

**Partida guardada**

- **FR-220**: El conocimiento DEBE formar parte del estado de la partida: la partida guardada DEBE incluir el estado (explorada o avistada) de cada sala no desconocida y el estado recordado de cada puerta observada, y al cargarla DEBE restaurarse exactamente.
- **FR-221**: Un archivo de partida guardado por una versión sin niebla de guerra DEBE rechazarse con un mensaje que indique la versión encontrada y la esperada; NO DEBE cargarse ni migrarse.

**Determinismo**

- **FR-222**: Misma cripta, misma semilla y mismas acciones DEBEN producir el mismo mapa conocido en cada instante, con independencia de qué contenido de sala ya fue descargado y de si la partida se guardó y cargó por el camino.

**Rendimiento**

- **FR-223**: Consultar el estado de conocimiento de una sala y el estado recordado de una puerta NO DEBE crecer con el tamaño de la cripta ni del mapa conocido.
- **FR-224**: Actualizar el conocimiento al entrar a una sala (con o sin antorcha) DEBE costar en proporción a las salas y salidas reveladas, no al tamaño del mapa conocido ni de la cripta.
- **FR-225**: Registrar un cambio de conocimiento para el pergamino y revertirlo DEBE costar en proporción a los cambios de esa acción, sin copiar el conocimiento completo.
- **FR-226**: `--bench` DEBE poder medir, en criptas sintéticas de varios tamaños: la consulta del estado de una sala y de una puerta, la exploración con y sin antorcha, y la reversión con el pergamino.

### Entidades clave

- **Conocimiento del jugador**: lo que el jugador sabe de la cripta; parte del estado de la partida. Se compone del estado de cada sala y de la memoria de puertas.
- **Estado de una sala**: explorada (se conoce nombre, salidas y costos), avistada (solo se sabe que existe detrás de una salida conocida) o desconocida.
- **Puerta recordada**: estado de una puerta tal como estaba en la última observación del jugador (abierta o cerrada), o «sin observar» si nunca la observó; puede no coincidir con el real.
- **Observación**: instante en que el jugador está en una de las dos salas que conecta una puerta y actualiza su estado recordado.
- **Mapa conocido**: presentación del conocimiento del jugador, a pedido.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: En el 100 % de los escenarios de aceptación de las historias 1 a 6, el comportamiento observado coincide con el descrito.
- **SC-002**: Al alterar nombres, salidas, contenido o puertas de las salas desconocidas o avistadas, la salida del mapa en el mismo instante no cambia en ningún caso.
- **SC-003**: Tras cualquier secuencia de hasta 5 acciones deshechas con el pergamino, el conocimiento coincide en el 100 % de los casos con el que había antes de esas acciones.
- **SC-004**: Una partida guardada y cargada muestra el mismo mapa conocido que antes de guardar.
- **SC-005**: Dos ejecuciones con la misma cripta, semilla y acciones producen el mismo mapa conocido en cada instante y registros idénticos.
- **SC-006**: Al multiplicar por 10 el tamaño de la cripta, el tiempo de consultar el estado de una sala o de una puerta no aumenta de forma apreciable.
- **SC-007**: Quien juega identifica en el mapa, sin consultar documentación, qué salidas de las salas exploradas llevan a salas sin explorar y qué puertas recuerda cerradas.

## Supuestos

- El esqueleto de la cripta, descargado completo al iniciar, incluye el nombre y las salidas de cada sala; por eso explorar una sala con la antorcha no requiere descargar su contenido.
- El jugador «entra» a una sala en el instante en que su movimiento termina, según la regla existente de movimiento; mientras cruza una salida sigue observando las puertas de la sala de origen.
- Una puerta es una sola para las dos salas que conecta; abrirla o cerrarla desde un lado cambia su estado visto desde el otro.
- El id de una sala explorada puede mostrarse; el de una avistada no.
- La forma exacta del comando de mapa y su presentación textual se definen en el plan; esta especificación fija qué se muestra y qué no.
- La cripta de referencia y los umbrales de tiempo son los del reglamento del proyecto.
