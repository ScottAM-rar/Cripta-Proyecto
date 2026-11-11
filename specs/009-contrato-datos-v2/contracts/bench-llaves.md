# Contrato: bloque `llaves` de `--bench`

```text
python main.py --bench llaves
python main.py --bench llaves --bench-csv llaves.csv
```

No usa red ni vista. Usa criptas sintéticas deterministas por semilla (`tests_labs/cripta_sintetica.py`) y `HttpConfigurable` para contar solicitudes. Se registra en `bench/__init__.py` (`BLOQUES`).

## Secciones

| Sección | Filas | Alternativa descartada | Código de salida |
|---|---|---|---|
| A. Presupuesto con cazadores (FR-322, FR-323) | Por cada lado (10, 20, 40), cazadores (1, 4, 16) y regla (`saltos`, `costo`): solicitudes totales y solicitudes disparadas por enemigos. Promedio de 5 semillas | Precarga por costo (solo existe en el bench) | Informativa: no hace fallar |
| B. Guardar llaves | Por cada cantidad de salas con contenido (50, 500, 5 000): µs para guardar y para leer, con la opción A y con la B | B (archivo aparte) | Falla si A supera los 50 ms con 5 000 salas (research.md §4) |
| C. Entradas repetidas | k = 10, 100 y 1 000: µs de validación ordenando frente a comparando todas las parejas | Todas las parejas | Informativa |
| D. Una solicitud por cripta | Partida guionada con la API falsa v2: solicitudes `("llaves", …)` en la primera partida, en la segunda con la misma versión y en `--offline` | — | Falla si no son exactamente 1, 0 y 0 (SC-001, SC-002) |

## Protocolo de la sección A

1. `esqueleto_rejilla(lado, lado, semilla, costo_max=9)`. Los cazadores se colocan con `random.Random(semilla)` a una distancia de 4 o más salidas del jugador.
2. Para cada regla se crea un `HttpConfigurable` nuevo y una carpeta temporal nueva, así que se arranca sin nada guardado.
3. Guion fijo: 60 movimientos del jugador que se generan con la semilla y solo usan salidas abiertas.
4. Una solicitud cuenta como «disparada por un enemigo» si ocurre dentro de una carga que no corresponde a la sala del jugador. El bench envuelve `ingresarEnSala` para marcarlo; no se modifica el juego.
5. La regla `costo` se implementa como subclase de `ServicioCripta` en `bench/llaves.py`, que sobrescribe solo el orden con que se llena el lote de `precargar_vecinas`.

El resultado y la recomendación se copian a `specs/009-contrato-datos-v2/mediciones.md` (FR-324).
