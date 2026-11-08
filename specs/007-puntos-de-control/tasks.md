# Tareas: Puntos de control de la partida (007-puntos-de-control)

**Entrada**: Documentos de diseño en `specs/007-puntos-de-control/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/formato-partida-v7.md`, `quickstart.md`).

**Prerrequisitos**: `plan.md` y `spec.md` (con todas las clarificaciones resueltas e integradas). La capacidad se construye sobre el código existente de la Parte I y II: `main.py`, `Servicio/EstadoJuegoServicio.py`, `Logica/EstadoJuegoLogica.py`, `Logica/EstadoGuardadoLogica.py`, `adaptadores/AlmacenPartidaBinario.py` y `bench/`.

**Pruebas**: Se incluyen en todas las historias de usuario porque la Constitución (Principio IX) exige que cada escenario de aceptación tenga una prueba automatizada. Cada prueba se escribe **antes** del código y debe fallar primero.

**Organización**: Tareas agrupadas por historia de usuario en orden de prioridad. Cada tarea indica entre paréntesis los requisitos funcionales que atiende.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: Se puede ejecutar en paralelo (archivos distintos, sin dependencia de tareas incompletas).
- **[USn]**: Historia de `spec.md` a la que pertenece ([US1], [US2], [US3], [US4], [US5]).
- Las rutas son relativas a la raíz del repositorio. Las pruebas usan `unittest`.

## Reglas para todas las tareas (Constitución)

- **No usar** `dict` ni `set` como índice, caché o tabla de búsqueda; ni `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` ni bibliotecas de grafos (Principio I). Se permiten `list` como almacenamiento contiguo, `struct`, `json`, `requests` y `dataclass`.
- Ningún id de sala o entidad, cantidad de páginas, presupuesto ni estadística de una cripta concreta en el código de producción (Principio V).
- El modelo (`Logica/`, `DTO/`) no importa red, disco ni vista ni escribe en la consola (Principio IV).
- Las opciones `--replay` y `--bench` no instancian la vista interactiva (Principio IV).
- La toma de puntos de control no consume solicitudes de red ni altera las decisiones o el azar de la partida (Principio II, Principio VI, FR-423).

---

## Phase 1: Setup (Shared Infrastructure)

**Propósito**: Verificación constitucional previa y soporte de pruebas sintéticas.

- [ ] T001 Revisar `plan.md` y este `tasks.md` contra la lista de estructuras prohibidas del principio I de la constitución (sin `heapq`, `bisect`, `collections`, `networkx` ni `dict`/`set` como índice/caché) y anotar el resultado en `specs/007-puntos-de-control/checklists/requirements.md`. (Principio I)
- [ ] T002 [P] Crear el módulo de apoyo para pruebas sintéticas en `tests/fixtures_puntos_control.py` para construir estados y partidas deterministas parametrizables por semilla (`semilla=2026`) con secuencias conocidas de acciones. (Principio II, FR-421)

**Punto de control**: Verificación de estructuras anotada y fixtures listos para las pruebas.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Propósito**: Componentes base de datos, DTOs y validación de tipos requeridos por todas las historias de usuario.

- [ ] T003 [P] Crear `DTO/PuntoControlDTO.py` con los campos exactos de `data-model.md`: `numero_punto: int`, `acciones_linea_tiempo: int`, `instante_reloj: int` y `estado: EstadoGuardadoDTO`, inmutable (`frozen=True`). (FR-421, Principio I, Principio IV)
- [ ] T004 [P] Implementar la función validadora `_intervalo_checkpoint(texto: str) -> int` en `main.py` para rechazar enteros menores que 1, flotantes o no numéricos con `argparse.ArgumentTypeError("el intervalo entre puntos de control debe ser un entero mayor o igual que 1")`. (FR-414, FR-415, FR-417)
- [ ] T005 Inicializar los atributos `self.acciones_linea_tiempo: int = 0`, `self.k_checkpoint: int = 10` y `self.puntos_control: list[PuntoControlDTO] = []` en `Logica/EstadoJuegoLogica.py` sin alterar el contador acumulativo de puntaje `self.accionesJugador`. (FR-414, FR-416, FR-418, Principio I)

**Punto de control**: `PuntoControlDTO` importable, validador de CLI listo y atributos base definidos en la lógica.

---

## Phase 3: User Story 1 — Configurar el intervalo entre puntos de control (Priority: P1) 🎯 MVP

**Meta**: Aceptar la bandera `--checkpoint-cada K`, validar tempranamente con código 2 ante valores inválidos, usar valor por defecto e informar $K$ antes de la primera decisión.

**Prueba independiente**: Lanzar la aplicación con distintos valores de K (válidos, cero, negativos, decimales, texto) comprobando arranque o rechazo sin tocar disco.

### Pruebas para User Story 1 (escribir primero; deben fallar)

- [ ] T006 [P] [US1] Crear `tests/test_cli_checkpoint.py` con pruebas para validación de `--checkpoint-cada`: valores válidos (ej. 1, 10), valores inválidos (0, negativos, decimales, texto) saliendo con código 2 sin inicializar servicios ni tocar disco, y verificación del reporte inicial del valor vigente de K antes de la primera decisión. (FR-414, FR-415, FR-416, FR-417, SC-006)

### Implementación de User Story 1

- [ ] T007 [US1] Añadir el argumento `--checkpoint-cada` con `type=_intervalo_checkpoint` en `leer_argumentos()` en `main.py` y propagarlo a `EstadoJuegoServicio` y `EstadoJuegoLogica.k_checkpoint`. (FR-414, FR-415, FR-417)
- [ ] T008 [US1] Añadir en `main.py` y `ControladorJuego` el mensaje informativo que reporta el valor vigente de $K$ (configurado o por defecto) antes de que el jugador tome su primera decisión. (FR-416, SC-006)
- [ ] T009 [US1] Ejecutar `python -m unittest tests/test_cli_checkpoint.py` y verificar que todos los escenarios de aceptación de la Historia 1 pasan exitosamente. (FR-414 a FR-417, SC-006)

**Punto de control**: La Historia 1 (MVP) funciona y pasa sus pruebas unitarias e integradas de forma independiente.

---

## Phase 4: User Story 2 — Tomar puntos de control durante la partida (Priority: P1)

**Meta**: Capturar automáticamente el punto 0 al iniciar, capturar puntos periódicos cada $K$ acciones al completarse el turno del jugador (estado previo a la decisión $n \times K + 1$ sin fin de partida), y podar puntos posteriores al revertir con pergamino de retroceso.

**Prueba independiente**: Ejecutar una partida simulada y verificar la presencia de puntos de control exactamente en los múltiplos de K, la transparencia en consola y el descarte tras uso de pergamino.

### Pruebas para User Story 2 (escribir primero; deben fallar)

- [ ] T010 [P] [US2] Crear `tests/test_puntos_control.py` con pruebas para: captura automática del punto 0 en `iniciarJuego` (FR-418); captura periódica exacta en múltiplos de $K$ al completarse el turno del jugador y verificando que no se toma si la acción causó fin de partida (FR-418, FR-419); transparencia sin mensajes en consola (FR-420); contenido exhaustivo de `PuntoControlDTO.estado` incluyendo estado de generador aleatorio y reloj (FR-421); y descarte de puntos de control posteriores tras uso de pergamino (FR-418).

### Implementación de User Story 2

- [ ] T011 [US2] Implementar el método privado `_capturarPuntoControlInicial(self)` en `Logica/EstadoJuegoLogica.py` e invocarlo en `iniciarJuego()` para registrar el punto de control 0 con `acciones_linea_tiempo = 0` y estado completo desconectado. (FR-418, FR-421)
- [ ] T012 [US2] Implementar `_verificarYCapturarPuntoControl(self)` en `Logica/EstadoJuegoLogica.py`, integrándolo al final de `accionJugador()` tras `_avanzarHastaProximoTurno()` y `_registrarAccionEnLog()`, verificando `not self.fin` y `self.acciones_linea_tiempo % self.k_checkpoint == 0`. (FR-418, FR-419, FR-420)
- [ ] T013 [US2] Modificar la rama de `GestorEventos.es_uso_de_pergamino` en `Logica/EstadoJuegoLogica.py`: tras ejecutar el retroceso, decrementar `self.acciones_linea_tiempo` e invocar `_podarPuntosControlPosteriores(self, self.acciones_linea_tiempo)` para eliminar con `pop()` los puntos con `acciones > self.acciones_linea_tiempo`. (FR-418, Principio I)
- [ ] T014 [US2] Implementar el método de lectura `obtenerPuntoControlReciente(self, k: int) -> PuntoControlDTO | None` en `Logica/EstadoJuegoLogica.py` que recorre en sentido inverso `self.puntos_control` para encontrar el último punto con `acciones_linea_tiempo <= k`. (FR-419, Principio I)
- [ ] T015 [US2] Ejecutar `python -m unittest tests/test_puntos_control.py` y verificar que todos los escenarios de la Historia 2 pasan exitosamente. (FR-418 a FR-421)

**Punto de control**: Captura periódica, punto inicial y poda por pergamino funcionando correctamente.

---

## Phase 5: User Story 3 — Reproducibilidad desde un punto de control (Priority: P1)

**Meta**: Demostrar que reanudar la partida desde cualquier punto de control produce exactamente el mismo resultado y `partida.log`, y que la partida es invariante ante distintos valores de $K$.

**Prueba independiente**: Reanudar desde puntos de control sobre partidas conocidas y comparar `partida.log` línea a línea; correr la misma partida con $K=1$, $K=10$ y $K=1000$ verificando desenlaces idénticos.

### Pruebas para User Story 3 (escribir primero; deben fallar)

- [ ] T016 [P] [US3] Crear `tests/test_determinismo_puntos_control.py` con pruebas de: reanudación desde punto de control $n$ con idénticas acciones generando exactamente el mismo `partida.log` y estado final (FR-422, Principio II); y ejecución de la misma partida con diferentes valores de $K$ (ej. $K=1$, $K=10$, $K=100$, y $K > N$) verificando que el resultado final y los desempates aleatorios son 100% idénticos (FR-423).

### Implementación de User Story 3

- [ ] T017 [US3] Implementar en `Logica/EstadoJuegoLogica.py` el método `restaurarDesdePuntoControl(self, punto: PuntoControlDTO)` que reestablece el estado completo mediante `EstadoGuardadoLogica.restaurar(self, punto.estado)`, actualiza `self.acciones_linea_tiempo = punto.acciones_linea_tiempo` y preserva la lista de puntos de control hasta dicho punto. (FR-422, Principio II, Principio III)
- [ ] T018 [US3] Adaptar `Servicio/EstadoJuegoServicio.py` para exponer la reanudación desde punto de control y asegurar que `--replay` procesa la partida con la contabilización transparente de $K$ sin alterar el desenlace. (FR-422, FR-423, Principio IV)
- [ ] T019 [US3] Ejecutar `python -m unittest tests/test_determinismo_puntos_control.py` y verificar que todos los escenarios de la Historia 3 pasan exitosamente. (FR-422, FR-423)

**Punto de control**: Reproducibilidad determinista e invarianza de desenlace demostradas.

---

## Phase 6: User Story 4 — Guardar y cargar una partida conserva sus puntos de control (Priority: P2)

**Meta**: Persistir los puntos de control en el archivo binario v7 (`VERSION_FORMATO = 7`), mantenerlos al recargar respetando la precedencia de $K$, y rechazar explícitamente archivos v6 o anteriores con `ErrorPartida`.

**Prueba independiente**: Guardar una partida con puntos de control, cerrar, recargar y verificar puntos; intentar cargar archivo v6 y comprobar rechazo explícito con mensaje descriptivo.

### Pruebas para User Story 4 (escribir primero; deben fallar)

- [ ] T020 [P] [US4] Crear `tests/test_persistencia_v7.py` con pruebas para: serialización y deserialización de partidas con puntos de control en `AlmacenPartidaBinario` v7 (FR-424); verificación de que al cargar una partida sin `--checkpoint-cada` se conserva el $K$ del archivo, y con bandera explícita rige el nuevo $K$ para acciones futuras preservando los puntos previos (FR-424); y comprobación de que archivos guardados con versión 6 o de la Parte I son rechazados con mensaje claro de incompatibilidad (FR-425).

### Implementación de User Story 4

- [ ] T021 [US4] Actualizar `adaptadores/AlmacenPartidaBinario.py` a `VERSION_FORMATO = 7`: implementar la serialización de `k_checkpoint`, `acciones_linea_tiempo` y el bloque contenedor indexado de `puntos_control` según `contracts/formato-partida-v7.md`. (FR-424)
- [ ] T022 [US4] Implementar en `adaptadores/AlmacenPartidaBinario.py` la deserialización del bloque de puntos de control y el rechazo explícito con `ErrorPartida` cuando `version != 7`, emitiendo mensaje descriptivo que menciona incompatibilidad con versión 7. (FR-424, FR-425, Principio VI)
- [ ] T023 [US4] Integrar en `Servicio/EstadoJuegoServicio.py` y `ControladorJuego` la lógica de carga: si `--checkpoint-cada` fue provisto explícitamente en CLI, asignar el nuevo $K$ al estado restaurado; si no, mantener el $K$ cargado desde el archivo v7. (FR-424)
- [ ] T024 [US4] Ejecutar `python -m unittest tests/test_persistencia_v7.py` y verificar que los escenarios de la Historia 4 pasan al 100%. (FR-424, FR-425)

**Punto de control**: Persistencia binaria v7 funcional y rechazo de versiones anteriores verificado.

---

## Phase 7: User Story 5 — Rendimiento transparente y benchmarking (Priority: P2)

**Meta**: Medir que el ciclo de eventos en instantes con punto de control no supera 20 ms con $K=1$, evaluar el consumo de memoria a 5 000 acciones, comparar alternativas de historiales y derivar empíricamente el valor por defecto de $K$.

**Prueba independiente**: Ejecutar `python main.py --bench puntos_control` y verificar el límite de 20 ms y las tablas de resultados.

### Pruebas para User Story 5 (escribir primero; deben fallar)

- [ ] T025 [P] [US5] Crear `bench/test_bench_puntos_control.py` para verificar que el bloque de benchmark `puntos_control` se ejecuta sin errores, genera métricas válidas en consola y en archivo CSV opcional, y reporta tiempos por debajo del umbral de 20 ms en partidas sintéticas deterministas. (FR-426, Principio VII)

### Implementación de User Story 5

- [ ] T026 [US5] Crear el módulo de benchmark `bench/puntos_control.py` con cargas sintéticas deterministas por semilla (`semilla=2026`) para $K \in \{1, 10, 50, 100\}$: medir tiempo de captura de punto, tiempo del ciclo de eventos con y sin punto, tamaño de archivo / memoria a 5 000 acciones, y pasos necesarios hasta una acción $k$. (FR-426, SC-004, Principio VII)
- [ ] T027 [US5] Implementar en `bench/puntos_control.py` la comparación con las alternativas descartadas: Alternativa A (copia completa exhaustiva de bitácora y log de acciones) vs Alternativa B (instantánea de estado con marca de longitud en historiales append-only) vs Alternativa C (sin puntos de control = reproducir desde cero). (FR-426, Principio VII)
- [ ] T028 [US5] Registrar el bloque `("puntos_control", puntos_control.ejecutar)` en `BLOQUES` de `bench/__init__.py` para habilitar `--bench puntos_control`. (FR-426)
- [ ] T029 [US5] Ejecutar `python main.py --bench puntos_control` y verificar el cumplimiento del límite de 20 ms con $K=1$ en la cripta sintética de referencia. (FR-426, SC-004)

**Punto de control**: Benchmark implementado y umbrales de rendimiento validados con datos.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Propósito**: Trazabilidad final, documentación de decisiones y registro en bitácoras de prompts.

- [ ] T030 [P] Actualizar `specs/007-puntos-de-control/checklists/requirements.md` confirmando la verificación de todos los requisitos y la trazabilidad de pruebas. (Principio IX)
- [ ] T031 Documentar los resultados del benchmark, la comparación con la alternativa descartada y la justificación del $K$ por defecto en `DECISIONES.md` (§007). (Principio VII)
- [ ] T032 Registrar el comando `/speckit-tasks` y los comandos de implementación en `PROMPTS_LLM_JP.md` y `PROMPTS_LLM.md` con herramienta y modelo reales (`Gemini 3.8 Flash`). (Principio XI)
- [ ] T033 Ejecutar la suite completa de pruebas del proyecto (`python -m unittest discover -s tests`) para garantizar que ninguna funcionalidad preexistente sufrió regresiones.

---

## Dependencias y Orden de Ejecución

### Dependencias entre fases
1. **Setup (Fase 1)**: Sin dependencias, se puede iniciar de inmediato.
2. **Foundational (Fase 2)**: Depende de la Fase 1. Bloquea todas las historias de usuario.
3. **Historias de Usuario (Fases 3 a 7)**:
   - **User Story 1 (Fase 3 - MVP)**: Depende de Fase 2.
   - **User Story 2 (Fase 4)**: Depende de Fase 2 y Fase 3.
   - **User Story 3 (Fase 5)**: Depende de Fase 4.
   - **User Story 4 (Fase 6)**: Depende de Fase 4 y Fase 5.
   - **User Story 5 (Fase 7)**: Depende de Fase 4, 5 y 6.
4. **Polish (Fase 8)**: Depende de la finalización de todas las historias de usuario.

### Oportunidades de ejecución paralela
- T002, T003 y T004 se pueden ejecutar en paralelo al inicio.
- Cada prueba de historia ([P]) se escribe en paralelo antes de la implementación de esa historia.
- Las tareas T010, T016, T020 y T025 pueden redactarse en paralelo una vez completada la fase fundacional.

---

## Estrategia de Implementación

### MVP Primero (User Story 1)
1. Completar Setup y Foundational (T001..T005).
2. Implementar User Story 1 (T006..T009): bandera `--checkpoint-cada`, validación de CLI y reporte inicial.
3. **Validar MVP**: Comprobar que `--checkpoint-cada` valida correctamente los parámetros en consola.

### Entrega Incremental
1. Añadir User Story 2 (T010..T015): captura periódica, punto inicial y poda por pergamino.
2. Añadir User Story 3 (T016..T019): determinismo y reproducibilidad idéntica.
3. Añadir User Story 4 (T020..T024): formato v7 y rechazo explícito de versiones anteriores.
4. Añadir User Story 5 (T025..T029): benchmark y medición de 20 ms.
5. Finalizar con Polish y verificación global (T030..T033).
