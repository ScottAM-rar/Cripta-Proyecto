# Guía de validación: Niebla de guerra y mapa conocido

**Especificación**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Cómo comprobar de punta a punta que la capacidad cumple su especificación. Los nombres de pruebas y de módulos son los planeados; `/speckit-tasks` los convierte en tareas.

## Requisitos previos

- Python 3.11 o superior, desde la raíz del repositorio.
- Sin red: las pruebas y `--bench` usan la API falsa (`tests_labs/api_falsa.py`) y criptas sintéticas deterministas por semilla.
- Para jugar a mano: `python main.py --offline` con una cripta guardada en disco (ver `README.md`).

## 1. Pruebas automatizadas

```text
python -m unittest test_mapa_conocido test_niebla_retroceso test_niebla_vista ^
    test_niebla_guardado test_niebla_determinismo test_niebla_proporcional ^
    test_vista_conocimiento_buscador test_puertas_punto_unico
python -m unittest discover
```

Resultado esperado: todas en OK. La segunda línea confirma que la Parte I y las capacidades 001 y 005 no se rompieron.

## 2. Escenarios de reproducción

```text
python -m tests_labs.escenarios_niebla
```

Genera un `partida.log` por escenario en `specs/002-niebla-de-guerra/replays/`, con el requisito en el nombre (por ejemplo `FR-210-antorcha-explora-vecinas.log`), y comprueba que reproducirlo (`--replay`) da el mismo mapa conocido. Cubre los tres casos del Apéndice B.

## 3. Mediciones

```text
python main.py --bench mapa
python main.py --bench ordenamiento,inventario,retroceso,guardado,ciclo
```

Resultado esperado: las verificaciones previas de cada sección dicen `OK`; los criterios duros (conteos de B, E y F, equivalencia H) se cumplen; `ciclo` queda bajo 20 ms. Los resultados y su comparación con la Parte I y la 001 van a `mediciones.md`; el antes y el después de cualquier decisión que cambie, a `DECISIONES.md`. Ver [contracts/bench-mapa.md](contracts/bench-mapa.md).

## 4. Recorrido manual (humo)

1. Iniciar una partida. La pantalla muestra las salidas de la sala inicial: los destinos aparecen como **«sala sin explorar»**, sin número ni nombre.
2. Escribir `mapa`: aparece solo la sala inicial con sus salidas. Verificar que **no avanzó el tiempo** (mismo reloj en la pantalla siguiente).
3. Cruzar una salida abierta: el destino ahora aparece **con nombre**; `mapa` lista dos salas en orden ascendente de id.
4. Encender una antorcha y entrar a otra sala: `mapa` lista también las vecinas; ningún enemigo de esas vecinas se mueve ni ataca hasta que se entre a ellas.
5. Usar el pergamino: `mapa` vuelve al estado de antes de la acción.
6. Abrir una puerta con cierre automático, alejarse hasta que se cierre y consultar `mapa`: la puerta figura **abierta**. Volver a una de sus salas: pasa a **cerrada**.
7. Guardar, salir, cargar y escribir `mapa`: idéntico al de antes de guardar.
8. Intentar cargar un archivo de partida anterior a esta capacidad: se rechaza indicando la versión encontrada y la esperada.

## 5. Matriz de trazabilidad (requisito → escenario → módulo → prueba)

Pruebas en la raíz del repositorio. Los escenarios son los de `spec.md` (H = historia, número = escenario de aceptación).

| Requisito | Escenarios | Módulo | Prueba |
|---|---|---|---|
| FR-201 | H1.1 | `MapaConocido` | `test_mapa_conocido` (estados) |
| FR-202 | H1.1 | `EstadoJuegoLogica`, `MapaConocido` | `test_mapa_conocido` (instante 0) |
| FR-203 | H1.1, H1.3, H1.4, H1.7, H3.2 | `MapaConocido` | `test_mapa_conocido` (avistar, un solo sentido) |
| FR-204 | H1.2, H1.3, H1.5, H3.4 | `MapaConocido`, `GestorEventos` | `test_mapa_conocido` (entrar) |
| FR-205 | H1.5, H1.6, H3.6 | `MapaConocido` | `test_mapa_conocido` (sin retroceso de estado) |
| FR-206 | H1.2, H2.4 | `MapaConocido` | `test_mapa_conocido` (lo que se conoce de una explorada) |
| FR-207 | H1.6, H2.1, H2.3, H2.4, H3.7 | `MapaConocido`, `GestorEventos` | `test_mapa_conocido` (observación al entrar y al cambiar) |
| FR-208 | H2.1, H2.2 | `MapaConocido` | `test_mapa_conocido` (puerta con cierre automático, Apéndice B) |
| FR-209 | H3.7 | `MapaConocido`, `Vista` | `test_mapa_conocido`, `test_niebla_vista` (sin observar) |
| FR-210 | H3.1 a H3.4 | `MapaConocido` | `test_mapa_conocido` (antorcha, Apéndice B) |
| FR-211 | H3.1 | `MapaConocido`, `GestorEventos` | `test_mapa_conocido`: 0 solicitudes, 0 enemigos activados, agenda y trampas intactas |
| FR-212 | H3.5, H3.6 | `MapaConocido` | `test_mapa_conocido` (encender y apagar) |
| FR-213 | H3.1, H7.2 | todos | `test_niebla_determinismo`: las decisiones de los enemigos son idénticas con el conocimiento desactivado y activado |
| FR-214 | H4.1, H4.2, H4.3, H4.5 | `MapaConocido`, `PergaminoLogica` | `test_niebla_retroceso` (Apéndice B) y equivalencia con `referencia_conocimiento` |
| FR-215 | H4.4 | `MapaConocido`, `RetrocesoLogica` | `test_niebla_retroceso` (sin historial) |
| FR-216 | H5.1 | `Servicio`, `Controlador`, `Vista` | `test_niebla_vista` |
| FR-217 | H5.1, H5.2 | `MapaConocido`, `Logica/ordenamiento` | `test_niebla_vista` (orden ascendente, sin desconocidas) |
| FR-218 | H5.6 | `Controlador` | `test_niebla_vista` (reloj, acciones, historial y log intactos) |
| FR-219 | H2.2, H5.3, H5.4, H5.5 | `Servicio`, `Vista`, `ConocimientoDTO` | `test_niebla_vista`: vista con el grafo completo apagado, sin fugas, búsqueda inversa |
| FR-220 | H6.1, H6.2 | `EstadoGuardadoLogica`, `EstadoGuardadoDTO` | `test_niebla_guardado` |
| FR-221 | H6.3 | `EstadoGuardadoLogica`, `AlmacenPartidaBinario` | `test_niebla_guardado` (versión encontrada y esperada) |
| FR-222 | H6.2, H7.1 | todos | `test_niebla_determinismo`, `test_niebla_guardado`, escenarios de reproducción |
| FR-223 | H7.3 | `MapaConocido` | `--bench mapa` A; `test_niebla_proporcional` (conteos) |
| FR-224 | H7.4 | `MapaConocido` | `test_niebla_proporcional`: salas reveladas y salidas examinadas iguales en tres tamaños; `--bench mapa` B |
| FR-225 | H7.5 | `MapaConocido`, `PergaminoLogica` | `test_niebla_proporcional`: cambios revertidos = r; `--bench mapa` E |
| FR-226 | H7.3 a H7.5 | `bench/mapa.py` | `--bench mapa` |

Sin huecos: los 26 requisitos tienen escenario y prueba. Esta matriz se revisa en `/speckit-analyze` (constitución IX).

## 6. Evidencia que debe quedar en el repositorio

- `specs/002-niebla-de-guerra/mediciones.md` con los resultados de `--bench mapa` y las repeticiones de la Parte I.
- `specs/002-niebla-de-guerra/replays/` con un `partida.log` por escenario.
- `DECISIONES.md` con la sección «002 · Niebla de guerra», que enlaza a `spec.md` y `plan.md` e indica, para cada decisión, si coincide con el plan original y la medición que lo respalda.
