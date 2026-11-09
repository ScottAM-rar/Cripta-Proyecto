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
| D. Crecimiento | Razón t(3 000) / t(300) de cada estrategia | La razón de `repetida` (medida: 1 112,8, no cerca de 100 como se preveía; el oráculo, además de recorrer desde cero en cada oleada, busca linealmente si una llave ya se obtuvo y su costo se acerca a O(K² · (S + E)); ver [../mediciones.md](../mediciones.md)) | La razón de `incremental` supera 20 (SC-007, FR-346) |

## Medición en la cripta publicada más grande (FR-345)

`--bench` no la cubre porque no usa red ni la caché del usuario. Se mide a mano con el paso 3 de [../quickstart.md](../quickstart.md), con los datos guardados de la cripta (mapa, datos generales y llaves) y sin red. Se arma un `ServicioCripta` sobre un cliente que lee solo de disco sin exigir la cripta completa, y se cronometran con `time.perf_counter_ns` la verificación completa (`verificar`) y la función pura (`verificar_resolubilidad`). Se anota en `mediciones.md` con el id, las salas y las llaves de la cripta medida. No se usa `FuenteSoloLocal` porque `ClienteOffline` exige la cripta completa, con el contenido de todas las salas, y la verificación no necesita ese contenido: descargarlo solo para medir gastaría solicitudes. Si la cripta ya está completa en disco, `FuenteSoloLocal` + `verificar` es una alternativa equivalente. Así se midió cripta-06 en T057: 300 salas, 2,925 ms y 0 solicitudes.
