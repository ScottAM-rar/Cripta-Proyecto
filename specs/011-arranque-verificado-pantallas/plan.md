# Plan de implementación: Arranque verificado y pantallas de consola claras

**Rama**: `011-arranque-verificado-pantallas` | **Fecha**: 2026-11-13 | **Especificación**: [spec.md](spec.md)

**Entrada**: `specs/011-arranque-verificado-pantallas/spec.md` (FR-301 a FR-317, con las 3 clarificaciones de la sesión 2026-11-13)

## Resumen

Dos historias P1 que se construyen juntas. **Arranque verificado**: el reporte de resolubilidad que ya existe (003) se muestra al iniciar una partida nueva, `--verificar` lo muestra sin abrir partida y `--forzar` permite jugar una cripta no resoluble. **Pantallas claras**: la sala, el fin de partida, la ayuda y los mensajes de rechazo pasan a ser **funciones puras** que reciben datos ya listos y devuelven texto; la vista solo las imprime.

El enfoque, justificado en [research.md](research.md), tiene seis piezas:

1. **Reutilización exacta de la 003**: `EstadoJuegoServicio.verificar`, el parámetro `forzar` de `iniciarJuego`, `resultadoVerificacion` y `avisoResolubilidad` de la lógica, y `lineas_reporte` / `aviso_forzado` de `ReporteVerificacion`. No se modifican la verificación, su reporte ni la lógica de inicio.
2. **`forzar` viaja por parámetros**: `main.py` (`args.forzar`) → `ControladorJuego(..., forzar=)` → `servicio.iniciarJuego(..., forzar=)`. Ninguna capa lo decide (FR-305).
3. **El reporte al iniciar lo arma el servicio y lo imprime la vista**: el servicio entrega las líneas del reporte (`reporteVerificacion()`, un método de lectura nuevo que llama a `lineas_reporte`); el controlador las pasa a la vista. Un rechazo (`CriptaNoResoluble`) se atrapa en el controlador y muestra el mismo reporte más qué hacer.
4. **Pantallas como funciones puras** en un módulo nuevo `Controlador/Pantallas.py`: `texto_sala`, `texto_fin_partida`, `texto_ayuda`, `texto_error`. `VistaConsola` solo hace `print(texto_…)`. Las pruebas comparan el texto devuelto, sin capturar la salida estándar.
5. **Ayuda desde una sola lista de tuplas** `COMANDOS = ((nombre, sintaxis, descripción), …)`. La ayuda la recorre; la validación de sintaxis también (búsqueda lineal por el primer término; la lista tiene unas 15 filas). Sin `dict` ni `set`.
6. **Códigos de salida en `main.py`**, con constantes con nombre: 0 resoluble, 1 no resoluble, 2 error de uso o lectura (clarificación de FR-302). `--verificar` no instancia la vista (constitución IV).

Lo que **no** cambia: `VerificacionResolubilidad`, `ReporteVerificacion`, `EstadoJuegoLogica` (salvo, si hace falta, un acceso de solo lectura al puntaje), el formato de guardado (formato 8, estado 5), `partida.log` y su formato (el uso de `--forzar` no se registra, FR-304), la sintaxis de todos los comandos existentes.

## Contexto técnico

**Lenguaje/versión**: Python 3.11+ (el del proyecto).

**Dependencias**: solo biblioteca estándar. Sin dependencias nuevas, sin colores ANSI.

**Almacenamiento**: ninguno nuevo. No se toca el guardado ni el log.

**Pruebas**: `unittest`, un archivo por tema, en la raíz como las demás (`test_arranque_*.py`, `test_pantallas_*.py`). Comparan texto exacto y códigos de salida de `main.main(argv)`.

**Plataforma**: consola (Windows y Linux); salida de texto plano en español. Terminales con codificación que no sea UTF-8: se conservan los textos actuales del proyecto (acentos); no se agregan caracteres de dibujo.

**Tipo de proyecto**: juego de consola por capas Controlador → Servicio → Lógica.

**Objetivos de rendimiento**: el ciclo de eventos sigue bajo 20 ms (constitución VII; `--bench ciclo`). Las pantallas se construyen **fuera** del ciclo, pero se miden con un bloque nuevo `--bench pantallas` (sala con 0, 10 y 100 enemigos, resumen final, con la alternativa descartada).

**Restricciones**: sin `dict`/`set` como índice, sin `sorted()`/`list.sort()`, sin `heapq`, `bisect`, `collections`, `networkx`; sin solicitudes de red nuevas; determinista; el modelo no conoce la vista.

**Escala**: la sala actual puede tener decenas de enemigos u objetos; se mide hasta 100.

## Revisión de la constitución

*Puerta antes de la Fase 0; repetida tras el diseño.*

| Principio | Cumple | Cómo |
|---|---|---|
| I. Estructuras propias | Sí | La tabla de comandos es una `list` de tuplas con búsqueda lineal. El texto se arma con `list` y `"\n".join`. Sin `dict`/`set`, `sorted()`, `list.sort()` ni módulos prohibidos. La revisión con búsqueda de importaciones está en la tarea final. |
| II. Determinismo | Sí | Las funciones de pantalla son puras: mismos datos, mismo texto. Sin hora, sin aleatoriedad, sin orden de iteración ajeno a una lista. La semilla aleatoria que genera el controlador cuando el jugador no la da ya existe y no cambia. |
| III. Equivalencia ante el reuso | No aplica | No hay cachés ni reuso de cálculos. Los datos de la pantalla se leen del modelo en cada turno. |
| IV. MVC y adaptadores | Sí | La vista no calcula ni decide: recibe texto o datos. `--verificar` y `--replay` no crean la vista; imprimen desde `main.py`. El modelo no importa la vista. |
| V. Sin datos de una cripta | Sí | Ningún id de sala ni literal de una cripta. |
| VI. Presupuesto y versiones | Sí | Sin solicitudes nuevas: el reporte al iniciar usa las llaves que la partida ya pidió. Formato 8 / estado 5 intactos. |
| VII. Rendimiento medido | Sí | Bloque `pantallas` con la alternativa descartada (concatenar con `+=`), y `ciclo` repetido: debe seguir bajo 20 ms. |
| VIII. Especificación primero | Sí | Este plan no agrega reglas: los textos exactos están en `contracts/`, los requisitos en `spec.md`. |
| IX. Trazabilidad | Sí | Tabla requisito → prueba en [quickstart.md](quickstart.md). |
| X. Cambios de especificación | Sí | Si el diseño obliga a cambiar `spec.md` (ver nota de FR-306 en research D8), se corrige primero la especificación en su propia confirmación. |
| XI. Uso de LLM | Sí | El comando `/speckit-plan` con texto propio se registra en `PROMPTS_LLM_Fer.md` (el registro de Fernanda, para no mezclarlo con `PROMPTS_LLM.md` de Cesar). |

**Resultado**: sin violaciones; no se necesita la tabla de complejidad.

Tras el diseño (Fase 1) se repitió la revisión: sin cambios. El único punto a vigilar es que `Pantallas.py` no llame a ningún método del servicio ni lea el modelo (se prueba con funciones que reciben solo valores simples y DTO ya creados).

## Decisiones y alternativas

Detalle, complejidades y razones en [research.md](research.md). Resumen:

| # | Decisión | Elegida | Alternativas descartadas |
|---|---|---|---|
| D1 | Dónde se arma el reporte al iniciar | Servicio entrega líneas; controlador las pasa a la vista | A) la lógica lo imprime; B) el controlador llama a `lineas_reporte` de la lógica; C) `main.py` lo arma antes de crear el controlador |
| D2 | Cómo se construye la pantalla de sala | Función pura que devuelve texto, con lista de líneas y `"\n".join` | A) imprimir línea a línea desde la vista (como hoy); B) concatenar con `+=`; C) plantilla de texto con `str.format` |
| D3 | Cómo se genera la ayuda | Una lista de tuplas que alimenta ayuda y validación | A) texto fijo escrito a mano; B) `dict` de comandos (prohibido); C) derivarla de la cadena `if` del controlador |
| D4 | Dónde se asignan los códigos de salida | `main.py`, con constantes con nombre | A) en el servicio; B) en el controlador; C) en `ReporteVerificacion` |
| D5 | Cómo viaja `forzar` | Parámetro explícito por capa | A) variable global o de entorno; B) atributo del servicio que cada capa lee |
| D6 | De dónde salen los datos del resumen final | Controlador junta valores existentes y los pasa a la función | A) ampliar `FinPartidaDTO`; B) que la función consulte al servicio |
| D7 | Mensajes de error y rechazo | Función `texto_error(qué_pasó, qué_hacer)` + catálogo de mensajes | A) textos sueltos en cada `print`; B) clase de excepción con mensaje |
| D8 | Estado de la puerta en la pantalla de sala | Abierta / Cerrada / Sin observar (niebla, 002) | A) solo abierta/cerrada (revela lo no visto) |

## Estructura del proyecto

### Documentación de esta capacidad

```text
specs/011-arranque-verificado-pantallas/
├── spec.md
├── plan.md              # este archivo
├── research.md          # decisiones D1 a D8, alternativas y mediciones previstas
├── data-model.md        # datos que reciben las pantallas
├── quickstart.md        # cómo validar a mano y con pruebas; tabla requisito → prueba
├── contracts/
│   ├── cli-argumentos.md    # --verificar, --forzar, códigos de salida
│   ├── pantallas.md         # texto exacto de sala, fin de partida, ayuda y errores
│   └── bench-pantallas.md   # bloque de medición
├── checklists/requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Código fuente (raíz del repositorio)

```text
main.py                          # + --verificar, --forzar; constantes de salida; --verificar sin vista
Controlador/
├── ControladorJuego.py          # + forzar; reporte al iniciar; rechazo; resumen y ayuda; prompt corto
├── Vista.py                     # imprime lo que devuelven las funciones de Pantallas
└── Pantallas.py                 # NUEVO: texto_sala, texto_fin_partida, texto_ayuda, texto_error, COMANDOS
Servicio/
└── EstadoJuegoServicio.py       # + reporteVerificacion(), lineasDeReporte(resultado), CriptaNoResoluble re-exportada,
                                 #   puntaje() de solo lectura (si no existe un acceso equivalente)
bench/
├── pantallas.py                 # NUEVO: bloque --bench pantallas
└── __init__.py                  # + ("pantallas", pantallas.ejecutar) y su texto de ayuda
test_arranque_verificado.py      # NUEVO: reporte al iniciar, --verificar, --forzar, códigos de salida
test_pantallas_texto.py          # NUEVO: texto exacto, orden, idempotencia, español, ayuda, errores
test_pantallas_aislamiento.py    # NUEVO: la vista no calcula; Pantallas no importa Servicio ni Lógica
README.md  DECISIONES.md  PROMPTS_LLM.md
```

**Decisión de estructura**: se mantiene la separación por capas del proyecto. `Pantallas.py` vive en `Controlador/` junto a `Vista.py` porque es presentación, pero **no imprime ni importa el servicio**, para que sus funciones se prueben con valores simples. No se crean carpetas nuevas.

## Plan de medición

Contrato en [contracts/bench-pantallas.md](contracts/bench-pantallas.md). Resumen:

- **Sala**: 0, 10 y 100 enemigos (y objetos en proporción), elegida (lista + `join`) contra descartada (`+=`); verificación previa de que ambas producen el mismo texto.
- **Resumen final**: elegida contra descartada.
- **Ayuda**: construcción y validación de sintaxis sobre la tabla (informativo).
- **Criterio duro**: la sala con 100 enemigos se construye en menos de 20 ms (mediana y máximo); el texto elegido es idéntico al descartado.
- **Ciclo**: se vuelve a correr `--bench ciclo` completo y debe seguir cumpliendo 20 ms (las pantallas no están en el ciclo, pero se confirma que nada cambió en el camino de eventos).
- Resultados y antes/después en `DECISIONES.md`.

## Riesgos

- **Pruebas que comparan texto de la vista**: `test_niebla_vista.py`, `test_terreno_costos.py`, `test_resolubilidad_reporte.py`, `test_viaje_comando.py` y las demás que usan `VistaConsola` o `ControladorJuego` (`test_cazador.py`, `test_equivalencia_cazador.py`, `test_historia_accion.py`, `test_historia_tiempo.py`). Se revisan una por una; cada texto que cambia se actualiza de forma explícita, en una confirmación aparte con la lista de cambios antes/después (FR-317).
- **`CriptaNoResoluble` hereda de `RuntimeError`**: hoy `main.py` lo atrapa como error genérico y sale con 1. Se atrapa antes, en el controlador, para mostrar reporte y guía; el código de salida de ese rechazo sigue siendo 1 (comportamiento actual).
- **Codificación de la consola**: los textos con acentos ya existen; no se agregan símbolos.
