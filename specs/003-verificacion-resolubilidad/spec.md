# Especificación de capacidad: Verificación de resolubilidad

**Carpeta**: `003-verificacion-resolubilidad`

**Creada**: 2026-11-08

**Estado**: Borrador

**Entrada**: Capacidad 3 de la Parte II — verificación de resolubilidad de una cripta: opción `--verificar`, opción `--forzar` y resultado de la verificación (`ResultadoVerificacion`). Requisitos con prefijo FR-330 en adelante (la 009 llegó hasta FR-325; la 010 usa FR-360).

## Contexto y motivación

Una cripta con puertas cerradas y llaves repartidas puede quedar sin solución: por ejemplo, la llave de una puerta está detrás de esa misma puerta. Quien juega descubriría el problema después de recorrer media cripta, sin poder hacer nada. Antes de jugar, el juego debe poder decir si la cripta se puede completar y, si no, explicar por qué y hasta dónde se llega.

**Lo existente y vigente (no se re-especifica)**: el mapa de la cripta con sus salas, salidas (que pueden ser de un solo sentido) y puertas cerradas, cada una con la llave que la abre; la sala inicial, la sala de salida y la llave de salida en los datos generales de la cripta; la ubicación de las llaves (sala del suelo, o enemigo que la suelta y su sala inicial) que entrega la capacidad 009 mediante la consulta de llaves, una sola vez por cripta y sin solicitudes si ya está guardada (FR-301 a FR-325); el aviso de FR-313 cuando una partida no puede obtener las llaves; el recorrido por niveles de la capacidad 005, con desempate por menor id de sala; el cliente real, `--offline` y la API falsa v2 con los casos del Apéndice B.

**Fuera de alcance**: obtener las llaves (009); el formato de guardado (010); la niebla de guerra (002); el cableado de `--verificar` y `--forzar` en la línea de comandos (lo hace Fernanda usando la operación y el resultado que define esta capacidad); cualquier cambio de puertas durante la partida (la verificación mira la cripta tal como se publica al iniciar).

## Clarificaciones

### Sesión 2026-11-08

- Q: ¿Qué significa completar la cripta? → A: Llegar a la sala de salida respetando las puertas, con la llave de salida obtenible; no se exige una puerta concreta hacia la sala de salida (FR-332).
- Q: Cuando varias llaves se pueden conseguir en el mismo momento, ¿en qué orden aparecen? → A: Por menor id de la sala donde se ubica la llave y, dentro de la misma sala, por id de llave (FR-335).
- Q: Con `--forzar`, ¿dónde se ve el aviso de cripta no resoluble? → A: Solo al iniciar la partida, igual que el aviso de FR-313 (FR-340).
- Q: ¿Qué significa que varias llaves se vuelvan obtenibles «en el mismo momento»? → A: Por oleadas: una oleada son todas las llaves que se pueden conseguir antes de tener que abrir otra puerta; dentro de la oleada, menor sala y luego id; una oleada anterior siempre va antes que una posterior (FR-335).
- Q: Al iniciar una partida nueva, si las llaves se obtuvieron pero la verificación no se puede completar por datos inválidos de la cripta, ¿la partida inicia? → A: Sí, con un aviso que da el motivo y dice que la verificación no está disponible, igual que cuando faltan las llaves; `--verificar` sigue terminando con el código de error de datos (FR-339).
- Q: Si una puerta bloqueada pide una llave que existe pero está en una sala sin camino desde la sala inicial ni abriendo todas las puertas, ¿cómo se clasifica? → A: Como bloqueo, con el motivo «la llave está en una sala sin camino desde la sala inicial»; una puerta cerrada sin llave también es un bloqueo, con el motivo «no tiene llave» (FR-338).

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Saber antes de jugar si la cripta se puede completar (Prioridad: P1)

Quien juega ejecuta `--verificar <cripta>`. El juego analiza la cripta sin iniciar partida, sin abrir la vista, y muestra un reporte: si la cripta es resoluble, un orden válido en el que conseguir las llaves; si no lo es, qué llaves y puertas forman el ciclo o bloqueo y hasta qué salas sí se llega. El programa termina con código 0 solo si la cripta es resoluble.

**Por qué esta prioridad**: es el núcleo de la capacidad; todo lo demás (bloquear el inicio, forzar) usa este mismo resultado.

**Prueba independiente**: con la API falsa v2, ejecutar `--verificar` sobre una cripta resoluble y sobre la cripta del caso B-R1, y comprobar reporte y código de salida.

**Escenarios de aceptación**:

1. **Dado** una cripta sin puertas cerradas entre la sala inicial y la sala de salida, y la llave de salida en una sala alcanzable, **cuando** se ejecuta `--verificar`, **entonces** el reporte dice que la cripta es resoluble, muestra el orden de llaves y el programa termina con código 0, sin iniciar partida. *(FR-330, FR-331, FR-336)*
2. **(B-R1)** **Dado** una cripta en la que la llave de salida está detrás de la única puerta que ella misma abre, **cuando** se ejecuta `--verificar`, **entonces** el reporte dice que no es resoluble, señala el ciclo (esa llave y esa puerta) y las salas a las que sí se llega, y el programa termina con un código distinto de cero. *(FR-332, FR-333, FR-334, FR-337, FR-338)*
3. **Dado** una cripta con una cadena de puertas A → B → C en la que la llave de cada puerta está antes de ella, **cuando** se ejecuta `--verificar`, **entonces** es resoluble y el orden de llaves es el de la cadena. *(FR-333, FR-336)*
4. **Dado** una cripta cuya sala de salida no tiene ningún camino desde la sala inicial, aunque se tengan todas las llaves, **cuando** se ejecuta `--verificar`, **entonces** no es resoluble y el reporte indica que la sala de salida no es alcanzable y hasta qué salas se llega. *(FR-332, FR-337, FR-338)*
5. **Dado** una cripta cuya llave de salida no aparece en la ubicación de llaves, **cuando** se ejecuta `--verificar`, **entonces** no es resoluble y el reporte indica que la llave de salida no existe en la cripta. *(FR-332, FR-338)*
6. **Dado** una puerta que solo se puede abrir con una llave ubicada detrás de una salida de un solo sentido que no tiene vuelta, **cuando** se ejecuta `--verificar`, **entonces** el resultado respeta el sentido de las salidas: una sala solo es alcanzable si existe un camino en el sentido permitido. *(FR-333, FR-334)*
7. **Dado** una puerta cerrada que pide la llave `L`, y `L` está solo en una sala sin ningún camino desde la sala inicial (ni abriendo todas las puertas), **cuando** se ejecuta `--verificar`, **entonces** el reporte muestra esa puerta como bloqueo con el motivo «la llave está en una sala sin camino desde la sala inicial», no como ciclo. *(FR-338)*

---

### Historia 2 — Llaves que suelta un enemigo (Prioridad: P1)

Algunas llaves no están en el suelo: las suelta un enemigo. La verificación las considera ubicadas en la sala donde ese enemigo inicia, aunque el enemigo se mueva durante la partida.

**Por qué esta prioridad**: sin esto, cualquier cripta con llaves en enemigos se declararía no resoluble por error (o resoluble por error).

**Prueba independiente**: con la cripta del caso B-R2 de la API falsa v2, ejecutar `--verificar` y comprobar que la llave aparece asociada a la sala inicial del enemigo.

**Escenarios de aceptación**:

1. **(B-R2)** **Dado** una cripta en la que una llave está en lo que suelta un enemigo errante, **cuando** se ejecuta `--verificar`, **entonces** la verificación ubica la llave en la sala inicial del enemigo y el reporte la muestra con esa sala y ese enemigo. *(FR-334, FR-336)*
2. **Dado** un enemigo que suelta una llave e inicia en una sala que solo se alcanza cruzando una puerta, **cuando** la llave de esa puerta es obtenible, **entonces** la llave del enemigo también lo es; **cuando** no lo es, la llave del enemigo tampoco. *(FR-334)*
3. **Dado** una misma llave ubicada en el suelo de una sala y en lo que suelta un enemigo, **cuando** se verifica, **entonces** basta con que una de sus ubicaciones sea alcanzable para que la llave sea obtenible. *(FR-334)*

---

### Historia 3 — Un orden de llaves que siempre es el mismo (Prioridad: P1)

Cuando hay varios órdenes válidos de obtener las llaves, la verificación elige siempre el mismo, con una regla de desempate fija. Dos ejecuciones sobre la misma cripta producen el mismo reporte, carácter por carácter.

**Por qué esta prioridad**: el principio de determinismo lo exige, y sin él las pruebas y los reportes no se pueden comparar.

**Prueba independiente**: con la cripta del caso B-R3, ejecutar `--verificar` dos veces (con y sin datos guardados) y comparar los reportes.

**Escenarios de aceptación**:

1. **(B-R3)** **Dado** una cripta con varios órdenes válidos de obtención de llaves, **cuando** se ejecuta `--verificar` dos veces, **entonces** las dos ejecuciones producen el mismo orden y el mismo reporte. *(FR-335, FR-336)*
2. **Dado** una cripta cuya sala inicial es la 5, en la que en la misma oleada se vuelven obtenibles la llave `X` en la sala 4, la llave `B` en la sala 2 y la llave `A` también en la sala 2, y la llave `C` está en la sala 3, detrás de una puerta que se abre con `A`, **cuando** se verifica, **entonces** el orden es `A`, `B`, `X`, `C`: dentro de la primera oleada, primero por menor id de sala y, dentro de la sala 2, por id de llave; `C` va última aunque su sala tenga menor id que la de `X`, porque es de la oleada siguiente. *(FR-335)*
3. **Dado** la misma cripta, **cuando** se verifica una vez con el contenido de las salas ya guardado y otra sin él, **entonces** el reporte es idéntico. *(FR-335, FR-341)*
4. **Dado** la misma cripta, **cuando** se verifica con el cliente real, con `--offline` y con la API falsa v2 sobre los mismos datos, **entonces** el resultado es el mismo. *(FR-335, FR-342)*
5. **Dado** una cripta, **cuando** se verifica con `--verificar` y al iniciar una partida, **entonces** ambos usan la misma operación de verificación y obtienen el mismo resultado (resoluble o no, mismo orden, mismo bloqueo). *(FR-344, FR-339)*

---

### Historia 4 — No empezar una partida imposible, salvo que se fuerce (Prioridad: P2)

Al iniciar una partida nueva, el juego verifica la cripta. Si no es resoluble, la partida no inicia y se muestra el reporte. Quien quiera jugar igualmente (para explorar o probar) usa `--forzar`: la partida inicia y el aviso de que la cripta no es resoluble queda visible.

**Por qué esta prioridad**: protege a quien juega, pero depende de la Historia 1.

**Prueba independiente**: con la cripta del caso B-R4 de la API falsa v2, iniciar una partida sin `--forzar` y con `--forzar`.

**Escenarios de aceptación**:

1. **(B-R4)** **Dado** una cripta no resoluble, **cuando** se intenta iniciar una partida sin `--forzar`, **entonces** la partida no inicia, se muestra el reporte de la verificación y no se escribe ninguna acción en el registro de partida. *(FR-339)*
2. **Dado** una cripta no resoluble, **cuando** se inicia una partida con `--forzar`, **entonces** la partida inicia y el aviso de que la cripta no es resoluble se muestra al iniciar la partida, igual que el aviso de FR-313, y no se repite durante la partida. *(FR-340)*
3. **Dado** una cripta resoluble, **cuando** se inicia una partida, con o sin `--forzar`, **entonces** la partida inicia con normalidad y sin aviso. *(FR-339, FR-340)*
4. **Dado** una cripta cuyas llaves no se pudieron obtener, **cuando** se inicia una partida, **entonces** la partida continúa con el aviso de FR-313 (la verificación no está disponible) y no se bloquea. *(FR-339, FR-313)*
5. **Dado** una cripta con llaves obtenidas cuya sala de salida no existe en el mapa, **cuando** se inicia una partida, **entonces** la partida inicia con un aviso que da el motivo y dice que la verificación no está disponible; **cuando** se ejecuta `--verificar` sobre la misma cripta, **entonces** termina con el código de error de datos. *(FR-339, FR-343)*

---

### Historia 5 — Errores claros cuando faltan los datos (Prioridad: P2)

Si no se pueden obtener las llaves de la cripta (servicio sin responder, presupuesto agotado, respuesta inválida o `--offline` sin llaves guardadas), `--verificar` no inventa un resultado: muestra un error claro que nombra la cripta y el motivo, y termina con un código distinto de cero, distinto del de «no resoluble».

**Por qué esta prioridad**: un resultado inventado haría creer que una cripta es (o no es) resoluble sin serlo.

**Prueba independiente**: con la API falsa v2 configurada para fallar en la consulta de llaves, y con `--offline` sobre una caché sin llaves.

**Escenarios de aceptación**:

1. **Dado** que el servicio no responde a la consulta de llaves, **cuando** se ejecuta `--verificar`, **entonces** se muestra un error que nombra la cripta y el motivo, no se muestra «resoluble» ni «no resoluble», y el programa termina con el código de error de datos. *(FR-331, FR-343)*
2. **Dado** `--offline` y una cripta guardada sin llaves (o, en general, no guardada completa: mapa, datos generales, llaves y contenido de todas sus salas), **cuando** se ejecuta `--verificar`, **entonces** se muestra el error claro, no se hacen solicitudes y el programa termina con el código de error de datos. *(FR-342, FR-343)*
3. **Dado** una cripta con las llaves ya guardadas y vigentes, **cuando** se ejecuta `--verificar`, **entonces** no se hace ninguna solicitud de llaves ni de contenido de salas. *(FR-341)*
4. **Dado** una cripta que no existe, **cuando** se ejecuta `--verificar`, **entonces** se muestra un error claro que la nombra y el programa termina con el código de error de datos. *(FR-343)*

---

### Historia 6 — Verificar rápido incluso en criptas grandes (Prioridad: P3)

La verificación tarda menos de 200 ms en la cripta más grande publicada, con los datos ya descargados, y su costo crece de forma aproximadamente proporcional al tamaño de la cripta (salas, salidas y llaves).

**Por qué esta prioridad**: la verificación se hace en cada inicio de partida; no debe notarse.

**Prueba independiente**: `--bench` con criptas sintéticas deterministas de muchas llaves encadenadas a dos tamaños.

**Escenarios de aceptación**:

1. **Dado** la cripta más grande publicada con sus datos guardados, **cuando** se verifica, **entonces** tarda menos de 200 ms. *(FR-345)*
2. **Dado** dos criptas sintéticas de llaves encadenadas, la segunda al menos 10 veces más grande que la primera, **cuando** se ejecuta `--bench`, **entonces** el tiempo crece de forma aproximadamente proporcional al tamaño y el reporte del bench muestra ambos tamaños y la alternativa descartada. *(FR-346)*

---

### Casos límite

- La sala inicial es la sala de salida: la cripta es resoluble si la llave de salida es obtenible desde ahí.
- La llave de salida está en la sala inicial y no hay puertas: resoluble, con el orden de llaves formado solo por la llave de salida.
- Una puerta cerrada sin llave asignada: nunca se puede cruzar; si separa lo alcanzable de lo no alcanzable, el reporte la muestra como bloqueo con el motivo «no tiene llave» (FR-338).
- Una puerta pide una llave que está en una sala sin ningún camino desde la sala inicial, ni abriendo todas las puertas: bloqueo con el motivo «la llave está en una sala sin camino desde la sala inicial», no ciclo (FR-338).
- Una misma llave abre varias puertas: una vez obtenible, sirve para todas (las llaves no se gastan al abrir).
- Una llave aparece en varias ubicaciones: figura una sola vez en el orden, en el momento en que la primera de sus ubicaciones resulta alcanzable.
- Llaves que no hacen falta para salir (están en salas alcanzables pero no abren nada necesario): aparecen en el orden si son obtenibles antes de alcanzar la salida [ver Supuestos].
- Una salida que lleva a una sala que no existe en la cripta: se ignora, igual que en el recorrido de la capacidad 005.
- Una ubicación de llave en una sala inexistente o un enemigo que no está donde se indica: lo rechaza ya la capacidad 009 (FR-311); para esta capacidad es un error de datos.
- Varios bloqueos independientes: el reporte los muestra todos, en orden determinista.
- La cripta cambia de versión entre `--verificar` y la partida: la partida vuelve a verificar con los datos vigentes al iniciar.
- Partida cargada y reproducción (`--replay`, `--hasta`): no se verifica al cargar ni al reproducir; no son partidas nuevas.
- Datos inválidos de la cripta al iniciar una partida (llaves presentes, pero la sala inicial o la de salida no existe en el mapa): la partida inicia con aviso; `--verificar` da error de datos (FR-339, FR-343).

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Verificación desde la línea de comandos**

- **FR-330**: `--verificar <cripta>` DEBE analizar la cripta sin iniciar una partida, sin abrir la vista y sin escribir el registro de partida, y DEBE mostrar un reporte de la verificación. En esta capacidad el comportamiento se verifica en la operación de verificación (FR-344); la prueba desde la consola es de la capacidad que conecta las opciones `--verificar` y `--forzar`.
- **FR-331**: `--verificar` DEBE terminar con código de salida 0 si la cripta es resoluble, con un código distinto de cero si no es resoluble, y con otro código distinto de cero (y distinto del anterior) si no se pudieron obtener los datos necesarios. En esta capacidad el comportamiento se verifica en la operación de verificación (FR-344); la prueba desde la consola es de la capacidad que conecta las opciones `--verificar` y `--forzar`.

**Regla de resolubilidad**

- **FR-332**: Una cripta DEBE considerarse resoluble si y solo si, partiendo de la sala inicial, existe un orden de obtención de llaves que permite completarla usando la llave de salida. Completarla significa llegar a la sala de salida respetando las puertas (FR-333) con la llave de salida obtenible (FR-334); NO DEBE exigirse una puerta concreta hacia la sala de salida.
- **FR-333**: Una sala DEBE considerarse alcanzable si existe un camino desde la sala inicial, respetando el sentido de las salidas, en el que cada puerta cerrada que se cruza tiene su llave ya obtenible. Una puerta cerrada sin llave asignada NO DEBE cruzarse nunca.
- **FR-334**: Una llave DEBE considerarse obtenible cuando al menos una de sus ubicaciones está en una sala alcanzable: el suelo de esa sala o lo que suelta un enemigo cuya sala inicial es esa sala. El movimiento del enemigo durante la partida NO DEBE influir.
- **FR-335**: La verificación DEBE ser determinista: la misma cripta con los mismos datos DEBE producir siempre el mismo resultado, el mismo orden de llaves y el mismo reporte, aunque existan varios órdenes válidos, sin depender del orden en que llegaron los datos ni de qué contenido ya estaba guardado. El orden DEBE construirse por **oleadas**: una oleada son todas las llaves que se pueden obtener antes de tener que abrir otra puerta; las llaves de una oleada anterior van siempre antes que las de una posterior. Dentro de una oleada, el desempate DEBE ser por menor id de la sala donde se ubica la llave y, dentro de la misma sala, por id de llave.

**Reporte**

- **FR-336**: Si la cripta es resoluble, el reporte DEBE mostrar un orden válido de obtención de llaves: cada llave con la sala donde se obtiene y, si la suelta un enemigo, qué enemigo es; la llave de salida DEBE figurar en el orden.
- **FR-337**: Si la cripta no es resoluble, el reporte DEBE mostrar las salas alcanzables (en orden creciente de id) y la cantidad de salas no alcanzables.
- **FR-338**: Si la cripta no es resoluble, el reporte DEBE indicar el motivo: cada puerta que separa lo alcanzable de lo no alcanzable con la llave que necesita y dónde está esa llave, señalando como **ciclo** cuando la llave está detrás de esa misma puerta (directamente o a través de otras puertas bloqueadas), y como **bloqueo**, con su motivo, cuando la puerta está cerrada y no tiene llave, cuando la llave no existe en la cripta o cuando la llave existe pero todas sus ubicaciones están en salas sin camino desde la sala inicial aunque se abrieran todas las puertas. Una llave cuenta como «detrás de la puerta» (ciclo) solo si alguna de sus ubicaciones tiene camino desde la sala inicial abriendo todas las puertas. Los ciclos y bloqueos se refieren solo a puertas; el reporte DEBE indicar además la **causa** de que la cripta no sea resoluble: que la llave de salida no exista en la cripta, que la sala de salida no tenga camino aunque se tengan todas las llaves, que tenga camino pero las puertas lo impidan, o que se llegue a ella pero la llave de salida no se pueda obtener.

**Inicio de partida**

- **FR-339**: Al iniciar una partida nueva, el juego DEBE verificar la cripta; si no es resoluble y no se usó `--forzar`, la partida NO DEBE iniciar y DEBE mostrarse el reporte. Si las llaves no se pudieron obtener, se aplica FR-313: la partida continúa con aviso y no se bloquea. Si las llaves se obtuvieron pero la verificación no se puede completar por datos inválidos de la cripta (por ejemplo, la sala inicial o la de salida no existe en el mapa), la partida tampoco se bloquea: continúa con un aviso, mostrado solo al iniciar, que da el motivo y dice que la verificación de resolubilidad no está disponible. En esta capacidad la verificación al iniciar se prueba en la operación de inicio de partida (`iniciarJuego`); mostrar el reporte y el aviso en pantalla es de la capacidad que conecta las opciones `--verificar` y `--forzar`.
- **FR-340**: Con `--forzar`, una cripta no resoluble DEBE iniciar igualmente y el aviso de que no es resoluble DEBE mostrarse al iniciar la partida, igual que el aviso de FR-313. `--forzar` NO DEBE cambiar nada en una cripta resoluble. En esta capacidad el comportamiento se verifica en la operación de verificación (FR-344); la prueba desde la consola es de la capacidad que conecta las opciones `--verificar` y `--forzar`.

**Datos y solicitudes**

- **FR-341**: La verificación DEBE usar solo el mapa de la cripta, sus datos generales y la ubicación de llaves de la capacidad 009. NO DEBE pedir contenido de salas ni hacer solicitudes más allá de la consulta de llaves de la 009 (que no gasta nada si ya está guardada) y de la descarga del mapa existente.
- **FR-342**: La verificación DEBE funcionar igual con el cliente real, con `--offline` y con la API falsa v2, y dar el mismo resultado sobre los mismos datos. Con `--offline` la cripta DEBE estar guardada completa (mapa, datos generales, llaves y el contenido de todas sus salas, como exige la capacidad 009); si no lo está, se informa como cripta inexistente y el código de salida es 2, igual que cualquier otro error de datos (FR-343).
- **FR-343**: Si no se pueden obtener la ubicación de llaves, el mapa o los datos generales de la cripta, la verificación NO DEBE dar un resultado de resoluble o no resoluble: DEBE informar un error claro que nombre la cripta y el motivo.

**Interfaz para otras capacidades**

- **FR-344**: DEBE existir una operación de verificación que reciba el id de una cripta y devuelva el resultado de la verificación: si es resoluble, el orden de llaves, el ciclo o bloqueo con las salas alcanzables, y el motivo de error si no hubo datos. `--verificar`, `--forzar` y el inicio de partida DEBEN usar esa misma operación, sin repetir la regla.

**Rendimiento**

- **FR-345**: La verificación DEBE tardar menos de 200 ms en la cripta más grande publicada, con los datos ya guardados.
- **FR-346**: El costo de la verificación DEBE crecer de forma aproximadamente lineal con la cantidad de salas, salidas y llaves. DEBE medirse con `--bench` sobre criptas sintéticas deterministas por semilla, con muchas llaves encadenadas, a dos tamaños, junto con la alternativa descartada.

### Entidades clave

- **Resultado de la verificación** (`ResultadoVerificacion`, nombre acordado con quien conecta las opciones): si la cripta es resoluble; el orden de llaves (si lo es); el ciclo o bloqueo y las salas alcanzables (si no lo es); el motivo de error (si no hubo datos, en cuyo caso no dice resoluble ni no resoluble).
- **Paso del orden de llaves**: una llave, la sala donde se obtiene y, si corresponde, el enemigo que la suelta.
- **Bloqueo**: una puerta (sala de origen, sala de destino) con la llave que necesita y dónde está esa llave o que no existe, y si forma un ciclo.
- **Reporte de verificación**: el texto que ve quien juega, construido solo a partir del resultado, idéntico entre ejecuciones.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Los cuatro casos de resolubilidad del Apéndice B (B-R1 a B-R4) pasan como pruebas automatizadas que citan sus requisitos.
- **SC-002**: Dos ejecuciones de `--verificar` sobre la misma cripta producen reportes idénticos en el 100 % de las pruebas, incluida la comparación con y sin contenido de salas guardado.
- **SC-003**: Con las llaves guardadas, la verificación no hace ninguna solicitud de llaves, de salas ni de contenido (más allá del arranque de la Parte I: lista de criptas y validación de versión); sin ellas, hace como máximo la única consulta de llaves de la 009.
- **SC-004**: El 100 % de los fallos de datos terminan con un mensaje que nombra la cripta y el motivo y con el código de error de datos; ninguno muestra un resultado de resolubilidad.
- **SC-005**: Ninguna partida sobre una cripta no resoluble inicia sin `--forzar`; con `--forzar`, el 100 % muestra el aviso.
- **SC-006**: La verificación de la cripta más grande publicada tarda menos de 200 ms con los datos guardados.
- **SC-007**: En las criptas sintéticas de llaves encadenadas, al multiplicar el tamaño por al menos 10, el tiempo de verificación no crece más del doble de esa proporción.

## Supuestos

- Las llaves no se gastan: una llave obtenible abre todas las puertas que piden su id, durante toda la partida.
- Que un enemigo suelte una llave se considera obtenible con solo alcanzar su sala inicial; la dificultad de vencerlo no forma parte de la verificación.
- El orden de llaves incluye todas las llaves obtenibles antes de completar la cripta según la regla de desempate, no solo las imprescindibles; mostrar solo las imprescindibles queda fuera de esta capacidad.
- Si al iniciar una partida las llaves no se pueden obtener, se respeta FR-313 de la 009 (continúa con aviso); solo `--verificar` termina con error.
- La partida cargada y la reproducción no verifican, igual que no piden las llaves al cargar (FR-325 de la 009).
- Los códigos de salida concretos (por ejemplo 1 para «no resoluble» y 2 para «error de datos») se fijan en el plan; esta especificación solo exige que sean distintos entre sí y de 0.
- La «cripta más grande publicada» es la de mayor cantidad de salas en el catálogo del servicio en el momento de medir.
