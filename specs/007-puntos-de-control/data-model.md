# Modelo de Datos: Puntos de control de la partida

**Capacidad**: `007-puntos-de-control` | **Fecha**: 2026-11-07 | **Especificación**: [spec.md](spec.md)

Este documento describe las entidades de datos, atributos, relaciones y ciclo de vida de los puntos de control en memoria y en persistencia.

---

## 1. Entidades Principales

### 1.1. `PuntoControlDTO` (DTO de transporte de punto de control)
Ubicación: `DTO/PuntoControlDTO.py`

Representa una captura instantánea inmutable del estado del juego en un punto clave de la línea de tiempo.

```python
@dataclass(frozen=True)
class PuntoControlDTO:
    numero_punto: int             # 0 para inicial, 1..n para periódicos
    acciones_linea_tiempo: int    # Contador de acciones vigentes al tomarlo (0, K, 2K, ...)
    instante_reloj: int           # reloj.tiempo_actual en el momento de la captura
    estado: EstadoGuardadoDTO     # Copia completa desconectada del estado del juego
```

- **Invariantes**:
  - `numero_punto >= 0`.
  - `acciones_linea_tiempo >= 0`.
  - Para puntos periódicos $n \ge 1$: `acciones_linea_tiempo == n * k`.
  - `estado` es un grafo de objetos desconectado (`EstadoGuardadoDTO`), libre de referencias compartidas a los objetos activos de la simulación.

---

### 1.2. Extensiones en `EstadoJuegoLogica`

Se agregan los siguientes atributos y métodos a la clase central `EstadoJuegoLogica`:

```python
class EstadoJuegoLogica:
    # Atributos nuevos:
    k_checkpoint: int                      # Intervalo configurado (entero >= 1)
    acciones_linea_tiempo: int             # Acciones aceptadas en la línea temporal vigente
    puntos_control: list[PuntoControlDTO]  # Lista contigua ordenada por acciones
```

- **`acciones_linea_tiempo`**:
  - Inicia en `0`.
  - Se incrementa en `1` tras procesar exitosamente cada acción que no sea de pergamino.
  - Se decrementa en `m` (típicamente 1) al procesar exitosamente el pergamino de retroceso.
- **`puntos_control`**:
  - Lista contigua de Python (`list`), autorizada por el Principio I como almacenamiento contiguo.
  - Ordenada de manera natural en forma estrictamente creciente por `acciones_linea_tiempo`.
  - No utiliza colecciones prohibidas (`deque`, `heapq`, `dict`, `set`).

---

## 2. Operaciones y Métodos del Modelo

### 2.1. `_capturarPuntoControlInicial(self) -> None`
- Se invoca al final de `iniciarJuego`, tras cargar la sala de inicio y generar la agenda inicial.
- Construye un `PuntoControlDTO` con `numero_punto = 0`, `acciones_linea_tiempo = 0`, `instante_reloj = self.estadoJuego.reloj.tiempo_actual` y `estado = EstadoGuardadoLogica.exportar(self)`.
- Se almacena como el primer elemento de `self.puntos_control`.

### 2.2. `_verificarYCapturarPuntoControl(self) -> None`
- Se invoca al final de `accionJugador`, tras `_avanzarHastaProximoTurno` y `_registrarAccionEnLog`.
- Si `self.fin` es verdadero, no se ejecuta ninguna captura.
- Comprueba si `self.acciones_linea_tiempo % self.k_checkpoint == 0`:
  - En caso afirmativo, calcula `numero_punto = self.acciones_linea_tiempo // self.k_checkpoint`.
  - Exporta el estado actual mediante `EstadoGuardadoLogica.exportar(self)`.
  - Añade el nuevo `PuntoControlDTO` al final de `self.puntos_control`.

### 2.3. `_podarPuntosControlPosteriores(self, limite_acciones: int) -> None`
- Se invoca en la rama de `GestorEventos.es_uso_de_pergamino` tras aplicar los deltas de reversión.
- Trunca la lista desde el final mientras `self.puntos_control[-1].acciones_linea_tiempo > limite_acciones`:
  ```python
  while self.puntos_control and self.puntos_control[-1].acciones_linea_tiempo > limite_acciones:
      self.puntos_control.pop()
  ```
- Si el nuevo `limite_acciones` coincide exactamente con un punto de control (por ejemplo, retroceder de la acción $K+1$ a la acción $K$), ese punto de control en $K$ se preserva.

### 2.4. `obtenerPuntoControlReciente(self, k: int) -> PuntoControlDTO | None`
- Método público expuesto para la futura capacidad 004 (`historia #k`).
- Dado un número de acción $k$, busca el punto de control con mayor `acciones_linea_tiempo <= k`.
- Al estar la lista ordenada, se recorre en sentido inverso o mediante búsqueda binaria manual:
  ```python
  # Búsqueda manual eficiente hacia atrás
  for punto in reversed(self.puntos_control):
      if punto.acciones_linea_tiempo <= k:
          return punto
  return None
  ```

---

## 3. Diagrama de Transición de Estados

```text
       [ Iniciar Juego ]
               │
               ▼
   +────────────────────────+
   | Captura Punto 0        | (acciones_linea_tiempo = 0)
   +────────────────────────+
               │
               ▼
        Acción Jugador
               │
     ┌─────────┴─────────────────────────────┐
     ▼ Rechazada                             ▼ Aceptada (normal)
(Sin cambios)                          acciones_linea_tiempo += 1
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼ acciones % K == 0 y no fin                ▼ Otro caso
            +──────────────────────────+                  (Continúa sin capturar)
            | Captura Punto n          |
            | (acciones = n * K)       |
            +──────────────────────────+
                       │
                       ▼
            Uso de Pergamino (revierte m)
                       │
                       ▼
            acciones_linea_tiempo -= m
            Poda de puntos con acciones > acciones_linea_tiempo
```
