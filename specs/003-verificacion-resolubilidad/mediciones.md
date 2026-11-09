# Mediciones: verificación de resolubilidad (capacidad 003)

- **Bench** (T056): `python main.py --bench resolubilidad` · **Código de salida**: 0 · corrido el 2026-11-08 19:05 con la máquina libre.
- **Medición manual** (T057): guion temporal fuera del repositorio, sin red, corrido el 2026-11-09 01:05 en la misma máquina.
- **Python**: 3.12.10 · **Sistema**: Windows AMD64 (Windows 11) · **Semilla**: 2026 (`bench.datos.SEMILLA`).

Los tiempos dependen de la máquina y de su carga: se informa la **mediana** de 5 repeticiones, medida con `time.perf_counter_ns`. Las verificaciones de igualdad de resultados y las cuentas de solicitudes no dependen del reloj.

## Bench: salida completa (T056)

Copiada de la evidencia de T056 en [tasks.md](tasks.md). El bench no se volvió a correr para este documento.

```text
CRIPTA --bench · Python 3.12.10 · Windows AMD64 · 2026-11-08 19:05 · semilla 2026
... midiendo resolubilidad

Resolubilidad (A): incremental frente a recorrido repetido, cadena de llaves encadenadas
  verificación: n = 300: el incremental y la repetida dan el mismo resultado (300 llaves en el orden) OK
  n = 300 (600 salas): incremental (elegido)                         2.71 ms  mediana de 5
  n = 300 (600 salas): repetida (oráculo, descartada)                198.41 ms  mediana de 5
  verificación: n = 3,000: el incremental y la repetida dan el mismo resultado (3,000 llaves en el orden) OK
  n = 3,000 (6,000 salas): incremental (elegido)                     34.29 ms  mediana de 5
  n = 3,000 (6,000 salas): repetida (oráculo, descartada)            220,792.58 ms  1 repetición (la primera superó 10 s)

Resolubilidad (B): índice de llaves, búsqueda binaria frente a búsqueda lineal (INFORMATIVA)
  verificación: K = 100: binaria y lineal dan la misma posición      OK
  K = 100, 100 consultas: búsqueda binaria (elegida)                 44.5 µs  mediana de 5
  K = 100, 100 consultas: búsqueda lineal (descartada)               108.0 µs  mediana de 5
  verificación: K = 1,000: binaria y lineal dan la misma posición    OK
  K = 1,000, 1,000 consultas: búsqueda binaria (elegida)             794.4 µs  mediana de 5
  K = 1,000, 1,000 consultas: búsqueda lineal (descartada)           11.11 ms  mediana de 5
  verificación: K = 10,000: binaria y lineal dan la misma posición   OK
  K = 10,000, 10,000 consultas: búsqueda binaria (elegida)           10.69 ms  mediana de 5
  K = 10,000, 10,000 consultas: búsqueda lineal (descartada)         1,194.44 ms  1 repetición

Resolubilidad (C): límite de 200 ms del incremental (FR-345)
  cadena n = 5,000 (10,000 salas, 5,000 llaves, resoluble)           58.51 ms  mediana de 5; límite 200 ms: CUMPLE
  rejilla 70 × 70 con puertas y llaves al azar (4,900 salas, 1,461 llaves, resoluble) 16.00 ms  mediana de 5; límite 200 ms: CUMPLE

Resolubilidad (D): crecimiento t(3 000) / t(300) (FR-346, SC-007)
  incremental (elegido)                                              12.7  tamaño ×10; límite 20: CUMPLE
  repetida (oráculo, descartada)                                     1,112.8  INFORMATIVA
  Una razón cercana a 10 es crecimiento lineal; cerca de 100, cuadrático. 

Resolubilidad (FR-345, FR-346): CUMPLE.
exit=0
```

## Tablas por sección

### A. Estrategias (cadena de llaves encadenadas)

| n (salas) | Incremental (elegida) | Repetida (oráculo, descartada) | Mismo resultado |
|---|---|---|---|
| 300 (600) | 2,71 ms (mediana de 5) | 198,41 ms (mediana de 5) | Sí (300 llaves en el orden) |
| 3 000 (6 000) | 34,29 ms (mediana de 5) | 220 792,58 ms (1 repetición: la primera superó 10 s) | Sí (3 000 llaves en el orden) |

### B. Índice de llaves (informativa)

| K | Consultas | Búsqueda binaria (elegida) | Búsqueda lineal (descartada) | Misma posición |
|---|---|---|---|---|
| 100 | 100 | 44,5 µs | 108,0 µs | Sí |
| 1 000 | 1 000 | 794,4 µs | 11,11 ms | Sí |
| 10 000 | 10 000 | 10,69 ms | 1 194,44 ms (1 repetición) | Sí |

### C. Límite de 200 ms (FR-345)

| Cripta sintética | Salas | Llaves | Resultado | Incremental | Límite |
|---|---|---|---|---|---|
| Cadena n = 5 000 | 10 000 | 5 000 | Resoluble | 58,51 ms | CUMPLE |
| Rejilla 70 × 70, `fraccion_cerradas=0.15` | 4 900 | 1 461 | Resoluble | 16,00 ms | CUMPLE |

### D. Crecimiento t(3 000) / t(300) (FR-346, SC-007)

| Estrategia | Razón (tamaño ×10) | Límite |
|---|---|---|
| Incremental (elegida) | 12,7 | ≤ 20: CUMPLE |
| Repetida (oráculo, descartada) | 1 112,8 | Informativa |

### Hallazgo del grupo H: la razón de la repetida es 1 112,8, no «cercana a 100»

El contrato ([contracts/bench-resolubilidad.md](contracts/bench-resolubilidad.md)) y [research.md §9](research.md) preveían para la repetida una razón «cercana a 100», que corresponde a O(K · (S + E)) con K ≈ n. La medida fue **1 112,8** (198,41 ms → 220 792,58 ms con tamaño ×10). El oráculo `verificar_repetida` (`tests_labs/referencia_resolubilidad.py`) no solo recorre desde cero en cada oleada. También comprueba si una llave ya se obtuvo con búsquedas lineales sobre listas (`_contiene`), y eso agrega otro factor K. Su costo real se acerca a **O(K² · (S + E))**, por eso la razón con tamaño ×10 se acerca a 1 000 y no a 100. Esto no cambia la conclusión: la incremental crece de forma lineal (12,7) y la alternativa descartada mucho más rápido. El oráculo no se modificó. La frase del contrato y de research.md §9 se corrigió en un cambio de documentos aparte (ver la nota al final de [tasks.md](tasks.md)).

## Medición manual en las criptas publicadas (T057)

### Método, y en qué se aparta del paso 3 de quickstart.md

El paso 3 de [quickstart.md](quickstart.md) pide `crear_fuente_solo_local` (`FuenteSoloLocal` sobre `ClienteOffline`) y `verificar(fuente, <id>)`. **No se pudo usar así** en la cripta más grande. `ClienteOffline` solo da por existente una cripta guardada **por completo**, con datos, salas y el contenido de cada sala. cripta-06 tiene guardados el mapa, los datos generales y las llaves, pero no el contenido de sus salas, así que `verificar` respondía «La cripta cripta-06 no está en la lista de criptas guardada en disco» sin llegar al algoritmo. Lo mismo pasaba con cripta-02 y cripta-03. **El contenido no se descargó** por dos razones: la verificación no lo usa (FR-341) y descargarlo gasta solicitudes. Decisión de Scott: medir sin `FuenteSoloLocal`, de dos maneras y sin red:

1. **Verificación completa.** Primero se intentó la fuente más realista: `ServicioCripta(ClientePersistente(<HTTP que lanza un error si se le llama>, AlmacenDisco("datos_cripta")))`. No sirve sin red: el arranque de la Parte I pide la lista de criptas al empezar la sesión (`ClientePersistente.obtener_criptas`) y los datos generales para validar la versión. En las cinco criptas, `verificar` devolvió `NO SE PUDO VERIFICAR` con `HttpQueFalla: se intentó obtener_criptas()`, y ese fue el único intento de red. No se escribió nada en disco, porque la escritura va después de la respuesta de la red. Evitarlo habría exigido tocar el repositorio, así que se usó una **fuente armada con los datos leídos de disco**: `ServicioCripta` sobre una subclase temporal de `ClienteOffline` que solo cambia `obtener_criptas` para devolver la lista guardada tal cual (sin el filtro de cripta completa). El resto es el código del repositorio: el esqueleto normalizado y su `MapaDTO`, los datos generales, `validar_llaves` y `UbicacionLlavesDTO`. Se mide `verificar(servicio, id)` con un servicio nuevo en cada repetición: lectura de disco, armado del mapa y de las llaves, y algoritmo.
2. **Solo la función pura**: `verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves, id)` con el `MapaCripta` y la `UbicacionLlavesDTO` ya construidos, lo mismo que mide el bench.

Comprobaciones:
- 0 solicitudes: `requests` bloqueado y el cliente de disco no tiene red (`solicitudes_realizadas` = 0).
- `datos_cripta/` sin cambios: sha1 de cada archivo igual antes y después.
- El reporte de (1) es igual carácter por carácter al de (2) en las cinco criptas.
- En cripta-04 y cripta-05, que están completas, el reporte de (1) es además igual al de `FuenteSoloLocal`. Con `FuenteSoloLocal` la mediana fue de 2,481 ms y 2,262 ms, porque compara la versión en disco antes de cada operación.

Datos en disco: los guardó el guion de Scott, que verificó en línea cada cripta del catálogo el 2026-11-09 entre las 00:59 y las 01:00. En cada cripta, la versión del archivo coincide con la de sus datos generales. Sin red no se puede confirmar contra el servidor que esa versión siga vigente. Versión del catálogo guardada: `4b9e75a42be5`. Las criptas sin contenido guardado (02, 03 y 06) se validan sin la comprobación «enemigo contra el contenido guardado» de `validar_llaves`, que solo se hace si hay contenido. Es lo mismo que ocurre en una partida antes de traer esas salas.

### Resultados

| id | Nombre | Versión | Salas | Llaves | Contenido en disco | Resultado | (1) Completa | (2) Pura | Solicitudes |
|---|---|---|---|---|---|---|---|---|---|
| **cripta-06** | Cripta de referencia | `f9ed9afa683d` | **300** | 4 | 0 / 300 | RESOLUBLE | **2,925 ms** | **0,391 ms** | 0 |
| cripta-04 | Catacumbas profundas | `7074a17814ad` | 50 | 3 | 50 / 50 | RESOLUBLE | 0,765 ms | 0,055 ms | 0 |
| cripta-03 | Catacumbas medias | `f9186ac25124` | 40 | 3 | 0 / 40 | RESOLUBLE | 0,659 ms | 0,045 ms | 0 |
| cripta-05 | Cripta sellada | `48bfa3b75055` | 24 | 3 | 24 / 24 | **NO RESOLUBLE** | 0,592 ms | 0,064 ms | 0 |
| cripta-02 | Catacumbas menores | `52532a77ee04` | 20 | 2 | 0 / 20 | RESOLUBLE | 0,458 ms | 0,027 ms | 0 |

cripta-06 es la publicada más grande y es la que cuenta para FR-345 y SC-006: **2,925 ms** con la verificación completa, unas 68 veces por debajo del límite de 200 ms.

### Reportes (`lineas_reporte`)

cripta-06:

```text
Verificación de la cripta cripta-06: RESOLUBLE.
Orden de obtención de llaves:
  1. itm_llave_bronce en la sala 22
  2. itm_llave_hierro en la sala 247, la suelta e-cripta-06-1
  3. itm_llave_plata en la sala 92
  4. itm_llave_negra en la sala 136 (llave de salida)
```

cripta-04:

```text
Verificación de la cripta cripta-04: RESOLUBLE.
Orden de obtención de llaves:
  1. itm_llave_bronce en la sala 2
  2. itm_llave_negra en la sala 4 (llave de salida)
  3. itm_llave_hierro en la sala 16, la suelta e-cripta-04-8
```

cripta-03:

```text
Verificación de la cripta cripta-03: RESOLUBLE.
Orden de obtención de llaves:
  1. itm_llave_bronce en la sala 2
  2. itm_llave_negra en la sala 4 (llave de salida)
  3. itm_llave_hierro en la sala 16, la suelta e-cripta-03-8
```

cripta-05:

```text
Verificación de la cripta cripta-05: NO RESOLUBLE.
Motivo: la sala de salida 20 tiene camino, pero las puertas lo impiden.
Puertas bloqueadas:
  - Sala 7, salida este hacia la sala 22: pide itm_llave_hierro, que está en la sala 24. Ciclo: la llave está detrás de esta puerta o de otras puertas bloqueadas.
  - Sala 12, salida este hacia la sala 24: pide itm_llave_negra (llave de salida), que está en la sala 23. Ciclo: la llave está detrás de esta puerta o de otras puertas bloqueadas.
  - Sala 19, salida norte hacia la sala 20: pide itm_llave_negra (llave de salida), que está en la sala 23. Ciclo: la llave está detrás de esta puerta o de otras puertas bloqueadas.
Salas alcanzables (20): 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21
Salas no alcanzables: 4
```

cripta-02:

```text
Verificación de la cripta cripta-02: RESOLUBLE.
Orden de obtención de llaves:
  1. itm_llave_bronce en la sala 2
  2. itm_llave_negra en la sala 4 (llave de salida)
```

### Observaciones sobre los datos reales

- **cripta-05 («Cripta sellada») no es resoluble.** Las llaves que abren la salida están detrás de las puertas que ellas mismas abren (ciclo): la llave de salida `itm_llave_negra` está en la sala 23 y `itm_llave_hierro` en la sala 24, las dos fuera de las 20 salas alcanzables. **Consecuencia**: con la regla de FR-339, una partida nueva en cripta-05 no inicia sin `--forzar` (`iniciarJuego` lanza `CriptaNoResoluble` antes de crear el log). Con `--forzar` inicia y muestra el aviso (FR-340). No se corrigió ni se ocultó: es un dato del servicio.
- **La versión publicada de cripta-02 cambió**, de `8091a5cd8b7c` a `52532a77ee04`. Al validarla con la versión nueva, `AlmacenDisco.validar_cripta` vació el archivo y se perdió el contenido de las 20 salas que estaba guardado antes; quedaron solo los datos, el mapa y las llaves que trajo el guion. Es el caso de cambio de versión de la spec: lo guardado de una versión anterior no se reutiliza.
- **cripta-01 ya no aparece en la lista guardada de criptas** (`criptas.bin`, que ahora tiene cripta-02 a cripta-06). Su archivo `cripta_cripta-01.bin` (del 2026-10-18) sigue en disco, pero `existe_cripta` responde que no existe. No se midió.

## Estado de los requisitos

| Requisito | Estado | Evidencia |
|---|---|---|
| FR-345 (menos de 200 ms en la cripta publicada más grande, con los datos guardados) | **CUMPLE** | Medición manual: cripta-06 (300 salas, 4 llaves), 2,925 ms (completa) y 0,391 ms (pura), 0 solicitudes. Bench C: cadena de 10 000 salas, 58,51 ms; rejilla de 4 900 salas, 16,00 ms |
| FR-346 (crecimiento aproximadamente lineal, medido con criptas sintéticas a dos tamaños y la alternativa descartada) | **CUMPLE** | Bench A y D: razón 12,7 de la incremental con tamaño ×10, frente a 1 112,8 de la repetida. Resultados iguales en los dos tamaños |
| SC-006 (la verificación de la cripta publicada más grande tarda menos de 200 ms con los datos guardados) | **CUMPLE**, con la salvedad del método | cripta-06, 2,925 ms. La medición usó los datos guardados sin `FuenteSoloLocal` (ver «Método») |
| SC-007 (tamaño ×10 o más: el tiempo no crece más del doble de esa proporción) | **CUMPLE** | Bench D: 12,7 ≤ 20 |

## Conclusión

**Se mantiene el recorrido incremental por oleadas.** Ninguna medición lo contradice:
- Da el mismo resultado que el recorrido repetido.
- Crece de forma aproximadamente lineal (razón 12,7 con tamaño ×10).
- Verifica una cripta sintética de 10 000 salas en 58,51 ms.
- Verifica la cripta publicada más grande (300 salas) en menos de 3 ms con lectura de disco incluida, y en 0,39 ms la función pura.

La alternativa repetida crece cerca de O(K² · (S + E)) en su implementación de referencia (razón 1 112,8) y tarda más de 3 minutos con n = 3 000. La búsqueda binaria de `IndiceLlaves` gana a la lineal en los tres tamaños medidos (de 2,4 veces con K = 100 a unas 112 veces con K = 10 000).
