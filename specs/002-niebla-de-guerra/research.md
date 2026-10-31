# Investigación: Niebla de guerra y mapa conocido

**Especificación**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Cada decisión sigue el mismo orden: qué se decide, alternativas, complejidad esperada, módulos afectados, evidencia y límites. «Evidencia preliminar» son mediciones de un script desechable, hechas el 2026-10-31 sobre rejillas sintéticas con las estructuras del repositorio; **no sustituyen a `--bench mapa`**, que las repite de forma reproducible (semilla fija, tres tamaños, mediana de 7 repeticiones) y es la que se cita en `mediciones.md` y `DECISIONES.md`. Cuando una decisión dependa de una medición que todavía no existe, se dice qué resultado la cambiaría.

Notación: N = mayor id de sala + 1 (tamaño de las listas; los ids van desde 1), k = salas exploradas, g = salidas de una sala (como máximo 4), r = cambios de conocimiento de una acción.

## 0. Hechos del código que condicionan el diseño

1. **El esqueleto ya está completo y gratis.** `MapaCripta` se construye una vez al iniciar con salientes, entrantes, costo y estado inicial de la puerta de cada salida. Leerlo no gasta solicitudes ni depende de qué salas tengan contenido descargado. La antorcha puede explorar vecinas **sin** `ingresarEnSala` (que activa enemigos y trampas) ni `construir_sala` (que gasta presupuesto).
2. **El esqueleto trae el nombre de cada sala, pero `MapaDTO` lo descarta** (pendiente P2 del plan). Se añade `SalaMapaDTO.nombre`.
3. **Cada salida tiene su propio estado de puerta** y no hay sincronización con la salida inversa (pendiente P1). La memoria es por salida; una conexión son dos salidas.
4. **`fijar_cerrada` ya avisa.** Recibe un `avisar(salida)` y todo cambio de puerta (abrir, cierre automático, deshacer) pasa por él. `GestorEventos._puerta_cambio` ya es ese aviso para el campo de costos de los cazadores.
5. **El retroceso solo registra dentro de una acción.** `RetrocesoLogica.registrar_cambio` no hace nada si `cantidad_acciones == 0`, y al deshacer saca los nodos del final de la lista; dentro de un nodo `PergaminoLogica.aplicar_cambios` recorre los `CambioDTO` en orden inverso. Esto da gratis FR-215 (el conocimiento del instante 0 se crea antes de cualquier acción y no es deshacible) y el orden «quitar del final».
6. **El jugador «entra» en `MOVER_JUGADOR` con éxito.** `GestorEventos` llama entonces a `cargar_sala` (que es `ingresarEnSala`, y activa enemigos) y luego `EstadoJuegoLogica.accionJugador` activa las trampas. Son los puntos que la antorcha no debe tocar.
7. **El pergamino no abre grupo** y, al deshacer, `fijar_cerrada` vuelve a llamar al aviso de puertas. Si ese aviso observara, registraría cambios nuevos en medio de una reversión (research §2).

## 1. Estado de conocimiento por sala (FR-201 a FR-206, FR-223)

**Decisión.** Una lista `estado` de tamaño N con un entero por sala (0 desconocida, 1 avistada, 2 explorada), indexada por id. Consultar es `estado[id]`.

| | Arreglo indexado por id (elegida) | Recorrer una lista de salas conocidas |
|---|---|---|
| Consultar el estado | O(1) | O(k) por consulta |
| Marcar una sala | O(1) | O(1) añadir, O(k) para saber si ya estaba |
| Memoria | O(N), una vez por partida | O(k) |
| Inicializar o restaurar | O(N) | O(k) |
| Módulos afectados | `MapaConocido` | `MapaConocido` |

**Evidencia preliminar** (100 consultas, mediana):

| Cripta | k | Arreglo | Lista de conocidas |
|---|---:|---:|---:|
| 400 salas | 200 | 2,9 µs | 337,9 µs |
| 4 900 salas | 300 | 3,8 µs | 575,0 µs |
| 40 000 salas | 300 | 4,0 µs | 468,4 µs |

El arreglo es entre 115 y 150 veces más rápido y casi no crece al multiplicar N por 100 (2,9 → 4,0 µs, efecto de caché del procesador). La lista crece con k.

**Evidencia que dará `--bench mapa` A**: consulta de estado y de puerta en tres tamaños (400, 2 000 y 20 000 salas), con k fijo y con k proporcional a N.

**Límites.** El arreglo ocupa memoria proporcional a la cripta aunque se explore poco (con 40 000 salas, las dos listas suman unos 1,6 MB de punteros, 5·N posiciones; comparable al esqueleto que `MapaCripta` ya guarda). Reiniciar o restaurar cuesta O(N) una vez. Si una cripta llegara a millones de salas, la alternativa de listas pequeñas ganaría en memoria; la capacidad 001 ya asume el mismo dimensionamiento para el esqueleto.

**Qué la cambiaría.** Que la consulta del arreglo creciera con N de forma apreciable en el bloque A (no ocurre en la medición preliminar).

## 2. Memoria de puertas (FR-206 a FR-209, FR-214)

**Decisión.** Una lista plana `puertas` de tamaño 4·N: la posición `sala*4 + d` guarda el estado recordado de la salida de `sala` en la dirección `d` (0 norte, 1 sur, 2 este, 3 oeste, el orden N, S, E, O del esqueleto). Valores: 0 sin observar, 1 abierta, 2 cerrada.

### 2.1 Dónde se guarda

| | Lista plana de 4·N (elegida) | Campo `recordada` dentro de cada `AristaCripta` | Lista de observaciones (sala, dirección, estado) |
|---|---|---|---|
| Consultar | O(1) | O(1) | O(observadas) |
| Modifica `MapaCripta` | No | **Sí** (prohibido por la tarea) | No |
| Comparte estado con los cazadores | No | Riesgo: la arista es la del mapa real | No |
| Memoria | O(N) | O(aristas) | O(observadas) |

La segunda se descarta por la restricción de no modificar `MapaCripta` y porque mezclaría conocimiento del jugador con el esqueleto que usa el cazador (FR-117 exige que no dependan). La tercera consulta en O(observadas).

### 2.2 Cómo se observa una puerta (FR-207)

Dos momentos, un solo punto de cambio de puertas:

1. **Al entrar a una sala `S`** (`entrar`): para cada arista saliente de `S` y para cada arista **entrante** a `S` se lee el estado real con `MapaCripta.esta_abierta(arista, salas)` (el de la sala cargada o, si no está cargada, el inicial: la misma regla de la 001) y se anota si difiere de lo recordado. Cuesta O(g + entrantes de S).
2. **Cuando una puerta cambia mientras el jugador sigue allí** (`puerta_cambio`): `fijar_cerrada` llama a `avisar(salida)`. El aviso de las acciones hacia adelante (`SalaLogica`: abrir y cerrar, incluido el cierre automático, que llega como evento `CERRAR_PUERTA`) llega además a `MapaConocido.puerta_cambio(salida)`. Este busca por identidad el objeto `salida` entre las salidas de la sala del jugador y entre las salidas de las salas de origen de sus aristas entrantes (a lo sumo 4 + 4·entrantes comparaciones). Si lo encuentra, observa esa posición; **si no, no hace nada**, que es exactamente FR-208: una puerta que cambia lejos no se observa.

El aviso **no necesita saber el origen** de la salida (`SalidaDTO` no lo trae) y **no cambia la firma de `fijar_cerrada`**.

### 2.3 El aviso del pergamino no observa

`PergaminoLogica` recibe un aviso distinto: solo el del campo de costos. Si observara, el orden inverso del deshacer produciría esto: se revierte `OBSERVAR_PUERTA` (recordada vuelve a su valor anterior) y después `CAMBIAR_PUERTA` (la puerta real vuelve atrás) avisaría y volvería a observar, escribiendo la memoria con un valor que el jugador no tenía antes de la acción y registrando un cambio nuevo en medio de una reversión. Con avisos separados, deshacer restaura la memoria **solo** por los `OBSERVAR_PUERTA` registrados.

### 2.4 Alternativas para «cómo se entera»

| | Aviso al cambiar + lectura al entrar (elegida) | Sondeo: leer las puertas de la sala actual después de cada evento |
|---|---|---|
| Costo por evento sin cambio de puertas | 0 | O(g + entrantes) en **cada** evento |
| Costo por cambio de puerta | O(g + entrantes) | igual, pero además cada evento |
| Segundo camino de cambio de puertas | No: reutiliza `avisar` | No |
| Riesgo | Olvidar enganchar un camino hacia adelante | Observa tarde: el cambio y la lectura quedan en nodos distintos |

El ciclo de eventos de la Parte I corre con decenas de cazadores y debe quedar bajo 20 ms; pagar un sondeo en cada evento no tiene justificación cuando los cambios de puerta son raros. **`--bench mapa` F** mide ambos con puertas que cambian poco y mucho. La prueba `test_puertas_punto_unico` sigue prohibiendo escribir `.cerrada` fuera de `fijar_cerrada`, y una prueba nueva verifica que todo camino que llega a `fijar_cerrada` hacia adelante pasa por un aviso que alcanza a `MapaConocido`.

### 2.5 Equivalencia por evento (principio III)

El conocimiento es estado, no una caché; lo que se debe demostrar es que **el estado recordado de cada puerta coincide con lo que se obtendría releyendo la historia de observaciones desde cero**. Se razona por evento:

| Evento | Qué hace el conocimiento | Por qué es equivalente a empezar de cero |
|---|---|---|
| Instante 0 | Explora la sala inicial y observa sus puertas sin registrar | Es la definición (FR-202) |
| Entrar a una sala | Lee el estado real de sus salidas y entrantes; anota solo diferencias | Una lectura es una observación (FR-207) |
| Puerta cambia junto al jugador | `puerta_cambio` anota el estado nuevo | Es la segunda observación de FR-207 |
| Puerta cambia lejos del jugador | No pasa nada | FR-208 |
| Deshacer con el pergamino | Revierte `EXPLORAR_SALA`, `AVISTAR_SALA` y `OBSERVAR_PUERTA` de la acción en orden inverso | Cada reversión devuelve el `valor_anterior` exacto |
| Restaurar una partida | Carga los arreglos guardados y los valida | El archivo contiene el mismo estado (FR-220) |
| Un enemigo se mueve, ataca o muere | Nada | FR-213 |
| Contenido de una sala se descarga o no | Nada | El conocimiento solo lee el esqueleto y `esta_abierta` (FR-222) |

La referencia de pruebas (`tests_labs/referencia_conocimiento.py`) reconstruye el conocimiento repitiendo, sobre un modelo vacío, las entradas y observaciones de la historia de acciones, y se compara con el conocimiento incremental tras cada acción y tras cada deshacer. Un deshacer de r acciones debe dar exactamente el conocimiento de r acciones antes (SC-003).

**Límites.** La búsqueda por identidad depende de que `salas[...].salidas` contenga el mismo objeto que `fijar_cerrada` recibe, algo que hoy es cierto (los avisos se disparan con el objeto de la sala). Si alguien clonara salidas, la prueba de caminos de cambio de puertas lo detectaría.

## 3. Lista de exploradas y orden del comando `mapa` (FR-217, FR-224)

**Decisión.** Una lista `exploradas` con los ids en orden de descubrimiento (se añade al explorar; se quita del final al deshacer). El comando `mapa` obtiene el orden ascendente de id **al consultar**, con `ordenar_adaptativo(copia de exploradas)`; la lista guardada no se reordena.

Qué usa cada operación la lista: deshacer (quitar del final), guardar (el estado guardado es el orden de descubrimiento, canónico) y el comando `mapa`.

| | Ordenar al consultar (elegida) | Escanear `estado` de 1 a N buscando las exploradas | Mantener una lista siempre ordenada (búsqueda binaria propia + inserción) |
|---|---|---|---|
| Costo en cada entrada | O(1) por sala explorada | O(1) | O(k) por inserción (desplazar) |
| Costo en cada deshacer | O(1) (quitar del final) | O(1) | O(k) (localizar y quitar) |
| Costo del comando | O(k log k) (mezcla; datos en orden arbitrario) | **O(N)**, no depende de k | O(k) (copiar) |
| Cumple FR-224 (la entrada no depende del mapa conocido) | Sí | Sí | **No**: la entrada depende de k |
| Depende del tamaño de la cripta | No | **Sí** | No |
| Módulos afectados | `MapaConocido`, `Logica/ordenamiento` (reutilizado) | `MapaConocido` | `MapaConocido` |

**Evidencia preliminar** (una consulta del comando; las exploradas siguen un paseo en la rejilla, es decir, orden de descubrimiento real):

| Cripta | k | Ordenar al consultar | Escanear el arreglo | Mantener ordenada (por inserción) |
|---|---:|---:|---:|---:|
| 4 900 | 50 | 86,5 µs | 179,4 µs | 0,4 µs |
| 4 900 | 500 | 880,1 µs | 187,9 µs | 1,3 µs |
| 40 000 | 50 | 83,0 µs | 2,31 ms | 0,4 µs |
| 40 000 | 500 | 1,20 ms | 2,30 ms | 0,7 µs |
| 40 000 | 5 000 | 10,47 ms | 1,39 ms | 1,6 µs |

Las tres dan el mismo resultado (verificado en el script). Lectura: ordenar al consultar gana cuando k es pequeño respecto de N (la situación típica: se explora una fracción de la cripta) y el escaneo gana cuando k pasa de ≈ N/8 (con 5 000 de 40 000 el escaneo es 7,5 veces más rápido). La lista siempre ordenada cuesta casi nada por inserción pero lo paga **en cada entrada y cada deshacer**, justo lo que FR-224 y FR-225 piden evitar, y el comando se usa a ritmo humano.

**Por qué se elige ordenar al consultar.** El comando es manual (a lo sumo unas veces por minuto), imprime O(k) líneas —un costo mayor que el del orden—, y ordenar al consultar mantiene la entrada y el deshacer en O(1) por sala. 10 ms para 5 000 exploradas no se percibe.

**Evidencia que dará `--bench mapa` D**: los tres métodos con k = 50, 500 y 5 000 en los tres tamaños, con verificación de igualdad de resultados.

**Límites conocidos.** Con k comparable a N (jugador que explora casi toda la cripta con antorcha) el escaneo es mejor. Un híbrido (escanear si `k·log k > N`) sería correcto y determinista, pero añade un camino que probar; se deja anotado y no se adopta salvo que el bloque D muestre más de 50 ms para el k realista de la cripta de referencia. No se usa `sorted()` ni `list.sort()`.

## 4. Exploración al entrar y con antorcha (FR-204, FR-210 a FR-212, FR-224)

**Decisión.** `entrar(sala, antorcha)` hace, leyendo solo `MapaCripta`:

1. Explora `sala` (si no lo estaba) y avista el destino de cada una de sus salidas que esté desconocido.
2. Observa las puertas (§2.2).
3. Si la antorcha estaba encendida **en el instante de entrar**: para cada salida de `sala`, en el orden N, S, E, O, explora el destino (si existe y no estaba explorado) y avista los destinos de **sus** salidas que estén desconocidos. No observa puertas, no activa enemigos ni trampas, no descarga contenido, no toca `ultimo_paso`.
4. Registra todo lo anterior en **un solo nodo** del historial.

Costo: O(g + g²) = a lo sumo 20 comprobaciones por entrada, constante y proporcional a lo revelado (FR-224). No depende de k ni de N.

### 4.1 Cómo recorrer las vecinas de la antorcha

| | Bucle directo sobre `salidas(sala)` (elegida) | Reutilizar `RecorridoPorNiveles` con límite 1 |
|---|---|---|
| Qué visita | Las salidas de `sala` | Las salidas de `sala` (con límite 1 no examina las de sus vecinas) |
| Orden | N, S, E, O (determinista) | Menor id de sala dentro del nivel |
| Asigna memoria por llamada | No | Sí: una lista de salas, otra de niveles, un `RecorridoDTO` y un ordenamiento por nivel |
| Cola, marcas de época | No hacen falta (un nivel) | Se usan sin necesitarlas |
| Reutiliza código | No | Sí |
| Módulos afectados | `MapaConocido` | `MapaConocido` + dependencia de `RecorridoPorNiveles` |

**Evidencia preliminar** (explorar las vecinas de una sala del centro y avistar sus destinos):

| Cripta | Bucle directo | `RecorridoPorNiveles` (límite 1) |
|---|---:|---:|
| 400 | 1,2 µs | 7,7 µs |
| 4 900 | 1,1 µs | 7,9 µs |
| 40 000 | 1,1 µs | 8,6 µs |

Ambos son independientes de N, pero reutilizar el recorrido cuesta unas 7 veces más por entrada porque pone en marcha una estructura pensada para varios niveles. La única ventaja de reutilizarlo sería heredar su orden (menor id), que aquí **no importa**: el orden en que se descubren no se ve (el comando ordena) y cualquier orden fijo es determinista. Se elige el bucle directo y se mide el recorrido como alternativa descartada, **verificando que ambos exploran el mismo conjunto de salas**.

**Qué la cambiaría.** Si en el futuro la antorcha alcanzara más de un nivel, el recorrido por niveles pasa a ser la herramienta adecuada (su costo se amortiza); hoy FR-210 fija un solo nivel.

### 4.2 Por qué no pasa por `ingresarEnSala`

`ingresarEnSala` carga el contenido (`construir_sala`, que gasta presupuesto), precarga vecinas y activa los enemigos dormidos de la sala (`_activarEnemigos`). FR-211 prohíbe lo último. La exploración lee solo `MapaCripta`; no necesita ninguna sala cargada. Una prueba falla si, con la antorcha encendida, el número de solicitudes, de enemigos activos o de eventos en la agenda cambia por explorar vecinas.

### 4.3 FR-212 («la antorcha actúa solo al entrar»)

`entrar` lee `jugador.antorcha_encendida` una sola vez, en el instante de la entrada. Encender o apagar la antorcha no llama a `entrar`.

## 5. Cambios deshacibles (FR-214, FR-215, FR-225)

**Decisión.** Tres tipos nuevos de `CambioDTO`, cada uno con valor anterior y nuevo, registrados con una sola llamada de `registrar_cambio` por entrada o por aviso de puerta, de modo que cada acción del jugador contiene lo que descubrió. Detalle en [contracts/cambios-deshacibles.md](contracts/cambios-deshacibles.md).

| Operación | Qué cambia | `valor_anterior` → `valor_nuevo` |
|---|---|---|
| `EXPLORAR_SALA` | `estado[sala]` y la lista `exploradas` | 0 o 1 → 2 |
| `AVISTAR_SALA` | `estado[sala]` | 0 → 1 |
| `OBSERVAR_PUERTA` | `puertas[sala*4+d]` | 0, 1 o 2 → 1 o 2 |

Deshacer: `PergaminoLogica` delega en `MapaConocido.deshacer(cambio)`, que restaura el valor anterior y, para `EXPLORAR_SALA`, quita la sala del final de `exploradas`. El orden inverso del deshacer garantiza que la sala explorada más reciente es la última de la lista.

| | Diferencias con valor anterior (elegida) | Instantánea de los arreglos antes de cada acción |
|---|---|---|
| Registrar | O(r) | O(N) copiar |
| Deshacer | O(r) | O(N) restaurar |
| Memoria con 5 acciones en el historial | O(5·r) | O(5·N) |
| Coherente con la Parte I | Sí (el historial ya guarda diferencias, §4.6) | No |
| Módulos afectados | `MapaConocido`, `PergaminoLogica`, `GestorEventos` | los mismos y `RetrocesoLogica` |

**Evidencia preliminar.** La Parte I ya midió esta comparación para el estado del juego (`--bench retroceso`, diferencias frente a instantáneas); aquí la diferencia es más marcada porque los arreglos son de tamaño N. **`--bench mapa` E** mide deshacer r = 1, 10 y 100 cambios en los tres tamaños frente a copiar y restaurar los arreglos.

**Garantías que se prueban.**
- FR-215: el conocimiento del instante 0 se crea antes de que haya una acción abierta; `registrar_cambio` lo ignora. Una prueba intenta deshacer sin acciones y comprueba que la sala inicial sigue explorada y sus vecinas avistadas.
- Una acción rechazada (sin éxito) se descarta con sus cambios; los de conocimiento se revierten igual.
- `recortar_historial` descarta las acciones más antiguas **sin deshacerlas**: el conocimiento que se haya descubierto en ellas se conserva (no hay nada que deshacer).
- Un deshacer de varias acciones devuelve el conocimiento exacto previo (SC-003, referencia de §2.5).

**Límites.** El deshacer asume el orden inverso estricto de `RetrocesoLogica`; si otra capacidad (línea de tiempo) restaurara puntos de control, deberá restaurar también el conocimiento (ver contrato).

## 6. Persistencia (FR-220, FR-221)

**Decisión.** El estado guardado gana un campo `conocimiento` (al final, como pide el mecanismo del codec), con tres listas: exploradas en orden de descubrimiento, avistadas en orden ascendente y puertas observadas. Detalle en [contracts/estado-guardado-niebla.md](contracts/estado-guardado-niebla.md).

| | Solo lo no desconocido (elegida) | Volcar los arreglos completos (N y 4·N enteros) |
|---|---|---|
| Tamaño en el archivo | O(k + observadas) | O(N) siempre |
| Restaurar | O(k + observadas) más O(N) para dimensionar | O(N) |
| Archivo canónico | Sí | Sí |
| Coherente con el guardado de salas (solo las cargadas) | Sí | No |

La lista de avistadas **se puede derivar** de las exploradas y el esqueleto (FR-203: no explorada y destino de una salida de una explorada), pero FR-220 pide guardarla. Se guarda y se **valida al cargar** que coincide con la derivada: así un archivo incoherente se rechaza antes de tocar la partida (`restaurar` arma todo primero y reemplaza al final). Los archivos sin conocimiento se rechazan por versión (FR-221); el número depende de P3.

**Evidencia que dará `--bench guardado`** (repetido): tamaño y tiempo de guardar y cargar con el conocimiento, en los tres tamaños, para comprobar que no se rompe la ventaja del binario sobre JSON de la Parte I.

## 7. Vista del conocimiento para `BuscadorRutas` (futura 006)

**Decisión.** Un objeto `VistaMapaConocido(mapa_conocido)` que cumple el contrato que `BuscadorRutas` ya exige —`tamano`, `salidas(sala)`, `entrantes(sala)`, `transitable(arista)`— consultando los arreglos del conocimiento, sin copiar nada. Detalle en [contracts/vista-buscador.md](contracts/vista-buscador.md).

- `salidas(sala)` y `entrantes(sala)`: las del esqueleto si `sala` está explorada; vacías si no (de una sala no explorada no se conocen sus salidas).
- `transitable(arista)`: verdadero solo si el origen y el destino están explorados **y** la puerta recordada de esa salida es abierta.
- `version_conocimiento`: entero que sube con cada cambio del conocimiento, **también al deshacer**; la 006 lo comparará como hoy se compara `version_puertas`.

| | Vista que consulta los arreglos (elegida) | Materializar un mapa conocido nuevo (aristas copiadas, solo exploradas) |
|---|---|---|
| Costo de construir | 0 | O(aristas de las exploradas) en cada cambio |
| Costo de cada consulta | O(1) | O(1) |
| Memoria | 0 extra | O(k·g) |
| Consistencia | Siempre vigente | Hay que reconstruir ante cada cambio |
| Módulos afectados | `MapaConocido` | `MapaConocido` (+ un segundo mapa) |

**Evidencia.** La 001 ya midió el costo de pasar por una vista (T071: entre 14 % y 22 % más que sin vista, y el peor ciclo en ≈ 0,25 ms frente a 20 ms). **`--bench mapa` G** mide una búsqueda `BuscadorRutas` sobre la vista directa y sobre el mapa materializado, y verifica que ambas dan los mismos costos.

**Límite aceptado.** La puerta «abierta» es lo que el jugador **recuerda**; puede estar cerrada en realidad. Decidir qué hace el viaje al encontrarla cerrada es de la 006.

## 8. Vista de la consola (FR-216 a FR-219)

**Decisión.** La vista **solo recibe DTO de conocimiento**, nunca `MapaCripta` ni la lista de salas ni el estado real de las puertas:

- `Servicio.mapaConocido()` entrega un `MapaConocidoDTO` con las exploradas en orden ascendente; por cada salida: dirección, costo, puerta recordada (abierta, cerrada o sin observar) y destino (`id` y nombre solo si está explorado; si está avistado, solo la marca «sala sin explorar», sin id).
- `Servicio.vistaSalaActual()` entrega el mismo formato para la sala actual, de modo que `mostrar_juego` muestra las salidas con nombre solo si el destino está explorado (hoy imprime `Sala {id}` del destino, lo que viola FR-219).
- El comando `mapa` se resuelve en el controlador y **no pasa por `accionJugador`** ni por el log (FR-218).

| | Vista alimentada solo por DTO de conocimiento (elegida) | Vista con el mapa completo y filtros en cada llamada |
|---|---|---|
| Puede mostrar lo desconocido por error | **No**: el DTO no lo contiene | Sí: depende de que cada filtro esté |
| Prueba de FR-219 | Se arma el DTO a mano, sin mapa ni salas, y se imprime | Hay que vigilar cada punto de uso |
| Costo del comando | O(k log k) para el orden + O(k·g) para armar el DTO | igual |
| Módulos afectados | `Servicio`, `Controlador`, `Vista`, `MapaConocido` (instantánea), `DTO/ConocimientoDTO` | los mismos |

**Pruebas que la defienden** (no son de rendimiento): (1) construir el DTO a mano y renderizar con **ni `MapaCripta` ni salas disponibles** (objetos que fallan al tocarse), lo que demuestra que la vista funciona con el grafo completo apagado; (2) alterar nombres, salidas y contenido de las salas desconocidas y avistadas y comprobar que el texto del mapa no cambia (SC-002); (3) buscar en el texto impreso los ids y nombres de salas desconocidas y avistadas, que no pueden aparecer.

**Límites.** Armar el DTO copia k salas (O(k·g)); para un mapa de miles de salas serían miles de objetos pequeños, costo irrelevante a ritmo humano pero medido en el bloque D.

## 9. Mediciones de la Parte I que se repiten

Constitución VII: si la carga nueva cambia una decisión de la Parte I, se cambia y se documenta antes y después. Se repiten `ordenamiento` y `inventario` (el comando `mapa` es un uso nuevo del ordenamiento y comparte la presentación de listas con `vistaInventario`), `retroceso` (tres tipos nuevos de diferencia), `guardado` (el estado guardado crece) y `ciclo` (cada movimiento llama a `entrar`; límite 20 ms). Ver P4 sobre la referencia «§5.6».

## 10. Resumen de las decisiones

| # | Decisión | Elegida | Alternativa(s) descartada(s) medidas |
|---|---|---|---|
| 1 | Estado por sala | Arreglo por id | Lista de salas conocidas |
| 2 | Memoria de puertas | Lista plana 4·N; lectura al entrar + aviso al cambiar | Campo en la arista; lista de observaciones; sondeo tras cada evento |
| 3 | Orden del comando | Ordenar al consultar | Escanear el arreglo; lista siempre ordenada |
| 4 | Exploración | Bucle directo por las salidas | `RecorridoPorNiveles` con límite 1 |
| 5 | Deshacer | Diferencias con valor anterior | Instantánea de arreglos |
| 6 | Persistencia | Solo lo no desconocido, validado al cargar | Volcar los arreglos completos |
| 7 | Vista para rutas | Consulta directa a los arreglos | Mapa conocido materializado |
| 8 | Vista de consola | Solo DTO de conocimiento | Mapa completo con filtros |
