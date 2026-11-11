# Modelo de datos: Línea de tiempo (004-linea-de-tiempo)

**Capacidad**: `004-linea-de-tiempo`  
**Fecha**: 2026-11-08  
**Estado**: Definitivo  

Este documento describe las estructuras de datos, entidades, invariantes y modelos de transferencia involucrados en la capacidad de consulta de estados pasados.

---

## 1. Persistencia y Formato de Archivo

> **IMPORTANTE**: Esta capacidad **NO** introduce nuevos campos persistidos ni modifica el formato binario de partida.
> El formato de guardado binario permanece exactamente en **v7** (estado 4, introducido en la capacidad 007).

Los puntos de control (`puntos_control: list[PuntoControlDTO]`) y la longitud de acciones en el log ya se almacenan y serializan dentro del formato v7. Esta capacidad opera consumiendo esos datos existentes para la reconstrucción en memoria, sin alterar el archivo ni la serialización.

---

## 2. Entidades y DTOs

### 2.1 `ResumenEstadoDTO` (Salida de `consultarHistoria`)

Ubicación: `DTO/ResumenEstadoDTO.py`  
Define la instantánea exhaustiva del juego en el instante o número de acción solicitado.

```python
@dataclass
class ResumenEstadoDTO:
    """Estado de la partida en el instante o acción consultada.
    No reemplaza ni muta la partida viva.
    """
    instante: int                          # Instante virtual del reloj alcanzado
    acciones_jugador: int                  # Acciones del jugador ejecutadas en la línea vigente
    id_sala_jugador: int                   # Sala en la que se encuentra el jugador
    vida_jugador: int                      # Puntos de vida actuales del jugador
    ataque_jugador: int                    # Ataque efectivo del jugador
    defensa_jugador: int                   # Defensa efectiva del jugador
    velocidad_jugador: int                 # Velocidad efectiva del jugador
    inventario_llaves: list[str] = field(default_factory=list)      # Lista de id_catalogo de llaves
    inventario_objetos: list[str] = field(default_factory=list)     # Nombres de objetos en inventario
    efectos_activos: list[str] = field(default_factory=list)        # 'veneno', 'velocidad temporal', etc.
    enemigos_sala: list[tuple[str, str, int]] = field(default_factory=list) # (id_instancia, nombre, vida)
    partida_terminada: bool = False        # Si en ese instante la partida ya había concluido
    motivo_terminacion: str | None = None  # Motivo del fin ('MUERTE', 'SALIDA', etc.)
    mapa_conocido: object | None = None    # None hasta que se integre capacidad 002
```

#### Reglas de validación y campos:
- `instante`: Entero $\ge 0$. Coincide con $t$ en `historia <t>`, o con el tiempo de inicio de la acción $k$ en `historia #k`.
- `acciones_jugador`: Entero $\ge 0$. Número de acciones ya ejecutadas hasta ese estado.
- `enemigos_sala`: Lista de tuplas ordenadas deterministamente por identificador de instancia (`id_instancia`). Solo incluye enemigos con vida $> 0$.
- `mapa_conocido`: Se mantiene en `None` en esta capacidad (FR-431 ítem 7). La vista no mostrará ninguna sección de mapa mientras sea `None`.

---

### 2.2 `PuntoControlDTO` (Consumido de la Capacidad 007)

Ubicación: `DTO/PuntoControlDTO.py`  
Estructura inmutable capturada periódicamente cada $K$ acciones.

```python
@dataclass(frozen=True)
class PuntoControlDTO:
    numero_punto: int
    acciones_linea_tiempo: int
    instante_reloj: int
    estado: EstadoGuardadoDTO
    longitud_bitacora: int = 0
    longitud_acciones_log: int = 0
```

#### Relación con el log y la reconstrucción:
- `longitud_acciones_log`: Índice en `logEventos.obtener_registros_cronologicos()` que delimita qué porción del log ya estaba aplicada al momento del punto de control.
- La reconstrucción lee el segmento `registros[punto.longitud_acciones_log : longitud_acciones_log del punto siguiente]` (o hasta el final del log si es el último punto). Dentro del segmento hay acciones vigentes, acciones revertidas, usos de pergamino y movimientos de cursor; solo una pila local decide cuáles son vigentes.

---

## 3. Estado en Memoria y Aislamiento

Durante la ejecución de `consultarHistoria`:
1. **Partida Viva (`EstadoJuegoLogica`)**:
   - `self.puntos_control`: Lista ordenada monótonamente por `acciones_linea_tiempo` e `instante_reloj`.
   - `self.logEventos`: Historial completo de eventos ejecutados y vigentes.
   - **Invariable**: No se modifica ningún atributo de la partida viva durante o tras la consulta.
2. **Instancia Aislada (`EstadoJuegoLogica`)**:
   - Creada temporalmente durante la invocación.
   - Descartada por el recolector de basura al terminar la consulta.
   - Atributos clave de aislamiento:
     - `registrador_log = None` (sin escritura en disco).
     - `_es_repeticion = True` (sin captura de puntos ni registro en puntajes).
     - Azar restaurado a partir de `punto.estado.estado_azar`.
3. **Singleton `RetrocesoLogica`**:
   - Preservado y restaurado en `try ... finally`.

---

## 4. Transiciones de Estado en la Línea de Tiempo

```
[Inicio de partida]
       │
       ▼
 [Punto 0: t=0, acc=0]
       │
       ├── Acción 1..K-1 (avanzan tiempo y registran en log)
       │
       ▼
 [Punto 1: t=t1, acc=K]
       │
       ├── Acción K+1..2K-1
       │
       ▼
 [Punto 2: t=t2, acc=2K]
       │
       ├── Pergamino usado (revierte m acciones)
       │         │
       │         ▼
       │   Puntos con acc > (2K - m) son podados con pop()
       │   El log NO se trunca: conserva revertidas y el uso del pergamino
       ▼
[Línea de tiempo vigente: monótona y consistente]
```

### Invariantes de los datos:
1. **Monotonicidad**: Para cualesquiera puntos contiguos $i$ e $i+1$ en `puntos_control`:
   $$\text{punto}_{i}.\text{acciones\_linea\_tiempo} < \text{punto}_{i+1}.\text{acciones\_linea\_tiempo}$$
   $$\text{punto}_{i}.\text{instante\_reloj} < \text{punto}_{i+1}.\text{instante\_reloj}$$
2. **Cota de Reconstrucción**: Para cualquier consulta, la cantidad de acciones a reproducir desde el punto base seleccionado es:
   $$\Delta \text{acciones} \le K - 1$$
