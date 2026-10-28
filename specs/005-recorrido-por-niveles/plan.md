# Plan de implementación: Recorrido por niveles de la cripta

**Rama**: `005-recorrido-por-niveles` | **Fecha**: 2026-10-28 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/005-recorrido-por-niveles/spec.md` (FR-501 a FR-512, con las 2 clarificaciones de la sesión 2026-10-27)

## Resumen

Se construye un recorrido por niveles en `Logica/`, sin modificar todavía la precarga de vecinas ni la verificación de resolubilidad: por ahora **solo se construye, se prueba y se mide**. Las otras funciones lo adoptarán en capacidades posteriores.

El enfoque, justificado en [research.md](research.md):

1. **Esqueleto reutilizado**: el recorrido lee las aristas salientes de `MapaCripta` (capacidad 001). No pide nada a la red.
2. **Cola circular propia** sobre una `list`, que duplica su capacidad al llenarse. Nada de `deque` ni de `collections`.
3. **Visitados con marca de época**: dos listas indexadas por id de sala (marca y nivel), sin `dict` ni `set`. Un recorrido nuevo no limpia nada: incrementa la época.
4. **Orden dentro de cada nivel** (menor id, FR-502): cada nivel se ordena con `ordenar_adaptativo` del repositorio. Es necesario porque el orden de descubrimiento sigue el orden de los padres, no el de los ids (ejemplo en `research.md` §4).
5. **Criterio de transitabilidad** (FR-507): quien pide el recorrido pasa una función que recibe cada salida y dice si es transitable; sin función, valen todas.
6. **Mediciones con `--bench`**: bloque nuevo `recorrido` con recorrido acotado frente a sin límite al crecer la cripta, y la cola circular frente a la alternativa descartada, en criptas de frontera angosta y de frontera ancha.

## Contexto técnico

**Lenguaje/versión**: Python 3.11+ (el del proyecto).

**Dependencias principales**: ninguna nueva. Solo código del repositorio: `MapaCripta` (capacidad 001) y `Logica/ordenamiento.py`.

**Almacenamiento**: ninguno. El recorrido es una función pura sobre el esqueleto ya construido.

**Pruebas**: `unittest`, convención del repositorio (`test_*.py` en la raíz, ayudas en `tests_labs/`). Se reutilizan los generadores de criptas de `tests_labs/cripta_sintetica.py`.

**Plataforma**: consola, multiplataforma.

**Tipo de proyecto**: aplicación de consola por capas. Esta capacidad agrega módulos a la capa de lógica y no toca la vista, el controlador ni los adaptadores.

**Objetivos de rendimiento** (FR-510, SC-004): costo proporcional a las salas y salidas visitadas; un recorrido de 2 niveles en una cripta de 40 000 salas toma a lo sumo el doble que en una de 400.

**Restricciones**: sin `dict`/`set` como índice, sin `heapq`/`bisect`/`collections`/bibliotecas de grafos; sin `list.sort()` ni `sorted()` para ordenar lo evaluado (convención del repositorio, `bench/ordenamiento.py`). El modelo no importa red, disco ni vista. Sin ids ni tamaños de una cripta concreta.

**Escala/alcance**: criptas sintéticas de 400 a 40 000 salas; recorridos de 1 sala a toda la cripta.

## Verificación de la constitución

*Compuerta: debe pasar antes de la investigación (Fase 0) y se reevalúa tras el diseño (Fase 1).*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Estructuras propias | Cola circular y visitados escritos a mano sobre `list`; orden por `ordenar_adaptativo`. Sin `dict`/`set`, `deque`, `heapq`, `bisect`, `collections` ni `sorted()`. Las alternativas con montículo reutilizan `MonticuloMinimo` (propio). | Pasa |
| II. Determinismo | Sin azar ni dependencia del orden de iteración de contenedores: el orden sale de los ids. Dos recorridos iguales dan la misma secuencia (FR-509). | Pasa |
| III. Equivalencia ante el reuso | El recorrido **no reutiliza resultados** entre llamadas. Solo reutiliza buffers (marcas de época), que no cambian el resultado; una prueba compara contra un recorrido de referencia ingenuo. | Pasa |
| IV. MVC y adaptadores | Vive en `Logica/`, recibe `MapaCripta` ya construido, no importa red, disco ni vista. `--bench` no instancia la vista. | Pasa |
| V. Sin datos de una cripta | Las listas se dimensionan con `MapaCripta.tamano`. Ningún id ni tamaño fijo. | Pasa |
| VI. Presupuesto y versiones | 0 solicitudes. No persiste nada: no cambia ningún formato ni versión. | Pasa |
| VII. Rendimiento medido | Bloque `recorrido` de `--bench` con la alternativa descartada y los tamaños de SC-004. Si una medición contradice la decisión, se cambia y se documenta el antes y el después. | Pasa |
| VIII. Especificación primero | Este plan no agrega reglas. Hallazgos que afectan a la especificación, abajo. | Pasa con observaciones |
| IX. Trazabilidad | Matriz FR-5xx → prueba en `quickstart.md`. | Pasa |
| X. Cambios de especificación | Se corrige primero la especificación, en commit aparte, si la implementación lo exige. | Pasa |
| XI. Uso de LLM | Registrar este `/speckit-plan` y los siguientes en `PROMPTS_LLM.md`. | Acción del grupo |

### Observaciones y hallazgos

1. **La cola circular y el orden por nivel se solapan.** Como cada nivel se ordena antes de procesarse, la cola solo contiene un nivel a la vez: hace el papel de «nivel actual» y una lista auxiliar acumula «el nivel siguiente». Es válido y es lo que se pidió, pero una alternativa que intercambia dos listas por nivel (sin cola) hace lo mismo con menos piezas. El plan mantiene la cola circular como decisión y **mide las dos**; si la alternativa gana, se cambia y se documenta (principio VII). Detalle en `research.md` §3.
2. **Existe un recorrido previo, `ServicioCripta.salas_vecinas`**, que usa `deque` y busca repetidos con `in` sobre una lista (lineal). No se toca en esta capacidad. Se incluye en el bench como referencia de «lo que hay hoy». Retirarlo es parte de la capacidad que adopte el recorrido.
3. **Costos de salida ignorados**: el nivel cuenta salidas, no costos (supuesto de la especificación). El recorrido lee solo destino y dirección de `MapaCripta`.
4. **SC-004 puede ser frágil**: «a lo sumo el doble» al pasar de 400 a 40 000 salas depende del comportamiento de la memoria en Python. Si la medición lo contradice, la corrección va primero a `spec.md` (principio X), no al código.

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/005-recorrido-por-niveles/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones, alternativas con razón concreta, complejidad
├── data-model.md        # Fase 1: entidades, campos, validaciones
├── quickstart.md        # Fase 1: validación y matriz de trazabilidad
├── contracts/
│   ├── interfaz-recorrido.md   # cómo se pide un recorrido y qué devuelve
│   └── bench-recorrido.md      # secciones y criterios de --bench
├── checklists/requirements.md
└── tasks.md             # Lo genera /speckit-tasks (no este comando)
```

### Código fuente (raíz del repositorio)

```text
DTO/
└── RecorridoDTO.py            # NUEVO: salas visitadas y su nivel, en orden

Logica/
├── ColaCircular.py            # NUEVO: cola sobre list que crece al llenarse
├── RecorridoPorNiveles.py     # NUEVO: el recorrido (marcas de época, orden por nivel, límite, transitabilidad)
└── MapaCripta.py              # MODIFICADO (mínimo): indica qué ids existen en el esqueleto

bench/
├── recorrido.py               # NUEVO: bloque "recorrido"
└── __init__.py                # registra el bloque

test_cola_circular.py          # NUEVO: la cola y su cumplimiento del principio I
test_recorrido_por_niveles.py  # NUEVO: escenarios de la especificación, equivalencia con una referencia, determinismo
tests_labs/
└── referencia_recorrido.py    # NUEVO: recorrido ingenuo de referencia para las pruebas (no se usa en el juego)
```

**No se modifican**: `adaptadores/servicioCripta.py` (`salas_vecinas`, `precargar_vecinas`), la verificación de resolubilidad (capacidad futura), el controlador, la vista ni el guardado.

**Decisión de estructura**: el recorrido es un servicio de la capa de lógica que recibe un `MapaCripta` y no sabe de dónde salió. Se mantienen las capas de la Parte I.

## Complejidad de las operaciones más frecuentes

*V = salas visitadas, E = salidas examinadas (las de las salas visitadas con nivel menor que el límite), a = ancho del nivel más ancho. N = salas de la cripta.*

| Operación | Costo | Nota |
|---|---|---|
| Agregar / sacar de la cola circular | O(1) amortizado | Al llenarse se duplica la capacidad: copia O(a), que se reparte entre las inserciones |
| ¿Visitada esta sala? / marcarla | O(1) | Comparar o escribir la marca de época en una lista indexada por id |
| Reiniciar los visitados entre recorridos | O(1) | Se incrementa la época; no se limpia nada |
| Examinar las salidas de una sala | O(grado) | El grado máximo es 4 (N, S, E, O) |
| Ordenar un nivel de m salas | O(m²) con m ≤ 15 (inserción); O(m log m) por encima (mezcla) | `ordenar_adaptativo`, estable |
| **Un recorrido completo** | **O(V + E + Σ m·log m)** ≈ O(V log a) | Independiente de N; las listas se reservan una vez por mapa, fuera del recorrido |
| Preparar el recorridor para un mapa | O(N), una sola vez | Dos listas de tamaño `MapaCripta.tamano` |

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar.

| Decisión que podría parecer compleja | Por qué se necesita | Alternativa más simple descartada |
|---|---|---|
| Ordenar cada nivel con `ordenar_adaptativo` | FR-502 exige menor id dentro del nivel y el orden de descubrimiento no lo da | No ordenar: incumple FR-502. Ver `research.md` §4 |
