# Plan de implementación: Reproducir partida grabada hasta un instante dado (replay-hasta)

**Rama**: `008-replay-hasta` | **Fecha**: 2026-11-04 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/008-replay-hasta/spec.md` (FR-401 a FR-413, con las clarificaciones de corte inclusivo en $t$ y reporte exhaustivo de estado).

---

## Resumen

Esta capacidad incorpora la opción `--hasta t` a la herramienta de reproducción desatendida `--replay <PARTIDA.log>`, permitiendo acotar la simulación de una partida grabada hasta un instante virtual específico $t$ y exhibir el estado exhaustivo alcanzado (FR-401, FR-404). La regla del instante $t$ es la de la especificación corregida (FR-402, FR-403, FR-406): se ejecutan los eventos de los demás actores con tiempo $\le t$ y no se ejecuta la decisión del jugador cuyo instante sea mayor o igual que $t$ (estado «justo antes de tomarla», enunciado §3.6).

El enfoque técnico, respaldado y justificado en [research.md](research.md):

1. **Tope en el ciclo de eventos (Opción b)**: Se añade un parámetro opcional `tope: int | None` en `EstadoJuegoLogica._avanzarHastaProximoTurno`. El ciclo se detiene sin desapilar cuando el próximo evento del reloj virtual tiene un tiempo estrictamente mayor que $t$ (FR-402).
2. **Decisión del jugador en $t$ (FR-403, FR-406)**: en la Parte I el jugador decide en el instante actual del reloj (`reloj.tiempo_actual`) y su acción ocurre en ese momento; su costo solo programa el turno siguiente. Por eso `EstadoJuegoLogica.repetirPartida` toma el siguiente registro del log únicamente si `reloj.tiempo_actual < hasta`. Si es mayor o igual, la decisión no se ejecuta. Con $t = 0$ el reloj vale 0, no se ejecuta ninguna acción y se obtiene el estado inicial sin regla especial.
3. **Completar el instante $t$ (FR-403)**: cuando el turno del jugador cae exactamente en $t$, el ciclo lo consume y devuelve el control, pero pueden quedar eventos de otros actores con tiempo $t$ y número de secuencia posterior. Un método auxiliar `_completarInstante(hasta)` los ejecuta con el mismo cuerpo de procesamiento que usa el ciclo (código compartido, sin duplicarlo) y nunca ejecuta una decisión del jugador.
4. **Corte anticipado de lectura del log**: al alcanzar el tope o al terminar la partida, `repetirPartida` cesa la lectura de acciones. El costo es proporcional al tiempo reproducido y no al tamaño total del archivo (FR-412).
5. **Invarianza de `--replay` base**: Si `tope is None`, el comportamiento es 100% idéntico al actual (FR-409).
6. **Validación temprana y rechazo en CLI**: En `main.py`, la función validadora `_instante_hasta` y la verificación de precedencia rechazan valores negativos, valores no enteros o el uso huérfano de `--hasta` sin `--replay` antes de instanciar el servicio o acceder al disco (FR-407, FR-408, Principio IV).
7. **Separación MVC estricta**: La lógica devuelve un objeto de datos puro `ResultadoReplayHastaDTO` en `DTO/` con la información exhaustiva (sala, vida y estadísticas, llaves, objetos, efectos activos, enemigos con vida, fin de partida y log agotado). `main.py` se encarga de imprimirlo (FR-404, Principio IV). El mapa conocido queda diferido hasta que exista la capacidad de niebla de guerra (Assumptions de `spec.md`).
8. **Medición con `--bench`**: Se agrega el bloque `replay` en `bench/replay.py` con cargas sintéticas deterministas de 250, 1 000 y 4 000 acciones, midiendo la Opción b frente a las alternativas descartadas (a y c) y evaluando la proporcionalidad por conteo de eventos procesados (FR-412, FR-413, Principio VII).

---

## Contexto técnico

- **Lenguaje/versión**: Python 3.11+ (estándar del proyecto).
- **Dependencias principales**: Ninguna biblioteca externa nueva. Solo módulos estándar de Python (`argparse`, `dataclasses`, `time`, `gc`) y módulos existentes del repositorio (`EstadoJuegoServicio`, `EstadoJuegoLogica`, `RelojVirtual`).
- **Almacenamiento**: Acceso de solo lectura a archivos de registro existentes en `logs/`. No se crean nuevos logs, no se modifican archivos de partidas ni se escribe en la tabla de puntajes (FR-410).
- **Pruebas**: Framework `unittest` del repositorio (`test_replay_hasta.py`, `test_determinismo_replay.py`).
- **Plataforma**: Multiplataforma consola (Windows / Linux / macOS).
- **Tipo de proyecto**: Aplicación de consola por capas (Controlador → Servicio → Lógica → DTO / Adaptadores).
- **Objetivos de rendimiento**: Costo computacional proporcional a lo reproducido hasta $t$ y nunca mayor que la reproducción completa (FR-412, SC-003). Criterio duro: conteo de eventos procesados $\le 0.55 \times \text{total}$ para $t = T / 2$.
- **Restricciones constitucionales**: Prohibido el uso de `heapq`, `bisect`, `collections` (`deque`, `defaultdict`), `networkx`, y `dict`/`set` como índice o caché.

---

## Verificación de la constitución

*Compuerta: Evaluación de principios fundamentales antes de la implementación.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| **I. Estructuras propias** | El ciclo de eventos utiliza el montículo propio existente `RelojVirtual` (`heap` propio). Los datos reportados se estructuran en `ResultadoReplayHastaDTO` usando tipos estándar autorizados (`list`, `tuple`, `dataclass`). No se introducen `dict`/`set` como índices ni bibliotecas prohibidas (`collections`, `heapq`, etc.). | Pasa |
| **II. Determinismo** | Mismo log, misma semilla y mismo $t$ producen siempre la misma partida y la misma salida (FR-411). El desempate de eventos en el reloj es estricto por `id_secuencia`. La lista de enemigos en sala se ordena deterministamente por identificador. | Pasa |
| **III. Equivalencia ante el reuso** | La reproducción acotada no reutiliza estado sucio ni arrastra cachés viejas. El estado resultante en $t$ es idéntico al prefijo de una ejecución completa (propiedad de prefijo). | Pasa |
| **IV. Separación MVC y adaptadores** | `EstadoJuegoLogica` y `EstadoJuegoServicio` retornan un `ResultadoReplayHastaDTO` puro. La presentación en consola se realiza exclusivamente en `main.py`. `--replay` con `--hasta` no inicializa componentes de vista interactiva (FR-410). | Pasa |
| **V. Sin datos de una cripta concreta** | No hay literales de salas, enemigos ni criptas específicas en el código. El sistema funciona con cualquier log y con partidas sintéticas de cualquier tamaño en `--bench`. | Pasa |
| **VI. Presupuesto de red y versiones** | La reproducción opera sin conexión y valida las versiones de cripta y catálogo declaradas en la cabecera del log sin realizar solicitudes de red. | Pasa |
| **VII. Rendimiento medido** | Bloque `replay` en `--bench` mide partidas sintéticas deterministas de 250, 1 000 y 4 000 acciones. Mide la Opción b frente a las alternativas descartadas a y c. El criterio duro se basa en conteo de eventos. | Pasa |
| **VIII. La especificación precede al código** | Cada decisión responde a un requisito funcional FR-4xx de `spec.md`. Se documentan hallazgos observados en la especificación. | Pasa |
| **IX. Trazabilidad** | Matriz exhaustiva FR-4xx → Escenario → Prueba automatizada en `quickstart.md`. | Pasa |
| **X. Cambios de especificación** | Los hallazgos del análisis de consistencia (regla del instante $t$, FR-404, FR-405, SC-003 y propiedad de prefijo) se corrigieron primero en `spec.md`, sesión de corrección del 2026-11-04, y este plan se alineó después con la especificación corregida. | Pasa |
| **XI. Uso de LLM** | Los comandos con texto propio se registran con modelo y fecha en `PROMPTS_LLM.md` (tarea T031). | Pasa |

---

## Correcciones de la especificación incorporadas

Los hallazgos del `/speckit-analyze` se resolvieron primero en `spec.md` (principio X) y este plan no introduce reglas nuevas:

1. **Instante $t$ y decisión del jugador** (FR-402, FR-403, FR-406): reemplaza la «regla de guarda» que este plan proponía para $t = 0$. Ya no hay excepción: la decisión del jugador en $t$ no se ejecuta, y con $t = 0$ eso da el estado inicial.
2. **Propiedad de prefijo** (Historia 3, escenario 2, FR-411): `--replay` es un proceso por lotes sin reanudación; la equivalencia se verifica comparando el estado al detenerse en $t$ con el que tenía la reproducción completa en ese instante.
3. **Criterio de rendimiento por conteo** (SC-003): para $t = T / 2$, los eventos procesados deben ser $\le 0.55 \times$ los de la reproducción completa. La razón de tiempos de reloj se reporta como dato informativo en `--bench`.
4. **Resumen completo** (FR-404): se agregan estadísticas y efectos activos. El mapa conocido queda diferido hasta la capacidad de niebla de guerra.

---

## Decisiones arquitectónicas y justificación por requisito

### D1. Tope opcional en el ciclo de eventos y compleción del instante (`_avanzarHastaProximoTurno`, `_completarInstante`)
- **Justificación**: Satisface **FR-402** (detención en $t$, exclusión de eventos $> t$) y **FR-403** (inclusión de los eventos de otros actores con tiempo $\le t$). Al interrumpir el ciclo cuando el próximo evento supera $t$ (sin desapilarlo, incluido un `TURNO_JUGADOR` posterior), se congela el avance en el último evento ejecutado. Si `tope is None`, el comportamiento es invariante (**FR-409**).
- **Eventos restantes en $t$**: si el `TURNO_JUGADOR` consumido tiene tiempo exactamente $t$, `_completarInstante(hasta)` ejecuta los eventos pendientes con tiempo $t$ en el orden `(tiempo, id_secuencia)`, reutilizando el cuerpo de procesamiento del ciclo. Así el estado es el posterior a todos los eventos de los demás actores en $t$ (Apéndice B del enunciado).
- **Descarte de alternativa a**: Cortar solo entre acciones del jugador permitiría que eventos de enemigos entre turnos se ejecuten más allá de $t$, violando FR-402.
- **Descarte de alternativa c**: Reproducir todo y recortar procesaría el 100% de los eventos, violando FR-412.

### D2. Validación temprana de argumentos en CLI
- **Justificación**: Satisface **FR-407** (rechazo de $t$ negativo o no entero con mensaje claro) y **FR-408** (rechazo de `--hasta` sin `--replay`). La validación se realiza mediante `_instante_hasta` en `main.py` antes de instanciar `EstadoJuegoServicio` ni cargar adaptadores (Principio IV).

### D3. DTO de salida desacoplado de la consola
- **Justificación**: Satisface **FR-404** (reporte exhaustivo de estado) y el **Principio IV** (separación MVC). `EstadoJuegoLogica` arma `ResultadoReplayHastaDTO` conteniendo: instante pedido, instante alcanzado, acciones reproducidas, sala, vida, estadísticas vigentes (ataque, defensa, velocidad), llaves, objetos, efectos activos, enemigos en la sala con sus vidas, estado de fin de partida y bandera de log agotado. `main.py` da formato de texto al DTO. El mapa conocido no se incluye (diferido, Assumptions de `spec.md`).

### D4. Decisión del jugador, acciones sin costo y regla `reloj.tiempo_actual < hasta`
- **Justificación**: Satisface **FR-403** y **FR-406**. En la Parte I la decisión del jugador ocurre en `reloj.tiempo_actual`. Antes de tomar cada registro del log (acción con costo, movimiento de cursor del inventario o uso de pergamino, que no consumen o no avanzan el reloj por sí mismos) se comprueba `reloj.tiempo_actual < hasta`. Si no se cumple, la lectura del log se detiene y el estado es el de justo antes de esa decisión. Con $t = 0$ se obtiene el estado inicial sin caso especial.

### D5. Detección unívoca de fin de partida vs. log agotado
- **Justificación**: Satisface **FR-404** y **FR-405**. Si `self.fin` es verdadero, se informa `partida_terminada = True` con el motivo; el aviso «terminó antes de alcanzar $t$» solo aplica si `instante_alcanzado < instante_pedido`. Si el log concluye sin que la partida haya terminado y con el reloj estrictamente antes de $t$, se informa `log_agotado = True` y se emite la advertencia de FR-405. Si el reloj llegó exactamente a $t$, no hay aviso.

### D6. Definición precisa de «instante alcanzado»
- **Justificación**: Corresponde al valor exacto de `self.estadoJuego.reloj.tiempo_actual` tras concluir el último evento ejecutado, garantizando que siempre sea $\le t$.

### D7. Determinismo e independencia de almacenamiento
- **Justificación**: Satisface **FR-411** y el **Principio II**. El desempate de eventos simultáneos utiliza `(tiempo, id_secuencia)` del reloj virtual, y la lista de enemigos en sala se ordena deterministamente por identificador.

### D8. Benchmark `replay` y cargas sintéticas deterministas
- **Justificación**: Satisface **FR-412**, **FR-413** y el **Principio VII**. Integra el bloque `replay` a `--bench`, evaluando partidas sintéticas de 250, 1 000 y 4 000 acciones, comparando la Opción b con las alternativas descartadas a y c.

---

## Estructura del proyecto y módulos afectados

### Documentación de la capacidad
```text
specs/008-replay-hasta/
├── spec.md              # Especificación funcional aprobada
├── plan.md              # Este plan de implementación
├── research.md          # Fase 0: Alternativas y justificación técnica
├── data-model.md        # Fase 1: Estructura ResultadoReplayHastaDTO
├── quickstart.md        # Fase 1: Guía de ejecución y matriz de trazabilidad
├── contracts/           # Fase 1: Contratos de interfaz CLI, texto y bench
│   ├── argumento-hasta.md
│   ├── salida-texto.md
│   └── bench-replay.md
├── checklists/          # Listas de verificación de calidad
│   └── requirements.md
└── tasks.md             # Fase 2: Tareas de implementación (/speckit-tasks)
```

### Código fuente afectado en el repositorio

```text
main.py                              # Validación temprana de --hasta, argumento argparse,
                                     # llamada a servicio con hasta y formateo de salida.
DTO/
└── ResultadoReplayHastaDTO.py       # Nuevo DTO para el reporte exhaustivo de estado.
Servicio/
└── EstadoJuegoServicio.py           # Adaptación de repetirPartida(archivo, hasta=None).
Logica/
└── EstadoJuegoLogica.py             # Parámetro tope en _avanzarHastaProximoTurno,
                                     # corte de log en repetirPartida, armado de DTO.
bench/
├── __init__.py                      # Registro del bloque "replay" en BLOQUES.
└── replay.py                        # Nuevo módulo de benchmark para evaluar proporcionalidad
                                     # y comparar con alternativas descartadas a y c.
tests_labs/
└── generador_partidas.py            # Generador determinista de logs sintéticos para pruebas y bench.
test_replay_hasta.py                 # Suite de pruebas unitarias para todos los FR-4xx.
test_determinismo_replay.py          # Pruebas de determinismo y propiedad de prefijo.
```

---

## Análisis de complejidad

### Complejidad temporal

Sea:
- $N$: Cantidad total de acciones en el archivo de registro.
- $t$: Instante virtual de corte especificado en `--hasta`.
- $K$: Cantidad de eventos del juego cuyo tiempo virtual es $\le t$.
- $M$: Cantidad de eventos pendientes en la agenda del `RelojVirtual` en un instante dado (crece con los actores activos de la cripta; no se asume una cota fija).

1. **Lectura y avance del ciclo**: Cada evento desapilado o programado en el montículo del reloj toma $O(\log M)$.
2. **Número de operaciones**: Al detenerse en el instante $t$, se procesan los $K$ eventos con tiempo $\le t$ y las acciones del jugador con decisión anterior a $t$. Los restantes no se desapilan ni se ejecutan.
3. **Costo total**: $O(K \log M)$, proporcional a lo ocurrido hasta $t$ e independiente del tamaño total del log $N$ (FR-412). La compleción del instante agrega solo los eventos con tiempo exactamente $t$, ya contados en $K$.

### Complejidad espacial

- **Memoria adicional**: $O(1)$ más allá del estado regular del juego en memoria. No se almacenan historiales de retroceso de repetición ni buffers intermedios de salida.
- `ResultadoReplayHastaDTO` almacena únicamente el estado puntual en el instante $t$: $O(E + I + F)$, con $E$ enemigos en la sala actual, $I$ objetos del inventario y $F$ efectos activos.
