# Investigación técnica: Línea de tiempo — consulta de estados pasados

**Capacidad**: `004-linea-de-tiempo` (FR-427 a FR-443)  
**Fecha**: 2026-11-08  
**Autor**: Equipo de Desarrollo Cripta  

Este documento consolida las investigaciones, evaluaciones arquitectónicas y decisiones de diseño técnico para la capacidad de consulta de estados pasados (`historia <t>` e `historia #k`), fundamentadas en los principios de la Constitución de Cripta (especialmente Principios I, II, III, IV y VII).

---

## Decisión 1: Reconstrucción aislada del estado histórico

### Contexto del problema
La consulta `historia` debe reconstruir y exhibir el estado exacto de la partida en cualquier instante $t$ o acción $k$ del pasado sin alterar en lo más mínimo la partida en curso (FR-432, SC-005). La partida viva tiene un reloj virtual avanzado, un inventario, un log abierto en disco, una bitácora y una estructura de retroceso activa.

### Riesgos identificados y mitigaciones
1. **Singleton global de `RetrocesoLogica`**:
   - *Riesgo*: `RetrocesoLogica` implementa el patrón singleton (`_instancia`). Tanto `iniciarJuego` como `EstadoGuardadoLogica.restaurar` invocan `retroceso.reiniciar()`, lo cual borra la cabeza, cola, reloj, contador de acciones y suspensiones. Si una instancia de reconstrucción llama a restaurar o reiniciar, destruiría el historial del pergamino de la partida viva.
   - *Solución*: Envolver la reconstrucción en un bloque `try ... finally` que captura una instantánea completa de las variables de estado del singleton (`cabeza`, `cola`, `actual`, `reloj`, `cantidad_actual`, `cantidad_acciones`, `tiempo_evento`, `suspensiones`) y la referencia `self.estadoJuego.reloj.retroceso`. En la cláusula `finally`, se restauran exactamente todos estos atributos en el singleton y se vuelve a asociar al reloj de la partida viva.
2. **Determinismo del azar (`GestorEventos.azar`)**:
   - *Riesgo*: Si la reconstrucción utilizara el generador de números pseudoaleatorios de la partida viva, consumiría pasos de la secuencia determinista, desincronizando los eventos futuros del juego vivo.
   - *Solución*: Cada punto de control (`PuntoControlDTO`) guarda el estado serializado del azar (`estado_azar = [azar[0], list(azar[1]), azar[2]]`). Al restaurar el punto en la instancia aislada (`EstadoGuardadoLogica.restaurar`), se crea una nueva instancia de `GestorEventos` con su propio `azar` restaurado mediante `setstate()`. La partida viva nunca comparte ni avanza su generador durante la consulta.
3. **Presupuesto y consumo de red**:
   - *Riesgo*: La reconstrucción podría disparar peticiones HTTP o fallar por presupuesto (FR-440, Principio VI).
   - *Solución*: La instancia aislada reutiliza el adaptador `comunicacion` ya existente en la partida viva, el cual ya mantiene en su caché LRU local todas las salas, descripciones y catálogo descargados al inicio. No se piden llaves adicionales (`pedir_llaves=False`). El contador de solicitudes de red antes y después de `consultarHistoria` debe ser idéntico (delta = 0).
4. **Efectos colaterales (disco, log, bitácora, reloj)**:
   - *Solución*: La instancia aislada se configura explícitamente con `registrador_log = None` (no escribe archivos en `logs/`), `_es_repeticion = True` (inhibe la captura automática de puntos de control con `_verificarYCapturarPuntoControl`), y opera en un espacio de memoria completamente independiente. La partida viva no avanza su reloj ni altera su bitácora.

### Alternativas consideradas
- **Alternativa A (Clonado superficial de la lógica viva)**: Descartada porque los objetos internos (jugador, salas, reloj, cola de eventos) están interconectados y mutan durante el avance; un clon superficial causaría corrupción cruzada de memoria.
- **Alternativa B (Segunda instancia aislada hidratada desde punto de control con guarda en singleton)**: **Elegida**. Garantiza aislamiento absoluto sin costo de I/O ni fugas de estado.

---

## Decisión 2: Búsqueda binaria manual del punto de control

### Contexto del problema
`EstadoJuegoLogica.obtenerPuntoControlReciente(k)` implementaba un recorrido lineal inverso (`for punto in reversed(self.puntos_control)`). Para partidas de 5 000 acciones con $K = 10$, la lista contiene más de 500 puntos. Un recorrido lineal es $O(M)$, mientras que una búsqueda binaria es $O(\log M)$.

### Restricción constitucional (Principio I)
El Principio I prohíbe taxativamente el uso de `bisect`, `dict`, `set` o `collections` como índice o estructura de búsqueda.

### Solución adoptada
Implementar algoritmos propios de búsqueda binaria sobre la lista contigua `self.puntos_control`:
1. `_buscarPuntoPorAcciones(k: int) -> PuntoControlDTO | None`: Encuentra el último punto con `acciones_linea_tiempo <= k`.
2. `_buscarPuntoPorInstante(t: int) -> PuntoControlDTO | None`: Encuentra el último punto con `instante_reloj <= t`.

```python
def _buscarPuntoPorAcciones(self, k: int) -> PuntoControlDTO | None:
    izq, der = 0, len(self.puntos_control) - 1
    candidato = None
    while izq <= der:
        medio = (izq + der) // 2
        if self.puntos_control[medio].acciones_linea_tiempo <= k:
            candidato = self.puntos_control[medio]
            izq = medio + 1
        else:
            der = medio - 1
    return candidato
```

### Justificación de monotonía
- El punto inicial 0 tiene `acciones = 0` e `instante = 0`.
- Cada punto posterior se añade cuando `acciones - ultimo.acciones >= K >= 1`. Dado que toda acción incrementa `acciones_linea_tiempo` en 1 y consume al menos 1 unidad de tiempo virtual, ambos campos son estrictamente crecientes.
- El uso del pergamino poda el sufijo de puntos con `acciones > límite` mediante `pop()`, preservando intacta la monotonicidad estricta del prefijo remanente.
- Complejidad temporal: $O(\log M)$, donde $M \le N / K + 1$. Para $N=5\,000$ y $K=10$, $M \le 501$, requiriendo a lo sumo 9 comparaciones.

### Alternativas consideradas
- **Alternativa A (Recorrido lineal inverso existente)**: $O(M)$. En el peor caso (consultar instantes cercanos al inicio de la partida), recorre 500 elementos. Descartada por ineficiente.
- **Alternativa B (Búsqueda binaria escrita a mano)**: **Elegida**. Cumple con el Principio I, garantiza $O(\log M)$ y respeta el almacenamiento contiguo en lista de Python.

---

## Decisión 3: Semántica de reconstrucción para `historia <t>` e `historia #k`

### Semántica y algoritmo
Ver `plan.md` sección 3 (reconstrucción por segmento vigente). Puntos clave: el log conserva revertidas y pergamino; se obtiene la línea vigente con una pila local sobre el segmento entre dos puntos de control; la reproducción es fiel (aplica todo, porque el pergamino no restaura el azar) y la parada se decide solo sobre acciones vigentes. `#1` = estado inicial; `#N+1` = estado vivo; `#>N+1` y `<t>` futuro se rechazan.

### Tabla de instantes por acción no requerida
No se necesita una tabla auxiliar indexada de `acción -> instante`: la lista de puntos de control y el log determinista permiten alcanzar directamente cualquier acción $k$ contando las decisiones del jugador aplicadas desde el punto base. La monotonicidad garantiza que no hay ambigüedades.

---

## Decisión 4: Invariante del pergamino de retroceso y poda de puntos

- Al usar un pergamino, `acciones_linea_tiempo` baja en 1 y se llama a `_podarPuntosControlPosteriores`. Todo punto superviviente tiene `acciones_linea_tiempo <= contador vigente`; por tanto las acciones que el pergamino revierte son siempre posteriores a cualquier punto superviviente.
- El log **no** se trunca: conserva las acciones revertidas y el registro de cada uso de pergamino. La línea vigente de un segmento se obtiene con una pila local (push por acción, pop por pergamino).
- Reproducir el segmento completo y fiel desde el punto base (con el retroceso vivo de la instancia aislada) es correcto porque cada pergamino del segmento revierte una acción del mismo segmento, y mantiene el azar idéntico al de la partida viva (el pergamino no restaura el azar).
- El punto 0 nunca se poda.

## Decisión 5: Reconstrucción hacia adelante vs. hacia atrás (§5.5)

### Comparación técnica
1. **Reconstrucción hacia atrás (deshacer cambios con historial del pergamino)**:
   - `RetrocesoLogica.MAX_HISTORIAL = 5`. El pergamino únicamente almacena deltas reversibles de las últimas 5 acciones para mantener acotada la memoria en tiempo de ejecución.
   - Si una consulta `historia` solicita un estado de hace 10, 50 o 1 000 acciones atrás, el historial de retroceso simplemente no tiene la información (fue descartada por la política FIFO del historial).
   - Para permitir retroceso arbitrario hacia atrás, habría que guardar un historial inverso infinito ($O(N)$ deltas), registrando cada mutación de vida, movimiento de enemigos, generación de objetos y cambios de agenda del reloj, multiplicando el uso de memoria por un factor inaceptable.
2. **Reconstrucción hacia adelante desde puntos de control (enfoque adoptado)**:
   - Almacena una instantánea compacta cada $K$ acciones.
   - Para cualquier consulta en una partida de $N$ acciones, se localiza el punto en $O(\log(N/K))$ y se avanzan como máximo $K - 1$ acciones hacia adelante.
   - El peor caso de avance está estrictamente acotado por $K - 1$ acciones, independientemente de que $N = 5\,000$ o $N = 50\,000$.

### Respaldo de mediciones
Las cifras de tiempo de esta decisión salen de `bench/historia.py` (tarea T026/T027) y de `bench/puntos_control.py` (capacidad 007). Antes de que ese bench exista no se citan números. Nota de 007: con la cripta sintética solo K=10 cabe en 50 ms de reconstrucción; K=50 y K=100 pueden superarlo y eso se reporta tal cual, sin ocultarlo, al justificar el K por defecto.
Reconstruir hacia atrás no es viable porque el historial del pergamino retiene solo 5 acciones (`MAX_HISTORIAL`).

---

## Decisión 6: Reutilización de lógica de extracción de estado (Capacidad 008)

### Extracción común
En la capacidad 008, `EstadoJuegoLogica._armarResultadoReplayHasta` recopila los datos del jugador (sala, vida, ataque, defensa, velocidad, inventario de llaves y objetos, efectos activos, enemigos en sala y terminación).
Para evitar duplicación de código (Principio DRY y Constitución):
- Se extrae el armado del estado a un método común en `EstadoJuegoLogica`:
  `_extraerResumenEstadoActual(self, instante: int, acciones: int) -> ResumenEstadoDTO`.
- `_armarResultadoReplayHasta` reutiliza este método para poblar los campos comunes de `ResultadoReplayHastaDTO`.
- `consultarHistoria` utiliza directamente `_extraerResumenEstadoActual` para generar el `ResumenEstadoDTO` final.

---

## Resumen de decisiones técnicas

| Decisión | Opción Elegida | Alternativa Descartada | Justificación |
|---|---|---|---|
| Aislamiento de ejecución | Segunda instancia aislada con protección de singleton | Clonar lógica viva / modificar partida viva | Evita corrupción del juego activo y del singleton global |
| Búsqueda de punto base | Búsqueda binaria propia en lista de puntos | Recorrido lineal / bisect estándar | Cumple Principio I (sin librerías prohibidas) y garantiza $O(\log M)$ |
| Dirección de reconstrucción | Hacia adelante desde punto base más cercano | Hacia atrás con historial de retroceso | El historial del pergamino solo retiene 5 acciones; hacia adelante acota el peor caso a $K-1$ |
| Extracción de DTO | Método helper común compartido con capacidad 008 | Duplicación de código en 004 y 008 | Mantenibilidad, consistencia y reutilización |
| Comando de consola | Interceptación previa en `ControladorJuego` | Tratar como `EventoDTO` en `accionJugador` | No debe contar como acción ni consumir tiempo virtual (FR-432) |
