# Guía de validación (quickstart): Recorrido por niveles

Prerrequisitos: Python 3.11+ y `pip install requests` (el bench no usa la red).

## 1. Pruebas automatizadas

```bash
python -m unittest test_cola_circular test_recorrido_por_niveles
python -m unittest discover -p "test_*.py"     # la suite completa debe seguir pasando
```

Resultado esperado: todas pasan. Las pruebas del recorrido comparan contra una referencia ingenua (`tests_labs/referencia_recorrido.py`) en criptas aleatorias con ciclos, caminos paralelos y conexiones de un solo sentido.

## 2. Mediciones

```bash
python main.py --bench recorrido
```

Resultado esperado: sección A con el recorrido acotado casi constante al crecer la cripta; sección B con las cuatro colas dando el mismo recorrido; sección F con 0 diferencias. Los resultados se guardan en `mediciones.md`.

## 3. Escenarios a mano

Para comprobar a mano el orden (SC-005): en la cripta del ejemplo de `research.md` §4 (origen 1 con salidas a 5 y 3; 3 lleva a 9; 5 lleva a 4) el recorrido esperado es `1, 3, 5, 4, 9` con niveles `0, 1, 1, 2, 2`.

## 4. Matriz de trazabilidad (requisito → escenario → prueba prevista)

| Requisito | Escenarios (spec.md) | Prueba prevista |
|---|---|---|
| FR-501 | Historia 1 (1) | `test_recorrido_por_niveles` (línea de 5 salas) |
| FR-502 | Historia 1 (2) | `test_recorrido_por_niveles` (desempate por id con salidas declaradas en otro orden; ejemplo de `research.md` §4) |
| FR-503 | Historia 1 (3, 4); casos límite | `test_recorrido_por_niveles` (ciclo, caminos paralelos, salidas repetidas, salida a sí misma) |
| FR-504 | Historia 2 (1 a 3); casos límite | `test_recorrido_por_niveles` (límites 0, 2 y mayor que la distancia; límite inválido) |
| FR-505 | Historia 1 (5, 6, 8) | `test_recorrido_por_niveles` (salas inalcanzables) |
| FR-506 | Historia 1 (7) | `test_recorrido_por_niveles` (un solo sentido) |
| FR-507 | Historia 1 (8, 9) | `test_recorrido_por_niveles` (criterio de transitabilidad y sin criterio) |
| FR-508 | Historia 1 (5) | `test_recorrido_por_niveles` (origen sin salidas; sin salidas transitables) |
| FR-509 | Historia 3 (1) | `test_recorrido_por_niveles` (100 repeticiones iguales) |
| FR-510 | Historia 3 (2) | `python main.py --bench recorrido`, sección A |
| FR-511 | Historia 3 (3) | `python main.py --bench recorrido` |
| FR-512 | Historia 1 (10) | `test_recorrido_por_niveles` (origen inexistente) |
| Principio I | — | `test_cola_circular` (sin importaciones prohibidas) |
