# Guía de validación: Arranque verificado y pantallas de consola claras

Cómo comprobar la capacidad de punta a punta. Detalles de formato en [contracts/](contracts/) y de datos en [data-model.md](data-model.md).

## Requisitos previos

- Python 3.11 o superior; el repositorio clonado. Sin dependencias extra.
- Spec Kit instalado con la versión fija indicada en el README (el comando exacto se documenta ahí, FR-314).
- Para probar sin red: `--offline` con datos ya descargados, o las criptas sintéticas de `tests_labs/`.

## 1. Pruebas automáticas

```text
python -m unittest test_arranque_verificado test_pantallas_texto test_pantallas_controlador test_pantallas_aislamiento bench.test_bench_pantallas -v
.venv/Scripts/python.exe -m unittest discover -p "test_*.py"          # toda la suite (con el intérprete del entorno virtual: el del sistema no tiene `requests`): nada de las capacidades anteriores se rompe
```

## 2. Arranque verificado a mano

```text
python main.py --verificar <cripta resoluble>        # reporte RESOLUBLE; echo del código = 0
python main.py --verificar <cripta no resoluble>     # reporte NO RESOLUBLE; código = 1
python main.py --verificar cripta_que_no_existe      # NO SE PUDO VERIFICAR; código = 2
python main.py --verificar                           # mensaje de uso; código = 2
python main.py                                       # partida nueva: el reporte sale antes del primer turno
python main.py --forzar                              # cripta no resoluble: reporte + AVISO y se juega
```

El código de salida: `echo $?` en Bash, `echo $LASTEXITCODE` en PowerShell.

## 3. Pantallas a mano

En una partida: escribir `ayuda` (lista todos los comandos con su sintaxis), moverse (la pantalla de sala mantiene el mismo orden), provocar un rechazo (`xyz`, una dirección sin salida) y terminar la partida para ver el resumen.

## 4. Medición

```text
python main.py --bench pantallas
python main.py --bench ciclo                         # debe seguir bajo 20 ms
```

## Tabla requisito → escenario → prueba (principio IX)

| Requisito | Escenario | Prueba (archivo, comprobación) |
|---|---|---|
| FR-301 | H1-1, H1-2 | `test_arranque_verificado`: el reporte se imprime antes del primer turno, con cripta resoluble y no resoluble |
| FR-302 | H1-4 | `test_arranque_verificado`: `main.main(["--verificar", id])` devuelve 0, 1 y 2 (resoluble, no resoluble, inexistente); no se abre partida ni log; no se instancia la vista |
| FR-303 | H1-2, H1-3, H1-5 | `test_arranque_verificado`: sin `--forzar` se rechaza (salida 1); con `--forzar` se abre; en cripta resoluble `--forzar` no agrega aviso |
| FR-304 | H1-3 | `test_arranque_verificado`: el aviso sale al iniciar; `partida.log` no contiene `forzar` y es idéntico al de una partida sin forzar |
| FR-305 | H1-6 | `test_arranque_verificado`: servicio doble que registra el `forzar` recibido por `iniciarJuego` |
| FR-306 | H2-1, H2-2 | `test_pantallas_texto`: texto exacto de la sala en ≥ 5 situaciones; secciones vacías con `(ninguno)` |
| FR-307 | H2-3 | `test_pantallas_texto`: texto exacto del resumen, motivo vacío, sin mapa |
| FR-308, FR-310 | H2-5 | `test_pantallas_texto`: catálogo completo de mensajes: dos partes, español, sin términos en otro idioma |
| FR-309 | H2-4 | `test_pantallas_texto`: la ayuda contiene todos los comandos reconocidos y cada fila es reconocida |
| FR-311 | H2-6 | `test_pantallas_texto`: dos construcciones iguales; sin `\x1b` |
| FR-312 | H2-1 | `test_pantallas_aislamiento`: `Pantallas.py` no importa `Servicio` ni `Logica`; la vista imprime exactamente lo devuelto |
| FR-313 | — | pruebas existentes de comandos (`test_viaje_comando`, `test_historia_*`, …) sin cambios de sintaxis; prueba de la lista `COMANDOS` |
| FR-314 | — | revisión del README (SC-308) |
| FR-315 | — | `test_persistencia_v7` y las de guardado siguen pasando; comparar `partida.log` antes y después |
| FR-316 | — | búsqueda de importaciones y usos prohibidos (`dict`/`set` como índice, `sorted()`, `list.sort()`, `heapq`, `bisect`, `collections`, `networkx`) en los archivos nuevos y tocados; `test_sin_red.py` sigue pasando |
| FR-317 | — | lista de pruebas actualizadas y texto cambiado, en la confirmación correspondiente |

Escenarios `H1-n` / `H2-n` = n-ésimo escenario de aceptación de la historia 1 / 2 de [spec.md](spec.md).

## Criterio de cierre

Todo lo anterior pasa; `--bench pantallas` y `--bench ciclo` cumplen; el README explica los argumentos nuevos, la instalación de spec-kit con versión fija y cómo ejecutar las pruebas de aceptación; `DECISIONES.md` enlaza a `spec.md` y `plan.md` con las cifras medidas.
