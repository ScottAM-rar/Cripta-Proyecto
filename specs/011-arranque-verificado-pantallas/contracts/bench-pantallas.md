# Contrato: bloque `--bench pantallas`

Cubre la constitución VII y la sección «Plan de medición» de [plan.md](../plan.md). Se ejecuta con `python main.py --bench pantallas` (y entra en `--bench` completo). Sin red ni vista; criptas y datos sintéticos deterministas por semilla; se usa el medidor común de `bench/medicion.py` (mediana, mínimo y máximo); sin `dict`/`set`/`sorted()`.

## Secciones

| Sección | Elegida | Descartada | Qué se mide |
|---|---|---|---|
| A. Sala con 0, 10 y 100 enemigos | lista de líneas + `"\n".join` | concatenar con `+=` | µs por pantalla; cantidad de objetos proporcional (0, 10, 100) |
| B. Resumen final | lista + `join` | `+=` | µs por resumen |
| C. Ayuda | recorrer `COMANDOS` | texto fijo | µs por llamada (informativo) |
| D. Ciclo de eventos | sin cambios | — | `--bench ciclo` repetido; límite 20 ms |

## Verificaciones previas (si fallan, el tiempo no vale)

- El texto de la elegida es **idéntico** al de la descartada en cada tamaño.
- La construcción dos veces con los mismos datos da el mismo texto.

## Criterios

| Criterio | Tipo |
|---|---|
| Texto elegido == texto descartado (A, B) | duro |
| Sala con 100 enemigos: mediana y máximo < 20 ms | duro |
| Razón de tiempos elegida/descartada | informa |
| `ciclo` < 20 ms (ya existente) | duro |

La salida imprime por sección las filas `elegida` y `descartada` con `anotar(...)`, una fila `CUMPLE` / `NO CUMPLE` por criterio duro, y una frase final `Pantallas: CUMPLE.` o `NO CUMPLE`. `bench/__init__.py` registra `("pantallas", pantallas.ejecutar)`, lo incluye en el texto de ayuda de `--bench` y en la decisión de código de salida de `bench.ejecutar`.

Los resultados se copian a `DECISIONES.md` (sección 011) con la cifra de `ciclo` de antes y después.
