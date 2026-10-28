<!--
Sync Impact Report (temporal; eliminar antes de confirmar)
- Cambio de versión: plantilla sin rellenar → 1.0.0
- Principios modificados: ninguno renombrado (todos nuevos, I–XI)
- Secciones añadidas: Principios Fundamentales, Restricciones y Alcance, Flujo de Desarrollo, Gobernanza
- Secciones eliminadas: ninguna
- Pendientes diferidos: ninguno
-->
# Constitución de CRIPTA

Cripta es un juego por turnos sobre un servicio web que publica criptas (salas, salidas, puertas,
llaves, enemigos, objetos, trampas). Es un proyecto de Estructuras de Datos II (2026): las reglas
del juego están especificadas; las decisiones de estructuras de datos no, y se defienden con
mediciones. Esta constitución rige para todo el grupo y para todo agente que asista al proceso.

## Principios Fundamentales

### I. Estructuras propias

Las estructuras de datos de los problemas evaluados DEBEN implementarse a mano.
NO DEBEN usarse `dict` ni `set` como índice, caché o tabla de búsqueda; `heapq`, `bisect`,
`collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` ni ninguna biblioteca
de grafos o rutas. Están permitidos `list` como almacenamiento contiguo, `struct`, `json`,
`requests` y bibliotecas de interfaz; el `dict` de `respuesta.json()` solo se usa para leer JSON.
Las estructuras de la Parte I DEBEN reutilizarse cuando sean adecuadas. Todo plan o tarea generado
por un agente DEBE revisarse contra esta lista antes de implementar.

- **Motivo:** el objetivo del curso es construir y defender las estructuras, no importarlas.
- **Verificación:** búsqueda de importaciones y usos prohibidos en el código; revisión de cada
  plan y tarea contra la lista, registrada antes de implementar.

### II. Determinismo

Misma cripta, misma semilla y mismas acciones DEBEN producir la misma partida. Todo desempate DEBE
ser explícito y por regla (menor id, número de secuencia). Cualquier estado aleatorio DEBE formar
parte del estado guardado y de los puntos de control. Ninguna decisión DEBE depender del orden de
iteración, de la hora ni de qué contenido ya fue descargado.

- **Motivo:** sin determinismo no hay reproducción, ni pruebas fiables, ni comparaciones justas.
- **Verificación:** ejecutar dos veces la misma partida y comparar `partida.log`; reproducir con
  contenido descargado y sin descargar y obtener resultados idénticos.

### III. Equivalencia ante el reuso

Reutilizar un cálculo anterior (rutas, mapas, cachés) SOLO es válido si se demuestra que no
cambia la decisión respecto de calcular desde cero en ese instante. La invalidación DEBE razonarse
por evento y medirse.

- **Motivo:** un reuso incorrecto produce decisiones distintas sin que nada falle visiblemente.
- **Verificación:** pruebas que comparan el resultado reutilizado con el recalculado desde cero
  tras cada tipo de evento; el razonamiento de invalidación consta en `plan.md`.

### IV. Separación MVC y adaptadores

El modelo NO DEBE conocer HTTP, archivos ni la interfaz. Red y disco DEBEN ir detrás de
interfaces; `--offline` DEBE sustituir la fuente de datos sin condicionales en el modelo.
`--replay`, `--bench` y `--verificar` NO DEBEN instanciar la vista.

- **Motivo:** permite probar, reproducir y medir el modelo sin dependencias externas.
- **Verificación:** el modelo no importa módulos de red, disco ni interfaz; los modos `--replay`,
  `--bench` y `--verificar` se ejecutan sin vista y sin red salvo lo que su especificación exija.

### V. Sin datos de una cripta concreta

NO DEBE existir en el código ningún id de sala o entidad, cantidad de páginas, presupuesto ni
estadística de una cripta específica. El programa DEBE funcionar con una cripta nueva y más grande.

- **Motivo:** el código evaluado no puede depender de la cripta de desarrollo.
- **Verificación:** búsqueda de literales de la cripta de desarrollo en el código; ejecución con
  una cripta sintética mayor.

### VI. Presupuesto de red y versiones

DEBE respetarse `presupuesto_solicitudes`, incluida la consulta de llaves. Lo persistido de una
versión anterior DEBE invalidarse mediante la validación de versión, nunca borrando archivos a
mano. El formato binario de partida DEBE versionarse: un archivo incompatible DEBE rechazarse o
migrarse de forma explícita, y NO DEBE cargarse en silencio.

- **Motivo:** exceder el presupuesto o cargar datos obsoletos corrompe la partida sin aviso.
- **Verificación:** contador de solicitudes comparado con el presupuesto en pruebas; pruebas con
  caché y guardados de versión anterior que comprueban el rechazo o la migración explícita.

### VII. Rendimiento medido

Toda afirmación de rendimiento DEBE respaldarse con `--bench`, y al menos una sección DEBE medir
la alternativa descartada. Límites locales: ciclo de eventos 20 ms con decenas de cazadores;
verificación de resolubilidad 200 ms; historia 50 ms con 5 000 acciones; un paso de «ir a» 5 ms.
Los benchmarks DEBEN usar criptas sintéticas deterministas por semilla. Las mediciones de la
Parte I DEBEN repetirse con la carga nueva y, si una decisión deja de servir, DEBE cambiarse y
documentarse el antes y el después.

- **Motivo:** las decisiones de estructuras se defienden con datos, no con intuición.
- **Verificación:** salida de `--bench` con los límites y con la alternativa descartada; registro
  del antes y el después en `DECISIONES.md` cuando una decisión cambia.

### VIII. La especificación precede al código

`spec.md` DEBE describir reglas del juego, historias, escenarios de aceptación y requisitos
numerados, sin nombres de estructuras, clases ni módulos. `plan.md` DEBE describir estructuras
elegidas, alternativas, complejidad, módulos afectados y mediciones, sin reglas nuevas.
`tasks.md` DEBE contener tareas pequeñas y verificables, cada una con los requisitos que atiende.
Un programa que hace algo que ninguna especificación describe es un defecto del mismo tipo que una
especificación que no describe el programa.

- **Motivo:** separa qué debe hacer el juego de cómo se construye y evita comportamiento no
  documentado.
- **Verificación:** revisión de `spec.md`, `plan.md` y `tasks.md` contra este contenido; cada
  comportamiento del programa se remonta a un requisito.

### IX. Trazabilidad

Cada requisito funcional DEBE tener un identificador estable (FR-NNN) con prefijo por capacidad:
1xx terreno y cazador, 2xx niebla e «ir a», 3xx resolubilidad, 4xx línea de tiempo. Cada caso del
Apéndice B DEBE ser un escenario de aceptación. Cada escenario DEBE tener una prueba automatizada
o un `partida.log` de reproducción que cite el id del requisito. Las pruebas DEBEN conservarse en
el repositorio.

- **Motivo:** permite demostrar que cada requisito se cumple y que nada quedó sin cubrir.
- **Verificación:** tabla requisito → escenario → prueba o log, sin huecos, revisada en `analyze`.

### X. Cambios de especificación

Si la implementación revela que la especificación estaba mal, DEBE corregirse primero la
especificación y después el código, en confirmaciones separadas. El historial de Git DEBE mostrar
la especificación de cada capacidad confirmada antes de su código. Una especificación desactualizada
respecto del programa entregado es un defecto.

- **Motivo:** la especificación es la fuente de verdad y debe poder auditarse.
- **Verificación:** `git log` por capacidad muestra la confirmación de especificación anterior a la
  de código; comparación final de cada especificación con el programa entregado.

### XI. Uso de LLM

Spec-kit y el agente son herramientas de proceso: NO DEBEN introducir dependencias prohibidas y el
código que producen es responsabilidad del grupo. Todo comando `/speckit` con texto propio DEBE
registrarse en `PROMPTS_LLM.md` con herramienta y modelo. Cualquier integrante DEBE poder explicar
cualquier especificación y defender cualquier decisión.

- **Motivo:** la autoría y la comprensión son del grupo, no de la herramienta.
- **Verificación:** cada comando `/speckit` con texto propio tiene su entrada en `PROMPTS_LLM.md`;
  la defensa oral de cualquier integrante sobre cualquier parte.

## Restricciones y Alcance

- El repositorio contiene la Parte I terminada. La Parte II DEBE continuar sobre ella sin
  reescribirla, y todo lo de la Parte I sigue vigente salvo que la Parte II lo modifique
  explícitamente.
- Lo existente NO DEBE re-especificarse ni romperse: capas Controlador → Servicio → Lógica →
  Inventario más adaptadores (red, disco, caché, binario, log); reloj virtual con agenda de
  eventos y desempate por número de secuencia; intervalo = `max(1, costo*100 // velocidad)`;
  pergamino de retroceso limitado a 5 acciones; inventario del jugador; caché persistente con
  validación de versión de la cripta; guardado binario versionado; `partida.log` y reproducción;
  comportamientos errante, guardián y rastreador; `--offline`, `--replay` y `--bench`.
- La Parte II agrega cuatro capacidades, cada una con su propia especificación en
  `specs/<NNN-nombre>/`: (1) terreno y cazador, (2) niebla de guerra e «ir a», (3) verificación de
  resolubilidad (`--verificar`, `--forzar`, consulta de llaves), (4) línea de tiempo
  (`historia <t>` / `#k`, puntos de control, `--checkpoint-cada`, `--replay … --hasta`).
- Las elecciones de estructuras de datos y las reglas de una capacidad concreta NO DEBEN
  incluirse en esta constitución: pertenecen a `plan.md` y `spec.md` respectivamente.

## Flujo de Desarrollo

Cada capacidad DEBE seguir, en este orden: constitution (una vez, para todo el grupo) → specify →
clarify → plan → tasks → analyze → implement.

- `DECISIONES.md` DEBE enlazar a la `spec.md` y al `plan.md` de cada capacidad, indicar si la
  decisión final coincide con el plan original y, si no, qué medición motivó el cambio.
- Cada agente DEBE leer esta constitución en cada fase.
- Un plan o tarea que contradiga esta constitución es un error del grupo, no del agente.

## Gobernanza

Esta constitución prevalece sobre cualquier plan o tarea. Se enmienda SOLO por acuerdo del grupo,
con versión y fecha. Una enmienda que afecte especificaciones ya escritas obliga a revisarlas.
El versionado es semántico: MAJOR para eliminar o redefinir principios de forma incompatible,
MINOR para añadir un principio o ampliar materialmente la guía, PATCH para aclaraciones.
El cumplimiento se revisa en las fases `analyze` e `implement` de cada capacidad y en la
revisión de cada confirmación.

**Version**: 1.0.0 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-10-27
