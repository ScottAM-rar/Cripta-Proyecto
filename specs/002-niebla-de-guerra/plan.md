# Plan de implementación: Niebla de guerra y mapa conocido

**Rama**: `002-niebla-de-guerra` | **Fecha**: 2026-10-31 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/002-niebla-de-guerra/spec.md` (FR-201 a FR-226, con las 2 clarificaciones de la sesión 2026-10-31)

## Resumen

El jugador pasa a tener un **conocimiento propio de la cripta**: cada sala está explorada, avistada o desconocida, y cada salida recuerda el estado de su puerta tal como se vio por última vez. Ese conocimiento es estado del modelo (no de la vista), se deshace con el pergamino, se guarda con la partida y se consulta con un comando `mapa`.

El enfoque técnico, justificado en [research.md](research.md), tiene seis piezas:

1. Un módulo nuevo `Logica/MapaConocido.py` con **arreglos indexados por id de sala** (estado de sala) y **un arreglo plano de 4 posiciones por sala** (puerta recordada). Consultar es acceso directo.
2. Una **lista de salas exploradas en orden de descubrimiento**: sirve para deshacer quitando del final y para guardar. El orden ascendente del comando `mapa` se obtiene **al consultar** con `ordenar_adaptativo`.
3. **Exploración proporcional a lo revelado**: al entrar se recorren solo las salidas de la sala (y, con antorcha, las de sus vecinas), leyendo el esqueleto `MapaCripta` sin modificarlo y sin pasar por `ingresarEnSala`.
4. **Observación de puertas por lectura al entrar y por aviso al cambiar**: el aviso reutiliza el `avisar` que ya recibe `fijar_cerrada`; el único punto de cambio de puertas no cambia.
5. **Cambios deshacibles** `EXPLORAR_SALA`, `AVISTAR_SALA` y `OBSERVAR_PUERTA` como `CambioDTO`, registrados en un solo nodo por entrada y revertidos en orden inverso.
6. **Tres contratos hacia afuera**: el estado guardado (Scott), la reversión (JP y Scott) y una vista del conocimiento para `BuscadorRutas` (la futura 006 «ir a»).

## Contexto técnico

**Lenguaje/versión**: Python 3.11+ (el del proyecto).

**Dependencias principales**: solo las existentes. No se agrega ninguna.

**Almacenamiento**: el conocimiento viaja en el guardado binario existente, que sube de versión (ver [contracts/estado-guardado-niebla.md](contracts/estado-guardado-niebla.md)). Sin caché nueva.

**Pruebas**: `unittest`, convención del repositorio (`test_*.py` en la raíz, `tests_labs/` con la API falsa y las criptas sintéticas).

**Plataforma**: consola, multiplataforma.

**Tipo de proyecto**: aplicación de consola por capas (Controlador → Servicio → Lógica + adaptadores). La capacidad se agrega sin reescribir la Parte I.

**Objetivos de rendimiento** (FR-223 a FR-226, constitución VII): consultar el estado de una sala o de una puerta no crece con el tamaño de la cripta ni del mapa conocido; entrar a una sala cuesta lo revelado; registrar y revertir cuesta los cambios de la acción. El ciclo de eventos con decenas de cazadores sigue por debajo de 20 ms.

**Restricciones**: sin `dict`/`set` como índice, sin `heapq`/`bisect`/`collections`/`networkx`; sin `sorted()` ni `list.sort()`. `MapaCripta` no se modifica. El modelo no importa red, disco ni vista. 0 solicitudes nuevas: todo sale del esqueleto que ya se descarga al iniciar.

**Escala/alcance**: cripta de referencia y criptas sintéticas deterministas por semilla en tres tamaños, el mayor 50 veces el menor.

## Verificación de la constitución

*Compuerta: debe pasar antes de la investigación (Fase 0) y se reevalúa tras el diseño (Fase 1).*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Estructuras propias | Arreglos sobre `list`, lista de exploradas y vista propia; el orden sale de `ordenar_adaptativo` del repositorio. Sin `dict`/`set`, sin `heapq`/`bisect`/`collections`/`networkx`, sin `sorted()`/`list.sort()`. Se reutiliza `RecorridoPorNiveles` solo como alternativa medida (research §4). | Pasa |
| II. Determinismo | El conocimiento no usa azar. Depende solo del esqueleto, de la sala del jugador y de las puertas; el orden de exploración es el de las salidas (N, S, E, O). No depende de qué salas estén descargadas (research §2). | Pasa |
| III. Equivalencia ante el reuso | No hay resultado reutilizado que invalidar: el conocimiento es estado, no caché. La excepción es el `version_conocimiento` que la 006 podrá comparar; sube también al deshacer. La equivalencia se prueba contra una referencia que reconstruye el conocimiento desde cero repitiendo las acciones (research §2 y §5). | Pasa |
| IV. MVC y adaptadores | `MapaConocido` vive en Lógica y no importa red, disco ni vista. La vista recibe un DTO de conocimiento y no el mapa completo. El nombre de cada sala llega por el esqueleto, que ya viene por la interfaz de fuente de datos (`--offline` incluido). | Pasa |
| V. Sin datos de una cripta | Todo se dimensiona con el mayor id del esqueleto. Ningún id, cantidad ni nombre fijo. | Pasa |
| VI. Presupuesto y versiones | 0 solicitudes extra (la antorcha no descarga contenido). El formato de partida sube de versión y un archivo sin niebla se rechaza con versión encontrada y esperada. | Pasa con pendiente P3 |
| VII. Rendimiento medido | Bloque nuevo `mapa` en `--bench` con la alternativa descartada de cada decisión; se repiten `ordenamiento`, `inventario`, `retroceso`, `guardado` y `ciclo` con la carga nueva ([contracts/bench-mapa.md](contracts/bench-mapa.md)). | Pasa |
| VIII. Especificación primero | Este plan no agrega reglas. Lo que la especificación dice distinto del modelo se eleva como pendiente (abajo). | Pasa con pendiente P1 |
| IX. Trazabilidad | Matriz FR → módulo → prueba en [quickstart.md](quickstart.md); cada caso del Apéndice B tiene escenario y prueba. | Pasa |
| X. Cambios de especificación | P1 se corrige primero en `spec.md`, en confirmación aparte, antes de tocar el código. | Pasa con pendiente |
| XI. Uso de LLM | El registro de los comandos `/speckit` de esta capacidad lo lleva el grupo en `PROMPTS_LLM_Fer.md` (instrucción expresa; este plan no escribe en `PROMPTS_LLM.md`). | Acción del grupo |

**Observación sobre código existente (no es violación de este plan)**: la Parte I ya usa `collections.deque` en `SalaDTO.salidas`, en `servicioCripta` y en la caché. Esta capacidad recorre ese `deque` (solo lectura) y no agrega usos nuevos.

**Reevaluación tras el diseño (Fase 1)**: sin cambios. El diseño solo agrega listas, enteros y un DTO; ninguna decisión necesitó una estructura prohibida. La única estructura de búsqueda alternativa que sí la usaría (montículo) no interviene aquí.

### Pendientes detectados al planificar

Ninguno bloquea el plan; P1 y P3 piden decisión del grupo antes de implementar.

- **P1. La especificación dice una cosa distinta del modelo sobre las puertas.** Los Supuestos de `spec.md` afirman que «una puerta es una sola para las dos salas que conecta; abrirla o cerrarla desde un lado cambia su estado visto desde el otro». En el modelo no es así: cada salida de cada sala es un objeto propio con su estado, y abrir o cerrar solo cambia la salida de la sala donde ocurre (`SalaLogica.intentarAbrirPuerta`, `cerrarPuerta`; `GestorEventos` registra un `CAMBIAR_PUERTA` para esa salida). Una conexión A↔B son dos salidas que pueden estar en estados distintos. El plan es válido con ambas lecturas: la memoria es **por salida** (cuatro por sala), y estar en A o en B observa **las dos** salidas de la conexión (la propia y la entrante). Pero el texto del supuesto es falso y debe corregirse en `spec.md` antes de implementar (principio X). Redacción propuesta: «Cada salida tiene su propia puerta. Una conexión entre dos salas se compone de una salida por sentido, con estados independientes. El jugador observa una puerta mientras está en la sala de origen o en la de destino de esa salida.»
- **P2. El esqueleto trae el nombre de cada sala, pero el mapa del esqueleto lo descarta.** `MapaDTO` guarda solo salidas. Para mostrar el nombre de una sala explorada por la antorcha sin descargar su contenido hace falta conservarlo. Cambio aditivo y sin efecto sobre la 001: `SalaMapaDTO.nombre` (por defecto vacío), que rellena `ServicioCripta.obtener_mapa`. `MapaCripta` no se toca (ignora el campo). No es un hueco de especificación; queda aquí por transparencia.
- **P3. Numeración del formato binario.** El repositorio ya declara `VERSION_FORMATO = 6` y `VERSION_ESTADO = 3` por la 001. Este plan llama «formato v6» al que entrega Scott el 9 de noviembre, como pide la tarea. Si ese «6» es el que ya existe, un archivo de la 001 llegaría al decodificador con otra cantidad de campos y daría un error genérico en lugar de «versión encontrada y esperada» (FR-221). El contrato recomienda subir a `VERSION_FORMATO = 7` y `VERSION_ESTADO = 4`. Decide el grupo con Scott.
- **P4. Referencia «§5.6».** No encontré esa sección en los documentos del repositorio. Se interpretó «mediciones de ordenamiento y de vista de la Parte I» como los bloques `ordenamiento` (§4.9) e `inventario` (§4.5, `vistaInventario`) de `--bench`, más `retroceso`, `guardado` y `ciclo` por tocar lo mismo que esta carga. Si «§5.6» designa otra cosa, hay que añadirla a la lista de [contracts/bench-mapa.md](contracts/bench-mapa.md).

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/002-niebla-de-guerra/
├── plan.md              # Este archivo
├── research.md          # Fase 0: las 8 decisiones, alternativas, complejidad, evidencia preliminar
├── data-model.md        # Fase 1: estructuras, invariantes, transiciones, validaciones
├── quickstart.md        # Fase 1: validación de extremo a extremo y matriz de trazabilidad
├── contracts/
│   ├── cambios-deshacibles.md      # EXPLORAR_SALA, AVISTAR_SALA, OBSERVAR_PUERTA (JP y Scott)
│   ├── estado-guardado-niebla.md   # campos nuevos del estado guardado (Scott)
│   ├── vista-buscador.md           # vista del conocimiento para BuscadorRutas (futura 006)
│   ├── interfaz-vista.md           # qué muestra la consola y de dónde sale
│   └── bench-mapa.md               # secciones y criterios de --bench
├── checklists/requirements.md
├── mediciones.md        # se agregará al implementar
├── replays/             # partida.log por escenario, con el requisito en el nombre (se agregará al implementar)
└── tasks.md             # Lo genera /speckit-tasks (no este comando)
```

### Código fuente (raíz del repositorio)

```text
DTO/
├── MapaDTO.py                 # SalaMapaDTO.nombre (aditivo, por defecto vacío)
├── ConocimientoDTO.py         # NUEVO: MapaConocidoDTO, SalaConocidaDTO, SalidaConocidaDTO (lo que ve la vista)
└── EstadoGuardadoDTO.py       # ConocimientoGuardadoDTO, PuertaRecordadaDTO; campo `conocimiento` al final; VERSION_ESTADO

Logica/
├── MapaConocido.py            # NUEVO: estado de salas, puertas recordadas, exploradas; entrar, puerta_cambio, deshacer,
│                              #        exportar/restaurar, instantánea para la vista y VistaMapaConocido
├── MapaCripta.py              # SIN CAMBIOS
├── RecorridoPorNiveles.py     # SIN CAMBIOS (solo se mide como alternativa)
├── BuscadorRutas.py           # SIN CAMBIOS (la vista nueva cumple su contrato)
├── PuertasLogica.py           # SIN CAMBIOS: sigue siendo el único punto de cambio de puertas
├── GestorEventos.py           # engancha `entrar` tras MOVER_JUGADOR; el aviso de puerta de las acciones hacia adelante
│                              #   también llega a MapaConocido (el del pergamino no)
├── PergaminoLogica.py         # revierte los 3 cambios nuevos delegando en MapaConocido
├── EstadoJuegoLogica.py       # construye MapaConocido al iniciar (conocimiento del instante 0) y expone la consulta
└── EstadoGuardadoLogica.py    # exporta y restaura el conocimiento; rechaza un conocimiento incoherente

adaptadores/
├── servicioCripta.py          # obtener_mapa rellena el nombre de cada sala
├── codec_partida.py           # registra las dos clases guardadas nuevas (lo hace Scott)
└── AlmacenPartidaBinario.py   # VERSION_FORMATO sube (lo hace Scott)

Servicio/
└── EstadoJuegoServicio.py     # mapaConocido() y vistaSalaActual(): entregan DTO, nunca el mapa completo

Controlador/
├── ControladorJuego.py        # comando `mapa` (no es acción: no pasa por accionJugador ni por el log)
└── Vista.py                   # mostrar_mapa_conocido; mostrar_juego muestra salidas desde el conocimiento

bench/
├── mapa.py                    # NUEVO: bloque "mapa"
├── ordenamiento.py / inventario.py / retroceso.py / guardado.py / ciclo.py   # se repiten con la carga nueva
└── __init__.py                # registra el bloque

test_mapa_conocido.py          # NUEVO: historias 1, 2 y 3 (estados, puertas, antorcha)
test_niebla_retroceso.py       # NUEVO: historia 4 (pergamino) y equivalencia con la referencia
test_niebla_vista.py           # NUEVO: historia 5 (mapa, sin fugas, vista con el grafo completo apagado)
test_niebla_guardado.py        # NUEVO: historia 6 (guardar, cargar, rechazar versión anterior)
test_niebla_determinismo.py    # NUEVO: historia 7 (determinismo, enemigos sin cambios)
test_niebla_proporcional.py    # NUEVO: FR-223 a FR-225 por conteo, no por tiempo
test_vista_conocimiento_buscador.py   # NUEVO: contrato de la vista para BuscadorRutas
test_puertas_punto_unico.py    # EXISTENTE: sigue pasando; MapaConocido no escribe `.cerrada`
tests_labs/
├── referencia_conocimiento.py # NUEVO: reconstruye el conocimiento desde cero repitiendo acciones
└── escenarios_niebla.py       # NUEVO: escenarios de reproducción (python -m tests_labs.escenarios_niebla)
```

**Decisión de estructura**: se mantiene la arquitectura por capas. `MapaConocido` recibe datos ya construidos (`MapaCripta`, la lista de salas, el jugador y una función para registrar cambios) y no importa red, disco ni vista.

## Seguimiento de complejidad

Sin violaciones de la constitución que justificar.
