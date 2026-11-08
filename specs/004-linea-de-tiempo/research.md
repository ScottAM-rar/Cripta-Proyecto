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

### Semántica para `historia <t>`
- **Validación**: Si $t < 0$ o no es entero, rechazar con `ValueError` (FR-437). Si $t > \text{reloj.tiempo\_actual}$, rechazar como instante futuro (FR-433).
- **Selección de base**: Búsqueda binaria del último punto con `instante_reloj <= t`.
- **Reproducción**:
  1. Hidratar `juego_aislado` desde `punto.estado`.
  2. Leer los registros de `logEventos` a partir del índice `punto.longitud_acciones_log`.
  3. Reproducir acciones con `juego_aislado.accionJugador(ev, tope=t)` hasta que el próximo evento supere $t$ o el reloj alcance $t$.
  4. Si el reloj se detiene en $t$, invocar `juego_aislado._completarInstante(t)` para procesar todos los eventos de otros actores programados exactamente en $t$, excluyendo la decisión del jugador en $t$ (FR-428).
  5. Extraer y retornar `ResumenEstadoDTO`.

### Semántica para `historia #k`
- **Validación**:
  - $k$ debe ser entero $\ge 1$ (FR-435). Si $k \le 0$, rechazar con `ValueError`.
  - Sea $N = \text{self.acciones\_linea\_tiempo}$ el número de acciones vigentes en la partida viva.
  - Si $k = N + 1$: Retorna el estado actual de la partida viva sin reproducir (FR-436).
  - Si $k > N + 1$: Rechazar como acción futura (FR-436).
- **Definición de `#k`**: Estado *justo antes* de que el jugador tome su $k$-ésima acción (es decir, tras haber completado exactamente $k - 1$ acciones).
  - `#1`: Estado inicial (0 acciones ejecutadas, equivalente al punto de control 0 y a `historia 0`).
  - Para $1 \le k \le N$:
    1. Búsqueda binaria del último punto con `acciones_linea_tiempo <= k - 1`.
    2. Sea $c = \text{punto.acciones\_linea\_tiempo}$. Restan por ejecutar $(k - 1) - c$ acciones del jugador.
    3. Hidratar `juego_aislado` desde `punto.estado`.
    4. Reproducir desde `punto.longitud_acciones_log` hasta alcanzar `juego_aislado.acciones_linea_tiempo == k - 1` y completar los eventos hasta el turno del jugador.
    5. Extraer y retornar `ResumenEstadoDTO`.

### Tabla de instantes por acción no requerida
No se necesita una tabla auxiliar indexada de `acción -> instante`: la lista de puntos de control y el log determinista permiten alcanzar directamente cualquier acción $k$ contando las decisiones del jugador aplicadas desde el punto base. La monotonicidad garantiza que no hay ambigüedades.

---

## Decisión 4: Invariante del pergamino de retroceso y poda de puntos

### Invariante de coherencia temporal
- Cuando el jugador usa un pergamino de retroceso, revierte $m$ acciones. La variable `acciones_linea_tiempo` se decrementa y se llama a `_podarPuntosControlPosteriores(self.acciones_linea_tiempo)`.
- **Invariante**: Todo punto de control que permanece en `puntos_control` tiene `acciones_linea_tiempo <= acciones_actuales`.
- Dado que el log en memoria y en disco preserva la secuencia cronológica hasta el retroceso, las acciones revertidas son eliminadas de la línea de tiempo vigente.
- Por tanto, restaurar un punto de control superviviente y avanzar aplicando el segmento de log vigente reconstruye de forma fiel y determinista la historia de la partida.
- El punto de control 0 (`acciones = 0`) nunca se poda, garantizando que siempre existe al menos una base para reproducir cualquier instante válido.

---

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
Siguiendo las mediciones de `bench/puntos_control.py`:
- Reconstruir desde el punto más cercano toma típicamente $< 5$ ms para $K = 10$, frente a $> 150$ ms si se reprodujera desde el inicio (Alternativa C descartada).
- Intentar reconstruir hacia atrás no es viable porque el historial solo retiene 5 acciones. Por tanto, la reconstrucción hacia adelante sobre checkpoints periódicos es la única arquitectura viable y demostrada.

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
