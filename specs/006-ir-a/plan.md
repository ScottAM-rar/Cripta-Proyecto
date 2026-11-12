# Plan de implementación: Comando «ir a»

**Rama**: `006-ir-a` | **Fecha**: 2026-11-11 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/006-ir-a/spec.md` (FR-231 a FR-252, con las 5 clarificaciones de la sesión 2026-11-11)

## Resumen

El jugador pasa a poder ordenar «ir a <sala>»: el modelo calcula la ruta más barata **sobre lo que el jugador conoce** (002), la recorre **un paso por vez** y se detiene cuando algo cambia o lo amenaza. Cada paso es un movimiento normal del jugador, así que el reloj, la agenda de eventos, las trampas, la antorcha, la observación de puertas, el pergamino y los puntos de control funcionan sin reglas duplicadas.

El enfoque técnico, justificado en [research.md](research.md), tiene seis piezas:

1. Un módulo nuevo `Logica/ViajeLogica.py` que **orquesta** pasos del jugador. No tiene reglas de movimiento propias: construye el mismo evento `MOVER_JUGADOR` que el controlador y lo entrega a `accionJugador`.
2. **Ruta con `BuscadorRutas` sobre `VistaMapaConocido`** (contrato [vista-buscador](../002-niebla-de-guerra/contracts/vista-buscador.md)), sin modificar ninguno de los dos. `distancias_hacia(destino)` más `siguiente_paso(sala)` dan exactamente el desempate de FR-234 (se demuestra en research D1).
3. **Recálculo solo cuando cambia `version_conocimiento`** (equivalente a recalcular en cada paso, se demuestra en research D3) y **con cota de costo** (el parámetro `limite` de `BuscadorRutas`, adoptado tras medir: sin cota, un recálculo cerca del destino costaba 10 a 15 ms en 20 000 salas). Una puerta recordada abierta que resulta cerrada actualiza el conocimiento al entrar a la sala (002, FR-207); el recálculo no encuentra ruta y el viaje se detiene sin dar el paso.
4. **Detención por comprobaciones tras cada paso**: en este orden, muerte, llegada, enemigos dormidos activados, enemigo activo en la sala y daño. El motivo viaja en un resultado con datos simples.
5. **Pergamino**: cada paso es una acción deshacible; `accionJugador` avisa al viaje en curso cuando se usa el pergamino y el viaje se cancela.
6. **Registro**: dos marcas informativas en el log (`IR_A` con el destino y `FIN_IR_A` con el resultado) alrededor de los pasos, que son registros normales de movimiento. La reproducción repite los pasos y verifica las marcas.

Lo que **no** cambia: `BuscadorRutas`, `VistaMapaConocido`, `MapaConocido`, `MapaCripta`, `RetrocesoLogica`, el formato binario de partida (formato 8) y el estado guardado (estado 5).

## Contexto técnico

**Lenguaje/versión**: Python 3.11+ (el del proyecto).

**Dependencias principales**: solo las existentes. No se agrega ninguna.

**Almacenamiento**: ninguno nuevo. Un viaje es transitorio (se ejecuta dentro de una orden y nunca se guarda en curso); el log lo recoge como registros informativos dentro de su lista actual (ver [contracts/registro-viaje.md](contracts/registro-viaje.md)).

**Pruebas**: `unittest`, convención del repositorio (`test_*.py` en la raíz, `tests_labs/` con la API falsa y las criptas sintéticas). Casos B-N1, B-N2, B-N3 y B-N6 con una prueba cada uno.

**Plataforma**: consola, multiplataforma.

**Tipo de proyecto**: aplicación de consola por capas (Controlador → Servicio → Lógica + adaptadores).

**Objetivos de rendimiento** (FR-250, FR-251, constitución VII): un paso de «ir a» en **5 ms o menos**, medido con `--bench` en el peor caso (antorcha encendida, recálculo tras una puerta cerrada, criptas de 400 y 2 000 salas con el 10 % explorado, y con el mapa conocido completo en 400 salas, el criterio del enunciado §6.1; criterio duro). Con 20 000 salas, y con el mapa completo en 2 000 y 20 000 salas, se mide como informativo: el paso que captura un punto de control (007) y el recálculo desde cero tras una puerta cerrada superan 5 ms. El ciclo de eventos sigue bajo 20 ms.

**Restricciones**: sin `dict`/`set` como índice, sin `heapq`/`bisect`/`collections`/`networkx`; sin `sorted()` ni `list.sort()`. El modelo no importa red, disco ni vista. 0 solicitudes nuevas: la ruta sale del esqueleto que ya se descargó (FR-248).

**Escala/alcance**: criptas sintéticas deterministas por semilla en tres tamaños (400, 2 000 y 20 000 salas), el mayor 50 veces el menor; el criterio duro rige en 400 y 2 000 salas con el 10 % explorado y en 400 salas con el mapa completo.

## Verificación de la constitución

*Puerta antes de la investigación; se repite al final del diseño.*

| Principio | Cumplimiento | Dónde se comprueba |
|---|---|---|
| I. Estructuras propias | Listas indexadas por id y cola de prioridad propia (dentro de `BuscadorRutas`, ya existente). Ningún `dict`, `set`, `heapq`, `bisect`, `collections` ni `networkx` nuevo. La ruta no se materializa: se pregunta el siguiente paso. | Búsqueda de importaciones prohibidas en `Logica/ViajeLogica.py` y `bench/ir_a.py` (tarea de revisión) |
| II. Determinismo | Desempate explícito por menor id (FR-234); el viaje no usa azar, hora ni orden de iteración; no depende del contenido descargado (FR-248). | `test_viaje_determinismo.py` (dos ejecuciones, con y sin contenido descargado, mismo `partida.log`) |
| III. Equivalencia ante el reuso | El campo de distancias se reutiliza entre pasos solo si `version_conocimiento` no cambió; la invalidación se razona por evento en [research.md](research.md) D3 y se prueba contra el recálculo desde cero en cada paso. | `test_viaje_equivalencia.py` y `--bench ir_a` sección H |
| IV. MVC y adaptadores | `ViajeLogica` no importa red, disco ni vista. El controlador solo interpreta el comando y la vista solo imprime el resultado. `--replay` y `--bench` no instancian la vista. | Revisión de importaciones |
| V. Sin datos de una cripta concreta | Ningún id de sala ni cifra de la cripta de desarrollo en el código; las pruebas usan criptas sintéticas. | Búsqueda de literales |
| VI. Presupuesto de red y versiones | 0 solicitudes nuevas. No cambia ningún formato persistido, así que no hay versión que subir. | `test_viaje_sin_red.py`; cargar una partida con viaje previo no cambia nada |
| VII. Rendimiento medido | `--bench ir_a`: un paso ≤ 5 ms en el peor caso y la alternativa descartada de cada decisión. | [contracts/bench-ir-a.md](contracts/bench-ir-a.md) |
| VIII. Especificación primero | Este plan no agrega reglas. Un ajuste de redacción de FR-252 queda señalado en research D6 para corregir `spec.md` **antes** del código. | Revisión de `analyze` |
| IX. Trazabilidad | Cada caso del Apéndice B (B-N1, B-N2, B-N3, B-N6) tiene prueba que cita su FR. Tabla en [quickstart.md](quickstart.md). | `analyze` |
| X. Cambios de especificación | Si la implementación revela un defecto de `spec.md`, se corrige primero y en confirmación separada. | `git log` |
| XI. Uso de LLM | Este comando se registra en `PROMPTS_LLM.md` con herramienta y modelo. | Entrada de la bitácora |

**Resultado de la puerta inicial**: sin violaciones. **Re-evaluación tras el diseño**: sin violaciones; el único punto abierto es el ajuste de redacción de FR-252 (no es una violación del plan sino una precisión de la especificación).

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/006-ir-a/
├── plan.md              # Este archivo
├── research.md          # Fase 0: 8 decisiones con alternativas, complejidad y mediciones
├── data-model.md        # Fase 1: entidades y transiciones
├── quickstart.md        # Fase 1: validación de punta a punta y trazabilidad
├── contracts/
│   ├── viaje-logica.md  # Interfaz del orquestador y del servicio
│   ├── comando-ir-a.md  # Comando del jugador y mensajes
│   ├── registro-viaje.md# Marcas del log y reglas de la reproducción
│   └── bench-ir-a.md    # Bloque --bench ir_a
├── checklists/requirements.md
└── tasks.md             # Lo genera /speckit-tasks
```

### Código fuente (raíz del repositorio)

```text
Logica/
├── ViajeLogica.py          # NUEVO: orquesta el viaje (ruta, pasos, detenciones, motivo)
├── EstadoJuegoLogica.py    # pequeños cambios: viaje activo, contador de activaciones, aviso del pergamino,
│                           #   marcas del log, omitir marcas en repetición y segmentos
└── LogEventos.py           # marcas informativas: registrar_marca y TIPOS_MARCA_VIAJE
DTO/
└── ResultadoViajeDTO.py    # NUEVO: resultado del viaje (datos simples)
Servicio/
└── EstadoJuegoServicio.py  # irA, iniciarViaje, avanzarViaje, cancelarViaje
Controlador/
├── ControladorJuego.py     # comando «ir a <id>»
└── Vista.py                # mostrar_viaje
bench/
├── ir_a.py                 # NUEVO: bloque de --bench
└── __init__.py             # registra el bloque "ir_a" y su criterio de salida
tests_labs/
└── escenarios_ir_a.py      # NUEVO: criptas de los casos B-N1, B-N2, B-N3 y B-N6
test_viaje_*.py             # NUEVOS: pruebas (ver quickstart.md)
```

**Decisión de estructura**: se conserva la arquitectura por capas. El viaje vive en `Logica/` como módulo propio (decisión pedida), reutiliza sin modificar `BuscadorRutas` y `VistaMapaConocido`, y el resto de cambios son puntuales en archivos que ya tratan acciones y log.

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar.
