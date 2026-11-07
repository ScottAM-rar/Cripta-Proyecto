# Especificación de capacidad: Contrato de datos v2 y ubicación de llaves

**Carpeta**: `009-contrato-datos-v2`

**Creada**: 2026-11-06

**Estado**: Borrador

**Entrada**: Capacidad de apoyo de la Parte II — consulta de ubicación de llaves, lectura solo local, medición de la precarga con cazadores y API falsa v2 de pruebas. Requisitos con prefijo FR-301 a FR-329 (la capacidad 003 continúa desde FR-330 y la 010 desde FR-360).

## Contexto y motivación

La verificación de resolubilidad (capacidad 003) necesita saber dónde está cada llave de la cripta y, si una llave la suelta un enemigo, qué enemigo es. Obtenerlo descargando el contenido de cada sala gastaría casi todo el presupuesto de solicitudes. El servicio publica para eso una consulta nueva, la **consulta de llaves**, que entrega en una sola respuesta la ubicación de todas las llaves de una cripta.

Además, los demás integrantes necesitan probar el juego sin red y sin gastar solicitudes, y la línea de tiempo (capacidad 004) necesita leer datos ya guardados sin tocar la red.

**Lo existente y vigente (no se re-especifica)**: costo de las salidas, comportamiento cazador con su rango y formato de partida 6 con esos campos (capacidad 001); el esqueleto completo de la cripta se descarga al iniciar; el presupuesto de solicitudes de cada cripta y el reporte final de solicitudes; la caché persistente que invalida lo guardado cuando cambia la versión de la cripta; el cliente real del servicio, el modo `--offline` y la API falsa de la Parte I.

**Fuera de alcance**: la verificación de resolubilidad en sí (003), el formato de partida v6 (010), niebla de guerra e «ir a» (002), línea de tiempo (004). Cambiar la regla de precarga: si la medición de esta capacidad indica que conviene, será una especificación aparte.

## Clarificaciones

### Sesión 2026-11-06

- Q: Si no se pueden obtener las llaves de una cripta, ¿qué hace el programa después del mensaje? → A: La partida continúa con aviso; `--verificar` y todo uso explícito de la verificación terminan con error claro.
- Q: ¿Cómo se comprueba que el enemigo que suelta una llave inicia en la sala indicada, si el esqueleto no trae enemigos? → A: Solo si el contenido de esa sala ya está guardado; si no hay contradicción visible, se acepta.
- Q: Si la consulta de llaves trae el mismo id de llave en dos salas distintas, ¿la respuesta es válida? → A: Válida; cada aparición es una ubicación distinta. Solo es inválida una entrada idéntica repetida (misma llave, sala y enemigo).

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Conocer la ubicación de las llaves con una sola solicitud (Prioridad: P1)

Al jugar una cripta, el juego obtiene del servicio, una sola vez, la lista de llaves de esa cripta: cada llave con su id y la sala donde está; si la suelta un enemigo, también qué enemigo es, y la sala indicada es donde ese enemigo inicia. Esa solicitud se descuenta del presupuesto y aparece en el reporte final.

**Por qué esta prioridad**: sin esta información la verificación de resolubilidad no puede hacerse sin descargar el contenido de todas las salas.

**Prueba independiente**: con la API falsa v2, iniciar una partida en una cripta sin datos guardados y comprobar la lista de llaves obtenida, el contador de solicitudes y el reporte final.

**Escenarios de aceptación**:

1. **Dado** una cripta sin datos de llaves guardados, **cuando** el juego obtiene las llaves, **entonces** hace exactamente una consulta de llaves, el contador de solicitudes sube en 1 y el reporte final de solicitudes la muestra. *(FR-301, FR-303, FR-304)*
2. **Dado** una cripta donde la llave `L` la suelta el enemigo `E`, que inicia en la sala 7, **cuando** el juego obtiene las llaves, **entonces** `L` aparece asociada a `E` y a la sala 7. *(FR-302)*
3. **Dado** una cripta donde la llave `M` está en el suelo de la sala 3, **cuando** el juego obtiene las llaves, **entonces** `M` aparece en la sala 3 sin enemigo asociado. *(FR-302)*
4. **Dado** una partida en curso que ya obtuvo las llaves, **cuando** se vuelve a necesitar la ubicación de las llaves en esa misma partida, **entonces** no se hace ninguna solicitud nueva. *(FR-301)*
5. **Dado** una cripta donde la llave `B` está en el suelo de la sala 3 y otra copia de `B` en la sala 9, **cuando** el juego obtiene las llaves, **entonces** `B` aparece con ambas ubicaciones y la respuesta es válida. *(FR-302, FR-311)*

---

### Historia 2 — Reutilizar las llaves guardadas mientras la versión coincida (Prioridad: P1)

La lista de llaves se guarda junto con los demás datos de la cripta. En una partida posterior con la misma versión de la cripta no se vuelve a consultar. Si la versión cambió, lo guardado se descarta por la validación de versión existente y se consulta de nuevo.

**Por qué esta prioridad**: el presupuesto es escaso; repetir la consulta en cada partida lo malgasta, y usar llaves de otra versión daría verificaciones falsas.

**Prueba independiente**: jugar dos partidas seguidas con la API falsa v2 y la misma versión; luego cambiar la versión publicada y jugar una tercera. Contar solicitudes en cada una.

**Escenarios de aceptación**:

1. **Dado** que una partida anterior guardó las llaves de la cripta con la versión `v1`, **cuando** se inicia otra partida y el servicio sigue publicando `v1`, **entonces** las llaves se leen de disco y no se hace consulta de llaves. *(FR-305, FR-306)*
2. **Dado** llaves guardadas con la versión `v1`, **cuando** se inicia una partida y el servicio publica `v2`, **entonces** lo guardado se invalida, se hace una nueva consulta de llaves y se guarda el resultado con `v2`. *(FR-306, FR-307)*
3. **Dado** datos de la cripta guardados por la Parte I (sin llaves), **cuando** se inicia una partida con esta capacidad, **entonces** el juego no falla, se consultan las llaves una vez y nadie tuvo que borrar archivos a mano. *(FR-307, FR-308)*

---

### Historia 3 — Fallos claros del servicio y del modo sin red (Prioridad: P1)

Si el servicio no responde, si la respuesta de la consulta de llaves es inválida o si en `--offline` no hay llaves guardadas, el programa lo dice con un mensaje claro que identifica el problema y la cripta.

**Por qué esta prioridad**: un fallo silencioso haría que la verificación de resolubilidad diera un resultado equivocado sin aviso.

**Prueba independiente**: con la API falsa v2 configurada para no responder, para responder datos inválidos, y con `--offline` sobre una caché sin llaves.

**Escenarios de aceptación**:

1. **Dado** que el servicio no responde a la consulta de llaves, **cuando** el juego la intenta, **entonces** muestra un mensaje claro que indica que no pudo obtener las llaves de esa cripta, y no guarda nada. *(FR-309, FR-310)*
2. **Dado** una respuesta de llaves inválida (por ejemplo, una llave sin sala, una sala que no existe en el esqueleto, o un enemigo ausente del contenido ya guardado de la sala indicada), **cuando** el juego la recibe, **entonces** la rechaza completa con un mensaje claro y no la guarda. *(FR-309, FR-310, FR-311)*
3. **Dado** el modo `--offline` y una cripta guardada sin llaves, **cuando** se inicia la partida, **entonces** el juego muestra un mensaje claro de que faltan las llaves de esa cripta, no hace solicitudes y la partida continúa con aviso; si se pidió `--verificar`, termina con un error claro. *(FR-312, FR-313)*
4. **Dado** el modo `--offline` y una cripta guardada con llaves, **cuando** se inicia la partida, **entonces** las llaves se leen de disco y el contador de solicitudes queda en 0. *(FR-312)*

---

### Historia 4 — Leer solo de disco, sin gastar solicitudes (Prioridad: P2)

Existe una forma de pedir datos de la cripta (esqueleto, contenido de salas, llaves) que solo lee lo guardado en disco. Si falta un dato, falla con un mensaje claro que dice qué dato y de qué cripta falta, y nunca hace una solicitud. La usa la consulta histórica de la capacidad 004.

**Por qué esta prioridad**: es requisito de la línea de tiempo, que se especifica después.

**Prueba independiente**: con una caché a la que le falta el contenido de una sala, pedir ese contenido por la vía solo local y comprobar el mensaje y que el contador de solicitudes no cambia.

**Escenarios de aceptación**:

1. **Dado** una caché sin el contenido de la sala 5, **cuando** se pide ese contenido por la vía solo local, **entonces** falla con un mensaje claro que nombra la sala 5 y la cripta, y el contador de solicitudes no cambia. *(FR-314, FR-315)*
2. **Dado** una caché completa y vigente, **cuando** se piden datos por la vía solo local, **entonces** se obtienen los mismos datos que daría la vía normal, sin solicitudes. *(FR-314, FR-316)*
3. **Dado** una caché guardada con una versión distinta de la que se indica como vigente, **cuando** se piden datos por la vía solo local, **entonces** se trata como dato faltante, con mensaje claro. *(FR-315, FR-317)*

---

### Historia 5 — Probar sin red con la API falsa v2 (Prioridad: P2)

Los integrantes cuentan con una API falsa v2 de pruebas: publica criptas con costos en las salidas, al menos un cazador, la consulta de llaves y los casos del Apéndice B. Es determinista y no usa red.

**Por qué esta prioridad**: todas las pruebas de esta capacidad y de 003, 004 y 010 dependen de ella. Es infraestructura de pruebas, no comportamiento del juego.

**Prueba independiente**: ejecutar dos veces la misma secuencia de solicitudes contra la API falsa v2 y comparar las respuestas; comprobar que no se abre ninguna conexión de red.

**Escenarios de aceptación**:

1. **Dado** la API falsa v2, **cuando** se piden dos veces los mismos datos, **entonces** las respuestas son idénticas. *(FR-318)*
2. **Dado** la API falsa v2, **cuando** se juega una cripta suya, **entonces** hay salidas con costos distintos de 100, al menos un cazador y una consulta de llaves con al menos una llave en el suelo y una que suelta un enemigo. *(FR-319)*
3. **Dado** la API falsa v2, **cuando** se ejecutan los casos del Apéndice B, **entonces** cada caso está disponible como cripta o situación reproducible. *(FR-320)*
4. **Dado** la API falsa v2, **cuando** se la configura para fallar o para responder datos inválidos, **entonces** produce ese fallo de forma repetible. *(FR-321)*
5. **Dado** el cliente real, `--offline` y la API falsa v2, **cuando** se obtienen las llaves de una misma cripta guardada, **entonces** las tres fuentes entregan la misma lista. *(FR-303)*

---

### Historia 6 — Medir el costo de red de los cazadores y la regla de precarga (Prioridad: P3)

Se mide cuántas solicitudes extra provoca un cazador que cruza salas cuyo contenido aún no se descargó, y si conviene que la precarga elija salas por el costo de las salidas en lugar de por el número de saltos. El resultado se documenta.

**Por qué esta prioridad**: no cambia el juego; informa una decisión futura.

**Prueba independiente**: ejecutar la medición sobre criptas sintéticas deterministas y revisar el documento de resultados.

**Escenarios de aceptación**:

1. **Dado** criptas sintéticas con cazadores, **cuando** se ejecuta la medición, **entonces** se reporta el número de solicitudes extra con precarga por saltos y con precarga por costo, para las mismas criptas y semillas. *(FR-322, FR-323)*
2. **Dado** la medición terminada, **cuando** se revisa la documentación, **entonces** consta el resultado y la recomendación (mantener o cambiar la precarga), sin que la regla de precarga haya cambiado. *(FR-324)*

---

### Casos límite

- La cripta no tiene ninguna llave: la respuesta vacía es válida, se guarda y no se vuelve a consultar con la misma versión.
- El presupuesto de solicitudes ya está agotado cuando hay que consultar las llaves: se trata como fallo del servicio (FR-309), sin exceder el presupuesto.
- El mismo id de llave aparece en salas distintas o con enemigos distintos: válido; son ubicaciones distintas de la misma llave y todas se conservan (FR-302).
- Una entrada aparece dos veces idéntica (misma llave, sala y enemigo): la respuesta es inválida (FR-311).
- Un enemigo suelta más de una llave: válido; cada llave aparece por separado con el mismo enemigo y la misma sala.
- La llave de salida de la cripta figura en la lista como cualquier otra llave.
- La versión de la cripta cambia durante una partida: no se vuelve a consultar en esa partida; la invalidación ocurre al iniciar la siguiente.
- Llave soltada por un enemigo en una sala cuyo contenido aún no se descargó: se acepta; la comprobación del enemigo se omite sin solicitudes (FR-311).
- Fallo a medio guardar: lo guardado a medias no debe tomarse como válido en la partida siguiente.

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Consulta de llaves**

- **FR-301**: El juego DEBE obtener la ubicación de las llaves de una cripta mediante la consulta de llaves del servicio, como máximo una vez por cripta mientras la versión no cambie, y no repetirla dentro de una misma partida.
- **FR-302**: Una misma llave (mismo id) PUEDE tener varias ubicaciones; el juego DEBE conservarlas todas. Cada ubicación DEBE tener su id y una sala. Si la llave la suelta un enemigo, DEBE indicar además la instancia del enemigo, y la sala DEBE ser la sala donde ese enemigo inicia. Si no hay enemigo, la sala es donde la llave está.
- **FR-303**: La consulta de llaves DEBE funcionar igual con el cliente real, con `--offline` (leyendo lo guardado) y con la API falsa v2, y las tres DEBEN entregar la misma lista para los mismos datos.
- **FR-304**: La consulta de llaves DEBE contar como una solicitud dentro del presupuesto de solicitudes de la cripta y DEBE aparecer en el reporte final de solicitudes.

**Guardado y versión**

- **FR-305**: La lista de llaves DEBE guardarse junto con los demás datos de la cripta, asociada a la versión de la cripta.
- **FR-306**: Al iniciar una partida, si hay llaves guardadas y la versión guardada coincide con la publicada, el juego DEBE usar las guardadas sin consultar.
- **FR-307**: Si la versión guardada no coincide, lo guardado DEBE invalidarse mediante la validación de versión existente y las llaves DEBEN consultarse de nuevo.
- **FR-308**: Los datos guardados por la Parte I (sin llaves) DEBEN tratarse como datos incompletos o de otra versión mediante la validación existente; NO DEBE requerirse borrar archivos a mano.

**Fallos**

- **FR-309**: Si el servicio no responde a la consulta de llaves, o no queda presupuesto para hacerla, el juego DEBE mostrar un mensaje claro que indique que no se pudieron obtener las llaves y de qué cripta.
- **FR-310**: Una respuesta fallida o inválida NO DEBE guardarse ni usarse parcialmente.
- **FR-311**: Una respuesta de llaves DEBE considerarse inválida si alguna llave no tiene id o sala, si una entrada se repite idéntica (misma llave, misma sala y mismo enemigo o ausencia de enemigo), o si la sala no existe en el esqueleto. Además, si el contenido de la sala indicada para una llave soltada por un enemigo ya está guardado y ese enemigo no figura en él, la respuesta DEBE considerarse inválida; si el contenido no está guardado, la asociación se acepta sin hacer solicitudes.
- **FR-312**: En `--offline`, las llaves DEBEN leerse solo de lo guardado; si faltan, el juego DEBE mostrar un mensaje claro y no hacer solicitudes.
- **FR-313**: Ante cualquier fallo de FR-309 a FR-312, la partida DEBE poder jugarse: el juego DEBE avisar que la verificación de resolubilidad no está disponible para esa cripta. Si se pidió `--verificar` o cualquier uso explícito de la verificación, el programa DEBE terminar con un error claro que nombre la cripta, sin dar un resultado de verificación.

**Lectura solo local**

- **FR-314**: DEBE existir una forma de pedir datos de la cripta (esqueleto, contenido de salas y llaves) que lea solo de disco y nunca haga solicitudes.
- **FR-315**: Si por esa vía falta un dato, DEBE fallar con un mensaje claro que nombre el dato faltante y la cripta, sin solicitudes y sin modificar lo guardado.
- **FR-316**: Para datos presentes y vigentes, la vía solo local DEBE entregar lo mismo que la vía normal.
- **FR-317**: Por la vía solo local, un dato guardado con una versión distinta de la vigente DEBE tratarse como faltante.

**API falsa v2 (infraestructura de pruebas)**

- **FR-318**: La API falsa v2 DEBE ser determinista (mismas solicitudes, mismas respuestas) y NO DEBE usar red.
- **FR-319**: La API falsa v2 DEBE publicar criptas con costos en las salidas, al menos un cazador con rango y la consulta de llaves, con al menos una llave en el suelo y una que suelta un enemigo.
- **FR-320**: La API falsa v2 DEBE ofrecer cada caso del Apéndice B como situación reproducible.
- **FR-321**: La API falsa v2 DEBE poder configurarse para no responder o responder datos inválidos en la consulta de llaves, de forma repetible.

**Medición**

- **FR-322**: DEBE medirse, sobre criptas sintéticas deterministas por semilla, cuántas solicitudes extra provoca un cazador que cruza salas cuyo contenido no se descargó.
- **FR-323**: La medición DEBE comparar la precarga actual (por número de saltos) con una precarga por costo de las salidas, en las mismas criptas y semillas.
- **FR-324**: El resultado y la recomendación DEBEN documentarse. Esta capacidad NO DEBE cambiar la regla de precarga.

### Entidades clave

- **Ubicación de llave**: id de la llave, sala, y opcionalmente la instancia del enemigo que la suelta (en cuyo caso la sala es la inicial de ese enemigo).
- **Lista de llaves de una cripta**: todas las ubicaciones de llave de una cripta, asociada a la versión de la cripta con la que se obtuvo.
- **Fuente de datos**: de dónde obtiene el juego los datos de una cripta: el servicio real, lo guardado (`--offline` o solo local) o la API falsa v2.
- **Informe de medición**: solicitudes extra por cazador con cada regla de precarga, criptas y semillas usadas, recomendación.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: En una partida con datos sin guardar, la consulta de llaves suma exactamente 1 solicitud; en una partida posterior con la misma versión, suma 0.
- **SC-002**: En `--offline`, ninguna partida ni consulta de llaves hace solicitudes (contador en 0 en el 100 % de las pruebas).
- **SC-003**: Por la vía solo local, el contador de solicitudes no cambia en el 100 % de las pruebas, incluidas las de dato faltante.
- **SC-004**: El 100 % de los fallos de servicio, respuesta inválida y dato faltante producen un mensaje que nombra la cripta y el problema; ninguno termina en un error sin explicar.
- **SC-005**: Ninguna partida supera el presupuesto de solicitudes de su cripta por causa de la consulta de llaves.
- **SC-006**: Cualquier integrante puede ejecutar la suite completa de esta capacidad sin red, y dos ejecuciones dan los mismos resultados.
- **SC-007**: La medición documenta, para al menos tres tamaños de cripta sintética, las solicitudes extra con cada regla de precarga.

## Supuestos

- La consulta de llaves del servicio responde con todas las llaves de la cripta en una sola respuesta, sin paginación.
- La versión de la cripta que valida la lista de llaves es la misma que ya valida el resto de los datos guardados.
- La consulta de llaves se hace al iniciar la partida, junto con la descarga del esqueleto, para que la información esté disponible antes de cualquier verificación.
- Si no queda presupuesto para la consulta de llaves, se trata igual que un servicio que no responde.
- La validación de la respuesta (FR-311) usa el esqueleto y, si ya está guardado, el contenido de las salas indicadas; nunca hace solicitudes adicionales.
- La medición de la precarga usa las criptas sintéticas deterministas ya existentes en el proyecto, ampliadas con cazadores si hace falta.
- La API falsa v2 sustituye a la de la Parte I en las pruebas nuevas; las pruebas de la Parte I pueden seguir usando la suya.
