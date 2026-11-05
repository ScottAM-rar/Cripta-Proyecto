# Contrato de `--bench`: bloque `recorrido`

Invocación: `python main.py --bench recorrido` (también incluido en `--bench` sin argumentos). Sin red ni vista. Criptas sintéticas deterministas por semilla (`bench/datos.py`, `tests_labs/cripta_sintetica.py`).

| Sección | Mide | Alternativa descartada que también se mide | Criterio |
|---|---|---|---|
| A. Acotado frente a sin límite | Límites 2 y 5 niveles y sin límite, en rejillas de 400, 4 900 y 40 000 salas, origen central. Informa cuántas salas se visitaron | Sin límite (el recorrido completo) | SC-004: con límite 2, el tiempo en 40 000 salas ≤ 2 × el de 400 |
| B. Cola circular frente a las alternativas | La cola circular elegida | `list` con `pop(0)` · `list` con índice de cabeza · dos listas por nivel | Mismo recorrido en todas (verificación previa); se informa el tiempo de cada una |
| C. Dos formas de cripta | B en rejilla (frontera angosta) y en árbol de ramificación 3 de 29 524 salas (frontera ancha) | — | Muestra dónde se degrada `pop(0)` |
| D. Orden dentro del nivel | `ordenar_adaptativo` por nivel | Montículo con clave `(nivel, id)` | Se informa la ganancia; si el montículo gana, se cambia la decisión |
| E. Referencia actual | El recorrido nuevo | `ServicioCripta.salas_vecinas` (con `deque` y búsqueda lineal) | Informativa: no se modifica esa función |
| F. Equivalencia | Recorrido frente a una referencia ingenua en criptas aleatorias | — | 0 diferencias |

El código de salida de `--bench` es distinto de 0 si falla la verificación previa de B, si la sección F tiene diferencias o si no se cumple SC-004 en A. Las alternativas descartadas (`pop(0)`, índice de cabeza, dos listas, montículo) existen **solo** en `bench/recorrido.py`.
