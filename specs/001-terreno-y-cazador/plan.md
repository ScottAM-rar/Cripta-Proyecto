# Plan de implementación: Terreno y cazador

**Rama**: `001-terreno-y-cazador` | **Fecha**: 2026-10-27 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/001-terreno-y-cazador/spec.md` (FR-101 a FR-131, con las 3 clarificaciones de la sesión 2026-10-27)

## Resumen

Cada salida gana un costo de tránsito que sustituye al 100 fijo del movimiento, para el jugador y para todos los enemigos. Se agrega el comportamiento *cazador*, que en cada turno decide con la ruta de menor costo hasta la sala del jugador, limitada por su rango.

El enfoque técnico, justificado en [research.md](research.md), tiene cuatro piezas:

1. Un **mapa del esqueleto** completo (listas contiguas, aristas con costo) que se construye con el esqueleto que ya se descarga al iniciar. No gasta solicitudes y no depende de qué salas tengan contenido descargado.
2. Un **campo de costos hacia el jugador**: una búsqueda de menor costo acotada por el mayor rango activo y calculada desde la sala del jugador. Es compartida por todos los cazadores del mismo instante. Una decisión individual cuesta O(grado de la sala).
3. Una **regla de invalidación razonada por evento** (tabla en `research.md` §4). Su equivalencia con calcular desde cero se prueba de forma automatizada.
4. El **costo de la acción** deja de ser 100 fijo: el movimiento informa el costo de la salida cruzada y el siguiente evento del actor se programa con él.

## Contexto técnico

**Lenguaje/versión**: Python 3.11+ (el del proyecto, `match` ya se usa).

**Dependencias principales**: solo las existentes (`requests`, `json`, `struct`). No se agrega ninguna.

**Almacenamiento**: caché de disco existente (esqueleto y catálogo, ya validados por versión) y guardado binario propio, que sube de versión (ver `contracts/formato-partida.md`).

**Pruebas**: `unittest`, siguiendo la convención del repositorio (`test_*.py` en la raíz y `tests_labs/` con la API falsa `HttpFalso`).

**Plataforma**: consola, multiplataforma.

**Tipo de proyecto**: aplicación de consola por capas (Controlador → Servicio → Lógica → Inventario + adaptadores). La Parte II se agrega sin reescribir la Parte I.

**Objetivos de rendimiento** (FR-121, FR-122, constitución VII): ciclo de eventos < 20 ms con decenas de cazadores; el costo de un cazador de rango pequeño crece con la región dentro de su rango, no con el tamaño de la cripta.

**Restricciones**: sin `dict`/`set` como índice, sin `heapq`/`bisect`/`collections`/bibliotecas de grafos; el `dict` de `respuesta.json()` solo para leer. El presupuesto de solicitudes no cambia: el esqueleto ya se pide. El modelo no importa red, disco ni vista. Sin ids ni estadísticas de una cripta concreta.

**Escala/alcance**: cripta de referencia más criptas sintéticas deterministas por semilla de hasta decenas de miles de salas, con 1 a cientos de cazadores.

## Verificación de la constitución

*Compuerta: debe pasar antes de la investigación (Fase 0) y se reevalúa tras el diseño (Fase 1).*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Estructuras propias | Montículo mínimo, mapa de aristas y campo de costos escritos a mano sobre `list`. Sin `dict`/`set` como índice, sin `heapq`/`bisect`/`collections`/`networkx`. Se estudió reutilizar el montículo del reloj y se descartó con motivo (`research.md` §3). | Pasa |
| II. Determinismo | El cazador no usa azar. Desempate por menor id. La decisión no depende de qué salas estén descargadas ni del orden de iteración. | Pasa |
| III. Equivalencia ante el reuso | El campo reutilizado se invalida por evento (tabla en `research.md` §4). Se compara con el cálculo desde cero tras cada tipo de evento. | Pasa |
| IV. MVC y adaptadores | El mapa llega por la interfaz de fuente de datos; `--offline` lo recibe por el mismo camino. El modelo no importa red, disco ni vista. La vista solo muestra. | Pasa |
| V. Sin datos de una cripta | Ningún id, cantidad ni rango fijo en el código. Las estructuras se dimensionan con la cantidad de salas del esqueleto. | Pasa |
| VI. Presupuesto y versiones | 0 solicitudes extra. El formato de partida sube de versión y un archivo viejo se rechaza con mensaje claro. La caché se invalida por la validación de versión ya existente. | Pasa |
| VII. Rendimiento medido | Bloque nuevo `terreno` en `--bench` con la alternativa descartada, y repetición de las mediciones de la Parte I afectadas (`ciclo`, `guardado`, `retroceso`). | Pasa |
| VIII. Especificación primero | Este plan no introduce reglas nuevas. Las dudas de reglas se elevan como pendientes (ver abajo). | Pasa |
| IX. Trazabilidad | Matriz FR → módulo → prueba en `quickstart.md`. | Pasa |
| X. Cambios de especificación | Los dos huecos de especificación detectados se corrigen primero en `spec.md`. | Pasa con pendientes |
| XI. Uso de LLM | Registrar en `PROMPTS_LLM.md` los comandos `/speckit` de esta capacidad. | Acción del grupo |

**Observación sobre código existente (no es violación de este plan)**: la Parte I ya usa `collections.deque` en `SalaDTO.salidas`, en el recorrido de vecinas de `servicioCripta` y en la caché. Esta capacidad no agrega ningún uso nuevo de `deque` y no amplía los existentes. Solo añade el campo `costo` a los objetos que ese contenedor ya guarda. Si el grupo quiere retirar esos usos, es una tarea de la Parte I, no de esta capacidad.

### Pendientes de especificación detectados al planificar (RESUELTOS el 2026-10-27)

Se resolvieron en `spec.md` antes de implementar (principio X): FR-102 ampliado y FR-124 nuevo.

1. **Costos distintos en los dos lados de una conexión.** FR-102 dice que el costo es el mismo en ambos sentidos, pero no dice qué hacer si el esqueleto declara costos distintos en las dos salidas de una misma conexión. Decisión del grupo: gana la declaración de la sala de menor id y se emite una advertencia; si una sola sala declara costo, ese vale para ambos lados.
2. **Conexiones sin salida de vuelta.** El plan no asume que toda salida tenga su inversa. El mapa guarda las aristas entrantes por separado, de modo que una conexión de un solo sentido se trata correctamente. Decisión del grupo: es válido (FR-124).

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/001-terreno-y-cazador/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones, alternativas, invalidación por evento
├── data-model.md        # Fase 1: entidades, campos, validaciones, estados
├── quickstart.md        # Fase 1: validación de extremo a extremo y matriz de trazabilidad
├── contracts/
│   ├── esqueleto-y-catalogo.md   # contrato de datos de entrada (costo, comportamiento, rango)
│   ├── formato-partida.md        # cambio de formato del guardado binario
│   ├── interfaz-vista.md         # qué debe mostrar la vista
│   └── bench-terreno.md          # secciones y límites de --bench
├── checklists/requirements.md
├── mediciones.md        # Resultados de --bench y comparación con la Parte I (se agregó al implementar)
├── replays/             # partida.log por escenario, con el requisito en el nombre (se agregó al implementar)
└── tasks.md             # Lo genera /speckit-tasks (no este comando)
```

### Código fuente (raíz del repositorio)

```text
DTO/
├── SalaDTO.py                 # SalidaDTO.costo (por defecto 100)
├── ActorDTO.py                # EnemigoDTO.rango
├── CatalogoDTO.py             # EnemigoCatalogoDTO.rango
├── ResultadoEventoDTO.py      # costo de la acción realizada (por defecto sin informar)
├── AccionEnemigoDTO.py        # NUEVO: mensaje + costo de la acción de un enemigo
├── EstadoGuardadoDTO.py       # SalidaGuardadaDTO.costo, EnemigoGuardadoDTO.rango, VERSION_ESTADO
└── MapaDTO.py                 # NUEVO: esqueleto completo (sala, destino, costo, cerrada inicial)

Logica/
├── PuertasLogica.py           # NUEVO: único punto que cambia el estado de una puerta (fijar_cerrada)
├── MonticuloMinimo.py         # NUEVO: montículo binario sobre list, clave (costo, id)
├── MapaCripta.py              # NUEVO: aristas salientes y entrantes en listas contiguas
├── CampoDeCostos.py           # NUEVO: costo mínimo hacia la sala del jugador, acotado; con invalidación
├── CompCazador.py             # NUEVO: ComportamientoCazador
├── ComportamientoEnemigo.py   # contrato: devuelve AccionEnemigoDTO
├── CompErrante.py / CompRastreador.py / CompGuardian.py   # adaptados al contrato (misma conducta)
├── ComportamientoFactory.py   # registra "cazador"
├── EnemigosLogica.py          # programa el siguiente evento con el costo informado
├── ActorLogica.py             # _mover informa el costo de la salida cruzada
├── SalasLogica.py             # único punto que cambia el estado de una puerta (+ aviso de cambio)
├── GestorEventos.py           # ACCION_ENEMIGO pasa el campo de costos; avisa cambios de puerta
├── RetrocesoLogica.py         # el deshacer de puertas pasa por el mismo punto de cambio
├── EstadoGuardadoLogica.py    # guarda y restaura costo y rango; versión de estado
├── EstadoJuegoLogica.py       # construye el mapa al iniciar; costo del movimiento del jugador
└── FuenteCripta.py            # interfaz: obtener el mapa y las advertencias de datos

adaptadores/
├── servicioCripta.py          # lee "costo" de las salidas, arma el mapa, advierte costos inválidos
├── resolucion.py              # copia "rango" de la ficha; rango inválido → 0 con advertencia
├── codec_partida.py           # sin cambio de mecanismo; los campos nuevos van al final
└── AlmacenPartidaBinario.py   # VERSION_FORMATO sube

Controlador/
├── ControladorJuego.py        # el movimiento del jugador usa el costo de la salida
└── Vista.py                   # muestra costos y marca a los cazadores

bench/
├── terreno.py                 # NUEVO: bloque "terreno"
├── ciclo.py                   # se repite con cazadores
├── guardado.py / retroceso.py # se repiten con la carga nueva
└── __init__.py                # registra el bloque

test_terreno_costos.py         # NUEVO: historias 1 y 5, datos inválidos, persistencia
test_cazador.py                # NUEVO: historia 2
test_monticulo_minimo.py       # NUEVO: montículo propio y comprobación de importaciones prohibidas
test_equivalencia_cazador.py   # NUEVO: historia 3 (comparación con cálculo desde cero)
test_puertas_punto_unico.py    # NUEVO: ninguna otra parte escribe el estado de una puerta
test_determinismo_cazador.py   # NUEVO: historia 4 (partidas idénticas, logs de reproducción)
tests_labs/
├── api_falsa.py               # HttpConfigurable: cripta definida por la prueba
├── cripta_sintetica.py        # generadores deterministas por semilla (también los usa --bench)
├── partida_prueba.py          # arma una partida real del modelo para las pruebas
└── escenarios_terreno.py      # escenarios de reproducción (python -m tests_labs.escenarios_terreno)
```

**Decisión de estructura**: se mantiene la arquitectura por capas de la Parte I. Los módulos nuevos de lógica no importan red, disco ni vista; solo reciben datos ya construidos. Las pruebas siguen la convención del repositorio.

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar.

| Decisión que podría parecer compleja | Por qué se necesita | Alternativa más simple descartada |
|---|---|---|
| Campo compartido con invalidación por evento en lugar de recalcular en cada turno | Con decenas de cazadores, recalcular por cazador multiplica el trabajo. El presupuesto es 20 ms por ciclo. | Recalcular por cazador y por turno. Se conserva como alternativa **medida** en `--bench` (VII) y como referencia de las pruebas de equivalencia (III). |
