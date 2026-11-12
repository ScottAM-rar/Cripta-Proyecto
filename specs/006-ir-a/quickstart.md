# Guía de validación: Comando «ir a»

**Carpeta**: `006-ir-a`. Cómo comprobar de punta a punta que la capacidad cumple. No contiene código de implementación (eso va en `tasks.md`).

## Requisitos previos

- Python 3.11+ y el repositorio en la rama de la capacidad. Sin red: todo usa criptas sintéticas y la API falsa de `tests_labs/`.
- La 002 integrada (formato 8, estado 5): el conocimiento y su vista existen.

## 1. Pruebas automatizadas

```text
python -m unittest discover -p "test_viaje_*.py"
python -m unittest discover -p "test_*.py"
```

Resultado esperado: todas en OK; las pruebas anteriores (001 a 009) siguen iguales. Los laboratorios de `tests_labs` no cambian.

## 2. Los casos del Apéndice B

| Caso | Escenario | Prueba | Resultado esperado |
|---|---|---|---|
| **B-N1** | `ir a` hacia una sala solo avistada o desconocida | `test_viaje_rechazo.py` | Rechazo con motivo; reloj, conocimiento, log y pergamino idénticos (FR-237, FR-238) |
| **B-N2** | El mapa recuerda abierta una puerta cerrada; el viaje la observa al llegar a su sala | `test_viaje_puerta_cerrada.py` | Con alterna: la ruta se recalcula y llega; sin alterna: se detiene en esa sala, mapa actualizado, sin tiempo adicional (FR-239 a FR-241) |
| **B-N3** | La ruta entra a una sala con enemigos dormidos | `test_viaje_enemigos.py` | Los enemigos se activan como en una entrada a mano (§2.4) y el viaje se detiene allí (FR-242, FR-243) |
| **B-N6** | Un pergamino durante el viaje | `test_viaje_pergamino.py` | Se revierte solo el último paso y el viaje no continúa (FR-244, FR-245) |

La API falsa de la 009 ya nombra estos casos con los pasos `("ir_a", sala)` y `("pergamino",)`; esta capacidad es la que los ejecuta.

## 3. Determinismo y equivalencia

```text
python -m unittest test_viaje_determinismo test_viaje_equivalencia test_viaje_registro
```

Comprueba: dos ejecuciones dan el mismo `partida.log`, con y sin contenido de salas descargado (FR-247, FR-248); reutilizar el campo de costos da las mismas decisiones que recalcularlo en cada paso (constitución III); la repetición de un viaje es fiel (FR-252).

## 4. Rendimiento

```text
python main.py --bench ir_a
```

Esperado: sección G con mediana y máximo ≤ 5 ms por paso en 400 y 2 000 salas con el 10 % explorado, y sección I con lo mismo en 400 salas con el mapa completo (criterio duro; en 2 000 y 20 000 salas con el mapa completo se informa); en 20 000 salas se informan, sin decidir, el paso con captura de punto de control y el recálculo tras una puerta cerrada; secciones A a F, H e I con sus verificaciones en OK; cierre «Ir a (paso ≤ 5 ms y equivalencias): CUMPLE». Después: `python main.py --bench ciclo` (informativo; debe seguir bajo 20 ms).

## 5. Prueba manual en consola

1. Iniciar una partida (`python main.py`) y recorrer a mano tres o cuatro salas.
2. `mapa` para ver los ids de las salas exploradas.
3. `ir a <id de una sala explorada>`: el personaje camina hasta ella y se muestra el resumen (pasos y tiempo).
4. `ir a <id de una sala solo avistada>`: se rechaza con el motivo; `historia #k` y el reloj no cambian.
5. Encender la antorcha y repetir un viaje: el `mapa` posterior muestra las vecinas exploradas, igual que caminando.
6. Revisar `partida.log`: aparecen `IR_A`, los movimientos y `FIN_IR_A`; `python main.py --replay <log>` termina sin «no es fiel».

## Trazabilidad requisito → escenario → prueba

| Requisitos | Historia | Prueba |
|---|---|---|
| FR-231 a FR-236 | 1 | `test_viaje_ruta.py` |
| FR-237, FR-238 | 2 (B-N1) | `test_viaje_rechazo.py`, `test_viaje_comando.py` |
| FR-239 a FR-241 | 3 (B-N2) | `test_viaje_puerta_cerrada.py` |
| FR-242, FR-243, FR-249 | 4 (B-N3) | `test_viaje_enemigos.py` |
| FR-244, FR-245 | 4 (B-N6) | `test_viaje_pergamino.py` |
| FR-246 | 5 | `test_viaje_antorcha.py` |
| FR-247, FR-248 | 6 | `test_viaje_determinismo.py`, `test_viaje_sin_red.py` |
| FR-250, FR-251 | — | `--bench ir_a` (sección G y demás) |
| FR-252 | — | `test_viaje_registro.py` |
