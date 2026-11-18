# Especificación de capacidad: Revisión de la Parte I con la carga nueva

**Carpeta**: `012-revision-parte-i`

**Creada**: 2026-11-17

**Estado**: Borrador

**Entrada**: Revisión de la Parte I con la carga nueva (§5.6 del enunciado): red, caché, guardado y planeación de la vecindad. Requisitos con prefijo FR-370 en adelante (comprobado con búsqueda: los FR-3xx existentes llegan a FR-346 en la 003 y FR-360 en la 010; FR-370 a FR-399 están libres).

## Contexto y motivación

El enunciado (§5.6) pide repetir las mediciones de la Parte I con la carga de la Parte II (cazadores, costos de salida, llaves y partida de formato 8) y documentar el antes y el después de cada medición. Además, §6.2 y el principio I de la constitución prohíben usar colas, mapas y conjuntos de biblioteca en el código evaluado.

Hoy la planeación de la vecindad (qué salas rodean a una sala hasta cierta profundidad) usa una cola de biblioteca, y ninguna especificación cubre la revisión de red, caché y guardado con la carga nueva. La 009 ya repitió el bloque de caché tras agregar las llaves, pero lo midió con un cliente que no pide llaves y sin cazadores, así que no basta como revisión de §5.6.

**Ya especificado, no se repite aquí**: el contrato v2, las llaves y el presupuesto (009), la verificación de resolubilidad (003), los costos de salida y el cazador (001), el rechazo de partidas de versión anterior y la lectura de una sala individual del archivo (FR-425 de la 004 y las pruebas de formato existentes). La regla de precarga **no cambia** (FR-324).

## Clarificaciones

### Sesión 2026-11-17

- P: ¿Cómo entra la carga nueva en las mediciones? → R: En las mismas filas de los bloques, con la carga puesta. No se agregan filas aparte (FR-378).
- P: ¿Cuáles son los límites actuales de guardar y cargar? → R: El doble del valor de cada fila en el antes, como en red (FR-384).
- P: ¿Se corrigen hoy todos los usos prohibidos que quedan en el código de producción, o solo algunos? → R: Se corrigen solo los del código que resuelve un problema evaluado en §5: la caché de fichas y la planeación de la vecindad. Se justifican por escrito el contenedor de salidas de cada sala, su conversión desde la respuesta de la API y su reconstrucción al cargar la partida, porque solo guardan hasta 4 salidas que se recorren en orden y no son un índice (FR-385, FR-386).
- P: ¿Qué se cuenta como «lectura del esqueleto»? → R: Las dos cosas. Las búsquedas de una sala dentro del esqueleto en memoria deben dar el mismo número que hoy: 1 para validar la sala de partida más 1 por cada sala explorada con nivel menor que la profundidad. Las descargas del esqueleto desde la fuente de datos no deben aumentar: 0 después de la primera por cripta. Ambas se cuentan con espías y se comparan con la versión vigente (FR-374).
- P: ¿En qué documento van los veredictos, las tablas de antes y después y las justificaciones del inventario? → R: El detalle va en una sección «012» de `DECISIONES.md`. Además, cada decisión revisada en `DOCUMENTACION_DECISIONES_DISENO.md` lleva una nota breve con su veredicto y un enlace a esa sección (FR-380, FR-386, FR-388).
- P: ¿Con qué cripta se genera la partida de formato 8 para medir la lectura de una sala individual? → R: Con una cripta sintética determinista por semilla, del tamaño de la cripta de referencia (§6.1), dentro del bloque de guardado. Además, se hace una medición manual documentada con la cripta publicada más grande que esté descargada, que no entra al bloque (FR-382).

## Escenarios de usuario y pruebas *(obligatorio)*

Convenciones de las criptas de los escenarios (las salidas se recorren en el orden N, E, S, O):

- **Lineal**: salas 1 a 6 en fila; cada sala tiene salida E a la siguiente y O a la anterior.
- **Rejilla**: 3 × 3, salas 1 a 9 por filas (1 2 3 / 4 5 6 / 7 8 9); N sube una fila, S baja, E y O se mueven en la fila.
- **Árbol**: la sala 1 tiene S→2 y E→3; la 2 tiene S→4 y O→5; la 3 tiene E→6; cada hija tiene la salida de vuelta a su madre.
- **Con ciclos**: 2 × 2, salas 1 2 / 3 4, todas las salidas en ambos sentidos.

### Historia 1 · La vecindad se planea igual que hoy (Prioridad: P1)

El juego pregunta qué salas rodean a la sala del jugador hasta cierta profundidad para decidir qué precargar. Tras la revisión, la respuesta tiene que ser exactamente la de hoy: mismas salas, mismo orden, mismos errores y misma cantidad de lecturas del esqueleto de la cripta.

**Por qué esta prioridad**: la precarga, la caché y las cuentas de solicitudes dependen de esta respuesta. Si cambia aunque sea el orden, cambian las salas que se traen y todas las mediciones de red dejan de ser comparables.

**Prueba independiente**: con las cuatro criptas de arriba y las profundidades 0, 1, 2 y 5, se compara la respuesta revisada con la que da la versión vigente antes del cambio (salas, orden, errores y lecturas del esqueleto).

**Escenarios de aceptación**:

1. **Dado** cualquiera de las cuatro criptas y una sala que existe, **cuando** se pide su vecindad con profundidad 0, **entonces** la respuesta es vacía y solo se lee el esqueleto para comprobar que la sala existe. *(FR-370, FR-372, FR-374)*
2. **Dado** la cripta lineal, **cuando** se pide la vecindad de la sala 3, **entonces** con profundidad 1 es [4, 2]; con 2, [4, 2, 5, 1]; con 5, [4, 2, 5, 1, 6]. *(FR-370, FR-371)*
3. **Dado** la cripta lineal, **cuando** se pide la vecindad de la sala 1 con profundidad 5, **entonces** es [2, 3, 4, 5, 6] y no incluye la sala 1. *(FR-370, FR-371)*
4. **Dado** la rejilla, **cuando** se pide la vecindad de la sala 5, **entonces** con profundidad 1 es [2, 6, 8, 4]; con 2 y con 5, [2, 6, 8, 4, 3, 1, 9, 7]. *(FR-370, FR-371)*
5. **Dado** la rejilla, **cuando** se pide la vecindad de la sala 1 con profundidad 2, **entonces** es [2, 4, 3, 5, 7], sin la sala 1 aunque varias salidas vuelvan a ella. *(FR-370, FR-371)*
6. **Dado** el árbol, **cuando** se pide la vecindad de la sala 1, **entonces** con profundidad 1 es [3, 2]; con 2 y con 5, [3, 2, 6, 4, 5]. *(FR-370, FR-371)*
7. **Dado** el árbol, **cuando** se pide la vecindad de la sala 4 con profundidad 5, **entonces** es [2, 1, 5, 3, 6]. *(FR-370, FR-371)*
8. **Dado** la cripta con ciclos, **cuando** se pide la vecindad de la sala 1, **entonces** con profundidad 1 es [2, 3]; con 2 y con 5, [2, 3, 4], sin repetir la sala 4 aunque se llegue a ella por dos caminos. *(FR-370, FR-371)*
9. **Dado** una sala con una salida cuya puerta está cerrada, **cuando** se pide su vecindad con profundidad 1, **entonces** la sala detrás de la puerta aparece igual que hoy. *(FR-370)*
10. **Dado** cualquier cripta, **cuando** se pide una vecindad con profundidad negativa, **entonces** se rechaza con el mismo error que hoy y no se lee el esqueleto. *(FR-373)*
11. **Dado** una sala que no existe en la cripta, **cuando** se pide su vecindad con profundidad 0, 1, 2 o 5, **entonces** se rechaza con el mismo error que hoy. *(FR-373)*
12. **Dado** las cuatro criptas y las profundidades 0, 1, 2 y 5, **cuando** se cuentan con espías las búsquedas de salas en el esqueleto y las descargas del esqueleto de cada consulta, **entonces** las búsquedas son las mismas que en la versión vigente en cada combinación (por ejemplo, en la rejilla desde la sala 5: 1 búsqueda con profundidad 0, 2 con profundidad 1 y 6 con profundidad 2) y no hay descargas después de la primera. *(FR-374)*
13. **Dado** una cripta sintética de 1 000 salas, **cuando** se planea la vecindad desde muchas salas, **entonces** la respuesta coincide con la de la versión vigente en todas. *(FR-370, FR-371, FR-374)*

---

### Historia 2 · La planeación de la vecindad cumple el principio I (Prioridad: P1)

Quien revisa el código busca usos de colas, mapas y conjuntos de biblioteca. La planeación de la vecindad no debe aparecer en esa búsqueda.

**Por qué esta prioridad**: §6.2 lo exige en el código evaluado y hoy es un incumplimiento conocido.

**Prueba independiente**: búsqueda de importaciones y usos prohibidos en la parte del código que planea la vecindad, más las pruebas de la Historia 1.

**Escenarios de aceptación**:

1. **Dado** el código revisado, **cuando** se buscan las estructuras de biblioteca que prohíbe el principio I en la planeación de la vecindad, **entonces** no hay ninguna. *(FR-375)*
2. **Dado** la planeación revisada, **cuando** se pide la vecindad con profundidad 5 en la rejilla y en una cripta sintética de 1 000 salas, **entonces** el tiempo de cada consulta es proporcional a las salas alcanzadas y no al tamaño de la cripta. *(FR-375, FR-376)*
3. **Dado** una estructura propia del proyecto que ya sirve para recorrer en orden de llegada, **cuando** se elige con qué planear la vecindad, **entonces** se reutiliza si es adecuada o se deja escrito por qué no. *(FR-375)*

---

### Historia 3 · Las mediciones de red, caché y guardado se repiten con la carga nueva (Prioridad: P1)

El grupo vuelve a medir red, caché y guardado con cazadores, costos de salida, llaves y partida de formato 8, y registra, fila por fila, el valor de antes, el de después, la diferencia y su causa. Con esos datos se decide si cada decisión de la Parte I sigue siendo adecuada.

**Por qué esta prioridad**: es lo que pide §5.6 y la evidencia que se defiende.

**Prueba independiente**: ejecutar los bloques de medición antes del cambio (código vigente) y después, y comparar las tablas generadas.

**Escenarios de aceptación**:

1. **Dado** el código vigente antes de esta capacidad, **cuando** se ejecutan los bloques de red/caché y de guardado, **entonces** sus resultados se guardan como «antes», con la fecha y el comando usado. *(FR-377)*
2. **Dado** el código revisado y la carga nueva (cazadores que se mueven, costos de salida, consulta de llaves, partida de formato 8), **cuando** se ejecutan los mismos bloques, **entonces** cada fila queda con su valor de antes, de después, la diferencia y la causa. *(FR-377, FR-378)*
3. **Dado** una fila de cuenta de solicitudes, **cuando** el después difiere del antes, **entonces** la causa nombra el elemento de la carga nueva que la explica (por ejemplo, la consulta de llaves). *(FR-378, FR-379)*
4. **Dado** cualquier fila de red, **cuando** se compara el después con el antes, **entonces** no es más del doble. *(FR-383)*
5. **Dado** una decisión de la Parte I (estrategia de precarga, capacidad y búsqueda de la caché, formato y tamaño del catálogo en disco), **cuando** los datos muestran que dejó de ser adecuada, **entonces** se cambia y el cambio queda en el Documento de Decisiones con la fila que lo motivó. *(FR-380)*
6. **Dado** una decisión de la Parte I que sigue siendo adecuada, **cuando** se documenta la revisión, **entonces** se cita la fila del después que lo muestra. *(FR-380)*
7. **Dado** una decisión revisada (se mantenga o cambie), **cuando** se lee su apartado en el documento de la Parte I, **entonces** tiene una nota con el veredicto y un enlace a la sección «012» de `DECISIONES.md`, y la evidencia original sigue ahí. *(FR-388)*
8. **Dado** el bloque de guardado con la partida de formato 8, **cuando** se mide guardar y cargar con 10, 100 y 1 000 salas, **entonces** ningún valor supera el doble de su antes. *(FR-381, FR-384)*
9. **Dado** las filas de tiempo, **cuando** varían entre ejecuciones, **entonces** el registro indica que dependen de la máquina y las filas de cuenta salen idénticas en dos ejecuciones con la misma semilla. *(FR-379)*

---

### Historia 4 · Leer una sala de una partida guardada sigue sin leer todo el archivo (Prioridad: P2)

Al consultar una sala individual de una partida guardada, el juego sigue leyendo solo esa parte del archivo, también con la partida de formato 8 de la cripta de referencia.

**Por qué esta prioridad**: es una decisión de la Parte I que la carga nueva (más datos por sala y conocimiento del jugador) podría haber roto sin que nada falle.

**Prueba independiente**: guardar una partida de formato 8 de la cripta sintética del tamaño de la cripta de referencia (y, a mano, de la cripta publicada más grande descargada) y medir bytes leídos y tiempo al recuperar una sala, frente a cargar la partida completa.

**Escenarios de aceptación**:

1. **Dado** una partida de formato 8 guardada a partir de la cripta sintética del tamaño de la cripta de referencia, **cuando** se lee una sala individual, **entonces** los bytes leídos son menos que el tamaño del archivo y no dependen de cuántas salas tiene la partida. *(FR-382)*
2. **Dado** la misma partida, **cuando** se mide la lectura de una sala y la carga completa, **entonces** ambas filas quedan con su antes y después, y la lectura de una sala es más rápida que la carga completa. *(FR-377, FR-382)*
3. **Dado** una partida de formato 8 con 10, 100 y 1 000 salas, **cuando** se lee la primera, una del medio y la última, **entonces** el tiempo de lectura no crece con la cantidad de salas más allá de la variación de la máquina. *(FR-382)*
4. **Dado** la cripta publicada más grande descargada, **cuando** se guarda una partida de formato 8 sin gastar solicitudes y se lee una sala, **entonces** los bytes leídos son menos que el tamaño del archivo y el resultado queda en la sección «012» de `DECISIONES.md`. *(FR-382, FR-388)*

---

### Historia 5 · Inventario de usos prohibidos que quedan (Prioridad: P2)

El grupo lista todos los usos de estructuras de biblioteca que prohíbe el principio I que quedan en el código de producción (fuera de pruebas y mediciones). Se corrigen los del código que resuelve un problema evaluado en §5 (la caché de fichas y la planeación de la vecindad). Los demás se justifican por escrito en el Documento de Decisiones (FR-388).

**Por qué esta prioridad**: la vecindad no es el único caso. Hay otros que se conocen y no están documentados.

**Prueba independiente**: búsqueda de importaciones y usos prohibidos en el código de producción, comparada con la tabla del inventario.

**Escenarios de aceptación**:

1. **Dado** el código de producción, **cuando** se buscan las estructuras prohibidas por el principio I, **entonces** cada aparición está en la tabla del inventario con su ubicación y su destino (corregida o justificada). *(FR-385, FR-386)*
2. **Dado** la caché de fichas corregida, **cuando** se vuelven a pasar las pruebas existentes y el bloque de red/caché, **entonces** el comportamiento observable no cambia y las filas de cuenta (solicitudes, aciertos y fallos por capacidad) salen idénticas. *(FR-386, FR-387)*
3. **Dado** el contenedor de salidas de cada sala, su conversión desde la API y su reconstrucción al cargar una partida, **cuando** se lee el Documento de Decisiones, **entonces** cada uno está justificado: guarda hasta 4 salidas que solo se recorren en orden, no es un índice, caché ni tabla de búsqueda, y se dice qué costaría corregirlo. *(FR-386)*
4. **Dado** el inventario terminado, **cuando** se repite la búsqueda, **entonces** no aparece ningún uso que no esté en la tabla. *(FR-385)*

---

### Casos límite

- Profundidad negativa **y** sala inexistente a la vez: se rechaza por la profundidad, como hoy (no se lee el esqueleto). *(FR-373)*
- Sala sin salidas: la vecindad es vacía con cualquier profundidad. *(FR-370)*
- Salida que lleva a la propia sala o dos salidas que llevan a la misma sala: la sala de destino aparece una sola vez, o ninguna si es la propia. *(FR-371)*
- Salida en un solo sentido (A tiene salida a B, pero B no a A): desde A se llega a B; desde B no se llega a A. *(FR-370)*
- Profundidad mayor que el tamaño de la cripta: el resultado es igual al de la profundidad suficiente para alcanzarlo todo. *(FR-370)*
- La carga nueva cambia una cuenta de solicitudes por un motivo legítimo (la consulta de llaves): no se marca como regresión si la causa queda escrita y no se pasa del doble. *(FR-378, FR-383)*
- Una fila del antes no puede reproducirse porque el bloque cambió de escenario: se marca como «sin antes comparable» con el motivo, no se inventa un valor. *(FR-377)*
- Un uso de biblioteca solo está en código de medición o de pruebas: no entra al inventario de producción, pero se menciona el criterio de exclusión. *(FR-385)*

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Planeación de la vecindad**

- **FR-370**: La planeación de la vecindad DEBE devolver, para toda cripta, sala existente y profundidad no negativa, exactamente las mismas salas que la versión vigente antes de esta capacidad: las que se alcanzan desde la sala por sus salidas (con la puerta abierta o cerrada) en a lo sumo esa cantidad de pasos.
- **FR-371**: La respuesta DEBE conservar el orden de descubrimiento vigente: por niveles de distancia y, dentro de cada sala, por salidas en el orden N, E, S, O. No DEBE repetir salas ni incluir la sala de partida.
- **FR-372**: Con profundidad 0, la respuesta DEBE ser vacía para toda sala existente.
- **FR-373**: Una profundidad negativa y una sala inexistente DEBEN rechazarse con los mismos errores y en el mismo orden de comprobación que hoy (primero la profundidad, después la existencia de la sala).
- **FR-374**: Las lecturas del esqueleto de la cripta por consulta DEBEN ser iguales a las de la versión vigente para cada cripta, sala y profundidad de los escenarios. Se cuentan dos cosas, ambas con espías y comparadas con la versión vigente:
  - las **búsquedas de una sala dentro del esqueleto en memoria**: 1 para validar la sala de partida más 1 por cada sala cuyas salidas se exploran (nivel menor que la profundidad); con profundidad negativa, 0;
  - las **descargas del esqueleto desde la fuente de datos**: ninguna adicional después de la primera por cripta.
- **FR-375**: La planeación de la vecindad NO DEBE usar ninguna estructura de biblioteca prohibida por el principio I. DEBE reutilizar una estructura propia de la Parte I o II cuando sea adecuada, o dejar escrito por qué no lo es.
- **FR-376**: El trabajo de una consulta DEBE crecer con las salas alcanzadas y sus salidas, no con el total de salas de la cripta (más allá de la lectura del esqueleto, que no cambia).

**Repetición de mediciones**

- **FR-377**: Los bloques de medición de red/caché y de guardado DEBEN ejecutarse con el código vigente antes de cualquier cambio de esta capacidad («antes») y con el código revisado («después»), y ambos resultados DEBEN guardarse junto con el comando y la fecha. Si una fila no tiene antes comparable, DEBE marcarse así y decir por qué.
- **FR-378**: El «después» DEBE medirse con la carga nueva: cazadores que se mueven, costos de salida, la consulta de llaves contada en el presupuesto y la partida de formato 8. La carga nueva entra en los mismos escenarios de los bloques: las filas son las mismas que en el antes, con la carga puesta, y no se agregan filas aparte. Por eso la causa de cada diferencia DEBE decir si viene del cambio de código o de la carga (FR-379).
- **FR-379**: Cada fila DEBE registrar el antes, el después, la diferencia (absoluta y en porcentaje) y la causa. Las filas de cuenta DEBEN salir idénticas en dos ejecuciones con la misma semilla; las de tiempo DEBEN marcarse como dependientes de la máquina.
- **FR-380**: Para cada decisión de la Parte I sobre red, caché y guardado (estrategia de precarga, capacidad y búsqueda de la caché, catálogo en disco, formato binario de partida), el Documento de Decisiones DEBE decir si sigue siendo adecuada, citando las filas del después. Si deja de serlo, DEBE cambiarse y documentarse el cambio con la fila que lo motivó. La regla de precarga queda fuera (FR-324): solo se registran sus filas.
- **FR-381**: El bloque de guardado DEBE medir guardar, cargar, tamaño en bytes y lectura de una sala individual con partidas de formato 8 de 10, 100 y 1 000 salas.

**Lectura de una sala individual**

- **FR-382**: Leer una sala individual de una partida guardada NO DEBE leer el archivo completo. DEBEN medirse los bytes leídos y el tiempo, frente al tamaño del archivo y al tiempo de la carga completa, en dos mediciones:
  - **En el bloque de guardado**, con una partida de formato 8 generada a partir de una cripta sintética determinista por semilla, del tamaño de la cripta de referencia (§6.1). Esta medición se repite igual en cualquier máquina y sin red.
  - **A mano**, con una partida de formato 8 de la cripta publicada más grande que esté descargada, sin gastar solicitudes. Su resultado se documenta en la sección «012» de `DECISIONES.md` y no entra al bloque. Si no hay ninguna cripta publicada completa descargada, se registra así y no se descarga ninguna.

**Rendimiento**

- **FR-383**: Ninguna fila de red del después DEBE ser más del doble de su antes (en solicitudes o en tiempo).
- **FR-384**: Guardar y cargar una partida NO DEBEN exceder sus límites actuales. El límite de cada fila de guardado (guardar, cargar y leer una sala, con 10, 100 y 1 000 salas) es el doble de su valor en el antes, la misma regla que en red (FR-383).

**Inventario de usos prohibidos**

- **FR-385**: DEBE inventariarse cada uso de estructuras de biblioteca prohibidas por el principio I en el código de producción, con su ubicación y para qué sirve. Quedan fuera las pruebas y el código de medición, y el criterio de exclusión DEBE escribirse.
- **FR-386**: Los usos en código que resuelve un problema evaluado en §5 (la caché de fichas y la planeación de la vecindad) DEBEN corregirse en esta capacidad. Los demás DEBEN justificarse por escrito en el Documento de Decisiones (qué hacen, por qué no son índice, caché ni tabla de búsqueda y qué costaría corregirlos). Entre ellos están el contenedor de salidas de cada sala (hasta 4, solo se recorre en orden), su conversión desde la respuesta de la API y su reconstrucción al cargar una partida. Un uso nuevo que aparezca en el inventario se clasifica con este mismo criterio.
- **FR-387**: Corregir un uso NO DEBE cambiar el comportamiento observable. Las pruebas existentes DEBEN seguir pasando, y las filas de cuenta de los bloques afectados DEBEN salir idénticas.

**Documentación**

- **FR-388**: «Documento de Decisiones» designa a dos archivos, cada uno con su parte:
  - **`DECISIONES.md`**: una sección «012» con las tablas de antes y después (FR-377, FR-379), el veredicto de cada decisión de la Parte I (FR-380) y el inventario con sus correcciones y justificaciones (FR-385, FR-386);
  - **`DOCUMENTACION_DECISIONES_DISENO.md`** (el documento de la Parte I): en cada decisión revisada, una nota breve con el veredicto (se mantiene o cambia) y un enlace a esa sección. Su evidencia original no se borra.

### Entidades clave

- **Consulta de vecindad**: cripta, sala de partida y profundidad. Su respuesta es una lista ordenada de salas o un error.
- **Fila de medición**: bloque, sección, nombre de la medición, valor de antes, valor de después, diferencia, causa y tipo (cuenta o tiempo).
- **Revisión de decisión**: decisión de la Parte I, filas que la respaldan, veredicto (se mantiene o cambia) y, si cambia, en qué cambia.
- **Uso inventariado**: ubicación en el código de producción, estructura usada, para qué sirve y destino (corregido o justificado, con su texto).

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: En las 4 criptas de los escenarios × las profundidades 0, 1, 2 y 5 × todas sus salas, y en una cripta sintética de 1 000 salas, el 100 % de las respuestas, errores y cuentas de lecturas del esqueleto coinciden con la versión vigente.
- **SC-002**: La búsqueda de estructuras prohibidas no encuentra ninguna en la planeación de la vecindad, y cada uso que encuentra en el resto del código de producción está en el inventario (0 sin registrar).
- **SC-003**: El 100 % de las filas de los bloques de red/caché y guardado tienen su antes, su después, la diferencia y la causa (o la marca «sin antes comparable» con su motivo).
- **SC-004**: Ninguna fila de red del después supera el doble de su antes.
- **SC-005**: Guardar y cargar una partida de formato 8 con 10, 100 y 1 000 salas no superan el doble de su antes en ninguna fila (FR-384).
- **SC-006**: Con la partida de formato 8 de la cripta sintética del tamaño de la cripta de referencia, y también con la de la cripta publicada más grande descargada, leer una sala individual lee menos bytes que el archivo completo y tarda menos que cargar la partida entera.
- **SC-007**: Cada decisión de la Parte I sobre red, caché y guardado tiene su veredicto en la sección «012» de `DECISIONES.md`, respaldado por al menos una fila del después, y una nota con enlace en `DOCUMENTACION_DECISIONES_DISENO.md` (FR-388).

## Supuestos

- «Versión vigente» es el código de producción en el commit `1f009a1` (la punta de la rama al aclarar esta especificación, antes de cualquier cambio de la 012). Las mediciones del «antes» se toman con ese código. Su respuesta a la planeación de la vecindad es la referencia de equivalencia, y las salidas de los escenarios se calcularon con esa regla (por niveles, N, E, S, O).
- Los bloques de medición son los que ya existen: «red/caché» es el que se ejecuta como `--bench cache` (precarga, búsqueda en la caché, disco, catálogo, vecindad, aciertos por capacidad) y «guardado» es `--bench guardado`. Se repiten tal cual y se agrega solo lo que pide la carga nueva.
- El antes de la caché puede tomarse de nuevo y no copiarse de la 009, porque la 009 midió con un cliente que no pide llaves. Las cifras de la 009 se citan como referencia, no como antes.
- «Código de producción» es todo lo que ejecuta el juego, sin contar las pruebas, el código de medición ni los scripts de descarga auxiliares.
- El dict que devuelve la lectura de JSON de la API puede seguir usándose solo para leer JSON (lo permite el principio I). No cuenta como índice ni entra en el inventario si solo se usa así.
- «Cripta de referencia (§6.1)» fija el tamaño de la cripta sintética que generan los bloques de medición, como en la 004 y la 007. No es una cripta publicada concreta (principio V).
- Fuera de alcance: cambiar la regla de precarga (por costo, FR-324), el formato de partida y su rechazo de versiones anteriores, la verificación de resolubilidad y el replay.
