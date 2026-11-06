# Guía de validación (quickstart): Recorrido por niveles

Prerrequisitos: Python 3.11+ y `pip install requests` (el bench no usa la red).

## 1. Pruebas automatizadas

```bash
python -m unittest test_cola_circular test_recorrido_por_niveles test_recorrido_determinismo test_recorrido_proporcional
python -m unittest discover -p "test_*.py"     # la suite completa debe seguir pasando
```

Resultado esperado: todas pasan. Las pruebas del recorrido comparan contra una referencia ingenua (`tests_labs/referencia_recorrido.py`) en criptas aleatorias con ciclos, caminos paralelos, conexiones de un solo sentido y salidas hacia salas que no existen; los resultados de los escenarios están escritos a mano en las pruebas. La proporcionalidad (SC-004) se comprueba contando salas visitadas y salidas examinadas, no con tiempos.

## 2. Mediciones

```bash
python main.py --bench recorrido
```

Resultado esperado: sección A con los mismos conteos (salas visitadas y salidas examinadas) del recorrido acotado en las tres criptas y la razón de tiempos como dato informativo; sección B con las cuatro colas dando el mismo recorrido; sección F con 0 diferencias. Los resultados se guardan en `mediciones.md`.

## 3. Escenarios a mano

Para comprobar a mano el orden (SC-005): en la cripta del ejemplo de `research.md` §4 (origen 1 con salidas a 5 y 3; 3 lleva a 9; 5 lleva a 4) el recorrido esperado es `1, 3, 5, 4, 9` con niveles `0, 1, 1, 2, 2`.

## 4. Matriz de trazabilidad (requisito → escenario → prueba)

Comprobada con un recorrido automático de las pruebas y del bench (cada nombre de prueba cita su requisito): ningún FR-501 a FR-513 queda sin cubrir. Resultados esperados de los escenarios escritos a mano en `test_recorrido_por_niveles`.

| Requisito | Escenarios (spec.md) | Prueba |
|---|---|---|
| FR-501 | Historia 1 (1) | `test_recorrido_por_niveles`: `TestOrdenYAlcance` (línea de 5 salas, desde un extremo y desde el medio) |
| FR-502 | Historia 1 (2) | `TestOrdenYAlcance` (salidas declaradas en orden contrario al de los ids; ejemplo `1, 3, 5, 4, 9`) |
| FR-503 | Historia 1 (3, 4); casos límite | `TestOrdenYAlcance` (ciclo, caminos paralelos, salidas repetidas, salida a sí misma, origen en un ciclo); `TestEquivalenciaConLaReferencia` |
| FR-504 | Historia 2 (1 a 3); casos límite | `TestLimiteDeNiveles` (límites 0, 1, 2 y mayor que la distancia; límites inválidos; equivalencia con límite) |
| FR-505 | Historia 1 (5, 6, 8) | `TestOrdenYAlcance` (salas sin camino desde el origen) |
| FR-506 | Historia 1 (7) | `TestOrdenYAlcance` (un solo sentido, en los dos sentidos) |
| FR-507 | Historia 1 (8, 9) | `TestOrdenYAlcance` (criterio de transitabilidad, sin criterio, evaluación de la arista) |
| FR-508 | Historia 1 (5) | `TestOrdenYAlcance` (origen sin salidas; ninguna salida transitable) |
| FR-509 | Historia 3 (1) | `test_recorrido_determinismo` (100 repeticiones, recorridor reutilizado, otro orden de las salas del esqueleto) |
| FR-510 | Historia 3 (2) | `test_recorrido_proporcional` (conteo de salas visitadas y salidas examinadas en 400, 4 900 y 40 000 salas: criterio de SC-004); `python main.py --bench recorrido`, sección A (razón de tiempos, informativa) |
| FR-511 | Historia 3 (3) | `python main.py --bench recorrido` (secciones A a F) |
| FR-512 | Historia 1 (10) | `TestOrigenYSalasInexistentes` (origen inexistente o de tipo no entero) |
| FR-513 | Historia 1 (11) | `TestOrigenYSalasInexistentes` (salida hacia un hueco y hacia un id fuera de rango); también en `TestEquivalenciaConLaReferencia` |
| Principio I | — | `test_cola_circular` (sin importaciones prohibidas), `test_monticulo_minimo` |
| SC-005 | — | Los resultados esperados de `test_recorrido_por_niveles` son listas literales escritas a mano |
