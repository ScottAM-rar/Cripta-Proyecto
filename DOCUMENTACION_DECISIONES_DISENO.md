# CRIPTA — Documento de Decisiones de Diseño

La CRIPTA es un juego de exploración de criptas por eventos: no hay rondas, sino un reloj virtual que ejecuta lo que corresponda en cada instante. En este documento explicamos qué estructuras de datos usamos, por qué nos parecieron adecuadas y qué otras opciones también podían funcionar.

## Lectura del documento

En cada sección se explica el problema, las operaciones que realmente hace el juego, la estructura elegida, su complejidad, una alternativa con sus ventajas y desventajas, y el punto en el que la decisión dejaría de ser conveniente. Si varias partes del código usan la misma estructura, las explicamos juntas para no repetir lo mismo.

Estas fueron las restricciones principales que guiaron las decisiones del proyecto:

- **§7:** no utilizar `dict` como índice o almacenamiento del modelo; `list` solo como almacenamiento contiguo de bajo nivel, y el resto con estructuras propias.
- **§2.3 y §4.1:** el tiempo es un entero virtual, no el reloj de pared, y el orden de ejecución debe ser determinista: mismo tiempo, desempata el número de secuencia.
- **§4.9:** no utilizar `list.sort()` ni `sorted()` en los ordenamientos evaluados.
- **§5 y §9:** el presupuesto de solicitudes de red es parte del contrato, y la defensa será con una cripta que no vimos, posiblemente mucho mayor.

### Estado de la evidencia empírica

Las cifras de este documento salen de `python3 main.py --bench`. Cada valor es la mediana de varias repeticiones. También se midió la alternativa descartada, como pide el §8, y el mínimo y el máximo quedan en `bench_final.csv`. Los tiempos pueden cambiar según la computadora; lo importante aquí es comparar las estructuras entre sí.

En cuatro casos los resultados fueron distintos de lo que esperábamos al diseñar: la agenda, el inventario, la carga completa del guardado y la bitácora en memoria. En cada sección explicamos qué pasó.

## 1. Agenda de eventos del reloj virtual

La agenda es un montículo binario (*heap*) de mínimos. Los eventos se ordenan por `(tiempo de ejecución, número de secuencia)` y cada uno guarda su posición dentro del arreglo.

### Problema

Todo lo que ocurre en CRIPTA se programa como un evento futuro: una acción de un enemigo, el cierre de una puerta, el rearme de una trampa o el final de una poción o una antorcha. El juego repite el mismo ciclo: buscar el evento más cercano, sacarlo, ejecutarlo y normalmente programar otro.

También hay dos operaciones menos frecuentes, pero necesarias: cancelar un evento ya programado y volver a calcular el tiempo de las acciones de un actor cuando cambia su velocidad (§2.3). Con cientos de eventos pendientes, lo que más se repite es «dame el siguiente». Si para hacerlo recorriéramos toda la agenda cada vez, el costo del ciclo crecería demasiado.

### Por qué elegimos esta estructura

- Insertar y sacar el mínimo cuestan `O(log n)`; consultar el siguiente sin sacarlo cuesta `O(1)` (`heap[0]`), que es lo que necesita el ciclo para decidir si ya toca el turno del jugador.
- El desempate (§4.1) está incluido en la comparación: si dos eventos tienen el mismo tiempo, gana el número de secuencia más bajo. Así, dos ejecuciones con la misma semilla procesan los eventos en el mismo orden, que es necesario para `--replay`.
- Cada evento guarda su posición en el arreglo, lo que permite quitar un evento cualquiera en `O(log n)` sin recorrer la agenda. Sin ese dato, cancelar una puerta o reprogramar una acción costaría `O(n)` cada vez.
- Reprogramar no modifica el evento: lo reemplaza por uno nuevo con número de secuencia nuevo, como pide §2.3, y ambos movimientos quedan en el historial de retroceso (sección 3), así que deshacerlo es mover los mismos objetos en sentido contrario.

### Complejidad

| Operación | Costo | Frecuencia en el juego |
|---|---|---|
| Programar un evento | `O(log n)` | Una o más por cada acción |
| Sacar el siguiente | `O(log n)` | Una por cada evento ejecutado |
| Ver el siguiente | `O(1)` | Una por evento, para decidir el turno |
| Cancelar un evento concreto | `O(log n)` | Ocasional: puertas, muertes, pergamino |
| Reajustar velocidad de un actor | `O(n)` | Solo al empezar o terminar un efecto de velocidad |

El reajuste de velocidad es lineal a propósito: ocurre dos veces por poción, no por ciclo, y mantener un índice por actor para evitarlo habría añadido una segunda estructura que sincronizar sin ganar nada medible.

### Alternativa que también habría funcionado

**Lista ordenada con inserción por búsqueda binaria.**

|  | Lista ordenada (arreglo contiguo) | Heap con posición (elegido) |
|---|---|---|
| **Pro** | Ver y sacar el siguiente es `O(1)` si se mantiene en orden inverso; el código es más corto y la agenda queda siempre ordenada, lo que facilita depurarla y mostrarla. | Insertar y cancelar son `O(log n)` incluso con muchos eventos simultáneos. |
| **Contra** | Cada inserción o cancelación desplaza elementos: `O(n)`. Con varios cientos de eventos y criptas más grandes, el costo crece justo en la operación frecuente. | Solo el mínimo está ordenado; para ver toda la agenda hay que extraer o copiar y ordenar, y hay que mantener el campo `posicion` sincronizado en cada intercambio. |

Para las agendas normales del juego, de hasta 1 000 eventos pendientes, la lista ordenada habría sido más sencilla y habría funcionado bien. De hecho, la medición muestra que fue más rápida en el ciclo habitual. Aun así, dejamos el heap porque garantiza `O(log n)` en la defensa (§9), no porque haya sido siempre el más rápido.

### Límites conocidos

Si la agenda nunca superara unas decenas de eventos, la diferencia con la lista ordenada sería imperceptible y el heap sobraría. Si se necesitara consultar la agenda por actor con frecuencia, por ejemplo para mostrar «próxima acción de cada enemigo», el barrido lineal por actor dejaría de ser aceptable y habría que añadir un índice por actor.

### Evidencia empírica (`--bench`)

Ambas estructuras sacan los eventos en el mismo orden, verificado con 2 000 eventos con empates.

| Operación | N | Heap con posición | Lista ordenada |
|---|---|---|---|
| Programar N eventos | 100 | 67.4 µs | 75.1 µs |
| Programar N eventos | 1 000 | 732 µs | 1.08 ms |
| Programar N eventos | 10 000 | 7.56 ms | 20.15 ms |
| Sacar los N eventos | 100 | 135.6 µs | 11.4 µs |
| Sacar los N eventos | 1 000 | 2.29 ms | 127.5 µs |
| Sacar los N eventos | 10 000 | 35.74 ms | 1.55 ms |
| Cancelar N/2 eventos | 100 | 31.3 µs | 34.1 µs |
| Cancelar N/2 eventos | 1 000 | 338 µs | 511 µs |
| Cancelar N/2 eventos | 10 000 | 4.05 ms | 8.94 ms |
| 1 000 ciclos sacar + programar | 100 | 2.45 ms | 1.10 ms |
| 1 000 ciclos sacar + programar | 1 000 | 3.44 ms | 1.61 ms |
| 1 000 ciclos sacar + programar | 10 000 | 4.80 ms | 3.18 ms |

**Lectura:** Los resultados no muestran que el heap sea mejor en el ciclo habitual: la lista ordenada sacó y reprogramó eventos más rápido en los tres tamaños. Una posible explicación, que no medimos directamente, es que las operaciones de la lista se ejecutan en C, mientras que el heap se mueve con código Python.

El heap sí gana al programar muchos eventos de una vez, 2.7× con 10 000, y al cancelar, 2.2× con 10 000. Además, su costo por ciclo crece menos: 2.0× al pasar de 100 a 10 000 eventos, frente a 2.9× en la lista. Como el ciclo real suele tener solo unos cientos de eventos, la alternativa sencilla habría sido suficiente; el heap se justifica porque su costo crece mejor cuando aumenta la cantidad de eventos.

## 2. Caché de fichas y almacenamiento en disco

Las fichas del catálogo se manejan en dos niveles: una caché LRU de capacidad fija, que usa una cola doble de entradas `[clave, valor, veces_en_uso]`, y debajo un archivo binario indexado en disco. El archivo tiene un encabezado, bloques de datos, un índice y un pie con la posición del índice.

### Problema

Cada solicitud HTTP cuenta contra el presupuesto de la cripta y además tarda del orden de 400 ms (§5). El juego necesita las mismas fichas una y otra vez: un enemigo, su arma y el objeto que suelta.

La caché recibe muchas más búsquedas que inserciones y tiene que cumplir tres cosas: no superar su capacidad, no sacar una ficha que una sala cargada todavía usa y conservar el trabajo entre ejecuciones. El disco evita tener que repetir solicitudes.

### Por qué elegimos esta estructura

- **LRU:** lo que el jugador usó hace poco probablemente vuelva a necesitarse. Por eso se elimina primero lo que lleva más tiempo sin usarse y se mantienen disponibles las fichas de la zona actual.
- **Contador «en uso»:** una ficha que pertenece a un objeto o enemigo vivo en una sala cargada nunca se elimina de la caché. Si todas están en uso, la nueva no se guarda; la capacidad no se supera y el dato igual queda en disco.
- **Contadores de aciertos y fallos:** se obtienen durante la búsqueda y sirven para el reporte final del §5.1.
- **Cola doble:** mover una entrada al frente al usarla no desplaza el resto del arreglo.
- **Disco con índice al final:** primero se escribe un archivo temporal y luego se reemplaza el anterior. Así, si el programa se interrumpe, no se daña el archivo viejo. El encabezado valida el formato y la versión, y una ficha o sala se puede leer directamente desde su bloque.

### Complejidad

Buscar en la caché cuesta `O(c)`, donde `c` es su capacidad. Como la capacidad por defecto es 25 y se puede cambiar con `--cache-size`, el recorrido secuencial sigue siendo razonable.

En disco, localizar una ficha recorre el índice, `O(k)` para `k` claves, y después lee un solo bloque. Escribir cuesta `O(tamaño)` porque se vuelve a escribir el archivo completo. Esto es aceptable porque solo se hace al traer lotes nuevos de la red, no en cada ciclo.

### Alternativa que también habría funcionado

**Tabla hash propia más lista doblemente enlazada.**

|  | Tabla hash propia + lista doble (alternativa) | Cola doble con búsqueda lineal (elegido) |
|---|---|---|
| **Pro** | Búsqueda, inserción y eliminación `O(1)` en promedio, sin importar la capacidad; escala si la caché se agranda mucho. | Código corto y fácil de entender; sin función de dispersión ni colisiones; con capacidades chicas el costo es muy pequeño. |
| **Contra** | Hay que escribir y probar la tabla; §7 prohíbe `dict` en el modelo. También hay que sincronizarla con la lista y manejar colisiones y redimensionado. | Cada búsqueda recorre hasta `c` entradas; si la capacidad creciera a miles, la operación más frecuente se volvería la más cara. |

Si en la defensa aparece una cripta mucho más grande y se necesita una caché grande, esta sería la primera parte que convendría cambiar.

### Límites conocidos

- Con una capacidad de miles de fichas, el recorrido lineal de la caché dejaría de ser tan pequeño.
- El archivo indexado relee el índice completo en cada consulta y reescribe todo en cada escritura. Con cientos de salas guardadas, escribir lote por lote sería cada vez más caro. La salida es dividir por cripta, como ya se hace, y, si hiciera falta, añadir al final en vez de reescribir.
- Los valores se guardan como JSON: es un formato sencillo y depurable a costa de tamaño en disco.

### Evidencia empírica (`--bench`)

Al recorrer un pasillo de 60 salas con 400 ms simulados por solicitud:

| Estrategia de carga | Solicitudes | Espera simulada |
|---|---|---|
| Sala por sala, sin precarga | 63 | 25.2 s |
| Actual + vecinas en cada paso, profundidad 2 | 61 | 24.4 s |
| Perezosa, profundidad 2 | 33 | 13.2 s |
| Perezosa, lote de 10, por defecto | 9 | 3.6 s |

Búsqueda en la caché, en µs por operación:

| Fichas | Cola lineal, acierto | Cola lineal, fallo | Tabla hash propia, acierto (descartada) |
|---|---|---|---|
| 25 | 0.74 | 0.44 | 0.17 |
| 100 | 2.32 | 1.40 | 0.17 |
| 1 000 | 24.5 | 14.3 | 0.19 |
| 5 000 | 132.3 | 76.5 | 0.22 |

Disco: recuperar una ficha liberada cuesta 0.013 ms con 25 fichas en el catálogo, 0.047 ms con 200 y 0.204 ms con 1 000, contra unos 400 ms de una solicitud real. Guardar 10 fichas nuevas cuesta 1.6, 1.9 y 1.4 ms con 25, 200 y 1 000 fichas. Planear la vecindad en una cripta de 1 000 salas cuesta 15 µs a un paso y 38 µs a dos.

**Lectura:** La carga perezosa por lotes reduce las solicitudes de 63 a 9, es decir, 7×, y la espera baja de 25 s a 3.6 s. Con la capacidad por defecto, buscar cuesta 0.74 µs, unas 540 000 veces menos que una solicitud. Por eso la tabla hash no marca una diferencia importante en este caso; empezaría a valer la pena con cientos de fichas. Leer del disco también es unas 2 000 veces más barato que repetir la solicitud.

### Caché en una partida completa

Se simuló un recorrido de 150 pasos por una rejilla de 10×10 salas, con 40 tipos de enemigo y 30 de objeto, precargando vecinas, reteniendo las fichas de los enemigos de la sala actual y liberando al salir.

| Capacidad | Aciertos | Fallos | Tasa de aciertos | Solicitudes de red |
|---|---|---|---|---|
| 5 | 82 | 938 | 8.0 % | 19 |
| 10 | 316 | 704 | 31.0 % | 19 |
| por defecto (25) | 487 | 533 | 47.7 % | 19 |
| 100 | 950 | 70 | 93.1 % | 19 |
| 1 000 | 950 | 70 | 93.1 % | 19 |

La tasa de aciertos aumenta con la capacidad hasta cubrir las aproximadamente 70 fichas distintas de la cripta. Sin embargo, las solicitudes de red son las mismas con cualquier capacidad, porque lo que no conserva la caché se recupera desde el disco. En este caso, la capacidad reduce lecturas de disco, pero no solicitudes de red.

## 3. Historial de retroceso (pergamino)

El historial es una lista doblemente enlazada de nodos de cambio que se usa como una pila. Cada nodo guarda uno o más cambios, el valor anterior y el nuevo de lo que se modificó, y un nodo especial marca dónde empieza cada acción del jugador. Solo se conservan las últimas 5 acciones.

### Problema

El pergamino debe devolver el juego al instante anterior a la última acción del jugador. También debe deshacer sus consecuencias: golpes de enemigos, una trampa activada, una puerta programada para cerrarse, cambios en el reloj y eventos agregados o quitados de la agenda.

Cada ataque, recolección, movimiento, cambio de velocidad o evento de puerta deja una huella distinta. Las operaciones que se repiten son agregar al final, cada vez que algo cambia, y quitar del final, al deshacer. Descartar la acción más antigua ocurre solo cuando se pasa del límite.

### Por qué elegimos esta estructura

- Guardamos diferencias en vez de copias: cada cambio se registra como «el atributo X pasó de `a` a `b`». Así, el costo depende de lo que cambió y no del tamaño completo de la cripta.
- Pila sobre lista doble: agregar y sacar del final son `O(1)`, sin desplazar nada.
- Marcadores de acción: permiten deshacer una acción completa retirando nodos hasta encontrar el marcador, sin buscar ni contar.
- Límite de 5 acciones: acota la memoria sin importar cuánto dure la partida. Descartar la más antigua solo recorre los nodos de esa acción.
- Acción rechazada: como el marcador se abre antes de ejecutar, una acción rechazada se descarta sin gastar un lugar del historial ni mover el reloj (§2.13). El recorte se difiere hasta que la acción se acepta para no perder una acción válida anterior.

### Complejidad

| Operación | Costo |
|---|---:|
| Registrar un cambio | `O(1)` |
| Deshacer la última acción | `O(k)`, con `k` = cambios de esa acción |
| Descartar la acción más antigua | `O(kₐ)`, con `kₐ` = cambios de esa acción |
| Memoria total | Limitada a 5 acciones, sin importar la duración de la partida |

### Límites conocidos

- El mayor riesgo no es el rendimiento, sino que no falte ningún cambio: cada mecánica nueva debe registrar lo que modifica. Si se olvida algo, el retroceso puede quedar inconsistente. Por eso las pruebas comparan una foto completa del estado antes y después.
- El historial es un único objeto compartido por partida, patrón singleton; no admite dos partidas simultáneas en el mismo proceso.
- El historial no se guarda en disco: una partida cargada empieza con el historial vacío.

### Evidencia empírica (`--bench`)

Deshacer una acción devuelve el mundo a su estado anterior.

| Entidades en el mundo | Cambios por acción | Diferencias (elegido) | Instantáneas (alternativa) |
|---|---|---|---|
| 30 | 1 | 302 µs | 234 µs |
| 30 | 10 | 1.52 ms | 256 µs |
| 300 | 1 | 286 µs | 1.30 ms |
| 300 | 10 | 1.53 ms | 1.40 ms |
| 3 000 | 1 | 292 µs | 12.88 ms |
| 3 000 | 10 | 1.56 ms | 12.85 ms |

Deshacer una acción en un mundo de 300 entidades: con 1 cambio, 1.5 µs contra 11.4 µs; con 10 cambios, 4.5 µs contra 11.5 µs; con 100 cambios, 34.1 µs contra 11.7 µs.

El costo de las diferencias no depende del mundo, mientras que el de las instantáneas crece 55× de 30 a 3 000 entidades. Con un mundo de 300 entidades o más, las diferencias empatan o ganan al registrar y deshacen de 2.6 a 7.6× más rápido las acciones típicas de 1 a 10 cambios. Las instantáneas ganan en mundos de 30 entidades y al deshacer acciones de 100 cambios, algo que rara vez pasaría en el juego.

## 4. Inventario del jugador

El inventario es una lista doblemente enlazada con un cursor (`actual`) que apunta al objeto seleccionado, con capacidad máxima fija. Los dos primeros nodos son los objetos equipados: arma y armadura.

### Problema

El jugador recorre su mochila con «siguiente» y «anterior», usa o suelta el objeto bajo el cursor, recoge objetos al final y equipa o desequipa moviendo un objeto a los primeros lugares. El pergamino debe poder devolver un objeto a la posición exacta donde estaba.

Las operaciones frecuentes son mover el cursor, agregar al final y quitar el objeto seleccionado. Buscar un objeto por identidad y volver a insertarlo en una posición dada ocurre solo al usar, equipar o deshacer.

### Por qué elegimos esta estructura

- Mover el cursor al vecino, agregar al final y quitar los enlaces del nodo seleccionado son operaciones `O(1)` y no desplazan al resto.
- Quitar un objeto en medio no deja huecos que compactar ni obliga a renumerar índices.
- La capacidad se controla con un contador, sin reservar ni redimensionar memoria.
- Los objetos equipados son los dos primeros nodos, de modo que equipar es reenlazar un nodo y deshacer es reenlazarlo en su índice anterior.
- Las vistas ordenadas copian los objetos a una lista de trabajo y la ordenan ahí; el orden real de la mochila nunca cambia.

### Complejidad

| Operación | Costo | Frecuencia |
|---|---|---|
| Mover el cursor | `O(1)` | Muy frecuente |
| Agregar al final | `O(1)` | Frecuente |
| Soltar o usar el objeto del cursor | `O(1)` | Frecuente |
| Buscar un objeto por identidad | `O(n)` | Al usar, equipar o deshacer |
| Volver a insertar en un índice | `O(n)` | Solo al usar el pergamino |
| Vista ordenada | `O(n)` para copiar + costo del ordenamiento | Al consultar la mochila |

`n` es la capacidad del inventario, que es chica y fija; por eso los recorridos lineales son aceptables.

### Alternativa que también habría funcionado

**Arreglo contiguo con índice de cursor.**

|  | Arreglo con índice (alternativa) | Lista doble con cursor (elegido) |
|---|---|---|
| **Pro** | Acceso por índice `O(1)` y uso más cercano de la memoria; volver a insertar en una posición para el retroceso es un solo código; las vistas ordenadas se trabajan directamente sobre el arreglo. | Quitar y volver a conectar un nodo en medio no desplaza elementos; el cursor siempre apunta a un nodo válido sin recalcular índices. |
| **Contra** | Quitar en medio desplaza todos los elementos siguientes, `O(n)`; hay que ajustar el índice del cursor tras cada quita y el espacio se reserva por adelantado. | Sin acceso por posición: ir al índice `i` recorre `i` nodos; cada nodo agrega dos referencias de memoria. |

Con una capacidad de unas pocas decenas de objetos, ambas cuestan microsegundos; medido, el arreglo es más rápido en casi todo, así que la lista se mantiene por claridad y no por velocidad.

### Límites conocidos

Si la capacidad del inventario creciera a cientos o miles de objetos, las búsquedas lineales por identidad y las operaciones para volver a insertar durante el retroceso dejarían de ser tan pequeñas y habría que añadir un índice auxiliar. No es algo muy probable para el inventario de un jugador, pero es un límite importante. El ordenamiento vive en `Logica/ordenamiento.py`, así que el inventario no depende del controlador, como pide la separación MVC del §6.

### Evidencia empírica (`--bench`)

| Capacidad | Operación | Lista doble (elegido) | Arreglo (alternativa) |
|---:|---|---:|---:|
| 10 | Agregar N objetos | 2.3 µs | 1.0 µs |
| 10 | Mover el cursor de punta a punta | 0.8 µs | 0.9 µs |
| 10 | 200× quitar y reinsertar el del medio | 191 µs | 79 µs |
| 100 | Agregar N objetos | 20.8 µs | 7.2 µs |
| 100 | Mover el cursor de punta a punta | 7.0 µs | 8.2 µs |
| 100 | 200× quitar y reinsertar el del medio | 552 µs | 308 µs |
| 1 000 | Agregar N objetos | 193.5 µs | 59.7 µs |
| 1 000 | Mover el cursor de punta a punta | 57.7 µs | 70.5 µs |
| 1 000 | 200× quitar y reinsertar el del medio | 4.72 ms | 2.84 ms |

La medición contradice la expectativa: el arreglo es de 2.3 a 3.2× más rápido al agregar y de 1.7 a 2.4× al quitar y volver a insertar. La lista solo gana al mover el cursor. La ventaja teórica de no desplazar elementos no aparece porque la búsqueda por identidad es `O(n)` en las dos y termina siendo lo que más pesa.

## 5. Ordenamiento

Se implementaron dos algoritmos propios y estables: ordenamiento por inserción y ordenamiento por mezcla (*merge sort*), y una función que elige entre ellos:

- Hasta 15 elementos usa inserción.
- De 16 a 64 prueba la inserción con un presupuesto de `4·n` desplazamientos y, si los datos no estaban casi ordenados, se rinde y usa mezcla.
- Con más de 64 usa mezcla directamente.

Ambos reciben una función de clave, así que sirven para cualquier criterio sin conocer el tipo de dato.

### Problema

El §4.9 pide ordenar en contextos distintos: vistas del inventario, tabla de puntajes y listas auxiliares. Los tamaños, el orden previo de los datos y el costo de comparar cambian de un caso a otro. El enunciado exige dos algoritmos con características distintas y una elección automática.

### Por qué elegimos esta estructura

- **Inserción:** en listas pequeñas o casi ordenadas hace pocas comparaciones y mueve elementos sin memoria extra.
- **Mezcla:** garantiza `O(n log n)` sin importar cómo lleguen los datos. Es estable, así que ordenar por varios criterios sucesivos conserva el orden anterior entre iguales.
- **Estabilidad en ambos:** el resultado es determinista para empates.
- **Función de clave:** extrae el dato a comparar una sola vez por criterio de uso y permite que la lista enlazada del inventario no sepa nada del ordenamiento.

### Complejidad

| Algoritmo | Mejor caso | Peor caso | Memoria extra | Cuándo conviene |
|---|---|---|---|---|
| Inserción | `O(n)`, datos ya ordenados | `O(n²)` | `O(1)` | Pocos elementos o casi ordenados |
| Mezcla | `O(n log n)` | `O(n log n)` | `O(n)` | Muchos elementos, orden desconocido |

El límite de 15 elementos es el punto donde el costo de insertar uno por uno todavía es menor que el de crear las sublistas de la mezcla. Según `--bench`, con datos aleatorios el cambio se nota entre 15 y 50 elementos.

### Alternativa que también habría funcionado

**Un solo algoritmo:** ordenamiento rápido (*quicksort*) con pivote mediana de tres, o montículo (*heapsort*).

|  | Un algoritmo único (alternativa) | Inserción + mezcla según tamaño y orden previo (elegido) |
|---|---|---|
| **Pro** | Menos código y una sola estrategia que probar y explicar; quicksort ordena en el lugar y es muy rápido en promedio. | Cada algoritmo trabaja en el rango donde es bueno y se cumple el requisito del §4.9 de dos algoritmos con características distintas. |
| **Contra** | Quicksort no es estable y puede llegar a `O(n²)` con ciertos datos; heapsort usa la memoria de forma menos conveniente y no aprovecha datos ya ordenados. | Hay dos caminos que probar; la elección mira el tamaño y el orden previo, pero no el costo de comparar. |

### Límites conocidos

El enunciado pide escoger el algoritmo según propiedades medibles de los datos. Por eso la regla mira el tamaño y el orden previo. También medimos comparaciones costosas, pero no las usamos para decidir en tiempo de ejecución, porque eso podría producir elecciones distintas entre ejecuciones y afectar el determinismo del §4.1.

El orden previo solo se prueba hasta 64 elementos, porque con más la mezcla ya gana incluso con datos casi ordenados. La mezcla copia sublistas en cada nivel; con listas de decenas de miles de elementos, esa memoria extra podría notarse frente a una mezcla que use un solo arreglo auxiliar.

El ordenamiento se usa en el inventario y en la tabla de puntajes; los índices del archivo de guardado y las listas auxiliares del catálogo (§4.9).

### Evidencia empírica (`--bench`)

Los cuatro algoritmos dan el mismo resultado con clave compuesta, verificado con 300 datos.

| Clave | N | Entrada | Inserción | Mezcla | Automática | Quicksort (alternativa) |
|---|---:|---|---:|---:|---:|---:|
| Barata | 15 | Aleatoria | 5.5 µs | 7.6 µs | 5.4 µs | 4.5 µs |
| Barata | 15 | Inversa | 8.4 µs | 6.5 µs | 8.4 µs | 4.5 µs |
| Barata | 50 | Aleatoria | 48.5 µs | 33.5 µs | 33.5 µs | 18.9 µs |
| Barata | 50 | Casi ordenada | 11.8 µs | 28.3 µs | 28.5 µs | 19.4 µs |
| Barata | 50 | Inversa | 88.4 µs | 26.6 µs | 26.6 µs | 20.9 µs |
| Barata | 500 | Aleatoria | 4.71 ms | 487 µs | 486 µs | 284 µs |
| Barata | 500 | Inversa | 8.83 ms | 344 µs | 335 µs | 379 µs |
| Barata | 5 000 | Aleatoria | omitida | 6.71 ms | 6.69 ms | 3.93 ms |
| Barata | 5 000 | Casi ordenada | 53.6 ms | 5.89 ms | 5.93 ms | 4.94 ms |
| Barata | 5 000 | Inversa | omitida | 4.35 ms | 4.37 ms | 5.83 ms |
| Cara, 4 campos | 15 | Aleatoria | 11.4 µs | 10.5 µs | 11.5 µs | 7.3 µs |
| Cara, 4 campos | 50 | Aleatoria | 78.5 µs | 50.6 µs | 49.7 µs | 31.8 µs |
| Cara, 4 campos | 500 | Aleatoria | 7.83 ms | 742 µs | 741 µs | 476 µs |
| Cara, 4 campos | 5 000 | Aleatoria | omitida | 10.26 ms | 10.24 ms | 6.43 ms |
| Cara, 4 campos | 5 000 | Casi ordenada | 804 ms | 10.11 ms | 10.08 ms | 6.56 ms |

**Lectura:** El umbral de 15 se confirma para datos aleatorios: a `N = 15` la inserción gana y a `N = 50` pierde. La regla que solo mira el tamaño falla con datos casi ordenados: a `N = 50` elige mezcla cuando inserción tarda 11.8 µs frente a 28.5 µs.

La alternativa de un solo algoritmo fue la más rápida en 15 de 18 combinaciones con `N ≥ 50`, entre 1.2 y 1.8× sobre la mezcla, pero la mezcla gana con entrada inversa. Mantenemos la mezcla porque es estable y tiene un peor caso conocido, no porque siempre sea más rápida.

### Regla actual del juego, medida

Entre 16 y 64 elementos prueba la inserción con un presupuesto de `4·n` desplazamientos y se rinde a la mezcla si lo agota.

| Caso | Regla anterior | Regla actual |
|---|---:|---:|
| N = 50, casi ordenada | 27.7 µs | 11.2 µs |
| N = 50, aleatoria | 33.1 µs | 47.5 µs |
| N = 50, inversa | 26.6 µs | 41.0 µs |
| N = 50, casi ordenada, clave cara | 47.7 µs | 87.2 µs |
| N = 500, casi ordenada | 401.6 µs | 394.6 µs |
| N = 5 000, casi ordenada | 5.84 ms | 5.84 ms |

La regla nueva gana 2.5× donde el enunciado lo pide y pierde entre 14 y 40 µs cuando la inserción gasta su presupuesto antes de rendirse. Con presupuestos de `2·n` o `1·n` desaparece la ganancia con 50 casi ordenados, así que se dejó `4·n`.

### Tabla de puntajes

El archivo crece por anexado, así que en la práctica la tabla llega casi ordenada con partidas nuevas al final.

| N | Entrada | Inserción | Mezcla | Regla actual | Quicksort (alternativa) |
|---:|---|---:|---:|---:|---:|
| 1 000 | Aleatoria | omitida | 1.72 ms | 1.69 ms | 1.10 ms |
| 1 000 | Casi ordenada | 2.97 ms | 1.09 ms | 1.09 ms | 2.61 ms |
| 10 000 | Aleatoria | omitida | 23.21 ms | 23.18 ms | 14.87 ms |
| 10 000 | Casi ordenada | omitida | 14.14 ms | 14.19 ms | 19.87 ms |

Quicksort es 1.6× más rápido con datos aleatorios, pero con la tabla casi ordenada tarda de 1.4 a 2.4× más que la mezcla y no es estable. Para esta tabla la mezcla es la mejor opción por estabilidad y por el patrón real de los datos.

## 6. Guardado binario de la partida

La partida se guarda en un archivo binario con un formato propio: encabezado con marca y versión, bloques de datos, un índice de secciones, una tabla de salas ordenada por número y un pie de tamaño fijo que apunta a todo lo anterior.

Los valores se guardan con una marca de un byte por tipo y enteros de largo variable, usando 7 bits por byte y signo en zigzag. No se usa `pickle`, `json` ni diccionarios.

### Problema

El §4.10 pide formato propio, recuperar una sala específica sin leer el archivo completo y detectar un archivo de otra versión del programa. Además exige comparar tamaño y tiempo de carga contra guardar lo mismo en JSON.

### Por qué elegimos esta estructura

- El pie fijo al final permite saltar directo al final, validar el archivo y llegar al índice sin recorrer nada.
- La tabla de salas ordenada tiene entradas de tamaño fijo; se puede saltar a la entrada correspondiente y localizar una sala con búsqueda binaria en `O(log s)` lecturas pequeñas.
- El CRC por bloque detecta una sala dañada sin contaminar el resto.
- Los enteros de largo variable reducen el tamaño frente a un ancho fijo de ocho bytes.
- La escritura a un temporal y el reemplazo mantienen intacto el archivo anterior si el programa se cierra a mitad de guardar.
- La versión del formato en el encabezado rechaza archivos incompatibles con un mensaje claro.
- El modelo no conoce el archivo: el estado se exporta como datos simples y un adaptador los escribe.

### Complejidad

| Operación | Costo |
|---|---|
| Guardar la partida | `O(tamaño del estado)`, una sola pasada |
| Cargar una sala | `O(log s)` lecturas en la tabla + una lectura del bloque |
| Cargar la partida completa | `O(tamaño del estado)` |
| Listar las salas guardadas | `O(s)`, sin leer ningún bloque de sala |

### Alternativa que también habría funcionado

**Registros de tamaño fijo con `struct`, una fila por entidad.**

|  | Registros fijos con `struct` (alternativa) | Codificación con marcas y enteros variables (elegido) |
|---|---|---|
| **Pro** | Leer cualquier entidad es calcular una posición: acceso `O(1)` sin tabla; formato simple de documentar y verificar. | Compacto; los campos opcionales y listas de largo variable no desperdician espacio; un tipo nuevo se agrega al final. |
| **Contra** | Los textos y listas de largo variable obligan a reservar un ancho máximo o mantener tablas auxiliares; agregar un campo cambia el tamaño de todos los registros. | Para llegar a una sala hace falta la tabla; no se puede calcular directamente su posición porque los bloques miden distinto. |

La tabla de puntajes sí usa registros fijos porque todos los registros son del mismo tipo y agregar uno nuevo es escribir al final.

### Límites conocidos

- Guardar siempre escribe todo el estado; con cientos de salas cargadas, un guardado incremental sería más rápido pero más complejo.
- Las secciones del estado se buscan en orden porque son pocas; si creciera su número, convendría indexarlas igual que las salas.
- El historial del pergamino no se guarda; una partida cargada empieza sin poder retroceder.

### Evidencia empírica (`--bench`)

El binario devuelve exactamente el estado guardado y rechaza un archivo de otra versión.

| Salas | Tamaño en disco, binario / JSON | Guardar la partida, binario / JSON | Cargar todo, binario / JSON | Conseguir una sala, binario / JSON |
|---:|---|---|---|---|
| 10 | 8 107 B / 18 852 B, 2.33× | 520 µs / 736 µs | 1.13 ms / 69 µs | 30 µs / 67 µs |
| 100 | 42 296 B / 120 030 B, 2.84× | 2.54 ms / 4.17 ms | 5.18 ms / 427 µs | 30 µs / 446 µs |
| 1 000 | 395 092 B / 1 147 831 B, 2.91× | 23.3 ms / 40.3 ms | 46.9 ms / 4.28 ms | 38 µs / 4.28 ms |

El binario gana en tamaño, guardado y recuperación de una sala. Sin embargo, cargar la partida completa resultó más lento: el binario construye los objetos de datos y `json.loads` solo analiza el texto en C. Con 1 000 salas son 47 ms contra 4 ms. Esta diferencia solo aparece al continuar una partida guardada.

## 7. Bitácora de partida y reproducción (`--replay`)

Cada acción del jugador se guarda en dos lugares con roles distintos:

- En memoria, con una lista doblemente enlazada de acciones en orden de tiempo (`LogEventos`).
- En disco, con un archivo de texto (`AlmacenLogTexto`) con un encabezado de cuatro líneas: cripta, semilla, versión de cripta y versión de catálogo, seguido de una línea por acción.

### Problema

El §4.11 exige que cada acción quede registrada en un archivo de texto y que `--replay partida.log` reproduzca la partida completa sin interacción.

La reproducción debe ser determinista: con las mismas acciones, semilla y datos se debe obtener la misma partida. Si la cripta o el catálogo cambiaron desde que se grabó, el programa informa que no puede garantizar una reproducción correcta.

### Por qué elegimos esta estructura

- Agregar al final es `O(1)` y recorrer conserva el orden cronológico.
- El archivo de texto escribe cada acción en el instante en que ocurre. Es legible y se puede revisar con cualquier editor.
- Cada línea contiene los datos mínimos: tipo de acción, tiempo, actor y referencias por identificador, nunca objetos completos.
- El encabezado con versiones comprueba que la cripta y el catálogo sigan siendo los mismos.
- Un solo generador de azar por partida permite reconstruir la misma secuencia de tiradas.
- El modelo no escribe archivos: avisa cada acción a un registrador y el adaptador la guarda.

### Complejidad

| Operación | Costo |
|---|---|
| Registrar una acción en memoria | `O(1)` |
| Anexar una línea al archivo | `O(1)`, una escritura pequeña |
| Reproducir la partida | `O(a)`, con `a` acciones, más el costo de cada ciclo de eventos |
| Leer y validar el encabezado | `O(1)` |

Para interpretar cada línea, que está en JSON, se usa temporalmente el diccionario producido por `json.loads`. No se guarda ni se usa como índice, por lo que respeta el §7.

### Alternativa que también habría funcionado

**Arreglo dinámico (`list`) en memoria y formato binario para el log.**

|  | Arreglo dinámico + log binario (alternativa) | Lista enlazada + log de texto (elegido) |
|---|---|---|
| **Pro** | El arreglo da acceso por índice `O(1)` y aprovecha mejor la memoria; el log binario es más compacto y rápido de leer. | Agregar al final nunca copia ni cambia el tamaño de toda la estructura; el log de texto se puede leer, revisar y editar a mano para armar escenarios de prueba. |
| **Contra** | Un arreglo que crece copia sus elementos cada cierto tiempo; un binario no se puede inspeccionar sin herramienta. | Cada nodo agrega referencias de memoria; el texto ocupa más que el binario y cada línea hay que interpretarla al reproducir. |

### Límites conocidos

- Una partida de cientos de miles de acciones haría que la lista en memoria y el texto pesen más de lo óptimo.
- La reproducción es fiel solo mientras las versiones coincidan; con una versión distinta el programa se niega a reproducir.
- Una acción rechazada por el juego no se registra, así que el log contiene solo lo que efectivamente ocurrió.

### Evidencia empírica (`--bench`)

Ambas bitácoras de mensajes dejan los mismos 20 últimos, en el mismo orden.

| Medición | Elegido | Alternativa |
|---|---|---|
| 20 000 mensajes con la bitácora llena | Cola enlazada: 4.70 ms | Buffer circular: 1.48 ms |
| 1 000 acciones registradas en memoria | Lista enlazada: 214 µs | Arreglo: 21.3 µs |
| 10 000 acciones registradas en memoria | Lista enlazada: 2.62 ms | Arreglo: 209 µs |
| 300 líneas anexadas al `.log` | Abriendo y cerrando en cada acción: 944 µs | Archivo abierto una sola vez: 8.6 µs |
| Reproducir un log de 300 acciones | 49.7 ms | No medido |

Los resultados no confirman que agregar a una lista enlazada sea tan rápido como agregar a un arreglo: en memoria el arreglo es de 3 a 12× más rápido. Abrir y cerrar el `.log` en cada acción cuesta 110× más, pero permite que cada acción quede escrita aunque el programa se cierre inesperadamente.

## 8. El mundo: salas, vecindad, mensajes recientes y puntajes

Hay cuatro piezas más pequeñas que completan el juego: un arreglo indexado por número de sala, una cola para recorrer vecinos y guardar los mensajes recientes, y una tabla de registros fijos para los puntajes.

### Salas como arreglo indexado por número

La lista de salas tiene un puesto por cada número de sala; las salas que todavía no están cargadas quedan vacías. Encontrar la sala del jugador, de un enemigo o de una trampa es un acceso directo `O(1)` y es una de las consultas más frecuentes del ciclo.

Esto cumple el §7 porque se usa `list` como almacenamiento contiguo de bajo nivel y no como índice de un diccionario.

**Alternativa:** lista enlazada de salas cargadas.

- **Pro:** no reserva puestos para salas que nunca se visitan, útil si la cripta fuera enorme y casi toda quedara sin cargar.
- **Contra:** encontrar una sala pasa a ser `O(s)` y habría que recorrerla en cada evento.
- **Límite:** el arreglo asume que los números de sala son consecutivos desde 1. Con IDs muy dispersos habría que pasar a una estructura ordenada con búsqueda binaria.

### Cola para vecinos y últimos mensajes

Las salas vecinas se encuentran con un recorrido por niveles sobre una cola de doble extremo. Visita primero todas las salas a un paso, luego a dos, y así hasta la profundidad pedida. El orden por distancia decide qué salas entran primero en un lote de contenido, que es una sola solicitud con hasta 10 salas.

La bitácora de mensajes es una cola enlazada de 20 mensajes: agregar uno nuevo es enlazarlo al final y, si se pasa de 20, soltar el del frente. Ambas operaciones son `O(1)`.

**Alternativa:** buffer circular sobre un arreglo de tamaño fijo.

- **Pro:** memoria reservada una sola vez y mejor aprovechamiento de la memoria.
- **Contra:** quitar un mensaje del medio, como hace el retroceso, obliga a desplazar elementos; en la cola enlazada solo se vuelven a conectar dos nodos.
- **Límite:** comprobar si una sala ya fue alcanzada recorre la lista de alcanzadas, `O(n)` por sala. Con criptas de miles de salas conviene reemplazarla por una marca por número de sala.

### Tabla de puntajes en registros fijos

Cada partida terminada agrega un registro de tamaño fijo al final del archivo: nombre de hasta 15 caracteres, cripta, versión, acciones, enemigos derrotados, tiempo final y si fue victoria.

Agregar es `O(1)` y no reescribe el archivo. La tabla se ordena en memoria con los algoritmos de la sección 5 y una clave compuesta: primero las victorias, luego menos tiempo, menos acciones y más enemigos derrotados.

**Alternativa:** registros de texto CSV o JSON.

- **Pro:** legible y editable a mano.
- **Contra:** hay que interpretar cada línea y un campo mal escrito rompe la lectura; los registros fijos se validan solos por tamaño.
- **Límite:** con muchos miles de partidas, ordenar en cada consulta empezaría a costar y convendría mantener el archivo ordenado o leer solo los mejores N.

### Evidencia empírica (`--bench`)

Con 200 consultas por número a salas ya cargadas, el arreglo indexado tarda 1.6 µs con 10, 100 y 1 000 salas. La lista enlazada tarda 26 µs, 162 µs y 1.56 ms, respectivamente. El recorrido por niveles a profundidad 3 cuesta 3.4 µs con 10 salas, 10.9 µs con 100 y 75 µs con 1 000.

## 9. Qué se degrada primero si la cripta crece 50 veces

Las decisiones anteriores están pensadas para la cripta de referencia. Si la cripta de la defensa tiene 50 veces más salas y actores, lo primero que probablemente se note no será la agenda de eventos, sino las búsquedas lineales sobre datos que crecen con la cripta.

1. **Búsqueda de una sala en el esqueleto de la cripta.** Se hace recorriendo la lista de salas en cada consulta. Solución: construir una vez un arreglo indexado por número de sala.
2. **Archivo indexado de fichas y criptas.** Cada lectura relee el índice y cada escritura reescribe el archivo entero. Solución: guardar el índice en memoria durante la sesión y añadir al final.
3. **Caché con búsqueda lineal.** Aceptable con la capacidad actual; si se agranda a cientos de fichas, es candidata a pasar a una tabla hash propia.
4. **Comprobación de salas alcanzadas.** Actualmente es `O(n)` por sala. Solución: una marca por número de sala.
5. **Reajuste de velocidad.** El barrido por actor solo afecta cuando hay muchos actores y muchos cambios de velocidad seguidos. Solución: un índice por actor.
6. **Guardado completo.** Crece con las salas cargadas, no con las existentes, así que se mantiene limitado por la precarga y el tamaño de la caché.

En cambio, estas operaciones no dependen demasiado del tamaño de la cripta: agregar y sacar eventos de la agenda, registrar y deshacer cambios, agregar elementos a la bitácora y al log, acceder a una sala ya cargada por número y leer una sala del guardado mediante búsqueda binaria.

### Evidencia del ciclo de eventos (§5.2, `--bench`)

El límite es de 20 ms entre dos decisiones del jugador. Un ciclo es la acción ESPERAR más todos los eventos hasta la siguiente decisión. El veredicto usa el peor de 30 ciclos.

| Esbirros activos, eventos pendientes | Ciclo, mediana | Peor de 30 ciclos | Veredicto |
|---|---|---|---|
| 10 | 112 µs | 115 µs | Cumple |
| 100 | 1.05 ms | 2.07 ms | Cumple |
| 300 | 3.39 ms | 4.63 ms | Cumple |
| 1 000, prueba de estrés | 12.67 ms | 13.23 ms | Cumple, no decide el veredicto |

El ciclo cumple con bastante margen hasta 300 esbirros y todavía cumple con 1 000. Para lograrlo se ajustó el recolector de basura con umbrales 50 000, 20 y 100, y se congelaron los objetos de larga vida después del calentamiento. Sin ese ajuste, el peor ciclo con 1 000 esbirros llegaba a unos 55 ms.

## 10. Resumen de las decisiones

| Problema | Estructura elegida | Alternativa considerada |
|---|---|---|
| Agenda de eventos | Heap binario con posición por evento | Lista ordenada con búsqueda binaria |
| Caché de fichas | Cola doble LRU con contador de uso + archivo indexado | Tabla hash propia + lista doble |
| Historial de retroceso | Lista doble como pila con marcadores de acción | Instantáneas en buffer circular |
| Inventario | Lista doble con cursor | Arreglo contiguo con índice |
| Ordenamiento | Inserción + mezcla según tamaño y orden previo | Un solo algoritmo, quicksort o heapsort |
| Guardado binario | Bloques con marcas + tabla de salas ordenada + pie fijo | Registros fijos con `struct` |
| Bitácora y reproducción | Lista doble en memoria + texto de solo anexado | Arreglo dinámico + log binario |
| Salas, mensajes y puntajes | Arreglo indexado, cola enlazada, registros fijos | Lista enlazada, buffer circular, texto CSV/JSON |

## 11. Pendientes antes de la defensa

- **Hecho:** `--bench`, con la medición de cada sección y de la alternativa descartada. Todavía falta repetir todo en Python 3.11+ y medir el ciclo de 1 000 esbirros con y sin el ajuste del recolector de basura.
- **Hecho:** veneno y regeneración del §2.10: pulsos de veneno cada 80 unidades durante 400 y regeneración de enemigos cada 200, con sus cambios en el historial de retroceso y sus eventos en la agenda.
- La selección del ordenamiento ya usa el tamaño y el orden previo (§4.9); el costo de comparar se mide pero no entra en la regla. Falta extenderlo a los índices del guardado y a las listas del catálogo.
- **Hecho:** comparación del guardado binario con JSON (§4.10, sección 6): gana en tamaño, guardado y recuperación de una sala, y pierde al cargar la partida completa.
- **Hecho:** el módulo de ordenamiento vive ahora en la capa de lógica (§6).
