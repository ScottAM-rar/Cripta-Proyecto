# Especificación de capacidad: Terreno y cazador

**Rama / carpeta**: `001-terreno-y-cazador`

**Creada**: 2026-10-27

**Estado**: Borrador

**Entrada**: Capacidad 1 de la Parte II — costo de las salidas (terreno) y enemigo cazador. Requisitos con prefijo FR-1xx.

## Contexto y motivación

Hoy moverse cuesta siempre 100 y los enemigos solo persiguen mirando las salas vecinas. Esta capacidad hace que cada salida tenga un costo de tránsito, de modo que algunos caminos sean más caros que otros, y agrega un enemigo, el cazador, que sí calcula la ruta más barata hasta el jugador.

Quien juega debe sentir que algunas rutas conviene evitarlas y que ciertos enemigos lo persiguen de forma inteligente pero predecible. Quien revisa debe poder predecir, dado un estado, qué hará un cazador.

**Lo existente y vigente (no se re-especifica)**: reloj virtual con eventos ordenados por tiempo y número de secuencia; intervalo de una acción = `max(1, costo*100 // velocidad)`; enemigos errante, guardián y rastreador; costos propios de ataque, espera y demás acciones; puertas abiertas o cerradas, con llave y con cierre automático; esqueleto de la cripta descargado completo al iniciar, con el estado de las puertas.

**Fuera de alcance**: niebla de guerra, «ir a», resolubilidad y línea de tiempo (otras capacidades); cambios al costo de ataque, espera u otras acciones.

## Clarificaciones

### Sesión 2026-10-27

- Q: Si una puerta se cierra mientras un actor cruza esa salida, ¿el cruce se completa o se cancela? → A: Se completa; la puerta se evalúa solo al iniciar el movimiento.
- Q: Si una salida declara un costo inválido (cero, negativo o no entero), ¿qué hace el juego? → A: Usa 100 para esa salida y emite una advertencia.
- Q: Si la ficha de un cazador no trae rango o es inválido, ¿qué hace el juego y qué significa rango 0? → A: Se trata como 0 con advertencia; rango 0 declarado es válido y solo ataca en su sala.
- Q: Si las dos salidas de una misma conexión declaran costos distintos, ¿qué costo vale para ambos sentidos? → A: El declarado por la sala de menor id, con advertencia; si solo una declara costo, ese vale para ambos sentidos.
- Q: ¿Se permiten conexiones de un solo sentido (una sala con salida hacia otra que no tiene salida de vuelta)? → A: Sí, son válidas.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Las salidas tienen costo de tránsito (Prioridad: P1)

Quien juega ve el costo de cada salida de la sala actual y comprueba que cruzar una salida cara tarda más que cruzar una barata. Los enemigos existentes se mueven con las mismas reglas de costo.

**Por qué esta prioridad**: es la base de la capacidad; sin costos de salida el cazador no tiene nada que minimizar.

**Prueba independiente**: con una cripta cuyas salidas declaran costos distintos, mover al jugador por cada una y comprobar el tiempo que tarda; una cripta sin costos declarados debe comportarse como hasta ahora.

**Escenarios de aceptación**:

1. **Dado** una salida sin costo declarado, **cuando** un actor la cruza, **entonces** su costo base es 100. *(FR-101, FR-102)*
2. **Dado** una salida de costo distinto de 100 (por ejemplo 250) y el jugador con velocidad 100, **cuando** el jugador la cruza, **entonces** la acción tarda lo que indica la fórmula de intervalo aplicada a ese costo (250). *(FR-103, FR-104)*
3. **Dado** un actor de velocidad alta y una salida de costo 1, **cuando** la cruza, **entonces** el intervalo es al menos 1. *(FR-104)*
4. **Dado** un actor atravesando una salida costosa, **cuando** cambia su velocidad, **entonces** el tiempo restante se reescala según la regla existente de cambio de velocidad. *(FR-105)*
5. **Dado** un errante o un rastreador, **cuando** se mueve por una salida de costo distinto de 100, **entonces** conserva su comportamiento de elección de destino y solo cambia cuánto tarda el movimiento. *(FR-106)*
6. **Dado** cualquier salida, **cuando** se cruza en un sentido o en el contrario, **entonces** el costo es el mismo. *(FR-102)*
7. **Dado** una conexión cuyas dos salidas declaran costos distintos, **cuando** se carga la cripta, **entonces** el costo en ambos sentidos es el de la salida de la sala de menor id y se emite una advertencia. *(FR-102)*
8. **Dado** una conexión en la que solo una salida declara costo, **cuando** se cruza en cualquiera de los dos sentidos, **entonces** se usa ese costo. *(FR-102)*
9. **Dado** una salida con costo inválido (cero, negativo o no entero), **cuando** se carga la cripta, **entonces** su costo es 100 y se emite una advertencia que indica la salida y el valor. *(FR-101)*
10. **Dado** cualquier actor, **cuando** ataca o espera, **entonces** el costo es el de siempre y no el de ninguna salida. *(FR-107)*
11. **Dado** un esqueleto de la Parte I sin ningún costo declarado, **cuando** se juega, **entonces** todas las salidas cuestan 100 y la partida es idéntica a la anterior. *(FR-118)*
12. **Dado** una caché o una partida guardada de una versión anterior, **cuando** se inicia el juego, **entonces** la caché se invalida por la validación de versión sin borrar archivos a mano y la partida guardada se rechaza con un mensaje que indica la versión encontrada y la esperada. *(FR-119)*

---

### Historia 2 — El cazador persigue por la ruta más barata (Prioridad: P1)

Un cazador en la cripta calcula el camino de menor costo hasta la sala del jugador y avanza un paso por él, siempre que el jugador esté dentro de su rango. Si comparte sala con el jugador, ataca.

**Por qué esta prioridad**: es el comportamiento central que justifica la capacidad.

**Prueba independiente**: colocar un cazador y al jugador en una cripta pequeña con rutas de costos conocidos y verificar paso a paso la decisión del cazador.

**Escenarios de aceptación**:

1. **Dado** un cazador en la misma sala que el jugador, **cuando** le toca actuar, **entonces** ataca con la regla de ataque existente y no se mueve. *(FR-110)*
2. **Dado** un cazador sin ninguna ruta abierta hacia la sala del jugador, **cuando** le toca actuar, **entonces** espera con costo 100. *(FR-112)*
3. **Dado** que el costo mínimo hasta el jugador es mayor que el rango del cazador, **cuando** le toca actuar, **entonces** espera con costo 100. *(FR-112)*
4. **Dado** una ruta de menos salas pero mayor costo y otra de más salas y menor costo, **cuando** el cazador actúa, **entonces** avanza por la de menor costo. *(FR-111, FR-113)*
5. **Dado** dos salas vecinas desde las que parte una ruta de costo mínimo, **cuando** el cazador actúa, **entonces** va a la de menor id. *(FR-114)*
6. **Dado** un cazador que se mueve, **cuando** cruza la salida elegida, **entonces** la acción cuesta lo que cuesta esa salida. *(FR-113)*
7. **Dado** un cazador con una puerta cerrada en su única ruta, **cuando** actúa, **entonces** no la abre y trata la ruta como inexistente. *(FR-115)*
8. **Dado** un cazador que ya inició el cruce de una salida abierta, **cuando** la puerta se cierra antes de terminar el tránsito, **entonces** el cruce se completa. *(FR-109)*
9. **Dado** un cazador con rango 0 declarado, **cuando** el jugador está en otra sala, **entonces** espera con costo 100; y **dado** una ficha sin rango o con rango negativo o no entero, **entonces** se trata como rango 0 y se emite una advertencia. *(FR-108, FR-112)*
10. **Dado** una conexión de un solo sentido, **cuando** el cazador necesita cruzarla en el sentido contrario al que existe, **entonces** no hay ruta por ahí y la trata como inexistente. *(FR-124)*

---

### Historia 3 — La decisión del cazador es siempre la de calcular desde cero (Prioridad: P1)

Quien revisa puede verificar que, ocurra lo que ocurra entre dos turnos de un cazador (puertas que cambian, el jugador que se mueve, otros actores que mueren), su decisión es la misma que se obtendría analizando la cripta en ese instante, sin arrastrar información vieja.

**Por qué esta prioridad**: sin esta garantía el cazador sería impredecible y las partidas no serían reproducibles.

**Prueba independiente**: comparar, turno a turno, la decisión del cazador con la de un cálculo independiente hecho desde cero sobre el mismo estado, tras cada tipo de evento.

**Escenarios de aceptación**:

1. **Dado** una puerta de la ruta del cazador que se cierra entre dos de sus turnos, **cuando** le toca actuar, **entonces** decide como si calculara desde cero, con la puerta cerrada. *(FR-116)*
2. **Dado** una puerta cerrada que se abre entre dos turnos, **cuando** actúa, **entonces** puede aprovechar la ruta nueva. *(FR-116)*
3. **Dado** que el jugador cambió de sala entre dos turnos, **cuando** el cazador actúa, **entonces** persigue a la nueva posición. *(FR-116)*
4. **Dado** un cazador cuya decisión no depende del contenido descargado de las salas, **cuando** se comparan dos partidas, una con salas ya descargadas y otra sin descargar, **entonces** la decisión es idéntica. *(FR-117)*

---

### Historia 4 — Partidas deterministas y medibles (Prioridad: P2)

Quien revisa reproduce una partida con cazadores y obtiene siempre el mismo resultado, y mide con `--bench` que el costo de los cazadores es el esperado.

**Por qué esta prioridad**: es una garantía de calidad transversal; puede probarse una vez que las historias 1 a 3 existen.

**Prueba independiente**: ejecutar dos veces la misma cripta, semilla y acciones y comparar registros; ejecutar `--bench` y leer las secciones nuevas.

**Escenarios de aceptación**:

1. **Dado** la misma cripta, la misma semilla y las mismas acciones con cazadores, **cuando** se juega dos veces, **entonces** las dos partidas son idénticas. *(FR-120)*
2. **Dado** la cripta de referencia con decenas de cazadores activos, **cuando** se mide el ciclo de eventos entre dos decisiones del jugador, **entonces** toma menos de 20 ms. *(FR-121)*
3. **Dado** un cazador de rango pequeño en una cripta grande, **cuando** se mide, **entonces** su costo no crece con el tamaño de la cripta sino con la región dentro de su rango. *(FR-122)*
4. **Dado** `--bench`, **cuando** se ejecuta, **entonces** reporta un cazador frente a muchos, rango pequeño frente a grande, y puertas que cambian con frecuencia frente a estables. *(FR-123)*

---

### Historia 5 — Los costos y los cazadores se ven en pantalla (Prioridad: P2)

Quien juega ve el costo de cada salida de la sala actual y distingue a los cazadores de los demás enemigos.

**Por qué esta prioridad**: sin información el jugador no puede decidir qué rutas evitar.

**Prueba independiente**: mostrar una sala con salidas de costos distintos y un cazador junto a otro tipo de enemigo.

**Escenarios de aceptación**:

1. **Dado** la sala actual con varias salidas, **cuando** se muestra, **entonces** cada salida aparece con su costo. *(FR-130)*
2. **Dado** una sala con un cazador y otro enemigo, **cuando** se muestra, **entonces** el cazador se distingue del otro. *(FR-131)*

---

### Casos límite

- Salida sin costo declarado: vale 100 (FR-101).
- Cazador en la misma sala que el jugador: ataca en lugar de calcular ruta (FR-110).
- Varias rutas de igual costo mínimo, incluso muchas: siempre gana la vecina de menor id (FR-114).
- Jugador inalcanzable por puertas cerradas: el cazador espera (FR-112).
- Costo de salida igual a 1 con velocidad muy alta: el intervalo nunca baja de 1 (FR-104).
- Una puerta se cierra mientras un actor ya está cruzando esa salida: el cruce en curso se completa; la puerta se evalúa solo al iniciar el movimiento (FR-109).
- Una salida declara un costo inválido (cero, negativo o no entero): se usa 100 para esa salida y se emite una advertencia que indica la salida y el valor (FR-101).
- Una ficha de cazador sin rango o con rango no válido (negativo o no entero): se trata como rango 0 y se emite una advertencia; un rango 0 declarado es válido y deja al cazador atacando solo en su sala (FR-108).

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Costo de salidas**

- **FR-101**: Cada salida PUEDE declarar un costo, entero mayor o igual que 1; si no lo declara, su costo es 100. Si declara un costo inválido (cero, negativo o no entero), DEBE usarse 100 para esa salida y DEBE emitirse una advertencia que indique la salida y el valor.
- **FR-102**: El costo de una salida DEBE ser el mismo en ambos sentidos de tránsito. Si las dos salidas de una misma conexión declaran costos distintos, DEBE valer el declarado por la sala de menor id y DEBE emitirse una advertencia; si solo una de las dos declara costo, ese vale para ambos sentidos.
- **FR-103**: El costo base de moverse por una salida DEBE ser el costo de esa salida, y esto DEBE aplicar a todos los actores (jugador y enemigos), en lugar del 100 fijo anterior.
- **FR-104**: El intervalo de un movimiento DEBE seguir calculándose con la fórmula existente `max(1, costo*100 // velocidad)`, usando como costo el de la salida; el intervalo NUNCA DEBE ser menor que 1.
- **FR-105**: Si cambia la velocidad de un actor que está atravesando una salida, el tiempo restante DEBE reescalarse según la regla existente de cambio de velocidad.
- **FR-106**: Los enemigos errante y rastreador DEBEN conservar su comportamiento de elección de destino; solo DEBE cambiar cuánto tarda su movimiento.
- **FR-107**: El costo de atacar, esperar y las demás acciones que no son moverse NO DEBE cambiar.

**Enemigo cazador**

- **FR-108**: Una ficha de catálogo con `"comportamiento": "cazador"` DEBE definir un enemigo cazador con un `"rango"` entero expresado en unidades de costo. Un rango 0 declarado es válido (el cazador solo ataca en su sala); un rango ausente o inválido (negativo o no entero) DEBE tratarse como 0 y DEBE emitirse una advertencia.
- **FR-109**: El estado de una puerta DEBE evaluarse solo al iniciar un movimiento; si la salida estaba abierta en ese instante, el cruce en curso DEBE completarse aunque la puerta se cierre durante el tránsito.
- **FR-110**: En su turno, si el cazador comparte sala con el jugador, DEBE atacar según la regla de ataque existente.
- **FR-111**: Si no comparte sala con el jugador, el cazador DEBE calcular el costo mínimo d de llegar desde su sala hasta la sala actual del jugador, sumando el costo de cada salida recorrida y usando solo salidas abiertas en ese instante.
- **FR-112**: Si no existe ruta, o si d es mayor que el rango, el cazador DEBE esperar con costo 100.
- **FR-113**: Si existe ruta con d dentro del rango, el cazador DEBE moverse un paso por una ruta de costo d, y el costo de esa acción DEBE ser el costo de la salida que atraviesa.
- **FR-114**: Para elegir el paso, sea u la sala del cazador: entre las salas vecinas v con costo(u,v) + dist(v, jugador) = d, el cazador DEBE ir a la de menor id. Esto DEBE cumplirse siempre, incluso con muchas rutas de igual costo.
- **FR-115**: El cazador NO DEBE abrir puertas cerradas.
- **FR-124**: Una conexión PUEDE existir en un solo sentido (una sala con salida hacia otra que no tiene salida de vuelta); en ese caso solo se puede transitar en el sentido en que existe y está abierta.
- **FR-116**: La decisión del cazador en cada turno DEBE ser idéntica a la que se obtendría calculando la ruta desde cero en ese instante; las aperturas y cierres de puertas, el movimiento del jugador y la muerte de otros actores PUEDEN cambiar la respuesta de un turno a otro.
- **FR-117**: El cazador DEBE conocer el esqueleto completo de la cripta (con el costo de cada salida) y el estado actual de todas las puertas; NO le DEBE afectar la niebla de guerra del jugador, y su decisión NUNCA DEBE depender de si el contenido de una sala ya fue descargado.

**Datos y compatibilidad**

- **FR-118**: El esqueleto DEBE admitir el campo opcional `"costo"` en cada salida (ausente = 100) y el catálogo DEBE admitir fichas con `"comportamiento": "cazador"` y `"rango"`.
- **FR-119**: Lo persistido de la Parte I DEBE invalidarse mediante la validación de versión ya existente, sin borrar archivos a mano.

**Determinismo**

- **FR-120**: Misma cripta, misma semilla y mismas acciones con cazadores DEBEN producir la misma partida.

**Rendimiento**

- **FR-121**: El ciclo de eventos entre dos decisiones del jugador, con decenas de cazadores activos y la cripta de referencia, DEBE tomar menos de 20 ms.
- **FR-122**: El costo de decisión de un cazador de rango pequeño NO DEBE crecer en proporción al tamaño de la cripta, sino con la región que queda dentro de su rango.
- **FR-123**: `--bench` DEBE poder medir: un cazador frente a muchos, rango pequeño frente a grande, y puertas que cambian con frecuencia frente a puertas estables.

**Interfaz**

- **FR-130**: La vista DEBE mostrar el costo de cada salida de la sala actual.
- **FR-131**: La vista DEBE distinguir a los cazadores de los demás enemigos.

### Entidades clave

- **Salida**: conexión entre dos salas, con estado de puerta y un costo de tránsito (por defecto 100) igual en ambos sentidos.
- **Cazador**: enemigo con comportamiento "cazador" y un rango en unidades de costo; conoce todo el esqueleto y el estado de las puertas.
- **Ruta de menor costo**: camino por salidas abiertas entre dos salas cuya suma de costos es mínima.
- **Rango**: umbral de costo de ruta más allá del cual el cazador no persigue.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: En 100 % de los escenarios de aceptación de las historias 1 a 3, el comportamiento observado coincide con el descrito.
- **SC-002**: Una cripta sin costos declarados produce partidas idénticas a las de antes de esta capacidad en el tiempo de movimiento.
- **SC-003**: Para cualquier estado y turno de un cazador, su decisión coincide en 100 % de los casos con la obtenida calculando desde cero.
- **SC-004**: Dos ejecuciones con la misma cripta, semilla y acciones producen registros idénticos.
- **SC-005**: El ciclo de eventos con decenas de cazadores toma menos de 20 ms en la cripta de referencia.
- **SC-006**: Con un rango pequeño, el tiempo de decisión de un cazador no aumenta de forma apreciable al agrandar la cripta.
- **SC-007**: Quien juega identifica en la pantalla el costo de cada salida y qué enemigos son cazadores sin consultar documentación.

## Supuestos

- Las puertas con llave y de cierre automático cuentan como cerradas mientras estén cerradas; el cazador no las abre.
- El estado de las puertas conocido por el cazador es el real en el instante de su turno.
- La vista afecta solo a la presentación; la lógica del juego no depende de ella.
- Las criptas existentes sin costos declarados siguen siendo válidas.
- La cripta de referencia y los umbrales de tiempo son los definidos en el reglamento del proyecto.
