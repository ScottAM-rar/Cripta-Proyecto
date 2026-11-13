# Especificación de capacidad: Arranque verificado y pantallas de consola claras

**Carpeta**: `011-arranque-verificado-pantallas`

**Creada**: 2026-11-13

**Estado**: Borrador

**Entrada**: Mostrar el reporte de resolubilidad al iniciar una partida, conectar los argumentos `--verificar` y `--forzar`, y renovar la pantalla de sala y el resumen de fin de partida de la consola. Las dos historias tienen la misma prioridad y se especifican, planifican e implementan juntas.

## Contexto y motivación

La verificación de resolubilidad y su reporte ya existen (003), pero hoy el jugador solo los ve cuando la partida se rechaza. El enunciado (§7.3, interfaz mínima) pide que los vea al iniciar. Además, la consola muestra la información de forma poco ordenada, y en la entrega anterior se descontaron puntos por la claridad de la interfaz.

Quien juega debe saber, antes del primer turno, si la cripta tiene solución; poder consultarlo sin abrir la partida; y poder jugar una cripta no resoluble solo si lo pide de forma explícita. Durante la partida debe encontrar siempre la misma información, en el mismo orden y formato, y al terminar debe ver un resumen claro.

**Lo existente y vigente (no se re-especifica)**: la verificación de resolubilidad y su reporte (003); los comandos de juego y su sintaxis (mover, mapa, ir a, historia y demás); niebla de guerra y mapa conocido (002); «ir a» (006); formato de guardado 8 y estado 5; `partida.log`.

**Fuera de alcance**: cambiar la verificación o el contenido de su reporte; cambiar el formato de guardado; colores ANSI o bibliotecas de interfaz nuevas; solicitudes de red adicionales.

## Clarificaciones

### Sesión 2026-11-13

- Q: ¿Qué códigos de salida usa `--verificar`? → A: 0 resoluble, 1 no resoluble, 2 error de uso o de lectura; el reporte se muestra siempre antes de salir.
- Q: ¿Se registra `--forzar` en `partida.log`? → A: No; la repetición no vuelve a verificar y el log conserva su formato. La advertencia solo se muestra al iniciar.
- Q: ¿Qué detalle lleva el resumen final? → A: Motivo, puntaje, acciones, tiempo virtual transcurrido, vida final y salas exploradas, en ese orden y con rótulos fijos.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Arranque verificado (Prioridad: P1)

Al iniciar una partida nueva, el jugador ve el reporte de resolubilidad antes de jugar, sea la cripta resoluble o no. Puede verificar una cripta sin abrir la partida y puede forzar el juego de una cripta no resoluble.

**Por qué esta prioridad**: cumple lo que pide el enunciado (§7.3) y evita que el jugador descubra tarde que la cripta no tiene solución.

**Prueba independiente**: iniciar una partida con una cripta resoluble y otra no resoluble, con y sin `--forzar`, y ejecutar `--verificar` sobre ambas; comprobar el texto mostrado, si se abre o no la partida y el código de salida.

**Escenarios de aceptación**:

1. **Dado** una cripta resoluble, **cuando** el jugador inicia una partida nueva, **entonces** ve el reporte de resolubilidad antes del primer turno y la partida se abre. *(FR-301)*
2. **Dado** una cripta no resoluble y sin `--forzar`, **cuando** inicia una partida nueva, **entonces** ve el reporte, la partida se rechaza como hoy y se le indica qué puede hacer (por ejemplo, usar `--forzar` o elegir otra cripta). *(FR-301, FR-303, FR-310)*
3. **Dado** una cripta no resoluble y `--forzar`, **cuando** inicia, **entonces** ve el reporte y una advertencia visible, y la partida se abre. *(FR-303, FR-304)*
4. **Dado** `--verificar <cripta>`, **cuando** se ejecuta, **entonces** se muestra el reporte, no se abre ninguna partida y el programa termina con código de salida 0 (resoluble) o 1 (no resoluble). *(FR-302)*
5. **Dado** `--forzar` sobre una cripta resoluble, **cuando** inicia, **entonces** la partida se abre normalmente sin advertencia de cripta no resoluble. *(FR-303)*
6. **Dado** el argumento `--forzar` indicado en la línea de comandos, **cuando** se inicia la partida, **entonces** ese valor llega hasta la operación que abre la partida pasando por cada capa, y ninguna capa lo decide por su cuenta. *(FR-305)*

---

### Historia 2 — Pantallas de consola claras (Prioridad: P1)

La consola muestra en cada turno una pantalla de sala con siempre el mismo orden y formato, un comando de ayuda con todos los comandos y un resumen claro al terminar la partida.

**Por qué esta prioridad**: la claridad de la interfaz se evalúa y fue penalizada en la entrega anterior.

**Prueba independiente**: con una partida de datos fijos, comparar el texto exacto de la pantalla de sala, de la ayuda, de los mensajes de rechazo y del resumen final contra el texto esperado, dos veces seguidas.

**Escenarios de aceptación**:

1. **Dado** un turno cualquiera, **cuando** se muestra la sala, **entonces** aparecen siempre en el mismo orden: la sala actual, sus salidas (dirección, costo y estado abierta, cerrada o sin observar), los enemigos presentes (activos o dormidos), los objetos y el estado del jugador (vida, tiempo, antorcha). *(FR-306)*
2. **Dado** una sala sin enemigos o sin objetos, **cuando** se muestra, **entonces** la sección aparece con una indicación explícita de que está vacía, sin cambiar el orden de las demás. *(FR-306)*
3. **Dado** una partida que termina (llegada a la salida, muerte u otro motivo), **cuando** termina, **entonces** se muestra un resumen con el motivo del fin, el puntaje, las acciones, el tiempo transcurrido, la vida final y las salas exploradas. *(FR-307)*
4. **Dado** el comando de ayuda, **cuando** el jugador lo escribe, **entonces** ve la lista de todos los comandos con su sintaxis. *(FR-309)*
5. **Dado** un comando inválido o rechazado, **cuando** se informa, **entonces** el mensaje dice qué pasó y qué puede hacer el jugador. *(FR-310)*
6. **Dado** los mismos datos de partida, **cuando** se muestra la misma pantalla dos veces, **entonces** el texto es idéntico carácter por carácter. *(FR-311)*

---

### Casos límite

- Cripta no resoluble con `--forzar`: la advertencia debe verse antes del primer turno, no perderse entre el reporte.
- `--verificar` sin cripta indicada, con cripta inexistente o ilegible: mensaje claro y código de salida 2.
- `--verificar` combinado con `--forzar`: la verificación no abre partida, por lo que `--forzar` no tiene efecto.
- Partida cargada o reproducida (`--replay`): no es una partida nueva; no se muestra el reporte de inicio.
- Sala con muchas salidas, enemigos u objetos: el orden y el formato no cambian.
- Fin de partida por un motivo no previsto: el resumen muestra un motivo genérico en español, nunca un texto vacío.

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Arranque verificado**

- **FR-301**: Al iniciar una partida nueva, el sistema DEBE mostrar el reporte de resolubilidad de la cripta antes del primer turno, tanto si es resoluble como si no.
- **FR-302**: El argumento `--verificar <cripta>` DEBE verificar la cripta indicada, mostrar su reporte y terminar sin abrir la partida, con código de salida 0 si la cripta es resoluble, 1 si no es resoluble y 2 si hay error de uso o de lectura (cripta inexistente, datos no disponibles, argumento faltante). El reporte se muestra siempre antes de salir.
- **FR-303**: El argumento `--forzar` DEBE permitir jugar una cripta que la verificación declara no resoluble; sin `--forzar`, una cripta no resoluble DEBE seguir rechazándose como hoy.
- **FR-304**: Al forzar una cripta no resoluble, el sistema DEBE mostrar una advertencia visible. El uso de `--forzar` NO se registra en `partida.log`: la repetición de una partida no vuelve a verificar la resolubilidad (solo ocurre al iniciar una partida nueva) y el log conserva su formato. La advertencia se muestra únicamente al iniciar.
- **FR-305**: El valor de forzar DEBE viajar desde el punto de entrada hasta el controlador del juego y de ahí a la operación que inicia la partida; ninguna capa DEBE decidirlo por su cuenta.

**Pantallas de consola**

- **FR-306**: En cada turno la consola DEBE mostrar, siempre en el mismo orden y formato: la sala actual; sus salidas con dirección, costo y estado (abierta, cerrada o sin observar: una puerta que el jugador aún no ha visto no se muestra como abierta ni como cerrada, para respetar la niebla de guerra de la 002); los enemigos presentes (activos o dormidos); los objetos; y el estado del jugador (vida, tiempo, antorcha).
- **FR-307**: Al terminar la partida la consola DEBE mostrar un resumen con el motivo del fin (llegada a la salida, muerte u otro), el puntaje, la cantidad de acciones, el tiempo virtual transcurrido, la vida final y la cantidad de salas exploradas, en ese orden y con rótulos fijos.
- **FR-308**: Todos los textos mostrados al jugador DEBEN estar en español y mostrarse sin caracteres dañados por la codificación (hoy los mensajes de error de `--cache-size` salen como «tamaÃ±o de la cachÃ©» en `main.py`).
- **FR-309**: DEBE existir un comando de ayuda que liste todos los comandos con su sintaxis, incluidos mover, mapa, ir a e historia.
- **FR-310**: Todo mensaje de error o rechazo DEBE decir qué pasó y qué puede hacer el jugador.
- **FR-311**: Una pantalla construida con los mismos datos DEBE verse idéntica cada vez; la salida es texto plano, sin colores ni secuencias de control.
- **FR-312**: La vista DEBE presentar solo lo que recibe del controlador: no decide reglas ni calcula nada del juego.
- **FR-313**: Los comandos existentes DEBEN conservar su sintaxis.

**Documentación**

- **FR-314**: El README DEBE explicar los argumentos nuevos, el comando de instalación de spec-kit con versión fija y cómo ejecutar las pruebas de aceptación.

**Restricciones**

- **FR-315**: La capacidad NO DEBE cambiar el formato de guardado (formato 8, estado 5), la verificación ni su reporte.
- **FR-316**: La capacidad NO DEBE hacer solicitudes de red adicionales, DEBE ser determinista, y NO DEBE usar dependencias nuevas, `dict`/`set` como índice ni `sorted()`/`list.sort()` (constitución I).
- **FR-317**: Toda prueba existente que compare textos de la vista y cambie por esta capacidad DEBE actualizarse de forma explícita, indicando qué texto cambió.

### Entidades clave

- **Reporte de verificación**: resultado de la verificación de una cripta (resoluble o no y su detalle); ya existe, solo se muestra.
- **Pantalla de sala**: texto del turno con secciones fijas (sala, salidas, enemigos, objetos, estado del jugador).
- **Resumen de fin de partida**: texto final con motivo, puntaje, acciones, tiempo, vida final y salas exploradas.
- **Indicador de forzar**: decisión del jugador de jugar una cripta no resoluble; nace en la línea de comandos y se transmite sin alterarse.
- **Catálogo de comandos**: lista de comandos con su sintaxis que alimenta la ayuda.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-301**: El 100 % de las partidas nuevas muestran el reporte de resolubilidad antes del primer turno, con cripta resoluble o no.
- **SC-302**: `--verificar` termina sin abrir partida en el 100 % de los casos, con códigos 0, 1 y 2 según resoluble, no resoluble y error.
- **SC-303**: Sin `--forzar`, el 100 % de las criptas no resolubles se rechazan; con `--forzar`, el 100 % se abren con advertencia visible.
- **SC-304**: Las pantallas de sala de cualquier turno tienen las mismas cinco secciones en el mismo orden (comprobado con pruebas de texto sobre al menos 5 situaciones distintas, incluidas salas vacías).
- **SC-305**: Dos construcciones de la misma pantalla con los mismos datos producen texto idéntico en el 100 % de los casos.
- **SC-306**: El 100 % de los comandos existentes aparece en la ayuda con su sintaxis, y el 100 % de los mensajes de error o rechazo existentes indica qué pasó y qué hacer.
- **SC-307**: Ningún texto mostrado al jugador contiene secuencias de color ni palabras en otro idioma que no sean términos del propio juego (comprobado con pruebas de texto).
- **SC-308**: Un lector nuevo puede instalar spec-kit con la versión fija y ejecutar las pruebas de aceptación siguiendo solo el README.

## Supuestos

- «Partida nueva» significa iniciar sin cargar partida guardada ni reproducir; el reporte de inicio no se muestra al cargar o reproducir.
- El reporte mostrado es exactamente el que ya produce la verificación, sin cambios de contenido.
- Sin `--forzar`, el rechazo actual se conserva, añadiendo solo la indicación de qué puede hacer el jugador.
- La palabra «acciones» del resumen final es la cantidad de acciones que el juego ya cuenta.
- La ayuda se invoca con un comando dentro de la partida; su nombre exacto se decide en la planificación sin cambiar los comandos existentes.
- Las pruebas de texto comparan la salida completa de las pantallas con textos esperados.
- «Sin observar» es el estado que la niebla de guerra (002, FR-219) da a una puerta cuya última observación no existe; la pantalla no inventa un estado para ella.
