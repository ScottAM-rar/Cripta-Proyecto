# Contrato de `--bench`: bloque `terreno`

Invocación: `python main.py --bench terreno` (también incluido en `--bench` sin argumentos). Sin red ni vista. Criptas sintéticas deterministas por semilla (`bench/datos.py`).

| Sección | Mide | Alternativa descartada que también se mide | Criterio |
|---|---|---|---|
| Un cazador frente a muchos | 1, 10, 50, 200 cazadores | Búsqueda por cazador | Ciclo < 20 ms con decenas (FR-121) |
| Rango pequeño frente a grande | N creciente (miles a decenas de miles) | Búsqueda sin cota | Rango pequeño ≈ constante al crecer N (FR-122) |
| Puertas estables frente a cambiantes | Misma partida con y sin cambios frecuentes | Invalidar con cualquier cambio de puerta | Se informa la ganancia (FR-123) |
| Equivalencia | Decisión con campo vs. desde cero tras cada tipo de evento | — | 100 % idénticas |

Se repiten con la carga nueva: `ciclo` (ahora con cazadores), `guardado` y `retroceso`. El código de salida es distinto de 0 si el ciclo supera 20 ms (comportamiento existente del bloque `ciclo`).
