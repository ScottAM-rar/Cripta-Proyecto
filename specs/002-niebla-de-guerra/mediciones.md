# Mediciones: Niebla de guerra y mapa conocido

**Especificación**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Contrato del bench**: [contracts/bench-mapa.md](contracts/bench-mapa.md)

Medido el 2026-10-31 con `python main.py --bench mapa` (Python 3.13, Windows, semilla 2026, mediana de 7 repeticiones tras una de calentamiento; código de salida 0: «Mapa conocido … CUMPLE»). Tres tamaños de cripta, el mayor 50 veces el menor: **400, 2 000 y 20 000 salas**. Las alternativas descartadas existen solo en `bench/mapa.py`. Los tiempos absolutos dependen de la máquina; lo que se compara es la forma de la curva y la razón entre alternativas.

Criterio (lección de la 005): lo **duro** es por conteo; la razón de tiempos solo se informa.

## Criterios duros

| Criterio | Resultado |
|---|---|
| A. Posiciones leídas por consulta de estado y de puerta (FR-223, SC-006) | 1 en los tres tamaños, con k = 1 y k = N/10 |
| B. Salas reveladas, salidas examinadas y cambios por entrada (FR-224) | Sin antorcha: (5, 12, 13) en las seis combinaciones. Con antorcha: (17, 28, 25) en las seis |
| E. Cambios revertidos = cambios registrados (FR-225) | Igual en todos los casos; una entrada con antorcha a una sala del borde de la rejilla son 18 cambios en los tres tamaños (25 en una sala interior, sección B) |
| F. Lecturas del esqueleto por evento con el aviso | 0 (el sondeo hizo 8 000 en 1 000 eventos) |
| H. Equivalencia con la referencia reconstruida desde cero (SC-003) | 150 de 150 pasos idénticos, con pergaminos intercalados |
| Verificaciones previas (C, D, G: misma respuesta en las alternativas) | Todas `OK` |

## A. Consulta del estado de una sala y de una puerta (1 000 consultas)

| Salas | k | Arreglo (elegida) | Lista de conocidas (descartada) |
|---:|---|---:|---:|
| 400 | 1 | 109,6 µs | 39,8 µs |
| 400 | N/10 | 113,5 µs | 659,9 µs |
| 2 000 | 1 | 114,2 µs | 40,2 µs |
| 2 000 | N/10 | 113,8 µs | 3,24 ms |
| 20 000 | 1 | 103,9 µs | 37,1 µs |
| 20 000 | N/10 | 110,3 µs | 33,78 ms |

El arreglo es plano: no cambia con N (×50) ni con k. La lista crece con k (de 0,66 ms a 33,8 ms con k = N/10). **Límite medido**: con k = 1 la lista es unas 3 veces más rápida que el arreglo; el arreglo se justifica porque el jugador explora cientos de salas, donde la lista ya cuesta 6 a 300 veces más.

## B. Exploración al entrar (mediana de una entrada)

| Salas | Mapa | Sin antorcha | Con antorcha |
|---:|---|---:|---:|
| 400 | vacío | 11,4 µs | 20,3 µs |
| 400 | N/10 | 12,3 µs | 22,4 µs |
| 2 000 | vacío | 12,0 µs | 21,4 µs |
| 2 000 | N/10 | 11,5 µs | 20,6 µs |
| 20 000 | vacío | 11,3 µs | 20,8 µs |
| 20 000 | N/10 | 11,5 µs | 20,2 µs |

El costo no depende del tamaño de la cripta ni del mapa conocido. La antorcha cuesta casi el doble (explora hasta cuatro vecinas): 17 salas tocadas frente a 5.

## C. Antorcha: bucle directo frente a `RecorridoPorNiveles` con límite 1

| Salas | Bucle directo (elegida) | `RecorridoPorNiveles` (descartada) |
|---:|---:|---:|
| 400 | 3,4 µs | 9,4 µs |
| 2 000 | 4,3 µs | 8,5 µs |
| 20 000 | 12,8 µs | 18,4 µs |

Ambos exploran el mismo conjunto. La razón baja de 2,8× a 1,4× al crecer la cripta porque **las dos funciones del bench reservan una lista de tamaño N en cada llamada** (para no arrastrar estado entre repeticiones), y ese costo compartido, que el juego no paga, domina con 20 000 salas. La medición preliminar de `research.md` §4 (7× sin esa reserva) se aproxima más al costo real por entrada.

## D. Orden de las exploradas para el comando `mapa`

| Salas | k | Ordenar al consultar (elegida) | Escanear el arreglo | Mantener ordenada (k inserciones) |
|---:|---:|---:|---:|---:|
| 400 | 50 | 67,2 µs | 11,3 µs | 17,2 µs |
| 2 000 | 50 | 68,8 µs | 55,6 µs | 18,0 µs |
| 2 000 | 500 | 653,8 µs | 68,4 µs | 332,0 µs |
| 20 000 | 50 | 71,1 µs | 602,3 µs | 18,9 µs |
| 20 000 | 500 | 668,1 µs | 616,6 µs | 336,6 µs |
| 20 000 | 5 000 | 9,11 ms | 685,0 µs | 8,71 ms |

Comando completo (ordenar y armar el DTO con k salas): 1,88 ms con k = 500 en 2 000 salas y **22,2 ms con k = 5 000 en 20 000 salas**, bajo el umbral de 50 ms de [bench-mapa.md](contracts/bench-mapa.md).

**Lo que dicen los números, con sus límites.** (1) El escaneo del arreglo depende de N (≈ 0,6 ms con 20 000 salas, sin importar k) y cruza al ordenamiento cerca de k ≈ N/40, no en N/8 como sugería la medición preliminar: con k grande el escaneo gana por mucho (0,69 ms frente a 9,1 ms con k = 5 000). (2) «Mantener ordenada» cuesta, repartido, entre 0,3 µs y 1,7 µs por entrada, es decir, hasta un 15 % de lo que cuesta entrar a una sala, y casi lo mismo que ordenar al consultar con k grande (8,71 ms frente a 9,11 ms): en estas cantidades **no hay una ganancia medida que justifique** cargar cada entrada y cada deshacer con una operación O(k). (3) Se mantiene «ordenar al consultar» por tres razones: no toca la entrada ni el deshacer (FR-224, FR-225), el comando es manual y su costo completo queda bajo 25 ms con 5 000 exploradas, y la mitad de ese costo es armar el DTO, no ordenar. **Se revisa** si el k realista de la cripta de referencia supera ≈ N/40, caso en que un híbrido (escanear si k·log k > N) sería mejor.

## E. Reversión con el pergamino (r cambios)

| Salas | r | Diferencias (elegida) | Instantánea de arreglos (descartada) |
|---:|---:|---:|---:|
| 400 | 18 | 4,0 µs | 8,3 µs |
| 400 | 87 | 17,5 µs | 5,7 µs |
| 400 | 344 | 70,1 µs | 5,6 µs |
| 2 000 | 18 | 4,0 µs | 23,2 µs |
| 2 000 | 358 | 71,4 µs | 23,2 µs |
| 20 000 | 18 | 17,1 µs | 952,9 µs |
| 20 000 | 87 | 69,0 µs | 881,6 µs |
| 20 000 | 363 | 156,1 µs | 793,5 µs |

Las diferencias crecen con r y no con N; la instantánea crece con N y no con r. **Límite medido**: con 400 salas y r ≥ 87 la instantánea gana (5,7 µs frente a 17,5 µs). En una rejilla, una entrada con antorcha cambia 18 elementos en el borde y 25 en una sala interior, donde las diferencias ganan o empatan, y la instantánea guardaría además 5 copias de los arreglos en el historial (5·N), que con 20 000 salas serían cientos de miles de posiciones.

## F. Observación de puertas (1 000 eventos)

| Caso | Aviso (elegida) | Sondeo tras cada evento (descartada) |
|---|---:|---:|
| Cambios raros (1 %) | 122,1 µs | 20,51 ms |
| Cambios frecuentes (50 %) | 2,66 ms | 20,10 ms |

Dejan las mismas puertas recordadas. El aviso gana 170× con cambios raros y 7,5× con cambios frecuentes. El sondeo cuesta lo mismo con cualquier frecuencia porque lee todas las puertas en cada evento.

## G. Vista del conocimiento para `BuscadorRutas`

| Salas | Vista directa (elegida) | Materializar y buscar (descartada) |
|---:|---:|---:|
| 400 | 422,0 µs | 1,05 ms |
| 2 000 | 2,03 ms | 1,86 ms |
| 20 000 | 1,89 ms | 6,84 ms |

Mismos costos hallados. **Límite**: con 2 000 salas las dos se igualan (los rangos se solapan: 1,12–3,35 ms frente a 1,34–2,66 ms); la vista directa gana con claridad en el menor y en el mayor tamaño. No hay ventaja medida que justifique materializar.

## Mediciones de la Parte I que esta capacidad repite

Según P4 del plan, a la 002 le tocan `ordenamiento` e `inventario`; `retroceso`, `guardado` y `ciclo` los repiten sus responsables.

| Bloque | Resultado con la carga nueva | ¿Cambia alguna decisión? |
|---|---|---|
| `ordenamiento` | Esta capacidad **no modifica** `Logica/ordenamiento.py`; el comando `mapa` lo usa sobre una copia. En clave cara (4 campos) con N = 5 000 aleatoria la mezcla tarda 20,5 ms y el quicksort descartado 12,4 ms: razón 1,66, frente a 1,60 en `DOCUMENTACION_DECISIONES_DISENO.md` §5 (10,26 ms y 6,43 ms, medidos en otra máquina). El orden relativo no cambia | No |
| `inventario` | Código sin cambios por esta capacidad. Se repite el bloque completo y se archiva su salida; esta capacidad no agrega uso del inventario | No |
| `ciclo` (informativo) | 10 cazadores: 314 µs; 50 cazadores: 1,48 ms (peor de 30 ciclos 1,83 ms); 300 esbirros: 5,62 ms; el estrés de 1 000 esbirros (20,2 ms) «no decide el veredicto», como antes. Veredicto del bloque: **CUMPLE** el límite de 20 ms | No |
| `retroceso`, `guardado` (informativo, `PYTHONIOENCODING=utf-8 python main.py --bench guardado,retroceso`, código 0) | `retroceso`: las diferencias siguen ganando a las instantáneas cuando el mundo crece (3 000 entidades, 1 cambio: 548 µs frente a 28,9 ms). `guardado`: 1 000 salas ocupan 408 161 B en binario (en la 001, 408 092 B: **+69 B**, el conocimiento de una partida recién empezada); binario 2,95× menor que JSON, igual que en la 001; cargar una sala suelta 313 µs frente a 15,25 ms del JSON (≈ 49×; la 001 midió ≈ 128× en otra máquina). Con conocimiento: ≈ 37 B por sala explorada (607 de 1 000 exploradas: 22 664 B, ≈ 5,5 % del archivo). Los tiempos absolutos no se comparan con la 001: cambió de máquina | No. **Quién repite estos bloques como responsable sigue por confirmar** |

## Pendiente

- Confirmar quién repite `retroceso` y `guardado` como responsable (la 002 solo los corrió de forma informativa).
- Aviso de herramienta, ajeno a esta capacidad: `--bench guardado` imprime «→» y falla con `UnicodeEncodeError` si la salida se redirige en una consola Windows con codificación cp1252; se corre con `PYTHONIOENCODING=utf-8`.
