# Contrato de `--bench`: bloque `mapa`

Invocación: `python main.py --bench mapa` (también incluido en `--bench` sin argumentos). Sin red ni vista. Criptas sintéticas deterministas por semilla (`bench/datos.py`, `tests_labs/cripta_sintetica.py`). **Requisitos**: FR-223 a FR-226; constitución VII.

## Tamaños

Tres tamaños de cripta, el mayor 50 veces el menor: **400, 2 000 y 20 000 salas** (rejillas 20×20, 20×100 y 100×200). Cada medición usa la mediana de 7 repeticiones tras una de calentamiento (`bench/medicion.py`).

Lección de la 005: **el criterio duro es por conteo** (cuántas salas y salidas se examinan); la razón de tiempos solo se informa, porque a decenas de microsegundos es frágil.

## Secciones

| Sección | Mide | Alternativa descartada que también se mide | Criterio |
|---|---|---|---|
| A. Consulta | Estado de una sala y puerta recordada, 1 000 consultas, k fijo y k proporcional a N | Recorrer una lista de salas conocidas | Elegida no crece con N ni con k (FR-223); se informa la razón |
| B. Exploración al entrar | `entrar` sin y con antorcha en un mapa conocido grande (k = N/10) frente a uno vacío | — | **Duro**: salas reveladas y salidas examinadas por entrada iguales en los tres tamaños y con k distinto (FR-224). Tiempo informativo |
| C. Antorcha | Explorar las vecinas con bucle directo | `RecorridoPorNiveles` con límite 1 | Ambos exploran el mismo conjunto (verificación); se informa la razón |
| D. Orden del comando | Obtener las exploradas ascendentes, k = 50, 500 y 5 000 por tamaño | Escanear el arreglo de 1 a N; lista siempre ordenada | Tres resultados iguales (verificación); **se informan los cruces** y el tiempo del comando completo (armar el DTO incluido) |
| E. Reversión | Deshacer una acción de r = 1, 10 y 100 cambios | Instantánea de los arreglos | **Duro**: cambios revertidos = r en los tres tamaños (FR-225). Tiempo informativo |
| F. Observación de puertas | 1 000 eventos con cambios de puerta raros (1 %) y frecuentes (50 %) | Sondeo de las puertas de la sala actual tras cada evento | Se informa la ganancia; **duro**: 0 observaciones por evento sin cambio de puertas |
| G. Vista para rutas | Una búsqueda `BuscadorRutas` sobre la vista, tras un cambio del conocimiento | Mapa conocido materializado | Mismos costos hallados (verificación); se informa |
| H. Equivalencia | Conocimiento incremental frente a la referencia reconstruida desde cero tras cada acción y cada deshacer | — | 100 % idénticos (SC-003) |

## Se repiten con la carga nueva

| Bloque | Por qué |
|---|---|
| `ordenamiento` (§4.9) | El comando `mapa` es un uso nuevo del ordenamiento |
| `inventario` (§4.5, `vistaInventario`) | Comparte la presentación de listas ordenadas |
| `retroceso` (§4.6) | Tres tipos nuevos de diferencia en el historial |
| `guardado` | El estado guardado crece con el conocimiento |
| `ciclo` | Cada movimiento llama a `entrar`; el ciclo debe seguir bajo **20 ms** con decenas de cazadores (código de salida distinto de 0 si no) |

Se compara con las cifras de `specs/001-terreno-y-cazador/mediciones.md` y de `DOCUMENTACION_DECISIONES_DISENO.md`, y el antes y el después de cualquier decisión que cambie se anota en `DECISIONES.md` (ver pendiente P4 del plan sobre la referencia «§5.6»).

## Qué resultado cambiaría cada decisión

| Decisión | Se revisa si… |
|---|---|
| Arreglo por id | La consulta crece con N de forma apreciable en A |
| Ordenar al consultar | En D, el comando completo pasa de 50 ms para el k realista de la cripta de referencia |
| Bucle directo en la antorcha | La antorcha pasara a más de un nivel (C) |
| Diferencias para deshacer | Las diferencias de E dejan de ganar a la instantánea con r pequeño y N pequeño |
| Aviso al cambiar | El sondeo de F resulta más barato con cambios frecuentes |
| Vista directa | G muestra que materializar gana de forma sostenida |
