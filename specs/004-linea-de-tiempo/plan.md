# Plan de implementación: Línea de tiempo — consulta de estados pasados

**Rama**: `004-linea-de-tiempo` | **Fecha**: 2026-11-08 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/004-linea-de-tiempo/spec.md` (FR-427 a FR-443). Requisitos de consulta de estados históricos (`historia <t>` e `historia #k`), invariantes del pergamino de retroceso, persistencia v7 y restricciones de aislamiento y rendimiento.

---

## Resumen

Esta capacidad incorpora a Cripta la habilidad de consultar instantáneas completas de estados pasados de la partida en cualquier momento (`historia <t>` e `historia #k`), tanto durante la partida viva como una vez concluida (victoria o derrota), sin modificar ni avanzar la partida en curso (FR-427, FR-429, FR-432).

El enfoque técnico se fundamenta en las investigaciones de [research.md](research.md):
1. **Reconstrucción aislada**: Se hidrata una segunda instancia temporal de `EstadoJuegoLogica` a partir del punto de control previo más cercano (capacidad 007). Para blindar la partida viva contra efectos colaterales, se implementa una guarda `try ... finally` que salva y restituye las variables de estado del singleton global `RetrocesoLogica`, asegurando además que el reloj, el generador de azar, el log y el presupuesto de red de la partida viva no sean tocados.
2. **Búsqueda binaria manual de puntos de control**: Se reemplaza el escaneo lineal inverso de `obtenerPuntoControlReciente` por una búsqueda binaria implementada a mano sobre `self.puntos_control`, operando en $O(\log M)$ sin usar bibliotecas prohibidas como `bisect`, `dict` o `set` (Principio I).
3. **Reproducción acotada hacia adelante por segmento vigente**: el log conserva las acciones revertidas y los usos de pergamino, así que se analiza el segmento entre el punto base y el siguiente con una pila local (pasada 1) y se reproduce fielmente en la instancia aislada (pasada 2), parando por acción vigente y no por contador o reloj (ver sección 3). El trabajo queda acotado por el tamaño del segmento (≈ K acciones, FR-439).
4. **Extracción unificada de estado**: Se extrae la lógica de empaquetado de estado compartida entre `_armarResultadoReplayHasta` (008) y `consultarHistoria` (004) en un método auxiliar común `_extraerResumenEstadoActual`, evitando duplicación.
5. **Interceptación en Controlador/Vista**: `ControladorJuego` intercepta los comandos `historia <t>` e `historia #k` antes del mapeo de eventos. La presentación se delega a `VistaConsola.mostrar_historia(resumen)` (FR-431), omitiendo el mapa conocido mientras no esté integrada la capacidad 002. En `--replay` y `--bench` la vista no se instancia (Principio IV).
6. **Validación de rendimiento**: Se incorpora el bloque `bench/historia.py` en `--bench`, evaluando partidas de $\ge 5\,000$ acciones para verificar que el tiempo de respuesta sea $\le 50$ ms (FR-442, Principio VII) y midiendo la alternativa descartada (reconstrucción desde el inicio sin puntos de control).

---

## Contexto técnico

- **Lenguaje/versión**: Python 3.11+
- **Dependencias principales**: Biblioteca estándar de Python (`dataclasses`, `time`, `gc`, `unittest`). No se agregan paquetes externos.
- **Almacenamiento**: Persistencia existente en formato binario **v7** (estado 4). Esta capacidad no agrega campos nuevos a disco ni altera el formato binario ni el log (FR-441).
- **Pruebas**: Framework `unittest` en la raíz del repositorio (`test_historia_firma.py`, `test_historia_tiempo.py`, `test_historia_aislamiento.py`).
- **Plataforma**: Multiplataforma (Windows / Linux / macOS).
- **Tipo de proyecto**: Arquitectura MVC por capas (Controlador → Servicio → Lógica → DTO / Adaptadores).
- **Objetivos de rendimiento**:
  - Tiempo de respuesta de `historia <t>` e `historia #k` $\le 50$ ms en partidas de $\ge 5\,000$ acciones con $K$ por defecto (FR-442).
  - Ciclo de eventos $\le 20$ ms (Principio VII).
  - Cero peticiones de red adicionales durante la consulta (FR-440).
- **Restricciones constitucionales**: Prohibido el uso de `heapq`, `bisect`, `collections` (`deque`, `defaultdict`), `networkx`, y `dict`/`set` como índice o caché. Todo desempate determinista.

---

## Verificación de la constitución

*Compuerta: Evaluación de principios fundamentales antes de la implementación.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| **I. Estructuras propias** | Búsqueda binaria escrita a mano en la lista contigua de puntos de control. No se usa `bisect`, `dict`, `set` ni `collections`. | Pasa |
| **II. Determinismo** | La instancia aislada restaura el generador `GestorEventos.azar` desde el punto de control (`estado_azar`). No se altera la semilla ni el azar de la partida viva. La reproducción es 100% determinista. | Pasa |
| **III. Equivalencia ante el reuso** | Reconstruir desde un punto de control y avanzar produce el mismo estado que reproducir desde el inicio (demostrado en mediciones). | Pasa |
| **IV. Separación MVC y adaptadores** | `EstadoJuegoServicio.consultarHistoria` devuelve `ResumenEstadoDTO`. `ControladorJuego` interpreta la entrada y `VistaConsola.mostrar_historia` muestra el resultado. En `--replay` y `--bench` no se crea la vista. | Pasa |
| **V. Sin datos de una cripta concreta** | No existen identificadores fijos ni dependencias de criptas particulares. Funciona con cualquier cripta y con criptas sintéticas de `--bench`. | Pasa |
| **VI. Presupuesto de red y versiones** | La reconstrucción no gasta solicitudes (`reporteSolicitudes` delta = 0, FR-440). Se preserva el formato v7 sin cambios. | Pasa |
| **VII. Rendimiento medido** | Medición rigurosa con `bench/historia.py` (cargas de 5 000 acciones, $K \in \{10, 50, 100\}$) y medición de la alternativa descartada (reconstrucción desde el inicio). GC desactivado durante la toma de tiempos. | Pasa |
| **VIII. La especificación precede al código** | Cada componente mapea a requisitos funcionales FR-427 a FR-443 de `spec.md`. No se introducen reglas nuevas. | Pasa |
| **IX. Trazabilidad** | Matriz exhaustiva FR $\to$ componente $\to$ prueba unitaria en `quickstart.md`. Escenarios de aceptación y Apéndice B cubiertos. | Pasa |
| **X. Cambios de especificación** | Sesión de clarificaciones completada y registrada en `spec.md`. No hay discrepancias pendientes. | Pasa |
| **XI. Uso de LLM** | Invocaciones y prompts registrados con herramienta y modelo. | Pasa |

---

## Estructura del proyecto

### Documentación de la capacidad (`specs/004-linea-de-tiempo/`)

```text
specs/004-linea-de-tiempo/
├── spec.md              # Especificación aprobada (FR-427 a FR-443)
├── plan.md              # Este documento de planificación técnica
├── research.md          # Investigación de decisiones 1 a 5 y alternativas
├── data-model.md        # Definición de DTOs, modelo de datos y persistencia v7
├── quickstart.md        # Guía de pruebas interactivas, bench y trazabilidad FR
└── contracts/
    ├── servicio_consultar_historia.md  # Contrato de EstadoJuegoServicio
    └── cli_historia_comando.md         # Contrato de Controlador y Vista
```

### Código fuente afectado (raíz del repositorio)

```text
DTO/
├── ResumenEstadoDTO.py       # DTO existente de salida (firma preservada)
├── PuntoControlDTO.py        # DTO existente consumido de capacidad 007
└── ResultadoReplayHastaDTO.py # Reutiliza método de extracción común

Logica/
├── EstadoJuegoLogica.py      # Búsqueda binaria (_buscarPuntoPorAcciones, _buscarPuntoPorInstante),
│                             # reconstrucción aislada, guarda de singleton RetrocesoLogica,
│                             # método común _extraerResumenEstadoActual
└── RetrocesoLogica.py        # Atributos protegidos del singleton

Servicio/
├── EstadoJuegoServicio.py    # Reemplazo del cuerpo provisional de consultarHistoria
                              # manteniendo firma exacta y compatibilidad test_historia_firma.py

Controlador/
├── ControladorJuego.py       # Interceptación de 'historia <t>' e 'historia #k'
│                             # y soporte en bucle post-partida terminada
└── Vista.py                  # VistaConsola.mostrar_historia(resumen)

bench/
├── __init__.py               # Registro del bloque 'historia' en BLOQUES
└── historia.py               # Benchmark de rendimiento (5 000 acciones, límite 50 ms)

tests (raíz del repositorio)/
├── test_historia_firma.py        # Prueba de firma existente (debe seguir pasando)
├── test_historia_tiempo.py       # Pruebas funcionales completas FR-427 a FR-443
└── test_historia_aislamiento.py  # Pruebas de aislamiento, singleton, red y persistencia
```

---

## Decisiones de diseño e implementación

### 1. Reconstrucción aislada y protección de `RetrocesoLogica`
- Se instancia una segunda `EstadoJuegoLogica(semilla=self.semilla, cripta=self.idCripta, comunicacion=self.comunicacion)`.
- Se protegen los atributos de `RetrocesoLogica()` mediante instantánea previa:
  ```python
  retro = RetrocesoLogica()
  estado_retro = (retro.cabeza, retro.cola, retro.actual, retro.reloj,
                  retro.cantidad_actual, retro.cantidad_acciones,
                  retro.tiempo_evento, retro.suspensiones)
  reloj_retro = self.estadoJuego.reloj.retroceso if self.estadoJuego and self.estadoJuego.reloj else None
  try:
      # Reconstrucción sobre juego_aislado
      ...
  finally:
      (retro.cabeza, retro.cola, retro.actual, retro.reloj,
       retro.cantidad_actual, retro.cantidad_acciones,
       retro.tiempo_evento, retro.suspensiones) = estado_retro
      if self.estadoJuego and self.estadoJuego.reloj:
          self.estadoJuego.reloj.retroceso = reloj_retro
  ```
- La instancia aislada establece `registrador_log = None` y `_es_repeticion = True`. Su generador de azar es restaurado desde `punto.estado.estado_azar` y no afecta al azar de la partida viva.

### 2. Búsqueda binaria manual de puntos de control
- En `EstadoJuegoLogica`:
  - `_buscarPuntoPorAcciones(self, k: int) -> PuntoControlDTO | None`: búsqueda binaria manual en `self.puntos_control` que encuentra el último punto con `acciones_linea_tiempo <= k`.
  - `_buscarPuntoPorInstante(self, t: int) -> PuntoControlDTO | None`: búsqueda binaria manual en `self.puntos_control` que encuentra el último punto con `instante_reloj <= t`.
  - `obtenerPuntoControlReciente(self, k: int)` se refactoriza para reutilizar `_buscarPuntoPorAcciones(k)`.
- Complejidad: $O(\log M)$, estrictamente sin `bisect` ni estructuras prohibidas.

### 3. Reconstrucción por segmento vigente (el log NO se trunca al usar un pergamino)
Hechos verificados en el código: el uso de un pergamino se **agrega** al log (`_registrarAccionEnLog`) y las acciones revertidas **siguen** en él; el pergamino restaura el reloj y NO restaura el azar. Consecuencias: (a) un contador que "llega a k-1" o un reloj que "llega a t" puede ocurrir en una rama luego revertida, así que no sirven como criterio de parada; (b) la reproducción debe aplicar TODOS los registros del segmento (también los revertidos y los usos de pergamino) para que el azar quede igual que en la partida viva.

Algoritmo común (`_planificarSegmento`):
1. **Punto base** por búsqueda binaria (`acciones_linea_tiempo <= k-1` en `#k`; `instante_reloj <= t` en `<t>`). **Fin del segmento** = `longitud_acciones_log` del punto siguiente, o el final del log si el base es el último. El siguiente punto sobrevivió a la poda, así que su prefijo de log ya contiene todos los pergamino anteriores a él: el segmento queda acotado (≈ K acciones más las revertidas dentro de él), no la cola entera del log.
2. **Pasada 1 (sin simular)**: recorrer los registros del segmento con una pila local (lista usada como pila). Cursor de inventario: se ignora. Uso de pergamino: `pop()`. Cualquier otra acción: `push` de su índice. Al terminar, la pila tiene los índices de las acciones **vigentes** `E[0..m-1]`; las demás son revertidas.
3. **Pasada 2 (instancia aislada, fiel)**: aplicar los registros en orden y completos. Revertidas y pergamino se aplican sin tope. Las vigentes se aplican y la parada se evalúa **después** de cada una.
   - `historia #k`: parar justo **antes** de aplicar `E[j]`, con `j = (k-1) - c` (estado tras `k-1` acciones vigentes).
   - `historia <t>`: aplicar cada vigente con `accionJugador(ev, tope=t)`; tras cada una, si el reloj llegó a `t` o el próximo evento programado supera `t`, parar y llamar `_completarInstante(t)` (misma regla que 008).
4. Prohibido parar por "contador == k-1" o "reloj >= t" sobre registros que no son vigentes.

Reglas de entrada:
- `historia <t>`: `t > reloj.tiempo_actual` se rechaza (FR-433); `t ==` reloj actual devuelve el estado vivo sin reconstruir.
- `historia #k`: `k >= 1` entero (FR-435); `k = N+1` devuelve el estado vivo (FR-436); `k > N+1` se rechaza; `1 <= k <= N` usa el algoritmo anterior (`#1` cae en el punto 0 con `j = 0`).

### 4. Coherencia con el pergamino de retroceso
- La poda de la partida viva (`_podarPuntosControlPosteriores`) elimina los puntos con más acciones que el contador vigente. Un punto superviviente solo puede tener por delante acciones que el pergamino revierte **después** de él, nunca antes.
- El log conserva las acciones revertidas y los usos de pergamino; la línea vigente se obtiene con la pila de la pasada 1 (sección 3), no truncando el log.
- Casos de prueba obligatorios: pergamino justo después de un punto de control; acción revertida cuyo contador coincide con el de la consulta (`A1 A2 A3 P A3' A4`, consulta `#4` debe dar el estado tras `A3'`, no tras `A3`); consulta `<t>` en un instante que solo existió en la rama revertida (rechazada por ser futuro).

### 5. Reutilización de código con Capacidad 008
- Se factoriza el armado del estado en `_extraerResumenEstadoActual(self, instante: int, acciones: int) -> ResumenEstadoDTO`.
- `_armarResultadoReplayHasta` delega la obtención de estos campos a la rutina común.

### 6. Partida terminada y mapa conocido
- El bucle principal de `ControladorJuego` permite consultas de historia tras finalizar la partida (victoria o derrota) antes de salir.
- `mapa_conocido` se fija en `None` en el DTO y la vista omite cualquier línea de mapa (FR-431).

### 7. Comandos interactivos en Controlador y Vista
- `ControladorJuego.iniciar()` detecta patrones `historia <t>`, `historia t`, `historia #k` antes de mapear eventos.
- Llama a `self.servicio.consultarHistoria(...)` y a `self.vista.mostrar_historia(resumen)`.
- Errores de sintaxis o rango muestran mensajes claros y continúan el bucle sin alterar la partida.

### 8. Benchmark y rendimiento
- Se crea `bench/historia.py` y se agrega a `BLOQUES` en `bench/__init__.py`.
- Se miden consultas sobre partidas de 5 000 acciones deterministas para $K \in \{10, 50, 100\}$.
- Se compara el tiempo frente a la Alternativa C descartada (reconstrucción desde el inicio sin checkpoints) y se mide el tiempo de búsqueda binaria vs. búsqueda lineal.

---

## Registro de complejidad

> No se introducen violaciones a la Constitución. No se requiere tracking de excepciones.

| Principio | Justificación |
|---|---|
| Principio I | Búsqueda binaria manual $O(\log M)$; no se usan diccionarios, conjuntos ni módulos de búsqueda de la biblioteca estándar. |
| Principio IV | Separación estricta entre capas: Controlador parsea, Servicio orquesta, Lógica computa y Vista presenta. `--bench` y `--replay` no usan vista. |
