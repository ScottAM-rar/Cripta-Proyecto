# Especificación de capacidad: Recorrido por niveles de la cripta

**Carpeta**: `005-recorrido-por-niveles`

**Creada**: 2026-10-27

**Estado**: Borrador

**Entrada**: Capacidad transversal de la Parte II: visitar las salas de la cripta en orden de cercanía a partir de una sala. Requisitos con prefijo FR-5xx.

## Contexto y motivación

Varias funciones del juego necesitan visitar las salas de la cripta en orden de cercanía a partir de una sala: la precarga de salas vecinas y la verificación de resolubilidad. Hoy cada una lo resuelve a su manera. Esta capacidad define **una sola regla de recorrido**, para que quien revisa pueda predecir exactamente en qué orden se visitan las salas y comprobar que dos ejecuciones dan lo mismo.

**Qué es un nivel**: la cantidad de salidas que hay que recorrer para llegar a una sala desde el origen por el camino más corto. El origen está en el nivel 0, sus vecinas directas en el nivel 1, y así sucesivamente.

**Lo existente y vigente (no se re-especifica)**: la cripta es un conjunto de salas conectadas por salidas; cada salida lleva de una sala a otra; una conexión puede existir en un solo sentido; el esqueleto completo se descarga al iniciar.

**Fuera de alcance**: costos de las salidas y cazador (capacidad 001), puertas y llaves, mapa conocido del jugador, verificación de resolubilidad. Esta capacidad entrega el recorrido; no decide qué hacer con las salas visitadas.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Recorrer la cripta en orden de cercanía (Prioridad: P1)

Quien revisa pide el recorrido desde una sala y obtiene la secuencia de salas alcanzables ordenada por nivel, con un desempate fijo dentro de cada nivel, sin repeticiones y sin salas inalcanzables.

**Por qué esta prioridad**: es el servicio que necesitan las otras funciones; sin un orden único y predecible cada una sigue resolviéndolo a su manera.

**Prueba independiente**: sobre criptas pequeñas armadas a mano (línea, ciclo, caminos paralelos, conexión de un solo sentido), comparar la secuencia obtenida con la esperada escrita a mano.

**Escenarios de aceptación**:

1. **Dado** una cripta en línea de 5 salas, **cuando** se recorre desde un extremo, **entonces** se visitan en orden de cercanía, empezando por el origen. *(FR-501)*
2. **Dado** una sala con dos vecinas al mismo nivel, **cuando** se recorre, **entonces** se respeta el desempate definido para ese nivel. *(FR-502)*
3. **Dado** un ciclo entre salas, **cuando** se recorre, **entonces** ninguna sala se repite. *(FR-503)*
4. **Dado** dos caminos hacia la misma sala, **cuando** se recorre, **entonces** se visita una sola vez, en el nivel del camino más corto. *(FR-503)*
5. **Dado** un origen sin salidas, **cuando** se recorre, **entonces** el recorrido contiene solo el origen. *(FR-505, FR-508)*
6. **Dado** salas sin ningún camino desde el origen, **cuando** se recorre, **entonces** no aparecen en el recorrido. *(FR-505)*
7. **Dado** una salida de un solo sentido, **cuando** se recorre, **entonces** no se recorre al revés. *(FR-506)*

---

### Historia 2 — Limitar hasta dónde se recorre (Prioridad: P1)

Quien pide el recorrido indica cuántos niveles le interesan y las salas más lejanas no se visitan.

**Por qué esta prioridad**: la precarga de vecinas solo necesita las salas cercanas; recorrer toda la cripta sería un desperdicio.

**Prueba independiente**: recorrer una línea larga con límites distintos y comprobar dónde se corta.

**Escenarios de aceptación**:

1. **Dado** un límite de 2 niveles, **cuando** se recorre, **entonces** no aparecen las salas a 3 saltos o más. *(FR-504)*
2. **Dado** un límite de 0 niveles, **cuando** se recorre, **entonces** el recorrido contiene solo el origen. *(FR-504)*
3. **Dado** un límite mayor que la distancia a la sala más lejana, **cuando** se recorre, **entonces** el resultado es el mismo que sin límite. *(FR-504)*

---

### Historia 3 — Resultados repetibles y de costo proporcional (Prioridad: P2)

Quien revisa comprueba que dos ejecuciones iguales dan la misma secuencia y que el costo depende de lo visitado, no del tamaño de la cripta.

**Por qué esta prioridad**: es una garantía de calidad transversal; puede comprobarse una vez que existe el recorrido.

**Prueba independiente**: repetir el mismo recorrido y comparar; medir con `--bench` el mismo recorrido acotado en criptas de distinto tamaño.

**Escenarios de aceptación**:

1. **Dado** la misma cripta y el mismo origen, **cuando** se recorre dos veces, **entonces** la secuencia de salas es exactamente la misma. *(FR-509)*
2. **Dado** un recorrido de pocos niveles, **cuando** la cripta crece cien veces sin cambiar la zona alrededor del origen, **entonces** el costo no crece en esa proporción (SC-004). *(FR-510)*
3. **Dado** `--bench`, **cuando** se ejecuta, **entonces** informa el recorrido sobre criptas sintéticas deterministas por semilla. *(FR-511)*

---

### Casos límite

- Origen que no existe en la cripta: se rechaza con un error claro y no se devuelve un recorrido vacío (FR-512).
- Límite de niveles negativo o no entero: se rechaza con un error claro (FR-504).
- Una sala que tiene dos salidas hacia la misma sala: se visita una sola vez (FR-503).
- Una salida que lleva de una sala a sí misma: no repite la sala (FR-503).
- Origen dentro de un ciclo: el origen aparece una sola vez, al principio (FR-501, FR-503).
- Dentro de un mismo nivel, el orden es: [NEEDS CLARIFICATION: ¿se desempata por menor id de sala, o por el orden de las direcciones N, S, E, O de la sala desde la que se llegó?]
- Qué salidas cuentan como transitables: [NEEDS CLARIFICATION: ¿se recorren todas las salidas existentes, o solo las que quien pide el recorrido declara transitables?]

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Orden y alcance**

- **FR-501**: Dada una sala de origen, el recorrido DEBE visitar las salas alcanzables por salidas en orden creciente de nivel (cantidad de salidas recorridas por el camino más corto desde el origen). El origen es el primero y está en el nivel 0.
- **FR-502**: Dentro de un mismo nivel, el orden DEBE ser determinista y definido por una regla escrita: [NEEDS CLARIFICATION: menor id de sala u orden de las direcciones N, S, E, O].
- **FR-503**: Cada sala DEBE visitarse una sola vez, en el nivel de su camino más corto, aunque existan varios caminos, ciclos, salidas repetidas hacia la misma sala o salidas hacia sí misma.
- **FR-504**: Quien pide el recorrido PUEDE indicar un límite de niveles, entero mayor o igual que 0. Las salas con nivel mayor que el límite NO DEBEN visitarse. Un límite negativo o no entero DEBE rechazarse con un error claro. Sin límite, se recorre todo lo alcanzable.
- **FR-505**: Las salas sin camino desde el origen NO DEBEN aparecer en el recorrido.
- **FR-506**: Una salida de un solo sentido DEBE recorrerse solo en el sentido en que existe.
- **FR-507**: Las salidas transitables son: [NEEDS CLARIFICATION: todas las salidas existentes, o solo las que quien pide el recorrido declara transitables].
- **FR-508**: Si el origen no tiene salidas transitables, el recorrido DEBE contener solo el origen.
- **FR-512**: Un origen que no existe en la cripta DEBE rechazarse con un error claro.

**Determinismo**

- **FR-509**: Dos recorridos con la misma cripta, el mismo origen, el mismo límite y la misma regla de transitabilidad DEBEN producir exactamente la misma secuencia de salas. El resultado NO DEBE depender del orden en que se descargó el contenido de las salas ni de la hora.

**Rendimiento**

- **FR-510**: El costo de un recorrido DEBE ser proporcional a las salas y salidas efectivamente visitadas, no al tamaño total de la cripta.
- **FR-511**: El recorrido DEBE poder medirse con `--bench` sobre criptas sintéticas deterministas por semilla, incluyendo una comparación entre un recorrido acotado y uno sin límite al crecer la cripta.

### Entidades clave

- **Sala**: nodo de la cripta, identificada por un id. Tiene salidas hacia otras salas.
- **Salida**: conexión de una sala a otra. Puede no tener su inversa (conexión de un solo sentido).
- **Nivel**: cantidad de salidas del camino más corto entre el origen y una sala. El origen está en el nivel 0.
- **Recorrido**: secuencia de salas visitadas, cada una con su nivel, ordenada por nivel y con el desempate fijado en FR-502.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: En 100 % de los escenarios de aceptación, la secuencia obtenida coincide con la esperada.
- **SC-002**: Repetir 100 veces el mismo recorrido sobre la misma cripta produce la misma secuencia en las 100.
- **SC-003**: Ninguna sala aparece dos veces en ningún recorrido de las pruebas, incluidas criptas con ciclos y caminos paralelos.
- **SC-004**: Un recorrido de 2 niveles toma casi el mismo tiempo en una cripta de 400 salas que en una de 40 000 (a lo sumo el doble), siempre que la zona alrededor del origen sea igual.
- **SC-005**: Quien revisa puede escribir a mano el recorrido esperado de una cripta pequeña a partir de las reglas de esta especificación, sin consultar el programa, y coincide con el resultado.

## Supuestos

- El nivel se mide en cantidad de salidas recorridas. Los costos de las salidas (capacidad 001) no afectan al recorrido por niveles.
- Los ids de sala son números enteros y se pueden comparar entre sí.
- El esqueleto de la cripta está completo al iniciar, así que el recorrido no necesita pedir nada a la red.
- Un origen inexistente y un límite inválido son errores de quien invoca el recorrido y se informan, no se corrigen en silencio.
- El límite 0 es válido y deja solo el origen.
