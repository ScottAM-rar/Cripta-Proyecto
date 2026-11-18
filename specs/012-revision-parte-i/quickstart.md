# Guía de validación: Revisión de la Parte I con la carga nueva

Comandos desde la raíz del repositorio, con Python 3.12 y sin red. Las decisiones están en [research.md](research.md), los contratos en [contracts/](contracts/) y el formato de las tablas en [contracts/filas-medicion.md](contracts/filas-medicion.md).

## 0. Requisito previo: spec corregida

Antes de las tareas hay que corregir la spec (research H1 y H2): el orden de las salidas es N, S, E, O, los valores de los escenarios 4 a 8 de la Historia 1 cambian, los bytes leídos crecen con log n y el commit de referencia es `0b031ec`. Va en un commit propio, anterior al código (principio X).

## 1. M0: el antes (primer paso, sin tocar código)

```
git rev-parse --short HEAD              # debe ser 0b031ec, o un commit posterior que solo cambie documentos
git diff --stat 0b031ec -- adaptadores Logica DTO Controlador Servicio model main.py bench   # sin salida
python main.py --bench cache    --bench-csv specs/012-revision-parte-i/bench-cache-M0.csv
python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M0.csv
python -m unittest discover -p "test_*.py"
```

**Esperado**: código de salida 0 en los dos bloques. La sección 1 da 63 / 61 / 33 / 9 solicitudes y la sección 6 da los aciertos y fallos de la 009 (T050). Se copian la salida, los comandos, la fecha y el commit en `mediciones.md` (FR-377).

## 2. Las pruebas de equivalencia pasan con el código vigente

```
python -m unittest test_vecindad_equivalencia test_cache_equivalencia -v
```

**Esperado**: todo pasa **antes** de cambiar `salas_vecinas` y `cache.py`. Eso demuestra que las referencias escritas en las pruebas reproducen lo vigente (FR-370 a FR-374, FR-387).

## 3. M1: la carga nueva con el código vigente

Con los cambios de medición hechos y sin tocar el código de producción (comprobar con `git diff --stat 0b031ec -- adaptadores/servicioCripta.py adaptadores/cache.py`, que no debe mostrar nada):

```
python main.py --bench cache    --bench-csv specs/012-revision-parte-i/bench-cache-M1.csv
python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M1.csv
```

**Esperado**: en la sección 1, cada fila tiene +1 solicitud por las llaves más las que disparen los cazadores (se ve en la unidad). En la sección 6, +1 en las solicitudes. Aparecen las filas nuevas del bloque de guardado. Toda diferencia con M0 se anota con la causa «carga: …».

## 4. Cambio de código y pruebas

```
python -m unittest test_vecindad_equivalencia test_cache_equivalencia -v
python -m unittest discover -p "test_*.py"
```

**Esperado**: el mismo resultado que en M0. No falla ninguna prueba que pasaba (FR-387).

## 5. M2: el después (dos veces)

```
python main.py --bench cache    --bench-csv specs/012-revision-parte-i/bench-cache-M2.csv
python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M2.csv
python main.py --bench cache    --bench-csv specs/012-revision-parte-i/bench-cache-M2b.csv
python main.py --bench guardado --bench-csv specs/012-revision-parte-i/bench-guardado-M2b.csv
```

**Esperado**:
- las filas de cuenta de M2 y M2b son idénticas (FR-379);
- las secciones 1 y 6 de M2 son iguales a las de M1 (el código no mueve las cuentas, FR-387);
- todas las filas de tiempo de red y de guardado quedan ≤ 2 × su antes (FR-383, FR-384). Si alguna lo pasa, se repite 3 veces y vale la mediana. En la sección 2, eso activa el criterio de cambio de D2;
- los bytes leídos por sala son mucho menos que el tamaño del archivo y crecen como mucho con log n (FR-382).

## 6. Medición manual con la cripta publicada más grande

1. Revisar en `datos_cripta/` qué criptas tienen esqueleto, contenido y catálogo. La más grande es la que se usa; si ninguna está completa, se anota así y no se descarga nada.
2. Generar una partida de formato 8 sin red (`--offline`, o armando el estado con `FuenteSoloLocal`), guardarla y medir con la subclase contadora del bloque de guardado: tamaño del archivo, bytes leídos y tiempo de la primera sala, la del medio y la última, y tiempo de la carga completa.
3. Comprobar que se hicieron 0 solicitudes y anotar el resultado en `mediciones.md` y en la sección 012 de `DECISIONES.md` (FR-382, FR-388).

## Inventario

```
P="adaptadores Controlador DTO Logica model Servicio main.py"
X="--exclude=bench_red.py --exclude=bench_red_mejorado.py"
grep -rnE "(import|from) +(heapq|bisect|collections|networkx)" $P --include=*.py $X
grep -rnE "sorted\(|\.sort\(" $P --include=*.py $X
grep -rnE "\bset\(|frozenset|\{[^}:]+\}" $P --include=*.py $X
grep -rnE "\bdict\(|= \{\}|: dict\b" $P --include=*.py $X
```

**Esperado al final**: cada aparición está en la tabla de `DECISIONES.md` (sección 012) como corregida, justificada o excluida por ser lectura de JSON, y no queda ninguna fuera de la tabla (FR-385, SC-002). `adaptadores/cache.py` ya no aparece. `adaptadores/servicioCripta.py` aparece solo por `_armar_salidas` (uso justificado), y el código de `salas_vecinas` no menciona nada de la lista (FR-375).

## Documentación

- `DECISIONES.md` tiene una sección «012» con enlaces, una tabla de decisiones («¿Coincide con el plan?»), las tablas de antes y después, el inventario y «Hallazgos y límites».
- `DOCUMENTACION_DECISIONES_DISENO.md` tiene una nota con el veredicto y un enlace en las secciones 2, 6 y 8. La evidencia original sigue ahí (FR-388).

## Trazabilidad

| Requisito | Escenarios (spec) | Prueba o evidencia |
|---|---|---|
| FR-370, FR-371, FR-372 | H1-1 a H1-9, H1-13; casos límite | `test_vecindad_equivalencia` (referencia y valores literales) |
| FR-373 | H1-10, H1-11; caso límite | `test_vecindad_equivalencia` (errores y orden de comprobación) |
| FR-374 | H1-1, H1-12, H1-13 | `test_vecindad_equivalencia` (espías de búsquedas y descargas) |
| FR-375 | H2-1, H2-3 | `test_vecindad_equivalencia` (código fuente del método); research D1 |
| FR-376 | H2-2 | `--bench cache` sección 5 (M0 y M2) |
| FR-377, FR-379 | H3-1, H3-2, H3-9; caso límite | `mediciones.md` (M0, M1, M2 y M2b) |
| FR-378 | H3-2, H3-3; caso límite | `mediciones.md`, columna de causa (M0 → M1) |
| FR-380 | H3-5, H3-6 | `DECISIONES.md` §012, tabla de decisiones |
| FR-381, FR-384 | H3-8 | `--bench guardado` (M0, M1 y M2) |
| FR-382 | H4-1 a H4-4 | `--bench guardado`, filas de bytes leídos; medición manual |
| FR-383 | H3-4 | `mediciones.md`, columna de límite |
| FR-385, FR-386 | H5-1, H5-3, H5-4 | inventario (búsqueda de arriba) y `DECISIONES.md` §012 |
| FR-386, FR-387 | H5-2 | `test_cache_equivalencia`; secciones 2 y 6 en M1 y M2; suite completa |
| FR-388 | H3-7, H4-4 | `DECISIONES.md` §012; notas en `DOCUMENTACION_DECISIONES_DISENO.md` §2, §6 y §8 |
