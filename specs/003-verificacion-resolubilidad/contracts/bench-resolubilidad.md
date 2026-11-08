# Contrato: bloque `resolubilidad` de `--bench`

```text
python main.py --bench resolubilidad
python main.py --bench resolubilidad --bench-csv resolubilidad.csv
```

No usa red, vista ni la caché del usuario. Usa criptas sintéticas deterministas por semilla (`tests_labs/cripta_sintetica.py`, semilla `bench.datos.SEMILLA`). Se registra en `bench/__init__.py` (`BLOQUES`) y, como `llaves` y `recorrido`, tiene su propio indicador de cumplimiento en el resumen final. Las mediciones se corren con la máquina libre y se copian a [../mediciones.md](../mediciones.md).

## Criptas

- `esqueleto_llaves_encadenadas(n, semilla)` ([../data-model.md §7](../data-model.md)): pasillo de n salas con una lateral por sala; la puerta i → i+1 pide la llave que está en la lateral de i. K ≈ n oleadas. Es el peor caso de la alternativa repetida.
- Rejilla `esqueleto_rejilla(70, 70, semilla, fraccion_cerradas=0.15)` a la que el bench asigna llaves (con `random.Random(semilla)`) a cada puerta cerrada y las ubica en salas al azar: carga realista sin estructura de cadena.

El mapa (`MapaCripta`) y la `UbicacionLlavesDTO` se construyen **antes** de medir: se mide la verificación con los datos ya descargados.

## Secciones

| Sección | Filas | Alternativa descartada | Falla si |
|---|---|---|---|
| A. Estrategias | Por n ∈ {300, 3 000} y estrategia (`incremental`, `repetida`): ms (mediana de 5; la repetida en n = 3 000 con 1 repetición si la primera supera 10 s, anotado en la fila) | `repetida`: recorrido completo desde la sala inicial en cada oleada | Las dos estrategias no dan el mismo `ResultadoVerificacion` (principio III) |
| B. Índice de llaves | Por K ∈ {100, 1 000, 10 000}: µs de resolver L + E consultas con búsqueda binaria y con búsqueda lineal | Búsqueda lineal | Informativa |
| C. Límite | ms de `incremental` en la cadena con n = 5 000 y en la rejilla de 70 × 70 (mediana de 5) | — | Alguna supera 200 ms (FR-345) |
| D. Crecimiento | Razón t(3 000) / t(300) de cada estrategia | La razón de `repetida` (se espera cerca de 100) | La razón de `incremental` supera 20 (SC-007, FR-346) |

## Medición en la cripta publicada más grande (FR-345)

`--bench` no la cubre porque no usa red ni la caché del usuario. Se mide a mano con el paso 3 de [../quickstart.md](../quickstart.md): con la cripta ya guardada, `FuenteSoloLocal` + `verificar` cronometrado con `time.perf_counter_ns`, y se anota en `mediciones.md` con el id y el tamaño de la cripta medida.
