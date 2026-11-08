# Plan de implementación: Puntos de control de la partida (007-puntos-de-control)

**Rama**: `007-puntos-de-control` | **Fecha**: 2026-11-07 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/007-puntos-de-control/spec.md` (FR-414 a FR-426, con todas las clarificaciones resueltas e integradas).

---

## Resumen

Esta capacidad implementa la infraestructura periódica de **puntos de control** de la partida (enunciado §3.6), permitiendo guardar copias completas del estado del juego a intervalos regulares de $K$ acciones del jugador ($K \ge 1$), configurables mediante la bandera `--checkpoint-cada K` o adoptando un valor por defecto medido. Esta infraestructura proporciona la base determinista y eficiente sobre la cual operará la futura consulta de estados pasados (`historia #k`, capacidad 004).

El enfoque técnico, respaldado y justificado en [research.md](research.md):

1. **Contador propio de la línea de tiempo vigente (`acciones_linea_tiempo`)**: Se crea un contador independiente de `accionesJugador`. Mientras `accionesJugador` (§2.12) mide el esfuerzo acumulado global para puntaje y ranking sin decrecer, `acciones_linea_tiempo` registra el avance en la línea temporal activa (se decrementa al usar el pergamino de retroceso).
2. **Punto de captura transparente y sincronizado**: 
   - El **Punto 0** se captura automáticamente al iniciar el juego antes de la primera decisión del jugador.
   - Los **Puntos periódicos $n$** se capturan al final de `EstadoJuegoLogica.accionJugador`, tras `_avanzarHastaProximoTurno` y `_registrarAccionEnLog`, cuando llega el turno del jugador y no hay fin de partida (estado previo a la decisión $n \times K + 1$). Si la acción finaliza la partida, no se captura.
   - **Poda por retroceso**: En la rama de uso del pergamino se descartan permanentemente los puntos de control con `acciones > acciones_linea_tiempo`.
3. **Reutilización de `EstadoGuardadoLogica` y `EstadoGuardadoDTO`**: Se reutiliza el mecanismo de instantáneas completas desconectadas (que incluye reloj, agenda, entidades, salas cargadas y estado del generador aleatorio). Como alternativa de diseño a medir en `--bench`, se compara la copia completa de historiales frente a la marca de longitud en historiales append-only.
4. **Formato binario v7 en `AlmacenPartidaBinario`**: La versión del formato de partida avanza a 7. Los archivos v6 y anteriores se rechazan explícitamente con `ErrorPartida` claro (FR-425).
5. **Validación temprana en CLI**: La función `_intervalo_checkpoint` en `main.py` rechaza valores $\le 0$, flotantes o no numéricos con código de salida 2 antes de inicializar servicios o tocar disco. El valor vigente se informa antes de la primera decisión.
6. **Estructuras propias (Principio I)**: Almacenamiento contiguo en `list[PuntoControlDTO]` ordenado por acciones, sin `dict`/`set` como índice, sin `heapq`, `bisect` ni `collections`. Se expone exclusivamente `obtenerPuntoControlReciente(k)` para la futura capacidad 004.
7. **Medición con `--bench` (Principio VII)**: Se añade el bloque `puntos_control` en `bench/puntos_control.py` evaluando $K \in \{1, 10, 50, 100\}$ en criptas sintéticas deterministas por semilla, verificando el límite de 20 ms con $K=1$, midiendo tamaño de archivo a 5 000 acciones y derivando el valor por defecto de $K$.

---

## Contexto técnico

- **Lenguaje/versión**: Python 3.11+ (estándar del proyecto).
- **Dependencias principales**: Módulos estándar (`argparse`, `dataclasses`, `struct`, `zlib`, `time`, `random`) y módulos existentes (`EstadoJuegoLogica`, `EstadoGuardadoLogica`, `EstadoGuardadoDTO`, `AlmacenPartidaBinario`).
- **Almacenamiento**: Persistencia binaria de partidas en formato v7 (`adaptadores/AlmacenPartidaBinario.py`). Los puntos de control se guardan dentro del mismo archivo de partida.
- **Pruebas**: Framework estándar `unittest` (`test_cli_checkpoint.py`, `test_puntos_control.py`, `test_determinismo_puntos_control.py`, `test_persistencia_v7.py`, `test_bench_puntos_control.py`).
- **Plataforma**: Multiplataforma consola (Windows / Linux / macOS).
- **Tipo de proyecto**: Aplicación por capas (Controlador → Servicio → Lógica → DTO / Adaptadores).
- **Objetivos de rendimiento**: Ciclo de eventos $\le 20$ ms en cripta de referencia con $K=1$ (FR-426, Principio VII). Crecimiento subcuadrático en memoria y almacenamiento.
- **Restricciones constitucionales**: Prohibido `dict` y `set` como índice o caché; prohibido `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`), `networkx`.

---

## Verificación de la constitución

*Compuerta: Evaluación de principios fundamentales antes de la implementación.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| **I. Estructuras propias** | Se utiliza `list` de Python exclusivamente como almacenamiento contiguo de `PuntoControlDTO`. No se utilizan `dict` ni `set` como índice o caché. Las operaciones de poda usan truncado de lista (`pop`) y la búsqueda de punto reciente para la capacidad 004 usa búsqueda manual lineal/binaria a mano sin `bisect` ni bibliotecas externas. | Pasa |
| **II. Determinismo** | Misma cripta, semilla y acciones producen exactamente el mismo resultado con cualquier $K$ (FR-423). El estado del generador aleatorio se incluye en cada punto de control (FR-421). Los puntos de control no alteran el reloj virtual ni el orden de eventos. Reanudar desde un punto de control genera un `partida.log` idéntico (FR-422). | Pasa |
| **III. Equivalencia ante el reuso** | Reanudar desde un punto de control produce una partida indistinguible de la ejecución continua desde cero. No se reutilizan cachés obsoletas ni estructuras con referencias compartidas. | Pasa |
| **IV. Separación MVC y adaptadores** | `EstadoJuegoLogica` desconoce archivos, red y presentación. El guardado en disco reside en `AlmacenPartidaBinario`. En `--replay`, no se inicializa la vista interactiva. `main.py` maneja la interfaz de consola y validación de argumentos CLI. | Pasa |
| **V. Sin datos de una cripta concreta** | No existen IDs ni estadísticas de criptas particulares en el código. Las pruebas y benchmarks operan sobre criptas sintéticas generadas deterministamente por semilla. | Pasa |
| **VI. Presupuesto de red y versiones** | El guardado binario incrementa a `VERSION_FORMATO = 7`. Archivos v6 o de la Parte I se rechazan explícitamente con mensaje claro sin cargar en silencio (FR-425). La toma de puntos de control no consume solicitudes de red. | Pasa |
| **VII. Rendimiento medido** | Bloque `puntos_control` en `--bench` mide criptas sintéticas con $K \in \{1, 10, 50, 100\}$. Se verifica el ciclo de eventos $\le 20$ ms con $K=1$. Se mide la alternativa de bitácora completa vs. marca de longitud y se defiende el valor por defecto de $K$ con datos. | Pasa |
| **VIII. La especificación precede al código** | Cada decisión responde estrictamente a un requisito funcional `FR-4xx` de `spec.md`. No se agregan reglas nuevas no contempladas en la especificación. | Pasa |
| **IX. Trazabilidad** | Matriz exhaustiva en `quickstart.md` vinculando cada requisito FR-414..FR-426 con escenarios de aceptación y pruebas automatizadas. | Pasa |
| **X. Cambios de especificación** | Todas las ambigüedades fueron clarificadas formalmente en `spec.md` (sesión 2026-11-07) antes de elaborar este plan. | Pasa |
| **XI. Uso de LLM** | El prompt y herramientas se registran en `PROMPTS_LLM_JP.md` y `PROMPTS_LLM.md` con modelo y fecha exactos. | Pasa |

---

## Decisiones arquitectónicas y justificación por requisito

### D1. Contador propio de línea de tiempo vigente (`acciones_linea_tiempo`)
- **Justificación**: Satisface **FR-418** y la definición clarificada de acción del jugador. `self.accionesJugador` es una métrica de puntaje acumulativo (§2.12) que no se reduce con el pergamino. Crear `self.acciones_linea_tiempo: int` permite incrementar por cada acción aceptada y decrementar en $m$ cuando el pergamino revierte $m$ acciones, manteniendo $K$ estrictamente alineado con la línea temporal activa.

### D2. Sincronización y captura en el ciclo de turnos
- **Justificación**: Satisface **FR-418**, **FR-419**, **FR-420** y **FR-421**.
  - **Punto 0**: Se toma en `iniciarJuego` antes de que el jugador realice su primera acción, asegurando que siempre exista una base completa desde la cual reconstruir el inicio.
  - **Puntos periódicos**: Al final de `accionJugador`, tras `_avanzarHastaProximoTurno` y `_registrarAccionEnLog`, si `not self.fin` y `acciones_linea_tiempo % K == 0`. Captura el estado exacto antes de la decisión $(n \times K + 1)$, con todos los eventos intermedios resueltos.
  - **Acción terminal**: Si la acción finaliza la partida (`self.fin = True`), el punto no se toma.
  - **Poda por retroceso**: Al usar el pergamino, se eliminan permanentemente los puntos con `acciones > acciones_linea_tiempo`.

### D3. Reutilización de `EstadoGuardadoDTO` e investigación de bitácora
- **Justificación**: Satisface **FR-421**, **FR-422** y el **Principio II**. Reutilizar `EstadoGuardadoLogica.exportar` garantiza que todo el estado del mundo (incluyendo `estado_azar` de `random.Random.getstate()`) quede desconectado e inmutable. Para evitar sobrecarga cuadrática de memoria con $K$ pequeños, se adopta y mide la alternativa de registrar la marca de longitud en historiales append-only en contraste con la copia exhaustiva de strings.

### D4. Formato binario v7 y rechazo explícito de versiones anteriores
- **Justificación**: Satisface **FR-424**, **FR-425** y el **Principio VI**. `AlmacenPartidaBinario` avanza a `VERSION_FORMATO = 7`. Se almacenan en el mismo archivo el $K$ configurado, `acciones_linea_tiempo` y el bloque indexado de puntos de control. Los archivos de versiones anteriores se rechazan explícitamente con mensaje explicativo, evitando corrupciones silenciosas. El contrato formal detallado se documenta en [contracts/formato-partida-v7.md](contracts/formato-partida-v7.md).

### D5. Validación temprana en CLI e invarianza de desenlace
- **Justificación**: Satisface **FR-414**, **FR-415**, **FR-416**, **FR-417** y **FR-423**.
  - `_intervalo_checkpoint` en `main.py` valida y rechaza valores inválidos ($\le 0$, flotantes, texto) con código de salida 2 antes de inicializar la lógica o tocar disco.
  - El valor vigente de $K$ se informa en consola antes de la primera decisión del jugador.
  - La elección de $K$ es puramente observacional y no afecta ninguna regla de juego ni desempate aleatorio; por ende, cualquier $K$ produce idéntico desenlace en `--replay` o partida interactiva.

### D6. Estructura de almacenamiento y consulta para capacidad 004
- **Justificación**: Satisface **FR-419**, **Principio I** y la preparación para la capacidad 004. Los puntos de control se mantienen en una lista contigua `list[PuntoControlDTO]`, ordenada monótonamente por `acciones_linea_tiempo`. La poda es un truncamiento eficiente desde la cola (`pop`). Se expone el método de lectura `obtenerPuntoControlReciente(k: int) -> PuntoControlDTO | None`, que halla el último punto con `acciones <= k` mediante búsqueda manual hacia atrás.

### D7. Benchmark `puntos_control` y derivación de $K$ por defecto
- **Justificación**: Satisface **FR-426**, **SC-004** y el **Principio VII**. Se implementa el módulo `bench/puntos_control.py` evaluando criptas sintéticas con $K \in \{1, 10, 50, 100\}$. Se mide el ciclo de eventos con $K=1$ frente al umbral de 20 ms, el consumo de memoria/archivo con 5 000 acciones y el número de pasos necesarios hasta una acción $k$. Con estos datos se valida y fija formalmente el valor por defecto de $K$ (propuesto inicialmente en 10).

---

## Estructura del proyecto y archivos afectados

```text
specs/007-puntos-de-control/
├── plan.md                                # Este documento de planificación
├── research.md                            # Justificación de alternativas y decisiones
├── data-model.md                          # Modelo de datos, DTOs y transiciones
├── contracts/
│   └── formato-partida-v7.md              # Especificación del formato binario v7
├── quickstart.md                          # Guía de validación y matriz de trazabilidad
└── checklists/
    └── requirements.md                    # Validación de calidad de requisitos (16/16)

Archivos de código a modificar o crear en la fase de implementación:
├── DTO/
│   └── PuntoControlDTO.py                 # Nuevo DTO inmutable de punto de control
├── Logica/
│   ├── EstadoJuegoLogica.py               # Atributos k_checkpoint, acciones_linea_tiempo, captura y poda
│   └── EstadoGuardadoLogica.py            # Adaptación para captura/restauración de puntos de control
├── adaptadores/
│   └── AlmacenPartidaBinario.py           # Formato v7, serialización de puntos de control y rechazo v6
├── main.py                                # Argumento --checkpoint-cada K, validador temprano y reporte
├── bench/
│   ├── puntos_control.py                  # Nuevo módulo de benchmark de puntos de control
│   ├── __init__.py                        # Registro del bloque puntos_control en --bench
│   └── test_bench_puntos_control.py       # Pruebas automatizadas del benchmark
└── tests/
    ├── test_cli_checkpoint.py             # Pruebas de validación CLI y código 2
    ├── test_puntos_control.py             # Pruebas unitarias de captura, turno y poda
    ├── test_determinismo_puntos_control.py# Pruebas de determinismo e invarianza de desenlace
    └── test_persistencia_v7.py            # Pruebas de guardado/carga v7 y rechazo de v6
```

---

## Complejidad y Justificación Constitucional

No se registran violaciones a los principios fundamentales ni se introducen bibliotecas prohibidas. Toda la funcionalidad se construye sobre estructuras de datos básicas autorizadas (`list`, `dataclass`, `struct`).
