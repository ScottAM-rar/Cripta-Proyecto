# Plan de implementación: Reproducir partida grabada hasta un instante dado (replay-hasta)

**Rama**: `008-replay-hasta` | **Fecha**: 2026-11-04 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/008-replay-hasta/spec.md` (FR-401 a FR-413, con las clarificaciones de corte inclusivo en $t$ y reporte exhaustivo de estado).

---

## Resumen

Esta capacidad incorpora la opción `--hasta t` a la herramienta de reproducción desatendida `--replay <PARTIDA.log>`, permitiendo acotar la simulación de una partida grabada hasta un instante virtual específico $t$ y exhibir el estado exhaustivo alcanzado (FR-401, FR-404).

El enfoque técnico, respaldado y justificado en [research.md](research.md):

1. **Tope en el ciclo de eventos (Opción b)**: Se añade un parámetro opcional `tope: int | None` en `EstadoJuegoLogica._avanzarHastaProximoTurno`. El ciclo se detiene sin desapilar cuando el próximo evento del reloj virtual tiene un tiempo estrictamente mayor que $t$ (FR-402). El corte es inclusivo (FR-403): todos los eventos programados en $t$ se procesan.
2. **Corte anticipado de lectura del log**: Cuando el tope de tiempo interrumpe el ciclo de eventos o la partida termina, `EstadoJuegoLogica.repetirPartida` cesa la lectura de acciones del log. Esto garantiza que el costo computacional sea proporcional al tiempo reproducido y no al tamaño total del archivo (FR-412).
3. **Invarianza de `--replay` base**: Si `tope is None`, el comportamiento es 100% idéntico al actual, preservando la compatibilidad regresiva completa (FR-409).
4. **Validación temprana y rechazo en CLI**: En `main.py`, la función validadora `_instante_hasta` y la verificación de precedencia rechazan valores negativos, valores no enteros o el uso huérfano de `--hasta` sin `--replay` antes de instanciar el servicio o acceder al disco (FR-407, FR-408, Principio IV).
5. **Separación MVC estricta**: La lógica devuelve un objeto de datos puro `ResultadoReplayHastaDTO` en `DTO/` con la información exhaustiva (sala, vida, llaves, objetos, enemigos con vida, fin de partida y log agotado). `main.py` se encarga de imprimirlo en consola sin que la lógica conozca la presentación (FR-404, Principio IV).
6. **Medición con `--bench`**: Se agrega el bloque `replay` en `bench/replay.py` con cargas sintéticas deterministas de 250, 1 000 y 4 000 acciones, midiendo la Opción b frente a las alternativas descartadas (a y c) y evaluando la proporcionalidad por conteo de eventos procesados (FR-412, FR-413, Principio VII).

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
| **II. Determinismo** | Mismo log, misma semilla y mismo $t$ producen siempre la misma partida y la misma salida (FR-411). El desempate de eventos en el reloj es estricto por `id_secuencia`. La lista de enemigos en sala se ordena deterministamente por nombre/id. | Pasa |
| **III. Equivalencia ante el reuso** | La reproducción acotada no reutiliza estado sucio ni arrastra cachés viejas. El estado resultante en $t$ es idéntico al prefijo de una ejecución completa (propiedad de prefijo). | Pasa |
| **IV. Separación MVC y adaptadores** | `EstadoJuegoLogica` y `EstadoJuegoServicio` retornan un `ResultadoReplayHastaDTO` puro. La presentación en consola se realiza exclusivamente en `main.py`. `--replay` con `--hasta` no inicializa componentes de vista interactiva (FR-410). | Pasa |
| **V. Sin datos de una cripta concreta** | No hay literales de salas, enemigos ni criptas específicas en el código. El sistema funciona con cualquier log y con partidas sintéticas de cualquier tamaño en `--bench`. | Pasa |
| **VI. Presupuesto de red y versiones** | La reproducción opera sin conexión y valida las versiones de cripta y catálogo declaradas en la cabecera del log sin realizar solicitudes de red. | Pasa |
| **VII. Rendimiento medido** | Bloque `replay` en `--bench` mide partidas sintéticas deterministas de 250, 1 000 y 4 000 acciones. Mide la Opción b frente a las alternativas descartadas a y c. El criterio duro se basa en conteo de eventos. | Pasa |
| **VIII. La especificación precede al código** | Cada decisión responde a un requisito funcional FR-4xx de `spec.md`. Se documentan hallazgos observados en la especificación. | Pasa |
| **IX. Trazabilidad** | Matriz exhaustiva FR-4xx → Escenario → Prueba automatizada en `quickstart.md`. | Pasa |
| **X. Cambios de especificación** | Los hallazgos se anotan como observaciones en este plan sin alterar las reglas de `spec.md`. | Pasa |
| **XI. Uso de LLM** | Comandos registrados con modelo y fecha en `PROMPTS_LLM_JP`. | Pasa |

---

## Observaciones y hallazgos para la especificación

1. **Incompatibilidad formal entre FR-406 ($t=0$) y FR-403 (corte inclusivo $\le t$)**:
   - FR-406 establece que si $t=0$, «no se ejecuta ningún evento y se muestra el estado inicial».
   - Sin embargo, FR-403 define que el límite es inclusivo y se ejecutan todos los eventos con tiempo virtual $\le t$. Dado que la primera acción del jugador en el log se programa e inicia en el instante virtual 0, una aplicación ciega de FR-403 ejecutaría dicha primera acción.
   - **Decisión del plan**: FR-406 actúa como una regla de guarda explícita: si $t=0$, la simulación se detiene inmediatamente antes de despachar cualquier acción o evento del log, mostrando el estado inicial puro. Para todo $t > 0$, rige plenamente el corte inclusivo de FR-403.
2. **Propiedad de prefijo vs. continuación en caliente (Historia 3, Escenario 2)**:
   - El escenario 2 de la Historia 3 menciona que «reproducir hasta t seguido de continuar da lo mismo que reproducir todo».
   - Dado que el modo `--replay` es un proceso por lotes de línea de comandos sin interfaz para pausar y reanudar interactivamente, la equivalencia se valida formalmente mediante la **propiedad de prefijo determinista**: el estado del juego obtenido al ejecutar hasta $t$ coincide exactamente con el estado alcanzado en el instante $t$ durante la reproducción completa del log.
3. **Criterio duro de proporcionalidad vs. umbral de tiempo (SC-003)**:
   - El criterio de tiempo del 60% en SC-003 puede presentar variaciones por carga del sistema operativo, recolección de basura (`gc`) o resolución del temporizador.
   - **Decisión del plan**: El criterio formal y determinista de aprobación en pruebas unitarias y benchmarks es el **conteo de eventos procesados y acciones ejecutadas**: para $t = T / 2$, el número de eventos procesados debe ser $\le 0.55 \times \text{eventos totales}$. La razón de tiempos de reloj se reporta como métrica informativa en `--bench`.

---

## Decisiones arquitectónicas y justificación por requisito

### D1. Tope opcional en el ciclo de eventos (`_avanzarHastaProximoTurno`)
- **Justificación**: Satisface **FR-402** (detención en $t$, exclusión de eventos $> t$) y **FR-403** (inclusión de eventos $\le t$). Al interrumpir el ciclo cuando el próximo evento supera $t$, se congela el avance en el instante exacto. Si `tope is None`, el comportamiento es invariante, satisfaciendo **FR-409**.
- **Descarte de alternativa a**: Cortar solo entre acciones del jugador permitiría que eventos de enemigos entre turnos se ejecuten más allá de $t$, violando FR-402.
- **Descarte de alternativa c**: Reproducir todo y recortar procesaría el 100% de los eventos, violando FR-412.

### D2. Validación temprana de argumentos en CLI
- **Justificación**: Satisface **FR-407** (rechazo de $t$ negativo o no entero con mensaje claro) y **FR-408** (rechazo de `--hasta` sin `--replay`). La validación se realiza mediante `_instante_hasta` en `main.py` antes de instanciar `EstadoJuegoServicio` ni cargar adaptadores (Principio IV).

### D3. DTO de salida desacoplado de la consola
- **Justificación**: Satisface **FR-404** (reporte exhaustivo de estado) y el **Principio IV** (separación MVC). `EstadoJuegoLogica` arma `ResultadoReplayHastaDTO` conteniendo: instante, acciones reproducidas, sala, vida, llaves, objetos, enemigos en la sala con sus vidas, estado de fin de partida y bandera de log agotado. `main.py` da formato de texto al DTO.

### D4. Tratamiento de registros sin costo temporal
- **Justificación**: Las acciones de cambio de cursor de inventario (`MOVER_CURSOR_SIGUIENTE`, `MOVER_CURSOR_ANTERIOR`) tienen costo 0. Se ejecutan en el instante actual si el reloj no ha superado el tope, asegurando que la selección del objeto activo coincida fielmente con lo registrado. Si el tope ya cortó la ejecución, no se procesan más registros.

### D5. Detección unívoca de fin de partida vs. log agotado
- **Justificación**: Satisface **FR-404** y **FR-405**. Si `self.fin` es verdadero, se informa `partida_terminada = True` con el motivo (muerte o victoria). Si el log concluye sin que la partida haya terminado y con el reloj antes de $t$, se informa `log_agotado = True` y se emite la advertencia requerida por FR-405.

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
- $K$: Cantidad de eventos del juego cuyo tiempo virtual es $\le t$ ($K \le N_{eventos\_totales}$).
- $M$: Cantidad de entidades activas simultáneamente en el montículo del `RelojVirtual` ($M \le 100$).

1. **Lectura y avance del ciclo**: Cada evento desapilado o programado en el montículo del reloj toma $O(\log M)$.
2. **Número de operaciones**: Al detenerse en el instante $t$, se procesan exactamente $K$ eventos. Los restantes $N_{eventos\_totales} - K$ eventos no se desapilan ni se ejecutan.
3. **Costo total**: $O(K \log M)$.
   - Dado que $M$ es pequeño y acotado, el costo es estrictamente proporcional a los eventos ocurridos hasta $t$, e **independiente del tamaño total del log $N$**, satisfaciendo FR-412.

### Complejidad espacial

- **Memoria adicional**: $O(1)$ más allá del estado regular del juego en memoria.
- No se almacenan historiales de retroceso de repetición ni buffers intermedios de salida.
- `ResultadoReplayHastaDTO` almacena únicamente el estado puntual en el instante $t$, ocupando $O(E + I)$ donde $E$ es la cantidad de enemigos en la sala actual ($E \le 10$) e $I$ la cantidad de objetos en inventario ($I \le 50$).
