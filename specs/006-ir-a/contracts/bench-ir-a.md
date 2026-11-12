# Contrato de `--bench`: bloque `ir_a`

Invocación: `python main.py --bench ir_a` (también incluido en `--bench` sin argumentos). Sin red ni vista. Criptas sintéticas deterministas por semilla (`bench/datos.py`, `tests_labs/cripta_sintetica.py`, `bench/juego.py`). **Requisitos**: FR-250, FR-251; constitución VII. Archivo: `bench/ir_a.py`.

## Tamaños

**400, 2 000 y 20 000 salas** (rejillas 20×20, 20×100 y 100×200), el mayor 50 veces el menor; explorado = 10 % de las salas salvo donde se indica. Las secciones A, E y F usan criptas pequeñas o corredores; B, C y H usan 2 000 salas; D y G usan los tres tamaños. G repite el viaje 5 veces (3 en 20 000 salas) con una partida nueva cada vez y reporta mediana, el máximo de las medianas por paso y el máximo absoluto.

El criterio de 5 ms de FR-250 es **duro por tiempo** (lo exige la especificación); los demás criterios son **por conteo** (lección de la 005: a decenas de microsegundos la razón de tiempos es frágil, solo se informa).

## Secciones

| Sección | Mide | Alternativa descartada que también se mide | Criterio |
|---|---|---|---|
| A. Ruta | Cálculo del campo y recorrido de un viaje de L pasos en rejillas con muchos empates | Enumerar rutas óptimas completas y comparar lista a lista (D1) | **Duro**: ambas dan la misma lista de salas (verificación previa). Se informan el número de rutas que enumera la alternativa y la razón de tiempos |
| B. Paso por el flujo normal | Un paso de «ir a» completo (`accionJugador` + `ingresarEnSala` + comprobaciones) | Camino propio que mueve y avanza el reloj (existe solo aquí; D2) | **Duro**: caminar a mano y viajar dejan el mismo estado (sala, reloj, conocimiento, vida, salas cargadas). Tiempo informado |
| C. Recálculo | Recálculos y salas fijadas por viaje en tres políticas: cada paso (A), solo si cambia la versión sin cota (B), solo si cambia la versión con cota de costo (C, la elegida) | Recalcular cada paso y la versión sin cota | **Duro**: C recalcula 0 veces en un viaje sin cambios de conocimiento, fija a lo sumo las salas que B, y las tres políticas recorren las mismas salas. Se informan las salas fijadas |
| D. Detención | Comprobaciones tras el paso con 0, 10 y 100 enemigos en la sala | Revisar el contenido de las salas de la ruta (D4) | **Duro**: el trabajo crece con los enemigos de la sala, no con V ni con el tamaño de la cripta (conteo de enemigos examinados) |
| E. Pergamino | Revertir un paso con y sin antorcha | Una sola acción por viaje (D5) | **Duro**: cambios revertidos = cambios del paso, en los tres tamaños |
| F. Registro | Escribir `IR_A`/`FIN_IR_A` y repetir viajes de 10, 100 y 1 000 pasos | Repetir sin marcas | **Duro**: la diferencia es de 2 registros, constante en L |
| G. **Paso, peor caso** | Un paso con antorcha encendida (la versión sube al entrar a salas nuevas), destino lejano, 10 % explorado, y un paso que descubre una puerta cerrada y recalcula sin cota. Los pasos que capturan un punto de control (007) se miden aparte | — | **Duro (FR-250) en 400 y 2 000 salas: el máximo de las medianas por paso ≤ 5 ms, también para el paso con captura y para el paso que recalcula tras una puerta cerrada.** En 20 000 salas (2 000 exploradas) el paso sin captura es duro; la captura (~8 ms) y el recálculo tras una puerta cerrada (~12 ms) superan 5 ms y se informan sin decidir el veredicto (ver `DECISIONES.md`). Pasos medidos con el recolector de basura apagado |
| H. Equivalencia | Reutilizar el campo (políticas B y C) frente a recalcular desde cero en cada paso, sobre viajes con y sin antorcha, puertas que cambian y pergamino | — | 100 % de decisiones idénticas (constitución III) |
| I. **Paso con el mapa conocido completo** | Un paso con antorcha encendida y **todas** las salas exploradas (criterio del enunciado §6.1), con y sin una puerta cerrada en la ruta, en 400, 2 000 y 20 000 salas | — | **Duro (FR-250, FR-251) en 400 salas: el máximo de las medianas por paso ≤ 5 ms**. En 2 000 y 20 000 salas se informa; lo que supera 5 ms se anota sin ocultarlo |

## Salida

`bench/__init__.py` registra el bloque `("ir_a", ir_a.ejecutar)` y su criterio de salida: el código de retorno global es 1 si G supera 5 ms en los tamaños de criterio duro o si I supera 5 ms en 400 salas o si falla cualquier verificación de A a F, H o I. La salida imprime, igual que el bloque `mapa`: «Ir a (paso ≤ 5 ms y equivalencias): CUMPLE / NO CUMPLE».

## Se repiten en esta capacidad con la carga nueva

| Bloque | Por qué |
|---|---|
| `mapa` (G, vista para rutas) | El viaje es el primer uso real de la vista |
| `retroceso` | Cada paso del viaje es un nodo más del historial |
| `ciclo` | El paso llama a `ingresarEnSala` y a `accionJugador`: el ciclo debe seguir bajo 20 ms |

El antes y el después de cualquier decisión que cambie (por ejemplo, adoptar la política C) se anota en `DECISIONES.md`.
